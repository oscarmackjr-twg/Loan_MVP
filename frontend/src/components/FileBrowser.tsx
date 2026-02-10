import { useState, useEffect } from 'react'
import axios from 'axios'

interface FileInfo {
  path: string
  size: number
  is_directory: boolean
  last_modified: string | null
}

interface FileBrowserProps {
  basePath?: string
  onFileSelect?: (path: string) => void
  showUpload?: boolean
  onUploadComplete?: () => void
}

export default function FileBrowser({
  basePath = '',
  onFileSelect,
  showUpload = true,
  onUploadComplete
}: FileBrowserProps) {
  const [currentPath, setCurrentPath] = useState(basePath)
  const [files, setFiles] = useState<FileInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)

  const fetchFiles = async (path: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`/api/files/list?path=${encodeURIComponent(path)}`)
      setFiles(response.data.files || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load files')
      setFiles([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFiles(currentPath)
  }, [currentPath])

  const handlePathClick = (path: string, isDirectory: boolean) => {
    if (isDirectory) {
      setCurrentPath(path)
      setSelectedFile(null)
    } else {
      setSelectedFile(path)
      onFileSelect?.(path)
    }
  }

  const handleDownload = async (filePath: string) => {
    try {
      const response = await axios.get(`/api/files/download/${encodeURIComponent(filePath)}`, {
        responseType: 'blob',
      })
      
      // Create a blob URL and trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filePath.split('/').pop() || 'file')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      alert(`Download failed: ${err.response?.data?.detail || err.message}`)
    }
  }

  const handleDelete = async (filePath: string) => {
    if (!confirm(`Are you sure you want to delete ${filePath}?`)) {
      return
    }

    try {
      await axios.delete(`/api/files/${encodeURIComponent(filePath)}`)
      fetchFiles(currentPath) // Refresh list
      if (selectedFile === filePath) {
        setSelectedFile(null)
      }
    } catch (err: any) {
      alert(`Delete failed: ${err.response?.data?.detail || err.message}`)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const navigateUp = () => {
    const parts = currentPath.split('/').filter(Boolean)
    if (parts.length > 0) {
      parts.pop()
      setCurrentPath(parts.join('/'))
    } else {
      setCurrentPath('')
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          {currentPath && (
            <button
              onClick={navigateUp}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
            >
              ↑ Up
            </button>
          )}
          <span className="text-sm font-medium text-gray-700">
            {currentPath || '/'}
          </span>
        </div>
        {showUpload && (
          <button
            onClick={() => {
              const input = document.createElement('input')
              input.type = 'file'
              input.multiple = true
              input.onchange = async (e) => {
                const files = Array.from((e.target as HTMLInputElement).files || [])
                for (const file of files) {
                  const formData = new FormData()
                  formData.append('file', file)
                  try {
                    await axios.post(
                      `/api/files/upload?path=${encodeURIComponent(currentPath)}`,
                      formData
                    )
                  } catch (err: any) {
                    alert(`Upload failed: ${err.response?.data?.detail || err.message}`)
                    return
                  }
                }
                fetchFiles(currentPath)
                onUploadComplete?.()
              }
              input.click()
            }}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Upload
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : files.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No files found</div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Size
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Modified
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {files.map((file) => (
                <tr
                  key={file.path}
                  className={`hover:bg-gray-50 ${
                    selectedFile === file.path ? 'bg-blue-50' : ''
                  }`}
                >
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handlePathClick(file.path, file.is_directory)}
                      className="text-left flex items-center space-x-2 text-sm font-medium text-gray-900 hover:text-blue-600"
                    >
                      {file.is_directory ? (
                        <span className="text-yellow-600">📁</span>
                      ) : (
                        <span className="text-gray-400">📄</span>
                      )}
                      <span>{file.path.split('/').pop()}</span>
                    </button>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {file.is_directory ? '—' : formatFileSize(file.size)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {file.last_modified
                      ? new Date(file.last_modified).toLocaleString()
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-right text-sm">
                    {!file.is_directory && (
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => handleDownload(file.path)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Download"
                        >
                          ⬇
                        </button>
                        <button
                          onClick={() => handleDelete(file.path)}
                          className="text-red-600 hover:text-red-800"
                          title="Delete"
                        >
                          🗑
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
