import { useEffect, useState } from 'react'
import axios from 'axios'
import { getRejectionCriteriaLabel } from '../utils/rejectionCriteria'

interface RunOption {
  id: number
  run_id: string
  status: string
  total_loans: number
  exceptions_count: number
  created_at: string
}

interface RejectedLoan {
  seller_loan_number: string
  disposition: string | null
  rejection_criteria: string | null
  loan_data?: Record<string, unknown>
}

export default function RejectedLoans() {
  const [runs, setRuns] = useState<RunOption[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string>('')
  const [rejectedLoans, setRejectedLoans] = useState<RejectedLoan[]>([])
  const [loadingRuns, setLoadingRuns] = useState(true)
  const [loadingLoans, setLoadingLoans] = useState(false)

  useEffect(() => {
    fetchRuns()
  }, [])

  useEffect(() => {
    if (selectedRunId) {
      fetchRejectedLoans(selectedRunId)
    } else {
      setRejectedLoans([])
    }
  }, [selectedRunId])

  const fetchRuns = async () => {
    try {
      const response = await axios.get('/api/runs?limit=50')
      setRuns(response.data ?? [])
      if (response.data?.length && !selectedRunId) {
        setSelectedRunId(response.data[0].run_id)
      }
    } catch (error) {
      console.error('Failed to fetch runs:', error)
    } finally {
      setLoadingRuns(false)
    }
  }

  const fetchRejectedLoans = async (runId: string) => {
    setLoadingLoans(true)
    try {
      const response = await axios.get(
        `/api/loans?run_id=${encodeURIComponent(runId)}&disposition=rejected&limit=500`
      )
      setRejectedLoans(response.data ?? [])
    } catch (error) {
      console.error('Failed to fetch rejected loans:', error)
      setRejectedLoans([])
    } finally {
      setLoadingLoans(false)
    }
  }

  if (loadingRuns) {
    return <div className="text-center py-8">Loading runs...</div>
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Rejected loans</h1>
      <p className="text-sm text-gray-600 mb-6">
        Select a pipeline run to see loans that were rejected and the <strong>rejection criteria</strong> that were not met.
      </p>

      <div className="mb-6">
        <label htmlFor="run-select" className="block text-sm font-medium text-gray-700 mb-2">
          Pipeline run
        </label>
        <select
          id="run-select"
          value={selectedRunId}
          onChange={(e) => setSelectedRunId(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-md min-w-[280px]"
        >
          <option value="">Select a run</option>
          {runs.map((r) => (
            <option key={r.run_id} value={r.run_id}>
              {r.run_id} — {r.total_loans} loans, {r.exceptions_count} rejected —{' '}
              {new Date(r.created_at).toLocaleString()}
            </option>
          ))}
        </select>
      </div>

      {!selectedRunId ? (
        <div className="bg-white shadow rounded-lg p-6 text-sm text-gray-500">
          Select a run to view rejected loans and their rejection criteria.
        </div>
      ) : loadingLoans ? (
        <div className="text-center py-8">Loading rejected loans...</div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <h2 className="text-lg font-medium text-gray-900 p-6 pb-2">
            Rejection criteria (why each loan was rejected)
          </h2>
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
                {rejectedLoans.length === 0 ? (
                  <tr>
                    <td colSpan={2} className="px-6 py-8 text-center text-sm text-gray-500">
                      No rejected loans for this run.
                    </td>
                  </tr>
                ) : (
                  rejectedLoans.map((loan) => (
                    <tr key={loan.seller_loan_number}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {loan.seller_loan_number}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        {getRejectionCriteriaLabel(loan.rejection_criteria)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
