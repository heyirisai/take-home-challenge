export default function AnswersPage() {
  // TODO: Implement the answer review and management page
  //
  // Suggested features:
  // - List questions with their generated answers
  // - Show answer status (pending, generating, complete, error)
  // - Allow editing/approving answers
  // - Show source documents used for each answer
  // - Show confidence scores
  // - Export final answers
  //
  // The API client is available at @/lib/api

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Review Answers</h1>
        <p className="mt-2 text-gray-600">
          Review, edit, and approve AI-generated answers to RFP questions.
        </p>
      </div>

      <div className="rounded-lg border border-dashed border-gray-300 bg-white p-12 text-center">
        <p className="text-gray-500">
          Answer review UI goes here. Check the TODO comments in this file to
          get started.
        </p>
      </div>
    </div>
  );
}
