import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import MapView from '../components/MapView'
import LocationPicker from './LocationPicker'
import FileBrowser from '../components/FileBrowser'
import { getAccurateLocation } from '../utils/geolocation'
import { formatDateTime, formatRelativeTime } from '../utils/dateFormatter'

const DeviceDetail = () => {
  const { deviceId } = useParams()
  const navigate = useNavigate()
  const [device, setDevice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activityLogs, setActivityLogs] = useState([])
  const [activeTab, setActiveTab] = useState('map')
  const [showSettingsMenu, setShowSettingsMenu] = useState(false)
  const [showRenameModal, setShowRenameModal] = useState(false)
  const [newDeviceName, setNewDeviceName] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  // Manual location picker removed: we rely on device-reported / GPS location only
  const [showGeofenceModal, setShowGeofenceModal] = useState(false)
  const [geofenceCenter, setGeofenceCenter] = useState(null)
  const [geofenceRadius, setGeofenceRadius] = useState('200')
  const [geofenceWifiSSID, setGeofenceWifiSSID] = useState('')
  const [geofenceSignalThreshold, setGeofenceSignalThreshold] = useState('30') // Default 30% signal strength threshold
  const [availableWifiNetworks, setAvailableWifiNetworks] = useState([])
  const [showLockModal, setShowLockModal] = useState(false)
  const [lockPassword, setLockPassword] = useState('antitheft2024')
  const [showLockMessage, setShowLockMessage] = useState(false)
  const [lockMessage, setLockMessage] = useState('')
  const [showWipeModal, setShowWipeModal] = useState(false)
  const [selectedPaths, setSelectedPaths] = useState([])
  const [wipeStatus, setWipeStatus] = useState(null)
  const [wipeInProgress, setWipeInProgress] = useState(false)
  const [showConfirmModal, setShowConfirmModal] = useState(false)

  // Initialize geofence settings when device loads
  useEffect(() => {
    if (device) {
      setGeofenceRadius(String(device.geofence_radius_m || 200))
      setGeofenceWifiSSID(device.geofence_wifi_ssid || '')
      // Signal threshold stored in radius_m field (repurposed for signal %)
      setGeofenceSignalThreshold(device.geofence_radius_m ? String(device.geofence_radius_m) : '30')
      if (device.geofence_center_lat && device.geofence_center_lng) {
        setGeofenceCenter({
          lat: device.geofence_center_lat,
          lng: device.geofence_center_lng
        })
      }
    }
  }, [device])

  // Auto-detect and fill WiFi SSID when geofence modal opens - completely automatic
  useEffect(() => {
    if (showGeofenceModal) {
      // Always auto-fill with current WiFi SSID if available (reported by agent running on the device)
      if (device?.current_wifi_ssid) {
        setGeofenceWifiSSID(device.current_wifi_ssid)
      }
      // If no current WiFi but device has a saved geofence WiFi, use that
      else if (device?.geofence_wifi_ssid) {
        setGeofenceWifiSSID(device.geofence_wifi_ssid)
      }
    }
  }, [showGeofenceModal, device?.current_wifi_ssid, device?.geofence_wifi_ssid])

  // Initial load: just fetch device details and activity logs.
  // IMPORTANT: we no longer auto-update the device location from this browser,
  // so the location follows the real laptop (reported by the agent) instead of
  // jumping to wherever the dashboard is opened.
  useEffect(() => {
    if (!deviceId) {
      console.error('No deviceId in URL params')
      setLoading(false)
      return
    }

    let isMounted = true

    const init = async () => {
      await fetchDeviceDetails()
      await fetchActivityLogs()
      if (isMounted) {
        setLoading(false)
      }
    }

    init()

    // Set up real-time location refresh every 5 seconds for faster status updates
    const refreshInterval = setInterval(() => {
      if (isMounted) {
        fetchDeviceDetails() // Refresh device location and status
        if (wipeInProgress) {
          fetchWipeStatus() // Poll wipe status if operation is in progress
        }
      }
    }, 5000) // 5 seconds for faster status updates (especially after unlock)

    return () => {
      isMounted = false
      clearInterval(refreshInterval)
    }
    // Only depend on deviceId, not device - prevents infinite loop
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId, wipeInProgress])

  // Track if fetch is in progress to prevent duplicate calls
  const fetchInProgressRef = useRef(false)

  const fetchDeviceDetails = async () => {
    // Prevent duplicate simultaneous calls
    if (fetchInProgressRef.current) {
      return
    }
    
    fetchInProgressRef.current = true
    
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        console.error('No token found')
        navigate('/login')
        setLoading(false)
        return
      }
      
      // Add cache-busting timestamp to ensure fresh data
      const response = await axios.get(`http://localhost:5000/api/get_device_status/${deviceId}?t=${Date.now()}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      if (response.data) {
        console.log('[DeviceDetail] Fetched device data:', {
          device_id: response.data.device_id,
          last_lat: response.data.last_lat,
          last_lng: response.data.last_lng,
          last_location_update: response.data.last_location_update
        })
        setDevice(response.data)
      } else {
        setDevice(null)
      }
    } catch (error) {
      if (error.response?.status === 404) {
        setDevice(null)
      } else if (error.response?.status === 401) {
        alert('Session expired. Please login again.')
        navigate('/login')
      } else {
        setDevice(null)
      }
    } finally {
      setLoading(false)
      fetchInProgressRef.current = false
    }
  }

  // When device is locked, poll status so it flips back to "active" shortly after unlock
  useEffect(() => {
    if (!device || !device.device_id) return
    if (device.status !== 'locked') return

    const intervalId = setInterval(() => {
      fetchDeviceDetails()
    }, 2000) // check every 2s while locked

    return () => clearInterval(intervalId)
  }, [device?.status, device?.device_id])

  const fetchActivityLogs = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`http://localhost:5000/api/get_activity_logs/${deviceId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setActivityLogs(response.data.logs || [])
    } catch (error) {
      console.error('Error fetching activity logs:', error)
    }
  }


  const fetchWipeStatus = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`http://localhost:5000/api/v1/wipe/status/${deviceId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (response.data.has_operation) {
        setWipeStatus(response.data.operation)
        if (response.data.operation.status === 'completed' || response.data.operation.status === 'failed') {
          setWipeInProgress(false)
        }
      } else {
        setWipeStatus(null)
        setWipeInProgress(false)
      }
    } catch (error) {
      console.error('Error fetching wipe status:', error)
    }
  }

  const handleTriggerWipe = async () => {
    if (selectedPaths.length === 0) {
      alert('Please select at least one file or folder to delete')
      return
    }

    setShowConfirmModal(true)
  }

  const confirmWipe = async () => {
    try {
      setWipeInProgress(true)
      setShowConfirmModal(false)
      const token = localStorage.getItem('token')
      const response = await axios.post(
        'http://localhost:5000/api/v1/wipe/trigger',
        {
          device_id: deviceId,
          paths: selectedPaths
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      alert('Wipe operation triggered! The device will begin deleting selected files/folders.')
      setShowWipeModal(false)
      setSelectedPaths([])
      fetchDeviceDetails()
      fetchActivityLogs()
      
      // Start polling for status
      const statusInterval = setInterval(async () => {
        await fetchWipeStatus()
        const token = localStorage.getItem('token')
        const statusResponse = await axios.get(`http://localhost:5000/api/v1/wipe/status/${deviceId}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (statusResponse.data.has_operation) {
          const op = statusResponse.data.operation
          if (op.status === 'completed' || op.status === 'failed') {
            clearInterval(statusInterval)
            setWipeInProgress(false)
            setWipeStatus(op)
          }
        }
      }, 2000)
      
      // Clear interval after 5 minutes max
      setTimeout(() => {
        clearInterval(statusInterval)
      }, 300000)
      
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to trigger wipe operation')
      setWipeInProgress(false)
    }
  }

  const handleAction = async (action) => {
    if (action === 'alarm') {
      if (!window.confirm('Trigger remote alarm on this device?')) return
    } else if (action === 'lock') {
      // Show screen lock modal instead of direct action
      setShowLockModal(true)
      return
    } else if (action === 'message') {
      const message = prompt('Enter alert message:')
      if (!message) return
    } else if (action === 'clear_alarm') {
      if (!window.confirm('Clear the alarm status for this device?')) return
    }

    try {
      const token = localStorage.getItem('token')
      
      // Handle clear alarm separately
      if (action === 'clear_alarm') {
        await axios.post(
          'http://localhost:5000/api/clear_alarm',
          { device_id: deviceId },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        alert('Alarm cleared successfully!')
      } else {
        await axios.post(
          'http://localhost:5000/api/trigger_action',
          { device_id: deviceId, action: action === 'message' ? 'alarm' : action },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        alert(`${action === 'alarm' ? 'Remote alarm' : 'Alert message'} triggered!`)
      }
      fetchDeviceDetails()
      fetchActivityLogs()
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to trigger action')
    }
  }

  const handleConfirmLock = async () => {
    // Get the exact password as typed by user (only trim leading/trailing whitespace)
    const exactPassword = lockPassword.trim()
    
    if (!exactPassword) {
      alert('Please enter an unlock password')
      return
    }

    try {
      const token = localStorage.getItem('token')
      // Send password exactly as user typed it (case-sensitive, preserving exact characters)
      await axios.post(
        'http://localhost:5000/api/trigger_action',
        {
          device_id: deviceId,
          action: 'lock',
          password: exactPassword,  // Send exactly as typed (case-sensitive)
          message: showLockMessage && lockMessage ? lockMessage.trim() : null
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      // Close modal immediately
      setShowLockModal(false)
      setShowLockMessage(false)
      setLockMessage('')
      // Refresh device details and activity logs
      fetchDeviceDetails()
      fetchActivityLogs()
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to send lock command')
    }
  }

  const handleMarkMissing = async () => {
    const isCurrentlyMissing = device?.is_missing
    
    const confirmMessage = isCurrentlyMissing
      ? 'Mark this device as found and restore to normal status?'
      : 'Set this device to Missing? This will activate tracking and capture screenshots.'
    
    if (!window.confirm(confirmMessage)) {
      return
    }

    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(
        'http://localhost:5000/api/mark_as_missing',
        { device_id: deviceId },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      const successMessage = isCurrentlyMissing
        ? 'Device marked as found! Status restored to normal.'
        : 'Device set to Missing!'
      
      alert(successMessage)
      fetchDeviceDetails()
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to update device status')
    }
  }

  const handleUpdateLocation = async () => {
    // IMPORTANT:
    // Do NOT use the browser's GPS here, because that would update the
    // device location to wherever the dashboard is opened (which is often
    // not where the protected laptop actually is).
    //
    // Instead, this button simply refreshes the latest location that was
    // reported by the device agent to the backend.
    try {
      await fetchDeviceDetails()
      alert('✅ Location refreshed from device reports.')
    } catch (error) {
      alert('❌ Failed to refresh location. Please try again.')
    }
  }

  const handleRenameDevice = async () => {
    if (!newDeviceName.trim()) {
      alert('Device name cannot be empty')
      return
    }

    try {
      const token = localStorage.getItem('token')
      await axios.put(
        'http://localhost:5000/api/update_device',
        {
          device_id: deviceId,
          name: newDeviceName.trim()
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      alert('Device renamed successfully!')
      setShowRenameModal(false)
      fetchDeviceDetails()
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to rename device')
    }
  }

  const handleDeleteDevice = async () => {
    try {
      const token = localStorage.getItem('token')
      await axios.delete(
        `http://localhost:5000/api/delete_device?device_id=${deviceId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      alert('Device deleted successfully!')
      navigate('/devices')
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to delete device')
      setShowDeleteConfirm(false)
    }
  }

  const formatLastSeen = (dateString) => {
    return formatRelativeTime(dateString)
  }

  const getStatusColor = () => {
    if (device?.is_missing) return 'bg-red-500'
    if (device?.status === 'active') return 'bg-green-500'
    return 'bg-gray-500'
  }

  const getDeviceIcon = () => {
    if (!device) return '💻'
    const type = (device.device_type || '').toLowerCase()
    if (type.includes('phone') || type.includes('mobile')) return '📱'
    if (type.includes('laptop')) return '💻'
    if (type.includes('tablet')) return '📱'
    if (type.includes('desktop')) return '🖥️'
    return '💻'
  }

  // Close settings menu when clicking outside (only when device is loaded)
  useEffect(() => {
    if (!device || !showSettingsMenu) return
    
    const handleClickOutside = (event) => {
      const target = event.target
      const settingsButton = document.querySelector('[data-settings-button]')
      const settingsMenu = document.querySelector('[data-settings-menu]')
      
      if (settingsMenu && !settingsMenu.contains(target) && !settingsButton?.contains(target)) {
        setShowSettingsMenu(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showSettingsMenu, device])

  // Always render something, even if loading or error
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-center">
          <div className="text-xl text-gray-600">Loading device details...</div>
          <div className="mt-4 text-sm text-gray-500">Please wait...</div>
          <div className="mt-2 text-xs text-gray-400">Device ID: {deviceId}</div>
        </div>
      </div>
    )
  }

  if (!device) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-center">
          <div className="text-xl text-gray-600 mb-4">Device not found</div>
          <div className="text-sm text-gray-500 mb-4">Device ID: {deviceId}</div>
          <button
            onClick={() => navigate('/devices')}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
          >
            Back to Devices
          </button>
        </div>
      </div>
    )
  }

  // Safety check - should never reach here if device is null, but just in case
  if (!device || !device.device_id) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">Error: Invalid device data</div>
          <button
            onClick={() => navigate('/devices')}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
          >
            Back to Devices
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Back Button */}
      <button
        onClick={() => navigate('/devices')}
        className="absolute top-4 left-4 z-50 bg-white hover:bg-gray-100 text-gray-700 px-4 py-2 rounded-lg shadow-md flex items-center space-x-2"
      >
        <span>←</span>
        <span>Back to Devices</span>
      </button>

      {/* Left Sidebar */}
      <div className="w-80 bg-white shadow-lg flex flex-col">
        {/* Device Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2 mb-3">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()}`}></div>
            <span className="font-semibold text-gray-800">Device Info</span>
          </div>
          <div className="text-sm text-gray-600 mb-2">
            <div className="flex items-center space-x-2">
              <span>WiFi: {device.current_wifi_ssid ? 'Connected' : 'Disconnected'}</span>
              <span className="text-gray-400">•</span>
              <span>Battery: {device.battery_percentage !== null && device.battery_percentage !== undefined ? `${device.battery_percentage}%` : 'N/A'}</span>
            </div>
            <div className="text-xs text-gray-500 mt-1">Agent v1.0.0</div>
          </div>
          
          <div className="flex items-center space-x-2 mt-3">
            <span className="text-2xl">{getDeviceIcon()}</span>
            <div>
              <div className="font-medium text-gray-800">{device.name}</div>
              <div className="text-xs text-gray-500">{device.device_type || 'Unknown Device'}</div>
            </div>
          </div>

          <div className="relative mt-3">
            <button 
              data-settings-button
              onClick={() => setShowSettingsMenu(!showSettingsMenu)}
              className="w-full px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded flex items-center space-x-2"
            >
              <span>⚙️</span>
              <span>Settings</span>
            </button>
            
            {showSettingsMenu && (
              <div data-settings-menu className="absolute left-0 mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                <button
                  onClick={() => {
                    setShowRenameModal(true)
                    setNewDeviceName(device.name)
                    setShowSettingsMenu(false)
                  }}
                  className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center space-x-2"
                >
                  <span>✏️</span>
                  <span>Rename Device</span>
                </button>
                <button
                  onClick={() => {
                    setShowDeleteConfirm(true)
                    setShowSettingsMenu(false)
                  }}
                  className="w-full text-left px-4 py-2 hover:bg-red-50 text-red-600 flex items-center space-x-2"
                >
                  <span>🗑️</span>
                  <span>Delete Device</span>
                </button>
              </div>
            )}
          </div>

          <div className="text-xs text-gray-500 mt-2">
            Logged in user: {device.user_id || 'admin'}
          </div>
        </div>

        {/* Missing/Found Toggle Button */}
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleMarkMissing}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
              device.is_missing
                ? 'bg-green-500 hover:bg-green-600 text-white'
                : 'bg-red-500 hover:bg-red-600 text-white'
            }`}
          >
            {device.is_missing ? (
              <>
                <span>✅ Mark as Found</span>
                <span className="block text-xs mt-1 opacity-90">Restore device to normal status</span>
              </>
            ) : (
              <>
                <span>🚨 Set device to Missing</span>
                <span className="block text-xs mt-1 opacity-90">Activate tracking and alerts</span>
              </>
            )}
          </button>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto p-4">
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab('map')}
              className={`w-full text-left px-3 py-2 rounded flex items-center justify-between hover:bg-gray-50 ${
                activeTab === 'map' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
              }`}
            >
              <span>📍 Map and Actions</span>
              <span>→</span>
            </button>
            <button
              onClick={() => setActiveTab('missing')}
              className={`w-full text-left px-3 py-2 rounded flex items-center justify-between hover:bg-gray-50 ${
                activeTab === 'missing' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
              }`}
            >
              <span>🚨 Missing reports</span>
              <span>→</span>
            </button>
            <button
              onClick={() => setActiveTab('activity')}
              className={`w-full text-left px-3 py-2 rounded flex items-center justify-between hover:bg-gray-50 ${
                activeTab === 'activity' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
              }`}
            >
              <span>📋 Activity Log</span>
              <span>→</span>
            </button>
            <button
              onClick={() => setActiveTab('hardware')}
              className={`w-full text-left px-3 py-2 rounded flex items-center justify-between hover:bg-gray-50 ${
                activeTab === 'hardware' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
              }`}
            >
              <span>🔧 Hardware Information</span>
              <span>→</span>
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {activeTab === 'map' && (
          <div className="flex-1 bg-blue-900 flex items-center justify-center relative">
            {device.last_lat && device.last_lng ? (
              <div className="w-full h-full">
                {device && (
                  <MapView
                    devices={device ? [device] : []} 
                    center={device.last_lat && device.last_lng ? { lat: device.last_lat, lng: device.last_lng } : undefined}
                    zoom={15}
                    geofence={device.geofence_enabled && device.geofence_center_lat && device.geofence_center_lng ? {
                      enabled: device.geofence_enabled,
                      center_lat: device.geofence_center_lat,
                      center_lng: device.geofence_center_lng,
                      radius_m: device.geofence_radius_m || 200
                    } : null}
                  />
                )}
                <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex flex-col items-center space-y-2 z-10">
                  <button
                    onClick={handleUpdateLocation}
                    className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg flex items-center space-x-2 shadow-lg"
                    title="Refresh to the latest location reported by the device agent"
                  >
                    <span>📍</span>
                    <span>Refresh Device Location</span>
                  </button>
                  {/* Manual "Set Exact Location" button removed to keep UI simple.
                      Location now comes from device reports and the GPS update button only. */}
                  <button
                    onClick={() => setShowGeofenceModal(true)}
                    className={`px-4 py-2 rounded-lg flex items-center space-x-2 shadow-lg text-sm ${
                      device.geofence_enabled 
                        ? 'bg-red-500 hover:bg-red-600 text-white' 
                        : 'bg-green-500 hover:bg-green-600 text-white'
                    }`}
                    title={device.geofence_enabled ? 'Geofence enabled - Click to configure' : 'Enable geofence alarm'}
                  >
                    <span>🔒</span>
                    <span>{device.geofence_enabled ? `Geofence: ${device.geofence_radius_m || 200}m` : 'Enable Geofence Alarm'}</span>
                  </button>
                  {device.geofence_enabled && (
                    <div className="bg-white px-3 py-1 rounded shadow text-xs text-gray-600">
                      Alarm triggers when device moves outside {device.geofence_radius_m || 200}m radius
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center text-white">
                <h2 className="text-3xl font-semibold mb-4">Unknown location</h2>
                <p className="text-blue-200 mb-6">Get your device's location with a quick refresh.</p>
                <button
                  onClick={handleUpdateLocation}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg flex items-center space-x-2 mx-auto shadow-lg"
                >
                  <span>📍</span>
                  <span>Refresh Device Location</span>
                </button>
                <p className="text-sm text-blue-300 mt-4">
                  This uses the last location reported by the device agent, not your browser.
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'missing' && (
          <div className="flex-1 bg-white p-6 overflow-y-auto">
            <h3 className="text-2xl font-bold text-gray-800 mb-4">Missing Reports</h3>
            {device.is_missing ? (
              <div className="space-y-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h4 className="font-semibold text-red-800 mb-2">Device Marked as Missing</h4>
                  <p className="text-sm text-red-600">
                    Missing since: {formatDateTime(device.missing_since)}
                  </p>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-800 mb-2">Tracking Information</h4>
                  {device.last_lat && device.last_lng ? (
                    <div>
                      <p className="text-sm text-gray-600">Last known location:</p>
                      <p className="text-sm font-mono">{device.last_lat.toFixed(6)}, {device.last_lng.toFixed(6)}</p>
                      <p className="text-xs text-gray-500 mt-1">Last seen: {formatLastSeen(device.last_seen)}</p>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600">No location data available</p>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-600">No missing reports for this device.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="flex-1 bg-white p-6 overflow-y-auto">
            <h3 className="text-2xl font-bold text-gray-800 mb-4">Activity Log</h3>
            <div className="space-y-2">
              {activityLogs.length === 0 ? (
                <p className="text-gray-600 text-center py-8">No activity logs available</p>
              ) : (
                activityLogs.map(log => (
                  <div key={log.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-gray-800">{log.action}</div>
                        {log.description && (
                          <div className="text-sm text-gray-600 mt-1">{log.description}</div>
                        )}
                        {log.lat && log.lng && (
                          <div className="text-xs text-blue-600 mt-1">
                            📍 {log.lat.toFixed(4)}, {log.lng.toFixed(4)}
                          </div>
                        )}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDateTime(log.created_at)}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'hardware' && (
          <div className="flex-1 bg-white p-6 overflow-y-auto">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">Hardware Information</h3>
            
            {/* System Information */}
            <div className="mb-6">
              <h4 className="text-lg font-semibold text-gray-800 mb-3 pb-2 border-b border-gray-200">System</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="space-y-2 text-sm">
                    <div><span className="font-medium text-gray-600">Vendor:</span> <span className="text-gray-800">{device.brand || device.motherboard_vendor || 'Unknown'}</span></div>
                    <div><span className="font-medium text-gray-600">Model:</span> <span className="text-gray-800">{device.model_name || device.motherboard_model || 'Unknown'}</span></div>
                    <div><span className="font-medium text-gray-600">Serial Number:</span> <span className="text-gray-800 font-mono text-xs">{device.serial_number || 'Unknown'}</span></div>
                    <div><span className="font-medium text-gray-600">Device ID:</span> <span className="text-gray-800 font-mono text-xs">{device.device_id}</span></div>
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="space-y-2 text-sm">
                    <div><span className="font-medium text-gray-600">OS:</span> <span className="text-gray-800">{device.os_name || 'Unknown'}</span></div>
                    <div><span className="font-medium text-gray-600">OS Version:</span> <span className="text-gray-800">{device.os_version || 'Unknown'}</span></div>
                    <div><span className="font-medium text-gray-600">Architecture:</span> <span className="text-gray-800">{device.architecture || 'Unknown'}</span></div>
                    <div><span className="font-medium text-gray-600">Hostname:</span> <span className="text-gray-800">{device.hostname || 'Unknown'}</span></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Motherboard Information */}
            {(device.motherboard_vendor || device.motherboard_model) && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-800 mb-3 pb-2 border-b border-gray-200">Motherboard</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="space-y-2 text-sm">
                    <div><span className="font-medium text-gray-600">Vendor:</span> <span className="text-gray-800">{device.motherboard_vendor || 'Unknown'}</span></div>
                    <div><span className="font-medium text-gray-600">Model:</span> <span className="text-gray-800">{device.motherboard_model || 'Unknown'}</span></div>
                    {device.motherboard_serial && (
                      <div><span className="font-medium text-gray-600">Serial:</span> <span className="text-gray-800 font-mono text-xs">{device.motherboard_serial}</span></div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* BIOS Information */}
            {(device.bios_vendor || device.bios_version) && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-800 mb-3 pb-2 border-b border-gray-200">BIOS</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="space-y-2 text-sm">
                    <div><span className="font-medium text-gray-600">Vendor:</span> <span className="text-gray-800">{device.bios_vendor || 'Unknown'}</span></div>
                    <div><span className="font-medium text-gray-600">Version:</span> <span className="text-gray-800">{device.bios_version || 'Unknown'}</span></div>
                  </div>
                </div>
              </div>
            )}

            {/* CPU Information */}
            {(device.cpu_model || device.cpu_cores) && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-800 mb-3 pb-2 border-b border-gray-200">CPU</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="space-y-2 text-sm">
                    <div><span className="font-medium text-gray-600">Model:</span> <span className="text-gray-800">{device.cpu_model || device.cpu_info || 'Unknown'}</span></div>
                    {device.cpu_cores && (
                      <div><span className="font-medium text-gray-600">Cores:</span> <span className="text-gray-800">{device.cpu_cores}</span></div>
                    )}
                    {device.cpu_threads && (
                      <div><span className="font-medium text-gray-600">Threads:</span> <span className="text-gray-800">{device.cpu_threads}</span></div>
                    )}
                    {device.cpu_speed_mhz && (
                      <div><span className="font-medium text-gray-600">Speed:</span> <span className="text-gray-800">
                        {device.cpu_speed_mhz >= 1000 
                          ? `${(device.cpu_speed_mhz / 1000).toFixed(2)} GHz` 
                          : `${device.cpu_speed_mhz} MHz`}
                      </span></div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* RAM Information */}
            {(device.ram_mb || device.ram_gb) && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-800 mb-3 pb-2 border-b border-gray-200">RAM</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="space-y-2 text-sm">
                    <div><span className="font-medium text-gray-600">Total:</span> <span className="text-gray-800">
                      {device.ram_gb ? `${device.ram_gb} GB` : device.ram_mb ? `${(device.ram_mb / 1024).toFixed(2)} GB` : 'Unknown'}
                    </span></div>
                    {device.ram_mb && (
                      <div className="text-xs text-gray-500">({device.ram_mb.toLocaleString()} MB)</div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Network Interfaces */}
            {(device.network_interfaces || device.mac_addresses) && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-800 mb-3 pb-2 border-b border-gray-200">Network Interfaces</h4>
                {device.network_interfaces && device.network_interfaces.length > 0 ? (
                  <div className="space-y-3">
                    {device.network_interfaces.map((iface, idx) => (
                      <div key={idx} className="bg-gray-50 rounded-lg p-4">
                        <div className="space-y-2 text-sm">
                          <div><span className="font-medium text-gray-600">Name:</span> <span className="text-gray-800">{iface.name || 'Unknown'}</span></div>
                          {iface.mac && (
                            <div><span className="font-medium text-gray-600">MAC Address:</span> <span className="text-gray-800 font-mono text-xs">{iface.mac}</span></div>
                          )}
                          {iface.connection_id && (
                            <div><span className="font-medium text-gray-600">Connection ID:</span> <span className="text-gray-800">{iface.connection_id}</span></div>
                          )}
                          {iface.ip_addresses && iface.ip_addresses.length > 0 && (
                            <div>
                              <span className="font-medium text-gray-600">IP Addresses:</span>
                              <div className="mt-1 space-y-1">
                                {iface.ip_addresses.map((ip, ipIdx) => (
                                  <div key={ipIdx} className="text-gray-800 font-mono text-xs">{ip}</div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500">No network interface information available</div>
                  </div>
                )}
                
                {/* MAC Addresses Summary */}
                {device.mac_addresses && device.mac_addresses.length > 0 && (
                  <div className="mt-4">
                    <h5 className="text-sm font-semibold text-gray-700 mb-2">All MAC Addresses</h5>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="space-y-1">
                        {device.mac_addresses.map((mac, idx) => (
                          <div key={idx} className="text-sm font-mono text-gray-800">{mac}</div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Basic Device Info (if hardware info not available) */}
            {!device.serial_number && !device.cpu_model && !device.motherboard_vendor && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-800 mb-3 pb-2 border-b border-gray-200">Device Details</h4>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-sm text-yellow-800">
                    ⚠️ Hardware information not available. This device may need to be registered by the native agent.
                  </p>
                  <div className="mt-3 space-y-2 text-sm">
                    <div><span className="font-medium">Name:</span> {device.name}</div>
                    <div><span className="font-medium">Device Type:</span> {device.device_type || 'Unknown'}</div>
                    <div><span className="font-medium">Status:</span> {device.status}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Geofence Configuration Modal */}
      {showGeofenceModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-800">Configure Geofence Alarm</h3>
              <button
                onClick={() => setShowGeofenceModal(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  <strong>⚠️ Automatic Alarm:</strong> When enabled, the alarm will automatically trigger if your device leaves the safe zone.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Required WiFi Network (SSID)
                </label>
                <div className="flex space-x-2 mb-2">
                  <input
                    type="text"
                    value={geofenceWifiSSID}
                    onChange={(e) => setGeofenceWifiSSID(e.target.value)}
                    className={`flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                      device?.current_wifi_ssid && geofenceWifiSSID === device.current_wifi_ssid 
                        ? 'bg-green-50 border-green-300 cursor-default' 
                        : 'border-gray-300'
                    }`}
                    placeholder={device?.current_wifi_ssid ? "WiFi network auto-filled - ready to save!" : "Enter WiFi network name (e.g., MyHomeWiFi)"}
                    title={device?.current_wifi_ssid && geofenceWifiSSID === device.current_wifi_ssid ? "WiFi network auto-detected. You can edit if needed." : "Enter WiFi network name"}
                  />
                </div>
                {device?.current_wifi_ssid && geofenceWifiSSID === device.current_wifi_ssid && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-2">
                    <p className="text-sm text-green-800">
                      ✅ <strong>Auto-detected:</strong> Using WiFi network <strong>"{device.current_wifi_ssid}"</strong> (automatically filled)
                    </p>
                  </div>
                )}
                {!device?.current_wifi_ssid && device?.last_seen && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-2">
                    <p className="text-sm text-blue-800">
                      💡 <strong>Waiting for WiFi detection:</strong> Make sure your device is connected to WiFi. The WiFi network name will be automatically detected and filled when the device reports its status.
                    </p>
                  </div>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  📍 Reference Location: Will use your current location automatically when geofence is enabled
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  WiFi Signal Strength Threshold (%) - Default: 30%
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  step="1"
                  value={geofenceSignalThreshold}
                  onChange={(e) => {
                    const value = e.target.value
                    setGeofenceSignalThreshold(value)
                  }}
                  onBlur={(e) => {
                    const numValue = parseFloat(e.target.value)
                    if (isNaN(numValue) || numValue < 1) {
                      setGeofenceSignalThreshold('30')
                      alert('Signal threshold must be between 1 and 100%. Set to default 30%.')
                    } else if (numValue > 100) {
                      setGeofenceSignalThreshold('100')
                      alert('Maximum signal threshold is 100%.')
                    } else {
                      setGeofenceSignalThreshold(String(numValue))
                    }
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter signal strength threshold (e.g., 30, 50)"
                />
                <p className="text-xs text-gray-500 mt-1">
                  🚨 Alarm triggers when WiFi signal strength drops below {isNaN(parseFloat(geofenceSignalThreshold)) ? 30 : (parseFloat(geofenceSignalThreshold) || 30)}%
                </p>
                <p className="text-xs text-blue-600 mt-2 font-semibold">
                  💡 How it works: When a thief takes your device and moves it away, the WiFi signal will weaken. When it drops below the threshold, the alarm triggers immediately and you'll receive a notification!
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="enableGeofence"
                  defaultChecked={device?.geofence_enabled || false}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="enableGeofence" className="text-sm font-medium text-gray-700">
                  Enable Geofence Alarm
                </label>
              </div>
            </div>

            <div className="mt-6 flex justify-between items-center">
              <button
                onClick={async () => {
                  if (!window.confirm('Are you sure you want to remove the geofence? The alarm will no longer trigger automatically.')) {
                    return
                  }
                  
                  try {
                    const token = localStorage.getItem('token')
                    await axios.post(
                      'http://localhost:5000/api/set_geofence',
                      {
                        device_id: deviceId,
                        enabled: false
                      },
                      { headers: { Authorization: `Bearer ${token}` } }
                    )
                    
                    alert('Geofence removed successfully!')
                    setShowGeofenceModal(false)
                    fetchDeviceDetails()
                  } catch (error) {
                    alert(error.response?.data?.error || 'Failed to remove geofence')
                  }
                }}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors text-sm font-medium"
              >
                🗑️ Remove Geofence
              </button>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowGeofenceModal(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={async () => {
                    // Validation for WiFi geofence
                    if (!geofenceWifiSSID || geofenceWifiSSID.trim() === '') {
                      if (device?.current_wifi_ssid) {
                        // If device has WiFi but field is empty, auto-fill it
                        setGeofenceWifiSSID(device.current_wifi_ssid)
                        // Continue with the auto-filled value
                      } else {
                        alert('WiFi network name is required. Please wait for auto-detection or enter it manually.')
                        return
                      }
                    }
                    
                    const signalThreshold = parseFloat(geofenceSignalThreshold)
                    if (isNaN(signalThreshold) || signalThreshold < 1 || signalThreshold > 100) {
                      alert('Please enter a valid signal threshold between 1 and 100%')
                      return
                    }
                    
                    // Use device's current location directly (faster, no browser GPS needed)
                    let centerLocation = null
                    if (device?.last_lat && device?.last_lng) {
                      // Use device's reported location - it's already accurate and real-time
                      centerLocation = { lat: device.last_lat, lng: device.last_lng }
                    } else {
                      // Fallback: try quick browser location (5 second timeout)
                      try {
                        const location = await Promise.race([
                          new Promise((resolve, reject) => {
                            if (!navigator.geolocation) {
                              reject(new Error('Geolocation not supported'))
                              return
                            }
                            navigator.geolocation.getCurrentPosition(
                              (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
                              reject,
                              { timeout: 5000, maximumAge: 60000 } // 5 second timeout, allow 1 minute old cache
                            )
                          }),
                          new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
                        ])
                        centerLocation = location
                      } catch (error) {
                        alert('Device location not available yet. Please wait for the device agent to report its location.')
                        return
                      }
                    }
                    
                    try {
                      const token = localStorage.getItem('token')
                      const enabled = document.getElementById('enableGeofence').checked
                      
                      // Show loading state
                      const saveButton = event.target
                      const originalText = saveButton.textContent
                      saveButton.disabled = true
                      saveButton.textContent = 'Saving...'
                      
                      const response = await axios.post(
                        'http://localhost:5000/api/set_geofence',
                        {
                          device_id: deviceId,
                          geofence_type: 'wifi',
                          wifi_ssid: geofenceWifiSSID.trim(),
                          center_lat: centerLocation.lat,
                          center_lng: centerLocation.lng,
                          radius_m: signalThreshold, // Repurpose radius_m to store signal threshold %
                          enabled: enabled
                        },
                        { 
                          headers: { Authorization: `Bearer ${token}` },
                          timeout: 10000 // 10 second timeout to prevent hanging
                        }
                      )
                      
                      saveButton.disabled = false
                      saveButton.textContent = originalText
                      
                      alert(`WiFi Geofence configured! Alarm will trigger when WiFi signal drops below ${signalThreshold}%`)
                      setShowGeofenceModal(false)
                      fetchDeviceDetails()
                    } catch (error) {
                      const saveButton = event.target
                      saveButton.disabled = false
                      saveButton.textContent = 'Save Geofence'
                      
                      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
                        alert('Request timed out. Please check your connection and try again.')
                      } else {
                        alert(error.response?.data?.error || 'Failed to save geofence settings')
                      }
                    }
                  }}
                  className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
                >
                  Save Geofence
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Location Picker Modal removed along with "Set Exact Location" button */}

      {/* Screen Lock Modal */}
      {showLockModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-lg shadow-xl overflow-hidden">
            {/* Blue Header */}
            <div className="bg-blue-600 text-white p-6 relative">
              <button
                onClick={() => {
                  setShowLockModal(false)
                  setShowLockMessage(false)
                  setLockMessage('')
                }}
                className="absolute top-4 right-4 text-white hover:text-gray-200 text-2xl font-bold"
              >
                ×
              </button>
              <h3 className="text-2xl font-bold mb-2">Screen lock</h3>
              <p className="text-blue-100 text-sm">
                You'll lock the device's screen so that no one can use it.
              </p>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              <p className="text-gray-700">
                We went ahead and gave you a password that will <strong>allow you to unlock your device</strong>. 
                You can use it as it is or change it, be our guest! If you lose it, you'll find it by entering the action again.
              </p>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Unlock password
                </label>
                <input
                  type="text"
                  value={lockPassword}
                  onChange={(e) => setLockPassword(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter unlock password"
                  autoComplete="off"
                  autoCapitalize="off"
                  autoCorrect="off"
                  spellCheck="false"
                />
                <p className="mt-1 text-xs text-gray-500">
                  ⚠️ Password is case-sensitive. Use the exact password you enter here to unlock.
                </p>
              </div>

              <div>
                <button
                  onClick={() => setShowLockMessage(!showLockMessage)}
                  className="w-full flex items-center justify-between text-left p-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-2">
                    <span>✏️</span>
                    <span className="text-sm font-medium text-gray-700">
                      Want to display a message on the locked device screen?
                    </span>
                  </div>
                  <span className={`transform transition-transform ${showLockMessage ? 'rotate-180' : ''}`}>
                    ▼
                  </span>
                </button>
                
                {showLockMessage && (
                  <div className="mt-3">
                    <textarea
                      value={lockMessage}
                      onChange={(e) => setLockMessage(e.target.value)}
                      placeholder="Enter a message to display on the locked screen (optional)"
                      rows={4}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                    />
                  </div>
                )}
              </div>

              {/* Info Banner */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center">
                    <span className="text-white text-xs font-bold">i</span>
                  </div>
                </div>
                <p className="text-sm text-blue-800">
                  This action will be executed once the device connects to the server, and will affect all its users.
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-3 border-t border-gray-200">
              <button
                onClick={() => {
                  setShowLockModal(false)
                  setShowLockMessage(false)
                  setLockMessage('')
                }}
                className="px-6 py-2 border border-blue-500 text-blue-500 hover:bg-blue-50 rounded-lg transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmLock}
                className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors font-medium"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {showRenameModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Rename Device</h3>
            <input
              type="text"
              value={newDeviceName}
              onChange={(e) => setNewDeviceName(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') handleRenameDevice()
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4"
              placeholder="Enter new device name"
              autoFocus
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowRenameModal(false)
                  setNewDeviceName('')
                }}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRenameDevice}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-xl font-semibold text-gray-800 mb-2">Delete Device</h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete <strong>{device?.name}</strong>? This action cannot be undone and will remove all associated data.
            </p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteDevice}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Right Actions Sidebar */}
      <div className="w-64 bg-blue-800 text-white flex flex-col">
        <div className="p-4 border-b border-blue-700 flex items-center space-x-2">
          <span>→</span>
          <span className="font-semibold">Actions</span>
        </div>

        <div className="flex-1 p-4">
          <h3 className="font-semibold mb-4 text-blue-200">Device Control</h3>
          
          <div className="space-y-3">
            {device?.status === 'alarm' && (
              <button
                onClick={() => handleAction('clear_alarm')}
                className="w-full bg-green-600 hover:bg-green-500 text-white py-3 px-4 rounded-lg flex items-center space-x-3 transition-colors"
              >
                <span className="text-xl">✅</span>
                <span>Clear Alarm</span>
              </button>
            )}
            
            <button
              onClick={() => handleAction('alarm')}
              className="w-full bg-blue-700 hover:bg-blue-600 text-white py-3 px-4 rounded-lg flex items-center space-x-3 transition-colors"
            >
              <span className="text-xl">🔊</span>
              <span>Remote alarm</span>
            </button>

            <button
              onClick={() => handleAction('message')}
              className="w-full bg-blue-700 hover:bg-blue-600 text-white py-3 px-4 rounded-lg flex items-center space-x-3 transition-colors"
            >
              <span className="text-xl">⚠️</span>
              <span>Alert message</span>
            </button>

            <button
              onClick={() => handleAction('lock')}
              className="w-full bg-blue-700 hover:bg-blue-600 text-white py-3 px-4 rounded-lg flex items-center space-x-3 transition-colors"
            >
              <span className="text-xl">🔒</span>
              <span>Screen lock</span>
            </button>
          </div>

          {/* Data Security Section */}
          <div className="mt-6 pt-6 border-t border-blue-700">
            <h3 className="font-semibold mb-4 text-blue-200">Data Security</h3>
            
            <div className="space-y-3">
              <button
                onClick={() => {
                  setShowWipeModal(true)
                  setSelectedPaths([])
                  setWipeStatus(null)
                }}
                disabled={wipeInProgress}
                className={`w-full bg-gray-700 hover:bg-gray-600 text-white py-3 px-4 rounded-lg flex items-center justify-between transition-colors ${
                  wipeInProgress ? 'opacity-50 cursor-not-allowed' : ''
                }`}
                title="Browse and select files/folders from D:\\ to delete remotely"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-xl">🗑️</span>
                  <span>Custom Wipe</span>
                </div>
                {wipeInProgress && (
                  <span className="text-xs bg-yellow-500 px-2 py-1 rounded">In Progress</span>
                )}
              </button>
              
              <div className="text-xs text-blue-300 mt-2">
                Browse D:\\ drive and select files/folders to delete
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Wipe Data Modal */}
      {showWipeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-6xl h-[90vh] flex flex-col shadow-xl">
            {/* Header */}
            <div className="bg-red-600 text-white p-6 relative flex-shrink-0">
              <button
                onClick={() => {
                  setShowWipeModal(false)
                  setSelectedPaths([])
                  setWipeStatus(null)
                }}
                className="absolute top-4 right-4 text-white hover:text-gray-200 text-2xl font-bold"
              >
                ×
              </button>
              <h3 className="text-2xl font-bold mb-2">Custom Wipe - File Browser</h3>
              <p className="text-red-100 text-sm">
                Browse D:\\ drive and select files/folders to permanently delete
              </p>
            </div>

            {/* Warning Banner */}
            <div className="bg-red-50 border-2 border-red-200 p-4 flex-shrink-0">
              <div className="flex items-start space-x-3">
                <span className="text-2xl">⚠️</span>
                <div>
                  <h4 className="font-bold text-red-800 mb-1">Irreversible Action</h4>
                  <p className="text-sm text-red-700">
                    Selected files and folders will be permanently deleted. This cannot be undone. 
                    Only paths within D:\\ are allowed. System directories are protected.
                  </p>
                </div>
              </div>
            </div>

            {/* File Browser */}
            <div className="flex-1 overflow-hidden p-6">
              <FileBrowser
                deviceId={deviceId}
                selectedPaths={selectedPaths}
                onSelect={setSelectedPaths}
              />
            </div>

            {/* Wipe Status Display */}
            {wipeStatus && (
              <div className={`border-2 rounded-lg p-4 mx-6 mb-4 flex-shrink-0 ${
                wipeStatus.status === 'completed' ? 'bg-green-50 border-green-200' :
                wipeStatus.status === 'failed' ? 'bg-red-50 border-red-200' :
                'bg-blue-50 border-blue-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">
                    {wipeStatus.status === 'completed' ? '✅ Deletion Completed' :
                     wipeStatus.status === 'failed' ? '❌ Deletion Failed' :
                     '⏳ Deletion In Progress'}
                  </span>
                  {wipeStatus.status === 'in_progress' && (
                    <span className="text-sm">{wipeStatus.progress_percentage}%</span>
                  )}
                </div>
                {wipeStatus.status === 'in_progress' && (
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${wipeStatus.progress_percentage}%` }}
                    ></div>
                  </div>
                )}
                <p className="text-xs text-gray-600">
                  {wipeStatus.files_deleted}/{wipeStatus.total_files} items deleted
                  {wipeStatus.error_message && (
                    <span className="block text-red-600 mt-1">{wipeStatus.error_message}</span>
                  )}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-3 border-t border-gray-200 flex-shrink-0">
              <button
                onClick={() => {
                  setShowWipeModal(false)
                  setSelectedPaths([])
                  setWipeStatus(null)
                }}
                className="px-6 py-2 border border-gray-300 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleTriggerWipe}
                disabled={selectedPaths.length === 0 || wipeInProgress}
                className={`px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium ${
                  selectedPaths.length === 0 || wipeInProgress ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                Delete Selected ({selectedPaths.length})
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-2xl shadow-xl">
            <div className="bg-red-600 text-white p-6">
              <h3 className="text-2xl font-bold">⚠️ Confirm Deletion</h3>
            </div>
            <div className="p-6 space-y-4">
              <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
                <p className="text-red-800 font-semibold mb-2">
                  You are about to permanently delete {selectedPaths.length} item(s):
                </p>
                <ul className="list-disc list-inside text-sm text-red-700 space-y-1 max-h-64 overflow-y-auto">
                  {selectedPaths.map((path, idx) => (
                    <li key={idx} className="font-mono text-xs">{path}</li>
                  ))}
                </ul>
                <p className="text-red-800 font-semibold mt-4">
                  This action CANNOT be undone. Are you absolutely sure?
                </p>
              </div>
            </div>
            <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-3 border-t border-gray-200">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="px-6 py-2 border border-gray-300 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={confirmWipe}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
              >
                Yes, Delete Permanently
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DeviceDetail

