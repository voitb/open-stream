import { JSX, useState, useCallback, useMemo, useTransition, memo, useRef, useEffect } from 'react'
import { useServer } from './hooks/useServer'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ServerErrorBoundary } from './components/ServerErrorBoundary'

// Types for better TypeScript support - matches server response
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

// Memoized components for better performance with null safety
const ServerStatus = memo<{ 
  isReady: boolean; 
  isChecking: boolean; 
  error: string | null;
  serverAPIAvailable: boolean;
  isInitializing: boolean;
}>(({ isReady = false, isChecking = false, error = null, serverAPIAvailable = false, isInitializing = true }) => {
  const statusText = useMemo(() => {
    if (error) return `❌ Error: ${error}`
    if (isInitializing && !serverAPIAvailable) return '🔄 Initializing application...'
    if (isChecking) return '🔄 Checking server status...'
    if (!serverAPIAvailable) return '⚠️ ServerAPI not available'
    return isReady ? '✅ Ready' : '⏳ Loading models...'
  }, [isReady, isChecking, error, serverAPIAvailable, isInitializing])
  
  const statusClass = useMemo(() => {
    if (error) return 'status-error'
    if (isInitializing && !serverAPIAvailable) return 'status-initializing'
    if (isChecking) return 'status-checking'
    if (!serverAPIAvailable) return 'status-error'
    return isReady ? 'status-ready' : 'status-loading'
  }, [isReady, isChecking, error, serverAPIAvailable, isInitializing])
  
  return (
    <div className={`status ${statusClass}`}>
      <p>Server: {statusText}</p>
      {process.env.NODE_ENV === 'development' && (
        <small>
          API Available: {serverAPIAvailable ? '✅' : '❌'} | 
          Initializing: {isInitializing ? '🔄' : '✅'}
        </small>
      )}
    </div>
  )
})

const LoadingSkeleton = memo(() => (
  <div className="skeleton-results">
    <div className="skeleton-header"></div>
    <div className="skeleton-box skeleton-toxicity"></div>
    <div className="skeleton-box skeleton-sentiment"></div>
    <div className="skeleton-box skeleton-emotion"></div>
  </div>
))

const ToxicityResult = memo<{ result: AnalysisResult }>(({ result }) => {
  const alertClass = useMemo(
    () => `alert ${result.toxic ? 'alert-danger' : 'alert-success'}`,
    [result.toxic]
  )
  
  const scorePercentage = useMemo(
    () => (result.toxicity_score * 100).toFixed(1),
    [result.toxicity_score]
  )
  
  // Compute severity and action from score for backward compatibility
  const severity = useMemo(() => {
    if (result.toxicity_severity) return result.toxicity_severity
    if (result.toxicity_score >= 0.8) return 'High'
    if (result.toxicity_score >= 0.5) return 'Moderate'
    if (result.toxicity_score >= 0.2) return 'Low'
    return 'Minimal'
  }, [result.toxicity_score, result.toxicity_severity])
  
  const suggestedAction = useMemo(() => {
    if (result.suggested_action) return result.suggested_action
    if (result.toxic) {
      if (result.toxicity_score >= 0.8) return 'Block message and warn user'
      if (result.toxicity_score >= 0.5) return 'Flag for moderation'
      return 'Monitor user activity'
    }
    return 'No action needed'
  }, [result.toxic, result.toxicity_score, result.suggested_action])
  
  return (
    <div className={alertClass}>
      <strong>Toxicity:</strong> {result.toxic ? '⚠️ Toxic' : '✅ Safe'}
      <br />
      Score: {scorePercentage}%
      <br />
      Severity: {severity}
      <br />
      Action: {suggestedAction}
      {result.hate_speech && (
        <>
          <br />
          <strong>⚠️ Hate Speech Detected</strong> ({((result.hate_speech_score || 0) * 100).toFixed(1)}%)
        </>
      )}
    </div>
  )
})

const SentimentResult = memo<{ result: AnalysisResult }>(({ result }) => {
  // Compute stars from sentiment for backward compatibility
  const sentimentStars = useMemo(() => {
    if (result.sentiment_stars !== undefined) return result.sentiment_stars
    // Convert sentiment score to 1-5 stars
    return Math.round(result.sentiment_score * 5)
  }, [result.sentiment_score, result.sentiment_stars])
  
  const stars = useMemo(
    () => '⭐'.repeat(Math.max(0, Math.min(5, sentimentStars))),
    [sentimentStars]
  )
  
  const confidencePercentage = useMemo(
    () => (result.confidence || result.sentiment_score * 100).toFixed(1),
    [result.confidence, result.sentiment_score]
  )
  
  return (
    <div className="alert alert-info">
      <strong>Sentiment:</strong> {result.sentiment}
      <br />
      Rating: {stars}
      <br />
      Confidence: {confidencePercentage}%
      {result.processing_time_ms && (
        <>
          <br />
          <small>Processing: {result.processing_time_ms.toFixed(1)}ms</small>
        </>
      )}
    </div>
  )
})

const EmotionResult = memo<{ result: AnalysisResult }>(({ result }) => {
  // Handle both legacy single emotion and new emotions object
  const emotions = useMemo(() => {
    if (result.emotion) {
      return { [result.emotion]: 1.0 }
    }
    return result.emotions || {}
  }, [result.emotion, result.emotions])
  
  const topEmotion = useMemo(() => {
    const entries = Object.entries(emotions)
    if (entries.length === 0) return null
    return entries.reduce((max, [emotion, score]) => 
      score > max.score ? { emotion, score } : max,
      { emotion: '', score: 0 }
    )
  }, [emotions])
  
  if (!topEmotion || topEmotion.score === 0) return null
  
  return (
    <div className="alert alert-secondary">
      <strong>Emotions:</strong>
      <br />
      {Object.entries(emotions).map(([emotion, score]) => (
        <span key={emotion} style={{ marginRight: '8px' }}>
          {emotion}: {(score * 100).toFixed(1)}%
        </span>
      ))}
    </div>
  )
})

const AnalysisResults = memo<{ 
  result: AnalysisResult | null
  isOptimisticResult?: boolean 
}>(({ result, isOptimisticResult }) => {
  if (!result) return null
  
  return (
    <div className={`results ${isOptimisticResult ? 'results-optimistic' : ''}`}>
      <h3>AI Analysis Results:</h3>
      <ToxicityResult result={result} />
      <SentimentResult result={result} />
      {(result.emotion || result.emotions) && <EmotionResult result={result} />}
    </div>
  )
})

// Analysis-specific error boundary fallback
const AnalysisErrorFallback = (
  <div className="alert alert-danger">
    <strong>Analysis Error:</strong> Something went wrong during analysis.
    <button onClick={() => window.location.reload()} style={{ marginLeft: '10px' }}>
      Refresh Page
    </button>
  </div>
)

export default function App(): JSX.Element {
  const serverHook = useServer()
  
  // Add null safety for the server hook return
  const { 
    isReady = false, 
    isChecking = false, 
    error = null,
    serverAPIAvailable = false,
    isInitializing = true,
    analyzeText, 
    getCacheStats, 
    clearCache,
    forceServerCheck,
    retryInitialization
  } = serverHook || {}
  
  const [text, setText] = useState('')
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [optimisticResult, setOptimisticResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  
  // Transitions for non-urgent updates
  const [isPending, startTransition] = useTransition()
  
  // Refs for request cancellation
  const currentRequestRef = useRef<Promise<any> | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  // Debounced text change handler
  const debouncedSetText = useCallback(
    debounce((newText: string) => {
      startTransition(() => {
        setText(newText)
        setAnalysisError(null) // Clear errors when text changes
      })
    }, 150),
    []
  )
  
  // Optimized text change handler
  const handleTextChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value
    
    // Update immediately for responsive UI
    setText(newText)
    
    // Debounced update for non-urgent state
    debouncedSetText(newText)
  }, [debouncedSetText])
  
  // Memoized form validation with null safety
  const isTextValid = useMemo(() => {
    return text.trim().length > 0 && text.trim().length <= 10000 // Reasonable limit
  }, [text])
  
  const canAnalyze = useMemo(() => {
    return Boolean(isReady && serverAPIAvailable && isTextValid && !loading && analyzeText)
  }, [isReady, serverAPIAvailable, isTextValid, loading, analyzeText])
  
  // Optimized analysis handler with optimistic updates and null safety
  const handleAnalyze = useCallback(async () => {
    if (!canAnalyze || !analyzeText) {
      console.warn('Cannot analyze: server not ready or analyzeText not available')
      return
    }
    
    // Cancel any existing request
    if (currentRequestRef.current) {
      // Note: We would need to implement cancellation in the API layer
      console.log('Cancelling previous request')
    }
    
    setLoading(true)
    setAnalysisError(null)
    
    // Create optimistic result for immediate feedback
    const optimistic: AnalysisResult = {
      text: text.trim(),
      toxic: false,
      toxicity_score: 0,
      sentiment: 'Analyzing...',
      sentiment_score: 0,
      ai_enabled: true,
      processing_time_ms: 0,
      model_versions: {},
      // Legacy compatibility fields
      toxicity_severity: 'Analyzing...',
      suggested_action: 'Please wait...',
      sentiment_stars: 0,
      confidence: 0,
      emotion: 'Processing...'
    }
    
    // Show optimistic result immediately
    startTransition(() => {
      setOptimisticResult(optimistic)
      setResult(null)
    })
    
    try {
      // Priority 2 for user-initiated requests (higher than background)
      const analysisPromise = analyzeText(text.trim(), 2)
      currentRequestRef.current = analysisPromise
      
      const analysis = await analysisPromise
      
      // Update with real result
      startTransition(() => {
        setResult(analysis)
        setOptimisticResult(null)
      })
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Analysis failed'
      
      startTransition(() => {
        setAnalysisError(errorMessage)
        setOptimisticResult(null)
      })
      
      console.error('Analysis failed:', error)
    } finally {
      currentRequestRef.current = null
      setLoading(false)
    }
  }, [canAnalyze, analyzeText, text])
  
  // Handle Enter key for quick analysis
  const handleKeyPress = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && canAnalyze) {
      e.preventDefault()
      handleAnalyze()
    }
  }, [handleAnalyze, canAnalyze])
  
  // Clear results when text is cleared
  useEffect(() => {
    if (text.length === 0) {
      startTransition(() => {
        setResult(null)
        setOptimisticResult(null)
        setAnalysisError(null)
      })
    }
  }, [text.length])
  
  // Focus textarea on mount
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])
  
  // Memoized cache stats for dev tools with null safety
  const cacheStats = useMemo(() => {
    if (getCacheStats) {
      return getCacheStats()
    }
    return { size: 0, queueLength: 0, isProcessing: false }
  }, [getCacheStats])
  
  // Button text based on state
  const buttonText = useMemo(() => {
    if (loading) return 'Analyzing...'
    if (isPending) return 'Processing...'
    if (isInitializing && !serverAPIAvailable) return 'Initializing...'
    if (!serverAPIAvailable) return 'ServerAPI Not Available'
    if (!isReady) return 'Server Not Ready'
    if (!isTextValid) return 'Enter Text to Analyze'
    return 'Analyze with AI'
  }, [loading, isPending, isInitializing, serverAPIAvailable, isReady, isTextValid])
  
  // Handle case where server hook is not properly initialized
  if (!serverHook) {
    console.error('App: serverHook is null/undefined!')
    return (
      <div className="container">
        <h1>🤗 Hugging Face AI Analysis</h1>
        <div className="alert alert-warning">
          <p>🔄 Initializing application...</p>
          <p><small>If this persists, there may be an issue with the Electron preload script.</small></p>
          <button 
            onClick={() => window.location.reload()}
            style={{ marginTop: '10px' }}
          >
            Reload Application
          </button>
        </div>
      </div>
    )
  }
  
  // Show initialization error with retry option
  if (error && !serverAPIAvailable && !isInitializing) {
    return (
      <ServerErrorBoundary onRetry={retryInitialization}>
        <div className="container">
          <h1>🤗 Hugging Face AI Analysis</h1>
          <div className="alert alert-danger">
            <strong>Initialization Error:</strong> {error}
            <br />
            <button 
              onClick={retryInitialization}
              style={{ marginTop: '10px', marginRight: '10px' }}
            >
              Retry Initialization
            </button>
            <button 
              onClick={() => window.location.reload()}
              style={{ marginTop: '10px' }}
            >
              Reload Application
            </button>
          </div>
        </div>
      </ServerErrorBoundary>
    )
  }

  return (
    <ServerErrorBoundary onRetry={forceServerCheck}>
      <div className="container">
        <h1>🤗 Hugging Face AI Analysis</h1>
        
        <ServerStatus 
          isReady={isReady} 
          isChecking={isChecking} 
          error={error}
          serverAPIAvailable={serverAPIAvailable}
          isInitializing={isInitializing}
        />
      
      <div className="input-section">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleTextChange}
          onKeyPress={handleKeyPress}
          placeholder="Enter text to analyze... (Ctrl+Enter to analyze)"
          rows={4}
          className={`text-input ${!isTextValid && text.length > 0 ? 'invalid' : ''}`}
          disabled={loading}
          maxLength={10000}
        />
        
        <div className="input-meta">
          <span className="char-count">
            {text.length}/10000 characters
            {text.trim().length > 0 && ` • ${text.trim().split(/\s+/).length} words`}
          </span>
          
          {process.env.NODE_ENV === 'development' && (
            <span className="cache-stats">
              Cache: {cacheStats.size} • Queue: {cacheStats.queueLength}
            </span>
          )}
        </div>
      </div>
      
      <div className="controls">
        <button 
          onClick={handleAnalyze} 
          disabled={!canAnalyze}
          className={`analyze-button ${loading ? 'loading' : ''}`}
        >
          {buttonText}
        </button>
        
        {result && (
          <button 
            onClick={() => startTransition(() => { setResult(null); setOptimisticResult(null) })}
            className="clear-button"
          >
            Clear Results
          </button>
        )}
        
        {process.env.NODE_ENV === 'development' && clearCache && (
          <button 
            onClick={clearCache}
            className="dev-button"
          >
            Clear Cache
          </button>
        )}
      </div>
      
      <ErrorBoundary fallback={AnalysisErrorFallback}>
        {loading && !result && !optimisticResult && <LoadingSkeleton />}
        
        {optimisticResult && (
          <AnalysisResults result={optimisticResult} isOptimisticResult={true} />
        )}
        
        {result && !optimisticResult && (
          <AnalysisResults result={result} isOptimisticResult={false} />
        )}
        
        {analysisError && (
          <div className="alert alert-danger">
            <strong>Error:</strong> {analysisError}
            <button 
              onClick={handleAnalyze} 
              disabled={!canAnalyze}
              style={{ marginLeft: '10px' }}
            >
              Retry
            </button>
          </div>
        )}
      </ErrorBoundary>
      </div>
    </ServerErrorBoundary>
  )
}

// Utility function (should be moved to utils if project grows)
function debounce<T extends (...args: any[]) => void>(func: T, wait: number): T {
  let timeout: NodeJS.Timeout | null = null
  return ((...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }) as T
}