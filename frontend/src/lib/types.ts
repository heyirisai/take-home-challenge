/** Matches the Django Document model */
export interface Document {
  id: number;
  title: string;
  content: string;
  file_name: string;
  uploaded_at: string;
}

/** Matches the Django RFPDocument model */
export interface RFPDocument {
  id: number;
  title: string;
  content: string;
  file_name: string;
  uploaded_at: string;
}

// ---------------------------------------------------------------------------
// TODO: Add TypeScript interfaces for your Question and Answer models
// once you define them in Django. For example:
//
// export interface Question {
//   id: number;
//   rfp_document: number;
//   text: string;
//   order: number;
// }
//
// export interface Answer {
//   id: number;
//   question: number;
//   content: string;
//   status: "draft" | "approved" | "rejected";
//   confidence_score: number | null;
//   source_documents: number[];
//   created_at: string;
// }
// ---------------------------------------------------------------------------

/** Paginated response from DRF */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
