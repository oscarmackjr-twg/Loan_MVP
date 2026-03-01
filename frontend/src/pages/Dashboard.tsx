import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

interface RunSummary {
  run_id: string
  status: string
  total_loans: number
  total_balance: number
  exceptions_count: number
  created_at: string
  last_phase?: string | null
}

/** Human-readable labels for pipeline last_phase (for run progress panel). */
const PHASE_LABELS: Record<string, string> = {
  load_reference_data: 'Loading reference data (MASTER_SHEET, Underwriting grids…)',
  load_input_files: 'Loading input files (Tape20Loans, SFY/PRIME exhibits…)',
  normalize_loans: 'Processing loans and tagging',
  underwriting: 'Running underwriting checks',
  comap: 'Running CoMAP checks',
  eligibility: 'Running eligibility checks',
  export_reports: 'Exporting reports',
  save_db: 'Saving to database and archiving',
}
function phaseLabel(phase: string | null | undefined): string {
  if (!phase) return 'Starting…'
  return PHASE_LABELS[phase] ?? phase
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

export default function Dashboard() {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [storageType, setStorageType] = useState<string>('local')
  const [runFolder, setRunFolder] = useState('')
  const [runAcceptedDialogOpen, setRunAcceptedDialogOpen] = useState(false)
  const [startedRunId, setStartedRunId] = useState<string | null>(null)
  const [runSubmitting, setRunSubmitting] = useState(false)
  const [effectiveDateModalOpen, setEffectiveDateModalOpen] = useState(false)
  const [effectiveDateInput, setEffectiveDateInput] = useState<string>('')
  const [stats, setStats] = useState({
    totalRuns: 0,
    completedRuns: 0,
    totalLoans: 0,
    totalExceptions: 0,
  })

  useEffect(() => {
    fetchRuns()
    axios.get('/api/config').then((r) => {
      const st = r.data?.storage_type ?? 'local'
      setStorageType(st)
      if (st === 'local') {
        setRunFolder('C:/Users/omack/Intrepid/pythonFramework/loan_engine/legacy')
      }
      // S3: no folder field used; run always reads from root of input directory
    }).catch(() => {})
  }, [])

  // Poll runs list while any run is in progress so progress panel and last_phase stay updated
  useEffect(() => {
    const hasRunning = runs.some((r) => r.status === 'running')
    if (!hasRunning) return
    const interval = setInterval(fetchRuns, 3000)
    return () => clearInterval(interval)
  }, [runs])

  const fetchRuns = async () => {
    try {
      const response = await axios.get('/api/runs?limit=10')
      setRuns(response.data)
      
      // Calculate stats
      const completed = response.data.filter((r: RunSummary) => r.status === 'completed')
      setStats({
        totalRuns: response.data.length,
        completedRuns: completed.length,
        totalLoans: completed.reduce((sum: number, r: RunSummary) => sum + r.total_loans, 0),
        totalExceptions: completed.reduce((sum: number, r: RunSummary) => sum + r.exceptions_count, 0),
      })
    } catch (error) {
      console.error('Failed to fetch runs:', error)
    } finally {
      setLoading(false)
    }
  }

  const openEffectiveDateModal = () => {
    setEffectiveDateInput(formatEffectiveDate(new Date()))
    setEffectiveDateModalOpen(true)
  }

  const closeEffectiveDateModal = () => {
    setEffectiveDateModalOpen(false)
  }

  const triggerRun = async (tdayYYYYMMDD: string | null) => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        alert('You are not logged in. Please log in and try again.')
        window.location.href = '/login'
        return
      }

      setRunSubmitting(true)
      const payload: { folder: string; tday?: string } = {
        folder: storageType === 's3' ? '' : runFolder.trim(),
      }
      if (tdayYYYYMMDD) payload.tday = tdayYYYYMMDD

      const response = await axios.post('/api/pipeline/run', payload)
      setStartedRunId(response.data?.run_id ?? null)
      setEffectiveDateModalOpen(false)
      setRunAcceptedDialogOpen(true)
      setTimeout(fetchRuns, 1500)
    } catch (error: any) {
      console.error('Pipeline run error:', error)
      if (error.response?.status === 401) {
        alert('Your session has expired. Please log in again.')
        window.location.href = '/login'
      } else if (error.response?.status === 409) {
        alert(error.response?.data?.detail ?? 'Another run is already in progress. Wait or cancel it before starting a new run.')
        fetchRuns()
      } else {
        alert(pipelineRunFailureMessage(error))
      }
    } finally {
      setRunSubmitting(false)
    }
  }

  const confirmStartRun = () => {
    const tday = parseEffectiveDateToApi(effectiveDateInput)
    if (effectiveDateInput.trim() && !tday) {
      alert('Please enter the effective date in mm/dd/yyyy format.')
      return
    }
    triggerRun(tday ?? null)
  }

  const closeRunAcceptedDialog = () => {
    setRunAcceptedDialogOpen(false)
    setStartedRunId(null)
    fetchRuns()
  }

  const hasRunningRun = runs.some((r) => r.status === 'running')

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      </div>

      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-2">Start pipeline run</h2>
        <p className="text-sm text-gray-500 mb-3">
          {storageType === 's3'
            ? 'Run reads from the inputs area (files_required/). File Manager opens at files_required/ by default.'
            : 'Local path to the input folder containing files_required/.'}
        </p>
        {hasRunningRun && (
          <p className="text-sm text-amber-600 mb-2">
            A run is in progress. Cancel it in the table below or wait for it to finish before starting another.
          </p>
        )}
        {hasRunningRun && (
          <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <h3 className="text-sm font-semibold text-amber-900 mb-2">Run in progress</h3>
            {runs
              .filter((r) => r.status === 'running')
              .map((run) => (
                <div key={run.run_id} className="text-sm text-amber-800">
                  <div className="font-mono font-medium">
                    <Link to={`/runs/${run.run_id}`} className="text-amber-900 hover:underline">
                      {run.run_id}
                    </Link>
                  </div>
                  <div className="mt-1 text-amber-700">
                    Current step: {phaseLabel(run.last_phase)}
                  </div>
                  <p className="mt-1 text-xs text-amber-600">
                    This panel updates every few seconds. If the run fails, the step above shows where it stopped (helps troubleshooting).
                  </p>
                </div>
              ))}
          </div>
        )}
        <div className="flex flex-wrap items-center gap-3">
          {storageType === 's3' ? null : (
            <input
              type="text"
              value={runFolder}
              onChange={(e) => setRunFolder(e.target.value)}
              placeholder="C:/path/to/input/folder"
              className="flex-1 min-w-[200px] rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          )}
          <button
            onClick={openEffectiveDateModal}
            disabled={runSubmitting || hasRunningRun}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {runSubmitting ? 'Starting…' : 'Start Pipeline Run'}
          </button>
        </div>
      </div>

      {/* Dialog: effective date (Tday) for pipeline run */}
      {effectiveDateModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="effective-date-title"
        >
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 id="effective-date-title" className="text-lg font-semibold text-gray-900 mb-2">
              Effective date for run
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              This date (Tday) is used as the base for file discovery and pdate calculation. Enter in <strong>mm/dd/yyyy</strong> format.
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
              aria-describedby="effective-date-hint"
            />
            <p id="effective-date-hint" className="text-xs text-gray-500 mb-4">
              Defaults to today. Override to run as of another date.
            </p>
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
                onClick={confirmStartRun}
                disabled={runSubmitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {runSubmitting ? 'Starting…' : 'Start Run'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dialog: command accepted, run in progress */}
      {runAcceptedDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" role="dialog" aria-modal="true" aria-labelledby="run-accepted-title">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 id="run-accepted-title" className="text-lg font-semibold text-gray-900 mb-2">
              Command accepted
            </h2>
            <p className="text-gray-600 mb-4">
              The pipeline run has been accepted and is in progress. You can track it in the Recent Runs table below or open the run for details.
            </p>
            {startedRunId && (
              <p className="text-sm text-gray-500 mb-4 font-mono">
                Run ID: {startedRunId}
              </p>
            )}
            <div className="flex justify-end">
              <button
                onClick={closeRunAcceptedDialog}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="text-sm font-medium text-gray-500">Total Runs</div>
            <div className="mt-1 text-3xl font-semibold text-gray-900">{stats.totalRuns}</div>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="text-sm font-medium text-gray-500">Completed Runs</div>
            <div className="mt-1 text-3xl font-semibold text-green-600">{stats.completedRuns}</div>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="text-sm font-medium text-gray-500">Total Loans</div>
            <div className="mt-1 text-3xl font-semibold text-gray-900">
              {stats.totalLoans.toLocaleString()}
            </div>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="text-sm font-medium text-gray-500">Total Exceptions</div>
            <div className="mt-1 text-3xl font-semibold text-red-600">{stats.totalExceptions}</div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Runs</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Run ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Loans
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Balance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Exceptions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {runs.map((run) => (
                  <tr key={run.run_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      <Link
                        to={`/runs/${run.run_id}`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        {run.run_id}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          run.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : run.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : run.status === 'cancelled'
                            ? 'bg-gray-100 text-gray-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {run.total_loans.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${run.total_balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {run.exceptions_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {run.status === 'running' && (
                        <button
                          type="button"
                          onClick={async () => {
                            if (!confirm(`Cancel run ${run.run_id}?`)) return
                            try {
                              await axios.post(`/api/runs/${run.run_id}/cancel`)
                              fetchRuns()
                            } catch (e: any) {
                              alert(e.response?.data?.detail ?? e.message ?? 'Failed to cancel run')
                            }
                          }}
                          className="text-red-600 hover:text-red-800 font-medium"
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
