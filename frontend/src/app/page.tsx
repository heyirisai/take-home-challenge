import { Card } from "@/components/ui/Card";

export default function HomePage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">
          RFP Answer Generator
        </h1>
        <p className="mt-2 text-gray-600">
          Upload company documents, import RFP questions, and generate
          AI-powered answers.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Card
          title="1. Knowledge Base"
          description="Upload company documents that will be used to answer RFP questions. Supports PDF, DOCX, and TXT files."
          href="/documents"
          linkText="Manage Documents"
        />
        <Card
          title="2. RFP Documents"
          description="Upload an RFP document to extract questions. The system will parse and identify individual questions."
          href="/rfp"
          linkText="Upload RFP"
        />
        <Card
          title="3. Review Answers"
          description="Review AI-generated answers, edit them, and export the final responses for your RFP submission."
          href="/answers"
          linkText="View Answers"
        />
      </div>
    </div>
  );
}
