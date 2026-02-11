export default function DocumentsPage() {
  // TODO: Implement the knowledge base document management page
  //
  // Suggested features:
  // - List all uploaded documents (fetch from GET /api/documents/)
  // - Upload new documents (POST /api/documents/ or file upload)
  // - Delete documents
  // - Show document preview/content
  //
  // The FileUpload component is available at @/components/ui/FileUpload
  // The API client is available at @/lib/api

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
        <p className="mt-2 text-gray-600">
          Upload and manage company documents used to answer RFP questions.
        </p>
      </div>

      <div className="rounded-lg border border-dashed border-gray-300 bg-white p-12 text-center">
        <p className="text-gray-500">
          Document management UI goes here. Check the TODO comments in this file
          to get started.
        </p>
      </div>
    </div>
  );
}
