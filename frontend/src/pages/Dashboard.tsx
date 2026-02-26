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
}

export default function Dashboard() {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [storageType, setStorageType] = useState<string>('local')
  const [runFolder, setRunFolder] = useState('')
  const [runAcceptedDialogOpen, setRunAcceptedDialogOpen] = useState(false)
  const [startedRunId, setStartedRunId] = useState<string | null>(null)
  const [runSubmitting, setRunSubmitting] = useState(false)
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

  const triggerRun = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        alert('You are not logged in. Please log in and try again.')
        window.location.href = '/login'
        return
      }

      setRunSubmitting(true)
      const response = await axios.post('/api/pipeline/run', {
        folder: storageType === 's3' ? '' : runFolder.trim(), // S3: no prefix, always root of input dir; local: path
      })
      setStartedRunId(response.data?.run_id ?? null)
      setRunAcceptedDialogOpen(true)
      setTimeout(fetchRuns, 1500)
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message
      console.error('Pipeline run error:', error)
      
      if (error.response?.status === 401) {
        alert('Your session has expired. Please log in again.')
        window.location.href = '/login'
      } else {
        alert(`Failed to start pipeline: ${errorMessage}`)
      }
    } finally {
      setRunSubmitting(false)
    }
  }

  const closeRunAcceptedDialog = () => {
    setRunAcceptedDialogOpen(false)
    setStartedRunId(null)
    fetchRuns()
  }

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
            ? 'Run reads from s3://bucket/input/input/files_required/. File Manager opens at input/files_required/ by default.'
            : 'Local path to the input folder containing files_required/.'}
        </p>
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
            onClick={triggerRun}
            disabled={runSubmitting}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {runSubmitting ? 'Starting…' : 'Start Pipeline Run'}
          </button>
        </div>
      </div>

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
