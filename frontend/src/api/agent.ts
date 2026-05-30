import axios from 'axios'

export interface ApiResponse<T = any> {
  e: string
  d: T
  m: string
}

export interface AgentLoopRequest {
  user_input: string
  room_id: string
  context?: {
    api_key?: string
    model?: string
    api_url?: string
    config_id?: number
    [key: string]: any
  }
  max_iterations?: number
  enabled_tools?: string[]
}

export interface AgentLoopEvent {
  type: 'start' | 'iteration' | 'agent_status' | 'brain_stream' | 'brain_result' | 'task_result' | 'check_stream' | 'check_result' | 'file_created' | 'summary' | 'warning' | 'done' | 'info' | 'error' | 'llm_generate_stream' | 'image_understand_stream' | 'variable_set' | 'paused' | 'request_env_vars' | 'env_vars_received'
  [key: string]: any
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

export async function runAgentLoop(
  request: AgentLoopRequest,
  onEvent: (event: AgentLoopEvent) => void,
  onError?: (error: Error) => void,
  signal?: AbortSignal
): Promise<void> {
  try {
    const response = await fetch('/api/agents/loop/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      },
      body: JSON.stringify(request),
      signal
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
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
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            onEvent(data)
          } catch (e) {
            console.warn('Failed to parse SSE data:', line)
          }
        }
      }
    }
  } catch (e: any) {
    const error = extractError(e)
    onError?.(error)
    throw error
  }
}

export async function runAgentLoopSync(request: AgentLoopRequest): Promise<any> {
  try {
    const res = await axios.post<ApiResponse<any>>('/api/agents/loop/run-sync', request)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function pauseAgentLoop(roomId: string): Promise<void> {
  try {
    const res = await axios.post<ApiResponse<any>>('/api/agents/loop/pause', { room_id: roomId })
    if (res.data.e) {
      throw new Error(res.data.m)
    }
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function getAvailableTools(): Promise<any[]> {
  try {
    const res = await axios.get<ApiResponse<any[]>>('/api/agents/loop/tools')
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function getAgentsStatus(): Promise<any> {
  try {
    const res = await axios.get<ApiResponse<any>>('/api/agents/status')
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function getUserPreferences(): Promise<Record<string, string>> {
  try {
    const res = await axios.get<ApiResponse<Record<string, string>>>('/api/user/preferences')
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function setUserPreference(key: string, value: string): Promise<void> {
  try {
    const res = await axios.post<ApiResponse<any>>('/api/user/preferences', { key, value })
    if (res.data.e) {
      throw new Error(res.data.m)
    }
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function submitEnvVars(roomId: string, values: Record<string, string>): Promise<void> {
  try {
    const res = await axios.post<ApiResponse<any>>('/api/agents/loop/submit-env-vars', { room_id: roomId, values })
    if (res.data.e) {
      throw new Error(res.data.m)
    }
  } catch (e: any) {
    throw extractError(e)
  }
}

export interface DeployConfig {
  frontend_external_url: string
}

export async function getDeployConfig(): Promise<DeployConfig> {
  try {
    const res = await axios.get<DeployConfig>('/api/deploy-config')
    return res.data
  } catch (e: any) {
    return { frontend_external_url: '' }
  }
}
