/**
 * Get accurate device location using browser geolocation API
 */

export const getAccurateLocation = () => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser'))
      return
    }

    const options = {
      enableHighAccuracy: true, // Use GPS if available
      timeout: 30000, // 30 seconds - wait longer for GPS to get accurate fix
      maximumAge: 0 // Don't use cached location - always get fresh GPS reading
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy, // in meters
          timestamp: position.timestamp
        }
        console.log('Accurate location obtained:', location)
        resolve(location)
      },
      (error) => {
        let errorMessage = 'Unable to retrieve your location'
        switch(error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location access denied. Please enable location permissions.'
            break
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information unavailable.'
            break
          case error.TIMEOUT:
            errorMessage = 'Location request timed out.'
            break
        }
        console.error('Geolocation error:', error)
        reject(new Error(errorMessage))
      },
      options
    )
  })
}

export const watchLocation = (callback, errorCallback) => {
  if (!navigator.geolocation) {
    errorCallback(new Error('Geolocation is not supported'))
    return null
  }

  const options = {
    enableHighAccuracy: true,
    timeout: 5000,
    maximumAge: 1000 // 1 second
  }

  return navigator.geolocation.watchPosition(
    (position) => {
      callback({
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        accuracy: position.coords.accuracy
      })
    },
    errorCallback,
    options
  )
}

