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

/** Paginated response from DRF */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
