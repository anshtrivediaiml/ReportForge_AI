import { ProgressUpdate } from '@/types'

type Listener = (data: any) => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private readonly maxReconnectAttempts = 5
  private readonly reconnectDelay = 3000
  private readonly listeners = new Map<string, Set<Listener>>()
  private intentionalClose = false
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  constructor(private readonly url: string) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.intentionalClose = false
        this.ws = new WebSocket(this.url)
        let isSettled = false

        this.ws.onopen = () => {
          this.reconnectAttempts = 0
          this.emit('connected', {})
          isSettled = true
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as ProgressUpdate & { type?: string }

            switch (data.type) {
              case 'progress':
                this.emit('progress', data)
                break
              case 'log':
                this.emit('log', data)
                break
              case 'error':
                this.emit('error', data)
                break
              case 'connected':
                this.emit('connected', data)
                break
              case 'heartbeat':
                this.emit('heartbeat', data)
                break
              default:
                this.emit('message', data)
            }
          } catch (error) {
            this.emit('connection-error', { error })
          }
        }

        this.ws.onerror = (error) => {
          this.emit('connection-error', { error })
          if (!isSettled) {
            isSettled = true
            reject(error)
          }
        }

        this.ws.onclose = (event) => {
          this.ws = null
          this.emit('disconnected', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean,
          })

          if (!isSettled && !this.intentionalClose) {
            isSettled = true
            reject(new Error('WebSocket connection closed before it opened'))
          }

          if (!this.intentionalClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts += 1
            this.emit('reconnecting', {
              attempt: this.reconnectAttempts,
              maxAttempts: this.maxReconnectAttempts,
              delayMs: this.reconnectDelay,
            })
            this.reconnectTimer = setTimeout(() => {
              this.connect().catch(() => {
                // Reconnect attempts are surfaced via connection-error/disconnected events.
              })
            }, this.reconnectDelay)
          }
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  on(event: string, callback: Listener) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)?.add(callback)
  }

  off(event: string, callback: Listener) {
    this.listeners.get(event)?.delete(callback)
  }

  disconnect() {
    this.intentionalClose = true
    this.reconnectAttempts = this.maxReconnectAttempts

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.listeners.clear()
  }

  send(data: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data)
    }
  }

  private emit(event: string, data: any) {
    this.listeners.get(event)?.forEach((callback) => callback(data))
  }
}
