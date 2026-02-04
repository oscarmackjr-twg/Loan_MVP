import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'

interface RunDetail {
  run_id: string
  status: string
  total_loans: number
  total_balance: number
  exceptions_count: number
  created_at: string
  started_at: string | null
  completed_at: string | null
}

interface Summary {
  run_id: string
  total_loans: number
  total_balance: number
  exceptions_count: number
  eligibility_checks: Record<string, any>
}

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const [run, setRun] = useState<RunDetail | null>(null)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (runId) {
      fetchRunDetail()
      fetchSummary()
    }
  }, [runId])

  const fetchRunDetail = async () => {
    try {
      const response = await axios.get(`/api/runs/${runId}`)
      setRun(response.data)
    } catch (error) {
      console.error('Failed to fetch run detail:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchSummary = async () => {
    try {
      const response = await axios.get(`/api/summary/${runId}`)
      setSummary(response.data)
    } catch (error) {
      console.error('Failed to fetch summary:', error)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  if (!run) {
    return <div className="text-center py-8">Run not found</div>
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Run Details: {run.run_id}</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Run Information</h2>
          <dl className="space-y-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1">
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
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Total Loans</dt>
              <dd className="mt-1 text-sm text-gray-900">{run.total_loans.toLocaleString()}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Total Balance</dt>
              <dd className="mt-1 text-sm text-gray-900">
                ${run.total_balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Exceptions</dt>
              <dd className="mt-1 text-sm text-gray-900">{run.exceptions_count}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Created</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(run.created_at).toLocaleString()}
              </dd>
            </div>
            {run.started_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Started</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(run.started_at).toLocaleString()}
                </dd>
              </div>
            )}
            {run.completed_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Completed</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(run.completed_at).toLocaleString()}
                </dd>
              </div>
            )}
          </dl>
        </div>

        {summary && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Eligibility Checks</h2>
            <div className="space-y-2">
              {Object.entries(summary.eligibility_checks).map(([key, value]: [string, any]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-sm text-gray-700">{key}</span>
                  <span
                    className={`px-2 py-1 text-xs rounded ${
                      value.pass ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {value.pass ? 'PASS' : 'FAIL'} ({value.value?.toFixed(4) || 'N/A'})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="mt-6">
        <a
          href={`/api/exceptions?run_id=${runId}`}
          className="text-blue-600 hover:text-blue-900"
        >
          View All Exceptions →
        </a>
      </div>
    </div>
  )
}
