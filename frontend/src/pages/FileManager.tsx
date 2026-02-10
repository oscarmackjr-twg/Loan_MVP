import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

interface FileInfo {
  path: string
  size: number
  is_directory: boolean
  last_modified: string | null
}

export default function FileManager() {
  const [currentPath, setCurrentPath] = useState('')
  const [files, setFiles] = useState<FileInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  useEffect(() => {
    loadFiles()
  }, [currentPath])

  const loadFiles = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/files/list', {
        params: { path: currentPath }
      })
      setFiles(response.data.files || [])
    } catch (error: any) {
      console.error('Failed to load files:', error)
      alert(`Failed to load files: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    if (droppedFiles.length === 0) return

    setUploading(true)
    try {
      for (const file of droppedFiles) {
        const formData = new FormData()
        formData.append('file', file)
        
        await axios.post('/api/files/upload', formData, {
          params: { path: currentPath },
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      }
      alert(`Successfully uploaded ${droppedFiles.length} file(s)`)
      loadFiles()
    } catch (error: any) {
      console.error('Upload failed:', error)
      alert(`Upload failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setUploading(false)
    }
  }, [currentPath])

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files
    if (!selectedFiles || selectedFiles.length === 0) return

    setUploading(true)
    try {
      for (const file of Array.from(selectedFiles)) {
        const formData = new FormData()
        formData.append('file', file)
        
        await axios.post('/api/files/upload', formData, {
          params: { path: currentPath },
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      }
      alert(`Successfully uploaded ${selectedFiles.length} file(s)`)
      loadFiles()
    } catch (error: any) {
      console.error('Upload failed:', error)
      alert(`Upload failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setUploading(false)
      e.target.value = '' // Reset input
    }
  }

  const handleDownload = async (filePath: string) => {
    try {
      const response = await axios.get(`/api/files/download/${filePath}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filePath.split('/').pop() || 'file')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error: any) {
      console.error('Download failed:', error)
      alert(`Download failed: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleDelete = async (filePath: string) => {
    if (!confirm(`Delete ${filePath}?`)) return

    try {
      await axios.delete(`/api/files/${filePath}`)
      alert('File deleted successfully')
      loadFiles()
    } catch (error: any) {
      console.error('Delete failed:', error)
      alert(`Delete failed: ${error.response?.data?.detail || error.message}`)
    }
  }

  const navigateToDirectory = (dirPath: string) => {
    setCurrentPath(dirPath)
  }

  const goUp = () => {
    const parts = currentPath.split('/').filter(p => p)
    parts.pop()
    setCurrentPath(parts.join('/'))
  }

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">File Manager</h1>
        <div className="flex gap-2">
          {currentPath && (
            <button
              onClick={goUp}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              ↑ Up
            </button>
          )}
          <button
            onClick={loadFiles}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Current Path */}
      <div className="mb-4">
        <div className="text-sm text-gray-600">
          <span className="font-medium">Current Path:</span> {currentPath || '/'}
        </div>
      </div>

      {/* Upload Area */}
      <div
        className={`mb-6 border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-gray-50 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          multiple
          className="hidden"
          onChange={handleFileSelect}
          disabled={uploading}
        />
        <label
          htmlFor="file-upload"
          className="cursor-pointer block"
        >
          <div className="text-gray-600">
            {uploading ? (
              <div>Uploading...</div>
            ) : (
              <>
                <div className="text-lg font-medium mb-2">
                  Drag and drop files here, or click to select
                </div>
                <div className="text-sm">Supports multiple files</div>
              </>
            )}
          </div>
        </label>
      </div>

      {/* File List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Files</h2>
          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading...</div>
          ) : files.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No files found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Modified
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {files.map((file) => (
                    <tr key={file.path}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {file.is_directory ? (
                          <button
                            onClick={() => navigateToDirectory(file.path)}
                            className="text-blue-600 hover:text-blue-900 font-medium"
                          >
                            📁 {file.path.split('/').pop()}
                          </button>
                        ) : (
                          <span className="text-sm text-gray-900">
                            📄 {file.path.split('/').pop()}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {file.is_directory ? '-' : formatSize(file.size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {file.last_modified
                          ? new Date(file.last_modified).toLocaleString()
                          : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {!file.is_directory && (
                          <>
                            <button
                              onClick={() => handleDownload(file.path)}
                              className="text-blue-600 hover:text-blue-900 mr-4"
                            >
                              Download
                            </button>
                            <button
                              onClick={() => handleDelete(file.path)}
                              className="text-red-600 hover:text-red-900"
                            >
                              Delete
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
