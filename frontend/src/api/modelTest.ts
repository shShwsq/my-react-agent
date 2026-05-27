import axios from 'axios'

export interface ApiResponse<T = any> {
  e: string
  d: T
  m: string
}

export type CallMethod = 'chat' | 'responses' | 'messages' | 'dashscope' | 'openai'

export interface TestRequestOptions {
  configId?: number
  model: string
  provider?: string
  callMethod: CallMethod
  category: string
  subCategory?: string
  baseUrl?: string
  customText?: string
  customAudioBase64?: string
  customImageBase64?: string
  voice?: string
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

export interface TestResult {
  success: boolean
  message: string
  responseContent?: string
  responseTime?: number
  audioUrl?: string
}

export async function testTextModel(options: TestRequestOptions): Promise<TestResult> {
  const { configId, model, provider = 'aliyun', callMethod, baseUrl = '', customText = 'Hi' } = options

  const startTime = Date.now()
  try {
    const res = await axios.post<ApiResponse>('/api/text/completions', {
      messages: [{ role: 'user', content: customText }],
      model,
      provider,
      call_method: callMethod,
      category: 'text',
      config_id: configId,
      base_url: baseUrl,
      stream: false,
      enable_thinking: false,
    })

    const responseTime = Date.now() - startTime

    if (res.data.e) {
      return { success: false, message: res.data.m || '请求失败', responseTime }
    }

    const responseContent = res.data.d?.content || '连接成功'
    return { success: true, message: '连接成功', responseContent, responseTime }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    const err = extractError(e)
    return { success: false, message: err.message, responseTime }
  }
}

export async function testASRModel(options: TestRequestOptions): Promise<TestResult> {
  const { configId, model, provider = 'aliyun', callMethod, baseUrl = '', customAudioBase64 } = options

  const defaultAudioUrl = 'https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3'
  const audioData = customAudioBase64 || defaultAudioUrl

  const startTime = Date.now()
  try {
    const res = await axios.post<ApiResponse>('/api/voice/asr', {
      audio_data: audioData,
      model,
      provider,
      call_method: callMethod,
      config_id: configId,
      base_url: baseUrl,
    })

    const responseTime = Date.now() - startTime

    if (res.data.e) {
      return { success: false, message: res.data.m || '请求失败', responseTime }
    }

    const responseContent = res.data.d?.content || '连接成功'
    return { success: true, message: '连接成功', responseContent, responseTime }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    const err = extractError(e)
    return { success: false, message: err.message, responseTime }
  }
}

export async function testTTSModel(options: TestRequestOptions): Promise<TestResult> {
  const { configId, model, provider = 'aliyun', callMethod, baseUrl = '', customText = '测试', voice } = options

  const defaultVoice = getDefaultVoice(model)
  const voiceParam = voice || defaultVoice

  const startTime = Date.now()
  try {
    const res = await axios.post<ApiResponse>('/api/voice/tts', {
      text: customText,
      model,
      provider,
      call_method: callMethod,
      config_id: configId,
      base_url: baseUrl,
      stream: false,
      voice: voiceParam,
    })

    const responseTime = Date.now() - startTime

    if (res.data.e) {
      return { success: false, message: res.data.m || '请求失败', responseTime }
    }

    const data = res.data.d
    if (data?.audio) {
      const binaryString = atob(data.audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      const audioFormat = data.format || 'mp3'
      const blob = new Blob([bytes], { type: `audio/${audioFormat}` })
      const audioUrl = URL.createObjectURL(blob)
      return { success: true, message: '连接成功', responseContent: '音频生成成功', responseTime, audioUrl }
    }

    return { success: true, message: '连接成功', responseContent: '连接成功', responseTime }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    const err = extractError(e)
    return { success: false, message: err.message, responseTime }
  }
}

export async function testImageGenerationModel(options: TestRequestOptions): Promise<TestResult> {
  const { configId, model, provider = 'aliyun', callMethod, baseUrl = '', customText = 'a red apple' } = options

  const startTime = Date.now()
  try {
    const res = await axios.post<ApiResponse>('/api/vision/generation', {
      prompt: customText,
      model,
      provider,
      call_method: callMethod,
      config_id: configId,
      base_url: baseUrl,
      size: '512*512',
      n: 1,
    })

    const responseTime = Date.now() - startTime

    if (res.data.e) {
      return { success: false, message: res.data.m || '请求失败', responseTime }
    }

    const images = res.data.d?.images || []
    const responseContent = images.length > 0 ? images[0] : '图片生成成功'
    return { success: true, message: '连接成功', responseContent, responseTime }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    const err = extractError(e)
    return { success: false, message: err.message, responseTime }
  }
}

export async function testImageUnderstandingModel(options: TestRequestOptions): Promise<TestResult> {
  const { configId, model, provider = 'aliyun', callMethod, baseUrl = '', customText = 'What is this?', customImageBase64 } = options

  const defaultImageUrl = 'https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg'
  const imageData = customImageBase64 ? `data:image/png;base64,${customImageBase64}` : defaultImageUrl

  const startTime = Date.now()
  try {
    const res = await axios.post<ApiResponse>('/api/vision/understanding', {
      messages: [{
        role: 'user',
        content: customText,
      }],
      model,
      provider,
      call_method: callMethod,
      config_id: configId,
      base_url: baseUrl,
      stream: false,
      image_url: imageData,
    })

    const responseTime = Date.now() - startTime

    if (res.data.e) {
      return { success: false, message: res.data.m || '请求失败', responseTime }
    }

    const responseContent = res.data.d?.content || '连接成功'
    return { success: true, message: '连接成功', responseContent, responseTime }
  } catch (e: any) {
    const responseTime = Date.now() - startTime
    const err = extractError(e)
    return { success: false, message: err.message, responseTime }
  }
}

export async function testModelConnection(options: TestRequestOptions): Promise<TestResult> {
  const { category, subCategory } = options

  if (category === 'text') {
    return testTextModel(options)
  }

  if (category === 'voice') {
    if (subCategory === 'asr') {
      return testASRModel(options)
    }
    if (subCategory === 'tts') {
      return testTTSModel(options)
    }
    return { success: false, message: '未知的语音模型子类型' }
  }

  if (category === 'vision') {
    if (subCategory === 'image_generation') {
      return testImageGenerationModel(options)
    }
    if (subCategory === 'image_understanding') {
      return testImageUnderstandingModel(options)
    }
    return { success: false, message: '未知的视觉模型子类型' }
  }

  return { success: false, message: '未知的模型类型' }
}
