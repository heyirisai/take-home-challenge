from django.db import models
from django.core.validators import FileExtensionValidator
import os


def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    # Organize by document type
    doc_type = instance.document_type.lower()
    return f'documents/{doc_type}/{filename}'


class Document(models.Model):
    """Model for storing uploaded documents"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('knowledge_base', 'Knowledge Base'),
        ('rfp', 'RFP Document'),
    ]
    
    name = models.CharField(max_length=255)
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default='knowledge_base'
    )
    file = models.FileField(
        upload_to=document_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'docx', 'txt', 'doc']
            )
        ]
    )
    file_size = models.IntegerField(help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Extracted content
    extracted_text = models.TextField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['-uploaded_at']),
            models.Index(fields=['document_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete the file from storage when model is deleted
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)
    
    @property
    def file_extension(self):
        """Get file extension"""
        return os.path.splitext(self.file.name)[1].lstrip('.')
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)

