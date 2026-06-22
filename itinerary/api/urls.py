from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ChecklistItemViewSet,
    DayViewSet,
    RegisterView,
    StopPhotoViewSet,
    StopViewSet,
    TripCreationJobViewSet,
    TripViewSet,
    health,
)

router = DefaultRouter()
router.register("trips", TripViewSet, basename="trip")
router.register("trip-jobs", TripCreationJobViewSet, basename="trip-job")
router.register("days", DayViewSet, basename="day")
router.register("stops", StopViewSet, basename="stop")
router.register("checklist-items", ChecklistItemViewSet, basename="checklist-item")
router.register("photos", StopPhotoViewSet, basename="photo")

urlpatterns = [
    path("health/", health, name="api-health"),
    path("auth/register/", RegisterView.as_view(), name="api-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="api-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("", include(router.urls)),
]
