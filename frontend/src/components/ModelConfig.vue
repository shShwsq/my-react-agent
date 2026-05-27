<template>
  <div class="model-config-overlay" v-if="visible" @click.self="$emit('close')">
    <div class="model-config-panel">
      <div class="panel-header">
        <h2 class="panel-title">模型配置</h2>
        <button class="close-btn" @click="$emit('close')">
          <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="panel-tabs">
        <button
          v-for="(info, key) in categories"
          :key="key"
          :class="['panel-tab', { active: activeTab === key }]"
          @click="activeTab = key as string"
        >
          {{ info.label }}
        </button>
      </div>

      <div class="panel-body">
        <div v-if="subCategoryOptions.length > 0" class="sub-category-filter">
          <button
            v-for="opt in subCategoryOptions"
            :key="opt.value"
            :class="['sub-tab', { active: activeSubCategory === opt.value }]"
            @click="activeSubCategory = opt.value"
          >
            {{ opt.label }}
          </button>
        </div>

        <div v-if="filteredConfigs.length === 0" class="empty-state">
          <p>暂无配置，点击下方按钮添加</p>
        </div>

        <div v-for="config in filteredConfigs" :key="config.id" class="config-card">
          <div class="config-header">
            <div class="config-name">{{ config.model_name }}</div>
            <div class="config-actions">
              <button class="action-btn test" @click="handleTest(config)" :disabled="testingId === config.id" title="测试连接">
                <svg v-if="testingId !== config.id" viewBox="0 0 16 16" fill="none" width="14" height="14">
                  <path d="M2 8L6 12L14 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span v-else class="btn-spinner"></span>
              </button>
              <button class="action-btn" @click="editConfig(config)" title="编辑">
                <svg viewBox="0 0 16 16" fill="none" width="14" height="14">
                  <path d="M11.5 1.5L14.5 4.5L5 14H2V11L11.5 1.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <button class="action-btn danger" @click="handleDelete(config.id!)" title="删除">
                <svg viewBox="0 0 16 16" fill="none" width="14" height="14">
                  <path d="M2 4H14M5.33 4V2.67C5.33 2.3 5.63 2 6 2H10C10.37 2 10.67 2.3 10.67 2.67V4M12.67 4V13.33C12.67 13.7 12.37 14 12 14H4C3.63 14 3.33 13.7 3.33 13.33V4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="config-meta">
            <span class="config-provider">{{ providerLabel(config.provider) }}</span>
            <span class="config-api-type">{{ callMethodLabel(config.call_method) }}</span>
            <span v-if="config.sub_category" class="sub-category-badge">{{ subCategoryLabel(config.sub_category) }}</span>
            <span v-if="config.is_default" class="default-badge">默认</span>
            <span v-if="config.is_public" class="public-badge">公开</span>
          </div>
          <div v-if="testResults[config.id!]" :class="['test-result', testResults[config.id!].success ? 'success' : 'error']">
            {{ testResults[config.id!].message }}
          </div>
        </div>
      </div>

      <div class="panel-footer">
        <button class="add-btn" @click="showAddForm = true">
          <svg viewBox="0 0 16 16" fill="none" width="14" height="14">
            <path d="M8 3V13M3 8H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          添加配置
        </button>
      </div>

      <div v-if="showAddForm" class="form-overlay" @click.self="showAddForm = false">
        <div class="form-card">
          <h3 class="form-title">{{ editingConfig ? '编辑配置' : '添加配置' }}</h3>
          <div v-if="currentSubCategories" class="form-group">
            <label>子分类</label>
            <select v-model="form.sub_category" class="form-select">
              <option v-for="(label, key) in currentSubCategories" :key="key" :value="key">{{ label }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group half">
              <label>服务商</label>
              <select v-model="form.provider" class="form-select">
                <option value="aliyun">阿里云</option>
              </select>
            </div>
            <div class="form-group half">
              <label>调用方法</label>
              <select v-model="form.call_method" class="form-select">
                <option v-for="opt in callMethodOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>模型名称</label>
            <select v-model="form.model_name" class="form-select">
              <option value="" disabled>请选择模型</option>
              <option v-for="name in modelNameOptions" :key="name" :value="name">{{ name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>API Key</label>
            <input v-model="form.api_key" type="password" class="form-input" :placeholder="editingConfig?.has_api_key ? '留空保持原 API Key 不变' : 'sk-...'" />
            <div v-if="editingConfig?.has_api_key && !form.api_key" class="api-key-hint">已配置 API Key，留空则保持不变</div>
          </div>
          <div class="form-group">
            <label>Base URL <span class="optional-hint">(选填)</span></label>
            <input v-model="form.base_url" class="form-input" placeholder="留空使用默认地址" />
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="form.is_default" type="checkbox" />
              <span>设为默认</span>
            </label>
          </div>
          <div v-if="isSuper" class="form-group">
            <label class="checkbox-label">
              <input v-model="form.is_public" type="checkbox" />
              <span>公开此配置（所有用户可见）</span>
            </label>
          </div>
          <div class="form-actions">
            <button class="cancel-btn" @click="resetForm">取消</button>
            <button class="save-btn" @click="handleSave">保存</button>
          </div>
        </div>
      </div>

      <div v-if="showTestModal" class="test-modal-overlay" @click.self="closeTestModal">
        <div class="test-modal-card test-input-modal">
          <div class="test-modal-header">
            <h3 class="test-modal-title">模型测试</h3>
            <button class="test-modal-close" @click="closeTestModal">
              <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
                <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
          <div class="test-modal-body">
            <div class="test-modal-row">
              <span class="test-modal-label">模型</span>
              <span class="test-modal-value">{{ testingConfig?.model_name }}</span>
            </div>

            <div v-if="canUseStreamMode()" class="test-modal-row">
              <span class="test-modal-label">测试模式</span>
              <div class="stream-mode-toggle">
                <button 
                  :class="['mode-btn', { active: !testStreamMode }]" 
                  @click="testStreamMode = false"
                >非流式</button>
                <button 
                  :class="['mode-btn', { active: testStreamMode }]" 
                  @click="testStreamMode = true"
                >流式</button>
              </div>
            </div>

            <template v-if="!isTesting && !testResult">
              <div v-if="getTestInputType() === 'text'" class="test-modal-row">
                <span class="test-modal-label">输入文本</span>
                <textarea v-model="testInputText" class="test-textarea" placeholder="请输入测试文本..."></textarea>
              </div>

              <div v-if="getTestInputType() === 'audio'" class="test-modal-row">
                <span class="test-modal-label">音频输入</span>
                <div class="audio-input-section">
                  <div class="audio-buttons">
                    <button 
                      :class="['record-btn', { recording: isRecording }]" 
                      @click="isRecording ? stopRecording() : startRecording()"
                    >
                      <svg v-if="!isRecording" viewBox="0 0 24 24" fill="none" width="16" height="16">
                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" fill="currentColor"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        <line x1="12" y1="19" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      </svg>
                      <span v-else class="recording-indicator"></span>
                      {{ isRecording ? '停止录音 (最多5秒)' : '开始录音' }}
                    </button>
                    <label class="upload-btn">
                      <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      上传音频
                      <input type="file" accept="audio/*" @change="handleAudioUpload" hidden />
                    </label>
                    <button class="default-btn" @click="useDefaultAudio">
                      <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      </svg>
                      使用默认
                    </button>
                  </div>
                  <div v-if="testInputAudioBase64" class="audio-status">
                    <span class="status-icon">✓</span> 已准备音频数据
                  </div>
                </div>
              </div>

              <div v-if="getTestInputType() === 'image'" class="test-modal-row">
                <span class="test-modal-label">图片输入</span>
                <div class="image-input-section">
                  <div class="image-buttons">
                    <label class="upload-btn">
                      <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      上传图片
                      <input type="file" accept="image/*" @change="handleImageUpload" hidden />
                    </label>
                    <button class="default-btn" @click="useDefaultImage">
                      <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
                        <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
                        <path d="M21 15l-5-5L5 21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      使用默认
                    </button>
                  </div>
                  <div v-if="testInputImageUrl" class="image-preview">
                    <img :src="testInputImageUrl" alt="预览图片" />
                  </div>
                </div>
              </div>

              <div v-if="getTestInputType() === 'image'" class="test-modal-row">
                <span class="test-modal-label">问题文本</span>
                <textarea v-model="testInputText" class="test-textarea" placeholder="请输入关于图片的问题..."></textarea>
              </div>
            </template>

            <div v-if="isTesting" class="test-progress-section">
              <div class="test-progress-spinner"></div>
              <div class="test-progress-text">正在测试连接...</div>
              <div v-if="playerStatus !== 'idle' && playerStatus !== 'completed'" class="player-status">
                <span :class="['status-indicator', playerStatus]"></span>
                <span class="status-text">{{ playerStatus === 'connecting' ? '正在连接音频流...' : '正在实时播放音频...' }}</span>
              </div>
              <div v-if="testStreamMode && streamingContent" class="streaming-content">
                <div class="streaming-label">实时响应：</div>
                <div class="streaming-text">{{ streamingContent }}</div>
              </div>
            </div>

            <template v-if="testResult && !isTesting">
              <div class="test-divider"></div>
              <div class="test-modal-row">
                <span class="test-modal-label">测试状态</span>
                <span :class="['test-modal-status', testResult.success ? 'success' : 'error']">
                  {{ testResult.success ? '成功' : '失败' }}
                </span>
              </div>
              <div v-if="testResult.responseTime" class="test-modal-row">
                <span class="test-modal-label">响应时间</span>
                <span class="test-modal-value">{{ testResult.responseTime }} ms</span>
              </div>
              <div v-if="testResult.responseContent" class="test-modal-row">
                <span class="test-modal-label">响应内容</span>
                <div v-if="testingConfig?.sub_category === 'image_generation' && testResult.responseContent.startsWith('http')" class="test-image-result">
                  <img :src="testResult.responseContent" alt="生成的图片" class="test-image-preview" />
                  <a :href="testResult.responseContent" target="_blank" class="test-image-link">{{ testResult.responseContent }}</a>
                </div>
                <div v-else class="test-modal-content">{{ testResult.responseContent }}</div>
              </div>
              <div v-if="testResult.audioUrl" class="test-modal-row">
                <span class="test-modal-label">音频播放</span>
                <audio :src="testResult.audioUrl" controls class="test-audio-player"></audio>
              </div>
              <div v-if="!testResult.success" class="test-modal-row">
                <span class="test-modal-label">错误信息</span>
                <div class="test-modal-error">{{ testResult.message }}</div>
              </div>
            </template>
          </div>
          <div class="test-modal-footer">
            <template v-if="!isTesting && !testResult">
              <button class="test-modal-btn secondary" @click="closeTestModal">取消</button>
              <button class="test-modal-btn primary" @click="executeTest">开始测试</button>
            </template>
            <template v-if="testResult && !isTesting">
              <button class="test-modal-btn secondary" @click="resetTestResult">重新测试</button>
              <button class="test-modal-btn primary" @click="closeTestModal">关闭</button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useModelConfigStore } from '@/stores/modelConfig'
import { useAuthStore } from '@/stores/auth'
import type { ModelConfigData, ModelCategory } from '@/api/modelConfig'
import { fetchModelCategories, fetchCallMethods as fetchCallMethodsApi, fetchModelNames as fetchModelNamesApi } from '@/api/modelConfig'
import { testModelConnection, type TestResult } from '@/api/modelTest'
import { testModelConnectionStream, testTTSModelStreamWithPlayback, type StreamTestResult } from '@/api/modelStreamTest'
import { StreamingAudioPlayer, type StreamingPlayerStatus } from '@/api/streamingAudioPlayer'

defineProps<{ visible: boolean }>()
defineEmits<{ close: [] }>()

const modelConfigStore = useModelConfigStore()
const authStore = useAuthStore()

const categories = ref<Record<string, ModelCategory>>({})
const activeTab = ref('text')
const activeSubCategory = ref<string | null>(null)
const showAddForm = ref(false)
const editingConfig = ref<ModelConfigData | null>(null)
const testingId = ref<number | null>(null)
const testResults = ref<Record<number, { success: boolean; message: string }>>({})

const showTestModal = ref(false)
const isTesting = ref(false)
const testResult = ref<TestResult | null>(null)
const testingConfig = ref<ModelConfigData | null>(null)
const testInputText = ref('')
const testInputAudioBase64 = ref('')
const testInputImageBase64 = ref('')
const testInputImageUrl = ref('')
const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordedChunks = ref<Blob[]>([])
const testStreamMode = ref(false)
const streamingContent = ref('')
const currentPlayer = ref<StreamingAudioPlayer | null>(null)
const playerStatus = ref<StreamingPlayerStatus>('idle')

const DEFAULT_TEST_TEXT = '你好，请简单介绍一下你自己。'
const DEFAULT_TEST_AUDIO_URL = 'https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3'
const DEFAULT_TEST_IMAGE_URL = 'https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg'

const isSuper = computed(() => authStore.isSuper)

const providerLabels: Record<string, string> = {
  aliyun: '阿里云',
}

function providerLabel(provider: string): string {
  return providerLabels[provider] || provider
}

const callMethodOptions = ref<{ value: string; label: string }[]>([])
const allCallMethodLabels = ref<Record<string, string>>({})
const modelNameOptions = ref<string[]>([])

async function fetchCallMethods() {
  try {
    const data = await fetchCallMethodsApi(form.value.category, form.value.provider, form.value.sub_category)
    callMethodOptions.value = data
    data.forEach((item) => {
      allCallMethodLabels.value[item.value] = item.label
    })
    if (callMethodOptions.value.length > 0 && !callMethodOptions.value.find(t => t.value === form.value.call_method)) {
      form.value.call_method = callMethodOptions.value[0].value
    }
  } catch {
    callMethodOptions.value = []
  }
}

async function fetchModelNames() {
  try {
    const data = await fetchModelNamesApi(form.value.category, form.value.provider, form.value.call_method, form.value.sub_category)
    modelNameOptions.value = data
    if (modelNameOptions.value.length > 0 && !modelNameOptions.value.includes(form.value.model_name)) {
      form.value.model_name = modelNameOptions.value[0]
    }
  } catch {
    modelNameOptions.value = []
  }
}

function callMethodLabel(callMethod: string): string {
  return allCallMethodLabels.value[callMethod] || callMethod
}

function subCategoryLabel(subCategory: string): string {
  const cat = categories.value[activeTab.value]
  if (cat?.sub_categories) {
    return cat.sub_categories[subCategory] || subCategory
  }
  return subCategory
}

const currentSubCategories = computed(() => {
  const cat = categories.value[activeTab.value]
  return cat?.sub_categories || null
})

const subCategoryOptions = computed(() => {
  const cat = categories.value[activeTab.value]
  if (!cat?.sub_categories) return []
  return Object.entries(cat.sub_categories).map(([value, label]) => ({ value, label }))
})

const form = ref<ModelConfigData>({
  category: 'text',
  sub_category: undefined,
  model_name: '',
  provider: 'aliyun',
  call_method: 'chat',
  api_key: '',
  base_url: '',
  is_default: false,
  is_public: false,
})

watch([() => form.value.provider, () => form.value.category, () => form.value.sub_category], () => {
  fetchCallMethods()
}, { immediate: true })

watch([() => form.value.call_method, () => form.value.provider, () => form.value.category, () => form.value.sub_category], () => {
  fetchModelNames()
}, { immediate: true })

const configs = computed(() => modelConfigStore.configs)

const filteredConfigs = computed(() => {
  let result = configs.value.filter((c) => c.category === activeTab.value)
  if (activeSubCategory.value) {
    result = result.filter((c) => c.sub_category === activeSubCategory.value)
  }
  return result
})

function editConfig(config: ModelConfigData) {
  editingConfig.value = config
  form.value = { ...config, sub_category: config.sub_category || undefined }
  showAddForm.value = true
  fetchModelNames()
}

function resetForm() {
  editingConfig.value = null
  const subCat = currentSubCategories.value ? Object.keys(currentSubCategories.value)[0] : undefined
  form.value = {
    category: activeTab.value,
    sub_category: subCat,
    model_name: '',
    provider: 'aliyun',
    call_method: 'chat',
    api_key: '',
    base_url: '',
    is_default: false,
    is_public: false,
  }
  showAddForm.value = false
}

async function handleSave() {
  form.value.category = activeTab.value
  if (!currentSubCategories.value) {
    form.value.sub_category = undefined
  }
  try {
    if (editingConfig.value?.id) {
      await modelConfigStore.editConfig(editingConfig.value.id, form.value)
    } else {
      await modelConfigStore.addConfig(form.value)
    }
    resetForm()
  } catch { /* empty */ }
}

async function handleDelete(id: number) {
  try {
    await modelConfigStore.removeConfig(id)
    delete testResults.value[id]
  } catch { /* empty */ }
}

async function handleTest(config: ModelConfigData) {
  if (!config.id) return

  testingConfig.value = config
  testInputText.value = DEFAULT_TEST_TEXT
  testInputAudioBase64.value = ''
  testInputImageBase64.value = ''
  testInputImageUrl.value = ''
  testResult.value = null
  showTestModal.value = true
}

function closeTestModal() {
  if (isRecording.value) {
    stopRecording()
  }

  if (testResult.value?.audioUrl) {
    URL.revokeObjectURL(testResult.value.audioUrl)
  }
  if (currentPlayer.value) {
    currentPlayer.value.stop()
    currentPlayer.value = null
  }
  playerStatus.value = 'idle'
  showTestModal.value = false
  isTesting.value = false
  testResult.value = null
}

function resetTestResult() {
  if (testResult.value?.audioUrl) {
    URL.revokeObjectURL(testResult.value.audioUrl)
  }
  if (currentPlayer.value) {
    currentPlayer.value.stop()
    currentPlayer.value = null
  }
  playerStatus.value = 'idle'
  testResult.value = null
}

function getTestInputType(): 'text' | 'audio' | 'image' {
  if (!testingConfig.value) return 'text'
  const { category, sub_category } = testingConfig.value
  if (category === 'voice' && sub_category === 'asr') return 'audio'
  if (category === 'vision' && sub_category === 'image_understanding') return 'image'
  return 'text'
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.value = new MediaRecorder(stream)
    recordedChunks.value = []

    mediaRecorder.value.ondataavailable = (e) => {
      if (e.data.size > 0) {
        recordedChunks.value.push(e.data)
      }
    }

    mediaRecorder.value.start()
    isRecording.value = true

    setTimeout(() => {
      if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
        stopRecording()
      }
    }, 5000)
  } catch (err) {
    console.error('无法访问麦克风:', err)
    alert('无法访问麦克风，请检查权限设置')
  }
}

function stopRecording(): Promise<void> {
  return new Promise((resolve) => {
    if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
      const recorder = mediaRecorder.value
      const stream = recorder.stream
      
      recorder.onstop = async () => {
        const blob = new Blob(recordedChunks.value, { type: 'audio/webm' })
        const arrayBuffer = await blob.arrayBuffer()
        const uint8Array = new Uint8Array(arrayBuffer)
        let binary = ''
        for (let i = 0; i < uint8Array.length; i++) {
          binary += String.fromCharCode(uint8Array[i])
        }
        testInputAudioBase64.value = btoa(binary)
        stream.getTracks().forEach(track => track.stop())
        resolve()
      }
      
      recorder.stop()
      isRecording.value = false
    } else {
      resolve()
    }
  })
}

function handleAudioUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    const arrayBuffer = reader.result as ArrayBuffer
    const uint8Array = new Uint8Array(arrayBuffer)
    let binary = ''
    for (let i = 0; i < uint8Array.length; i++) {
      binary += String.fromCharCode(uint8Array[i])
    }
    testInputAudioBase64.value = btoa(binary)
  }
  reader.readAsArrayBuffer(file)
}

function handleImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    const result = reader.result as string
    const base64 = result.split(',')[1]
    testInputImageBase64.value = base64
    testInputImageUrl.value = result
  }
  reader.readAsDataURL(file)
}

function useDefaultAudio() {
  testInputAudioBase64.value = DEFAULT_TEST_AUDIO_URL
}

function useDefaultImage() {
  testInputImageBase64.value = ''
  testInputImageUrl.value = DEFAULT_TEST_IMAGE_URL
}

function canUseStreamMode(): boolean {
  if (!testingConfig.value) return false
  const { category, sub_category, call_method } = testingConfig.value
  if (category === 'voice' && sub_category === 'asr' && call_method === 'dashscope') {
    return false
  }
  return category === 'text' || 
         (category === 'voice' && (sub_category === 'tts' || sub_category === 'asr')) ||
         (category === 'vision' && sub_category === 'image_understanding')
}

async function executeTest() {
  if (!testingConfig.value?.id) return

  if (isRecording.value) {
    await stopRecording()
  }

  isTesting.value = true
  testingId.value = testingConfig.value.id
  testResults.value[testingConfig.value.id] = null as any
  streamingContent.value = ''
  playerStatus.value = 'idle'

  const inputType = getTestInputType()
  const audioData = inputType === 'audio' ? (testInputAudioBase64.value || DEFAULT_TEST_AUDIO_URL) : undefined
  const imageData = inputType === 'image' ? testInputImageBase64.value : undefined
  const textData = testInputText.value || DEFAULT_TEST_TEXT

  const isTTSStream = testStreamMode.value && 
                      testingConfig.value.category === 'voice' && 
                      testingConfig.value.sub_category === 'tts'

  if (isTTSStream) {
    const result = await testTTSModelStreamWithPlayback(
      {
        configId: testingConfig.value.id,
        model: testingConfig.value.model_name,
        provider: testingConfig.value.provider,
        callMethod: testingConfig.value.call_method,
        category: testingConfig.value.category,
        subCategory: testingConfig.value.sub_category,
        baseUrl: testingConfig.value.base_url,
        customText: textData,
      },
      (status) => {
        playerStatus.value = status
      }
    )

    if (result.player) {
      currentPlayer.value = result.player
    }

    testResults.value[testingConfig.value.id] = result
    testResult.value = result as any
  } else if (testStreamMode.value && canUseStreamMode()) {
    const result = await testModelConnectionStream({
      configId: testingConfig.value.id,
      model: testingConfig.value.model_name,
      provider: testingConfig.value.provider,
      callMethod: testingConfig.value.call_method,
      category: testingConfig.value.category,
      subCategory: testingConfig.value.sub_category,
      baseUrl: testingConfig.value.base_url,
      customText: textData,
      customAudioBase64: audioData,
      customImageBase64: imageData,
      onChunk: (chunk) => {
        streamingContent.value += chunk
      },
    })

    testResults.value[testingConfig.value.id] = result
    testResult.value = result as any
  } else {
    const result = await testModelConnection({
      configId: testingConfig.value.id,
      model: testingConfig.value.model_name,
      provider: testingConfig.value.provider,
      callMethod: testingConfig.value.call_method as any,
      category: testingConfig.value.category,
      subCategory: testingConfig.value.sub_category,
      baseUrl: testingConfig.value.base_url,
      customText: textData,
      customAudioBase64: audioData,
      customImageBase64: imageData,
    })

    testResults.value[testingConfig.value.id] = result
    testResult.value = result
  }

  testingId.value = null
  isTesting.value = false
}

watch(
  () => activeTab.value,
  () => {
    const subCat = currentSubCategories.value ? Object.keys(currentSubCategories.value)[0] : null
    activeSubCategory.value = subCat
    form.value.category = activeTab.value
    form.value.sub_category = subCat || undefined
  }
)

async function loadCategories() {
  try {
    categories.value = await fetchModelCategories()
    const firstKey = Object.keys(categories.value)[0]
    if (firstKey) {
      activeTab.value = firstKey
      const cat = categories.value[firstKey]
      if (cat?.sub_categories) {
        activeSubCategory.value = Object.keys(cat.sub_categories)[0]
      }
    }
  } catch { /* empty */ }
}

loadCategories()
modelConfigStore.loadConfigs()
</script>

<style scoped>
.model-config-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.model-config-panel {
  width: 440px;
  height: 100vh;
  background: rgba(10, 14, 26, 0.98);
  border-left: 1px solid rgba(0, 195, 255, 0.15);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.1);
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #e0f0ff;
  margin: 0;
  letter-spacing: 2px;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid rgba(0, 195, 255, 0.15);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  color: #ff4d6a;
  border-color: rgba(255, 77, 106, 0.3);
}

.panel-tabs {
  display: flex;
  gap: 0;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.08);
}

.panel-tab {
  flex: 1;
  padding: 10px;
  background: transparent;
  border: none;
  color: rgba(224, 240, 255, 0.4);
  font-size: 13px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.panel-tab.active {
  color: #00c3ff;
  border-bottom-color: #00c3ff;
}

.sub-category-filter {
  display: flex;
  gap: 8px;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.05);
}

.sub-tab {
  padding: 6px 12px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.1);
  border-radius: 6px;
  color: rgba(224, 240, 255, 0.5);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sub-tab.active {
  background: rgba(0, 195, 255, 0.1);
  border-color: rgba(0, 195, 255, 0.3);
  color: #00c3ff;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.empty-state {
  text-align: center;
  padding: 48px 0;
  color: rgba(224, 240, 255, 0.3);
  font-size: 14px;
}

.config-card {
  display: flex;
  flex-direction: column;
  padding: 14px 16px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.08);
  border-radius: 10px;
  margin-bottom: 10px;
  transition: all 0.2s ease;
}

.config-card:hover {
  border-color: rgba(0, 195, 255, 0.2);
}

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.config-name {
  font-size: 14px;
  color: #e0f0ff;
  font-weight: 500;
}

.config-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.config-provider {
  font-size: 11px;
  padding: 1px 8px;
  background: rgba(138, 99, 255, 0.15);
  color: #a366ff;
  border-radius: 4px;
}

.config-api-type {
  font-size: 11px;
  padding: 1px 8px;
  background: rgba(255, 170, 0, 0.15);
  color: #ffaa00;
  border-radius: 4px;
}

.sub-category-badge {
  font-size: 11px;
  padding: 1px 8px;
  background: rgba(0, 255, 136, 0.15);
  color: #00ff88;
  border-radius: 4px;
}

.default-badge {
  font-size: 11px;
  padding: 1px 8px;
  background: rgba(0, 195, 255, 0.15);
  color: #00c3ff;
  border-radius: 4px;
}

.public-badge {
  font-size: 11px;
  padding: 1px 8px;
  background: rgba(255, 77, 106, 0.15);
  color: #ff4d6a;
  border-radius: 4px;
}

.config-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid rgba(0, 195, 255, 0.1);
  border-radius: 6px;
  color: rgba(224, 240, 255, 0.4);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  color: #00c3ff;
  border-color: rgba(0, 195, 255, 0.3);
}

.action-btn.danger:hover {
  color: #ff4d6a;
  border-color: rgba(255, 77, 106, 0.3);
}

.action-btn.test {
  color: rgba(0, 255, 136, 0.5);
}

.action-btn.test:hover {
  color: #00ff88;
  border-color: rgba(0, 255, 136, 0.3);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn .btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(0, 255, 136, 0.3);
  border-top-color: #00ff88;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.test-result {
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.test-result.success {
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.2);
  color: #00ff88;
}

.test-result.error {
  background: rgba(255, 77, 106, 0.1);
  border: 1px solid rgba(255, 77, 106, 0.2);
  color: #ff4d6a;
}

.panel-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(0, 195, 255, 0.08);
}

.add-btn {
  width: 100%;
  padding: 12px;
  background: rgba(0, 195, 255, 0.08);
  border: 1px dashed rgba(0, 195, 255, 0.2);
  border-radius: 10px;
  color: #00c3ff;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.add-btn:hover {
  background: rgba(0, 195, 255, 0.12);
  border-color: rgba(0, 195, 255, 0.3);
}

.form-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.form-card {
  width: 360px;
  background: rgba(12, 18, 36, 0.98);
  border: 1px solid rgba(0, 195, 255, 0.2);
  border-radius: 12px;
  padding: 24px;
  max-height: 90vh;
  overflow-y: auto;
}

.form-title {
  font-size: 16px;
  color: #e0f0ff;
  margin: 0 0 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-group.half {
  flex: 1;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.5);
  margin-bottom: 6px;
}

.optional-hint {
  font-size: 11px;
  color: rgba(224, 240, 255, 0.3);
  font-weight: normal;
}

.api-key-hint {
  margin-top: 6px;
  font-size: 11px;
  color: rgba(0, 195, 255, 0.6);
  padding: 6px 10px;
  background: rgba(0, 195, 255, 0.05);
  border: 1px solid rgba(0, 195, 255, 0.15);
  border-radius: 4px;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  color: #e0f0ff;
  font-size: 13px;
  outline: none;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.form-select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M3 5L6 8L9 5' stroke='rgba(0, 195, 255, 0.5)' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}

.form-select option {
  background: #0c1224;
  color: #e0f0ff;
}

.form-input:focus,
.form-select:focus {
  border-color: rgba(0, 195, 255, 0.35);
}

.form-input::placeholder {
  color: rgba(224, 240, 255, 0.25);
}

.checkbox-label {
  display: flex !important;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  accent-color: #00c3ff;
}

.checkbox-label span {
  font-size: 13px;
  color: #e0f0ff;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.cancel-btn,
.save-btn {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.cancel-btn {
  background: rgba(224, 240, 255, 0.06);
  color: rgba(224, 240, 255, 0.5);
}

.cancel-btn:hover {
  background: rgba(224, 240, 255, 0.1);
}

.save-btn {
  background: linear-gradient(135deg, #00c3ff, #0080ff);
  color: #fff;
}

.save-btn:hover {
  box-shadow: 0 0 16px rgba(0, 195, 255, 0.3);
}

.test-modal-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

.test-modal-card {
  width: 400px;
  max-width: 90%;
  max-height: 90vh;
  background: rgba(12, 18, 36, 0.98);
  border: 1px solid rgba(0, 195, 255, 0.2);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.test-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.1);
}

.test-modal-title {
  font-size: 15px;
  color: #e0f0ff;
  margin: 0;
  font-weight: 500;
}

.test-modal-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid rgba(0, 195, 255, 0.15);
  border-radius: 6px;
  color: rgba(224, 240, 255, 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
}

.test-modal-close:hover {
  color: #ff4d6a;
  border-color: rgba(255, 77, 106, 0.3);
}

.test-modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.test-modal-row {
  margin-bottom: 16px;
}

.test-modal-row:last-child {
  margin-bottom: 0;
}

.test-modal-label {
  display: block;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.5);
  margin-bottom: 6px;
}

.test-modal-value {
  font-size: 14px;
  color: #e0f0ff;
}

.test-modal-status {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.test-modal-status.success {
  background: rgba(0, 255, 136, 0.15);
  color: #00ff88;
}

.test-modal-status.error {
  background: rgba(255, 77, 106, 0.15);
  color: #ff4d6a;
}

.test-modal-content {
  padding: 12px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.1);
  border-radius: 8px;
  font-size: 13px;
  color: #e0f0ff;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
  word-break: break-word;
}

.test-audio-player {
  width: 100%;
  height: 40px;
  border-radius: 8px;
  outline: none;
}

.test-audio-player::-webkit-media-controls-panel {
  background: rgba(0, 195, 255, 0.08);
}

.test-modal-error {
  padding: 12px;
  background: rgba(255, 77, 106, 0.08);
  border: 1px solid rgba(255, 77, 106, 0.2);
  border-radius: 8px;
  font-size: 13px;
  color: #ff4d6a;
  line-height: 1.6;
  word-break: break-word;
}

.test-image-result {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.test-image-preview {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: 8px;
  border: 1px solid rgba(0, 195, 255, 0.15);
  background: rgba(0, 0, 0, 0.2);
}

.test-image-link {
  font-size: 12px;
  color: rgba(0, 195, 255, 0.7);
  text-decoration: none;
  word-break: break-all;
  transition: color 0.2s ease;
}

.test-image-link:hover {
  color: #00c3ff;
}

.test-modal-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(0, 195, 255, 0.1);
  display: flex;
  justify-content: flex-end;
}

.test-modal-btn {
  padding: 8px 20px;
  background: rgba(0, 195, 255, 0.1);
  border: 1px solid rgba(0, 195, 255, 0.2);
  border-radius: 6px;
  color: #00c3ff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.test-modal-btn:hover {
  background: rgba(0, 195, 255, 0.15);
  border-color: rgba(0, 195, 255, 0.3);
}

.test-input-modal {
  width: 450px;
}

.test-textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  color: #e0f0ff;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.test-textarea:focus {
  border-color: rgba(0, 195, 255, 0.35);
}

.test-textarea::placeholder {
  color: rgba(224, 240, 255, 0.25);
}

.audio-input-section,
.image-input-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.audio-buttons,
.image-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.record-btn,
.upload-btn,
.default-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(0, 195, 255, 0.08);
  border: 1px solid rgba(0, 195, 255, 0.2);
  border-radius: 6px;
  color: #00c3ff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.record-btn:hover,
.upload-btn:hover,
.default-btn:hover {
  background: rgba(0, 195, 255, 0.12);
  border-color: rgba(0, 195, 255, 0.3);
}

.record-btn.recording {
  background: rgba(255, 77, 106, 0.15);
  border-color: rgba(255, 77, 106, 0.3);
  color: #ff4d6a;
}

.recording-indicator {
  width: 12px;
  height: 12px;
  background: #ff4d6a;
  border-radius: 50%;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.audio-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.2);
  border-radius: 6px;
  color: #00ff88;
  font-size: 12px;
}

.status-icon {
  font-size: 14px;
}

.image-preview {
  width: 100%;
  max-height: 200px;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid rgba(0, 195, 255, 0.15);
}

.image-preview img {
  width: 100%;
  height: auto;
  max-height: 200px;
  object-fit: contain;
}

.test-modal-btn.secondary {
  background: rgba(224, 240, 255, 0.06);
  border-color: rgba(224, 240, 255, 0.15);
  color: rgba(224, 240, 255, 0.6);
}

.test-modal-btn.secondary:hover {
  background: rgba(224, 240, 255, 0.1);
  border-color: rgba(224, 240, 255, 0.25);
  color: rgba(224, 240, 255, 0.8);
}

.test-modal-btn.primary {
  background: linear-gradient(135deg, #00c3ff, #0080ff);
  border-color: transparent;
  color: #fff;
}

.test-modal-btn.primary:hover {
  box-shadow: 0 0 16px rgba(0, 195, 255, 0.3);
}

.test-modal-btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.test-progress-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 16px;
}

.test-progress-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(0, 195, 255, 0.15);
  border-top-color: #00c3ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.test-progress-text {
  font-size: 14px;
  color: rgba(224, 240, 255, 0.7);
}

.streaming-content {
  margin-top: 16px;
  width: 100%;
  max-width: 400px;
}

.streaming-label {
  font-size: 12px;
  color: rgba(224, 240, 255, 0.5);
  margin-bottom: 8px;
}

.streaming-text {
  padding: 12px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  font-size: 13px;
  color: #e0f0ff;
  line-height: 1.6;
  max-height: 150px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-wrap;
}

.player-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: rgba(0, 255, 136, 0.08);
  border: 1px solid rgba(0, 255, 136, 0.2);
  border-radius: 8px;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  animation: pulse 1s ease-in-out infinite;
}

.status-indicator.connecting {
  background: #ffaa00;
}

.status-indicator.playing {
  background: #00ff88;
}

.status-text {
  font-size: 13px;
  color: #00ff88;
}

.stream-mode-toggle {
  display: flex;
  gap: 8px;
}

.mode-btn {
  padding: 6px 16px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.15);
  border-radius: 6px;
  color: rgba(224, 240, 255, 0.5);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-btn:hover {
  border-color: rgba(0, 195, 255, 0.3);
}

.mode-btn.active {
  background: rgba(0, 195, 255, 0.12);
  border-color: rgba(0, 195, 255, 0.4);
  color: #00c3ff;
}

.test-divider {
  height: 1px;
  background: rgba(0, 195, 255, 0.1);
  margin: 16px 0;
}
</style>
