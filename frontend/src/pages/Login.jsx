import { useState, useEffect } from 'react'
import axios from 'axios'
import { useNavigate, Link } from 'react-router-dom'
import { detectOSDevice } from '../utils/deviceDetection'
import { discoverLocalDevice } from '../utils/deviceDiscovery'

const GOOGLE_CLIENT_ID = '913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com'

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    // Initialize Google Sign-In when script loads
    const initGoogleSignIn = () => {
      if (window.google && window.google.accounts) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleSignIn,
        })
        
        // Render the button
        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          {
            type: 'standard',
            size: 'large',
            text: 'sign_in_with',
            shape: 'rectangular',
            theme: 'outline',
            logo_alignment: 'left',
          }
        )
      } else {
        // Retry if Google script hasn't loaded yet
        setTimeout(initGoogleSignIn, 100)
      }
    }

    // Wait for Google script to load
    if (window.google && window.google.accounts) {
      initGoogleSignIn()
    } else {
      window.addEventListener('load', initGoogleSignIn)
      // Also try immediately in case script already loaded
      setTimeout(initGoogleSignIn, 500)
    }

    return () => {
      window.removeEventListener('load', initGoogleSignIn)
    }
  }, [])

  const handleGoogleSignIn = async (response) => {
    try {
      setLoading(true)
      setError('')

      // Send the credential to backend
      const loginResponse = await axios.post('http://localhost:5000/api/google_login', {
        id_token: response.credential
      })

      if (loginResponse.data.access_token) {
        const token = loginResponse.data.access_token
        const user = loginResponse.data.user

        // After Google login, automatically register/update the OS device
        try {
          const osDevice = await detectOSDevice()
          let lastIp = null
          try {
            const ipResponse = await axios.get('http://localhost:5000/api/client_info', {
              params: { timezone: osDevice.timezone }
            })
            lastIp = ipResponse.data.ip || null
          } catch (ipErr) {
            console.warn('Unable to fetch client IP for Google login:', ipErr.response?.data?.error || ipErr.message)
          }

          const osDevicePayload = {
            ...osDevice,
            last_ip: lastIp,
            user_email: user?.email
          }

          await axios.post(
            'http://localhost:5000/api/register_os_device',
            osDevicePayload,
            { headers: { Authorization: `Bearer ${token}` } }
          )
        } catch (deviceErr) {
          console.log('Browser device registration skipped (Google login):', deviceErr.response?.data?.error || deviceErr.message)
        }

        onLogin(token, user)
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Google sign-in failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Prey Project-style: Discover running agent device on localhost
      const deviceDiscovery = await discoverLocalDevice()
      
      // Build login payload
      const loginData = {
        email,
        password
      }
      
      // Link existing agent device if discovered
      if (deviceDiscovery.success && deviceDiscovery.device_id) {
        loginData.device_id = deviceDiscovery.device_id
        if (deviceDiscovery.fingerprint_hash) {
          loginData.fingerprint_hash = deviceDiscovery.fingerprint_hash
        }
        console.log(`[DEVICE-LINK] Linking discovered device: ${deviceDiscovery.device_id}`)
      }

      const response = await axios.post('http://localhost:5000/api/login', loginData)

      if (response.data.access_token) {
        onLogin(response.data.access_token, response.data.user)
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">🛡️ Anti-Theft System</h1>
          <p className="text-gray-600">Sign in to your account</p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="admin@antitheft.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or continue with</span>
            </div>
          </div>

          <div className="mt-4">
            <div
              id="google-signin-button"
              className="w-full flex justify-center"
            ></div>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <div className="text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link to="/signup" className="text-blue-500 hover:text-blue-600 font-medium">
                Sign up
              </Link>
            </p>
          </div>
          <div className="text-center text-sm text-gray-600">
            <p>Default credentials:</p>
            <p className="font-mono text-xs mt-1">admin@antitheft.com / admin123</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login

