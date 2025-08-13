import './assets/main.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

// Debug logging for serverAPI availability at React startup
console.log('React main: Starting application...')
console.log('React main: window.serverAPI exists:', typeof window.serverAPI !== 'undefined')
console.log('React main: window.electron exists:', typeof window.electron !== 'undefined')

if (typeof window.serverAPI !== 'undefined') {
  console.log('React main: ✅ serverAPI is available at startup')
  console.log('React main: serverAPI methods:', Object.keys(window.serverAPI))
} else {
  console.log('React main: ❌ serverAPI is NOT available at startup')
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
