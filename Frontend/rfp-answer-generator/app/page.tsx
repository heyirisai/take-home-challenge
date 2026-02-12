'use client'

import { useState, useEffect, useCallback } from 'react'
import Header from '@/components/header'
import DocumentUpload from '@/components/document-upload'
import RFPProcessor from '@/components/rfp-processor'
import AnswerReview from '@/components/answer-review'
import { apiService, Answer, TaskStatusResponse } from '@/lib/api-service'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

export default function Home() {
  const [mounted, setMounted] = useState(false)
  const [step, setStep] = useState<'upload' | 'process' | 'review'>('upload')
  const [documentIds, setDocumentIds] = useState<number[]>([])
  const [rfpId, setRfpId] = useState<number | null>(null)
  const [rfpFile, setRfpFile] = useState<File | null>(null)
  const [answers, setAnswers] = useState<Answer[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingError, setProcessingError] = useState<string | null>(null)
  const [processingProgress, setProcessingProgress] = useState<number>(0)
  const [processingStep, setProcessingStep] = useState<string>('')

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleDocumentsUploaded = useCallback((ids: number[]) => {
    setDocumentIds(ids)
  }, [])

  const handleRfpUploaded = useCallback((id: number, file: File) => {
    setRfpId(id)
    setRfpFile(file)
  }, [])

  const handleProcessRFP = async () => {
    if (!rfpId || documentIds.length === 0) {
      alert('Please upload both knowledge base documents and an RFP file')
      return
    }

    setIsProcessing(true)
    setProcessingError(null)
    setProcessingProgress(0)
    setProcessingStep('Starting RFP processing...')
    setStep('process')

    try {
      // Start async processing and get task_id
      const startResponse = await apiService.processRFP(rfpId, documentIds)
      
      // Poll for status updates
      const finalStatus = await apiService.pollTaskStatus(
        startResponse.task_id,
        (status: TaskStatusResponse) => {
          // Update progress UI
          setProcessingProgress(status.progress)
          setProcessingStep(status.current_step)
        }
      )
      
      // Processing complete - extract answers from result
      if (finalStatus.result && finalStatus.result.answers) {
        setAnswers(finalStatus.result.answers)
        setStep('review')
      } else {
        throw new Error('No answers were generated')
      }
    } catch (error) {
      console.error('Error processing RFP:', error)
      setProcessingError(
        error instanceof Error 
          ? error.message 
          : 'An error occurred while processing the RFP. Please try again.'
      )
      // Stay on process step to show error
    } finally {
      setIsProcessing(false)
      setProcessingProgress(0)
      setProcessingStep('')
    }
  }

  const handleExportAnswers = () => {
    // Create PDF document
    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 15
    const contentWidth = pageWidth - (margin * 2)
    
    // Title
    doc.setFontSize(20)
    doc.setFont('helvetica', 'bold')
    doc.text('RFP Response Document', margin, 20)
    
    // Date
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    doc.text(`Generated: ${new Date().toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })}`, margin, 28)
    
    // Summary statistics
    doc.setFontSize(12)
    doc.setFont('helvetica', 'bold')
    doc.text('Summary', margin, 38)
    
    const avgConfidence = (answers.reduce((sum, a) => sum + a.confidence_score, 0) / answers.length * 100).toFixed(0)
    const highConfidence = answers.filter(a => a.confidence_score >= 0.90).length
    
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    doc.text(`Total Questions: ${answers.length}`, margin, 45)
    doc.text(`Average Confidence: ${avgConfidence}%`, margin, 51)
    doc.text(`High Confidence Answers: ${highConfidence}`, margin, 57)
    
    // Line separator
    doc.setDrawColor(200, 200, 200)
    doc.line(margin, 62, pageWidth - margin, 62)
    
    let yPosition = 70
    
    // Loop through each answer
    answers.forEach((answer, idx) => {
      // Check if we need a new page
      if (yPosition > pageHeight - 40) {
        doc.addPage()
        yPosition = 20
      }
      
      // Question number and confidence badge
      doc.setFontSize(11)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(59, 130, 246) // Blue color
      doc.text(`Question ${idx + 1}`, margin, yPosition)
      
      // Confidence badge
      const confidence = (answer.confidence_score * 100).toFixed(0)
      doc.setFontSize(9)
      doc.setFont('helvetica', 'normal')
      
      // Set color based on confidence
      if (answer.confidence_score >= 0.90) {
        doc.setTextColor(34, 197, 94) // Green
      } else if (answer.confidence_score >= 0.75) {
        doc.setTextColor(59, 130, 246) // Blue
      } else if (answer.confidence_score >= 0.60) {
        doc.setTextColor(234, 179, 8) // Yellow
      } else {
        doc.setTextColor(249, 115, 22) // Orange
      }
      
      doc.text(`${confidence}% confidence`, pageWidth - margin - 30, yPosition)
      doc.setTextColor(0, 0, 0) // Reset to black
      
      yPosition += 6
      
      // Question text
      doc.setFontSize(10)
      doc.setFont('helvetica', 'bold')
      const questionLines = doc.splitTextToSize(answer.question_text, contentWidth)
      doc.text(questionLines, margin, yPosition)
      yPosition += questionLines.length * 5 + 3
      
      // Answer text
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9)
      
      // Clean markdown formatting for PDF
      let cleanAnswer = answer.answer_text
        .replace(/\*\*(.+?)\*\*/g, '$1') // Remove bold
        .replace(/\*(.+?)\*/g, '$1') // Remove italic
        .replace(/^#+\s+/gm, '') // Remove headers
        .replace(/```[\s\S]*?```/g, '') // Remove code blocks
      
      const answerLines = doc.splitTextToSize(cleanAnswer, contentWidth)
      
      // Check if answer fits on current page
      const answerHeight = answerLines.length * 4
      if (yPosition + answerHeight > pageHeight - 20) {
        doc.addPage()
        yPosition = 20
      }
      
      doc.text(answerLines, margin, yPosition)
      yPosition += answerHeight + 10
      
      // Add separator line
      if (idx < answers.length - 1) {
        doc.setDrawColor(220, 220, 220)
        doc.line(margin, yPosition, pageWidth - margin, yPosition)
        yPosition += 10
      }
    })
    
    // Footer on all pages
    const totalPages = doc.internal.pages.length - 1
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i)
      doc.setFontSize(8)
      doc.setTextColor(128, 128, 128)
      doc.text(
        `Page ${i} of ${totalPages}`,
        pageWidth / 2,
        pageHeight - 10,
        { align: 'center' }
      )
    }
    
    // Save the PDF
    doc.save(`RFP_Answers_${new Date().toISOString().split('T')[0]}.pdf`)
  }

  const handleStartOver = () => {
    setStep('upload')
    setDocumentIds([])
    setRfpId(null)
    setRfpFile(null)
    setAnswers([])
    setProcessingError(null)
    setProcessingProgress(0)
    setProcessingStep('')
  }

  if (!mounted) {
    return (
      <div className="min-h-screen bg-background">
        <Header step="upload" />
        <main className="mx-auto max-w-6xl px-4 py-8">
          <div className="space-y-8" />
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Header step={step} />

      <main className="mx-auto max-w-6xl px-4 py-8">
        {step === 'upload' && (
          <div className="space-y-8">
            <DocumentUpload onDocumentsUploaded={handleDocumentsUploaded} onRfpUploaded={handleRfpUploaded} onProcess={handleProcessRFP} />
          </div>
        )}

        {step === 'process' && (
          <RFPProcessor 
            isLoading={isProcessing} 
            error={processingError}
            onRetry={handleProcessRFP}
            progress={processingProgress}
            currentStep={processingStep}
          />
        )}

        {step === 'review' && answers.length > 0 && (
          <AnswerReview
            answers={answers}
            onBack={handleStartOver}
            onExport={handleExportAnswers}
          />
        )}
      </main>
    </div>
  )
}