declare global {
  interface Window {
    electron: {
      ipcRenderer: {
        sendMessage: (channel: string, ...args: any[]) => void
        on: (channel: string, func: (...args: any[]) => void) => void
        once: (channel: string, func: (...args: any[]) => void) => void
      }
    }
    api: unknown
    serverAPI: {
      getPort: () => Promise<number>
      isReady: () => Promise<boolean>
      getApiUrl: () => Promise<string>
      analyze: (text: string) => Promise<{
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
        // Legacy fields for backward compatibility
        toxicity_severity?: string
        suggested_action?: string
        sentiment_stars?: number
        confidence?: number
        emotion?: string
        categories?: string[]
      }>
      processChat: (message: {
        username: string
        message: string
        channel: string
        timestamp?: number
      }) => Promise<{
        message_id: string
        action: string
        reason: string | null
      }>
    }
  }
}
