from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model"""
    
    list_display = [
        'name',
        'document_type',
        'file_size_mb',
        'file_extension',
        'processed',
        'uploaded_at',
    ]
    list_filter = ['document_type', 'processed', 'uploaded_at']
    search_fields = ['name']
    readonly_fields = ['file_size', 'uploaded_at', 'processed_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('name', 'document_type', 'file')
        }),
        ('Status', {
            'fields': ('processed', 'processed_at', 'file_size', 'uploaded_at')
        }),
        ('Content', {
            'fields': ('extracted_text', 'metadata'),
            'classes': ('collapse',)
        }),
    )

