import { useEffect, useRef } from 'react'
import { Loader } from '@googlemaps/js-api-loader'

const LocationPicker = ({ onLocationSelect, initialLocation }) => {
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const mapRef_instance = useRef(null)

  useEffect(() => {
    const initMap = async () => {
      if (!mapRef.current) return

      const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY
      if (!apiKey) {
        console.error('Google Maps API key not found')
        return
      }

      const loader = new Loader({
        apiKey: apiKey,
        version: 'weekly',
      })

      try {
        await loader.load()
        
        if (typeof google === 'undefined' || !google.maps) {
          throw new Error('Google Maps API not loaded')
        }
        
        const { Map } = await loader.importLibrary('maps')
        const { Marker } = await loader.importLibrary('marker')

        // Initialize map with initial location or default
        const center = initialLocation || { lat: 3.139, lng: 101.686 }
        
        const map = new Map(mapRef.current, {
          center: center,
          zoom: 15,
          mapTypeControl: true,
          streetViewControl: true,
        })

        // Add marker
        const marker = new Marker({
          position: center,
          map: map,
          draggable: true,
          title: 'Drag to set device location'
        })

        markerRef.current = marker
        mapRef_instance.current = map

        // Update location when marker is dragged
        marker.addListener('dragend', () => {
          const position = marker.getPosition()
          onLocationSelect({
            lat: position.lat(),
            lng: position.lng()
          })
        })

        // Update location when map is clicked
        map.addListener('click', (e) => {
          const lat = e.latLng.lat()
          const lng = e.latLng.lng()
          marker.setPosition({ lat, lng })
          onLocationSelect({ lat, lng })
        })

      } catch (error) {
        console.error('Error loading Google Maps:', error)
      }
    }

    initMap()
  }, [])

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          }
          
          if (markerRef.current && mapRef_instance.current) {
            markerRef.current.setPosition(location)
            mapRef_instance.current.setCenter(location)
            mapRef_instance.current.setZoom(17)
          }
          
          onLocationSelect(location)
        },
        (error) => {
          alert('Error getting your location: ' + error.message)
        }
      )
    } else {
      alert('Geolocation is not supported by your browser')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Select Device Location</h3>
        <button
          onClick={getCurrentLocation}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm"
        >
          📍 Use My Current Location
        </button>
      </div>
      <div className="w-full h-96 rounded-lg overflow-hidden border border-gray-300">
        <div ref={mapRef} className="w-full h-full" />
      </div>
      <p className="text-sm text-gray-600">
        Click on the map or drag the marker to set the exact location
      </p>
    </div>
  )
}

export default LocationPicker

