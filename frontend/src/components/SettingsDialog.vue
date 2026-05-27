<template>
  <div class="settings-overlay" v-if="visible" @click.self="$emit('close')">
    <div class="settings-panel">
      <div class="panel-header">
        <h2 class="panel-title">设置</h2>
        <button class="close-btn" @click="$emit('close')">
          <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="panel-tabs">
        <button
          :class="['panel-tab', { active: activeTab === 'account' }]"
          @click="activeTab = 'account'"
        >
          账号设置
        </button>
        <button
          :class="['panel-tab', { active: activeTab === 'cache' }]"
          @click="activeTab = 'cache'"
        >
          本地缓存
        </button>
        <button
          :class="['panel-tab', { active: activeTab === 'tools' }]"
          @click="activeTab = 'tools'"
        >
          工具设置
        </button>
      </div>

      <div class="panel-body">
        <!-- 账号设置 -->
        <div v-if="activeTab === 'account'" class="account-section">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input
              v-model="username"
              class="form-input"
              placeholder="输入新用户名"
              :disabled="updating"
            />
          </div>
          <div class="form-group">
            <label class="form-label">当前密码</label>
            <input
              v-model="currentPassword"
              type="password"
              class="form-input"
              placeholder="输入当前密码"
              :disabled="updating"
            />
          </div>
          <div class="form-group">
            <label class="form-label">新密码</label>
            <input
              v-model="newPassword"
              type="password"
              class="form-input"
              placeholder="输入新密码（留空则不修改）"
              :disabled="updating"
            />
          </div>
          <button class="update-btn" @click="handleUpdateAccount" :disabled="updating">
            <span v-if="!updating">保存修改</span>
            <span v-else class="btn-spinner"></span>
          </button>
          <div v-if="accountMsg" :class="['msg', accountMsgType]">{{ accountMsg }}</div>
        </div>

        <!-- 本地缓存 -->
        <div v-if="activeTab === 'cache'" class="cache-section">
          <!-- 房间列表视图 -->
          <div v-if="!viewingRoom" class="cache-overview">
            <div class="cache-info">
              <p>本地缓存包含房间和对话消息，清理后将无法恢复历史记录。</p>
              <div class="cache-stats">
                <span>缓存房间数: <strong>{{ cacheRoomCount }}</strong></span>
                <span>缓存大小: <strong>{{ cacheSize }}</strong></span>
              </div>
            </div>

            <div v-if="cachedRooms.length === 0" class="empty-rooms">
              <p>暂无缓存的房间</p>
            </div>

            <div v-else class="room-list">
              <div
                v-for="room in cachedRooms"
                :key="room.id"
                class="room-card"
                @click="viewRoom(room)"
              >
                <div class="room-card-header">
                  <div class="room-card-title">{{ room.title || '未命名房间' }}</div>
                  <div class="room-card-actions">
                    <button class="room-action-btn delete" @click.stop="handleDeleteRoom(room.id)" title="删除">
                      <svg viewBox="0 0 16 16" fill="none" width="14" height="14">
                        <path d="M2 4H14M5.33 4V2.67C5.33 2.3 5.63 2 6 2H10C10.37 2 10.67 2.3 10.67 2.67V4M12.67 4V13.33C12.67 13.7 12.37 14 12 14H4C3.63 14 3.33 13.7 3.33 13.33V4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="room-card-meta">
                  <span class="room-id">{{ room.id.slice(0, 8) }}...</span>
                  <span class="room-msg-count">{{ room.messages.length }} 条消息</span>
                  <span class="room-time">{{ formatTime(room.updatedAt) }}</span>
                </div>
                <div v-if="room.messages.length > 0" class="room-card-preview">
                  <span :class="['msg-role', room.messages[room.messages.length - 1].role]">
                    {{ room.messages[room.messages.length - 1].role === 'user' ? '你' : 'AI' }}
                  </span>
                  <span class="msg-preview">{{ room.messages[room.messages.length - 1].content.slice(0, 50) }}</span>
                </div>
              </div>
            </div>

            <button v-if="cachedRooms.length > 0" class="clear-btn" @click="handleClearCache" :disabled="clearing">
              <span v-if="!clearing">清理所有缓存</span>
              <span v-else class="btn-spinner"></span>
            </button>
          </div>

          <!-- 房间详情视图 -->
          <div v-else class="room-detail">
            <div class="room-detail-header">
              <button class="back-btn" @click="viewingRoom = null">
                <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
                  <path d="M13 4L7 10L13 16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                返回
              </button>
              <div class="room-detail-title">{{ viewingRoom.title || '未命名房间' }}</div>
            </div>

            <div class="room-detail-info">
              <span class="info-item">ID: {{ viewingRoom.id.slice(0, 12) }}...</span>
              <span class="info-item">消息: {{ viewingRoom.messages.length }} 条</span>
              <span class="info-item">创建: {{ formatTime(viewingRoom.createdAt) }}</span>
            </div>

            <div class="room-messages">
              <div
                v-for="(msg, idx) in viewingRoom.messages"
                :key="idx"
                :class="['message-item', msg.role]"
              >
                <div class="message-role">{{ msg.role === 'user' ? '用户' : '智能体' }}</div>
                <div class="message-content">{{ msg.content }}</div>
                <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
              </div>
            </div>

            <button class="delete-room-btn" @click="handleDeleteRoom(viewingRoom.id)">
              <svg viewBox="0 0 16 16" fill="none" width="14" height="14">
                <path d="M2 4H14M5.33 4V2.67C5.33 2.3 5.63 2 6 2H10C10.37 2 10.67 2.3 10.67 2.67V4M12.67 4V13.33C12.67 13.7 12.37 14 12 14H4C3.63 14 3.33 13.7 3.33 13.33V4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
              删除此房间
            </button>
          </div>

          <div v-if="cacheMsg" :class="['msg', cacheMsgType]">{{ cacheMsg }}</div>
        </div>

        <!-- 工具设置 -->
        <div v-if="activeTab === 'tools'" class="tools-section">
          <div class="tools-info">
            <p>选择智能体可以使用的工具。禁用工具后，智能体将无法调用该工具。</p>
          </div>
          <div class="tools-loading" v-if="toolsLoading">
            <span class="btn-spinner"></span>
            加载工具列表...
          </div>
          <div v-else class="tools-list">
            <label
              v-for="tool in availableTools"
              :key="tool.name"
              class="tool-toggle-row"
            >
              <div class="tool-info">
                <div class="tool-name">{{ tool.name }}</div>
                <div class="tool-desc">{{ tool.description }}</div>
              </div>
              <label class="toggle-switch">
                <input
                  type="checkbox"
                  :checked="enabledTools.includes(tool.name)"
                  @change="handleToolToggle(tool.name, ($event.target as HTMLInputElement).checked)"
                  :disabled="toolsSaving"
                />
                <span class="toggle-slider"></span>
              </label>
            </label>
            <div v-if="toolsMsg" :class="['msg', toolsMsgType]">{{ toolsMsg }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getRoomCache, type RoomCache } from '@/utils/roomCache'
import { getAvailableTools, getUserPreferences, setUserPreference } from '@/api/agent'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ close: [] }>()

const authStore = useAuthStore()

const activeTab = ref('account')

// 账号设置
const username = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const updating = ref(false)
const accountMsg = ref('')
const accountMsgType = ref<'success' | 'error'>('success')

// 工具设置
interface ToolInfo {
  name: string
  description: string
  parameters: any
}
const availableTools = ref<ToolInfo[]>([])
const enabledTools = ref<string[]>([])
const toolsLoading = ref(false)
const toolsSaving = ref(false)
const toolsMsg = ref('')
const toolsMsgType = ref<'success' | 'error'>('success')

watch(() => props.visible, async (val) => {
  if (val) {
    username.value = authStore.username || ''
    currentPassword.value = ''
    newPassword.value = ''
    accountMsg.value = ''
    cacheMsg.value = ''
    activeTab.value = 'account'
    viewingRoom.value = null
    loadCachedRooms()
    loadToolsSettings()
  }
})

async function loadToolsSettings() {
  toolsLoading.value = true
  toolsMsg.value = ''
  try {
    const [tools, prefs] = await Promise.all([
      getAvailableTools(),
      getUserPreferences()
    ])
    availableTools.value = tools
    const stored = prefs['enabled_tools']
    if (stored) {
      try {
        enabledTools.value = JSON.parse(stored)
      } catch {
        enabledTools.value = tools.map(t => t.name)
      }
    } else {
      enabledTools.value = tools.map(t => t.name)
    }
  } catch (e: any) {
    toolsMsg.value = '加载失败: ' + (e.message || '未知错误')
    toolsMsgType.value = 'error'
  } finally {
    toolsLoading.value = false
  }
}

async function handleToolToggle(toolName: string, enabled: boolean) {
  toolsSaving.value = true
  toolsMsg.value = ''
  try {
    if (enabled) {
      if (!enabledTools.value.includes(toolName)) {
        enabledTools.value.push(toolName)
      }
    } else {
      enabledTools.value = enabledTools.value.filter(n => n !== toolName)
    }
    await setUserPreference('enabled_tools', JSON.stringify(enabledTools.value))
    toolsMsg.value = '保存成功'
    toolsMsgType.value = 'success'
  } catch (e: any) {
    // 回滚
    if (enabled) {
      enabledTools.value = enabledTools.value.filter(n => n !== toolName)
    } else {
      if (!enabledTools.value.includes(toolName)) {
        enabledTools.value.push(toolName)
      }
    }
    toolsMsg.value = '保存失败: ' + (e.message || '未知错误')
    toolsMsgType.value = 'error'
  } finally {
    toolsSaving.value = false
  }
}

async function handleUpdateAccount() {
  if (!currentPassword.value) {
    accountMsg.value = '请输入当前密码'
    accountMsgType.value = 'error'
    return
  }
  if (!username.value.trim()) {
    accountMsg.value = '用户名不能为空'
    accountMsgType.value = 'error'
    return
  }

  updating.value = true
  accountMsg.value = ''

  try {
    await authStore.updateProfile({
      username: username.value.trim(),
      current_password: currentPassword.value,
      new_password: newPassword.value || undefined
    })
    accountMsg.value = '修改成功'
    accountMsgType.value = 'success'
    currentPassword.value = ''
    newPassword.value = ''
  } catch (e: any) {
    accountMsg.value = e.message || '修改失败'
    accountMsgType.value = 'error'
  } finally {
    updating.value = false
  }
}

// 缓存管理
const clearing = ref(false)
const cacheMsg = ref('')
const cacheMsgType = ref<'success' | 'error'>('success')
const viewingRoom = ref<RoomCache | null>(null)
const cachedRooms = ref<RoomCache[]>([])

function loadCachedRooms() {
  const rooms: RoomCache[] = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key?.startsWith('room_')) {
      const data = localStorage.getItem(key)
      if (data) {
        try {
          rooms.push(JSON.parse(data))
        } catch {
          // ignore invalid data
        }
      }
    }
  }
  cachedRooms.value = rooms.sort((a, b) => b.updatedAt - a.updatedAt)
}

const cacheRoomCount = computed(() => cachedRooms.value.length)

const cacheSize = computed(() => {
  let total = 0
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    const value = localStorage.getItem(key || '')
    if (key?.startsWith('room_') && value) {
      total += value.length
    }
  }
  if (total < 1024) return `${total} B`
  if (total < 1024 * 1024) return `${(total / 1024).toFixed(1)} KB`
  return `${(total / (1024 * 1024)).toFixed(1)} MB`
})

function viewRoom(room: RoomCache) {
  viewingRoom.value = room
}

function handleDeleteRoom(roomId: string) {
  if (!confirm('确定要删除此房间缓存吗？此操作不可恢复。')) return

  try {
    localStorage.removeItem(`room_${roomId}`)
    loadCachedRooms()
    cacheMsg.value = '已删除房间缓存'
    cacheMsgType.value = 'success'
    if (viewingRoom.value?.id === roomId) {
      viewingRoom.value = null
    }
  } catch (e: any) {
    cacheMsg.value = '删除失败: ' + e.message
    cacheMsgType.value = 'error'
  }
}

function handleClearCache() {
  if (!confirm('确定要清理所有房间缓存吗？此操作不可恢复。')) return

  clearing.value = true
  cacheMsg.value = ''

  try {
    const keysToRemove: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith('room_')) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key))
    loadCachedRooms()
    viewingRoom.value = null
    cacheMsg.value = `已清理 ${keysToRemove.length} 个房间缓存`
    cacheMsgType.value = 'success'
  } catch (e: any) {
    cacheMsg.value = '清理失败: ' + e.message
    cacheMsgType.value = 'error'
  } finally {
    clearing.value = false
  }
}

function formatTime(ts: number): string {
  const d = new Date(ts)
  const Y = d.getFullYear()
  const M = String(d.getMonth() + 1).padStart(2, '0')
  const D = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${Y}-${M}-${D} ${h}:${m}`
}
</script>

<style scoped>
.settings-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.settings-panel {
  width: 560px;
  max-height: 85vh;
  background: #141a2e;
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.08);
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #e0f0ff;
  margin: 0;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e0f0ff;
}

.panel-tabs {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.08);
}

.panel-tab {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid rgba(0, 195, 255, 0.1);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.panel-tab:hover {
  border-color: rgba(0, 195, 255, 0.2);
  color: rgba(224, 240, 255, 0.8);
}

.panel-tab.active {
  background: rgba(0, 195, 255, 0.1);
  border-color: rgba(0, 195, 255, 0.3);
  color: #00c3ff;
}

.panel-body {
  padding: 20px;
  overflow-y: auto;
}

/* 账号设置 */
.account-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(224, 240, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-input {
  padding: 10px 14px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  color: #e0f0ff;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
}

.form-input:focus {
  border-color: rgba(0, 195, 255, 0.3);
  box-shadow: 0 0 12px rgba(0, 195, 255, 0.08);
}

.form-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.update-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #00c3ff, #0080ff);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
}

.update-btn:hover:not(:disabled) {
  box-shadow: 0 0 16px rgba(0, 195, 255, 0.3);
  transform: translateY(-1px);
}

.update-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 缓存管理 */
.cache-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.cache-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cache-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.08);
  border-radius: 12px;
}

.cache-info p {
  margin: 0;
  font-size: 13px;
  color: rgba(224, 240, 255, 0.6);
  line-height: 1.5;
}

.cache-stats {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: rgba(224, 240, 255, 0.8);
}

.cache-stats strong {
  color: #00c3ff;
}

.empty-rooms {
  text-align: center;
  padding: 32px;
  color: rgba(224, 240, 255, 0.4);
  font-size: 14px;
}

/* 房间列表 */
.room-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.room-card {
  padding: 12px 14px;
  background: rgba(0, 195, 255, 0.03);
  border: 1px solid rgba(0, 195, 255, 0.08);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.room-card:hover {
  background: rgba(0, 195, 255, 0.06);
  border-color: rgba(0, 195, 255, 0.2);
}

.room-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.room-card-title {
  font-size: 14px;
  font-weight: 600;
  color: #e0f0ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.room-card-actions {
  flex-shrink: 0;
  margin-left: 8px;
}

.room-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: rgba(224, 240, 255, 0.3);
  cursor: pointer;
  transition: all 0.2s ease;
}

.room-action-btn.delete:hover {
  color: #ff4d4d;
  background: rgba(255, 77, 77, 0.1);
  border-color: rgba(255, 77, 77, 0.2);
}

.room-card-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.4);
  margin-bottom: 6px;
}

.room-card-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.5);
  overflow: hidden;
}

.msg-role {
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.msg-role.user {
  background: rgba(0, 195, 255, 0.15);
  color: #00c3ff;
}

.msg-role.assistant {
  background: rgba(0, 200, 100, 0.15);
  color: #00c864;
}

.msg-preview {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clear-btn {
  padding: 10px 20px;
  background: rgba(255, 77, 77, 0.1);
  border: 1px solid rgba(255, 77, 77, 0.2);
  border-radius: 8px;
  color: #ff4d4d;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
}

.clear-btn:hover:not(:disabled) {
  background: rgba(255, 77, 77, 0.2);
  border-color: rgba(255, 77, 77, 0.4);
}

.clear-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 房间详情 */
.room-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.room-detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: rgba(0, 195, 255, 0.06);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-btn:hover {
  color: #00c3ff;
  border-color: rgba(0, 195, 255, 0.3);
}

.room-detail-title {
  font-size: 15px;
  font-weight: 600;
  color: #e0f0ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.room-detail-info {
  display: flex;
  gap: 16px;
  padding: 10px 14px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.08);
  border-radius: 8px;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.5);
}

.info-item {
  white-space: nowrap;
}

.room-messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  padding: 4px;
}

.message-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 14px;
  border-radius: 10px;
}

.message-item.user {
  background: rgba(0, 195, 255, 0.06);
  border: 1px solid rgba(0, 195, 255, 0.1);
}

.message-item.assistant {
  background: rgba(0, 200, 100, 0.06);
  border: 1px solid rgba(0, 200, 100, 0.1);
}

.message-role {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.message-item.user .message-role {
  color: #00c3ff;
}

.message-item.assistant .message-role {
  color: #00c864;
}

.message-content {
  font-size: 13px;
  color: rgba(224, 240, 255, 0.8);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-time {
  font-size: 11px;
  color: rgba(224, 240, 255, 0.3);
}

.delete-room-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 20px;
  background: rgba(255, 77, 77, 0.1);
  border: 1px solid rgba(255, 77, 77, 0.2);
  border-radius: 8px;
  color: #ff4d4d;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.delete-room-btn:hover {
  background: rgba(255, 77, 77, 0.2);
  border-color: rgba(255, 77, 77, 0.4);
}

/* 通用 */
.msg {
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 6px;
}

.msg.success {
  background: rgba(0, 200, 100, 0.1);
  border: 1px solid rgba(0, 200, 100, 0.2);
  color: #00c864;
}

.msg.error {
  background: rgba(255, 77, 77, 0.1);
  border: 1px solid rgba(255, 77, 77, 0.2);
  color: #ff4d4d;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 工具设置 */
.tools-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tools-info {
  padding: 14px 16px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.08);
  border-radius: 10px;
}

.tools-info p {
  margin: 0;
  font-size: 13px;
  color: rgba(224, 240, 255, 0.6);
  line-height: 1.5;
}

.tools-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  padding: 32px;
  color: rgba(224, 240, 255, 0.4);
  font-size: 14px;
}

.tools-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.tool-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  background: rgba(0, 195, 255, 0.03);
  border: 1px solid rgba(0, 195, 255, 0.08);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tool-toggle-row:hover {
  background: rgba(0, 195, 255, 0.06);
  border-color: rgba(0, 195, 255, 0.2);
}

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-size: 14px;
  font-weight: 600;
  color: #e0f0ff;
  margin-bottom: 4px;
}

.tool-desc {
  font-size: 12px;
  color: rgba(224, 240, 255, 0.5);
  line-height: 1.4;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
  margin-left: 12px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  bottom: 3px;
  background: #fff;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.toggle-switch input:checked + .toggle-slider {
  background: linear-gradient(135deg, #00c3ff, #0080ff);
}

.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(20px);
}

.toggle-switch input:disabled + .toggle-slider {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
