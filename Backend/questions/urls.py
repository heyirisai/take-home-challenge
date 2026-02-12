from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestionViewSet, AnswerViewSet, process_rfp, task_status

router = DefaultRouter()
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'answers', AnswerViewSet, basename='answer')

urlpatterns = [
    path('', include(router.urls)),
    path('process-rfp/', process_rfp, name='process-rfp'),
    path('task-status/<str:task_id>/', task_status, name='task-status'),
]
