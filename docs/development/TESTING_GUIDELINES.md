# Testing Guidelines

## Overview

Open Stream requires comprehensive testing to ensure reliability across its complex Electron + React + Python architecture. This guide covers unit testing, component testing, integration testing, and performance testing strategies for the AI-powered desktop application.

## Testing Stack

### Core Testing Technologies

```json
// package.json - Testing dependencies
{
  "devDependencies": {
    "vitest": "^2.0.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/user-event": "^14.0.0",
    "msw": "^2.0.0",
    "playwright": "^1.45.0",
    "@types/testing-library__jest-dom": "^6.0.0"
  }
}
```

### Test Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,ts,tsx}'],
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        'src/**/*.d.ts',
        'src/main/',  // Electron main process tested separately
      ]
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src/renderer/src')
    }
  }
})
```

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock Electron APIs
const mockServerAPI = {
  analyze: vi.fn(),
  isReady: vi.fn(),
  getPort: vi.fn(),
  getApiUrl: vi.fn(),
  processChat: vi.fn()
}

const mockElectronAPI = {
  openExternal: vi.fn(),
  showMessageBox: vi.fn(),
  getVersion: vi.fn()
}

Object.defineProperty(window, 'serverAPI', {
  value: mockServerAPI,
  writable: true
})

Object.defineProperty(window, 'electronAPI', {
  value: mockElectronAPI,
  writable: true
})

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))
```

## Unit Testing Patterns

### 1. Utility Function Testing

```typescript
// utils/analysis.test.ts
import { describe, it, expect } from 'vitest'
import { 
  calculateToxicitySeverity, 
  formatAnalysisResult, 
  validateInputText 
} from './analysis'
import type { AnalysisResult } from '@/types/analysis'

describe('Analysis Utilities', () => {
  describe('calculateToxicitySeverity', () => {
    it('should return "high" for scores >= 0.8', () => {
      expect(calculateToxicitySeverity(0.8)).toBe('high')
      expect(calculateToxicitySeverity(0.9)).toBe('high')
      expect(calculateToxicitySeverity(1.0)).toBe('high')
    })

    it('should return "moderate" for scores 0.5-0.79', () => {
      expect(calculateToxicitySeverity(0.5)).toBe('moderate')
      expect(calculateToxicitySeverity(0.7)).toBe('moderate')
      expect(calculateToxicitySeverity(0.79)).toBe('moderate')
    })

    it('should return "low" for scores 0.2-0.49', () => {
      expect(calculateToxicitySeverity(0.2)).toBe('low')
      expect(calculateToxicitySeverity(0.3)).toBe('low')
      expect(calculateToxicitySeverity(0.49)).toBe('low')
    })

    it('should return "minimal" for scores < 0.2', () => {
      expect(calculateToxicitySeverity(0)).toBe('minimal')
      expect(calculateToxicitySeverity(0.1)).toBe('minimal')
      expect(calculateToxicitySeverity(0.19)).toBe('minimal')
    })
  })

  describe('validateInputText', () => {
    it('should return true for valid text', () => {
      expect(validateInputText('Hello world')).toBe(true)
      expect(validateInputText('A'.repeat(100))).toBe(true)
    })

    it('should return false for empty or whitespace-only text', () => {
      expect(validateInputText('')).toBe(false)
      expect(validateInputText('   ')).toBe(false)
      expect(validateInputText('\n\t')).toBe(false)
    })

    it('should return false for text exceeding max length', () => {
      const longText = 'A'.repeat(10001)
      expect(validateInputText(longText)).toBe(false)
    })
  })

  describe('formatAnalysisResult', () => {
    const mockResult: AnalysisResult = {
      id: 'test-id',
      text: 'Test text',
      timestamp: 1234567890000,
      toxic: false,
      toxicity_score: 0.1,
      sentiment: 'positive',
      sentiment_score: 0.8,
      ai_enabled: true,
      processing_time_ms: 150,
      model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' }
    }

    it('should format result correctly', () => {
      const formatted = formatAnalysisResult(mockResult)
      
      expect(formatted).toMatchObject({
        severity: 'minimal',
        sentimentLabel: 'Positive',
        confidencePercentage: '80.0%',
        processingTime: '150ms'
      })
    })

    it('should handle missing optional fields', () => {
      const minimalResult = {
        ...mockResult,
        emotions: undefined,
        hate_speech: undefined
      }
      
      const formatted = formatAnalysisResult(minimalResult)
      expect(formatted).toBeDefined()
      expect(formatted.emotions).toBeUndefined()
    })
  })
})
```

### 2. Hook Testing

```typescript
// hooks/useServer.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { useServer } from './useServer'

// Mock the serverAPI
const mockServerAPI = {
  analyze: vi.fn(),
  isReady: vi.fn(),
  getPort: vi.fn(),
  getApiUrl: vi.fn(),
  processChat: vi.fn()
}

beforeEach(() => {
  vi.clearAllMocks()
  Object.defineProperty(window, 'serverAPI', {
    value: mockServerAPI,
    writable: true
  })
})

describe('useServer', () => {
  it('should initialize with default state', () => {
    const { result } = renderHook(() => useServer())
    
    expect(result.current.isReady).toBe(false)
    expect(result.current.isChecking).toBe(true)
    expect(result.current.isInitializing).toBe(true)
    expect(result.current.error).toBe(null)
  })

  it('should check server status on mount', async () => {
    mockServerAPI.isReady.mockResolvedValue(true)
    mockServerAPI.getPort.mockResolvedValue(55555)
    mockServerAPI.getApiUrl.mockResolvedValue('http://127.0.0.1:55555')

    const { result } = renderHook(() => useServer())

    await waitFor(() => {
      expect(result.current.isReady).toBe(true)
    })

    expect(result.current.port).toBe(55555)
    expect(result.current.apiUrl).toBe('http://127.0.0.1:55555')
    expect(result.current.isChecking).toBe(false)
    expect(result.current.serverAPIAvailable).toBe(true)
  })

  it('should handle server connection errors', async () => {
    mockServerAPI.isReady.mockRejectedValue(new Error('Connection failed'))

    const { result } = renderHook(() => useServer())

    await waitFor(() => {
      expect(result.current.error).toBe('Connection failed')
    })

    expect(result.current.isReady).toBe(false)
    expect(result.current.isChecking).toBe(false)
  })

  it('should analyze text successfully', async () => {
    const mockResult = {
      id: 'test-id',
      text: 'Test text',
      toxic: false,
      toxicity_score: 0.1,
      sentiment: 'positive',
      sentiment_score: 0.8,
      ai_enabled: true,
      processing_time_ms: 150,
      model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' },
      timestamp: Date.now()
    }

    mockServerAPI.isReady.mockResolvedValue(true)
    mockServerAPI.analyze.mockResolvedValue(mockResult)

    const { result } = renderHook(() => useServer())

    // Wait for server to be ready
    await waitFor(() => {
      expect(result.current.isReady).toBe(true)
    })

    // Test analysis
    const analysisResult = await result.current.analyzeText('Test text')
    expect(analysisResult).toEqual(mockResult)
    expect(mockServerAPI.analyze).toHaveBeenCalledWith('Test text')
  })

  it('should cache analysis results', async () => {
    const mockResult = {
      id: 'test-id',
      text: 'Test text',
      toxic: false,
      toxicity_score: 0.1,
      sentiment: 'positive',
      sentiment_score: 0.8,
      ai_enabled: true,
      processing_time_ms: 150,
      model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' },
      timestamp: Date.now()
    }

    mockServerAPI.isReady.mockResolvedValue(true)
    mockServerAPI.analyze.mockResolvedValue(mockResult)

    const { result } = renderHook(() => useServer())

    await waitFor(() => {
      expect(result.current.isReady).toBe(true)
    })

    // First call
    await result.current.analyzeText('Test text')
    
    // Second call should use cache
    await result.current.analyzeText('Test text')

    // API should only be called once
    expect(mockServerAPI.analyze).toHaveBeenCalledTimes(1)
  })
})
```

## Component Testing

### 1. UI Component Testing

```typescript
// components/ui/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import { Button } from './Button'

describe('Button Component', () => {
  it('should render with default props', () => {
    render(<Button>Click me</Button>)
    
    const button = screen.getByRole('button', { name: /click me/i })
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('btn-primary') // Default variant
  })

  it('should apply variant classes correctly', () => {
    const { rerender } = render(<Button variant="secondary">Test</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-secondary')

    rerender(<Button variant="destructive">Test</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-destructive')
  })

  it('should handle click events', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('disabled')
  })

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLButtonElement>()
    render(<Button ref={ref}>Test</Button>)
    
    expect(ref.current).toBeInstanceOf(HTMLButtonElement)
  })

  it('should merge custom className', () => {
    render(<Button className="custom-class">Test</Button>)
    
    const button = screen.getByRole('button')
    expect(button).toHaveClass('btn-primary') // Default class
    expect(button).toHaveClass('custom-class') // Custom class
  })
})
```

### 2. Feature Component Testing

```typescript
// components/features/analysis/AnalysisResults.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { AnalysisResults } from './AnalysisResults'
import type { AnalysisResult } from '@/types/analysis'

const createMockResult = (overrides: Partial<AnalysisResult> = {}): AnalysisResult => ({
  id: 'test-id',
  text: 'Test text',
  timestamp: Date.now(),
  toxic: false,
  toxicity_score: 0.1,
  sentiment: 'positive',
  sentiment_score: 0.8,
  ai_enabled: true,
  processing_time_ms: 150,
  model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' },
  ...overrides
})

describe('AnalysisResults Component', () => {
  it('should render safe content correctly', () => {
    const safeResult = createMockResult({
      toxic: false,
      toxicity_score: 0.1
    })

    render(<AnalysisResults result={safeResult} />)

    expect(screen.getByText('✅ Safe Content')).toBeInTheDocument()
    expect(screen.getByText('10.0%')).toBeInTheDocument() // Toxicity percentage
    expect(screen.getByText('Positive')).toBeInTheDocument() // Sentiment
  })

  it('should render toxic content correctly', () => {
    const toxicResult = createMockResult({
      toxic: true,
      toxicity_score: 0.9,
      sentiment: 'negative',
      sentiment_score: 0.2
    })

    render(<AnalysisResults result={toxicResult} />)

    expect(screen.getByText('⚠️ Toxic Content')).toBeInTheDocument()
    expect(screen.getByText('90.0%')).toBeInTheDocument()
    expect(screen.getByText('Negative')).toBeInTheDocument()
  })

  it('should render hate speech warning when present', () => {
    const hateResult = createMockResult({
      hate_speech: true,
      hate_speech_score: 0.7
    })

    render(<AnalysisResults result={hateResult} />)

    expect(screen.getByText(/hate speech detected/i)).toBeInTheDocument()
    expect(screen.getByText('70.0%')).toBeInTheDocument()
  })

  it('should render emotions when available', () => {
    const emotionResult = createMockResult({
      emotions: {
        joy: 0.8,
        sadness: 0.1,
        anger: 0.1
      }
    })

    render(<AnalysisResults result={emotionResult} />)

    expect(screen.getByText(/joy.*80\.0%/)).toBeInTheDocument()
    expect(screen.getByText(/sadness.*10\.0%/)).toBeInTheDocument()
    expect(screen.getByText(/anger.*10\.0%/)).toBeInTheDocument()
  })

  it('should show processing time', () => {
    const result = createMockResult({
      processing_time_ms: 245
    })

    render(<AnalysisResults result={result} />)

    expect(screen.getByText('245ms')).toBeInTheDocument()
  })

  it('should handle optimistic results', () => {
    const optimisticResult = createMockResult({
      sentiment: 'Analyzing...',
      toxicity_score: 0
    })

    render(<AnalysisResults result={optimisticResult} isOptimistic />)

    expect(screen.getByText('Analyzing...')).toBeInTheDocument()
    expect(screen.getByTestId('analysis-results')).toHaveClass('results-optimistic')
  })
})
```

### 3. Integration Component Testing

```typescript
// components/AnalysisContainer.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { AnalysisContainer } from './AnalysisContainer'

// Mock the useServer hook
vi.mock('@/hooks/useServer', () => ({
  useServer: vi.fn()
}))

const mockUseServer = vi.mocked(useServer)

describe('AnalysisContainer Integration', () => {
  const mockAnalyzeText = vi.fn()
  
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseServer.mockReturnValue({
      isReady: true,
      isChecking: false,
      error: null,
      serverAPIAvailable: true,
      isInitializing: false,
      analyzeText: mockAnalyzeText,
      getCacheStats: vi.fn(() => ({ size: 0, queueLength: 0, isProcessing: false })),
      clearCache: vi.fn(),
      forceServerCheck: vi.fn(),
      retryInitialization: vi.fn(),
      port: 55555,
      apiUrl: 'http://127.0.0.1:55555'
    })
  })

  it('should complete full analysis workflow', async () => {
    const user = userEvent.setup()
    const mockResult = {
      id: 'test-id',
      text: 'Test input text',
      toxic: false,
      toxicity_score: 0.2,
      sentiment: 'positive',
      sentiment_score: 0.7,
      ai_enabled: true,
      processing_time_ms: 200,
      model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' },
      timestamp: Date.now()
    }

    mockAnalyzeText.mockResolvedValue(mockResult)

    render(<AnalysisContainer />)

    // Find input and button
    const textInput = screen.getByPlaceholderText(/enter text to analyze/i)
    const analyzeButton = screen.getByRole('button', { name: /analyze with ai/i })

    // Initially button should be disabled
    expect(analyzeButton).toBeDisabled()

    // Type text
    await user.type(textInput, 'Test input text')

    // Button should be enabled
    expect(analyzeButton).toBeEnabled()

    // Click analyze
    await user.click(analyzeButton)

    // Should show loading state
    expect(screen.getByText(/analyzing/i)).toBeInTheDocument()

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('✅ Safe Content')).toBeInTheDocument()
    })

    // Verify API was called
    expect(mockAnalyzeText).toHaveBeenCalledWith('Test input text', 2)

    // Verify results are displayed
    expect(screen.getByText('20.0%')).toBeInTheDocument() // Toxicity score
    expect(screen.getByText('Positive')).toBeInTheDocument() // Sentiment
  })

  it('should handle analysis errors gracefully', async () => {
    const user = userEvent.setup()
    mockAnalyzeText.mockRejectedValue(new Error('Analysis failed'))

    render(<AnalysisContainer />)

    const textInput = screen.getByPlaceholderText(/enter text to analyze/i)
    const analyzeButton = screen.getByRole('button', { name: /analyze with ai/i })

    await user.type(textInput, 'Test text')
    await user.click(analyzeButton)

    await waitFor(() => {
      expect(screen.getByText(/analysis failed/i)).toBeInTheDocument()
    })

    // Should show retry button
    const retryButton = screen.getByRole('button', { name: /retry/i })
    expect(retryButton).toBeInTheDocument()
  })

  it('should support keyboard shortcuts', async () => {
    const user = userEvent.setup()
    const mockResult = {
      id: 'test-id',
      text: 'Keyboard test',
      toxic: false,
      toxicity_score: 0.1,
      sentiment: 'neutral',
      sentiment_score: 0.5,
      ai_enabled: true,
      processing_time_ms: 100,
      model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' },
      timestamp: Date.now()
    }

    mockAnalyzeText.mockResolvedValue(mockResult)

    render(<AnalysisContainer />)

    const textInput = screen.getByPlaceholderText(/enter text to analyze/i)

    await user.type(textInput, 'Keyboard test')

    // Use Ctrl+Enter to trigger analysis
    await user.keyboard('{Control>}{Enter}{/Control}')

    await waitFor(() => {
      expect(screen.getByText('✅ Safe Content')).toBeInTheDocument()
    })

    expect(mockAnalyzeText).toHaveBeenCalledWith('Keyboard test', 2)
  })

  it('should handle server not ready state', () => {
    mockUseServer.mockReturnValue({
      isReady: false,
      isChecking: true,
      error: null,
      serverAPIAvailable: true,
      isInitializing: true,
      analyzeText: mockAnalyzeText,
      getCacheStats: vi.fn(),
      clearCache: vi.fn(),
      forceServerCheck: vi.fn(),
      retryInitialization: vi.fn(),
      port: null,
      apiUrl: null
    })

    render(<AnalysisContainer />)

    const analyzeButton = screen.getByRole('button')
    expect(analyzeButton).toHaveTextContent(/initializing/i)
    expect(analyzeButton).toBeDisabled()
  })
})
```

## Mock Service Worker (MSW) for API Testing

### 1. MSW Setup

```typescript
// src/test/mocks/handlers.ts
import { http, HttpResponse } from 'msw'
import type { AnalysisResult } from '@/types/analysis'

export const handlers = [
  // Analysis endpoint
  http.post('http://127.0.0.1:55555/analyze', async ({ request }) => {
    const { text } = await request.json() as { text: string }
    
    // Simulate different responses based on input
    if (text.includes('toxic')) {
      return HttpResponse.json({
        id: 'mock-id',
        text,
        toxic: true,
        toxicity_score: 0.9,
        sentiment: 'negative',
        sentiment_score: 0.2,
        ai_enabled: true,
        processing_time_ms: 200,
        model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' },
        timestamp: Date.now()
      } satisfies AnalysisResult)
    }
    
    return HttpResponse.json({
      id: 'mock-id',
      text,
      toxic: false,
      toxicity_score: 0.1,
      sentiment: 'positive',
      sentiment_score: 0.8,
      ai_enabled: true,
      processing_time_ms: 150,
      model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' },
      timestamp: Date.now()
    } satisfies AnalysisResult)
  }),

  // Health check endpoint
  http.get('http://127.0.0.1:55555/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      timestamp: Date.now(),
      models_loaded: true
    })
  }),

  // Error simulation
  http.post('http://127.0.0.1:55555/analyze-error', () => {
    return HttpResponse.json(
      { error: 'Analysis service unavailable' },
      { status: 503 }
    )
  })
]
```

```typescript
// src/test/mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
```

### 2. MSW Integration Tests

```typescript
// hooks/useServer.integration.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { beforeAll, afterEach, afterAll, describe, it, expect } from 'vitest'
import { server } from '@/test/mocks/server'
import { useServer } from './useServer'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useServer Integration Tests', () => {
  it('should make real HTTP requests to mock server', async () => {
    // Override window.serverAPI to make real HTTP requests
    Object.defineProperty(window, 'serverAPI', {
      value: {
        analyze: async (text: string) => {
          const response = await fetch('http://127.0.0.1:55555/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
          })
          return response.json()
        },
        isReady: async () => {
          const response = await fetch('http://127.0.0.1:55555/health')
          const data = await response.json()
          return data.models_loaded
        },
        getPort: async () => 55555,
        getApiUrl: async () => 'http://127.0.0.1:55555'
      }
    })

    const { result } = renderHook(() => useServer())

    await waitFor(() => {
      expect(result.current.isReady).toBe(true)
    })

    // Test analysis with mock server
    const analysisResult = await result.current.analyzeText('Hello world')
    
    expect(analysisResult.text).toBe('Hello world')
    expect(analysisResult.toxic).toBe(false)
    expect(analysisResult.toxicity_score).toBe(0.1)
  })

  it('should handle toxic content from mock server', async () => {
    const { result } = renderHook(() => useServer())

    await waitFor(() => {
      expect(result.current.isReady).toBe(true)
    })

    const analysisResult = await result.current.analyzeText('This is toxic content')
    
    expect(analysisResult.toxic).toBe(true)
    expect(analysisResult.toxicity_score).toBe(0.9)
    expect(analysisResult.sentiment).toBe('negative')
  })
})
```

## E2E Testing with Playwright

### 1. Playwright Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] }
    }
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI
  }
})
```

### 2. E2E Test Examples

```typescript
// tests/e2e/analysis-workflow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Analysis Workflow', () => {
  test('should complete analysis from input to results', async ({ page }) => {
    await page.goto('/')

    // Wait for app to load
    await expect(page.getByText('🤗 Hugging Face AI Analysis')).toBeVisible()

    // Wait for server to be ready
    await expect(page.getByText('✅ Ready')).toBeVisible({ timeout: 30000 })

    // Input text
    const textInput = page.getByPlaceholder('Enter text to analyze...')
    await textInput.fill('This is a test message for analysis')

    // Click analyze button
    const analyzeButton = page.getByRole('button', { name: /analyze with ai/i })
    await expect(analyzeButton).toBeEnabled()
    await analyzeButton.click()

    // Should show loading state
    await expect(page.getByText('Analyzing...')).toBeVisible()

    // Wait for results
    await expect(page.getByText('AI Analysis Results:')).toBeVisible({ timeout: 10000 })
    
    // Check results are displayed
    await expect(page.getByText(/Safe|Toxic/)).toBeVisible()
    await expect(page.getByText(/Positive|Negative|Neutral/)).toBeVisible()
  })

  test('should handle keyboard shortcuts', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('✅ Ready')).toBeVisible({ timeout: 30000 })

    const textInput = page.getByPlaceholder('Enter text to analyze...')
    await textInput.fill('Keyboard shortcut test')

    // Use Ctrl+Enter
    await textInput.press('Control+Enter')

    await expect(page.getByText('AI Analysis Results:')).toBeVisible({ timeout: 10000 })
  })

  test('should clear results', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('✅ Ready')).toBeVisible({ timeout: 30000 })

    // Perform analysis
    const textInput = page.getByPlaceholder('Enter text to analyze...')
    await textInput.fill('Test for clearing results')
    await page.getByRole('button', { name: /analyze with ai/i }).click()
    
    await expect(page.getByText('AI Analysis Results:')).toBeVisible({ timeout: 10000 })

    // Clear results
    const clearButton = page.getByRole('button', { name: /clear results/i })
    await clearButton.click()

    // Results should be gone
    await expect(page.getByText('AI Analysis Results:')).not.toBeVisible()
  })

  test('should handle server errors gracefully', async ({ page }) => {
    await page.goto('/')

    // Mock server error
    await page.route('**/analyze', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Server error' })
      })
    })

    await expect(page.getByText('✅ Ready')).toBeVisible({ timeout: 30000 })

    const textInput = page.getByPlaceholder('Enter text to analyze...')
    await textInput.fill('Test error handling')
    await page.getByRole('button', { name: /analyze with ai/i }).click()

    // Should show error message
    await expect(page.getByText(/error/i)).toBeVisible({ timeout: 5000 })
    
    // Should show retry button
    await expect(page.getByRole('button', { name: /retry/i })).toBeVisible()
  })
})

test.describe('Server Status', () => {
  test('should show server status correctly', async ({ page }) => {
    await page.goto('/')

    // Should initially show checking status
    await expect(page.getByText(/checking|initializing/i)).toBeVisible()

    // Should eventually show ready status
    await expect(page.getByText('✅ Ready')).toBeVisible({ timeout: 30000 })
  })

  test('should handle server unavailable state', async ({ page }) => {
    // Mock all server requests to fail
    await page.route('**/health', route => {
      route.abort()
    })

    await page.goto('/')

    // Should show server unavailable
    await expect(page.getByText(/unavailable|error/i)).toBeVisible({ timeout: 10000 })
  })
})
```

## Performance Testing

### 1. Performance Test Utilities

```typescript
// test/performance/performance-utils.ts
import { performance } from 'perf_hooks'

export interface PerformanceMetrics {
  duration: number
  memoryUsage?: {
    used: number
    total: number
  }
  renderCount?: number
}

export async function measurePerformance<T>(
  name: string,
  testFn: () => Promise<T>
): Promise<{ result: T; metrics: PerformanceMetrics }> {
  const startTime = performance.now()
  const startMemory = (global as any).gc ? process.memoryUsage() : undefined

  if ((global as any).gc) {
    (global as any).gc()
  }

  const result = await testFn()

  const endTime = performance.now()
  const endMemory = (global as any).gc ? process.memoryUsage() : undefined

  const metrics: PerformanceMetrics = {
    duration: endTime - startTime,
    memoryUsage: startMemory && endMemory ? {
      used: endMemory.heapUsed - startMemory.heapUsed,
      total: endMemory.heapTotal
    } : undefined
  }

  console.log(`Performance Test [${name}]:`, metrics)

  return { result, metrics }
}

export function expectPerformance(metrics: PerformanceMetrics, thresholds: {
  maxDuration?: number
  maxMemoryIncrease?: number
}) {
  if (thresholds.maxDuration && metrics.duration > thresholds.maxDuration) {
    throw new Error(`Performance test failed: duration ${metrics.duration}ms exceeds threshold ${thresholds.maxDuration}ms`)
  }

  if (thresholds.maxMemoryIncrease && metrics.memoryUsage && metrics.memoryUsage.used > thresholds.maxMemoryIncrease) {
    throw new Error(`Performance test failed: memory increase ${metrics.memoryUsage.used} bytes exceeds threshold ${thresholds.maxMemoryIncrease} bytes`)
  }
}
```

### 2. Component Performance Tests

```typescript
// components/AnalysisResults.performance.test.tsx
import { render, act } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { AnalysisResults } from './AnalysisResults'
import { measurePerformance, expectPerformance } from '@/test/performance/performance-utils'

describe('AnalysisResults Performance', () => {
  it('should render large datasets efficiently', async () => {
    const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
      id: `result-${i}`,
      text: `Test text ${i}`,
      toxic: Math.random() > 0.5,
      toxicity_score: Math.random(),
      sentiment: 'neutral' as const,
      sentiment_score: Math.random(),
      ai_enabled: true,
      processing_time_ms: Math.random() * 1000,
      model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' },
      timestamp: Date.now()
    }))

    const { metrics } = await measurePerformance('Large dataset render', async () => {
      return new Promise<void>(resolve => {
        act(() => {
          render(<AnalysisResultsList results={largeDataset} />)
          resolve()
        })
      })
    })

    expectPerformance(metrics, {
      maxDuration: 1000, // 1 second max
      maxMemoryIncrease: 50 * 1024 * 1024 // 50MB max
    })
  })

  it('should handle rapid updates efficiently', async () => {
    let renderCount = 0
    const { rerender } = render(<AnalysisResults result={mockResult} />)

    const { metrics } = await measurePerformance('Rapid updates', async () => {
      return new Promise<void>(resolve => {
        const updateInterval = setInterval(() => {
          renderCount++
          rerender(<AnalysisResults result={{
            ...mockResult,
            timestamp: Date.now()
          }} />)

          if (renderCount >= 100) {
            clearInterval(updateInterval)
            resolve()
          }
        }, 10)
      })
    })

    expectPerformance(metrics, {
      maxDuration: 2000, // 2 seconds for 100 updates
      maxMemoryIncrease: 10 * 1024 * 1024 // 10MB max
    })
  })
})
```

## Test Organization and Best Practices

### 1. Test File Structure

```
src/
├── components/
│   ├── ui/
│   │   ├── Button.tsx
│   │   └── Button.test.tsx
│   ├── features/
│   │   ├── analysis/
│   │   │   ├── AnalysisResults.tsx
│   │   │   └── AnalysisResults.test.tsx
│   │   └── AnalysisContainer.test.tsx
├── hooks/
│   ├── useServer.ts
│   ├── useServer.test.ts
│   └── useServer.integration.test.ts
├── utils/
│   ├── analysis.ts
│   └── analysis.test.ts
└── test/
    ├── setup.ts
    ├── mocks/
    ├── fixtures/
    └── performance/
```

### 2. Test Data Management

```typescript
// test/fixtures/analysis.ts
import type { AnalysisResult } from '@/types/analysis'

export const createMockAnalysisResult = (overrides: Partial<AnalysisResult> = {}): AnalysisResult => ({
  id: 'mock-id',
  text: 'Mock text',
  timestamp: 1234567890000,
  toxic: false,
  toxicity_score: 0.1,
  sentiment: 'positive',
  sentiment_score: 0.8,
  ai_enabled: true,
  processing_time_ms: 150,
  model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' },
  ...overrides
})

export const mockAnalysisResults = {
  safe: createMockAnalysisResult({ toxic: false, toxicity_score: 0.1 }),
  toxic: createMockAnalysisResult({ toxic: true, toxicity_score: 0.9 }),
  withEmotions: createMockAnalysisResult({
    emotions: { joy: 0.8, sadness: 0.1, anger: 0.1 }
  }),
  withHateSpeech: createMockAnalysisResult({
    hate_speech: true,
    hate_speech_score: 0.7
  })
}
```

## CI/CD Integration

### 1. GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'pnpm'
      
      - name: Install dependencies
        run: pnpm install
      
      - name: Run unit tests
        run: pnpm test:unit
      
      - name: Run integration tests
        run: pnpm test:integration
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/coverage-final.json

  e2e:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'pnpm'
      
      - name: Install dependencies
        run: pnpm install
      
      - name: Install Playwright
        run: npx playwright install
      
      - name: Run E2E tests
        run: pnpm test:e2e
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

## Best Practices Summary

### ✅ Testing Do's

1. **Write tests first**: TDD approach for critical features
2. **Test behavior, not implementation**: Focus on user interactions
3. **Use proper test data**: Create realistic fixtures
4. **Mock external dependencies**: Use MSW for API calls
5. **Test error scenarios**: Cover edge cases and failures
6. **Monitor performance**: Include performance tests
7. **Keep tests isolated**: No dependencies between tests
8. **Use descriptive test names**: Clear intent and expected outcome

### ❌ Testing Don'ts

1. **Don't test implementation details**: Avoid testing internal state
2. **Don't skip error cases**: Always test error handling
3. **Don't use brittle selectors**: Prefer semantic queries
4. **Don't write overly complex tests**: Keep tests simple and focused
5. **Don't ignore test performance**: Slow tests hurt productivity
6. **Don't skip integration tests**: Unit tests alone aren't enough
7. **Don't test external libraries**: Focus on your code
8. **Don't commit failing tests**: Maintain green test suite

This comprehensive testing guide ensures Open Stream maintains high quality and reliability throughout its development lifecycle.