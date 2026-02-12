import { FileText } from 'lucide-react'

interface HeaderProps {
  step: 'upload' | 'process' | 'review'
}

export default function Header({ step }: HeaderProps) {
  return (
    <header className="border-b border-border bg-card shadow-sm">
      <div className="mx-auto max-w-6xl px-4 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
            <FileText className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">RFP Answer Generator</h1>
            <p className="text-sm text-muted-foreground">Intelligent proposal response system powered by RAG</p>
          </div>
        </div>

        {/* Progress indicator */}
        <div className="mt-6 flex gap-4">
          {[
            { label: 'Upload Documents', id: 'upload' },
            { label: 'Processing', id: 'process' },
            { label: 'Review Answers', id: 'review' },
          ].map((item, idx) => (
            <div key={item.id} className="flex items-center gap-3">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full font-semibold text-sm transition-colors ${
                  step === item.id
                    ? 'bg-primary text-primary-foreground'
                    : ['upload', 'process', 'review'].indexOf(step) > idx
                      ? 'bg-secondary text-secondary-foreground'
                      : 'bg-muted text-muted-foreground'
                }`}
              >
                {idx + 1}
              </div>
              <span
                className={`text-sm font-medium ${
                  step === item.id ? 'text-foreground' : 'text-muted-foreground'
                }`}
              >
                {item.label}
              </span>
              {idx < 2 && <div className="h-px w-8 bg-border" />}
            </div>
          ))}
        </div>
      </div>
    </header>
  )
}
