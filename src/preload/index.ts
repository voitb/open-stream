import { contextBridge, ipcRenderer } from 'electron'

console.log('Preload: Script starting to load')

// Create a simple electronAPI object to replace the @electron-toolkit/preload dependency
const electronAPI = {
  ipcRenderer: {
    sendMessage: (channel: string, ...args: any[]) => {
      ipcRenderer.send(channel, ...args)
    },
    on: (channel: string, func: (...args: any[]) => void) => {
      const validChannels = ['ping']
      if (validChannels.includes(channel)) {
        ipcRenderer.on(channel, (_, ...args) => func(...args))
      }
    },
    once: (channel: string, func: (...args: any[]) => void) => {
      const validChannels = ['ping']
      if (validChannels.includes(channel)) {
        ipcRenderer.once(channel, (_, ...args) => func(...args))
      }
    }
  }
}

// Custom APIs for renderer
const api = {}

const serverAPI = {
  getPort: () => ipcRenderer.invoke('server:getPort'),
  isReady: () => ipcRenderer.invoke('server:isReady'),
  getApiUrl: () => ipcRenderer.invoke('server:getApiUrl'),
  analyze: (text: string) => ipcRenderer.invoke('server:analyze', text),
  processChat: (message: any) => ipcRenderer.invoke('server:processChat', message)
}

console.log('Preload: serverAPI object created:', Object.keys(serverAPI))

// Always expose APIs - Use contextBridge if available, fallback to window
function exposeAPIs() {
  try {
    if (process.contextIsolated) {
      console.log('Preload: Using contextBridge (context isolation enabled)')
      contextBridge.exposeInMainWorld('electron', electronAPI)
      contextBridge.exposeInMainWorld('api', api)
      contextBridge.exposeInMainWorld('serverAPI', serverAPI)
      console.log('Preload: Successfully exposed APIs via contextBridge')
    } else {
      console.log('Preload: Using direct window assignment (context isolation disabled)')
      // @ts-ignore (define in dts)
      window.electron = electronAPI
      // @ts-ignore (define in dts)
      window.api = api
      // @ts-ignore (define in dts)
      window.serverAPI = serverAPI
      console.log('Preload: Successfully exposed APIs directly to window')
    }
    
    // Verify the API was exposed correctly
    setTimeout(() => {
      console.log('Preload: Verifying API exposure...')
      console.log('window.serverAPI exists:', typeof (window as any).serverAPI !== 'undefined')
      console.log('window.serverAPI keys:', (window as any).serverAPI ? Object.keys((window as any).serverAPI) : 'undefined')
    }, 100)
    
    return true
  } catch (error) {
    console.error('Preload: Failed to expose APIs:', error)
    return false
  }
}

// Expose APIs immediately
const apiExposed = exposeAPIs()

if (!apiExposed) {
  console.error('Preload: CRITICAL - Failed to expose serverAPI')
} else {
  console.log('Preload: APIs exposed successfully')
}

// Listen for DOMContentLoaded to verify everything is working
document.addEventListener('DOMContentLoaded', () => {
  console.log('Preload: DOM loaded, performing final API check')
  console.log('window.serverAPI available:', typeof (window as any).serverAPI !== 'undefined')
  
  if (typeof (window as any).serverAPI === 'undefined') {
    console.error('Preload: CRITICAL - serverAPI still not available after DOM load!')
  } else {
    console.log('Preload: ✅ serverAPI successfully available to renderer')
  }
})

console.log('Preload: Script finished loading')
