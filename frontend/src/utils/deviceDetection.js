/**
 * Real OS-level device detection using User-Agent Client Hints API (modern browsers)
 * with fallback to user-agent parsing for older browsers.
 * 
 * Detects:
 * - OS name & version (Windows 11, macOS Sonoma, etc.)
 * - Architecture (x64, arm64)
 * - Device class (laptop, desktop, mobile, tablet)
 * - Browser name & version
 * - Platform (Win32, MacIntel, Linux x86_64)
 * - GPU renderer (WebGL)
 * - Screen resolution, timezone
 * 
 * Generates persistent device_id stored in localStorage.
 */

/**
 * Get GPU renderer information via WebGL
 */
function getGPURenderer() {
  try {
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    if (!gl) return null
    
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info')
    if (debugInfo) {
      return gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || null
    }
    return null
  } catch {
    return null
  }
}

/**
 * Map Windows NT version to Windows version name
 */
function mapWindowsVersion(ntVersion) {
  const versionMap = {
    '10.0': 'Windows 11', // Windows 11 reports as 10.0
    '6.3': 'Windows 8.1',
    '6.2': 'Windows 8',
    '6.1': 'Windows 7',
    '6.0': 'Windows Vista',
    '5.1': 'Windows XP'
  }
  return versionMap[ntVersion] || `Windows ${ntVersion}`
}

/**
 * Map macOS version to macOS name
 */
function mapMacOSVersion(version) {
  const parts = version.split('.')
  const major = parseInt(parts[0]) || 0
  const minor = parseInt(parts[1]) || 0
  
  const versionMap = {
    '14': 'Sonoma',
    '13': 'Ventura',
    '12': 'Monterey',
    '11': 'Big Sur',
    '10.15': 'Catalina',
    '10.14': 'Mojave',
    '10.13': 'High Sierra'
  }
  
  const key = `${major}.${minor}`
  if (versionMap[key]) {
    return `macOS ${versionMap[key]}`
  }
  return `macOS ${version}`
}

/**
 * Detect device class from user agent and screen size
 */
function detectDeviceClass(userAgent, screenWidth, screenHeight) {
  const ua = userAgent.toLowerCase()
  
  // Mobile devices
  if (ua.includes('mobile') || ua.includes('android')) {
    return 'mobile'
  }
  
  // Tablets
  if (ua.includes('tablet') || ua.includes('ipad')) {
    return 'tablet'
  }
  
  // iOS devices
  if (ua.includes('iphone')) {
    return 'mobile'
  }
  if (ua.includes('ipad')) {
    return 'tablet'
  }
  
  // Desktop/laptop detection based on screen size and platform
  // Laptops typically have screens between 1280x720 and 3840x2160
  // Desktops often have larger or multiple displays
  if (screenWidth >= 1920 && screenHeight >= 1080) {
    // Large screen - likely desktop
    return 'desktop'
  } else if (screenWidth >= 1280) {
    // Medium-large screen - likely laptop
    return 'laptop'
  } else {
    // Smaller screen - default to laptop for desktop OS
    return 'laptop'
  }
}

/**
 * Parse user agent string (fallback when Client Hints not available)
 */
function parseUserAgent(userAgent) {
  const ua = userAgent
  let osName = 'Unknown OS'
  let osVersion = ''
  let architecture = 'unknown'
  let deviceClass = 'desktop'
  
  // Windows detection
  if (ua.includes('Windows NT')) {
    osName = 'Windows'
    const match = ua.match(/Windows NT ([0-9.]+)/)
    if (match) {
      const ntVersion = match[1]
      osVersion = mapWindowsVersion(ntVersion)
    }
    // Architecture detection for Windows
    if (ua.includes('WOW64') || ua.includes('Win64')) {
      architecture = 'x64'
    } else if (ua.includes('ARM64')) {
      architecture = 'arm64'
    } else {
      architecture = 'x86' // 32-bit
    }
    deviceClass = detectDeviceClass(ua, window.screen?.width || 1920, window.screen?.height || 1080)
  }
  // macOS detection
  else if (ua.includes('Mac OS X') || ua.includes('Macintosh')) {
    osName = 'macOS'
    const match = ua.match(/Mac OS X ([0-9_]+)/)
    if (match) {
      const version = match[1].replace(/_/g, '.')
      osVersion = mapMacOSVersion(version)
    }
    // macOS architecture
    if (ua.includes('Intel')) {
      architecture = 'x64'
    } else if (ua.includes('Apple')) {
      architecture = 'arm64' // Apple Silicon
    }
    deviceClass = detectDeviceClass(ua, window.screen?.width || 1920, window.screen?.height || 1080)
  }
  // Linux detection
  else if (ua.includes('Linux')) {
    osName = 'Linux'
    // Try to detect distribution
    if (ua.includes('Ubuntu')) {
      const match = ua.match(/Ubuntu\/([0-9.]+)/)
      if (match) osVersion = `Ubuntu ${match[1]}`
      else osVersion = 'Ubuntu'
    } else if (ua.includes('Fedora')) {
      osVersion = 'Fedora'
    } else {
      osVersion = 'Linux'
    }
    // Architecture
    if (ua.includes('x86_64') || ua.includes('x64')) {
      architecture = 'x64'
    } else if (ua.includes('aarch64') || ua.includes('arm64')) {
      architecture = 'arm64'
    } else {
      architecture = 'x64' // Default assumption
    }
    deviceClass = detectDeviceClass(ua, window.screen?.width || 1920, window.screen?.height || 1080)
  }
  // Android detection
  else if (ua.includes('Android')) {
    osName = 'Android'
    const match = ua.match(/Android ([0-9.]+)/)
    if (match) osVersion = `Android ${match[1]}`
    deviceClass = 'mobile'
    architecture = 'arm64' // Most Android devices are ARM
  }
  // iOS detection
  else if (ua.includes('iPhone') || ua.includes('iPad')) {
    osName = 'iOS'
    const match = ua.match(/OS ([0-9_]+)/)
    if (match) {
      const version = match[1].replace(/_/g, '.')
      osVersion = `iOS ${version}`
    }
    deviceClass = ua.includes('iPad') ? 'tablet' : 'mobile'
    architecture = 'arm64' // iOS devices are ARM
  }
  
  return { osName, osVersion, architecture, deviceClass }
}

/**
 * Detect browser name and version
 */
function detectBrowser(userAgent) {
  const ua = userAgent
  let browserName = 'Unknown Browser'
  let browserVersion = ''
  
  if (ua.includes('Edg/')) {
    browserName = 'Edge'
    const match = ua.match(/Edg\/([0-9.]+)/)
    if (match) browserVersion = match[1]
  } else if (ua.includes('Chrome/') && !ua.includes('Edg/') && !ua.includes('OPR/')) {
    browserName = 'Chrome'
    const match = ua.match(/Chrome\/([0-9.]+)/)
    if (match) browserVersion = match[1]
  } else if (ua.includes('Firefox/')) {
    browserName = 'Firefox'
    const match = ua.match(/Firefox\/([0-9.]+)/)
    if (match) browserVersion = match[1]
  } else if (ua.includes('Safari/') && !ua.includes('Chrome/')) {
    browserName = 'Safari'
    const match = ua.match(/Version\/([0-9.]+)/)
    if (match) browserVersion = match[1]
  }
  
  return { browserName, browserVersion }
}

/**
 * Main device detection function
 * Uses User-Agent Client Hints API when available, falls back to parsing user agent
 */
export async function detectOSDevice() {
  const userAgent = navigator.userAgent || ''
  const platform = navigator.platform || ''
  const screenWidth = window.screen?.width || 0
  const screenHeight = window.screen?.height || 0
  const screenResolution = `${screenWidth}x${screenHeight}`
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
  
  // Persistent device ID
  const STORAGE_KEY = 'device_id'
  let deviceId = null
  try {
    deviceId = localStorage.getItem(STORAGE_KEY)
  } catch {
    deviceId = null
  }
  
  if (!deviceId) {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
      deviceId = window.crypto.randomUUID()
    } else {
      deviceId = `dev-${Math.random().toString(36).substring(2)}-${Date.now().toString(36)}`
    }
    try {
      localStorage.setItem(STORAGE_KEY, deviceId)
    } catch {
      // Best-effort only
    }
  }
  
  let osName = 'Unknown OS'
  let osVersion = ''
  let architecture = 'unknown'
  let deviceClass = 'desktop'
  let browserName = 'Unknown Browser'
  let browserVersion = ''
  
  // Try User-Agent Client Hints API (modern browsers)
  if (navigator.userAgentData) {
    try {
      const hints = await navigator.userAgentData.getHighEntropyValues([
        'platform',
        'platformVersion',
        'architecture',
        'model',
        'uaFullVersion',
        'fullVersionList'
      ])
      
      // Platform (OS)
      const platformName = hints.platform || ''
      if (platformName.includes('Windows')) {
        osName = 'Windows'
        // Parse Windows version from platformVersion
        const pv = hints.platformVersion || ''
        const match = pv.match(/(\d+\.\d+)/)
        if (match) {
          osVersion = mapWindowsVersion(match[1])
        }
      } else if (platformName.includes('Mac')) {
        osName = 'macOS'
        const pv = hints.platformVersion || ''
        const match = pv.match(/(\d+)_(\d+)/)
        if (match) {
          const version = `${match[1]}.${match[2]}`
          osVersion = mapMacOSVersion(version)
        }
      } else if (platformName.includes('Linux')) {
        osName = 'Linux'
        osVersion = 'Linux'
      }
      
      // Architecture
      architecture = hints.architecture || 'unknown'
      
      // Browser from fullVersionList
      if (hints.fullVersionList && hints.fullVersionList.length > 0) {
        const browserInfo = hints.fullVersionList[0]
        browserName = browserInfo.brand || 'Unknown'
        browserVersion = browserInfo.version || ''
      }
      
      // Device class from model (if available) or screen size
      if (hints.model) {
        const model = hints.model.toLowerCase()
        if (model.includes('phone') || model.includes('mobile')) {
          deviceClass = 'mobile'
        } else if (model.includes('tablet') || model.includes('ipad')) {
          deviceClass = 'tablet'
        } else {
          deviceClass = detectDeviceClass(userAgent, screenWidth, screenHeight)
        }
      } else {
        deviceClass = detectDeviceClass(userAgent, screenWidth, screenHeight)
      }
    } catch (err) {
      // Fallback to user agent parsing if Client Hints fails
      const parsed = parseUserAgent(userAgent)
      osName = parsed.osName
      osVersion = parsed.osVersion
      architecture = parsed.architecture
      deviceClass = parsed.deviceClass
      
      const browser = detectBrowser(userAgent)
      browserName = browser.browserName
      browserVersion = browser.browserVersion
    }
  } else {
    // Fallback: Parse user agent string
    const parsed = parseUserAgent(userAgent)
    osName = parsed.osName
    osVersion = parsed.osVersion
    architecture = parsed.architecture
    deviceClass = parsed.deviceClass
    
    const browser = detectBrowser(userAgent)
    browserName = browser.browserName
    browserVersion = browser.browserVersion
  }
  
  // Get GPU renderer
  const gpuRenderer = getGPURenderer()
  
  // Build device name: "Windows 11 Laptop (Chrome)" or "macOS Sonoma Laptop (Safari)"
  const deviceClassName = deviceClass.charAt(0).toUpperCase() + deviceClass.slice(1)
  const browserLabel = browserVersion ? `${browserName} ${browserVersion}` : browserName
  const deviceName = `${osVersion || osName} ${deviceClassName} (${browserLabel})`
  
  return {
    // Identity
    device_id: deviceId,
    device_name: deviceName,
    device_type: 'os_device',
    
    // OS information
    os_name: osName,
    os_version: osVersion || osName,
    architecture: architecture,
    device_class: deviceClass,
    
    // Browser information
    browser_name: browserName,
    browser_version: browserVersion,
    browser: browserVersion ? `${browserName} ${browserVersion}` : browserName,
    
    // Environment
    platform: platform,
    user_agent: userAgent,
    screen_resolution: screenResolution,
    timezone: timezone,
    gpu: gpuRenderer,
  }
}

// Legacy export for backward compatibility (if needed)
export function detectBrowserDevice() {
  // Call async version synchronously (will use fallback parsing)
  return detectOSDevice().then(result => result).catch(() => {
    // Ultimate fallback
    const userAgent = navigator.userAgent || ''
    const platform = navigator.platform || ''
    const screenWidth = window.screen?.width || 0
    const screenHeight = window.screen?.height || 0
    
    return {
      device_id: `dev-${Date.now()}`,
      device_name: 'Unknown Device',
      device_type: 'os_device',
      os_name: 'Unknown OS',
      os_version: '',
      architecture: 'unknown',
      device_class: 'desktop',
      browser_name: 'Unknown Browser',
      browser_version: '',
      browser: 'Unknown Browser',
      platform: platform,
      user_agent: userAgent,
      screen_resolution: `${screenWidth}x${screenHeight}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      gpu: null,
    }
  })
}
