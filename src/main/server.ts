// src/main/server.ts
import { app, dialog } from 'electron'
import { spawn, ChildProcess, execFile } from 'child_process'
import path from 'path'
import fs from 'fs-extra'
import { is } from '@electron-toolkit/utils'
import axios from 'axios'
import { promisify } from 'util'
import { randomBytes } from 'crypto'

const execFileAsync = promisify(execFile)

// Security configuration
interface SecurityConfig {
  allowedPythonPaths: string[]
  commandTimeout: number
  maxRetries: number
}


interface PythonPathCache {
  path: string;
  timestamp: number;
  isValid: boolean;
}

interface StartupMetrics {
  totalStartTime: number;
  pythonDiscoveryTime: number;
  venvSetupTime: number;
  serverStartTime: number;
  firstResponseTime: number;
}

export class Server {
  private serverProcess: ChildProcess | null = null
  private pythonPath: string = ''
  private port: number = 0
  private isReady: boolean = false
  private shutdownToken: string = ''
  private tokenRotationInterval: NodeJS.Timeout | null = null
  private startupMetrics: StartupMetrics
  private pythonPathCache: PythonPathCache | null = null
  private readonly cacheExpiryMs = 24 * 60 * 60 * 1000 // 24 hours
  private readonly securityConfig: SecurityConfig = {
    allowedPythonPaths: this.getAllowedPythonPaths(),
    commandTimeout: 30000, // 30 seconds
    maxRetries: 3
  }

  constructor() {
    this.port = this.getRandomPort()
    this.startupMetrics = {
      totalStartTime: Date.now(),
      pythonDiscoveryTime: 0,
      venvSetupTime: 0,
      serverStartTime: 0,
      firstResponseTime: 0
    }
    this.loadPythonPathCache()
    this.generateShutdownToken()
  }

  /**
   * Generate a secure shutdown token and set up rotation
   */
  private generateShutdownToken(): void {
    this.shutdownToken = randomBytes(32).toString('hex')
    console.log('🔐 Generated new shutdown token')
    
    // Clear existing rotation timer
    if (this.tokenRotationInterval) {
      clearInterval(this.tokenRotationInterval)
    }
    
    // Rotate token every 30 minutes for enhanced security
    this.tokenRotationInterval = setInterval(() => {
      this.shutdownToken = randomBytes(32).toString('hex')
      console.log('🔄 Rotated shutdown token')
    }, 30 * 60 * 1000)
  }

  /**
   * Get the current shutdown token
   */
  getShutdownToken(): string {
    return this.shutdownToken
  }

  /**
   * Get list of allowed Python executable paths based on platform
   */
  private getAllowedPythonPaths(): string[] {
    const basePaths = process.platform === 'win32'
      ? [
          'C:\\Python312\\python.exe',
          'C:\\Python311\\python.exe', 
          'C:\\Python310\\python.exe',
          'C:\\Python39\\python.exe',
          'C:\\Python38\\python.exe'
        ]
      : [
          '/usr/bin/python3',
          '/usr/local/bin/python3',
          '/opt/homebrew/bin/python3',
          '/usr/bin/python3.12',
          '/usr/bin/python3.11',
          '/usr/bin/python3.10',
          '/usr/bin/python3.9',
          '/usr/bin/python3.8'
        ]

    // Add venv paths that we create
    const userDataPath = app.getPath('userData')
    const venvPython = process.platform === 'win32'
      ? path.join(userDataPath, 'server-venv', 'Scripts', 'python.exe')
      : path.join(userDataPath, 'server-venv', 'bin', 'python')
    
    if (is.dev) {
      const localVenvPython = process.platform === 'win32'
        ? path.join(__dirname, '../../server/venv', 'Scripts', 'python.exe')
        : path.join(__dirname, '../../server/venv', 'bin', 'python')
      basePaths.push(localVenvPython)
    }
    
    basePaths.push(venvPython)
    
    return basePaths
  }

  private getRandomPort(): number {
    return Math.floor(Math.random() * 10000) + 50000
  }

  /**
   * Validate that a Python path is safe to use
   */
  private async validatePythonPath(pythonPath: string): Promise<boolean> {
    try {
      // Check if path is absolute
      if (!path.isAbsolute(pythonPath)) {
        console.warn(`Rejected relative Python path: ${pythonPath}`)
        return false
      }

      // Check if path exists
      if (!await fs.pathExists(pythonPath)) {
        return false
      }

      // Check if it's in our allowlist
      const normalizedPath = path.normalize(pythonPath)
      const isAllowed = this.securityConfig.allowedPythonPaths.some(allowedPath => 
        path.normalize(allowedPath) === normalizedPath
      )

      if (!isAllowed) {
        console.warn(`Rejected non-allowlisted Python path: ${pythonPath}`)
        return false
      }

      // Verify it's actually a Python executable
      const { stdout } = await execFileAsync(pythonPath, ['--version'], {
        timeout: 5000,
        env: this.getSecureEnvironment()
      })
      
      if (!stdout.includes('Python 3.')) {
        console.warn(`Invalid Python executable: ${pythonPath}`)
        return false
      }

      const version = stdout.match(/Python 3\.(\d+)/)?.[1]
      if (!version || parseInt(version) < 8) {
        console.warn(`Python version too old: ${stdout.trim()}`)
        return false
      }

      return true
    } catch (error) {
      console.warn(`Failed to validate Python path ${pythonPath}:`, error)
      return false
    }
  }

  /**
   * Get secure environment variables for subprocess execution
   */
  private getSecureEnvironment(): Record<string, string> {
    // Only pass essential environment variables
    const secureEnv: Record<string, string> = {
      PATH: process.env.PATH || '',
      PYTHONUNBUFFERED: '1',
      PYTHONDONTWRITEBYTECODE: '1'
    }

    // Add platform-specific variables if needed
    if (process.platform === 'win32') {
      secureEnv.SYSTEMROOT = process.env.SYSTEMROOT || ''
      secureEnv.TEMP = process.env.TEMP || ''
      secureEnv.TMP = process.env.TMP || ''
    } else {
      secureEnv.HOME = process.env.HOME || ''
      secureEnv.TMPDIR = process.env.TMPDIR || '/tmp'
    }

    return secureEnv
  }

  /**
   * Secure command execution using execFile instead of exec
   */
  private async execSecureCommand(
    executable: string, 
    args: string[], 
    options: { cwd?: string; timeout?: number } = {}
  ): Promise<string> {
    const timeout = options.timeout || this.securityConfig.commandTimeout

    try {
      const { stdout } = await execFileAsync(executable, args, {
        cwd: options.cwd,
        timeout,
        env: this.getSecureEnvironment(),
        maxBuffer: 1024 * 1024 // 1MB max output
      })
      
      return stdout.trim()
    } catch (error: any) {
      if (error.killed && error.signal === 'SIGTERM') {
        throw new Error(`Command timed out after ${timeout}ms`)
      }
      throw error
    }
  }

  async initialize(): Promise<boolean> {
    const startTime = Date.now();
    
    try {
      console.log('🚀 Initializing optimized backend server...');
      
      // Start multiple checks in parallel
      const [setupExists, cachedPython] = await Promise.all([
        this.checkSetupExists(),
        this.getCachedOrFindPython()
      ]);
      
      this.startupMetrics.pythonDiscoveryTime = Date.now() - startTime;
      console.log(`⚡ Python discovery: ${this.startupMetrics.pythonDiscoveryTime}ms`);
      
      if (!setupExists) {
        console.log('📦 First run detected - installing dependencies...');
        
        if (!cachedPython) {
          const result = await dialog.showMessageBox({
            type: 'error',
            title: 'Python Not Found',
            message: 'Python 3.8+ is required to run the backend server.',
            detail: 'Please install Python from python.org and restart the app.\n\nRecommended: Python 3.11 or 3.12 for best compatibility.',
            buttons: ['Download Python', 'Quit'],
            defaultId: 0
          });
          
          if (result.response === 0) {
            const { shell } = require('electron');
            shell.openExternal('https://www.python.org/downloads/');
          }
          
          return false;
        }
        
        const setupSuccess = await this.firstTimeSetup();
        if (!setupSuccess) {
          return false;
        }
        
        if (!is.dev) {
          const setupPath = path.join(app.getPath('userData'), '.server-setup');
          await fs.writeFile(setupPath, new Date().toISOString());
        }
        
        console.log('✅ First-time setup completed successfully');
      } else {
        console.log('✅ Dependencies already installed, using cached setup...');
        
        // In development mode, always prefer local venv if it exists
        if (is.dev) {
          const localVenvPython = process.platform === 'win32'
            ? path.join(__dirname, '../../server/venv', 'Scripts', 'python.exe')
            : path.join(__dirname, '../../server/venv', 'bin', 'python');
            
          if (await fs.pathExists(localVenvPython)) {
            console.log(`🐍 Using development virtual environment: ${localVenvPython}`);
            // Add to allowed paths for validation
            this.securityConfig.allowedPythonPaths.push(path.normalize(localVenvPython));
            
            if (await this.validatePythonPath(localVenvPython)) {
              this.pythonPath = localVenvPython;
            } else {
              console.warn('Local venv Python failed validation, falling back to cached Python');
              this.pythonPath = cachedPython;
            }
          } else {
            this.pythonPath = cachedPython;
          }
        } else {
          this.pythonPath = cachedPython;
        }
      }
      
      // Start server
      await this.startServer();
      
      // Preload models in background after server is ready
      setTimeout(() => {
        this.preloadModelsInBackground();
      }, 1000);
      
      return true;
    } catch (error) {
      console.error('Failed to initialize server:', error);
      return false;
    }
  }

  private async firstTimeSetup(): Promise<boolean> {
    console.log('📦 First time setup - installing server dependencies...')
    
    // Find Python
    this.pythonPath = await this.findSecurePython()
    
    if (!this.pythonPath) {
      const result = await dialog.showMessageBox({
        type: 'error',
        title: 'Python Not Found',
        message: 'Python 3.8+ is required to run the backend server.',
        detail: 'Please install Python from python.org and restart the app.\n\nRecommended: Python 3.11 or 3.12 for best compatibility.',
        buttons: ['Download Python', 'Quit'],
        defaultId: 0
      })
      
      if (result.response === 0) {
        const { shell } = require('electron')
        shell.openExternal('https://www.python.org/downloads/')
      }
      
      return false
    }
    
    // Check Python version
    const versionCheck = await this.execSecureCommand(this.pythonPath, ['--version'])
    console.log('Python version:', versionCheck)
    
    if (versionCheck.includes('3.13')) {
      console.warn('⚠️ Python 3.13 detected - some packages may have compatibility issues')
      console.warn('💡 Recommended: Use Python 3.11 or 3.12 for best compatibility')
    }
    
    // Create venv
    let venvPath: string
    
    if (is.dev) {
      venvPath = path.join(__dirname, '../../server/venv')
      console.log('Creating local virtual environment in server/venv...')
    } else {
      venvPath = path.join(app.getPath('userData'), 'server-venv')
      console.log('Creating virtual environment...')
    }
    
    if (!await fs.pathExists(venvPath)) {
      console.log('Creating virtual environment...')
      
      try {
        await this.execSecureCommand(this.pythonPath, ['-m', 'venv', venvPath])
      } catch (error) {
        console.error('Failed to create venv:', error)
        throw new Error('Failed to create Python virtual environment')
      }
    }
    
    // Update Python path to use venv and validate it
    const newPythonPath = process.platform === 'win32'
      ? path.join(venvPath, 'Scripts', 'python.exe')
      : path.join(venvPath, 'bin', 'python')
    
    // Add the new venv path to allowed paths temporarily for validation
    this.securityConfig.allowedPythonPaths.push(path.normalize(newPythonPath))
    
    if (await this.validatePythonPath(newPythonPath)) {
      this.pythonPath = newPythonPath
    } else {
      throw new Error('Created Python virtual environment is not secure')
    }
    
    // Upgrade pip first
    console.log('Upgrading pip...')
    try {
      await this.execSecureCommand(this.pythonPath, ['-m', 'pip', 'install', '--upgrade', 'pip'])
    } catch (error) {
      console.warn('Could not upgrade pip:', error)
    }
    
    // Install from requirements.txt if it exists
    const requirementsPath = path.join(__dirname, '../../server/requirements.txt')
    
    if (await fs.pathExists(requirementsPath)) {
      console.log('Installing from requirements.txt...')
      try {
        await this.execSecureCommand(this.pythonPath, ['-m', 'pip', 'install', '-r', requirementsPath])
        console.log('✅ Installed all requirements!')
      } catch (error) {
        console.error('Failed to install from requirements.txt:', error)
        // Fall back to individual packages
        await this.installPackagesIndividually()
      }
    } else {
      // No requirements.txt, install individually
      await this.installPackagesIndividually()
    }
    
    console.log('✅ Server setup complete!')
    return true
  }

  private async installPackagesIndividually(): Promise<void> {
    console.log('Installing packages individually...')
    
    const packages = [
      'fastapi',
      'uvicorn[standard]'
      // FastAPI will handle pydantic automatically
    ]
    
    for (const pkg of packages) {
      console.log(`Installing ${pkg}...`)
      try {
        await this.execSecureCommand(this.pythonPath, ['-m', 'pip', 'install', pkg])
        console.log(`✅ Installed ${pkg}`)
      } catch (error) {
        console.error(`Failed to install ${pkg}:`, error)
      }
    }
  }

  /**
   * Find and validate a secure Python installation
   */
  private async findSecurePython(): Promise<string> {
    // First try system Python installations from our allowlist
    for (const candidatePath of this.securityConfig.allowedPythonPaths) {
      if (await this.validatePythonPath(candidatePath)) {
        console.log(`Found valid Python at: ${candidatePath}`)
        return candidatePath
      }
    }
    
    // If no pre-existing Python found, try to find Python executables in PATH
    // but still validate them against our security requirements
    const pathCandidates = process.platform === 'win32'
      ? ['python.exe', 'python3.exe']
      : ['python3', 'python']
    
    for (const candidate of pathCandidates) {
      try {
        // Use 'which' or 'where' to find the full path
        const whichCmd = process.platform === 'win32' ? 'where' : 'which'
        const result = await this.execSecureCommand(whichCmd, [candidate])
        const foundPath = result.split('\n')[0].trim()
        
        if (foundPath && await this.validatePythonPath(foundPath)) {
          console.log(`Found valid Python at: ${foundPath}`)
          // Add to allowed paths for future use
          this.securityConfig.allowedPythonPaths.push(path.normalize(foundPath))
          return foundPath
        }
      } catch {
        // Continue trying other candidates
      }
    }
    
    console.error('No valid Python installation found')
    return ''
  }

  private async startServer(): Promise<void> {
    const scriptPath = this.getSecureServerScriptPath()
    
    // Final validation of Python path before starting server
    if (!await this.validatePythonPath(this.pythonPath)) {
      throw new Error('Python path validation failed before server start')
    }
    
    console.log(`Starting backend server on port ${this.port}...`)
    console.log(`🐍 Python executable: ${this.pythonPath}`)
    
    // Log whether we're using venv or system Python
    if (this.pythonPath.includes('venv')) {
      console.log(`✅ Using virtual environment Python (with installed dependencies)`)
    } else {
      console.log(`⚠️ Using system Python - dependencies may not be available`)
    }
    
    console.log(`📜 Script path: ${scriptPath}`)
    
    // Validate script path exists and is in expected location
    if (!await fs.pathExists(scriptPath)) {
      throw new Error(`Server script not found: ${scriptPath}`)
    }
    
    const secureEnv = {
      ...this.getSecureEnvironment(),
      PORT: this.port.toString(),
      SHUTDOWN_TOKEN: this.shutdownToken,
      ELECTRON_APP_ID: `electron-${process.pid}-${Date.now()}` // Unique Electron app identifier
    }
    
    this.serverProcess = spawn(this.pythonPath, [scriptPath, this.port.toString()], {
      cwd: path.dirname(scriptPath),
      env: secureEnv,
      shell: false, // Never use shell
      stdio: ['ignore', 'pipe', 'pipe'], // Explicit stdio configuration
      detached: false // Keep attached to parent process
    })
    
    this.serverProcess.stdout?.on('data', (data) => {
      this.handleServerOutput(data.toString(), 'stdout')
    })
    
    this.serverProcess.stderr?.on('data', (data) => {
      this.handleServerOutput(data.toString(), 'stderr')
    })
    
    this.serverProcess.on('error', (error) => {
      console.error('Server process error:', error)
      this.isReady = false
    })
    
    this.serverProcess.on('exit', (code) => {
      console.log(`Server process exited with code ${code}`)
      this.isReady = false
      
      // Only restart on unexpected exits, not on normal shutdown
      if (code !== 0 && code !== null && this.serverProcess) {
        console.log('Scheduling server restart in 3 seconds...')
        setTimeout(() => {
          if (!this.isReady) { // Only restart if still not ready
            this.startServer().catch(error => {
              console.error('Failed to restart server:', error)
            })
          }
        }, 3000)
      }
    })
    
    await this.waitForServer()
  }

  /**
   * Handle server output with proper log level parsing
   * Parses Python log format: "2025-08-13 17:13:26,390 - services.ai_manager - INFO - 🖥️ Using device: CPU"
   */
  private handleServerOutput(data: string, source: 'stdout' | 'stderr'): void {
    const lines = data.toString().trim().split('\n')
    
    for (const line of lines) {
      if (!line.trim()) continue
      
      // Try to extract log level from Python log format
      // Format: YYYY-MM-DD HH:MM:SS,mmm - module_name - LEVEL - message
      const pythonLogMatch = line.match(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - .+ - (DEBUG|INFO|WARNING|ERROR|CRITICAL) - (.+)/)
      
      if (pythonLogMatch) {
        const [, logLevel, message] = pythonLogMatch
        
        switch (logLevel) {
          case 'DEBUG':
            console.log(`[Server Debug]: ${message}`)
            break
          case 'INFO':
            console.log(`[Server]: ${message}`)
            break
          case 'WARNING':
            console.warn(`[Server Warning]: ${message}`)
            break
          case 'ERROR':
          case 'CRITICAL':
            console.error(`[Server Error]: ${message}`)
            break
          default:
            // Fallback for unknown log levels
            console.log(`[Server ${logLevel}]: ${message}`)
        }
      } else {
        // Not a Python log format, use source-based fallback
        if (source === 'stderr') {
          // Check if it looks like an error message
          const looksLikeError = line.toLowerCase().includes('error') ||
                                line.toLowerCase().includes('exception') ||
                                line.toLowerCase().includes('traceback') ||
                                line.toLowerCase().includes('failed')
          
          if (looksLikeError) {
            console.error(`[Server Error]: ${line}`)
          } else {
            // Treat non-error stderr as info (common for Python apps)
            console.log(`[Server]: ${line}`)
          }
        } else {
          // stdout - treat as info
          console.log(`[Server]: ${line}`)
        }
      }
    }
  }

  private async waitForServer(maxAttempts = 30): Promise<void> {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const response = await axios.get(`http://127.0.0.1:${this.port}/health`)
        if (response.data.status === 'ok' || response.data.status === 'healthy') {
          console.log('✅ Backend server is ready!')
          console.log(`📚 API Documentation available at: http://127.0.0.1:${this.port}/docs`)
          this.isReady = true
          return
        }
      } catch {
        // Not ready yet
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
    
    throw new Error('Backend server failed to start')
  }

  /**
   * Get secure server script path with validation
   */
  private getSecureServerScriptPath(): string {
    const scriptPath = is.dev
      ? path.join(__dirname, '../../server/main.py')
      : path.join(process.resourcesPath, 'server', 'main.py')
    
    // Validate the path is within expected directories
    const normalizedPath = path.normalize(scriptPath)
    const allowedBasePaths = [
      path.normalize(path.join(__dirname, '../../server')),
      path.normalize(path.join(process.resourcesPath, 'server'))
    ]
    
    const isAllowed = allowedBasePaths.some(basePath => 
      normalizedPath.startsWith(basePath)
    )
    
    if (!isAllowed) {
      throw new Error(`Server script path not in allowed directories: ${scriptPath}`)
    }
    
    return normalizedPath
  }

  async stop(): Promise<void> {
    if (this.serverProcess) {
      console.log('Stopping backend server...')
      
      // Clear token rotation interval
      if (this.tokenRotationInterval) {
        clearInterval(this.tokenRotationInterval)
        this.tokenRotationInterval = null
      }
      
      try {
        // Try graceful shutdown first with authentication token
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
        
        await axios.post(`http://127.0.0.1:${this.port}/shutdown`, {}, {
          headers: {
            'X-Shutdown-Token': this.shutdownToken,
            'X-Electron-App-ID': `electron-${process.pid}-${Date.now()}`,
            'Content-Type': 'application/json'
          },
          signal: controller.signal,
          timeout: 5000
        })
        
        clearTimeout(timeoutId)
        console.log('Server shutdown gracefully')
      } catch (error) {
        console.warn('Graceful shutdown failed, forcing termination')
        
        // Force kill the process
        if (this.serverProcess && !this.serverProcess.killed) {
          this.serverProcess.kill('SIGTERM')
          
          // Wait a bit, then force kill if still running
          setTimeout(() => {
            if (this.serverProcess && !this.serverProcess.killed) {
              console.warn('Sending SIGKILL to server process')
              this.serverProcess.kill('SIGKILL')
            }
          }, 2000)
        }
      }
      
      this.serverProcess = null
      this.isReady = false
    }
  }

  getPort(): number {
    return this.port
  }

  getIsReady(): boolean {
    return this.isReady
  }

  getApiUrl(): string {
    return `http://127.0.0.1:${this.port}`
  }

  /**
   * Load cached Python path from persistent storage
   */
  private loadPythonPathCache(): void {
    try {
      const userDataPath = app.getPath('userData');
      const cacheFile = path.join(userDataPath, '.python-path-cache.json');
      
      if (fs.existsSync(cacheFile)) {
        const cached = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
        
        // Validate cache age and path existence
        if (
          Date.now() - cached.timestamp < this.cacheExpiryMs &&
          fs.existsSync(cached.path) &&
          cached.isValid
        ) {
          this.pythonPathCache = cached;
          console.log(`📄 Using cached Python path: ${cached.path}`);
        }
      }
    } catch (error) {
      console.warn('Failed to load Python path cache:', error);
    }
  }

  /**
   * Save Python path to cache
   */
  private savePythonPathCache(pythonPath: string): void {
    try {
      const userDataPath = app.getPath('userData');
      const cacheFile = path.join(userDataPath, '.python-path-cache.json');
      
      const cache: PythonPathCache = {
        path: pythonPath,
        timestamp: Date.now(),
        isValid: true
      };
      
      fs.writeFileSync(cacheFile, JSON.stringify(cache, null, 2));
      this.pythonPathCache = cache;
    } catch (error) {
      console.warn('Failed to save Python path cache:', error);
    }
  }

  /**
   * Get cached Python path or find new one
   * In development mode, always prioritize local venv
   */
  private async getCachedOrFindPython(): Promise<string> {
    // In development mode, always check for local venv first
    if (is.dev) {
      const localVenvPython = process.platform === 'win32'
        ? path.join(__dirname, '../../server/venv', 'Scripts', 'python.exe')
        : path.join(__dirname, '../../server/venv', 'bin', 'python');
        
      if (await fs.pathExists(localVenvPython)) {
        console.log(`🐍 Found development virtual environment: ${localVenvPython}`);
        
        // Add to allowed paths for validation
        if (!this.securityConfig.allowedPythonPaths.some(p => path.normalize(p) === path.normalize(localVenvPython))) {
          this.securityConfig.allowedPythonPaths.push(path.normalize(localVenvPython));
        }
        
        if (await this.validatePythonPath(localVenvPython)) {
          console.log(`✅ Using development virtual environment Python`);
          return localVenvPython;
        } else {
          console.warn('Local venv Python failed validation, falling back to discovery');
        }
      }
    }
    
    // Check cached path
    if (this.pythonPathCache && await this.validatePythonPath(this.pythonPathCache.path)) {
      console.log(`📄 Using cached Python path: ${this.pythonPathCache.path}`);
      return this.pythonPathCache.path;
    }
    
    console.log('🔍 Discovering Python installation...');
    const pythonPath = await this.findSecurePython();
    
    if (pythonPath) {
      this.savePythonPathCache(pythonPath);
      console.log(`💾 Cached discovered Python path: ${pythonPath}`);
    }
    
    return pythonPath;
  }

  /**
   * Check if setup exists (parallel-friendly)
   * Verifies both venv exists AND has required packages installed
   */
  private async checkSetupExists(): Promise<boolean> {
    if (is.dev) {
      const localVenv = path.join(__dirname, '../../server/venv');
      const localVenvPython = process.platform === 'win32'
        ? path.join(localVenv, 'Scripts', 'python.exe')
        : path.join(localVenv, 'bin', 'python');
        
      // Check if venv exists and Python executable is present
      if (!await fs.pathExists(localVenv) || !await fs.pathExists(localVenvPython)) {
        console.log('🔍 Development venv not found, setup required');
        return false;
      }
      
      // Quick check if required packages are installed by trying to import fastapi
      try {
        // Add to allowed paths temporarily for validation
        if (!this.securityConfig.allowedPythonPaths.some(p => path.normalize(p) === path.normalize(localVenvPython))) {
          this.securityConfig.allowedPythonPaths.push(path.normalize(localVenvPython));
        }
        
        if (await this.validatePythonPath(localVenvPython)) {
          await this.execSecureCommand(localVenvPython, ['-c', 'import fastapi, uvicorn'], { timeout: 5000 });
          console.log('✅ Development venv setup verified with required packages');
          return true;
        }
      } catch (error) {
        console.log('📦 Development venv exists but packages not installed or invalid, setup required');
        return false;
      }
      
      return false;
    } else {
      const setupPath = path.join(app.getPath('userData'), '.server-setup');
      const venvPath = path.join(app.getPath('userData'), 'server-venv');
      const venvPython = process.platform === 'win32'
        ? path.join(venvPath, 'Scripts', 'python.exe')
        : path.join(venvPath, 'bin', 'python');
        
      // Check if setup marker exists and venv is present
      return await fs.pathExists(setupPath) && await fs.pathExists(venvPython);
    }
  }

  /**
   * Get startup performance metrics
   */
  getStartupMetrics(): StartupMetrics {
    return {
      ...this.startupMetrics,
      totalStartTime: Date.now() - this.startupMetrics.totalStartTime
    };
  }

  /**
   * Preload models in background after startup
   */
  async preloadModelsInBackground(): Promise<void> {
    if (!this.isReady) {
      console.warn('Server not ready, skipping model preload');
      return;
    }
    
    try {
      console.log('🧠 Preloading AI models in background...');
      
      // Trigger model loading without waiting
      const axios = require('axios');
      axios.post(`http://127.0.0.1:${this.port}/analyze`, {
        text: "test",
        include_toxicity: true,
        include_sentiment: true
      }, { timeout: 1000 }).catch(() => {
        // Ignore timeout, we just want to trigger loading
      });
      
    } catch (error) {
      console.warn('Model preload failed:', error);
    }
  }

}

export const server = new Server()
