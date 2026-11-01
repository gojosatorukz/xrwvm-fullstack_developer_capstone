"""Session-based authentication for the dealership application."""

import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST, require_http_methods


def identity(user):
    return {
        "status": "Authenticated",
        "userName": user.username,
        "firstName": user.first_name,
        "lastName": user.last_name,
    }


def body(request):
    data = json.loads(request.body)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object.")
    return data


@require_GET
@ensure_csrf_cookie
def session_status(request):
    return JsonResponse(identity(request.user) if request.user.is_authenticated else {"status": "Anonymous"})


@require_POST
def login_user(request):
    try:
        data = body(request)
        user = authenticate(request, username=data.get("userName", ""), password=data.get("password", ""))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    if user is None:
        return JsonResponse({"error": "Invalid username or password."}, status=401)
    login(request, user)
    return JsonResponse(identity(user))


@require_http_methods(["GET", "POST"])
def logout_request(request):
    # GET confirms an already ended session; only CSRF-protected POST changes it.
    if request.method == "GET" and request.user.is_authenticated:
        return JsonResponse({"error": "Use POST to sign out."}, status=405)
    if request.method == "POST":
        logout(request)
    return JsonResponse({"status": "Logged out", "userName": ""})


@require_POST
def registration(request):
    try:
        data = body(request)
        username = str(data.get("userName", "")).strip()
        email = str(data.get("email", "")).strip()
        password = data.get("password", "")
        if not username or not email:
            raise ValidationError("Username and email are required.")
        User._meta.get_field("username").run_validators(username)
        validate_email(email)
        user = User(
            username=username,
            email=email,
            first_name=str(data.get("firstName", "")).strip()[:150],
            last_name=str(data.get("lastName", "")).strip()[:150],
        )
        validate_password(password, user)
        user.set_password(password)
        with transaction.atomic():
            user.save()
    except IntegrityError:
        return JsonResponse({"error": "That username is already registered."}, status=409)
    except ValidationError as exc:
        return JsonResponse({"error": " ".join(exc.messages)}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid registration data."}, status=400)
    login(request, user)
    return JsonResponse(identity(user), status=201)


@require_GET
def get_cars(request):
    from .models import CarMake, CarModel

    cars = [
        {"id": car.id, "CarMake": car.car_make.name, "CarModel": car.name, "CarYear": car.year, "CarType": car.type}
        for car in CarModel.objects.select_related("car_make")
    ]
    return JsonResponse({"status": 200, "CarModels": cars, "CarMakes": list(CarMake.objects.values("id", "name"))})


@require_GET
def get_dealerships(request, state="All"):
    from urllib.parse import quote
    from .restapis import get_request, ServiceError

    try:
        endpoint = "fetchDealers" if state == "All" else "fetchDealers/" + quote(state, safe="")
        return JsonResponse({"status": 200, "dealers": get_request(endpoint)})
    except ServiceError as exc:
        return JsonResponse({"error": str(exc)}, status=503)


@require_GET
def get_dealer_details(request, dealer_id):
    from .restapis import get_request, ServiceError

    try:
        dealers = get_request(f"fetchDealer/{dealer_id}")
        return JsonResponse({"status": 200, "dealer": dealers}, status=200 if dealers else 404)
    except ServiceError as exc:
        return JsonResponse({"error": str(exc)}, status=503)


@require_GET
def get_dealer_reviews(request, dealer_id):
    from .restapis import get_request, analyze_review_sentiments, ServiceError

    try:
        reviews = get_request(f"fetchReviews/dealer/{dealer_id}")
        for review in reviews:
            review["sentiment"] = analyze_review_sentiments(review["review"])
        return JsonResponse({"status": 200, "reviews": reviews})
    except ServiceError as exc:
        return JsonResponse({"error": str(exc)}, status=503)


@require_POST
def add_review(request):
    from datetime import date
    from .models import CarModel
    from .restapis import post_review, ServiceError

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Sign in before posting a review."}, status=401)
    try:
        data = body(request)
        text = str(data.get("review", "")).strip()
        dealer = int(data.get("dealership", 0))
        year = int(data.get("car_year", 0))
        purchase_date = date.fromisoformat(data.get("purchase_date", ""))
        if not text or len(text) > 5000 or dealer <= 0 or not 2015 <= year <= 2023:
            raise ValueError("Invalid review or purchase details.")
        if not isinstance(data.get("purchase"), bool):
            raise ValueError("Purchase must be true or false.")
        if not CarModel.objects.filter(car_make__name=data.get("car_make"), name=data.get("car_model")).exists():
            raise ValueError("Choose a car from the catalogue.")
        payload = {
            "name": request.user.get_full_name() or request.user.username,
            "dealership": dealer,
            "review": text,
            "purchase": data["purchase"],
            "purchase_date": purchase_date.isoformat(),
            "car_make": data["car_make"],
            "car_model": data["car_model"],
            "car_year": year,
        }
        saved = post_review(payload)
        return JsonResponse({"status": 200, "review": saved}, status=201)
    except (ValueError, TypeError, KeyError):
        return JsonResponse({"error": "Invalid review or purchase details."}, status=400)
    except ServiceError as exc:
        return JsonResponse({"error": str(exc)}, status=503)


@require_GET
def get_inventory(request, dealer_id=None):
    from .restapis import searchcars_request, ServiceError

    if dealer_id is None or dealer_id <= 0:
        return JsonResponse({"error": "A positive dealership ID is required."}, status=400)
    allowed = {"make", "model", "year", "mileage", "price"}
    if set(request.GET) - allowed:
        return JsonResponse({"error": "Unknown inventory filter."}, status=400)
    filters = {key: value for key, value in request.GET.items() if value}
    for key in ("year", "mileage", "price"):
        if key in filters and (not filters[key].isdigit() or not 0 < int(filters[key]) <= 10000000):
            return JsonResponse({"error": f"Invalid {key}."}, status=400)
    try:
        cars = searchcars_request(f"cars/{dealer_id}", **filters)
        return JsonResponse({"status": 200, "cars": cars})
    except ServiceError as exc:
        return JsonResponse({"error": str(exc)}, status=503)
