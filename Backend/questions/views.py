from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import os

# Import Celery tasks
USE_CELERY = os.getenv('USE_CELERY', 'True') == 'True'
if USE_CELERY:
    from .tasks import process_kb_documents_step, extract_and_generate_step
    from celery import chain

from .models import Question, Answer, ProcessingTask
from .serializers import (
    QuestionSerializer,
    AnswerSerializer,
    QuestionAnswerSerializer,
    ProcessRFPRequestSerializer,
    ExtractQuestionsRequestSerializer,
    GenerateAnswersRequestSerializer
)
from documents.models import Document
from rag_engine.document_extractor import DocumentExtractor
from rag_engine.rag_pipeline import get_rag_engine

import logging

logger = logging.getLogger(__name__)


class QuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for Question operations"""
    
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    
    def get_queryset(self):
        """Filter questions by RFP document if specified"""
        queryset = Question.objects.all()
        rfp_id = self.request.query_params.get('rfp_document', None)
        
        if rfp_id:
            queryset = queryset.filter(rfp_document_id=rfp_id)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def extract(self, request):
        """Extract questions from an RFP document"""
        serializer = ExtractQuestionsRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        rfp_document_id = serializer.validated_data['rfp_document_id']
        
        try:
            # Get RFP document
            rfp_doc = get_object_or_404(Document, id=rfp_document_id, document_type='rfp')
            
            # Extract text from document
            text = DocumentExtractor.extract_text(rfp_doc.file.path)
            if not text:
                return Response(
                    {'error': 'Failed to extract text from RFP document'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Use RAG engine to extract questions
            rag_engine = get_rag_engine()
            extracted_questions = rag_engine.extract_questions_from_rfp(text)
            
            if not extracted_questions:
                return Response(
                    {'error': 'No questions found in RFP document'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Delete existing questions for this RFP
            Question.objects.filter(rfp_document=rfp_doc).delete()
            
            # Create Question objects
            created_questions = []
            for i, q in enumerate(extracted_questions, 1):
                question = Question.objects.create(
                    rfp_document=rfp_doc,
                    question_text=q['question'],
                    question_number=i
                )
                created_questions.append(question)
            
            # Update RFP document metadata
            rfp_doc.metadata['questions_extracted'] = True
            rfp_doc.metadata['question_count'] = len(created_questions)
            rfp_doc.save()
            
            # Serialize and return
            response_serializer = QuestionSerializer(created_questions, many=True)
            
            return Response({
                'rfp_document_id': rfp_document_id,
                'questions_count': len(created_questions),
                'questions': response_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error extracting questions: {str(e)}")
            return Response(
                {'error': f'Failed to extract questions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnswerViewSet(viewsets.ModelViewSet):
    """ViewSet for Answer operations"""
    
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate answers for questions using RAG"""
        logger.info("=" * 80)
        logger.info("Starting answer generation")
        logger.info(f"Request data: {request.data}")
        
        serializer = GenerateAnswersRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"Invalid request data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Validated data: {serializer.validated_data}")
        
        try:
            # Get questions to answer
            questions = []
            
            if 'question_ids' in serializer.validated_data:
                # Use existing questions
                question_ids = serializer.validated_data['question_ids']
                logger.info(f"Fetching {len(question_ids)} questions by IDs: {question_ids}")
                questions = list(Question.objects.filter(id__in=question_ids))
                logger.info(f"Found {len(questions)} questions in database")
                for q in questions:
                    logger.info(f"  - Question {q.id}: {q.question_text[:50]}...")
            elif 'rfp_document_id' in serializer.validated_data:
                # Get all questions from RFP
                rfp_id = serializer.validated_data['rfp_document_id']
                logger.info(f"Fetching questions for RFP document {rfp_id}")
                questions = list(Question.objects.filter(rfp_document_id=rfp_id))
                logger.info(f"Found {len(questions)} questions for RFP {rfp_id}")
            elif 'questions_text' in serializer.validated_data:
                # Use provided question texts (for testing)
                logger.info("Using provided question texts")
                questions = [
                    {'id': f'temp_{i}', 'question_text': q}
                    for i, q in enumerate(serializer.validated_data['questions_text'])
                ]
            
            if not questions:
                logger.error("No questions found to generate answers for")
                return Response(
                    {'error': 'No questions provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate answers
            logger.info(f"Initializing RAG engine for {len(questions)} questions")
            rag_engine = get_rag_engine()
            generated_answers = []
            
            for idx, question in enumerate(questions, 1):
                logger.info(f"\n--- Processing question {idx}/{len(questions)} ---")
                if isinstance(question, dict):
                    # Temporary question
                    question_text = question['question_text']
                    question_id = question['id']
                    is_temp = True
                    logger.info(f"Temporary question: {question_text[:100]}")
                else:
                    # Database question
                    question_text = question.question_text
                    question_id = question.id
                    is_temp = False
                    logger.info(f"Database question ID {question_id}: {question_text[:100]}")
                
                # Generate answer using RAG
                logger.info("Calling RAG engine...")
                result = rag_engine.generate_answer(question_text)
                logger.info(f"Generated answer (confidence: {result['confidence']:.2f}): {result['answer'][:100]}...")
                logger.info(f"Sources: {len(result['sources'])} documents")
                
                if not is_temp:
                    # Save to database
                    logger.info(f"Saving answer to database for question {question_id}")
                    try:
                        answer, created = Answer.objects.update_or_create(
                            question=question,
                            defaults={
                                'answer_text': result['answer'],
                                'confidence_score': result['confidence'],
                                'source_documents': result['sources'],
                                'generated_at': timezone.now()
                            }
                        )
                        logger.info(f"Answer {'created' if created else 'updated'} with ID {answer.id}")
                    except Exception as db_error:
                        logger.error(f"Database error saving answer: {str(db_error)}")
                        logger.error(f"Question object: {question}, ID: {question_id}")
                        raise
                    
                    generated_answers.append({
                        'id': answer.id,
                        'question': question.id,
                        'question_text': question_text,
                        'question_number': question.question_number,
                        'answer_text': result['answer'],
                        'confidence_score': result['confidence'],
                        'source_documents': result['sources'],
                        'generated_at': answer.generated_at.isoformat(),
                        'edited': answer.edited,
                        'edited_at': answer.edited_at.isoformat() if answer.edited_at else None
                    })
                else:
                    # Return temporary answer
                    generated_answers.append({
                        'id': question_id,
                        'question': None,
                        'question_text': question_text,
                        'question_number': 0,
                        'answer_text': result['answer'],
                        'confidence_score': result['confidence'],
                        'source_documents': result['sources'],
                        'generated_at': timezone.now().isoformat(),
                        'edited': False,
                        'edited_at': None
                    })
            
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Answer generation complete: {len(generated_answers)} answers generated")
            logger.info(f"{'=' * 80}\n")
            
            return Response({
                'answers_count': len(generated_answers),
                'answers': generated_answers
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"\n{'!' * 80}")
            logger.error(f"ERROR generating answers: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            logger.error(f"{'!' * 80}\n")
            return Response(
                {'error': f'Failed to generate answers: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['patch'])
    def edit(self, request, pk=None):
        """Edit an existing answer"""
        answer = self.get_object()
        
        new_text = request.data.get('answer_text')
        if not new_text:
            return Response(
                {'error': 'answer_text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        answer.answer_text = new_text
        answer.edited = True
        answer.edited_at = timezone.now()
        answer.save()
        
        serializer = self.get_serializer(answer)
        return Response(serializer.data)


def _process_rfp_background(task_id, rfp_document_id, kb_ids, generate_answers):
    """
    Background worker function that processes RFP asynchronously
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Get the task
        task = ProcessingTask.objects.get(task_id=task_id)
        task.status = 'processing'
        task.save()
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"BACKGROUND TASK {task_id} STARTED")
        logger.info(f"{'=' * 80}")
        
        # 1. Process knowledge base documents
        if kb_ids:
            task.current_step = f"Processing {len(kb_ids)} knowledge base documents"
            task.progress = 10
            task.save()
            
            logger.info(f"STEP 1: {task.current_step}")
            rag_engine = get_rag_engine()
            for idx, kb_id in enumerate(kb_ids, 1):
                logger.info(f"  [{idx}/{len(kb_ids)}] Processing document {kb_id}...")
                kb_doc = Document.objects.filter(id=kb_id, document_type='knowledge_base').first()
                if kb_doc and not kb_doc.processed:
                    success = rag_engine.process_document_for_rag(
                        kb_doc.file.path,
                        kb_doc.id
                    )
                    if success:
                        kb_doc.processed = True
                        kb_doc.processed_at = timezone.now()
                        kb_doc.save()
                        logger.info(f"  ✓ Document {kb_id} processed successfully")
                    else:
                        logger.warning(f"  ✗ Document {kb_id} processing failed")
                elif kb_doc:
                    logger.info(f"  ✓ Document {kb_id} already processed")
                
                # Update progress
                task.progress = 10 + int((idx / len(kb_ids)) * 30)
                task.save()
            logger.info("")
        
        # 2. Extract questions
        task.current_step = "Extracting questions from RFP"
        task.progress = 40
        task.save()
        
        logger.info("STEP 2: Extracting questions from RFP")
        rfp_doc = Document.objects.filter(id=rfp_document_id, document_type='rfp').first()
        if not rfp_doc:
            raise Exception(f"RFP document {rfp_document_id} not found")
        
        # Extract text from document
        from rag_engine.document_extractor import DocumentExtractor
        text = DocumentExtractor.extract_text(rfp_doc.file.path)
        if not text:
            raise Exception('Failed to extract text from RFP document')
        
        # Use RAG engine to extract questions
        rag_engine = get_rag_engine()
        extracted_questions = rag_engine.extract_questions_from_rfp(text)
        
        if not extracted_questions:
            raise Exception('No questions found in RFP document')
        
        # Delete existing questions for this RFP
        Question.objects.filter(rfp_document=rfp_doc).delete()
        
        # Create Question objects
        created_questions = []
        for i, q in enumerate(extracted_questions, 1):
            question = Question.objects.create(
                rfp_document=rfp_doc,
                question_text=q['question'],
                question_number=i
            )
            created_questions.append(question)
        
        # Update RFP document metadata
        rfp_doc.metadata['questions_extracted'] = True
        rfp_doc.metadata['question_count'] = len(created_questions)
        rfp_doc.save()
        
        logger.info(f"✓ Extracted {len(created_questions)} questions")
        logger.info("")
        
        task.progress = 50
        task.save()
        
        # 3. Generate answers if requested (with batch processing)
        answers_data = []
        if generate_answers:
            task.current_step = f"Generating answers for {len(created_questions)} questions"
            task.save()
            
            logger.info("STEP 3: Generating answers (BATCH MODE)")
            question_ids = [q.id for q in created_questions]
            logger.info(f"Question IDs to process: {question_ids}")
            
            rag_engine = get_rag_engine()
            
            # Batch configuration
            BATCH_SIZE = 5  # Process 5 questions concurrently
            completed_count = 0
            progress_lock = Lock()
            
            def process_single_question(question, idx):
                """Process a single question and return result"""
                nonlocal completed_count
                
                try:
                    logger.info(f"\n[Thread-{threading.current_thread().name}] Processing question {idx}/{len(created_questions)}")
                    logger.info(f"Question {question.id}: {question.question_text[:100]}")
                    
                    # Generate answer using RAG
                    result = rag_engine.generate_answer(question.question_text)
                    logger.info(f"[Thread-{threading.current_thread().name}] Generated answer (confidence: {result['confidence']:.2f})")
                    
                    # Save to database
                    answer, created_answer = Answer.objects.update_or_create(
                        question=question,
                        defaults={
                            'answer_text': result['answer'],
                            'confidence_score': result['confidence'],
                            'source_documents': result['sources'],
                            'generated_at': timezone.now()
                        }
                    )
                    
                    answer_data = {
                        'id': answer.id,
                        'question': question.id,
                        'question_text': question.question_text,
                        'question_number': question.question_number,
                        'answer_text': result['answer'],
                        'confidence_score': result['confidence'],
                        'source_documents': result['sources'],
                        'generated_at': answer.generated_at.isoformat(),
                        'edited': answer.edited,
                        'edited_at': answer.edited_at.isoformat() if answer.edited_at else None
                    }
                    
                    # Update progress (thread-safe)
                    with progress_lock:
                        completed_count += 1
                        task.refresh_from_db()
                        task.progress = 50 + int((completed_count / len(created_questions)) * 50)
                        task.current_step = f"Generated {completed_count}/{len(created_questions)} answers"
                        task.save()
                    
                    logger.info(f"[Thread-{threading.current_thread().name}] ✓ Question {idx} completed ({completed_count}/{len(created_questions)})")
                    return answer_data
                    
                except Exception as e:
                    logger.error(f"[Thread-{threading.current_thread().name}] Error processing question {question.id}: {str(e)}")
                    return None
            
            # Process questions in batches using ThreadPoolExecutor
            logger.info(f"\nProcessing {len(created_questions)} questions with batch size {BATCH_SIZE}")
            
            with ThreadPoolExecutor(max_workers=BATCH_SIZE, thread_name_prefix="QuestionWorker") as executor:
                # Submit all questions to the executor
                future_to_question = {
                    executor.submit(process_single_question, question, idx): (question, idx)
                    for idx, question in enumerate(created_questions, 1)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_question):
                    result = future.result()
                    if result:
                        answers_data.append(result)
            
            logger.info(f"\n✓ Generated {len(answers_data)} answers using batch processing")
        
        # Task complete
        task.status = 'completed'
        task.progress = 100
        task.current_step = 'Processing complete'
        task.result = {
            'rfp_document_id': rfp_document_id,
            'questions_count': len(created_questions),
            'answers_count': len(answers_data),
            'answers': answers_data
        }
        task.save()
        
        logger.info(f"{'=' * 80}")
        logger.info(f"TASK {task_id} COMPLETED SUCCESSFULLY")
        logger.info(f"{'=' * 80}\n")
        
    except Exception as e:
        logger.error(f"\n{'!' * 80}")
        logger.error(f"TASK {task_id} FAILED: {str(e)}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        logger.error(f"{'!' * 80}\n")
        
        # Update task with error
        try:
            task = ProcessingTask.objects.get(task_id=task_id)
            task.status = 'failed'
            task.error = str(e)
            task.save()
        except:
            pass


@csrf_exempt
@api_view(['POST'])
def process_rfp(request):
    """
    Start async RFP processing and return task_id immediately
    """
    logger.info("\n" + "=" * 80)
    logger.info("RFP PROCESSING REQUEST RECEIVED")
    logger.info("=" * 80)
    logger.info(f"Request data: {request.data}")
    
    serializer = ProcessRFPRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        logger.error(f"✗ Invalid request data: {serializer.errors}")
        logger.error("=" * 80 + "\n")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    rfp_document_id = serializer.validated_data['rfp_document_id']
    kb_ids = serializer.validated_data.get('knowledge_base_ids', [])
    generate_answers = serializer.validated_data.get('generate_answers', True)
    
    logger.info(f"RFP Document ID: {rfp_document_id}")
    logger.info(f"Knowledge Base IDs: {kb_ids}")
    logger.info(f"Generate Answers: {generate_answers}")
    logger.info("")
    
    try:
        # Create processing task
        task_id = str(uuid.uuid4())
        task = ProcessingTask.objects.create(
            task_id=task_id,
            rfp_document_id=rfp_document_id,
            knowledge_base_ids=kb_ids,
            status='pending',
            progress=0,
            current_step='Starting processing...'
        )
        
        logger.info(f"Created task {task_id}")
        
        # Choose processing method based on environment variable
        if USE_CELERY:
            logger.info(f"Starting Celery task chain for RFP processing")
            logger.info("=" * 80 + "\n")
            
            # Update task status
            task.status = 'processing'
            task.save()
            
            # Create task chain: KB processing -> Question extraction & Answer generation
            # Using chain to avoid blocking .get() calls
            workflow = chain(
                process_kb_documents_step.s(kb_ids, task_id),
                extract_and_generate_step.s(rfp_document_id, task_id, generate_answers)
            )
            
            # Execute the chain
            result = workflow.apply_async()
            
            logger.info(f"Celery workflow {result.id} started for ProcessingTask {task_id}")
            
            return Response({
                'task_id': task_id,
                'celery_task_id': result.id,
                'status': 'processing',
                'message': 'RFP processing started with Celery. Use task_id to check status.',
                'method': 'celery'
            }, status=status.HTTP_202_ACCEPTED)
        else:
            logger.info(f"Starting background processing thread (threading mode)")
            logger.info("=" * 80 + "\n")
            
            # Start background thread (fallback)
            thread = threading.Thread(
                target=_process_rfp_background,
                args=(task_id, rfp_document_id, kb_ids, generate_answers),
                daemon=True
            )
            thread.start()
            
            return Response({
                'task_id': task_id,
                'status': 'pending',
                'message': 'RFP processing started with threading. Use task_id to check status.',
                'method': 'threading'
            }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"\n{'!' * 80}")
        logger.error(f"ERROR starting RFP processing: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        logger.error(f"{'!' * 80}\n")
        return Response(
            {'error': f'Failed to start RFP processing: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
def task_status(request, task_id):
    """
    Check the status of an async processing task
    """
    try:
        task = ProcessingTask.objects.get(task_id=task_id)
        
        response_data = {
            'task_id': task.task_id,
            'status': task.status,
            'progress': task.progress,
            'current_step': task.current_step,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        }
        
        if task.status == 'completed' and task.result:
            response_data['result'] = task.result
        elif task.status == 'failed':
            response_data['error'] = task.error
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except ProcessingTask.DoesNotExist:
        return Response(
            {'error': 'Task not found'},
            status=status.HTTP_404_NOT_FOUND
        )
