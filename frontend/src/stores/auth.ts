import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

interface ApiResponse<T = any> {
  e: string
  d: T
  m: string
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

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const isSuper = ref(localStorage.getItem('isSuper') === 'true')

  const isAuthenticated = computed(() => !!token.value)

  function setAuth(newToken: string, newUsername: string, superUser: boolean = false) {
    token.value = newToken
    username.value = newUsername
    isSuper.value = superUser
    localStorage.setItem('token', newToken)
    localStorage.setItem('username', newUsername)
    localStorage.setItem('isSuper', String(superUser))
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
  }

  function clearAuth() {
    token.value = ''
    username.value = ''
    isSuper.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('isSuper')
    delete axios.defaults.headers.common['Authorization']
  }

  async function fetchUserInfo() {
    if (!token.value) return
    try {
      const res = await axios.get<ApiResponse<{ is_super: boolean }>>('/api/auth/me')
      if (res.data.e) {
        clearAuth()
        return
      }
      isSuper.value = res.data.d.is_super || false
      localStorage.setItem('isSuper', String(isSuper.value))
    } catch {
      clearAuth()
    }
  }

  async function login(user: string, password: string) {
    try {
      const res = await axios.post<ApiResponse<{ access_token: string }>>('/api/auth/login', { username: user, password })
      if (res.data.e) {
        throw new Error(res.data.m || '登录失败')
      }
      setAuth(res.data.d.access_token, user)
      await fetchUserInfo()
    } catch (e: any) {
      throw extractError(e)
    }
  }

  async function register(user: string, password: string) {
    try {
      const res = await axios.post<ApiResponse<{ access_token: string }>>('/api/auth/register', { username: user, password })
      if (res.data.e) {
        throw new Error(res.data.m || '注册失败')
      }
      setAuth(res.data.d.access_token, user)
    } catch (e: any) {
      throw extractError(e)
    }
  }

  async function updateProfile(data: { username: string; current_password: string; new_password?: string }) {
    try {
      const res = await axios.put<ApiResponse<{ access_token: string; username: string }>>('/api/auth/profile', data)
      if (res.data.e) {
        throw new Error(res.data.m || '修改失败')
      }
      setAuth(res.data.d.access_token, res.data.d.username)
    } catch (e: any) {
      throw extractError(e)
    }
  }

  function logout() {
    clearAuth()
  }

  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  return { token, username, isSuper, isAuthenticated, login, register, logout, fetchUserInfo, updateProfile }
})
