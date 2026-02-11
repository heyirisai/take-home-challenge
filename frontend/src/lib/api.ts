import type { Document, RFPDocument, PaginatedResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API error ${response.status}: ${error}`);
    }

    return response.json();
  }

  // --- Documents ---

  async getDocuments(): Promise<PaginatedResponse<Document>> {
    return this.request("/documents/");
  }

  async getDocument(id: number): Promise<Document> {
    return this.request(`/documents/${id}/`);
  }

  async createDocument(
    data: Pick<Document, "title" | "content"> & { file_name?: string }
  ): Promise<Document> {
    return this.request("/documents/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async deleteDocument(id: number): Promise<void> {
    await this.request(`/documents/${id}/`, { method: "DELETE" });
  }

  // --- RFP Documents ---

  async getRFPDocuments(): Promise<PaginatedResponse<RFPDocument>> {
    return this.request("/rfp-documents/");
  }

  async getRFPDocument(id: number): Promise<RFPDocument> {
    return this.request(`/rfp-documents/${id}/`);
  }

  async createRFPDocument(
    data: Pick<RFPDocument, "title" | "content"> & { file_name?: string }
  ): Promise<RFPDocument> {
    return this.request("/rfp-documents/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async deleteRFPDocument(id: number): Promise<void> {
    await this.request(`/rfp-documents/${id}/`, { method: "DELETE" });
  }

  // --- TODO: Add methods for your Question and Answer endpoints ---
  // async getQuestions(rfpId: number): Promise<PaginatedResponse<Question>> { ... }
  // async generateAnswers(rfpId: number): Promise<void> { ... }
  // async getAnswers(rfpId: number): Promise<PaginatedResponse<Answer>> { ... }
  // async updateAnswer(id: number, data: Partial<Answer>): Promise<Answer> { ... }
}

export const api = new ApiClient(API_BASE);
