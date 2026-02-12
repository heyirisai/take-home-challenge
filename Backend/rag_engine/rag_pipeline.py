"""
RAG Engine for answer generation
Uses OpenAI and vector search to generate contextual answers
"""

import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from openai import OpenAI

from .vector_store import get_vector_store
from .document_extractor import DocumentExtractor

logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval-Augmented Generation engine"""
    
    def __init__(self):
        """Initialize RAG engine with OpenAI client"""
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            logger.warning("OPENAI_API_KEY not configured")
        
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.vector_store = get_vector_store()
        self.model = "gpt-4o-mini"  # or gpt-4 for better quality
    
    def extract_questions_from_rfp(self, rfp_text: str) -> List[Dict[str, str]]:
        """
        Extract questions from RFP document using LLM
        
        Args:
            rfp_text: Text content of RFP document
            
        Returns:
            List of questions with IDs
        """
        if not self.client:
            logger.error("OpenAI client not initialized - attempting fallback extraction")
            return self._fallback_question_extraction(rfp_text)
        
        try:
            prompt = f"""You are an expert at analyzing RFP (Request for Proposal) documents.
Extract all questions from the following RFP document. Return only the questions, one per line.
Focus on actual questions that require detailed answers, not simple yes/no questions.

RFP Document:
{rfp_text[:8000]}

Return the questions in this exact format:
1. [First question]
2. [Second question]
3. [Third question]
..."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing RFP documents and extracting questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"LLM response: {content[:500]}...")
            
            # Parse questions
            questions = []
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Remove numbering (1., 2., etc.)
                if line and line[0].isdigit() and '.' in line[:5]:
                    line = line.split('.', 1)[1].strip()
                
                if line and len(line) > 10:  # Filter out very short lines
                    questions.append({
                        'id': f'q_{len(questions) + 1}',
                        'question': line
                    })
            
            logger.info(f"Extracted {len(questions)} questions from RFP using LLM")
            
            # Fallback if LLM extraction failed
            if not questions:
                logger.warning("LLM extraction returned no questions, trying fallback")
                return self._fallback_question_extraction(rfp_text)
                
            return questions
            
        except Exception as e:
            logger.error(f"Error extracting questions with LLM: {str(e)}")
            return self._fallback_question_extraction(rfp_text)
    
    def _fallback_question_extraction(self, text: str) -> List[Dict[str, str]]:
        """
        Fallback method to extract questions using regex patterns
        """
        import re
        questions = []
        
        # Pattern 1: Lines ending with question marks
        question_lines = [line.strip() for line in text.split('\n') if line.strip().endswith('?')]
        
        # Pattern 2: Numbered items (common in RFPs)
        numbered_pattern = r'^\s*(\d+[\).\s]+)(.+?)(?=\n\s*\d+[\).\s]+|\Z)'
        numbered_items = re.findall(numbered_pattern, text, re.MULTILINE | re.DOTALL)
        
        # Combine both patterns
        all_potential_questions = question_lines + [item[1].strip() for item in numbered_items]
        
        # Deduplicate and filter
        seen = set()
        for q in all_potential_questions:
            q = q.strip()
            if q and len(q) > 10 and q not in seen:  # Minimum length filter
                seen.add(q)
                questions.append({
                    'id': f'q_{len(questions) + 1}',
                    'question': q
                })
        
        logger.info(f"Fallback extraction found {len(questions)} potential questions")
        return questions[:50]  # Limit to 50 questions
    
    def generate_answer(
        self,
        question: str,
        n_context_chunks: int = 5
    ) -> Dict[str, Any]:
        """
        Generate answer for a question using RAG
        
        Args:
            question: Question to answer
            n_context_chunks: Number of relevant document chunks to retrieve
            
        Returns:
            Dictionary with answer, confidence, and sources
        """
        logger.info(f"[RAG] Generating answer for: {question[:100]}...")
        
        if not self.client:
            logger.error("[RAG] OpenAI client not initialized")
            return {
                'answer': 'Error: OpenAI API key not configured',
                'confidence': 0.0,
                'sources': []
            }
        
        try:
            # 1. Retrieve relevant context from vector store
            logger.info(f"[RAG] Searching vector store for {n_context_chunks} relevant chunks...")
            search_results = self.vector_store.search(
                query=question,
                n_results=n_context_chunks
            )
            
            logger.info(f"[RAG] Found {len(search_results)} relevant chunks")
            
            if not search_results:
                logger.warning("[RAG] No relevant information found in knowledge base")
                return {
                    'answer': 'No relevant information found in the knowledge base.',
                    'confidence': 0.0,
                    'sources': []
                }
            
            # 2. Build context from search results
            context_parts = []
            sources = []
            for i, result in enumerate(search_results):
                context_parts.append(f"[Source {i+1}]: {result['document']}")
                # ChromaDB uses cosine distance (0 = identical, 2 = opposite)
                # Convert to similarity score (0-1, where 1 is most similar)
                distance = result['distance'] if result['distance'] else 1.0
                # Cosine distance ranges from 0 to 2, convert to similarity 0-1
                similarity = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
                logger.info(f"[RAG] Source {i+1}: distance={distance:.4f}, similarity={similarity:.4f}")
                sources.append({
                    'document_id': result['metadata'].get('document_id'),
                    'chunk_index': result['metadata'].get('chunk_index'),
                    'relevance_score': similarity
                })
            
            context = '\n\n'.join(context_parts)
            
            # 3. Generate answer using LLM
            prompt = f"""You are an expert at answering RFP questions based on company knowledge.

Use the following context from company documents to answer the question. Be specific and cite relevant details from the context.

Context:
{context}

Question: {question}

Instructions:
- Provide a comprehensive, professional answer
- Use specific information from the context
- If the context doesn't fully answer the question, state what information is available
- Keep the answer focused and relevant
- Write in a professional tone suitable for an RFP response

Answer:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at writing professional RFP responses based on company documentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            
            # 4. Calculate confidence score
            # Based on average relevance of retrieved sources
            avg_relevance = sum(s['relevance_score'] for s in sources) / len(sources) if sources else 0
            logger.info(f"[RAG] Average relevance score: {avg_relevance:.4f}")
            logger.info(f"[RAG] Individual relevance scores: {[s['relevance_score'] for s in sources]}")
            
            # Scale confidence: 
            # - High relevance (0.8-1.0) -> 85-95% confidence
            # - Medium relevance (0.6-0.8) -> 70-85% confidence  
            # - Low relevance (0.4-0.6) -> 55-70% confidence
            # - Very low (<0.4) -> 40-55% confidence
            if avg_relevance >= 0.8:
                confidence = 0.85 + (avg_relevance - 0.8) * 0.5  # 85-95%
            elif avg_relevance >= 0.6:
                confidence = 0.70 + (avg_relevance - 0.6) * 0.75  # 70-85%
            elif avg_relevance >= 0.4:
                confidence = 0.55 + (avg_relevance - 0.4) * 0.75  # 55-70%
            else:
                confidence = 0.40 + avg_relevance * 0.375  # 40-55%
            
            # Ensure confidence is in valid range
            confidence = max(0.4, min(0.95, confidence))
            logger.info(f"[RAG] Final confidence score: {confidence:.2f} ({confidence*100:.0f}%)")
            
            return {
                'answer': answer,
                'confidence': round(confidence, 2),
                'sources': sources[:3]  # Return top 3 sources
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                'answer': f'Error generating answer: {str(e)}',
                'confidence': 0.0,
                'sources': []
            }
    
    def process_document_for_rag(self, document_path: str, document_id: int) -> bool:
        """
        Process a document and add it to the vector store
        
        Args:
            document_path: Path to document file
            document_id: Database ID of the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # 1. Extract text
            text = DocumentExtractor.extract_text(document_path)
            if not text:
                logger.error(f"Failed to extract text from {document_path}")
                return False
            
            # 2. Chunk text
            chunk_size = getattr(settings, 'CHUNK_SIZE', 1000)
            chunk_overlap = getattr(settings, 'CHUNK_OVERLAP', 200)
            chunks = DocumentExtractor.chunk_text(text, chunk_size, chunk_overlap)
            
            if not chunks:
                logger.error(f"Failed to chunk text from {document_path}")
                return False
            
            # 3. Add to vector store
            success = self.vector_store.add_document(
                document_id=document_id,
                text_chunks=chunks,
                metadata={'source': document_path}
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing document for RAG: {str(e)}")
            return False


# Singleton instance
_rag_engine_instance = None


def get_rag_engine() -> RAGEngine:
    """Get or create RAG engine singleton instance"""
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance
