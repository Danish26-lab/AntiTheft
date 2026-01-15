import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const QRScanner = () => {
  const [scanning, setScanning] = useState(false)
  const [connectionKey, setConnectionKey] = useState('')
  const [error, setError] = useState('')
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const navigate = useNavigate()

  // Check if browser supports camera
  useEffect(() => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError('Camera access not available in this browser. Please use Safari on iOS or Chrome on Android.')
    }
  }, [])

  const startScanning = async () => {
    try {
      setError('')
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment' // Use back camera on mobile
        }
      })
      
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play()
      }
      
      setScanning(true)
      scanQRCode()
    } catch (err) {
      setError('Failed to access camera: ' + err.message)
      console.error('Camera error:', err)
    }
  }

  const stopScanning = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setScanning(false)
  }

  const scanQRCode = async () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    
    if (!video || !canvas || video.readyState !== video.HAVE_ENOUGH_DATA) {
      if (scanning) {
        requestAnimationFrame(scanQRCode)
      }
      return
    }

    const context = canvas.getContext('2d')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    try {
      // Try using jsQR library if available, otherwise use native QR detection
      if (window.jsQR) {
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height)
        const code = window.jsQR(imageData.data, imageData.width, imageData.height)
        
        if (code) {
          setConnectionKey(code.data)
          stopScanning()
          handleConnect(code.data)
        } else if (scanning) {
          requestAnimationFrame(scanQRCode)
        }
      } else {
        // Fallback: Use native BarcodeDetector API (if available)
        if (window.BarcodeDetector) {
          const barcodeDetector = new window.BarcodeDetector({
            formats: ['qr_code']
          })
          const barcodes = await barcodeDetector.detect(canvas)
          
          if (barcodes.length > 0) {
            setConnectionKey(barcodes[0].rawValue)
            stopScanning()
            handleConnect(barcodes[0].rawValue)
          } else if (scanning) {
            requestAnimationFrame(scanQRCode)
          }
        } else {
          // Fallback: Manual entry
          setError('Auto-scan not available. Please enter connection key manually below.')
          stopScanning()
        }
      }
    } catch (err) {
      console.error('Scan error:', err)
      if (scanning) {
        requestAnimationFrame(scanQRCode)
      }
    }
  }

  const handleConnect = async (key) => {
    if (!key) {
      setError('Please enter or scan a connection key')
      return
    }

    try {
      // Send registration request
      const apiUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://192.168.0.19:5000/api' 
        : `http://${window.location.hostname}:5000/api`;
      
      const response = await fetch(`${apiUrl}/register_device`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify({
          device_id: `iphone-${Date.now()}`,
          name: `iPhone (${new Date().toLocaleDateString()})`,
          device_type: 'iphone',
          connection_key: key
        })
      })

      if (response.ok) {
        alert('✅ Device connected successfully!')
        navigate('/devices')
      } else {
        const data = await response.json()
        setError(data.error || 'Failed to connect device')
      }
    } catch (err) {
      setError('Network error: ' + err.message)
    }
  }

  const handleManualEntry = () => {
    if (connectionKey.trim()) {
      handleConnect(connectionKey.trim())
    } else {
      setError('Please enter a connection key')
    }
  }

  useEffect(() => {
    return () => {
      stopScanning()
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">📱 Connect Your iPhone</h1>
        
        <div className="space-y-4">
          {/* Camera View */}
          <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '1/1' }}>
            {scanning ? (
              <>
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover"
                  playsInline
                  muted
                />
                <canvas ref={canvasRef} className="hidden" />
                <div className="absolute inset-0 border-4 border-blue-500 border-dashed rounded-lg pointer-events-none">
                  <div className="absolute top-4 left-4 right-4 text-white text-center bg-black bg-opacity-50 rounded p-2">
                    Point camera at QR code
                  </div>
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                <div className="text-center">
                  <div className="text-4xl mb-2">📷</div>
                  <p>Camera will appear here</p>
                </div>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Manual Entry */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Or enter connection key manually:
            </label>
            <input
              type="text"
              value={connectionKey}
              onChange={(e) => setConnectionKey(e.target.value)}
              placeholder="Paste connection key here"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Buttons */}
          <div className="flex space-x-3">
            {!scanning ? (
              <button
                onClick={startScanning}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-3 px-4 rounded-lg font-medium transition-colors"
              >
                📷 Start Scanner
              </button>
            ) : (
              <button
                onClick={stopScanning}
                className="flex-1 bg-red-500 hover:bg-red-600 text-white py-3 px-4 rounded-lg font-medium transition-colors"
              >
                ⏹️ Stop Scanner
              </button>
            )}
            
            <button
              onClick={handleManualEntry}
              disabled={!connectionKey.trim()}
              className="flex-1 bg-green-500 hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white py-3 px-4 rounded-lg font-medium transition-colors"
            >
              ✅ Connect
            </button>
          </div>

          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-xs text-blue-800">
              <strong>How to use:</strong>
            </p>
            <ol className="text-xs text-blue-700 mt-2 list-decimal list-inside space-y-1">
              <li>Get the QR code from the dashboard</li>
              <li>Click "Start Scanner" and allow camera access</li>
              <li>Point camera at QR code</li>
              <li>Or copy/paste the connection key manually</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  )
}

export default QRScanner

