from rest_framework import serializers
from .models import Question, Answer


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Question model"""
    
    class Meta:
        model = Question
        fields = [
            'id',
            'rfp_document',
            'question_text',
            'question_number',
            'extracted_at',
        ]
        read_only_fields = ['id', 'extracted_at']


class AnswerSerializer(serializers.ModelSerializer):
    """Serializer for Answer model"""
    
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    question_number = serializers.IntegerField(source='question.question_number', read_only=True)
    
    class Meta:
        model = Answer
        fields = [
            'id',
            'question',
            'question_text',
            'question_number',
            'answer_text',
            'confidence_score',
            'source_documents',
            'generated_at',
            'edited',
            'edited_at',
        ]
        read_only_fields = ['id', 'generated_at', 'confidence_score', 'source_documents']


class QuestionAnswerSerializer(serializers.Serializer):
    """Combined serializer for question and answer"""
    
    id = serializers.CharField()
    question = serializers.CharField()
    answer = serializers.CharField(required=False)
    confidence = serializers.FloatField(required=False)
    sources = serializers.ListField(required=False)


class ProcessRFPRequestSerializer(serializers.Serializer):
    """Serializer for RFP processing request"""
    
    rfp_document_id = serializers.IntegerField()
    knowledge_base_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    generate_answers = serializers.BooleanField(default=True)


class ExtractQuestionsRequestSerializer(serializers.Serializer):
    """Serializer for question extraction request"""
    
    rfp_document_id = serializers.IntegerField()


class GenerateAnswersRequestSerializer(serializers.Serializer):
    """Serializer for answer generation request"""
    
    question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    rfp_document_id = serializers.IntegerField(required=False)
    questions_text = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
