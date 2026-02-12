/**
 * API Service for RFP Answer Generator
 * Handles all communication with Django backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '180000') // 3 minutes for AI processing

// Types
export interface Document {
  id: number
  name: string
  document_type: 'knowledge_base' | 'rfp'
  file: string
  file_url: string
  file_size: number
  file_size_mb: number
  file_extension: string
  uploaded_at: string
  processed: boolean
  processed_at: string | null
  metadata: Record<string, any>
}

export interface DocumentUploadResponse {
  id: number
  name: string
  document_type: string
  file_url: string
  file_size_mb: number
}

export interface DocumentStats {
  total_documents: number
  knowledge_base_documents: number
  rfp_documents: number
  processed_documents: number
  pending_documents: number
}

export interface ApiError {
  error?: string
  detail?: string
  [key: string]: any
}

export interface Question {
  id: number
  rfp_document: number
  question_text: string
  question_number: number
  extracted_at: string
}

export interface Answer {
  id: number
  question: number
  question_text: string
  question_number: number
  answer_text: string
  confidence_score: number
  source_documents: Array<{
    document_id: number
    chunk_index: number
    relevance_score: number
  }>
  generated_at: string
  edited: boolean
  edited_at: string | null
}

export interface ProcessRFPResponse {
  rfp_document_id: number
  questions: {
    rfp_document_id: number
    questions_count: number
    questions: Question[]
  }
  answers: {
    answers_count: number
    answers: Array<{
      id: number
      question_id: number
      question: string
      answer: string
      confidence: number
      sources: Array<{
        document_id: number
        chunk_index: number
        relevance_score: number
      }>
    }>
  }
}

export interface ProcessRFPStartResponse {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  message: string
}

export interface TaskStatusResponse {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number // 0-100
  current_step: string
  created_at: string
  updated_at: string
  result?: {
    rfp_document_id: number
    questions_count: number
    answers_count: number
    answers: Answer[]
  }
  error?: string
}

export interface ExtractQuestionsResponse {
  rfp_document_id: number
  questions_count: number
  questions: Question[]
}

export interface GenerateAnswersResponse {
  answers_count: number
  answers: Array<{
    id: number | string
    question_id?: number
    question: string
    answer: string
    confidence: number
    sources: Array<{
      document_id: number
      chunk_index: number
      relevance_score: number
    }>
  }>
}

class ApiService {
  private baseUrl: string
  private timeout: number

  constructor() {
    this.baseUrl = API_BASE_URL
    this.timeout = API_TIMEOUT
  }

  /**
   * Generic fetch wrapper with error handling
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      return response
    } catch (error) {
      clearTimeout(timeoutId)
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout')
      }
      throw error
    }
  }

  /**
   * Handle API response
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        error: `HTTP ${response.status}: ${response.statusText}`,
      }))
      throw new Error(error.error || error.detail || 'API request failed')
    }
    return response.json()
  }

  // ============================================
  // DOCUMENT ENDPOINTS
  // ============================================

  /**
   * Get all documents
   * @param documentType Filter by document type (optional)
   */
  async getDocuments(documentType?: 'knowledge_base' | 'rfp'): Promise<Document[]> {
    const url = documentType
      ? `${this.baseUrl}/documents/?type=${documentType}`
      : `${this.baseUrl}/documents/`

    const response = await this.fetchWithTimeout(url)
    return this.handleResponse<Document[]>(response)
  }

  /**
   * Get a single document by ID
   */
  async getDocument(id: number): Promise<Document> {
    const response = await this.fetchWithTimeout(`${this.baseUrl}/documents/${id}/`)
    return this.handleResponse<Document>(response)
  }

  /**
   * Upload a document
   * @param file The file to upload
   * @param documentType Type of document (knowledge_base or rfp)
   * @param name Optional custom name (defaults to filename)
   */
  async uploadDocument(
    file: File,
    documentType: 'knowledge_base' | 'rfp' = 'knowledge_base',
    name?: string
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)
    // Always include name - use provided name or filename
    formData.append('name', name || file.name)

    const response = await this.fetchWithTimeout(`${this.baseUrl}/documents/`, {
      method: 'POST',
      body: formData,
    })

    return this.handleResponse<DocumentUploadResponse>(response)
  }

  /**
   * Upload multiple documents
   */
  async uploadDocuments(
    files: File[],
    documentType: 'knowledge_base' | 'rfp' = 'knowledge_base'
  ): Promise<DocumentUploadResponse[]> {
    const uploadPromises = files.map((file) =>
      this.uploadDocument(file, documentType)
    )
    return Promise.all(uploadPromises)
  }

  /**
   * Delete a document
   */
  async deleteDocument(id: number): Promise<{ message: string }> {
    const response = await this.fetchWithTimeout(`${this.baseUrl}/documents/${id}/`, {
      method: 'DELETE',
    })
    return this.handleResponse<{ message: string }>(response)
  }

  /**
   * Get document statistics
   */
  async getDocumentStats(): Promise<DocumentStats> {
    const response = await this.fetchWithTimeout(`${this.baseUrl}/documents/stats/`)
    return this.handleResponse<DocumentStats>(response)
  }

  /**
   * Mark document as processed
   */
  async markDocumentProcessed(id: number): Promise<Document> {
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/documents/${id}/mark_processed/`,
      {
        method: 'POST',
      }
    )
    return this.handleResponse<Document>(response)
  }

  // ============================================
  // QUESTION & ANSWER ENDPOINTS
  // ============================================

  /**
   * Extract questions from an RFP document
   * @param rfpDocumentId ID of the RFP document
   */
  async extractQuestions(rfpDocumentId: number): Promise<ExtractQuestionsResponse> {
    const response = await this.fetchWithTimeout(`${this.baseUrl}/questions/extract/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ rfp_document_id: rfpDocumentId }),
    })
    return this.handleResponse<ExtractQuestionsResponse>(response)
  }

  /**
   * Generate answers for questions using RAG
   * @param rfpDocumentId ID of the RFP document (generates for all questions)
   * @param questionIds Optional specific question IDs
   */
  async generateAnswers(
    rfpDocumentId?: number,
    questionIds?: number[]
  ): Promise<GenerateAnswersResponse> {
    const body: any = {}
    
    if (rfpDocumentId) {
      body.rfp_document_id = rfpDocumentId
    }
    if (questionIds) {
      body.question_ids = questionIds
    }

    const response = await this.fetchWithTimeout(`${this.baseUrl}/answers/generate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })
    return this.handleResponse<GenerateAnswersResponse>(response)
  }

  /**
   * Process complete RFP workflow: extract questions and generate answers (async)
   * Returns task_id immediately for polling
   * @param rfpDocumentId ID of the RFP document
   * @param knowledgeBaseIds Optional IDs of knowledge base documents
   * @param generateAnswers Whether to generate answers (default: true)
   */
  async processRFP(
    rfpDocumentId: number,
    knowledgeBaseIds?: number[],
    generateAnswers: boolean = true
  ): Promise<ProcessRFPStartResponse> {
    const body: any = {
      rfp_document_id: rfpDocumentId,
      generate_answers: generateAnswers,
    }
    
    if (knowledgeBaseIds && knowledgeBaseIds.length > 0) {
      body.knowledge_base_ids = knowledgeBaseIds
    }

    const response = await this.fetchWithTimeout(`${this.baseUrl}/process-rfp/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })
    return this.handleResponse<ProcessRFPStartResponse>(response)
  }

  /**
   * Check task status
   * @param taskId Task ID from processRFP
   */
  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/task-status/${taskId}/`
    )
    return this.handleResponse<TaskStatusResponse>(response)
  }

  /**
   * Poll task status until complete or failed
   * @param taskId Task ID from processRFP
   * @param onProgress Callback for progress updates
   * @param pollInterval Polling interval in ms (default: 2000)
   */
  async pollTaskStatus(
    taskId: string,
    onProgress?: (status: TaskStatusResponse) => void,
    pollInterval: number = 2000
  ): Promise<TaskStatusResponse> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await this.getTaskStatus(taskId)
          
          // Call progress callback if provided
          if (onProgress) {
            onProgress(status)
          }

          if (status.status === 'completed') {
            resolve(status)
          } else if (status.status === 'failed') {
            reject(new Error(status.error || 'Task failed'))
          } else {
            // Continue polling
            setTimeout(poll, pollInterval)
          }
        } catch (error) {
          reject(error)
        }
      }

      poll()
    })
  }

  /**
   * Get all questions for an RFP
   * @param rfpDocumentId Optional RFP document ID to filter
   */
  async getQuestions(rfpDocumentId?: number): Promise<Question[]> {
    const url = rfpDocumentId
      ? `${this.baseUrl}/questions/?rfp_document=${rfpDocumentId}`
      : `${this.baseUrl}/questions/`
    
    const response = await this.fetchWithTimeout(url)
    return this.handleResponse<Question[]>(response)
  }

  /**
   * Get all answers
   */
  async getAnswers(): Promise<Answer[]> {
    const response = await this.fetchWithTimeout(`${this.baseUrl}/answers/`)
    return this.handleResponse<Answer[]>(response)
  }

  /**
   * Edit an answer
   * @param answerId ID of the answer to edit
   * @param newAnswerText New answer text
   */
  async editAnswer(answerId: number, newAnswerText: string): Promise<Answer> {
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/answers/${answerId}/edit/`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ answer_text: newAnswerText }),
      }
    )
    return this.handleResponse<Answer>(response)
  }
}

// Export singleton instance
export const apiService = new ApiService()

// Export for direct use
export default apiService
