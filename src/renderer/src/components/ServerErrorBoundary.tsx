import { Component, ReactNode } from 'react'

interface ServerErrorBoundaryProps {
  children: ReactNode
  onRetry?: () => void
}

interface ServerErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: any
}

export class ServerErrorBoundary extends Component<ServerErrorBoundaryProps, ServerErrorBoundaryState> {
  constructor(props: ServerErrorBoundaryProps) {
    super(props)
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null 
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ServerErrorBoundaryState> {
    return { 
      hasError: true, 
      error 
    }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Server Error caught by boundary:', error, errorInfo)
    this.setState({
      error,
      errorInfo
    })
  }

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    })
    
    if (this.props.onRetry) {
      this.props.onRetry()
    }
  }

  render() {
    if (this.state.hasError) {
      const isServerError = this.state.error?.message?.includes('server') ||
                          this.state.error?.message?.includes('ServerAPI') ||
                          this.state.error?.message?.includes('Backend')

      return (
        <div className="server-error-container">
          <div className="alert alert-danger">
            <h3>🚨 Server Connection Error</h3>
            <p>
              <strong>Error:</strong> {this.state.error?.message || 'Unknown server error'}
            </p>
            
            {isServerError && (
              <div className="error-details">
                <p><strong>Possible causes:</strong></p>
                <ul>
                  <li>Python server is still starting up</li>
                  <li>Required Python packages are not installed</li>
                  <li>Server crashed during initialization</li>
                  <li>Port conflict or network issue</li>
                </ul>
              </div>
            )}
            
            <div className="error-actions">
              <button 
                onClick={this.handleRetry}
                className="retry-button"
              >
                🔄 Retry Connection
              </button>
              
              <button 
                onClick={() => window.location.reload()}
                className="reload-button"
                style={{ marginLeft: '10px' }}
              >
                🔃 Reload App
              </button>
            </div>
            
            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="error-stack">
                <summary>Debug Information (Development Only)</summary>
                <pre>{this.state.error?.stack}</pre>
                <pre>{JSON.stringify(this.state.errorInfo, null, 2)}</pre>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}