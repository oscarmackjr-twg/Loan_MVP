import { useEffect, useState } from 'react'
import axios from 'axios'

interface FileInfo {
  path: string
  size: number
  is_directory: boolean
  last_modified: string | null
}

/** Format Date as mm/dd/yyyy for display and input. */
function formatEffectiveDate(d: Date): string {
  const m = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const y = d.getFullYear()
  return `${m}/${day}/${y}`
}

/** Parse mm/dd/yyyy or m/d/yyyy to YYYY-MM-DD for API; returns null if invalid. */
function parseEffectiveDateToApi(value: string): string | null {
  const trimmed = value.trim()
  if (!trimmed) return null
  const parts = trimmed.split('/')
  if (parts.length !== 3) return null
  const [mm, dd, yyyy] = parts.map((p) => parseInt(p, 10))
  if (Number.isNaN(mm) || Number.isNaN(dd) || Number.isNaN(yyyy)) return null
  if (mm < 1 || mm > 12 || dd < 1 || dd > 31) return null
  const d = new Date(yyyy, mm - 1, dd)
  if (d.getFullYear() !== yyyy || d.getMonth() !== mm - 1 || d.getDate() !== dd) return null
  const y = d.getFullYear()
  const m = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** Build user-facing message for pre-funding / pipeline run failures (502, 500, or other). */
function pipelineRunFailureMessage(error: any): string {
  const status = error.response?.status
  const detail = error.response?.data?.detail
  const is502 = status === 502
  const is5xx = status >= 500 && status < 600
  const lines: string[] = []
  if (is502) {
    lines.push('The request timed out or the connection was closed (502). Pre-funding can take several minutes.')
  } else if (is5xx && detail) {
    lines.push(`Server error: ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`)
  } else if (detail) {
    lines.push(String(detail))
  } else {
    lines.push(error.message || 'Request failed.')
  }
  lines.push('')
  lines.push('What to do:')
  lines.push('1. Ensure input files are in File Manager under files_required/ (Tape20Loans, MASTER_SHEET, SFY/PRIME exhibits, etc.).')
  lines.push('2. In AWS CloudWatch, open your environment\'s ECS log group (e.g. /ecs/loan-engine-qa for QA) and search for the time of your run or for "Pipeline run" to see errors and run_id.')
  lines.push('3. If the run took longer than ~15 minutes, the load balancer may have closed the connection; check the Recent Runs table—the run might have completed.')
  lines.push('4. Fix any issues (e.g. missing files, wrong dates) and try again.')
  return lines.join('\n')
}

export default function ProgramRuns() {
  const [storageType, setStorageType] = useState<string>('local')
  const [runFolder, setRunFolder] = useState('')
  const [effectiveDateModalOpen, setEffectiveDateModalOpen] = useState(false)
  const [effectiveDateInput, setEffectiveDateInput] = useState('')
  const [preFundingSubmitting, setPreFundingSubmitting] = useState(false)
  const [taggingSubmitting, setTaggingSubmitting] = useState(false)
  const [finalFundingSGSubmitting, setFinalFundingSGSubmitting] = useState(false)
  const [finalFundingCIBCSubmitting, setFinalFundingCIBCSubmitting] = useState(false)
  const [runAcceptedDialogOpen, setRunAcceptedDialogOpen] = useState(false)
  const [startedRunId, setStartedRunId] = useState<string | null>(null)
  const [outputPath, setOutputPath] = useState('')
  const [outputFiles, setOutputFiles] = useState<FileInfo[]>([])
  const [outputFilesLoading, setOutputFilesLoading] = useState(false)

  useEffect(() => {
    axios.get('/api/config').then((r) => {
      const st = r.data?.storage_type ?? 'local'
      setStorageType(st)
      if (st === 'local') {
        setRunFolder('C:/Users/omack/Intrepid/pythonFramework/loan_engine/legacy')
      }
    }).catch(() => {})
  }, [])

  useEffect(() => {
    loadOutputFiles()
  }, [outputPath])

  const loadOutputFiles = async () => {
    setOutputFilesLoading(true)
    try {
      const response = await axios.get('/api/files/list', {
        params: { path: outputPath, area: 'outputs' }
      })
      setOutputFiles(response.data.files || [])
    } catch (error: any) {
      console.error('Failed to load output files:', error)
      setOutputFiles([])
    } finally {
      setOutputFilesLoading(false)
    }
  }

  const openEffectiveDateModal = () => {
    setEffectiveDateInput(formatEffectiveDate(new Date()))
    setEffectiveDateModalOpen(true)
  }

  const closeEffectiveDateModal = () => {
    setEffectiveDateModalOpen(false)
  }

  const triggerPreFundingRun = async (tdayYYYYMMDD: string | null) => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        alert('You are not logged in. Please log in and try again.')
        window.location.href = '/login'
        return
      }
      setPreFundingSubmitting(true)
      const payload: { folder: string; tday?: string } = {
        folder: storageType === 's3' ? '' : runFolder.trim(),
      }
      if (tdayYYYYMMDD) payload.tday = tdayYYYYMMDD
      const response = await axios.post('/api/pipeline/run', payload)
      setStartedRunId(response.data?.run_id ?? null)
      setEffectiveDateModalOpen(false)
      setRunAcceptedDialogOpen(true)
      loadOutputFiles()
    } catch (error: any) {
      if (error.response?.status === 401) {
        alert('Your session has expired. Please log in again.')
        window.location.href = '/login'
      } else if (error.response?.status === 409) {
        alert(error.response?.data?.detail ?? 'Another run is already in progress. Wait or cancel it on the Dashboard before starting a new run.')
      } else {
        alert(pipelineRunFailureMessage(error))
      }
    } finally {
      setPreFundingSubmitting(false)
    }
  }

  const confirmPreFundingRun = () => {
    const tday = parseEffectiveDateToApi(effectiveDateInput)
    if (effectiveDateInput.trim() && !tday) {
      alert('Please enter the effective date in mm/dd/yyyy format.')
      return
    }
    triggerPreFundingRun(tday ?? null)
  }

  const runTagging = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        alert('You are not logged in. Please log in and try again.')
        window.location.href = '/login'
        return
      }
      setTaggingSubmitting(true)
      await axios.post('/api/program-run', { phase: 'tagging' })
      alert('Tagging run completed. Check the output directory below.')
      loadOutputFiles()
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message
      if (error.response?.status === 401) {
        alert('Your session has expired. Please log in again.')
        window.location.href = '/login'
      } else {
        alert(`Tagging failed: ${errorMessage}`)
      }
    } finally {
      setTaggingSubmitting(false)
    }
  }

  const runFinalFundingSG = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        alert('You are not logged in. Please log in and try again.')
        window.location.href = '/login'
        return
      }
      setFinalFundingSGSubmitting(true)
      await axios.post('/api/program-run', { phase: 'final_funding_sg' })
      alert('Final Funding SG completed. Check the output directory below.')
      loadOutputFiles()
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message
      if (error.response?.status === 401) {
        alert('Your session has expired. Please log in again.')
        window.location.href = '/login'
      } else {
        alert(`Final Funding SG failed: ${errorMessage}`)
      }
    } finally {
      setFinalFundingSGSubmitting(false)
    }
  }

  const runFinalFundingCIBC = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        alert('You are not logged in. Please log in and try again.')
        window.location.href = '/login'
        return
      }
      setFinalFundingCIBCSubmitting(true)
      await axios.post('/api/program-run', { phase: 'final_funding_cibc' })
      alert('Final Funding CIBC completed. Check the output directory below.')
      loadOutputFiles()
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message
      if (error.response?.status === 401) {
        alert('Your session has expired. Please log in again.')
        window.location.href = '/login'
      } else {
        alert(`Final Funding CIBC failed: ${errorMessage}`)
      }
    } finally {
      setFinalFundingCIBCSubmitting(false)
    }
  }

  const handleDownload = async (filePath: string) => {
    try {
      const response = await axios.get(`/api/files/download/${filePath}`, {
        params: { area: 'outputs' },
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
      alert(`Download failed: ${error.response?.data?.detail || error.message}`)
    }
  }

  const navigateOutputDir = (dirPath: string) => {
    setOutputPath(dirPath)
  }

  const goUpOutput = () => {
    const parts = outputPath.split('/').filter(p => p)
    parts.pop()
    setOutputPath(parts.join('/'))
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
        <h1 className="text-2xl font-bold text-gray-900">Program Runs</h1>
      </div>

      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-3">Run program</h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={openEffectiveDateModal}
            disabled={preFundingSubmitting}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {preFundingSubmitting ? 'Starting…' : 'Pre-Funding'}
          </button>
          <button
            onClick={runTagging}
            disabled={taggingSubmitting}
            className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {taggingSubmitting ? 'Running…' : 'Tagging'}
          </button>
          <button
            onClick={runFinalFundingSG}
            disabled={finalFundingSGSubmitting}
            className="px-4 py-2 bg-violet-600 text-white rounded-md hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {finalFundingSGSubmitting ? 'Running…' : 'Final Funding SG'}
          </button>
          <button
            onClick={runFinalFundingCIBC}
            disabled={finalFundingCIBCSubmitting}
            className="px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {finalFundingCIBCSubmitting ? 'Running…' : 'Final Funding CIBC'}
          </button>
        </div>
        <p className="text-sm text-gray-500 mt-2">
          Pre-Funding runs the pipeline (same as Start Pipeline Run). Tagging runs the tagging script using files from the inputs directory. Final Funding SG and Final Funding CIBC run the respective workbooks using standard input and output directories. Outputs appear in the file manager below.
        </p>
      </div>

      {/* Effective date modal for Pre-Funding */}
      {effectiveDateModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="effective-date-title"
        >
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 id="effective-date-title" className="text-lg font-semibold text-gray-900 mb-2">
              Effective date for Pre-Funding run
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Enter in <strong>mm/dd/yyyy</strong> format. This date (Tday) is used for file discovery and pdate calculation.
            </p>
            <label htmlFor="effective-date-input" className="block text-sm font-medium text-gray-700 mb-1">
              Effective date
            </label>
            <input
              id="effective-date-input"
              type="text"
              value={effectiveDateInput}
              onChange={(e) => setEffectiveDateInput(e.target.value)}
              placeholder="mm/dd/yyyy"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={closeEffectiveDateModal}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmPreFundingRun}
                disabled={preFundingSubmitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {preFundingSubmitting ? 'Starting…' : 'Start Run'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Run accepted dialog */}
      {runAcceptedDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" role="dialog" aria-modal="true">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Pre-Funding run started</h2>
            <p className="text-gray-600 mb-4">
              The pipeline run has been accepted and is in progress. Outputs will appear in the file manager below when complete.
            </p>
            {startedRunId && (
              <p className="text-sm text-gray-500 mb-4 font-mono">Run ID: {startedRunId}</p>
            )}
            <div className="flex justify-end">
              <button
                onClick={() => { setRunAcceptedDialogOpen(false); setStartedRunId(null); }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Output file manager */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">Output directory</h2>
            <div className="flex items-center gap-2">
              {outputPath && (
                <button
                  onClick={goUpOutput}
                  className="px-3 py-1.5 text-sm bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  ↑ Up
                </button>
              )}
              <button
                onClick={loadOutputFiles}
                disabled={outputFilesLoading}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {outputFilesLoading ? 'Loading…' : 'Refresh'}
              </button>
            </div>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Path: {outputPath || '/'}
          </p>
          {outputFilesLoading ? (
            <div className="text-center py-8 text-gray-500">Loading…</div>
          ) : outputFiles.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No files in this directory</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Modified</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {outputFiles.map((file) => (
                    <tr key={file.path}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {file.is_directory ? (
                          <button
                            onClick={() => navigateOutputDir(file.path)}
                            className="text-blue-600 hover:text-blue-900 font-medium"
                          >
                            📁 {file.path.split('/').pop()}
                          </button>
                        ) : (
                          <span className="text-sm text-gray-900">📄 {file.path.split('/').pop()}</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {file.is_directory ? '—' : formatSize(file.size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {file.last_modified ? new Date(file.last_modified).toLocaleString() : '—'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {!file.is_directory && (
                          <button
                            onClick={() => handleDownload(file.path)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Download
                          </button>
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
