from django.urls import path
from . import views
from .views import get_active_session

urlpatterns = [
    path("auth/admin-login/", views.admin_login),
    path("active-session/", get_active_session),
]