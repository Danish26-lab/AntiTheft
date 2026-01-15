import { useState } from 'react'
import axios from 'axios'
import { useNavigate, Link } from 'react-router-dom'
import { detectOSDevice } from '../utils/deviceDetection'
import { discoverLocalDevice } from '../utils/deviceDiscovery'

const SignUp = ({ onLogin }) => {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // Validation
    if (password.length < 6) {
      setError('Password must be at least 6 characters long')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address')
      return
    }

    setLoading(true)

    try {
      // Prey Project-style: Discover running agent device on localhost
      const deviceDiscovery = await discoverLocalDevice()
      
      // Build registration payload
      const registrationData = {
        email,
        password,
        name: name || email.split('@')[0]
      }
      
      // Link existing agent device if discovered
      if (deviceDiscovery.success && deviceDiscovery.device_id) {
        registrationData.device_id = deviceDiscovery.device_id
        if (deviceDiscovery.fingerprint_hash) {
          registrationData.fingerprint_hash = deviceDiscovery.fingerprint_hash
        }
        console.log(`[DEVICE-LINK] Linking discovered device: ${deviceDiscovery.device_id}`)
      }
      
      // Register user (will link device if device_id provided)
      const response = await axios.post('http://localhost:5000/api/register_user', registrationData)

      if (response.data.user) {
        // Check if device was linked
        if (response.data.device_linked && response.data.device) {
          console.log(`[DEVICE-LINK] Device linked: ${response.data.device.name}`)
        } else {
          console.log('[DEVICE-LINK] No device linked. Start the agent to link your device.')
        }
        
        // Immediately log the user in
        try {
          const loginData = {
            email,
            password
          }
          
          // Include device_id in login if available
          if (deviceDiscovery.success && deviceDiscovery.device_id) {
            loginData.device_id = deviceDiscovery.device_id
          }
          
          const loginResponse = await axios.post('http://localhost:5000/api/login', loginData)

          if (loginResponse.data.access_token) {
            onLogin(loginResponse.data.access_token, loginResponse.data.user)
            navigate('/dashboard')
            return
          }
        } catch (loginErr) {
          // Registration successful but auto-login failed
          setError('Account created successfully! Please login.')
          setTimeout(() => {
            navigate('/login')
          }, 2000)
          return
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">🛡️ Anti-Theft System</h1>
          <p className="text-gray-600">Create your account</p>
        </div>

        {error && (
          <div className={`${error.includes('successfully') ? 'bg-green-100 border-green-400 text-green-700' : 'bg-red-100 border-red-400 text-red-700'} border px-4 py-3 rounded mb-4`}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Full Name
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="John Doe"
            />
          </div>

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
              placeholder="your.email@example.com"
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
              minLength={6}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="At least 6 characters"
            />
            <p className="text-xs text-gray-500 mt-1">Must be at least 6 characters</p>
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Re-enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-500 hover:text-blue-600 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default SignUp

