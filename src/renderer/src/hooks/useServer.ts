// src/renderer/src/hooks/useServer.ts
import { useState, useEffect, useCallback, useRef, useMemo } from 'react'

interface ServerState {
  isReady: boolean
  port: number | null
  apiUrl: string | null
  error: string | null
  isChecking: boolean
  serverAPIAvailable: boolean
  isInitializing: boolean
}

interface AnalysisResult {
  text: string
  language_detected?: string
  toxic: boolean
  toxicity_score: number
  sentiment: string
  sentiment_score: number
  emotions?: { [key: string]: number }
  hate_speech?: boolean
  hate_speech_score?: number
  ai_enabled: boolean
  processing_time_ms: number
  model_versions: { [key: string]: string }
  
  // Legacy fields for backward compatibility (computed from new fields)
  toxicity_severity?: string
  suggested_action?: string
  sentiment_stars?: number
  confidence?: number
  emotion?: string
}

interface CachedResult {
  result: AnalysisResult
  timestamp: number
  textHash: string
}

interface QueuedRequest {
  id: string
  text: string
  resolve: (result: AnalysisResult) => void
  reject: (error: Error) => void
  timestamp: number
  priority: number
}

// Simple hash function for caching
function hashText(text: string): string {
  let hash = 0
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return hash.toString()
}

// Transform API response to expected format (handles backward compatibility)
function transformApiResponse(apiResponse: any): AnalysisResult {
  // If it's already in the new format, return it
  if (apiResponse && typeof apiResponse.toxicity_score === 'number' && typeof apiResponse.sentiment_score === 'number') {
    return apiResponse as AnalysisResult
  }
  
  // Handle old format with legacy fields
  const oldResponse = apiResponse as any
  
  return {
    text: oldResponse.text || '',
    language_detected: oldResponse.language_detected || 'en',
    toxic: Boolean(oldResponse.toxic),
    toxicity_score: oldResponse.toxicity_score || (oldResponse.toxic ? 0.8 : 0.1),
    sentiment: oldResponse.sentiment || 'neutral',
    sentiment_score: oldResponse.confidence || 0.5,
    emotions: oldResponse.emotions || (oldResponse.emotion ? { [oldResponse.emotion]: 1.0 } : undefined),
    hate_speech: oldResponse.hate_speech,
    hate_speech_score: oldResponse.hate_speech_score,
    ai_enabled: oldResponse.ai_enabled !== false,
    processing_time_ms: oldResponse.processing_time_ms || 0,
    model_versions: oldResponse.model_versions || {},
    // Legacy fields for backward compatibility
    toxicity_severity: oldResponse.toxicity_severity,
    suggested_action: oldResponse.suggested_action,
    sentiment_stars: oldResponse.sentiment_stars,
    confidence: oldResponse.confidence,
    emotion: oldResponse.emotion
  }
}

// Debounce utility
function debounce<T extends (...args: any[]) => void>(func: T, wait: number): T {
  let timeout: NodeJS.Timeout | null = null
  return ((...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }) as T
}

// Default state factory to ensure consistent initialization
const createDefaultState = (): ServerState => ({
  isReady: false,
  port: null,
  apiUrl: null,
  error: null,
  isChecking: true,
  serverAPIAvailable: false,
  isInitializing: true
})

export function useServer() {
  console.log('useServer: Hook starting to initialize')
  const [state, setState] = useState<ServerState>(createDefaultState)
  
  // Refs for cleanup and request management
  const mountedRef = useRef(true)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const requestQueueRef = useRef<QueuedRequest[]>([])
  const processingRef = useRef(false)
  const cacheRef = useRef<Map<string, CachedResult>>(new Map())
  const consecutiveFailuresRef = useRef(0)
  const lastSuccessRef = useRef<number>(0)
  const initTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // Smart polling intervals based on server state with null safety
  const getPollingInterval = useCallback(() => {
    // Ensure state is not null/undefined before checking isReady
    if (state?.isReady) return null // Stop polling when ready
    if (!state?.serverAPIAvailable && state?.isInitializing) return 500 // Slightly slower polling during initialization
    if (consecutiveFailuresRef.current > 5) return 5000 // Slow down after failures
    if (Date.now() - lastSuccessRef.current > 30000) return 3000 // Medium interval after 30s
    return 2000 // Slower initial polling to avoid overwhelming
  }, [state?.isReady, state?.serverAPIAvailable, state?.isInitializing])
  
  // Simple synchronous check for serverAPI availability
  const isServerAPIAvailable = useCallback((): boolean => {
    const available = typeof window.serverAPI !== 'undefined' && window.serverAPI !== null
    console.log('Server hook: Checking serverAPI availability:', available)
    return available
  }, [])
  
  const checkServerStatus = useCallback(async (signal?: AbortSignal) => {
    if (!mountedRef.current) return
    
    try {
      // Simple synchronous check for serverAPI availability
      const apiAvailable = isServerAPIAvailable()
      
      if (signal?.aborted || !mountedRef.current) return
      
      if (!apiAvailable || !window.serverAPI) {
        console.warn('Server hook: serverAPI not available, will retry...')
        setState(prev => ({
          ...(prev || createDefaultState()),
          error: 'ServerAPI not initialized - Electron preload may have failed',
          isChecking: false,
          serverAPIAvailable: false,
          isInitializing: false
        }))
        return
      }
      
      console.log('Server hook: serverAPI is available, checking server status...')
      
      // Update state to show serverAPI is available
      setState(prev => ({
        ...(prev || createDefaultState()),
        serverAPIAvailable: true,
        isInitializing: false,
        error: null
      }))
      
      const [ready, port, apiUrl] = await Promise.all([
        window.serverAPI.isReady(),
        window.serverAPI.getPort(),
        window.serverAPI.getApiUrl()
      ])
      
      if (signal?.aborted || !mountedRef.current) return
      
      console.log('Server hook: Server status - ready:', ready, 'port:', port)
      
      setState(prev => ({
        ...(prev || createDefaultState()),
        isReady: ready || false,
        port: port || null,
        apiUrl: apiUrl || null,
        error: null,
        isChecking: false,
        serverAPIAvailable: true,
        isInitializing: false
      }))
      
      consecutiveFailuresRef.current = 0
      lastSuccessRef.current = Date.now()
      
      // If server is ready, stop polling
      if (ready && intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
        console.log('Server hook: Server is ready, stopped polling')
      }
      
    } catch (error) {
      if (signal?.aborted || !mountedRef.current) return
      
      consecutiveFailuresRef.current++
      console.error('Server hook: Error checking server status:', error)
      setState(prev => ({
        ...(prev || createDefaultState()),
        error: error instanceof Error ? error.message : 'Server connection failed',
        isChecking: false,
        isReady: false,
        isInitializing: false
      }))
    }
  }, [isServerAPIAvailable])
  
  // Debounced version for frequent calls
  const debouncedCheckServer = useMemo(
    () => debounce(() => checkServerStatus(), 300),
    [checkServerStatus]
  )
  
  // Initialize server checking with simple, reliable approach
  useEffect(() => {
    mountedRef.current = true
    console.log('Server hook: Initializing...')
    
    // Set initial checking state
    setState(prev => ({
      ...(prev || createDefaultState()),
      isChecking: true,
      error: null,
      isInitializing: true
    }))
    
    // Check immediately if serverAPI is already available
    const initialCheck = () => {
      console.log('Server hook: Performing initial serverAPI check...')
      console.log('Server hook: window.serverAPI exists:', typeof window.serverAPI !== 'undefined')
      
      if (mountedRef.current) {
        checkServerStatus()
      }
    }
    
    // Start checking immediately
    initialCheck()
    
    // Also check after a short delay to catch cases where preload script is still loading
    const delayedCheck = setTimeout(() => {
      if (mountedRef.current) {
        console.log('Server hook: Performing delayed serverAPI check...')
        console.log('Server hook: window.serverAPI exists (delayed):', typeof window.serverAPI !== 'undefined')
        checkServerStatus()
      }
    }, 100)
    
    return () => {
      console.log('Server hook: Cleaning up...')
      mountedRef.current = false
      clearTimeout(delayedCheck)
      if (initTimeoutRef.current) {
        clearTimeout(initTimeoutRef.current)
        initTimeoutRef.current = null
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
        abortControllerRef.current = null
      }
    }
  }, [checkServerStatus])
  
  // Separate effect for polling setup to avoid dependencies issues
  useEffect(() => {
    const setupPolling = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      
      const interval = getPollingInterval()
      if (interval && !state?.isReady && mountedRef.current) {
        intervalRef.current = setInterval(() => {
          if (mountedRef.current) {
            checkServerStatus()
          }
        }, interval)
      }
    }
    
    // Only setup polling if we have a valid state
    if (state) {
      setupPolling()
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [getPollingInterval, state?.isReady, checkServerStatus])
  
  // Process request queue with batching
  const processRequestQueue = useCallback(async () => {
    if (processingRef.current || requestQueueRef.current.length === 0 || !state?.isReady || !state?.serverAPIAvailable) {
      return
    }
    
    processingRef.current = true
    
    try {
      // Sort by priority and timestamp
      const sortedRequests = requestQueueRef.current
        .sort((a, b) => b.priority - a.priority || a.timestamp - b.timestamp)
        .splice(0, 5) // Process max 5 at a time
      
      // Remove processed requests from queue
      requestQueueRef.current = requestQueueRef.current.filter(
        req => !sortedRequests.includes(req)
      )
      
      // Process requests in parallel
      await Promise.allSettled(
        sortedRequests.map(async (request) => {
          try {
            // Check cache first
            const textHash = hashText(request.text)
            const cached = cacheRef.current.get(textHash)
            
            // Use cache if less than 5 minutes old
            if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
              request.resolve(cached.result)
              return
            }
            
            // Double-check serverAPI is still available
            if (!window.serverAPI) {
              throw new Error('ServerAPI became unavailable during processing')
            }
            
            // Make API call
            const apiResponse = await window.serverAPI.analyze(request.text) as unknown
            
            // Transform the API response to match our expected format
            const result: AnalysisResult = transformApiResponse(apiResponse)
            
            // Cache the result
            cacheRef.current.set(textHash, {
              result,
              timestamp: Date.now(),
              textHash
            })
            
            // Clean old cache entries (keep last 100)
            if (cacheRef.current.size > 100) {
              const entries = Array.from(cacheRef.current.entries())
              entries.sort((a, b) => b[1].timestamp - a[1].timestamp)
              cacheRef.current = new Map(entries.slice(0, 100))
            }
            
            request.resolve(result)
          } catch (error) {
            request.reject(error instanceof Error ? error : new Error('Analysis failed'))
          }
        })
      )
    } finally {
      processingRef.current = false
      
      // Process remaining queue
      if (requestQueueRef.current.length > 0) {
        setTimeout(processRequestQueue, 100)
      }
    }
  }, [state?.isReady, state?.serverAPIAvailable])
  
  // Optimized analyze function with queueing and caching
  const analyzeText = useCallback(async (text: string, priority: number = 1): Promise<AnalysisResult> => {
    if (!text.trim()) {
      throw new Error('Text cannot be empty')
    }
    
    if (!state?.serverAPIAvailable) {
      throw new Error('ServerAPI not available - please wait for initialization')
    }
    
    if (!state?.isReady) {
      throw new Error('Backend server not ready')
    }
    
    // Double-check that serverAPI is still available
    if (!window.serverAPI) {
      throw new Error('ServerAPI not available at call time')
    }
    
    // Check cache first
    const textHash = hashText(text)
    const cached = cacheRef.current.get(textHash)
    if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
      return cached.result
    }
    
    // Create promise for queued request
    return new Promise<AnalysisResult>((resolve, reject) => {
      const request: QueuedRequest = {
        id: Math.random().toString(36).substr(2, 9),
        text,
        resolve,
        reject,
        timestamp: Date.now(),
        priority
      }
      
      requestQueueRef.current.push(request)
      
      // Start processing queue
      processRequestQueue()
      
      // Timeout after 30 seconds
      setTimeout(() => {
        const index = requestQueueRef.current.findIndex(req => req.id === request.id)
        if (index !== -1) {
          requestQueueRef.current.splice(index, 1)
          reject(new Error('Request timeout'))
        }
      }, 30000)
    })
  }, [state?.isReady, state?.serverAPIAvailable, processRequestQueue])
  
  const processChat = useCallback(async (message: {
    username: string
    message: string
    channel: string
    timestamp?: number
  }) => {
    if (!state?.serverAPIAvailable) {
      throw new Error('ServerAPI not available - please wait for initialization')
    }
    
    if (!state?.isReady) {
      throw new Error('Backend server not ready')
    }
    
    if (!window.serverAPI) {
      throw new Error('ServerAPI not available at call time')
    }
    
    return await window.serverAPI.processChat(message)
  }, [state?.isReady, state?.serverAPIAvailable])
  
  // Clear cache function
  const clearCache = useCallback(() => {
    cacheRef.current.clear()
  }, [])
  
  // Force server check function with retry logic
  const forceServerCheck = useCallback(() => {
    consecutiveFailuresRef.current = 0 // Reset failure count
    debouncedCheckServer()
  }, [debouncedCheckServer])
  
  // Retry initialization function
  const retryInitialization = useCallback(async () => {
    setState(prev => ({
      ...(prev || createDefaultState()),
      isInitializing: true,
      isChecking: true,
      error: null
    }))
    
    await checkServerStatus()
  }, [checkServerStatus])
  
  // Get cache stats
  const getCacheStats = useCallback(() => ({
    size: cacheRef.current.size,
    queueLength: requestQueueRef.current.length,
    isProcessing: processingRef.current
  }), [])
  
  // Ensure we always return a valid state object
  const safeState = state || createDefaultState()
  
  return {
    ...safeState,
    analyzeText,
    processChat,
    clearCache,
    forceServerCheck,
    retryInitialization,
    getCacheStats
  }
}