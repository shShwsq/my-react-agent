<template>
  <div class="home-container">
    <div class="home-bg-grid"></div>

    <header class="home-header">
      <div class="header-left">
        <div class="header-logo">
          <svg viewBox="0 0 32 32" fill="none" width="28" height="28">
            <rect x="2" y="2" width="28" height="28" rx="6" stroke="currentColor" stroke-width="2" />
            <path d="M10 16L14 20L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h1 class="header-title">Not Toy Anymore</h1>
      </div>
      <div class="header-right">
        <button class="config-btn" @click="showConfig = true">
          <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
            <path d="M10 13C11.6569 13 13 11.6569 13 10C13 8.34315 11.6569 7 10 7C8.34315 7 7 8.34315 7 10C7 11.6569 8.34315 13 10 13Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M16.18 12.82C16.06 13.24 16.12 13.69 16.36 14.06L16.42 14.16C16.61 14.49 16.67 14.88 16.57 15.25C16.48 15.62 16.24 15.93 15.91 16.12C15.58 16.31 15.19 16.37 14.82 16.28C14.45 16.18 14.14 15.94 13.95 15.61L13.89 15.51C13.65 15.14 13.26 14.89 12.82 14.82C12.39 14.75 11.95 14.85 11.6 15.11C11.25 15.37 11.02 15.77 10.97 16.21V16.36C10.97 17.27 10.24 18 9.33 18C8.42 18 7.69 17.27 7.69 16.36V16.28C7.63 15.83 7.39 15.43 7.02 15.18C6.65 14.93 6.19 14.85 5.76 14.97L5.64 15.01C5.27 15.13 4.87 15.09 4.53 14.9C4.19 14.71 3.94 14.39 3.83 14.01C3.72 13.63 3.76 13.23 3.95 12.89L4.01 12.79C4.21 12.42 4.25 11.98 4.12 11.58C3.99 11.18 3.7 10.85 3.32 10.67L3.21 10.62C2.38 10.24 2 9.27 2.36 8.43C2.72 7.59 3.69 7.19 4.53 7.54L4.64 7.59C5.02 7.76 5.46 7.75 5.83 7.56C6.2 7.37 6.47 7.03 6.58 6.63C6.69 6.23 6.62 5.8 6.4 5.45L6.34 5.35C6.15 5.01 6.1 4.61 6.21 4.24C6.32 3.87 6.57 3.56 6.91 3.37C7.25 3.18 7.65 3.13 8.02 3.24C8.39 3.35 8.7 3.6 8.89 3.94L8.95 4.04C9.19 4.41 9.58 4.66 10.02 4.73C10.45 4.8 10.89 4.7 11.24 4.44C11.59 4.18 11.82 3.78 11.87 3.34V3.19C11.87 2.28 12.6 1.55 13.51 1.55C14.42 1.55 15.15 2.28 15.15 3.19V3.27C15.21 3.72 15.45 4.12 15.82 4.37C16.19 4.62 16.65 4.7 17.08 4.58L17.2 4.54C17.57 4.42 17.97 4.46 18.31 4.65C18.65 4.84 18.9 5.16 19.01 5.54C19.12 5.92 19.08 6.32 18.89 6.66L18.83 6.76C18.63 7.13 18.59 7.57 18.72 7.97C18.85 8.37 19.14 8.7 19.52 8.88L19.63 8.93C20.46 9.31 20.84 10.28 20.48 11.12C20.12 11.96 19.15 12.36 18.31 12.01L18.2 11.96C17.82 11.79 17.38 11.8 17.01 11.99C16.64 12.18 16.37 12.52 16.26 12.92C16.18 13.24 16.18 13.54 16.18 12.82Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
          <span>模型配置</span>
        </button>
        <button class="rooms-btn" @click="showRooms = true" title="我的房间">
          <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
            <path d="M3 4C3 3.44772 3.44772 3 4 3H16C16.5523 3 17 3.44772 17 4V16C17 16.5523 16.5523 17 16 17H4C3.44772 17 3 16.5523 3 16V4Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M3 7H17" stroke="currentColor" stroke-width="1.5"/>
            <path d="M7 3V7" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span>我的房间</span>
        </button>
        <button class="settings-btn" @click="showSettings = true" title="设置">
          <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
            <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" stroke="currentColor" stroke-width="2"/>
            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <button class="logout-btn" @click="handleLogout" title="退出登录">
          <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
            <path d="M13 3H16C16.55 3 17 3.45 17 4V16C17 16.55 16.55 17 16 17H13M8 14L3 10M3 10L8 6M3 10H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </header>

    <div class="home-chat">
      <div class="input-box">
        <div class="footer-input">
          <ChatInput ref="chatInputRef" :sending="sending" @send="handleSend" />
        </div>
        <div class="footer-actions">
          <ModelSelector v-model:selectedModel="selectedModel" @update:subModels="subModels = $event" />
          <VoiceInput 
            :disabled="sending" 
            :config-id="asrConfigId"
            @result="handleVoiceResult" 
            @error="handleVoiceError" 
          />
          <button class="upload-btn" @click="chatInputRef?.triggerFileInput()" title="上传文件">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <button class="send-btn" @click="handleSendClick" :disabled="!canSend">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M5 12L3 20L21 12L3 4L5 12ZM5 12L13 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <ModelConfig :visible="showConfig" @close="showConfig = false" />
    <SettingsDialog :visible="showSettings" @close="showSettings = false" />
    <RoomsDialog :visible="showRooms" @close="showRooms = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useModelConfigStore } from '@/stores/modelConfig'
import ChatInput from '@/components/ChatInput.vue'
import ModelSelector from '@/components/ModelSelector.vue'
import ModelConfig from '@/components/ModelConfig.vue'
import SettingsDialog from '@/components/SettingsDialog.vue'
import RoomsDialog from '@/components/RoomsDialog.vue'
import VoiceInput from '@/components/VoiceInput.vue'
import { createRoomCache, saveRoomCache, RoomMessage } from '@/utils/roomCache'
import { createRoom, addMessage, uploadFile } from '@/api/room'

const router = useRouter()
const authStore = useAuthStore()
const modelConfigStore = useModelConfigStore()

const selectedModel = ref('')
const subModels = ref<Record<string, any>>({})
const sending = ref(false)
const showConfig = ref(false)
const showSettings = ref(false)
const showRooms = ref(false)
const chatInputRef = ref<InstanceType<typeof ChatInput>>()

const canSend = computed(() => {
  const text = chatInputRef.value?.inputText?.trim() || ''
  const files = chatInputRef.value?.selectedFiles?.length || 0
  return (text.length > 0 || files > 0) && !sending.value && selectedModel.value.length > 0
})

const asrConfigId = computed(() => {
  if (subModels.value['voice_asr']) {
    return Number(subModels.value['voice_asr'])
  }
  const asrConfigs = modelConfigStore.getConfigsByCategory('voice', 'asr')
  if (asrConfigs.length === 0) return null
  const defaultConfig = asrConfigs.find(c => c.is_default)
  return defaultConfig ? defaultConfig.id ?? null : asrConfigs[0].id ?? null
})

function handleVoiceResult(text: string) {
  if (chatInputRef.value) {
    const currentText = chatInputRef.value.inputText || ''
    chatInputRef.value.inputText = currentText + (currentText && !currentText.endsWith(' ') && !currentText.endsWith('\n') ? ' ' : '') + text
  }
}

function handleVoiceError(message: string) {
  console.error('Voice input error:', message)
}

function setDefaultModel() {
  if (selectedModel.value) return
  const defaultConfig = modelConfigStore.getDefaultConfig('text')
  if (defaultConfig) {
    selectedModel.value = String(defaultConfig.id)
  } else if (modelConfigStore.textConfigs.length > 0) {
    selectedModel.value = String(modelConfigStore.textConfigs[0].id)
  }
}

watch(() => modelConfigStore.textConfigs, setDefaultModel, { immediate: true })

function handleSendClick() {
  if (chatInputRef.value) {
    chatInputRef.value.handleSend()
  }
}

function generateRoomId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

function buildModelsData(): Record<string, any> {
  const models: Record<string, any> = { text: selectedModel.value }
  
  for (const [key, modelId] of Object.entries(subModels.value)) {
    const parts = key.split('_')
    if (parts.length === 2) {
      const [category, subCategory] = parts
      if (!models[category]) {
        models[category] = {}
      }
      models[category][subCategory] = modelId
    } else {
      models[key] = modelId
    }
  }
  
  return models
}

async function handleSend(content: string, files?: File[]) {
  const roomId = generateRoomId()
  const models = buildModelsData()
  
  // 创建房间缓存
  const title = content.length > 30 ? content.slice(0, 30) + '...' : content
  const room = createRoomCache(roomId, models, title)
  
  // 构建显示内容（包含文件信息）
  let displayContent = content
  if (files && files.length > 0) {
    const fileInfo = files.map(f => f.name).join(', ')
    displayContent = content ? `${content}\n[附件: ${fileInfo}]` : `[附件: ${fileInfo}]`
  }
  
  // 添加用户消息
  const userMessage: RoomMessage = {
    id: `msg_${Date.now()}`,
    role: 'user',
    content: displayContent,
    timestamp: Date.now()
  }
  room.messages.push(userMessage)
  
  // 保存到 localStorage
  saveRoomCache(room)
  
  // 保存到数据库
  try {
    await createRoom({ id: roomId, title, models })
    await addMessage(roomId, { role: 'user', content: displayContent })
    
    // 上传文件
    if (files && files.length > 0) {
      for (const file of files) {
        try {
          await uploadFile(roomId, file)
        } catch (e) {
          console.error('Failed to upload file:', file.name, e)
        }
      }
    }
  } catch (e) {
    console.error('Failed to save room to database:', e)
  }
  
  // 跳转到房间页面
  router.push({
    path: `/room/${roomId}`
  })
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
  } else {
    await authStore.fetchUserInfo()
    await modelConfigStore.loadConfigs()
  }
})
</script>

<style scoped>
.home-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0a0e1a;
  position: relative;
  overflow: hidden;
}

.home-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 195, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 195, 255, 0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
}

.home-header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: rgba(10, 14, 26, 0.8);
  border-bottom: 1px solid rgba(0, 195, 255, 0.08);
  backdrop-filter: blur(12px);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-logo {
  color: #00c3ff;
}

.header-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 4px;
  color: #e0f0ff;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(0, 195, 255, 0.06);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.config-btn:hover {
  border-color: rgba(0, 195, 255, 0.3);
  color: #00c3ff;
}

.rooms-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(0, 195, 255, 0.06);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.rooms-btn:hover {
  border-color: rgba(0, 195, 255, 0.3);
  color: #00c3ff;
}

.logout-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid rgba(255, 77, 106, 0.15);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.4);
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  color: #ff4d6a;
  border-color: rgba(255, 77, 106, 0.3);
}

.settings-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.4);
  cursor: pointer;
  transition: all 0.2s ease;
}

.settings-btn:hover {
  color: #00c3ff;
  border-color: rgba(0, 195, 255, 0.3);
}

.home-chat {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  padding: 0 24px;
  display: flex;
  justify-content: center;
}

.input-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 12px;
  padding: 12px 16px;
  transition: all 0.3s ease;
  max-width: 800px;
  width: 100%;
}

.input-box:focus-within {
  border-color: rgba(0, 195, 255, 0.35);
  box-shadow: 0 0 20px rgba(0, 195, 255, 0.08);
}

.footer-input {
  width: 100%;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-actions :first-child {
  margin-right: auto;
}

.send-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #00c3ff, #0080ff);
  border: none;
  border-radius: 10px;
  color: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 0;
}

.upload-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 195, 255, 0.06);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 10px;
  color: rgba(224, 240, 255, 0.4);
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0;
}

.upload-btn:hover {
  color: #00c3ff;
  border-color: rgba(0, 195, 255, 0.3);
  background: rgba(0, 195, 255, 0.1);
}

.send-btn:hover:not(:disabled) {
  box-shadow: 0 0 16px rgba(0, 195, 255, 0.3);
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-btn svg,
.upload-btn svg {
  width: 20px;
  height: 20px;
  display: block;
  flex-shrink: 0;
  margin: 0 auto;
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
</style>
