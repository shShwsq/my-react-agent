<template>
  <button
    class="voice-input-btn"
    :class="{ recording: isRecording, processing: isProcessing }"
    @click="handleClick"
    :disabled="disabled || isProcessing"
    :title="buttonTitle"
  >
    <div v-if="isRecording" class="recording-animation">
      <div class="sound-wave">
        <span class="wave-bar"></span>
        <span class="wave-bar"></span>
        <span class="wave-bar"></span>
        <span class="wave-bar"></span>
        <span class="wave-bar"></span>
      </div>
      <span class="recording-time">{{ formatTime(recordingTime) }}</span>
    </div>
    <svg v-else-if="isProcessing" viewBox="0 0 24 24" fill="none" width="20" height="20" class="processing-icon">
      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-dasharray="31.4" stroke-dashoffset="0">
        <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
      </circle>
    </svg>
    <svg v-else viewBox="0 0 24 24" fill="none" width="20" height="20">
      <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M19 10v2a7 7 0 01-14 0v-2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="12" y1="19" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="8" y1="23" x2="16" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </button>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useModelConfigStore } from '@/stores/modelConfig'
import axios from 'axios'

const props = defineProps<{
  disabled?: boolean
  configId?: number | null
}>()

const emit = defineEmits<{
  result: [text: string]
  error: [message: string]
}>()

const modelConfigStore = useModelConfigStore()

const isRecording = ref(false)
const isProcessing = ref(false)
const recordingTime = ref(0)
const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])
const recordingTimer = ref<number | null>(null)

const buttonTitle = computed(() => {
  if (isProcessing.value) return '处理中...'
  if (isRecording.value) return '点击停止录音'
  return '语音输入'
})

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function getASRConfigId(): number | null {
  if (props.configId) return props.configId
  
  const asrConfigs = modelConfigStore.getConfigsByCategory('voice', 'asr')
  if (asrConfigs.length === 0) return null
  
  const defaultConfig = asrConfigs.find(c => c.is_default)
  return defaultConfig ? defaultConfig.id ?? null : asrConfigs[0].id ?? null
}

async function handleClick() {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    
    mediaRecorder.value = new MediaRecorder(stream, { mimeType: 'audio/webm' })
    audioChunks.value = []
    
    mediaRecorder.value.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunks.value.push(e.data)
      }
    }
    
    mediaRecorder.value.onstop = async () => {
      stream.getTracks().forEach(track => track.stop())
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
      await processAudio(audioBlob)
    }
    
    mediaRecorder.value.start()
    isRecording.value = true
    recordingTime.value = 0
    
    recordingTimer.value = window.setInterval(() => {
      recordingTime.value++
      if (recordingTime.value >= 60) {
        stopRecording()
      }
    }, 1000)
  } catch (e) {
    console.error('Failed to start recording:', e)
    emit('error', '无法访问麦克风，请检查权限设置')
  }
}

function stopRecording() {
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
  }
  
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    isRecording.value = false
  }
}

async function processAudio(audioBlob: Blob) {
  const configId = getASRConfigId()
  
  if (!configId) {
    await useNativeSpeechRecognition(audioBlob)
    return
  }
  
  isProcessing.value = true
  
  try {
    const reader = new FileReader()
    reader.readAsDataURL(audioBlob)
    
    await new Promise<void>((resolve) => {
      reader.onload = () => resolve()
    })
    
    const audioData = reader.result as string
    
    const response = await axios.post('/api/voice/asr', {
      audio_data: audioData,
      config_id: configId,
      stream: false,
      audio_format: 'webm',
    })
    
    const result = response.data
    const text = result.d?.content || result.d?.text || ''
    
    if (text) {
      emit('result', text)
    } else {
      emit('error', '未识别到语音内容')
    }
  } catch (e) {
    console.error('ASR error:', e)
    let errorMessage = '语音识别失败'
    
    if (axios.isAxiosError(e)) {
      const errorData = e.response?.data
      if (errorData?.m) {
        errorMessage = errorData.m
      } else if (errorData?.detail) {
        errorMessage = errorData.detail
      } else if (e.response?.status === 400) {
        errorMessage = '请求参数错误，请检查语音识别模型配置'
      }
    } else if (e instanceof Error) {
      errorMessage = e.message
    }
    
    emit('error', errorMessage)
  } finally {
    isProcessing.value = false
  }
}

async function useNativeSpeechRecognition(audioBlob: Blob) {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    emit('error', '浏览器不支持语音识别，请配置语音识别模型')
    return
  }
  
  isProcessing.value = true
  
  try {
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
    const recognition = new SpeechRecognition()
    
    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = 'zh-CN'
    
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      if (transcript) {
        emit('result', transcript)
      } else {
        emit('error', '未识别到语音内容')
      }
      isProcessing.value = false
    }
    
    recognition.onerror = (event: any) => {
      console.error('Native speech recognition error:', event.error)
      emit('error', `语音识别失败: ${event.error}`)
      isProcessing.value = false
    }
    
    recognition.onend = () => {
      isProcessing.value = false
    }
    
    recognition.start()
  } catch (e) {
    console.error('Native speech recognition error:', e)
    emit('error', '浏览器语音识别失败，请配置语音识别模型')
    isProcessing.value = false
  }
}

onUnmounted(() => {
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
  }
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
  }
})
</script>

<style scoped>
.voice-input-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 36px;
  height: 36px;
  background: rgba(0, 195, 255, 0.08);
  border: 1px solid rgba(0, 195, 255, 0.2);
  border-radius: 10px;
  color: #00c3ff;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0;
  position: relative;
  overflow: hidden;
}

.voice-input-btn:hover:not(:disabled) {
  background: rgba(0, 195, 255, 0.15);
  border-color: rgba(0, 195, 255, 0.4);
  transform: scale(1.05);
}

.voice-input-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.voice-input-btn.recording {
  width: 80px;
  height: 36px;
  background: rgba(255, 77, 106, 0.2);
  border-color: rgba(255, 77, 106, 0.5);
  color: #ff4d6a;
  border-radius: 18px;
  animation: recording-glow 1.5s ease-in-out infinite;
}

.voice-input-btn.processing {
  background: rgba(255, 193, 7, 0.15);
  border-color: rgba(255, 193, 7, 0.4);
  color: #ffc107;
}

.voice-input-btn svg {
  width: 22px;
  height: 22px;
  display: block;
  flex-shrink: 0;
  margin: 0 auto;
}

.recording-animation {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 100%;
}

.sound-wave {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: 24px;
}

.wave-bar {
  width: 3px;
  height: 8px;
  background: #ff4d6a;
  border-radius: 2px;
  animation: wave 0.5s ease-in-out infinite;
}

.wave-bar:nth-child(1) {
  animation-delay: 0s;
}

.wave-bar:nth-child(2) {
  animation-delay: 0.1s;
}

.wave-bar:nth-child(3) {
  animation-delay: 0.2s;
}

.wave-bar:nth-child(4) {
  animation-delay: 0.3s;
}

.wave-bar:nth-child(5) {
  animation-delay: 0.4s;
}

@keyframes wave {
  0%, 100% {
    height: 8px;
  }
  50% {
    height: 20px;
  }
}

@keyframes recording-glow {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 77, 106, 0.4);
  }
  50% {
    box-shadow: 0 0 20px 4px rgba(255, 77, 106, 0.3);
  }
}

.recording-time {
  font-size: 13px;
  font-weight: 600;
  min-width: 36px;
  color: #ff4d6a;
  letter-spacing: 0.5px;
}
</style>
