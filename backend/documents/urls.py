from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"documents", views.DocumentViewSet)
router.register(r"rfp-documents", views.RFPDocumentViewSet)

# TODO: Register additional viewsets here as you build them
# router.register(r"questions", views.QuestionViewSet)
# router.register(r"answers", views.AnswerViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
