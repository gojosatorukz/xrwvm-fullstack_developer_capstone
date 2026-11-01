from django.urls import path
from . import views

app_name = 'djangoapp'
urlpatterns = [
    path('session', views.session_status, name='session'),
    path('login', views.login_user, name='login'),
    path('logout', views.logout_request, name='logout'),
    path('register', views.registration, name='register'),
]
