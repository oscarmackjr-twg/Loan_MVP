import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import { getRejectionCriteriaLabel } from '../utils/rejectionCriteria'

interface RunDetail {
  run_id: string
  status: string
  total_loans: number
  total_balance: number
  exceptions_count: number
  created_at: string
  started_at: string | null
  completed_at: string | null
  run_weekday_name?: string | null
}

interface Summary {
  run_id: string
  total_loans: number
  total_balance: number
  exceptions_count: number
  eligibility_checks: Record<string, any>
}

interface RejectedLoan {
  seller_loan_number: string
  disposition: string | null
  rejection_criteria: string | null
  loan_data?: Record<string, unknown>
}

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const [run, setRun] = useState<RunDetail | null>(null)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [rejectedLoans, setRejectedLoans] = useState<RejectedLoan[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (runId) {
      fetchRunDetail()
      fetchSummary()
      fetchRejectedLoans()
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

  const fetchRejectedLoans = async () => {
    if (!runId) return
    try {
      const response = await axios.get(`/api/loans?run_id=${encodeURIComponent(runId)}&disposition=rejected&limit=500`)
      setRejectedLoans(response.data ?? [])
    } catch (error) {
      console.error('Failed to fetch rejected loans:', error)
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

      {/* Processing summary: logging of loan processing for this run */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Loan processing summary</h2>
        <p className="text-sm text-gray-600 mb-4">
          This run processed loans and recorded the following. Each rejected loan is tied to a specific <strong>rejection criteria</strong> (see table below).
        </p>
        <dl className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
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
            <dt className="text-sm font-medium text-gray-500">Loans processed</dt>
            <dd className="mt-1 text-sm text-gray-900">{run.total_loans.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Rejected (exceptions)</dt>
            <dd className="mt-1 text-sm text-red-600 font-medium">{run.exceptions_count.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Total balance</dt>
            <dd className="mt-1 text-sm text-gray-900">
              ${run.total_balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </dd>
          </div>
          {run.run_weekday_name && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Run day</dt>
              <dd className="mt-1 text-sm text-gray-900">{run.run_weekday_name}</dd>
            </div>
          )}
          <div>
            <dt className="text-sm font-medium text-gray-500">Started</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {run.started_at ? new Date(run.started_at).toLocaleString() : '—'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Completed</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {run.completed_at ? new Date(run.completed_at).toLocaleString() : '—'}
            </dd>
          </div>
        </dl>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {summary && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Eligibility checks</h2>
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

      {/* Rejected loans: visibility to which loans were rejected and why */}
      <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
        <h2 className="text-lg font-medium text-gray-900 p-6 pb-2">Rejected loans for this run</h2>
        <p className="text-sm text-gray-600 px-6 pb-4">
          Loans that did not meet requirements. <strong>Rejection criteria</strong> shows the specific rule that was not met.
        </p>
        {rejectedLoans.length === 0 ? (
          <div className="px-6 pb-6 text-sm text-gray-500">No rejected loans for this run.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Loan number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rejection criteria
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {rejectedLoans.map((loan) => (
                  <tr key={loan.seller_loan_number}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {loan.seller_loan_number}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {getRejectionCriteriaLabel(loan.rejection_criteria)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="flex gap-4">
        <Link
          to="/exceptions"
          className="text-blue-600 hover:text-blue-900"
        >
          View all exceptions →
        </Link>
        <Link
          to="/rejected-loans"
          className="text-blue-600 hover:text-blue-900"
        >
          Rejected loans by run →
        </Link>
      </div>
    </div>
  )
}
