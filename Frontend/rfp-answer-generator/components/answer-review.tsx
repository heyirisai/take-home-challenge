'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, Download, ArrowLeft, Edit2, Copy, CheckCircle2, FileText, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { apiService, Answer } from '@/lib/api-service'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface AnswerReviewProps {
  answers: Answer[]
  onBack: () => void
  onExport: () => void
}

export default function AnswerReview({
  answers: initialAnswers,
  onBack,
  onExport,
}: AnswerReviewProps) {
  const [answers, setAnswers] = useState<Answer[]>(initialAnswers)
  const [expandedId, setExpandedId] = useState<number | null>(answers[0]?.id || null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editedText, setEditedText] = useState<string>('')
  const [copiedId, setCopiedId] = useState<number | null>(null)
  const [savingId, setSavingId] = useState<number | null>(null)

  const handleStartEdit = (answer: Answer) => {
    setEditingId(answer.id)
    setEditedText(answer.answer_text)
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditedText('')
  }

  const handleSaveEdit = async (answerId: number) => {
    if (!editedText.trim()) return
    
    setSavingId(answerId)
    try {
      const updatedAnswer = await apiService.editAnswer(answerId, editedText)
      setAnswers(prevAnswers =>
        prevAnswers.map(a => a.id === answerId ? updatedAnswer : a)
      )
      setEditingId(null)
      setEditedText('')
    } catch (error) {
      console.error('Failed to save answer:', error)
      alert('Failed to save answer. Please try again.')
    } finally {
      setSavingId(null)
    }
  }

  const handleCopy = (answer: Answer) => {
    navigator.clipboard.writeText(answer.answer_text)
    setCopiedId(answer.id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
    if (confidence >= 75) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    if (confidence >= 60) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
  }

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 90) return 'High'
    if (confidence >= 75) return 'Medium'
    if (confidence >= 60) return 'Moderate'
    return 'Low'
  }

  return (
    <div className="space-y-6">
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-foreground">Generated Answers</h2>
          <p className="mt-1 text-muted-foreground">
            Review and edit the generated RFP answers below
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Start Over
          </Button>
          <Button onClick={onExport}>
            <Download className="mr-2 h-4 w-4" />
            Export Answers
          </Button>
        </div>
      </div>

      {/* Summary stats */}
      <Card className="bg-gradient-to-r from-primary/5 to-accent/5 p-6">
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-muted-foreground">Total Questions</p>
            <p className="mt-2 text-3xl font-bold text-foreground">{answers.length}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Average Confidence</p>
            <p className="mt-2 text-3xl font-bold text-foreground">
              {(
                answers.reduce((sum, a) => sum + a.confidence_score, 0) / answers.length * 100
              ).toFixed(0)}
              %
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">High Confidence Answers</p>
            <p className="mt-2 text-3xl font-bold text-foreground">
              {answers.filter((a) => a.confidence_score >= 0.90).length}
            </p>
          </div>
        </div>
      </Card>

      {/* Answer cards */}
      <div className="space-y-4">
        {answers.map((answer, idx) => (
          <Card key={answer.id} className="overflow-hidden">
            <button
              onClick={() => setExpandedId(expandedId === answer.id ? null : answer.id)}
              className="w-full p-6 text-left hover:bg-secondary/30 transition-colors flex items-center justify-between"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="inline-block h-8 w-8 rounded-full bg-primary text-primary-foreground text-sm font-bold flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <h3 className="font-semibold text-foreground text-lg">
                    {answer.question_text}
                  </h3>
                </div>
                <div className="ml-11 flex items-center gap-2">
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(
                      (answer.confidence_score ?? 0) * 100
                    )}`}
                  >
                    {getConfidenceLabel((answer.confidence_score ?? 0) * 100)} Confidence ({((answer.confidence_score ?? 0) * 100).toFixed(0)}%)
                  </span>
                  {answer.source_documents && answer.source_documents.length > 0 && (
                    <Badge variant="outline" className="text-xs">
                      <FileText className="mr-1 h-3 w-3" />
                      {answer.source_documents.length} source{answer.source_documents.length > 1 ? 's' : ''}
                    </Badge>
                  )}
                </div>
              </div>
              {expandedId === answer.id ? (
                <ChevronUp className="h-5 w-5 text-muted-foreground ml-4" />
              ) : (
                <ChevronDown className="h-5 w-5 text-muted-foreground ml-4" />
              )}
            </button>

            {expandedId === answer.id && (
              <div className="border-t border-border px-6 py-6">
                {editingId === answer.id ? (
                  <div className="space-y-4">
                    <Textarea
                      value={editedText}
                      onChange={(e) => setEditedText(e.target.value)}
                      rows={8}
                      className="font-normal"
                      disabled={savingId === answer.id}
                    />
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        onClick={handleCancelEdit}
                        disabled={savingId === answer.id}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={() => handleSaveEdit(answer.id)}
                        disabled={savingId === answer.id || !editedText.trim()}
                      >
                        {savingId === answer.id ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="mr-2 h-4 w-4" />
                            Save Changes
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          // Custom styling for markdown elements
                          p: ({node, ...props}) => <p className="text-foreground leading-relaxed mb-3" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc ml-5 mb-3 text-foreground space-y-2" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal ml-5 mb-3 text-foreground space-y-2" {...props} />,
                          li: ({node, children, ...props}) => (
                            <li className="text-foreground" {...props}>
                              <span className="inline">{children}</span>
                            </li>
                          ),
                          h1: ({node, ...props}) => <h1 className="text-2xl font-bold mb-3 text-foreground" {...props} />,
                          h2: ({node, ...props}) => <h2 className="text-xl font-bold mb-2 text-foreground" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-lg font-semibold mb-2 text-foreground" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-bold text-foreground" {...props} />,
                          em: ({node, ...props}) => <em className="italic text-foreground" {...props} />,
                          code: ({node, ...props}) => <code className="bg-secondary px-1.5 py-0.5 rounded text-sm" {...props} />,
                          pre: ({node, ...props}) => <pre className="bg-secondary p-3 rounded-md overflow-x-auto mb-3" {...props} />,
                        }}
                      >
                        {answer.answer_text}
                      </ReactMarkdown>
                    </div>
                    
                    {/* Source Documents */}
                    {answer.source_documents && answer.source_documents.length > 0 && (
                      <div className="border-t border-border pt-4 mt-4">
                        <h4 className="text-sm font-semibold text-foreground mb-2">
                          Source Documents
                        </h4>
                        <div className="space-y-2">
                          {answer.source_documents.map((doc, docIdx) => (
                            <div
                              key={docIdx}
                              className="bg-secondary/30 rounded p-3 text-sm"
                            >
                              <div className="flex items-center gap-2">
                                <FileText className="h-4 w-4 text-muted-foreground" />
                                <span className="font-medium text-foreground">
                                  Document {doc.document_id}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  (Relevance: {(doc.relevance_score * 100).toFixed(0)}%)
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleStartEdit(answer)}
                      >
                        <Edit2 className="mr-2 h-4 w-4" />
                        Edit Answer
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCopy(answer)}
                      >
                        {copiedId === answer.id ? (
                          <>
                            <CheckCircle2 className="mr-2 h-4 w-4" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="mr-2 h-4 w-4" />
                            Copy to Clipboard
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Export footer */}
      <Card className="bg-primary/5 p-6 border-primary/20">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-foreground">Ready to submit?</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Export your answers as a formatted document ready for submission
            </p>
          </div>
          <Button size="lg" onClick={onExport}>
            <Download className="mr-2 h-4 w-4" />
            Export as Document
          </Button>
        </div>
      </Card>
    </div>
  )
}
