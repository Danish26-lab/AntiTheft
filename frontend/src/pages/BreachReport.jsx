import { useState, useEffect } from 'react'
import axios from 'axios'

const BreachReport = () => {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    fetchBreachReports()
  }, [])

  const fetchBreachReports = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get('http://localhost:5000/api/get_breach_reports', {
        headers: { Authorization: `Bearer ${token}` },
        params: { resolved: false }
      })
      setReports(response.data.reports || [])
    } catch (error) {
      console.error('Error fetching breach reports:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCheckBreach = async () => {
    setChecking(true)
    try {
      const token = localStorage.getItem('token')
      await axios.get('http://localhost:5000/api/detect_breach', {
        headers: { Authorization: `Bearer ${token}` }
      })
      alert('Breach check completed!')
      fetchBreachReports()
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to check for breaches')
    } finally {
      setChecking(false)
    }
  }

  const handleMarkResolved = async (reportId) => {
    try {
      const token = localStorage.getItem('token')
      await axios.post(
        'http://localhost:5000/api/mark_breach_resolved',
        { report_id: reportId },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      fetchBreachReports()
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to mark as resolved')
    }
  }

  const getSeverityColor = (severity) => {
    const colors = {
      low: 'bg-blue-100 text-blue-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800',
    }
    return colors[severity] || colors.medium
  }

  if (loading) {
    return <div className="text-center py-8">Loading breach reports...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-800">Breach Report</h2>
        <button
          onClick={handleCheckBreach}
          disabled={checking}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
        >
          {checking ? 'Checking...' : '🔍 Check for Breaches'}
        </button>
      </div>

      {reports.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-600 text-lg">✅ No breaches detected!</p>
          <p className="text-gray-500 text-sm mt-2">Your credentials appear to be safe.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div key={report.id} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">
                    {report.breach_name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">{report.description || 'No description available'}</p>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>📧 {report.email}</span>
                    <span>📅 {new Date(report.date_detected).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end space-y-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getSeverityColor(report.severity)}`}>
                    {report.severity}
                  </span>
                  <button
                    onClick={() => handleMarkResolved(report.id)}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Mark Resolved
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          <strong>Note:</strong> This system uses the HaveIBeenPwned API to check for compromised credentials.
          If breaches are detected, change your passwords immediately and enable two-factor authentication.
        </p>
      </div>
    </div>
  )
}

export default BreachReport

