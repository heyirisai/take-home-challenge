export default function RFPPage() {
  // TODO: Implement the RFP upload and question extraction page
  //
  // Suggested features:
  // - Upload an RFP document (POST /api/rfp-documents/)
  // - List previously uploaded RFPs
  // - Show extracted questions from the selected RFP
  // - Trigger answer generation for all questions
  //
  // The FileUpload component is available at @/components/ui/FileUpload
  // The API client is available at @/lib/api

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">RFP Documents</h1>
        <p className="mt-2 text-gray-600">
          Upload RFP documents and extract questions for answer generation.
        </p>
      </div>

      <div className="rounded-lg border border-dashed border-gray-300 bg-white p-12 text-center">
        <p className="text-gray-500">
          RFP upload and question extraction UI goes here. Check the TODO
          comments in this file to get started.
        </p>
      </div>
    </div>
  );
}
