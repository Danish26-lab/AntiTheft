import { useState, useEffect } from 'react'
import axios from 'axios'
import MapView from '../components/MapView'
import { formatDateTime } from '../utils/dateFormatter'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalDevices: 0,
    missingDevices: 0,
    activeDevices: 0,
    breachAlerts: 0,
  })
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }

      const [devicesRes, breachRes] = await Promise.all([
        axios.get('http://localhost:5000/api/get_devices', { headers }),
        axios.get('http://localhost:5000/api/get_breach_reports', { headers }),
      ])

      const devicesData = devicesRes.data.devices || []
      const missingDevices = devicesData.filter(d => d.is_missing)
      const activeDevices = devicesData.filter(d => d.status === 'active')

      setStats({
        totalDevices: devicesData.length,
        missingDevices: missingDevices.length,
        activeDevices: activeDevices.length,
        breachAlerts: breachRes.data.reports?.length || 0,
      })

      setDevices(devicesData)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading dashboard...</div>
  }

  const StatCard = ({ title, value, icon, color }) => (
    <div className={`bg-white rounded-lg shadow-md p-6 ${color}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{value}</p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-800">Dashboard</h2>
        <button
          onClick={fetchDashboardData}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Devices"
          value={stats.totalDevices}
          icon="💻"
          color="border-l-4 border-blue-500"
        />
        <StatCard
          title="Missing Devices"
          value={stats.missingDevices}
          icon="🚨"
          color="border-l-4 border-red-500"
        />
        <StatCard
          title="Active Devices"
          value={stats.activeDevices}
          icon="✅"
          color="border-l-4 border-green-500"
        />
        <StatCard
          title="Breach Alerts"
          value={stats.breachAlerts}
          icon="🔒"
          color="border-l-4 border-orange-500"
        />
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Device Locations</h3>
        <MapView devices={devices} />
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Recent Activity</h3>
        <div className="space-y-2">
          {devices.slice(0, 5).map((device) => (
            <div key={device.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <p className="font-medium text-gray-800">{device.name}</p>
                <p className="text-sm text-gray-500">
                  Status: {device.status} • Last seen: {formatDateTime(device.last_seen)}
                </p>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs ${
                device.status === 'active' ? 'bg-green-100 text-green-800' :
                device.status === 'missing' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {device.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Dashboard

