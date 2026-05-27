import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export interface UserPreferenceData {
  key: string
  value: string
}

export async function setUserPreference(preference: UserPreferenceData): Promise<void> {
  await axios.post(`${API_BASE}/api/user/preferences`, preference, {
    withCredentials: true
  })
}

export async function getUserPreferences(): Promise<Record<string, string>> {
  const response = await axios.get(`${API_BASE}/api/user/preferences`, {
    withCredentials: true
  })
  return response.data.data || {}
}

export async function getUserPreference(key: string): Promise<string | null> {
  const response = await axios.get(`${API_BASE}/api/user/preferences/${key}`, {
    withCredentials: true
  })
  return response.data.data?.value || null
}
