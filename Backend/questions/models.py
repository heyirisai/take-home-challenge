from django.db import models
from documents.models import Document


class Question(models.Model):
    """Model for RFP questions"""
    
    rfp_document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='questions',
        limit_choices_to={'document_type': 'rfp'}
    )
    question_text = models.TextField()
    question_number = models.IntegerField()
    extracted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['question_number']
        indexes = [
            models.Index(fields=['rfp_document', 'question_number']),
        ]
    
    def __str__(self):
        return f"Q{self.question_number}: {self.question_text[:50]}..."


class Answer(models.Model):
    """Model for generated answers"""
    
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name='answer'
    )
    answer_text = models.TextField()
    confidence_score = models.FloatField(default=0.0)
    source_documents = models.JSONField(default=list, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # Allow manual editing
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['question']),
        ]
    
    def __str__(self):
        return f"Answer to: {self.question.question_text[:50]}..."


class ProcessingTask(models.Model):
    """Model for tracking async RFP processing tasks"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    task_id = models.CharField(max_length=100, unique=True, db_index=True)
    rfp_document_id = models.IntegerField()
    knowledge_base_ids = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)  # 0-100
    current_step = models.CharField(max_length=200, blank=True)
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Task {self.task_id}: {self.status}"

