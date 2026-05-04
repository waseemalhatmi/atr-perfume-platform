import { useCallback } from 'react'

// Simple Analytics Hook for Tracking Interactions
// In a real production app, this would integrate with Mixpanel, GA4, or Segment.
export const useAnalytics = () => {
  const track = useCallback((eventName: string, properties?: Record<string, any>) => {
    try {
      // Fire-and-forget: push to dataLayer or custom endpoint
      // console.log(`[Analytics] ${eventName}`, properties)
      // Example: window.dataLayer?.push({ event: eventName, ...properties })
      
      // Simulate non-blocking network request
      if (import.meta.env.PROD) {
        // fetch('/api/analytics/track', { method: 'POST', body: JSON.stringify({ eventName, properties }), keepalive: true }).catch(() => {})
      }
    } catch (e) {
      // Never fail the app due to analytics errors
    }
  }, [])

  return { track }
}
