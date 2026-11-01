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
from django.views.decorators.http import require_GET, require_POST


def identity(user):
    return {'status': 'Authenticated', 'userName': user.username,
            'firstName': user.first_name, 'lastName': user.last_name}


def body(request):
    data = json.loads(request.body)
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object.')
    return data


@require_GET
@ensure_csrf_cookie
def session_status(request):
    return JsonResponse(identity(request.user) if request.user.is_authenticated
                        else {'status': 'Anonymous'})


@require_POST
def login_user(request):
    try:
        data = body(request)
        user = authenticate(request, username=data.get('userName', ''),
                            password=data.get('password', ''))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    if user is None:
        return JsonResponse({'error': 'Invalid username or password.'}, status=401)
    login(request, user)
    return JsonResponse(identity(user))


@require_POST
def logout_request(request):
    logout(request)
    return JsonResponse({'status': 'Logged out'})


@require_POST
def registration(request):
    try:
        data = body(request)
        username = str(data.get('userName', '')).strip()
        email = str(data.get('email', '')).strip()
        password = data.get('password', '')
        if not username or not email:
            raise ValidationError('Username and email are required.')
        User._meta.get_field('username').run_validators(username)
        validate_email(email)
        user = User(username=username, email=email,
                    first_name=str(data.get('firstName', '')).strip()[:150],
                    last_name=str(data.get('lastName', '')).strip()[:150])
        validate_password(password, user)
        user.set_password(password)
        with transaction.atomic():
            user.save()
    except IntegrityError:
        return JsonResponse({'error': 'That username is already registered.'}, status=409)
    except ValidationError as exc:
        return JsonResponse({'error': ' '.join(exc.messages)}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid registration data.'}, status=400)
    login(request, user)
    return JsonResponse(identity(user), status=201)
