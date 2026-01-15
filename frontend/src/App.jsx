import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Login from './pages/Login'
import SignUp from './pages/SignUp'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'
import DeviceDetail from './pages/DeviceDetail'
import BreachReport from './pages/BreachReport'
import MissingMode from './pages/MissingMode'
import QRScanner from './pages/QRScanner'
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      // Verify token by fetching user info
      fetch('http://localhost:5000/api/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(res => {
        if (res.ok) {
          return res.json()
        }
        throw new Error('Invalid token')
      })
      .then(data => {
        setUser(data)
        setIsAuthenticated(true)
      })
      .catch(() => {
        localStorage.removeItem('token')
        setIsAuthenticated(false)
      })
      .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const handleLogin = (token, userData) => {
    localStorage.setItem('token', token)
    setUser(userData)
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setUser(null)
    setIsAuthenticated(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            isAuthenticated ? 
              <Navigate to="/dashboard" /> : 
              <Login onLogin={handleLogin} />
          } 
        />
        <Route 
          path="/signup" 
          element={
            isAuthenticated ? 
              <Navigate to="/dashboard" /> : 
              <SignUp onLogin={handleLogin} />
          } 
        />
        <Route
          path="/device/:deviceId"
          element={
            isAuthenticated ? <DeviceDetail /> : <Navigate to="/login" />
          }
        />
        <Route
          path="/qr-scanner"
          element={<QRScanner />}
        />
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <div className="flex h-screen bg-gray-100">
                <Sidebar />
                <div className="flex-1 flex flex-col overflow-hidden">
                  <Navbar user={user} onLogout={handleLogout} />
                  <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
                    <Routes>
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/devices" element={<Devices />} />
                      <Route path="/breach-report" element={<BreachReport />} />
                      <Route path="/missing-mode" element={<MissingMode />} />
                      <Route path="/" element={<Navigate to="/dashboard" />} />
                    </Routes>
                  </main>
                </div>
              </div>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
    </Router>
  )
}

export default App

