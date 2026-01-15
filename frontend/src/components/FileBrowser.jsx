import React, { useState, useEffect } from 'react'
import axios from 'axios'

const FileBrowser = ({ deviceId, onSelect, selectedPaths = [], onNavigate }) => {
  const [currentPath, setCurrentPath] = useState('D:\\')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedItems, setSelectedItems] = useState(new Set(selectedPaths))

  // Update selected items when prop changes
  useEffect(() => {
    setSelectedItems(new Set(selectedPaths))
  }, [selectedPaths])

  // Fetch files when path changes
  useEffect(() => {
    fetchFiles(currentPath)
  }, [currentPath, deviceId])

  const fetchFiles = async (path) => {
    setLoading(true)
    setError(null)
    
    try {
      // First, request browse
      await axios.post(
        `http://localhost:5000/api/v1/wipe/request_browse/${deviceId}`,
        { path },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      )

      // Poll for result (device agent needs time to process)
      let attempts = 0
      const maxAttempts = 20
      
      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 500)) // Wait 500ms
        
        const response = await axios.get(
          `http://localhost:5000/api/v1/wipe/browse/${deviceId}?path=${encodeURIComponent(path)}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )
        
        const data = response.data
        
        if (!data.pending && data.items) {
          setItems(data.items || [])
          setLoading(false)
          return
        }
        
        if (data.error) {
          setError(data.error)
          setLoading(false)
          return
        }
        
        attempts++
      }
      
      // Timeout
      setError('Timeout waiting for file list. Please try again.')
      setLoading(false)
      
    } catch (err) {
      console.error('Error fetching files:', err)
      setError(err.response?.data?.error || 'Failed to fetch files')
      setLoading(false)
    }
  }

  const handleItemClick = (item) => {
    if (item.type === 'folder') {
      // Navigate into folder
      const newPath = item.path
      setCurrentPath(newPath)
      if (onNavigate) {
        onNavigate(newPath)
      }
    }
  }

  const handleCheckboxChange = (item, checked) => {
    const newSelected = new Set(selectedItems)
    
    if (checked) {
      newSelected.add(item.path)
    } else {
      newSelected.delete(item.path)
    }
    
    setSelectedItems(newSelected)
    if (onSelect) {
      onSelect(Array.from(newSelected))
    }
  }

  const handleParentClick = () => {
    const parentPath = currentPath.split('\\').slice(0, -1).join('\\') || 'D:\\'
    setCurrentPath(parentPath)
    if (onNavigate) {
      onNavigate(parentPath)
    }
  }

  const formatSize = (bytes) => {
    if (bytes === null || bytes === undefined) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  }

  return (
    <div className="w-full h-full flex flex-col">
      {/* Path bar */}
      <div className="bg-gray-100 p-2 border-b border-gray-300 flex items-center space-x-2">
        <button
          onClick={handleParentClick}
          disabled={currentPath === 'D:\\'}
          className={`px-3 py-1 rounded text-sm ${
            currentPath === 'D:\\'
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
        >
          ↑ Up
        </button>
        <div className="flex-1 bg-white px-3 py-1 rounded border border-gray-300 font-mono text-sm">
          {currentPath}
        </div>
        <button
          onClick={() => fetchFiles(currentPath)}
          disabled={loading}
          className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600 disabled:opacity-50"
        >
          🔄 Refresh
        </button>
      </div>

      {/* File list */}
      <div className="flex-1 overflow-y-auto border border-gray-300">
        {loading && (
          <div className="p-8 text-center text-gray-500">
            <div className="animate-spin inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mb-2"></div>
            <p>Loading files...</p>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded m-4">
            <p className="text-red-800 text-sm">⚠️ {error}</p>
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <p>This folder is empty</p>
          </div>
        )}

        {!loading && !error && items.length > 0 && (
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="w-12 px-4 py-2 text-left"></th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Name</th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Type</th>
                <th className="px-4 py-2 text-right text-sm font-semibold text-gray-700">Size</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr
                  key={index}
                  className={`border-b border-gray-200 hover:bg-gray-50 cursor-pointer ${
                    selectedItems.has(item.path) ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => item.type === 'folder' && handleItemClick(item)}
                >
                  <td className="px-4 py-2">
                    <input
                      type="checkbox"
                      checked={selectedItems.has(item.path)}
                      onChange={(e) => {
                        e.stopPropagation()
                        handleCheckboxChange(item, e.target.checked)
                      }}
                      className="cursor-pointer"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">
                        {item.type === 'folder' ? '📁' : '📄'}
                      </span>
                      <span className="font-mono text-sm">{item.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-600">
                    {item.type === 'folder' ? 'Folder' : 'File'}
                  </td>
                  <td className="px-4 py-2 text-right text-sm text-gray-600">
                    {formatSize(item.size)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Selection summary */}
      <div className="bg-gray-50 p-2 border-t border-gray-300 text-sm text-gray-700">
        {selectedItems.size > 0 ? (
          <span>{selectedItems.size} item(s) selected</span>
        ) : (
          <span className="text-gray-500">No items selected</span>
        )}
      </div>
    </div>
  )
}

export default FileBrowser
