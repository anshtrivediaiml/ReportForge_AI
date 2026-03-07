import { ProgressUpdate } from '@/types'

export class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private listeners: Map<string, Set<(data: any) => void>> = new Map()

  constructor(private url: string) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected')
          this.reconnectAttempts = 0
          this.emit('connected', {})
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data: ProgressUpdate = JSON.parse(event.data)
            console.log('📨 WebSocket message received:', data.type, data)
            this.emit('message', data)
            
            // Emit specific event types
            if (data.type === 'progress') {
              this.emit('progress', data)
            } else if (data.type === 'log') {
              this.emit('log', data)
            } else if (data.type === 'error') {
              this.emit('error', data)
            } else if (data.type === 'connected') {
              this.emit('connected', data)
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error, event.data)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.emit('error', { error })
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket closed')
          this.emit('disconnected', {})
          
          // Attempt to reconnect
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++
            console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
            setTimeout(() => {
              this.connect().catch(console.error)
            }, this.reconnectDelay)
          }
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  on(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)
  }

  off(event: string, callback: (data: any) => void) {
    this.listeners.get(event)?.delete(callback)
  }

  private emit(event: string, data: any) {
    this.listeners.get(event)?.forEach((callback) => callback(data))
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.listeners.clear()
  }

  send(data: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data)
    }
  }
}

