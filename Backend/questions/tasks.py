from celery import shared_task, current_task, group, chord, chain
from django.utils import timezone
from django.core.cache import cache
import logging

from .models import Question, Answer, ProcessingTask
from documents.models import Document
from rag_engine.rag_pipeline import get_rag_engine
from rag_engine.document_extractor import DocumentExtractor

logger = logging.getLogger(__name__)


# ============= DOCUMENT PROCESSING TASKS =============

@shared_task(bind=True, max_retries=3)
def process_knowledge_base_document(self, document_id):
    """
    Background task to process a knowledge base document
    
    Args:
        document_id: ID of the document to process
    """
    try:
        logger.info(f"[Celery] Starting document processing for ID {document_id}")
        
        document = Document.objects.get(id=document_id, document_type='knowledge_base')
        
        if document.processed:
            logger.info(f"[Celery] Document {document_id} already processed")
            return {'status': 'already_processed', 'document_id': document_id}
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 'Processing document', 'total': 100, 'percent': 10}
        )
        
        # Process document
        rag_engine = get_rag_engine()
        success = rag_engine.process_document_for_rag(document.file.path, document.id)
        
        if success:
            document.processed = True
            document.processed_at = timezone.now()
            document.save()
            
            logger.info(f"[Celery] ✓ Document {document_id} processed successfully")
            return {'status': 'success', 'document_id': document_id}
        else:
            raise Exception(f"Failed to process document {document_id}")
            
    except self.MaxRetriesExceededError:
        logger.error(f"[Celery] Max retries exceeded for document {document_id}")
        return {'status': 'failed', 'document_id': document_id, 'reason': 'max_retries'}
    except Exception as exc:
        logger.error(f"[Celery] Error processing document: {str(exc)}")
        # Retry after 60 seconds with exponential backoff
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True)
def extract_questions_from_rfp(self, rfp_document_id, task_id):
    """
    Background task to extract questions from RFP
    
    Args:
        rfp_document_id: ID of the RFP document
        task_id: ID of the ProcessingTask for progress tracking
    """
    try:
        task = ProcessingTask.objects.get(task_id=task_id)
        task.status = 'processing'
        task.current_step = 'Extracting questions from RFP'
        task.progress = 40
        task.save()
        
        logger.info(f"[Celery Task {task_id}] Extracting questions from RFP {rfp_document_id}")
        
        # Update Celery task state
        self.update_state(state='PROGRESS', meta={
            'step': 'Extracting questions',
            'progress': 40,
            'task_id': task_id
        })
        
        rfp_doc = Document.objects.get(id=rfp_document_id, document_type='rfp')
        text = DocumentExtractor.extract_text(rfp_doc.file.path)
        
        if not text:
            raise Exception('Failed to extract text from RFP document')
        
        rag_engine = get_rag_engine()
        extracted_questions = rag_engine.extract_questions_from_rfp(text)
        
        if not extracted_questions:
            raise Exception('No questions found in RFP document')
        
        # Clear existing questions
        Question.objects.filter(rfp_document=rfp_doc).delete()
        
        # Create new questions
        created_questions = []
        for i, q in enumerate(extracted_questions, 1):
            question = Question.objects.create(
                rfp_document=rfp_doc,
                question_text=q['question'],
                question_number=i
            )
            created_questions.append(question)
        
        # Update RFP metadata
        rfp_doc.metadata['questions_extracted'] = True
        rfp_doc.metadata['question_count'] = len(created_questions)
        rfp_doc.save()
        
        logger.info(f"[Celery] ✓ Extracted {len(created_questions)} questions")
        
        return {
            'status': 'success',
            'questions_count': len(created_questions),
            'question_ids': [q.id for q in created_questions]
        }
        
    except Exception as e:
        logger.error(f"[Celery] Error extracting questions: {str(e)}")
        task.status = 'failed'
        task.error = str(e)
        task.save()
        raise


@shared_task(bind=True, max_retries=3)
def generate_answer_for_question(self, question_id, task_id, total_questions):
    """
    Background task to generate answer for a single question
    
    Args:
        question_id: ID of the question
        task_id: ID of the ProcessingTask for progress tracking
        total_questions: Total number of questions being processed
    """
    try:
        question = Question.objects.get(id=question_id)
        
        logger.info(f"[Celery Task {task_id}] Generating answer for question {question_id}")
        
        rag_engine = get_rag_engine()
        result = rag_engine.generate_answer(question.question_text)
        
        # Save answer to database
        answer, created = Answer.objects.update_or_create(
            question=question,
            defaults={
                'answer_text': result['answer'],
                'confidence_score': result['confidence'],
                'source_documents': result['sources'],
                'generated_at': timezone.now()
            }
        )
        
        # Update progress incrementally
        try:
            # Count completed answers so far
            completed_count = Answer.objects.filter(
                question__rfp_document=question.rfp_document
            ).count()
            
            # Calculate progress (50% to 95% range for answer generation)
            progress = 50 + int((completed_count / total_questions) * 45)
            
            task_obj = ProcessingTask.objects.get(task_id=task_id)
            task_obj.progress = progress
            task_obj.current_step = f'Generated {completed_count}/{total_questions} answers'
            task_obj.save()
            
            logger.info(f"[Celery] ✓ Answer {completed_count}/{total_questions} generated for question {question_id} (confidence: {result['confidence']:.2f})")
        except Exception as e:
            logger.warning(f"[Celery] Could not update progress: {str(e)}")
        
        return {
            'status': 'success',
            'answer_id': answer.id,
            'question_id': question_id,
            'confidence': result['confidence']
        }
        
    except self.MaxRetriesExceededError:
        logger.error(f"[Celery] Max retries exceeded for question {question_id}")
        raise
    except Exception as exc:
        logger.error(f"[Celery] Error generating answer: {str(exc)}")
        raise self.retry(exc=exc, countdown=30, max_retries=3)


@shared_task
def process_kb_documents_step(kb_ids, task_id):
    """
    Step 1: Process knowledge base documents
    Returns list of processed doc IDs
    """
    if not kb_ids:
        return []
    
    task = ProcessingTask.objects.get(task_id=task_id)
    task.current_step = f'Processing {len(kb_ids)} knowledge base documents'
    task.progress = 10
    task.save()
    
    logger.info(f"[Celery] Processing {len(kb_ids)} KB documents")
    
    processed = []
    for doc_id in kb_ids:
        try:
            doc = Document.objects.get(id=doc_id, document_type='knowledge_base')
            if not doc.processed:
                rag_engine = get_rag_engine()
                success = rag_engine.process_document_for_rag(doc.file.path, doc.id)
                if success:
                    doc.processed = True
                    doc.processed_at = timezone.now()
                    doc.save()
                    processed.append(doc_id)
            else:
                processed.append(doc_id)
        except Exception as e:
            logger.error(f"[Celery] Error processing doc {doc_id}: {str(e)}")
    
    return processed


@shared_task
def extract_and_generate_step(kb_results, rfp_document_id, task_id, generate_answers=True):
    """
    Step 2: Extract questions and trigger answer generation
    Args:
        kb_results: Results from KB processing (ignored, just for chaining)
        rfp_document_id: ID of RFP document
        task_id: ProcessingTask ID
        generate_answers: Whether to generate answers
    """
    try:
        task = ProcessingTask.objects.get(task_id=task_id)
        task.current_step = 'Extracting questions from RFP'
        task.progress = 40
        task.save()
        
        logger.info(f"[Celery] Extracting questions from RFP {rfp_document_id}")
        
        rfp_doc = Document.objects.get(id=rfp_document_id, document_type='rfp')
        text = DocumentExtractor.extract_text(rfp_doc.file.path)
        
        if not text:
            raise Exception('Failed to extract text from RFP document')
        
        rag_engine = get_rag_engine()
        extracted_questions = rag_engine.extract_questions_from_rfp(text)
        
        if not extracted_questions:
            raise Exception('No questions found in RFP document')
        
        # Clear existing questions
        Question.objects.filter(rfp_document=rfp_doc).delete()
        
        # Create new questions
        question_ids = []
        for i, q in enumerate(extracted_questions, 1):
            question = Question.objects.create(
                rfp_document=rfp_doc,
                question_text=q['question'],
                question_number=i
            )
            question_ids.append(question.id)
        
        # Update RFP metadata
        rfp_doc.metadata['questions_extracted'] = True
        rfp_doc.metadata['question_count'] = len(question_ids)
        rfp_doc.save()
        
        task.progress = 50
        task.save()
        
        logger.info(f"[Celery] ✓ Extracted {len(question_ids)} questions")
        
        # Trigger answer generation if requested
        if generate_answers and question_ids:
            total = len(question_ids)
            task.current_step = f'Generating answers for {total} questions'
            task.save()
            
            logger.info(f"[Celery] Starting parallel answer generation for {total} questions")
            
            # Use chord to process all answers in parallel and collect results
            callback = collect_answers_results.s(task_id, rfp_document_id, total)
            header = group(
                generate_answer_for_question.s(q_id, task_id, total) for q_id in question_ids
            )
            chord(header)(callback)
        else:
            # No answer generation, mark as complete
            finalize_task(task_id, rfp_document_id, question_ids, [])
        
        return question_ids
        
    except Exception as e:
        logger.error(f"[Celery] Error in extract_and_generate_step: {str(e)}")
        task = ProcessingTask.objects.get(task_id=task_id)
        task.status = 'failed'
        task.error = str(e)
        task.save()
        raise


@shared_task
def collect_answers_results(results, task_id, rfp_document_id, total_questions):
    """
    Callback task that collects all answer results
    Called after all generate_answer_for_question tasks complete
    """
    logger.info(f"[Celery] Collecting results for {len(results)} answers")
    
    answers_data = []
    for result in results:
        if result and result.get('status') == 'success':
            try:
                answer = Answer.objects.get(id=result['answer_id'])
                answers_data.append({
                    'id': answer.id,
                    'question': answer.question.id,
                    'question_text': answer.question.question_text,
                    'question_number': answer.question.question_number,
                    'answer_text': answer.answer_text,
                    'confidence_score': answer.confidence_score,
                    'source_documents': answer.source_documents,
                    'generated_at': answer.generated_at.isoformat(),
                    'edited': answer.edited,
                    'edited_at': answer.edited_at.isoformat() if answer.edited_at else None
                })
            except Answer.DoesNotExist:
                logger.warning(f"[Celery] Answer {result['answer_id']} not found")
    
    # Get question IDs from the RFP
    rfp_doc = Document.objects.get(id=rfp_document_id, document_type='rfp')
    question_ids = list(Question.objects.filter(rfp_document=rfp_doc).values_list('id', flat=True))
    
    finalize_task(task_id, rfp_document_id, question_ids, answers_data)
    
    return {'status': 'success', 'answers_count': len(answers_data)}


def finalize_task(task_id, rfp_document_id, question_ids, answers_data):
    """
    Helper function to mark task as complete
    """
    task = ProcessingTask.objects.get(task_id=task_id)
    task.status = 'completed'
    task.progress = 100
    task.current_step = 'Processing complete'
    task.result = {
        'rfp_document_id': rfp_document_id,
        'questions_count': len(question_ids),
        'answers_count': len(answers_data),
        'answers': answers_data
    }
    task.save()
    
    logger.info(f"[Celery] ✓ Task {task_id} completed successfully")


# ============= UTILITY TASKS =============

@shared_task
def clean_expired_tasks():
    """
    Clean up old processing tasks (runs daily via Celery Beat)
    """
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=7)
    deleted_count, _ = ProcessingTask.objects.filter(
        created_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"[Celery] Cleaned {deleted_count} expired tasks")
    return {'deleted': deleted_count}


@shared_task
def get_task_progress(task_id):
    """
    Get detailed progress info for a Celery task
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    
    return {
        'task_id': task_id,
        'state': result.state,
        'current': result.info.get('current') if isinstance(result.info, dict) else None,
        'total': result.info.get('total') if isinstance(result.info, dict) else None,
    }
