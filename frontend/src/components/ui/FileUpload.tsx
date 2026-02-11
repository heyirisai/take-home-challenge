"use client";

import { useCallback, useState, DragEvent, ChangeEvent } from "react";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  label?: string;
}

export function FileUpload({
  onFileSelect,
  accept = ".pdf,.docx,.txt,.csv",
  label = "Upload a file",
}: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      setFileName(file.name);
      onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
        isDragOver
          ? "border-indigo-500 bg-indigo-50"
          : "border-gray-300 bg-white hover:border-gray-400"
      }`}
    >
      <svg
        className="mx-auto h-10 w-10 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
        />
      </svg>
      <p className="mt-2 text-sm text-gray-600">
        {fileName ? (
          <>
            Selected: <span className="font-medium">{fileName}</span>
          </>
        ) : (
          <>
            Drag and drop or{" "}
            <label className="cursor-pointer font-medium text-indigo-600 hover:text-indigo-500">
              browse
              <input
                type="file"
                className="sr-only"
                accept={accept}
                onChange={handleChange}
              />
            </label>
          </>
        )}
      </p>
      <p className="mt-1 text-xs text-gray-500">{label}</p>
    </div>
  );
}
