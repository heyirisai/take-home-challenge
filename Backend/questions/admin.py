from django.contrib import admin
from .models import Question, Answer


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for Question model"""
    
    list_display = ['question_number', 'question_text_short', 'rfp_document', 'extracted_at']
    list_filter = ['rfp_document', 'extracted_at']
    search_fields = ['question_text']
    ordering = ['rfp_document', 'question_number']
    
    def question_text_short(self, obj):
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Admin interface for Answer model"""
    
    list_display = ['question_short', 'confidence_score', 'edited', 'generated_at']
    list_filter = ['edited', 'generated_at']
    search_fields = ['question__question_text', 'answer_text']
    readonly_fields = ['generated_at', 'source_documents']
    
    fieldsets = (
        ('Question', {
            'fields': ('question',)
        }),
        ('Answer', {
            'fields': ('answer_text', 'confidence_score')
        }),
        ('Metadata', {
            'fields': ('source_documents', 'generated_at', 'edited', 'edited_at')
        }),
    )
    
    def question_short(self, obj):
        return obj.question.question_text[:60] + '...'
    question_short.short_description = 'Question'

