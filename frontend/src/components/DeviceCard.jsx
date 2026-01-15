import { formatDateTime } from '../utils/dateFormatter'

const DeviceCard = ({ device, onAction }) => {
  const getStatusColor = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      missing: 'bg-red-100 text-red-800',
      locked: 'bg-yellow-100 text-yellow-800',
      alarm: 'bg-orange-100 text-orange-800',
      wiped: 'bg-gray-100 text-gray-800',
      inactive: 'bg-gray-100 text-gray-800'
    }
    return colors[status] || colors.active
  }

  const isOSDevice = (device.device_type || '').toLowerCase() === 'os_device'

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-semibold text-gray-800">{device.name}</h3>
          <p className="text-sm text-gray-500">{device.device_type || 'Unknown Device'}</p>
          <p className="text-xs text-gray-400 mt-1">ID: {device.device_id}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(device.status)}`}>
          {device.status}
        </span>
      </div>

      {device.last_lat && device.last_lng && (
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            📍 Location: {device.last_lat.toFixed(4)}, {device.last_lng.toFixed(4)}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Last seen: {formatDateTime(device.last_seen)}
          </p>
        </div>
      )}

      {device.is_missing && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-700 font-medium">
            ⚠️ Device marked as missing
          </p>
          {device.missing_since && (
            <p className="text-xs text-red-600 mt-1">
              Since: {formatDateTime(device.missing_since)}
            </p>
          )}
        </div>
      )}

      {!isOSDevice ? (
        <div className="flex space-x-2">
          <button
            onClick={() => onAction(device.device_id, 'lock')}
            className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded transition-colors text-sm font-medium"
          >
            🔒 Lock
          </button>
          <button
            onClick={() => onAction(device.device_id, 'alarm')}
            className="flex-1 bg-orange-500 hover:bg-orange-600 text-white py-2 px-4 rounded transition-colors text-sm font-medium"
          >
            🚨 Alarm
          </button>
          <button
            onClick={() => onAction(device.device_id, 'wipe')}
            className="flex-1 bg-red-500 hover:bg-red-600 text-white py-2 px-4 rounded transition-colors text-sm font-medium"
          >
            🗑️ Wipe
          </button>
        </div>
      ) : (
        <p className="text-xs text-gray-500 mt-2">
          OS devices are view-only. Install the device agent for full control (lock, alarm, wipe).
        </p>
      )}
    </div>
  )
}

export default DeviceCard

