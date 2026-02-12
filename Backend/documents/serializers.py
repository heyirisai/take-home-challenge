from rest_framework import serializers
from .models import Document
from django.conf import settings


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    
    file_extension = serializers.ReadOnlyField()
    file_size_mb = serializers.ReadOnlyField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'name',
            'document_type',
            'file',
            'file_url',
            'file_size',
            'file_size_mb',
            'file_extension',
            'uploaded_at',
            'processed',
            'processed_at',
            'metadata',
        ]
        read_only_fields = [
            'id',
            'file_size',
            'uploaded_at',
            'processed',
            'processed_at',
        ]
    
    def get_file_url(self, obj):
        """Get absolute URL for file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def validate_file(self, value):
        """Validate file size"""
        max_size = settings.MAX_UPLOAD_SIZE
        if value.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of {max_size_mb}MB"
            )
        return value
    
    def validate_name(self, value):
        """Ensure name is provided"""
        if not value or not value.strip():
            raise serializers.ValidationError("Document name is required")
        return value.strip()


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload"""
    
    file = serializers.FileField()
    name = serializers.CharField(max_length=255, required=False)
    document_type = serializers.ChoiceField(
        choices=Document.DOCUMENT_TYPE_CHOICES,
        default='knowledge_base'
    )
    
    def validate_file(self, value):
        """Validate file"""
        # Check file extension
        allowed_extensions = ['pdf', 'docx', 'txt', 'doc']
        extension = value.name.split('.')[-1].lower()
        if extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type .{extension} not supported. "
                f"Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Check file size
        max_size = settings.MAX_UPLOAD_SIZE
        if value.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of {max_size_mb}MB"
            )
        
        return value
    
    def create(self, validated_data):
        """Create document from uploaded file"""
        # Use filename as name if not provided
        if 'name' not in validated_data or not validated_data['name']:
            validated_data['name'] = validated_data['file'].name
        
        # Set file_size from uploaded file
        validated_data['file_size'] = validated_data['file'].size
        
        return Document.objects.create(**validated_data)
