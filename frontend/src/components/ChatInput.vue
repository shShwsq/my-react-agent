<template>
  <div class="chat-input-wrapper">
    <!-- 已选文件预览 -->
    <div class="file-preview-list" v-if="selectedFiles.length > 0">
      <div class="file-preview-item" v-for="(file, idx) in selectedFiles" :key="idx">
        <div class="file-preview-icon">
          <svg v-if="isImageFile(file)" viewBox="0 0 24 24" fill="none" width="16" height="16">
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
            <path d="M21 15l-5-5L5 21" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" width="16" height="16">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <span class="file-preview-name" :title="file.name">{{ file.name }}</span>
        <span class="file-preview-size">{{ formatFileSize(file.size) }}</span>
        <button class="file-preview-remove" @click="removeFile(idx)" title="移除">&times;</button>
      </div>
    </div>
    <input
      ref="fileInputRef"
      type="file"
      multiple
      :accept="acceptTypes"
      class="file-input-hidden"
      @change="handleFileSelect"
    />
    <textarea
      ref="textareaRef"
      v-model="inputText"
      class="chat-textarea"
      placeholder="输入消息..."
      rows="1"
      @keydown.enter.exact="handleSend"
      @input="autoResize"
    ></textarea>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'

const props = defineProps<{
  sending?: boolean
}>()

const emit = defineEmits<{
  send: [content: string, files?: File[]]
}>()

const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement>()
const fileInputRef = ref<HTMLInputElement>()
const selectedFiles = ref<File[]>([])

const acceptTypes = '.txt,.md,.json,.csv,.html,.htm,.xml,.yaml,.yml,.py,.js,.ts,.java,.c,.cpp,.h,.hpp,.cs,.go,.rs,.rb,.php,.sh,.bat,.ps1,.sql,.r,.m,.ini,.cfg,.conf,.log,.toml,.env,.docx,.pdf,.pptx,.xlsx,.jpg,.jpeg,.png,.gif,.bmp,.webp,.svg'

function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  for (const file of input.files) {
    if (!selectedFiles.value.find(f => f.name === file.name && f.size === file.size)) {
      selectedFiles.value.push(file)
    }
  }
  input.value = ''
}

function removeFile(idx: number) {
  selectedFiles.value.splice(idx, 1)
}

function autoResize() {
  nextTick(() => {
    const el = textareaRef.value
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 200) + 'px'
    }
  })
}

function handleSend(e?: Event) {
  if (e instanceof KeyboardEvent && e.shiftKey) return
  e?.preventDefault()
  const text = inputText.value.trim()
  const files = selectedFiles.value.length > 0 ? [...selectedFiles.value] : undefined
  if (!text && !files) return
  emit('send', text || '', files)
  inputText.value = ''
  selectedFiles.value = []
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
    }
  })
}

defineExpose({
  inputText,
  handleSend,
  selectedFiles,
  triggerFileInput
})
</script>

<style scoped>
.chat-input-wrapper {
  width: 100%;
}

.file-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.08);
  margin-bottom: 8px;
}

.file-preview-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(0, 195, 255, 0.06);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 6px;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.7);
  max-width: 200px;
}

.file-preview-icon {
  flex-shrink: 0;
  color: #00c3ff;
  display: flex;
  align-items: center;
}

.file-preview-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-preview-size {
  flex-shrink: 0;
  color: rgba(224, 240, 255, 0.35);
  font-size: 11px;
}

.file-preview-remove {
  flex-shrink: 0;
  background: none;
  border: none;
  color: rgba(224, 240, 255, 0.4);
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 0 2px;
}

.file-preview-remove:hover {
  color: #ff4d6a;
}

.file-input-hidden {
  display: none;
}

.chat-textarea {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  color: #e0f0ff;
  font-size: 15px;
  line-height: 1.6;
  resize: none;
  max-height: 200px;
  font-family: inherit;
}

.chat-textarea::placeholder {
  color: rgba(224, 240, 255, 0.25);
}
</style>
