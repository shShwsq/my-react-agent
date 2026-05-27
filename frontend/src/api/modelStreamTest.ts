import axios from 'axios'
import { StreamingAudioPlayer, StreamingPlayerStatus } from './streamingAudioPlayer'

export interface StreamTestResult {
  success: boolean
  message: string
  responseContent?: string
  responseTime?: number
  audioUrl?: string
  player?: StreamingAudioPlayer
  playerStatus?: StreamingPlayerStatus
}

function extractError(err: any): Error {
  if (err.response?.data) {
    const data = err.response.data
    const status = err.response.status
    const statusText = `HTTP ${status}`
    
    if (data.e && data.m) {
      return new Error(`${statusText}: ${data.m}`)
    }
    if (data.detail) {
      return new Error(`${statusText}: ${data.detail}`)
    }
    return new Error(`${statusText}: ${err.message || '请求失败'}`)
  }
  return new Error(err.message || '请求失败')
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

export interface StreamTestOptions {
  configId?: number
  model: string
  provider?: string
  callMethod: string
  category: string
  subCategory?: string
  baseUrl?: string
  customText?: string
  customAudioBase64?: string
  customImageBase64?: string
  voice?: string
  onChunk?: (chunk: string) => void
}

export async function testTextModelStream(options: StreamTestOptions): Promise<StreamTestResult> {
  const { configId, model, provider = 'aliyun', callMethod, baseUrl = '', customText = 'Hi', onChunk } = options

  const startTime = Date.now()
  let fullContent = ''

  const token = localStorage.getItem('token')

  try {
    const res = await fetch('/api/text/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        messages: [{ role: 'user', content: customText }],
        model,
        provider,
        call_method: callMethod,
        category: 'text',
        config_id: configId,
        base_url: baseUrl,
        stream: true,
        enable_thinking: false,
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

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data: ')) continue
        const data = trimmed.slice(6)
        if (data === '[DONE]') continue

        try {
          const parsed = JSON.parse(data)
          if (parsed.error) {
            return { success: false, message: parsed.error, responseTime }
          }
          if (parsed.e) {
            return { success: false, message: parsed.m || '请求失败', responseTime }
          }
          
          const content = parsed.content || ''
          if (content) {
            fullContent += content
            onChunk?.(content)
          }
        } catch {
          // ignore parse errors
        }
      }
    }

    return { success: true, message: '连接成功', responseContent: fullContent || '流式响应完成', responseTime }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    const err = extractError(e)
    return { success: false, message: err.message, responseTime }
  }
}

export async function testASRModelStream(options: StreamTestOptions): Promise<StreamTestResult> {
  const { configId, model, provider = 'aliyun', callMethod, baseUrl = '', customAudioBase64, onChunk } = options

  const defaultAudioUrl = 'https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3'
  const audioData = customAudioBase64 || defaultAudioUrl

  const startTime = Date.now()
  let fullContent = ''

  const token = localStorage.getItem('token')

  try {
    const res = await fetch('/api/voice/asr', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        audio_data: audioData,
        model,
        provider,
        call_method: callMethod,
        config_id: configId,
        base_url: baseUrl,
        stream: true,
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

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data: ')) continue
        const data = trimmed.slice(6)
        if (data === '[DONE]') continue

        try {
          const parsed = JSON.parse(data)
          if (parsed.error) {
            return { success: false, message: parsed.error, responseTime }
          }
          if (parsed.e) {
            return { success: false, message: parsed.m || '请求失败', responseTime }
          }
          
          const content = parsed.content || ''
          if (content) {
            fullContent += content
            onChunk?.(content)
          }
        } catch {
          // ignore parse errors
        }
      }
    }

    return { success: true, message: '连接成功', responseContent: fullContent || '流式响应完成', responseTime }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    const err = extractError(e)
    return { success: false, message: err.message, responseTime }
  }
}

export async function testTTSModelStream(options: StreamTestOptions): Promise<StreamTestResult> {
  const { configId, model, provider = 'aliyun', callMethod, baseUrl = '', customText = '测试', voice } = options

  const defaultVoice = getDefaultVoice(model)
  const voiceParam = voice || defaultVoice

  const startTime = Date.now()
  const audioChunks: Uint8Array[] = []
  const token = localStorage.getItem('token')

  try {
    const res = await fetch('/api/voice/tts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        text: customText,
        model,
        provider,
        call_method: callMethod,
        config_id: configId,
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

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      audioChunks.push(value)
    }

    const totalLength = audioChunks.reduce((sum, chunk) => sum + chunk.length, 0)
    const audioData = new Uint8Array(totalLength)
    let offset = 0
    for (const chunk of audioChunks) {
      audioData.set(chunk, offset)
      offset += chunk.length
    }

    const firstChunk = audioChunks[0]
    if (firstChunk && firstChunk[0] === 0x7B) {
      try {
        const text = new TextDecoder().decode(audioData)
        const parsed = JSON.parse(text)
        if (parsed.error) {
          return { success: false, message: parsed.error, responseTime }
        }
      } catch {
        // not JSON, continue as audio
      }
    }

    const blob = new Blob([audioData], { type: 'audio/mp3' })
    const audioUrl = URL.createObjectURL(blob)

    return { success: true, message: '连接成功', responseContent: '音频生成成功', responseTime, audioUrl }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    const err = extractError(e)
    return { success: false, message: err.message, responseTime }
  }
}

export async function testTTSModelStreamWithPlayback(
  options: StreamTestOptions,
  onStatusChange?: (status: StreamingPlayerStatus) => void
): Promise<StreamTestResult> {
  const { configId, model, provider = 'aliyun', callMethod, baseUrl = '', customText = '测试', voice } = options

  const defaultVoice = getDefaultVoice(model)
  const voiceParam = voice || defaultVoice

  const startTime = Date.now()
  const token = localStorage.getItem('token')

  const player = new StreamingAudioPlayer({
    onStatusChange,
    onError: (error) => {
      console.error('Streaming audio error:', error)
    },
  })

  try {
    const res = await fetch('/api/voice/tts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        text: customText,
        model,
        provider,
        call_method: callMethod,
        config_id: configId,
        base_url: baseUrl,
        stream: true,
        voice: voiceParam,
      }),
    })

    const responseTime = Date.now() - startTime

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      const errorMsg = errorData.m || errorData.detail || `HTTP ${res.status}`
      player.stop()
      return { success: false, message: errorMsg, responseTime }
    }

    const reader = res.body?.getReader()
    if (!reader) {
      player.stop()
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
      responseContent: '音频生成成功',
      responseTime,
      audioUrl,
      player,
    }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    player.stop()
    const err = extractError(e)
    return { success: false, message: err.message, responseTime }
  }
}

export async function testImageUnderstandingModelStream(options: StreamTestOptions): Promise<StreamTestResult> {
  const { configId, model, provider = 'aliyun', callMethod, baseUrl = '', customText = 'What is this?', customImageBase64, onChunk } = options

  const defaultImageUrl = 'https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg'
  const imageData = customImageBase64 ? `data:image/png;base64,${customImageBase64}` : defaultImageUrl

  const startTime = Date.now()
  let fullContent = ''

  const token = localStorage.getItem('token')

  try {
    const res = await fetch('/api/vision/understanding', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        messages: [{ role: 'user', content: customText }],
        model,
        provider,
        call_method: callMethod,
        config_id: configId,
        base_url: baseUrl,
        stream: true,
        image_url: imageData,
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

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data: ')) continue
        const data = trimmed.slice(6)
        if (data === '[DONE]') continue

        try {
          const parsed = JSON.parse(data)
          if (parsed.error) {
            return { success: false, message: parsed.error, responseTime }
          }
          if (parsed.e) {
            return { success: false, message: parsed.m || '请求失败', responseTime }
          }
          
          const content = parsed.content || ''
          if (content) {
            fullContent += content
            onChunk?.(content)
          }
        } catch {
          // ignore parse errors
        }
      }
    }

    return { success: true, message: '连接成功', responseContent: fullContent || '流式响应完成', responseTime }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    const err = extractError(e)
    return { success: false, message: err.message, responseTime }
  }
}

export async function testModelConnectionStream(options: StreamTestOptions): Promise<StreamTestResult> {
  const { category, subCategory } = options

  if (category === 'text') {
    return testTextModelStream(options)
  }

  if (category === 'voice') {
    if (subCategory === 'asr') {
      return testASRModelStream(options)
    }
    if (subCategory === 'tts') {
      return testTTSModelStream(options)
    }
    return { success: false, message: '未知的语音模型子类型' }
  }

  if (category === 'vision') {
    if (subCategory === 'image_understanding') {
      return testImageUnderstandingModelStream(options)
    }
    return { success: false, message: '未知的视觉模型子类型' }
  }

  return { success: false, message: '该模型类型暂不支持流式测试' }
}
