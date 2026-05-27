export type MessageRole = 'user' | 'assistant' | 'brain' | 'task' | 'check'

export interface RoomMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: number
}

export interface AgentHistoryRecord {
  content: string
  timestamp: number
}

export interface AgentCacheData {
  id: string
  name: string
  type: string
  status: string
  history: AgentHistoryRecord[]
}

export interface RoomCache {
  id: string
  title: string
  models: Record<string, any> | null
  messages: RoomMessage[]
  agents?: AgentCacheData[]
  createdAt: number
  updatedAt: number
}

function getRoomKey(roomId: string): string {
  return `room_${roomId}`
}

export function saveRoomCache(room: RoomCache): void {
  localStorage.setItem(getRoomKey(room.id), JSON.stringify(room))
}

export function getRoomCache(roomId: string): RoomCache | null {
  const data = localStorage.getItem(getRoomKey(roomId))
  return data ? JSON.parse(data) : null
}

export function addMessageToRoom(roomId: string, message: RoomMessage): void {
  const room = getRoomCache(roomId)
  if (room) {
    room.messages.push(message)
    room.updatedAt = Date.now()
    saveRoomCache(room)
  }
}

export function updateRoomMessages(roomId: string, messages: RoomMessage[]): void {
  const room = getRoomCache(roomId)
  if (room) {
    room.messages = messages
    room.updatedAt = Date.now()
    saveRoomCache(room)
  }
}

export function getAllRooms(): RoomCache[] {
  const rooms: RoomCache[] = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key?.startsWith('room_')) {
      const data = localStorage.getItem(key)
      if (data) {
        try {
          rooms.push(JSON.parse(data))
        } catch (e) {
          console.warn('Failed to parse room cache:', key)
        }
      }
    }
  }
  return rooms.sort((a, b) => b.updatedAt - a.updatedAt)
}

export function deleteRoomCache(roomId: string): void {
  localStorage.removeItem(getRoomKey(roomId))
}

export function createRoomCache(id: string, models: Record<string, any>, title?: string): RoomCache {
  const now = Date.now()
  return {
    id,
    title: title || '',
    models,
    messages: [],
    createdAt: now,
    updatedAt: now
  }
}

export interface UserPreference {
  key: string
  value: string
  updatedAt: number
}

const USER_PREFERENCES_KEY = 'user_preferences'

export function saveUserPreference(key: string, value: string): void {
  const prefs = getUserPreferences()
  prefs[key] = {
    key,
    value,
    updatedAt: Date.now()
  }
  localStorage.setItem(USER_PREFERENCES_KEY, JSON.stringify(prefs))
}

export function getUserPreferences(): Record<string, UserPreference> {
  const data = localStorage.getItem(USER_PREFERENCES_KEY)
  return data ? JSON.parse(data) : {}
}

export function getUserPreference(key: string): string | null {
  const prefs = getUserPreferences()
  return prefs[key]?.value || null
}

export function clearUserPreferences(): void {
  localStorage.removeItem(USER_PREFERENCES_KEY)
}
