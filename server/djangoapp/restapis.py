"""HTTP clients for the dealership and sentiment microservices."""

import os
from urllib.parse import quote
import requests
from dotenv import load_dotenv

load_dotenv()
backend_url = os.getenv("backend_url", "http://localhost:3030").rstrip("/")
sentiment_analyzer_url = os.getenv("sentiment_analyzer_url", "http://localhost:5050").rstrip("/")


class ServiceError(Exception):
    pass


def request_json(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=15, **kwargs)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ServiceError("A backend service is temporarily unavailable.") from exc


def get_request(endpoint, **kwargs):
    return request_json("GET", f'{backend_url}/{endpoint.lstrip("/")}', params=kwargs)


def analyze_review_sentiments(text):
    data = request_json("GET", f'{sentiment_analyzer_url}/analyze/{quote(text, safe="")}')
    value = data.get("sentiment")
    if value not in ("positive", "neutral", "negative"):
        raise ServiceError("Invalid sentiment service response.")
    return value


def post_review(data_dict):
    return request_json("POST", f"{backend_url}/insert_review", json=data_dict)


searchcars_url = os.getenv("searchcars_url", "http://localhost:3050").rstrip("/")


def searchcars_request(endpoint, **kwargs):
    return request_json("GET", f'{searchcars_url}/{endpoint.lstrip("/")}', params=kwargs)
