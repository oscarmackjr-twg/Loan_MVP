import { useEffect, useState } from 'react'
import axios from 'axios'

interface Exception {
  id: number
  seller_loan_number: string
  exception_type: string
  exception_category: string
  severity: string
  message: string | null
  created_at: string
}

export default function Exceptions() {
  const [exceptions, setExceptions] = useState<Exception[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    exception_type: '',
    severity: '',
  })

  useEffect(() => {
    fetchExceptions()
  }, [filters])

  const fetchExceptions = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.exception_type) {
        params.append('exception_type', filters.exception_type)
      }
      if (filters.severity) {
        params.append('severity', filters.severity)
      }
      const response = await axios.get(`/api/exceptions?${params}`)
      setExceptions(response.data)
    } catch (error) {
      console.error('Failed to fetch exceptions:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Loan Exceptions</h1>

      <div className="mb-4 flex gap-4">
        <select
          value={filters.exception_type}
          onChange={(e) => setFilters({ ...filters, exception_type: e.target.value })}
          className="px-4 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Types</option>
          <option value="purchase_price">Purchase Price</option>
          <option value="underwriting">Underwriting</option>
          <option value="comap">CoMAP</option>
          <option value="eligibility">Eligibility</option>
        </select>
        <select
          value={filters.severity}
          onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
          className="px-4 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Severities</option>
          <option value="error">Error</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Loan Number
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Severity
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Message
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {exceptions.map((exc) => (
              <tr key={exc.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {exc.seller_loan_number}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {exc.exception_type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {exc.exception_category}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      exc.severity === 'error'
                        ? 'bg-red-100 text-red-800'
                        : exc.severity === 'warning'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {exc.severity}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">{exc.message || '-'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(exc.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
