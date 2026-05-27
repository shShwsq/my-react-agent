export interface StreamingAudioPlayerOptions {
  onStatusChange?: (status: StreamingPlayerStatus) => void
  onError?: (error: string) => void
  onComplete?: (audioUrl: string) => void
}

export type StreamingPlayerStatus = 'idle' | 'connecting' | 'playing' | 'completed' | 'error'

export class StreamingAudioPlayer {
  private audioContext: AudioContext | null = null
  private mediaSource: MediaSource | null = null
  private sourceBuffer: SourceBuffer | null = null
  private audioElement: HTMLAudioElement | null = null
  private audioChunks: Uint8Array[] = []
  private status: StreamingPlayerStatus = 'idle'
  private options: StreamingAudioPlayerOptions
  private isBufferAppending = false
  private pendingChunks: Uint8Array[] = []
  private isEnded = false

  constructor(options: StreamingAudioPlayerOptions = {}) {
    this.options = options
  }

  getStatus(): StreamingPlayerStatus {
    return this.status
  }

  private setStatus(status: StreamingPlayerStatus) {
    this.status = status
    this.options.onStatusChange?.(status)
  }

  async start(): Promise<void> {
    this.audioChunks = []
    this.pendingChunks = []
    this.isEnded = false
    this.isBufferAppending = false
    this.setStatus('connecting')

    try {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      
      this.mediaSource = new MediaSource()
      const mediaSourceUrl = URL.createObjectURL(this.mediaSource)
      
      this.audioElement = new Audio(mediaSourceUrl)
      this.audioElement.autoplay = true
      
      await new Promise<void>((resolve, reject) => {
        if (!this.mediaSource) {
          reject(new Error('MediaSource not initialized'))
          return
        }
        
        this.mediaSource.addEventListener('sourceopen', () => {
          if (!this.mediaSource) {
            reject(new Error('MediaSource not available'))
            return
          }
          
          try {
            this.sourceBuffer = this.mediaSource.addSourceBuffer('audio/mpeg')
            this.sourceBuffer.mode = 'sequence'
            
            this.sourceBuffer.addEventListener('updateend', () => {
              this.isBufferAppending = false
              this.processPendingChunks()
              
              if (this.isEnded && this.pendingChunks.length === 0) {
                if (this.mediaSource && this.mediaSource.readyState === 'open') {
                  this.mediaSource.endOfStream()
                }
              }
            })
            
            this.sourceBuffer.addEventListener('error', (e) => {
              console.error('SourceBuffer error:', e)
              this.handleError('音频解码错误')
            })
            
            resolve()
          } catch (e) {
            reject(e)
          }
        })
        
        this.mediaSource!.addEventListener('sourceended', () => {
          this.setStatus('completed')
        })
        
        this.audioElement!.addEventListener('playing', () => {
          if (this.status === 'connecting') {
            this.setStatus('playing')
          }
        })
        
        this.audioElement!.addEventListener('error', (e) => {
          console.error('Audio element error:', e)
          this.handleError('音频播放错误')
        })
      })
    } catch (e: any) {
      this.handleError(e.message || '初始化音频播放器失败')
      throw e
    }
  }

  private processPendingChunks() {
    if (this.isBufferAppending || !this.sourceBuffer || this.pendingChunks.length === 0) {
      return
    }
    
    this.isBufferAppending = true
    const chunk = this.pendingChunks.shift()!
    
    try {
      this.sourceBuffer.appendBuffer(chunk as unknown as ArrayBuffer)
    } catch (e: any) {
      console.error('Error appending buffer:', e)
      this.isBufferAppending = false
      this.handleError('音频数据追加失败')
    }
  }

  appendChunk(chunk: Uint8Array): void {
    this.audioChunks.push(chunk)
    
    if (chunk[0] === 0x7B) {
      try {
        const text = new TextDecoder().decode(chunk)
        const parsed = JSON.parse(text)
        if (parsed.error) {
          this.handleError(parsed.error)
          return
        }
      } catch {
        // Not JSON, treat as audio
      }
    }
    
    if (this.sourceBuffer && this.mediaSource && this.mediaSource.readyState === 'open') {
      this.pendingChunks.push(chunk)
      this.processPendingChunks()
    }
  }

  end(): string | null {
    this.isEnded = true
    
    if (this.pendingChunks.length === 0 && this.mediaSource && this.mediaSource.readyState === 'open') {
      this.mediaSource.endOfStream()
    }
    
    const audioUrl = this.getCompleteAudioUrl()
    if (audioUrl) {
      this.options.onComplete?.(audioUrl)
    }
    
    return audioUrl
  }

  getCompleteAudioUrl(): string | null {
    if (this.audioChunks.length === 0) {
      return null
    }
    
    const totalLength = this.audioChunks.reduce((sum, chunk) => sum + chunk.length, 0)
    const audioData = new Uint8Array(totalLength)
    let offset = 0
    for (const chunk of this.audioChunks) {
      audioData.set(chunk, offset)
      offset += chunk.length
    }
    
    const blob = new Blob([audioData], { type: 'audio/mp3' })
    return URL.createObjectURL(blob)
  }

  private handleError(message: string) {
    this.setStatus('error')
    this.options.onError?.(message)
  }

  stop(): void {
    if (this.audioElement) {
      this.audioElement.pause()
      this.audioElement.src = ''
      this.audioElement = null
    }
    
    if (this.audioContext) {
      this.audioContext.close()
      this.audioContext = null
    }
    
    this.mediaSource = null
    this.sourceBuffer = null
    this.audioChunks = []
    this.pendingChunks = []
    this.setStatus('idle')
  }

  pause(): void {
    this.audioElement?.pause()
  }

  resume(): void {
    if (this.audioContext?.state === 'suspended') {
      this.audioContext.resume()
    }
    this.audioElement?.play()
  }

  setVolume(volume: number): void {
    if (this.audioElement) {
      this.audioElement.volume = Math.max(0, Math.min(1, volume))
    }
  }
}

export interface TTSStreamResult {
  success: boolean
  message: string
  responseTime?: number
  audioUrl?: string
  player?: StreamingAudioPlayer
}

export interface TTSStreamOptions {
  model: string
  provider?: string
  callMethod: string
  apiKey?: string
  baseUrl?: string
  text?: string
  voice?: string
  onStatusChange?: (status: StreamingPlayerStatus) => void
  onError?: (error: string) => void
  onAudioComplete?: (audioUrl: string) => void
}

const TTS_DEFAULT_VOICE: Record<string, string> = {
  'cosyvoice-v3.5-flash': 'cosyvoice-v3.5-flash-vd-announcer-d3516a74975247548d2c2067c72c63b7',
  'cosyvoice-v3.5-plus': 'cosyvoice-v3.5-plus-vd-announcer-d3516a74975247548d2c2067c72c63b7',
  'cosyvoice-v3-flash': 'longanyang',
  'cosyvoice-v3-plus': 'longanyang',
  'cosyvoice-v2': 'longxiaochun_v2',
  'cosyvoice-v1': 'longwan',
}

function getDefaultVoice(model: string): string {
  return TTS_DEFAULT_VOICE[model] || 'longanyang'
}

export async function streamTTSWithRealtimePlayback(
  options: TTSStreamOptions
): Promise<TTSStreamResult> {
  const {
    model,
    provider = 'aliyun',
    callMethod,
    apiKey = '',
    baseUrl = '',
    text = '测试',
    voice,
    onStatusChange,
    onError,
    onAudioComplete,
  } = options

  const defaultVoice = getDefaultVoice(model)
  const voiceParam = voice || defaultVoice

  const startTime = Date.now()
  const token = localStorage.getItem('token')

  const player = new StreamingAudioPlayer({
    onStatusChange,
    onError,
    onComplete: onAudioComplete,
  })

  try {
    const res = await fetch('/api/voice/tts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        text,
        model,
        provider,
        call_method: callMethod,
        api_key: apiKey,
        base_url: baseUrl,
        stream: true,
        voice: voiceParam,
      }),
    })

    const responseTime = Date.now() - startTime

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      const errorMsg = errorData.m || errorData.detail || `HTTP ${res.status}`
      return { success: false, message: errorMsg, responseTime }
    }

    const reader = res.body?.getReader()
    if (!reader) {
      return { success: false, message: '无法获取响应流', responseTime }
    }

    await player.start()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      player.appendChunk(value)
    }

    const audioUrl = player.end() || undefined

    return {
      success: true,
      message: '连接成功',
      responseTime,
      audioUrl,
      player,
    }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    player.stop()
    return { success: false, message: e.message || '请求失败', responseTime }
  }
}
