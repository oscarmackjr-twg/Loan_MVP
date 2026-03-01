import { useEffect, useState } from 'react'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'

interface Holiday {
  id: number
  date: string
  country: string
  name?: string | null
}

const COUNTRY_OPTIONS = [
  { code: 'US', label: 'United States' },
  { code: 'IN', label: 'India' },
  { code: 'GB', label: 'England (UK)' },
  { code: 'SG', label: 'Singapore' },
]

export default function HolidayMaintenance() {
  const { user } = useAuth()
  const [holidays, setHolidays] = useState<Holiday[]>([])
  const [loading, setLoading] = useState(true)
  const [countryFilter, setCountryFilter] = useState<string>('')
  const [newCountry, setNewCountry] = useState<string>('US')
  const [newDate, setNewDate] = useState<string>('')
  const [newName, setNewName] = useState<string>('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (user?.role !== 'admin') {
      setLoading(false)
      return
    }
    fetchHolidays()
  }, [countryFilter, user])

  const fetchHolidays = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (countryFilter) {
        params.append('country', countryFilter)
      }
      const response = await axios.get<Holiday[]>(`/api/admin/holidays?${params.toString()}`)
      setHolidays(response.data)
    } catch (err) {
      console.error('Failed to fetch holidays:', err)
      setError('Failed to load holidays.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newDate || !newCountry) return
    setSaving(true)
    setError(null)
    try {
      await axios.post<Holiday>('/api/admin/holidays', {
        date: newDate,
        country: newCountry,
        name: newName.trim() || null,
      })
      setNewDate('')
      setNewName('')
      if (!countryFilter || countryFilter === newCountry) {
        await fetchHolidays()
      }
    } catch (err) {
      console.error('Failed to create holiday:', err)
      setError('Failed to create holiday.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this holiday?')) return
    setSaving(true)
    setError(null)
    try {
      await axios.delete(`/api/admin/holidays/${id}`)
      setHolidays((prev) => prev.filter((h) => h.id !== id))
    } catch (err) {
      console.error('Failed to delete holiday:', err)
      setError('Failed to delete holiday.')
    } finally {
      setSaving(false)
    }
  }

  if (user?.role !== 'admin') {
    return <div className="text-center py-8 text-red-600">You do not have permission to view this page.</div>
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Holiday Maintenance</h1>
      </div>

      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-3">Filter</h2>
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={countryFilter}
            onChange={(e) => setCountryFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="">All countries</option>
            {COUNTRY_OPTIONS.map((c) => (
              <option key={c.code} value={c.code}>
                {c.code} – {c.label}
              </option>
            ))}
          </select>
          <button
            onClick={fetchHolidays}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-3">Add Holiday</h2>
        <form onSubmit={handleCreate} className="flex flex-wrap items-center gap-3">
          <select
            value={newCountry}
            onChange={(e) => setNewCountry(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            {COUNTRY_OPTIONS.map((c) => (
              <option key={c.code} value={c.code}>
                {c.code} – {c.label}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={newDate}
            onChange={(e) => setNewDate(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            required
          />
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Holiday name (optional)"
            className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Add'}
          </button>
        </form>
      </div>

      {error && <div className="mb-4 text-red-600 text-sm">{error}</div>}

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {loading ? (
          <div className="text-center py-6">Loading holidays…</div>
        ) : holidays.length === 0 ? (
          <div className="text-center py-6 text-gray-500">No holidays found.</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Country
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {holidays.map((h) => (
                <tr key={h.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(h.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{h.country}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{h.name || '—'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => handleDelete(h.id)}
                      disabled={saving}
                      className="text-red-600 hover:text-red-800 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

