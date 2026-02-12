/**
 * Backend API Configuration
 * 
 * Update these endpoints to point to your Django backend
 * The frontend expects the following API structure:
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export const API_ENDPOINTS = {
  // Document Ingestion API
  // POST /documents/upload
  // Body: FormData with files
  // Returns: { success: boolean, document_ids: string[] }
  UPLOAD_DOCUMENTS: `${API_BASE_URL}/documents/upload`,

  // Question Extraction API
  // POST /rfp/extract-questions
  // Body: FormData with rfp_file
  // Returns: { questions: Array<{ id: string, text: string }> }
  EXTRACT_QUESTIONS: `${API_BASE_URL}/rfp/extract-questions`,

  // Answer Generation API (RAG Pipeline)
  // POST /answers/generate
  // Body: { 
  //   questions: Array<{ id: string, text: string }>,
  //   document_ids: string[],
  //   use_rag: boolean
  // }
  // Returns: { 
  //   answers: Array<{ 
  //     id: string, 
  //     question: string, 
  //     answer: string, 
  //     confidence: number,
  //     sources: string[]
  //   }>
  // }
  GENERATE_ANSWERS: `${API_BASE_URL}/answers/generate`,

  // Combined RFP Processing (optional - single endpoint for upload + extract + generate)
  // POST /rfp/process
  // Body: FormData with rfp_file and documents
  // Returns: { 
  //   questions: Array<{ id: string, question: string }>,
  //   answers: Array<{ id: string, question: string, answer: string, confidence: number }>
  // }
  PROCESS_RFP: `${API_BASE_URL}/rfp/process`,

  // Export API (optional - generate downloadable document)
  // POST /answers/export
  // Body: { answers: Answer[], format: 'pdf' | 'docx' | 'txt' }
  // Returns: Blob (file download)
  EXPORT_ANSWERS: `${API_BASE_URL}/answers/export`,
}

/**
 * Expected Django Backend Structure
 * 
 * The backend should implement the following:
 * 
 * 1. Document Ingestion Module
 *    - File upload endpoint
 *    - Text extraction from PDFs/docs
 *    - Vector embedding for semantic search
 *    - Storage in vector database (Pinecone, Milvus, etc.)
 * 
 * 2. RFP Processing Module
 *    - Extract questions from RFP using LLM
 *    - Structure questions with metadata
 * 
 * 3. RAG (Retrieval-Augmented Generation) Pipeline
 *    - Retrieve relevant documents using semantic search
 *    - Generate answers using retrieved context
 *    - Score confidence based on retrieval quality
 * 
 * 4. Response Formatting
 *    - Return structured answers with confidence scores
 *    - Track source documents for transparency
 * 
 * Stack recommendation:
 * - Django REST Framework for APIs
 * - LangChain for RAG pipeline
 * - OpenAI/Anthropic for LLM
 * - Vector DB for semantic search
 * - Celery for async processing
 * - Redis for caching
 */

export type Answer = {
  id: string
  question: string
  answer: string
  confidence: number
  sources?: string[]
}

export type Question = {
  id: string
  question: string
}
