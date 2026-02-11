from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"documents", views.DocumentViewSet)
router.register(r"rfp-documents", views.RFPDocumentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
