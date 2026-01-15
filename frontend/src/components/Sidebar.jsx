import { NavLink } from 'react-router-dom'

const Sidebar = () => {
  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/devices', label: 'Devices', icon: '💻' },
    { path: '/breach-report', label: 'Breach Report', icon: '🔒' },
    { path: '/missing-mode', label: 'Missing Mode', icon: '🚨' },
  ]

  return (
    <aside className="w-64 bg-gray-800 text-white min-h-screen">
      <div className="p-6">
        <h2 className="text-xl font-bold">Navigation</h2>
      </div>
      <nav className="mt-6">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-6 py-3 hover:bg-gray-700 transition-colors ${
                isActive ? 'bg-gray-700 border-r-4 border-blue-500' : ''
              }`
            }
          >
            <span className="text-xl">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

export default Sidebar

