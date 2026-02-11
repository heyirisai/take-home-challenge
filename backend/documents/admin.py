from django.contrib import admin

from .models import Document, RFPDocument


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "file_name", "uploaded_at"]
    search_fields = ["title", "content"]


@admin.register(RFPDocument)
class RFPDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "file_name", "uploaded_at"]
    search_fields = ["title", "content"]


# TODO: Register your Question and Answer models here
