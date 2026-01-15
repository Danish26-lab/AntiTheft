import { useEffect, useRef, useMemo, useCallback } from 'react'
import { Loader } from '@googlemaps/js-api-loader'
import { formatDateTime } from '../utils/dateFormatter'

const MapView = ({ devices, center = { lat: 3.139, lng: 101.686 }, zoom = 10, geofence = null }) => {
  const mapRef = useRef(null)
  const markersRef = useRef([])
  const geofenceCircleRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const initializedRef = useRef(false)
  const apiLoadedRef = useRef(false)

  // Memoize center to prevent unnecessary re-renders
  const mapCenter = useMemo(() => {
    if (devices.length > 0 && devices[0].last_lat && devices[0].last_lng) {
      // Ensure coordinates are numbers and in valid ranges
      const lat = Number(devices[0].last_lat)
      const lng = Number(devices[0].last_lng)
      // Validate coordinate ranges (lat: -90 to 90, lng: -180 to 180)
      if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        return { lat, lng }
      }
    }
    return center
  }, [devices.length > 0 ? devices[0]?.last_lat : null, devices.length > 0 ? devices[0]?.last_lng : null, center?.lat, center?.lng])

  // Memoize geofence object to prevent re-renders
  const geofenceMemo = useMemo(() => {
    if (!geofence || !geofence.enabled || !geofence.center_lat || !geofence.center_lng) return null
    return geofence
  }, [geofence?.enabled, geofence?.center_lat, geofence?.center_lng, geofence?.radius_m])

  // Function to update markers and geofence without recreating the map
  const updateMapContent = useCallback(() => {
    if (!mapInstanceRef.current || !initializedRef.current || !apiLoadedRef.current) return
    
    const map = mapInstanceRef.current
    
    // Clear existing markers
    markersRef.current.forEach(marker => marker.setMap(null))
    markersRef.current = []
    
    // Add new markers
    devices.forEach(device => {
      if (device.last_lat && device.last_lng) {
        // Ensure coordinates are numbers and in valid ranges
        const lat = Number(device.last_lat)
        const lng = Number(device.last_lng)
        
        // Debug logging to verify coordinates
        console.log(`[MapView] Device ${device.name} coordinates:`, { 
          raw: { lat: device.last_lat, lng: device.last_lng },
          parsed: { lat, lng },
          isValid: !isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180
        })
        
        // Validate coordinate ranges (lat: -90 to 90, lng: -180 to 180)
        if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) {
          console.warn(`Invalid coordinates for device ${device.name}: lat=${device.last_lat}, lng=${device.last_lng}`)
          return
        }
        
        // Additional validation: Check if coordinates look swapped (common error)
        // For Malaysia: lat should be ~1-7, lng should be ~100-120
        // If lat is > 90 or lng is > 180, they might be swapped
        // Also check if lat is in the lng range (100-120) which would indicate a swap
        let finalLat = lat
        let finalLng = lng
        
        // Detect potential coordinate swap for Malaysia region
        // Malaysia lat range: ~0.5 to 7.5, lng range: ~99 to 120
        // If lat is in the 100-120 range, it's likely swapped
        if (lat >= 100 && lat <= 120 && lng >= 0.5 && lng <= 7.5) {
          console.warn(`[MapView] Detected swapped coordinates for device ${device.name}!`, {
            received: { lat, lng },
            corrected: { lat: lng, lng: lat }
          })
          // Swap them back
          finalLat = lng
          finalLng = lat
        }
        
        let markerColor = '#FF0000'
        if (device.status === 'active' && !device.is_missing) markerColor = '#00FF00'
        if (device.is_missing) markerColor = '#FF0000'
        if (device.status === 'locked') markerColor = '#FFA500'
        
        // Create marker position object explicitly with potentially corrected coordinates
        const markerPosition = { lat: finalLat, lng: finalLng }
        console.log(`[MapView] Creating marker at:`, markerPosition)
        
        const marker = new window.google.maps.Marker({
          position: markerPosition,
          map: map,
          title: device.name,
          label: {
            text: device.name.charAt(0).toUpperCase(),
            color: '#FFFFFF',
            fontSize: '12px',
            fontWeight: 'bold'
          },
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            fillColor: markerColor,
            fillOpacity: 1,
            strokeColor: '#FFFFFF',
            strokeWeight: 2,
            scale: 10,
          }
        })
        
        // Format last seen time properly
        const lastSeenFormatted = device.last_seen ? formatDateTime(device.last_seen) : 'N/A'
        
        const infoWindow = new window.google.maps.InfoWindow({
          content: `
            <div style="padding: 8px; min-width: 200px;">
              <h3 style="font-weight: bold; margin-bottom: 4px;">${device.name}</h3>
              <p style="font-size: 12px; margin: 2px 0;">Status: <strong>${device.status || 'active'}</strong></p>
              <p style="font-size: 11px; color: #666; margin: 2px 0;">${device.device_type || 'Unknown Device'}</p>
              <p style="font-size: 11px; color: #999; margin: 2px 0;">Last seen: ${lastSeenFormatted}</p>
              <p style="font-size: 10px; color: #999; margin-top: 4px;">📍 ${finalLat.toFixed(6)}, ${finalLng.toFixed(6)}</p>
            </div>
          `,
        })
        
        marker.addListener('click', () => {
          markersRef.current.forEach(m => {
            if (m.infoWindow) m.infoWindow.close()
          })
          infoWindow.open(map, marker)
          marker.infoWindow = infoWindow
        })
        
        markersRef.current.push(marker)
      }
    })
    
    // Update geofence circle
    if (geofenceMemo && devices.length === 1) {
      if (geofenceCircleRef.current) {
        geofenceCircleRef.current.setMap(null)
      }
      
      // Ensure geofence coordinates are numbers
      const geofenceLat = Number(geofenceMemo.center_lat)
      const geofenceLng = Number(geofenceMemo.center_lng)
      
      if (isNaN(geofenceLat) || isNaN(geofenceLng) || geofenceLat < -90 || geofenceLat > 90 || geofenceLng < -180 || geofenceLng > 180) {
        console.warn(`Invalid geofence coordinates: lat=${geofenceMemo.center_lat}, lng=${geofenceMemo.center_lng}`)
        return
      }
      
      const circle = new window.google.maps.Circle({
        strokeColor: '#FF0000',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: '#FF0000',
        fillOpacity: 0.15,
        map: map,
        center: { lat: geofenceLat, lng: geofenceLng },
        radius: geofenceMemo.radius_m || 200,
        clickable: false,
        editable: false,
        zIndex: 1
      })
      geofenceCircleRef.current = circle
    } else if (geofenceCircleRef.current) {
      geofenceCircleRef.current.setMap(null)
      geofenceCircleRef.current = null
    }
    
    // Update map center only if it changed significantly
    if (markersRef.current.length > 0 && mapCenter && !isNaN(mapCenter.lat) && !isNaN(mapCenter.lng)) {
      const currentCenter = map.getCenter()
      if (currentCenter) {
        const latDiff = Math.abs(currentCenter.lat() - mapCenter.lat)
        const lngDiff = Math.abs(currentCenter.lng() - mapCenter.lng)
        // Only update if difference is significant (more than ~100m)
        if (latDiff > 0.001 || lngDiff > 0.001) {
          map.setCenter(new window.google.maps.LatLng(mapCenter.lat, mapCenter.lng))
        }
      } else {
        map.setCenter(new window.google.maps.LatLng(mapCenter.lat, mapCenter.lng))
      }
    }
  }, [devices, mapCenter, geofenceMemo])

  // Initialize map only once
  useEffect(() => {
    const initMap = async () => {
      if (!mapRef.current || initializedRef.current) return

      const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY
      
      if (!apiKey) {
        console.warn('Google Maps API key not found')
        if (mapRef.current) {
          mapRef.current.innerHTML = `
            <div class="flex items-center justify-center h-full bg-gray-100 text-gray-600">
              <div class="text-center p-4">
                <p class="text-lg font-semibold mb-2">Map Unavailable</p>
                <p class="text-sm">Please add VITE_GOOGLE_MAPS_API_KEY to your .env file</p>
              </div>
            </div>
          `
        }
        return
      }

      try {
        const loader = new Loader({
          apiKey: apiKey,
          version: 'weekly',
        })

        await loader.load()
        
        if (typeof google === 'undefined' || !google.maps) {
          throw new Error('Google Maps API not loaded')
        }
        
        apiLoadedRef.current = true
        
        const { Map } = await loader.importLibrary('maps')
        const { Marker } = await loader.importLibrary('marker')
        
        // Ensure map center coordinates are numbers
        const centerLat = Number(mapCenter.lat)
        const centerLng = Number(mapCenter.lng)
        const validCenter = (!isNaN(centerLat) && !isNaN(centerLng) && centerLat >= -90 && centerLat <= 90 && centerLng >= -180 && centerLng <= 180)
          ? { lat: centerLat, lng: centerLng }
          : { lat: 3.139, lng: 101.686 } // Default to KL if invalid
        
        // Initialize map only once
        const map = new Map(mapRef.current, {
          center: validCenter,
          zoom: zoom,
          mapTypeControl: true,
          streetViewControl: true,
          fullscreenControl: true,
          disableDefaultUI: false,
        })
        
        mapInstanceRef.current = map
        initializedRef.current = true
        
        // Initial update of markers and geofence
        updateMapContent()
        
      } catch (error) {
        console.error('Error loading Google Maps:', error)
        if (mapRef.current) {
          mapRef.current.innerHTML = `
            <div class="flex items-center justify-center h-full bg-red-50 text-red-600">
              <div class="text-center p-4">
                <p class="text-lg font-semibold mb-2">Map Error</p>
                <p class="text-sm">${error.message}</p>
                <p class="text-xs mt-2 text-gray-500">Please check your Google Maps API key</p>
              </div>
            </div>
          `
        }
      }
    }

    initMap()
  }, []) // Empty deps - only run once on mount

  // Update map content when data changes (but don't recreate the map)
  useEffect(() => {
    if (initializedRef.current && apiLoadedRef.current) {
      updateMapContent()
    }
  }, [updateMapContent])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (markersRef.current.length > 0) {
        markersRef.current.forEach(marker => marker.setMap(null))
        markersRef.current = []
      }
      if (geofenceCircleRef.current) {
        geofenceCircleRef.current.setMap(null)
        geofenceCircleRef.current = null
      }
    }
  }, [])

  return (
    <div className="w-full h-full min-h-[500px] rounded-lg overflow-hidden shadow-lg">
      <div ref={mapRef} className="w-full h-full" />
    </div>
  )
}

export default MapView
