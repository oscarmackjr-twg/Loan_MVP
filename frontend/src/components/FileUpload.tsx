import { useState, useCallback } from 'react'
import axios from 'axios'

interface FileUploadProps {
  onUploadComplete?: () => void
  destinationPath?: string
  accept?: string
  multiple?: boolean
}

export default function FileUpload({
  onUploadComplete,
  destinationPath = '',
  accept,
  multiple = false
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({})

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const uploadFile = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(
        `/api/files/upload?path=${encodeURIComponent(destinationPath)}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              )
              setUploadProgress((prev) => ({
                ...prev,
                [file.name]: percentCompleted,
              }))
            }
          },
        }
      )
      return response.data
    } catch (error: any) {
      console.error(`Error uploading ${file.name}:`, error)
      throw error
    }
  }

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)

      const files = Array.from(e.dataTransfer.files)
      if (files.length === 0) return

      setUploading(true)
      setUploadProgress({})

      try {
        const uploadPromises = files.map((file) => uploadFile(file))
        await Promise.all(uploadPromises)
        onUploadComplete?.()
      } catch (error: any) {
        alert(`Upload failed: ${error.response?.data?.detail || error.message}`)
      } finally {
        setUploading(false)
        setUploadProgress({})
      }
    },
    [destinationPath, onUploadComplete]
  )

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || [])
      if (files.length === 0) return

      setUploading(true)
      setUploadProgress({})

      try {
        const uploadPromises = files.map((file) => uploadFile(file))
        await Promise.all(uploadPromises)
        onUploadComplete?.()
      } catch (error: any) {
        alert(`Upload failed: ${error.response?.data?.detail || error.message}`)
      } finally {
        setUploading(false)
        setUploadProgress({})
        // Reset input
        e.target.value = ''
      }
    },
    [destinationPath, onUploadComplete]
  )

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        isDragging
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400'
      } ${uploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="file-upload"
        className="hidden"
        accept={accept}
        multiple={multiple}
        onChange={handleFileSelect}
        disabled={uploading}
      />
      <label htmlFor="file-upload" className="cursor-pointer">
        {uploading ? (
          <div className="space-y-2">
            <div className="text-gray-600">Uploading...</div>
            {Object.entries(uploadProgress).map(([filename, progress]) => (
              <div key={filename} className="text-sm">
                <div className="flex justify-between mb-1">
                  <span className="text-gray-700">{filename}</span>
                  <span className="text-gray-500">{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div className="text-gray-600">
              <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
            </div>
            <div className="text-sm text-gray-500">
              {accept ? `Accepted: ${accept}` : 'Any file type'}
              {multiple && ' (multiple files allowed)'}
            </div>
            {destinationPath && (
              <div className="text-xs text-gray-400">Destination: {destinationPath}</div>
            )}
          </div>
        )}
      </label>
    </div>
  )
}
