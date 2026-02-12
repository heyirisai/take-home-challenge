'use client'

import React from "react"

import { useState, useRef, useEffect } from 'react'
import { Upload, X, File, FileText as FileTextIcon, CheckCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { apiService, type DocumentUploadResponse } from '@/lib/api-service'

interface UploadedDocument {
  file: File
  id?: number
  uploaded: boolean
  uploading: boolean
  error?: string
}

interface DocumentUploadProps {
  onDocumentsUploaded: (documentIds: number[]) => void
  onRfpUploaded: (documentId: number, file: File) => void
  onProcess: () => void
}

export default function DocumentUpload({
  onDocumentsUploaded,
  onRfpUploaded,
  onProcess,
}: DocumentUploadProps) {
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([])
  const [rfpFile, setRfpFile] = useState<File | null>(null)
  const [rfpUploaded, setRfpUploaded] = useState<{ id?: number; uploading: boolean }>({ uploading: false })
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const rfpInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  // Notify parent when uploaded documents change
  useEffect(() => {
    const uploadedIds = uploadedDocs
      .filter(doc => doc.uploaded && doc.id)
      .map(doc => doc.id!)
    if (uploadedIds.length > 0) {
      onDocumentsUploaded(uploadedIds)
    }
  }, [uploadedDocs, onDocumentsUploaded])

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDocumentDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      await handleDocumentFiles(files)
    }
  }

  const handleDocumentFiles = async (files: File[]) => {
    // Add files to state as pending upload
    const newDocs: UploadedDocument[] = files.map(file => ({
      file,
      uploaded: false,
      uploading: true,
    }))
    setUploadedDocs(prev => [...prev, ...newDocs])

    // Track uploaded IDs
    const newUploadedIds: number[] = []

    // Upload each file
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      try {
        const response = await apiService.uploadDocument(file, 'knowledge_base')
        
        // Update the document with the ID
        setUploadedDocs(prev => prev.map(doc => 
          doc.file === file 
            ? { ...doc, id: response.id, uploaded: true, uploading: false }
            : doc
        ))

        // Track the uploaded ID
        newUploadedIds.push(response.id)

        toast({
          title: "Document uploaded",
          description: `${file.name} uploaded successfully`,
        })
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed'
        
        setUploadedDocs(prev => prev.map(doc => 
          doc.file === file 
            ? { ...doc, uploaded: false, uploading: false, error: errorMessage }
            : doc
        ))

        toast({
          title: "Upload failed",
          description: `Failed to upload ${file.name}: ${errorMessage}`,
          variant: "destructive",
        })
      }
    }
  }

  const handleDocumentSelect = () => {
    fileInputRef.current?.click()
  }

  const handleRfpSelect = () => {
    rfpInputRef.current?.click()
  }

  const handleDocumentFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files) {
      await handleDocumentFiles(Array.from(files))
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleRfpFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files[0]) {
      const file = files[0]
      setRfpFile(file)
      setRfpUploaded({ uploading: true })

      try {
        const response = await apiService.uploadDocument(file, 'rfp')
        setRfpUploaded({ id: response.id, uploading: false })
        onRfpUploaded(response.id, file)
        
        toast({
          title: "RFP uploaded",
          description: `${file.name} uploaded successfully`,
        })
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed'
        setRfpUploaded({ uploading: false })
        setRfpFile(null)
        
        toast({
          title: "Upload failed",
          description: `Failed to upload RFP: ${errorMessage}`,
          variant: "destructive",
        })
      }
    }
    // Reset input
    if (rfpInputRef.current) {
      rfpInputRef.current.value = ''
    }
  }

  const removeDocument = async (index: number) => {
    const doc = uploadedDocs[index]
    
    // Delete from backend if uploaded
    if (doc.id) {
      try {
        await apiService.deleteDocument(doc.id)
        toast({
          title: "Document removed",
          description: `${doc.file.name} removed successfully`,
        })
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to remove document from server",
          variant: "destructive",
        })
      }
    }
    
    // Remove from state
    const updated = uploadedDocs.filter((_, i) => i !== index)
    setUploadedDocs(updated)
  }

  const removeRfp = async () => {
    if (rfpUploaded.id) {
      try {
        await apiService.deleteDocument(rfpUploaded.id)
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to remove RFP from server",
          variant: "destructive",
        })
      }
    }
    setRfpFile(null)
    setRfpUploaded({ uploading: false })
  }

  const canProcess = uploadedDocs.some(d => d.uploaded) && rfpUploaded.id

  return (
    <div className="space-y-8">
      {/* Knowledge Base Documents */}
      <Card className="p-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-foreground">Step 1: Upload Knowledge Base</h2>
          <p className="mt-2 text-muted-foreground">
            Upload company documents that will be used to generate RFP answers (PDFs, Word docs, text files)
          </p>
        </div>

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDocumentDrop}
          className={`rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
            dragActive ? 'border-primary bg-primary/5' : 'border-border'
          }`}
        >
          <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
          <p className="mt-4 text-foreground font-semibold">Drag and drop files here</p>
          <p className="mt-2 text-sm text-muted-foreground">or</p>
          <Button
            variant="default"
            size="lg"
            onClick={handleDocumentSelect}
            className="mt-4"
          >
            Choose Files
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleDocumentFileChange}
            className="hidden"
            accept=".pdf,.doc,.docx,.txt,.xlsx"
          />
          <p className="mt-4 text-xs text-muted-foreground">
            Supported formats: PDF, Word, Excel, Text
          </p>
        </div>

        {uploadedDocs.length > 0 && (
          <div className="mt-6 space-y-3">
            <p className="font-semibold text-foreground">Uploaded Documents ({uploadedDocs.length})</p>
            <div className="space-y-2">
              {uploadedDocs.map((doc, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between rounded-lg bg-secondary p-3"
                >
                  <div className="flex items-center gap-3">
                    {doc.uploading ? (
                      <Loader2 className="h-5 w-5 text-primary animate-spin" />
                    ) : doc.uploaded ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <X className="h-5 w-5 text-destructive" />
                    )}
                    <span className="text-sm font-medium text-foreground">{doc.file.name}</span>
                    {doc.error && (
                      <span className="text-xs text-destructive">({doc.error})</span>
                    )}
                  </div>
                  <button
                    onClick={() => removeDocument(idx)}
                    className="text-muted-foreground hover:text-foreground"
                    disabled={doc.uploading}
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* RFP File Upload */}
      <Card className="p-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-foreground">Step 2: Upload RFP</h2>
          <p className="mt-2 text-muted-foreground">
            Upload the RFP document that contains the questions to answer
          </p>
        </div>

        <div 
          className={`rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
            dragActive ? 'border-primary bg-primary/5' : 'border-border'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={async (e) => {
            e.preventDefault()
            e.stopPropagation()
            setDragActive(false)
            const files = Array.from(e.dataTransfer.files)
            if (files.length > 0 && files[0]) {
              const file = files[0]
              setRfpFile(file)
              setRfpUploaded({ uploading: true })

              try {
                const response = await apiService.uploadDocument(file, 'rfp')
                setRfpUploaded({ id: response.id, uploading: false })
                onRfpUploaded(response.id, file)
                
                toast({
                  title: "RFP uploaded",
                  description: `${file.name} uploaded successfully`,
                })
              } catch (error) {
                const errorMessage = error instanceof Error ? error.message : 'Upload failed'
                setRfpUploaded({ uploading: false })
                setRfpFile(null)
                
                toast({
                  title: "Upload failed",
                  description: `Failed to upload RFP: ${errorMessage}`,
                  variant: "destructive",
                })
              }
            }
          }}
        >
          {!rfpFile ? (
            <>
              <FileTextIcon className="mx-auto h-12 w-12 text-muted-foreground" />
              <p className="mt-4 text-foreground font-semibold">
                Drag and drop your RFP file here
              </p>
              <p className="mt-2 text-sm text-muted-foreground">or</p>
              <Button
                variant="default"
                size="lg"
                onClick={handleRfpSelect}
                className="mt-4"
              >
                Browse Files
              </Button>
              <input
                ref={rfpInputRef}
                type="file"
                onChange={handleRfpFileChange}
                className="hidden"
                accept=".pdf,.doc,.docx,.txt"
              />
              <p className="mt-4 text-xs text-muted-foreground">
                Supported formats: PDF, Word, Text
              </p>
            </>
          ) : (
            <>
              <div className="flex items-center justify-center gap-3 mb-4">
                {rfpUploaded.uploading ? (
                  <Loader2 className="h-8 w-8 text-primary animate-spin" />
                ) : rfpUploaded.id ? (
                  <CheckCircle className="h-8 w-8 text-green-500" />
                ) : (
                  <FileTextIcon className="h-8 w-8 text-muted-foreground" />
                )}
              </div>
              <p className="text-foreground font-semibold">{rfpFile.name}</p>
              {rfpUploaded.uploading && (
                <p className="text-sm text-muted-foreground mt-2">Uploading...</p>
              )}
              {rfpUploaded.id && (
                <p className="text-sm text-green-600 mt-2">Successfully uploaded!</p>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={removeRfp}
                className="mt-4"
                disabled={rfpUploaded.uploading}
              >
                <X className="mr-2 h-4 w-4" />
                Remove
              </Button>
            </>
          )}
        </div>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-end gap-4">
        <Button
          variant="outline"
          size="lg"
          onClick={async () => {
            // Delete all documents from backend
            for (const doc of uploadedDocs) {
              if (doc.id) {
                try {
                  await apiService.deleteDocument(doc.id)
                } catch (error) {
                  // Ignore errors during cleanup
                }
              }
            }
            if (rfpUploaded.id) {
              try {
                await apiService.deleteDocument(rfpUploaded.id)
              } catch (error) {
                // Ignore errors during cleanup
              }
            }
            setUploadedDocs([])
            setRfpFile(null)
            setRfpUploaded({ uploading: false })
          }}
        >
          Clear All
        </Button>
        <Button
          variant="default"
          size="lg"
          onClick={onProcess}
          disabled={!canProcess}
          className="px-8"
        >
          Generate Answers
        </Button>
      </div>
    </div>
  )
}
