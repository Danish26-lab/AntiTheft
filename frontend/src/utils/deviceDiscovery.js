/**
 * Prey Project-style Device Discovery
 * Discovers running agent device via localhost HTTP endpoint
 */

const AGENT_DISCOVERY_URL = 'http://127.0.0.1:9123/device-info'

export async function discoverLocalDevice() {
  /**
   * Discover device_id from running agent on localhost
   * Returns device_id and fingerprint_hash if agent is running
   */
  try {
    const response = await fetch(AGENT_DISCOVERY_URL, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      // Short timeout since it's localhost
      signal: AbortSignal.timeout(2000)
    })

    if (response.ok) {
      const data = await response.json()
      return {
        success: true,
        device_id: data.device_id,
        fingerprint_hash: data.fingerprint_hash,
        status: data.status
      }
    }
  } catch (error) {
    // Agent not running or not accessible - this is expected if agent isn't installed
    return {
      success: false,
      error: 'Agent not running or not accessible',
      device_id: null,
      fingerprint_hash: null
    }
  }

  return {
    success: false,
    error: 'Unknown error',
    device_id: null,
    fingerprint_hash: null
  }
}
