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

export interface RoomCreateData {
  id: string
  title?: string
  models?: Record<string, string>
}

export interface RoomMessage {
  id?: string | number
  role: 'user' | 'assistant' | 'brain' | 'task' | 'check'
  content: string
  created_at?: string
}

export interface RoomData {
  id: string
  title: string
  models: Record<string, string> | null
  created_at: string
  messages: RoomMessage[]
}

export interface RoomListItem {
  id: string
  title: string
  created_at: string
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

export async function createRoom(data: RoomCreateData): Promise<RoomData> {
  try {
    const res = await axios.post<ApiResponse<RoomData>>('/api/rooms', data)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export interface MessageCreateData {
  role: 'user' | 'assistant' | 'brain' | 'task' | 'check'
  content: string
}

export async function addMessage(roomId: string, msg: MessageCreateData): Promise<void> {
  try {
    const res = await axios.post<ApiResponse<any>>(`/api/rooms/${roomId}/messages`, msg)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function getRoom(roomId: string): Promise<RoomData> {
  try {
    const res = await axios.get<ApiResponse<RoomData>>(`/api/rooms/${roomId}`)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function getRoomVariables(roomId: string): Promise<Record<string, any>> {
  try {
    const res = await axios.get<ApiResponse<{ variables: Record<string, any> }>>(`/api/rooms/${roomId}/variables`)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d.variables
  } catch (e: any) {
    throw extractError(e)
  }
}

export interface RoomFile {
  filename: string
  folder: string
  file_size: number
  relative_path: string
}

export async function getRoomFiles(roomId: string): Promise<RoomFile[]> {
  try {
    const res = await axios.get<ApiResponse<{ files: RoomFile[] }>>(`/api/files/list/${roomId}`)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d.files || []
  } catch (e: any) {
    throw extractError(e)
  }
}

export interface UploadResult {
  filename: string
  file_size: number
  relative_path: string
  folder: string
}

export async function uploadFile(roomId: string, file: File): Promise<UploadResult> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await axios.post<ApiResponse<UploadResult>>(`/api/files/upload/${roomId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function listRooms(): Promise<RoomListItem[]> {
  try {
    const res = await axios.get<ApiResponse<RoomListItem[]>>('/api/rooms')
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}
