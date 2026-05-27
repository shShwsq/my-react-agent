import axios from 'axios'

export interface ApiResponse<T = any> {
  e: string
  d: T
  m: string
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  id: string
  content: string
  model: string
  usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

export type CallMethod = 'chat' | 'responses' | 'messages' | 'dashscope'

export interface ChatRequestOptions {
  messages: ChatMessage[]
  model: string
  provider?: string
  callMethod: CallMethod
  category?: string
  subCategory?: string
  apiKey?: string
  baseUrl?: string
  stream?: boolean
  onChunk?: (content: string) => void
  onDone?: () => void
  onError?: (error: Error) => void
}

function extractError(err: any): Error {
  if (err.response?.data) {
    const data = err.response.data
    if (data.e && data.m) {
      return new Error(data.m)
    }
  }
  return new Error(err.message || '请求失败')
}

export async function sendChatRequest(options: ChatRequestOptions): Promise<ChatResponse | void> {
  const { messages, model, provider = 'aliyun', callMethod, category = 'text', subCategory, apiKey = '', baseUrl = '', stream = false, onChunk, onDone, onError } = options

  if (stream) {
    return streamChatRequest(options)
  }

  try {
    const res = await axios.post<ApiResponse>('/api/text/completions', {
      messages,
      model,
      provider,
      call_method: callMethod,
      category,
      sub_category: subCategory,
      api_key: apiKey,
      base_url: baseUrl,
      stream: false,
    })
    
    if (res.data.e) {
      throw new Error(res.data.m || '请求失败')
    }
    
    const data = res.data.d

    if (callMethod === 'responses') {
      const outputText = data.output?.find((o: any) => o.type === 'message')
        ?.content?.find((c: any) => c.type === 'output_text')?.text || ''
      return {
        id: data.id,
        content: outputText,
        model: data.model || model,
        usage: data.usage,
      }
    }

    if (callMethod === 'messages') {
      const content = data.content?.find((c: any) => c.type === 'text')?.text || ''
      return {
        id: data.id,
        content,
        model: data.model || model,
        usage: data.usage,
      }
    }

    if (callMethod === 'dashscope') {
      const output = data.output || {}
      const text = output.text || output.choices?.[0]?.message?.content || ''
      return {
        id: data.request_id || '',
        content: text,
        model: model,
        usage: data.usage,
      }
    }

    return {
      id: data.id,
      content: data.choices?.[0]?.message?.content || '',
      model: data.model || model,
      usage: data.usage,
    }
  } catch (e: any) {
    const err = extractError(e)
    onError?.(err)
    throw err
  }
}

export async function streamChatRequest(options: ChatRequestOptions): Promise<void> {
  const { messages, model, provider = 'aliyun', callMethod, category = 'text', subCategory, apiKey = '', baseUrl = '', onChunk, onDone, onError } = options

  try {
    const res = await fetch('/api/text/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${axios.defaults.headers.common['Authorization']?.toString().replace('Bearer ', '') || localStorage.getItem('token')}`,
      },
      body: JSON.stringify({
        messages,
        model,
        provider,
        call_method: callMethod,
        category,
        sub_category: subCategory,
        api_key: apiKey,
        base_url: baseUrl,
        stream: true,
      }),
    })

    if (!res.ok) {
      const text = await res.text()
      try {
        const data = JSON.parse(text)
        if (data.e && data.m) {
          throw new Error(data.m)
        }
      } catch {
        throw new Error(`HTTP error: ${res.status}`)
      }
    }

    const reader = res.body?.getReader()
    if (!reader) throw new Error('No reader available')

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
        if (data === '[DONE]') {
          onDone?.()
          return
        }
        try {
          const parsed = JSON.parse(data)
          if (parsed.error) {
            onError?.(new Error(parsed.error))
            return
          }
          if (parsed.content) {
            onChunk?.(parsed.content)
          }
        } catch {
        }
      }
    }
    onDone?.()
  } catch (e: any) {
    onError?.(e)
    throw e
  }
}
