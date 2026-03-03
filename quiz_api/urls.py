from django.urls import path
from . import views
from .views import get_active_session
from rest_framework.routers import DefaultRouter
from .views import TeamViewSet

router = DefaultRouter()
router.register(r"teams", TeamViewSet, basename="team")

urlpatterns = [
    path("auth/admin-login/", views.admin_login),
    path("active-session/", get_active_session),
    path("session/active/", views.ActiveSessionView),
]

urlpatterns += router.urls