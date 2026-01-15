import { useState, useEffect } from 'react'
import axios from 'axios'
import { formatDateTime } from '../utils/dateFormatter'

const MissingMode = () => {
  const [missingDevices, setMissingDevices] = useState([])
  const [activityLogs, setActivityLogs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMissingDevices()
    fetchActivityLogs()
  }, [])

  const fetchMissingDevices = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get('http://localhost:5000/api/get_devices', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const devices = response.data.devices || []
      setMissingDevices(devices.filter(d => d.is_missing))
    } catch (error) {
      console.error('Error fetching missing devices:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchActivityLogs = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get('http://localhost:5000/api/get_activity_logs', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const logs = response.data.logs || []
      // Filter for missing mode related logs and screenshots
      setActivityLogs(logs.filter(log => 
        log.action === 'missing_mode_activated' || 
        log.action === 'screenshot' ||
        log.screenshot_path
      ))
    } catch (error) {
      console.error('Error fetching activity logs:', error)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading missing devices...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-800">Missing Mode</h2>
        <button
          onClick={() => {
            fetchMissingDevices()
            fetchActivityLogs()
          }}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
        >
          Refresh
        </button>
      </div>

      {missingDevices.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-600 text-lg">✅ No missing devices</p>
          <p className="text-gray-500 text-sm mt-2">All your devices are accounted for.</p>
        </div>
      ) : (
        <>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-semibold text-red-800 mb-4">
              🚨 Missing Devices ({missingDevices.length})
            </h3>
            <div className="space-y-3">
              {missingDevices.map((device) => (
                <div key={device.id} className="bg-white rounded p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-gray-800">{device.name}</p>
                      <p className="text-sm text-gray-600">ID: {device.device_id}</p>
                      {device.missing_since && (
                        <p className="text-xs text-gray-500 mt-1">
                          Missing since: {formatDateTime(device.missing_since)}
                        </p>
                      )}
                      {device.last_lat && device.last_lng && (
                        <p className="text-xs text-blue-600 mt-1">
                          Last location: {device.last_lat.toFixed(4)}, {device.last_lng.toFixed(4)}
                        </p>
                      )}
                    </div>
                    <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                      MISSING
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">
              📸 Screenshots & Activity Logs
            </h3>
            {activityLogs.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                No screenshots or activity logs available yet.
              </p>
            ) : (
              <div className="space-y-4">
                {activityLogs.map((log) => (
                  <div key={log.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-medium text-gray-800">{log.action}</p>
                        <p className="text-sm text-gray-600 mt-1">{log.description}</p>
                        {log.lat && log.lng && (
                          <p className="text-xs text-blue-600 mt-1">
                            Location: {log.lat.toFixed(4)}, {log.lng.toFixed(4)}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatDateTime(log.created_at)}
                      </span>
                    </div>
                    {log.screenshot_path && (
                      <div className="mt-3">
                        <p className="text-sm text-gray-600 mb-2">Screenshot:</p>
                        <div className="bg-gray-100 rounded p-4 text-center">
                          <p className="text-gray-500 text-sm">
                            Screenshot captured at: {log.screenshot_path}
                          </p>
                          <p className="text-xs text-gray-400 mt-2">
                            (In production, this would display the actual screenshot image)
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default MissingMode

