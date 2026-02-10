import { useEffect, useState } from 'react'
import axios from 'axios'
import { getRejectionCriteriaLabel, REJECTION_CRITERIA_OPTIONS } from '../utils/rejectionCriteria'

interface Exception {
  id: number
  seller_loan_number: string
  exception_type: string
  exception_category: string
  severity: string
  message: string | null
  rejection_criteria: string | null
  created_at: string
}

export default function Exceptions() {
  const [exceptions, setExceptions] = useState<Exception[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    exception_type: '',
    severity: '',
    rejection_criteria: '',
  })

  useEffect(() => {
    fetchExceptions()
  }, [filters])

  const buildExportParams = () => {
    const params = new URLSearchParams()
    if (filters.exception_type) params.append('exception_type', filters.exception_type)
    if (filters.severity) params.append('severity', filters.severity)
    if (filters.rejection_criteria) params.append('rejection_criteria', filters.rejection_criteria)
    return params
  }

  const fetchExceptions = async () => {
    try {
      const params = buildExportParams()
      const response = await axios.get(`/api/exceptions?${params}`)
      setExceptions(response.data)
    } catch (error) {
      console.error('Failed to fetch exceptions:', error)
    } finally {
      setLoading(false)
    }
  }

  const [exporting, setExporting] = useState(false)
  const handleExport = async (format: 'csv' | 'xlsx') => {
    setExporting(true)
    try {
      const params = buildExportParams()
      params.set('format', format)
      const response = await axios.get(`/api/exceptions/export?${params}`, {
        responseType: 'blob',
      })
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const disposition = response.headers['content-disposition']
      const match = disposition?.match(/filename="?([^";]+)"?/)
      link.download = match ? match[1].trim() : `loan_exceptions.${format === 'xlsx' ? 'xlsx' : 'csv'}`
      document.body.appendChild(link)
      link.click()
      window.URL.revokeObjectURL(url)
      link.remove()
    } catch (error: unknown) {
      console.error('Export failed:', error)
      const err = error as { response?: { data?: Blob; status?: number } }
      if (err.response?.status === 404) {
        alert('No exceptions match the current filters. Try different filters or run a pipeline first.')
      } else {
        alert('Export failed. Please try again.')
      }
    } finally {
      setExporting(false)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Loan Exceptions</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleExport('csv')}
            disabled={exporting}
            className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {exporting ? 'Exporting…' : 'Export to CSV'}
          </button>
          <button
            type="button"
            onClick={() => handleExport('xlsx')}
            disabled={exporting}
            className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {exporting ? 'Exporting…' : 'Export to Excel'}
          </button>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-4">
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
        <select
          value={filters.rejection_criteria}
          onChange={(e) => setFilters({ ...filters, rejection_criteria: e.target.value })}
          className="px-4 py-2 border border-gray-300 rounded-md"
          title="Filter by specific criteria that was not met"
        >
          <option value="">All rejection criteria</option>
          {REJECTION_CRITERIA_OPTIONS.map(({ value, label }) => (
            <option key={value} value={value}>{label}</option>
          ))}
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
                Rejection criteria
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
                <td className="px-6 py-4 text-sm text-gray-700 font-medium">
                  {getRejectionCriteriaLabel(exc.rejection_criteria)}
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
