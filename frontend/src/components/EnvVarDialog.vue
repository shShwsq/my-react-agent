<template>
  <div v-if="visible" class="env-var-overlay" @click="handleOverlayClick">
    <div class="env-var-modal" @click.stop>
      <div class="modal-header">
        <div class="modal-icon">
          <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
            <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h3 class="modal-title">{{ title }}</h3>
        <button class="modal-close" @click="handleClose">
          <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      
      <div class="modal-body">
        <p class="modal-desc">{{ description }}</p>
        
        <div class="env-var-list">
          <div 
            v-for="(varInfo, name) in variables" 
            :key="name" 
            class="env-var-item"
          >
            <div class="var-label">
              <span class="var-name">{{ name }}</span>
              <span class="var-desc">{{ varInfo.description }}</span>
            </div>
            <input
              v-model="inputValues[name]"
              type="password"
              :placeholder="varInfo.placeholder"
              class="var-input"
              :required="varInfo.required"
            />
          </div>
        </div>
        
        <div class="security-hint">
          <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
            <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>敏感信息仅在本次请求中使用，不会被保存或记录</span>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="btn btn-cancel" @click="handleClose">取消</button>
        <button class="btn btn-confirm" @click="handleConfirm">确认</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

interface EnvVarInfo {
  description?: string
  placeholder?: string
  required?: boolean
}

const props = defineProps<{
  visible: boolean
  title?: string
  description?: string
  variables?: Record<string, EnvVarInfo>
}>()

const emit = defineEmits<{
  close: []
  confirm: [values: Record<string, string>]
}>()

const inputValues = reactive<Record<string, string>>({})

// 初始化输入值
watch(() => props.visible, (val) => {
  if (val && props.variables) {
    Object.keys(props.variables).forEach(name => {
      inputValues[name] = ''
    })
  }
}, { immediate: true })

function handleClose() {
  emit('close')
}

function handleOverlayClick() {
  // 点击遮罩不关闭，防止误操作
}

function handleConfirm() {
  const values: Record<string, string> = {}
  Object.keys(inputValues).forEach(key => {
    if (inputValues[key]) {
      values[key] = inputValues[key]
    }
  })
  emit('confirm', values)
}
</script>

<style scoped>
.env-var-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.env-var-modal {
  width: 90%;
  max-width: 480px;
  background: linear-gradient(135deg, #1a2332 0%, #0f1419 100%);
  border: 1px solid rgba(0, 195, 255, 0.15);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: rgba(0, 195, 255, 0.05);
  border-bottom: 1px solid rgba(0, 195, 255, 0.1);
}

.modal-icon {
  color: #00c3ff;
}

.modal-title {
  flex: 1;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #e0f0ff;
}

.modal-close {
  background: none;
  border: none;
  color: rgba(224, 240, 255, 0.5);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: color 0.2s;
}

.modal-close:hover {
  color: #e0f0ff;
  background: rgba(224, 240, 255, 0.05);
}

.modal-body {
  padding: 20px;
}

.modal-desc {
  margin: 0 0 16px;
  color: rgba(224, 240, 255, 0.6);
  font-size: 14px;
  line-height: 1.5;
}

.env-var-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.env-var-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.var-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.var-name {
  font-size: 13px;
  font-weight: 500;
  color: #00c3ff;
}

.var-desc {
  font-size: 12px;
  color: rgba(224, 240, 255, 0.4);
}

.var-input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 195, 255, 0.15);
  border-radius: 8px;
  color: #e0f0ff;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  font-family: 'Monaco', 'Consolas', monospace;
}

.var-input:focus {
  border-color: #00c3ff;
  box-shadow: 0 0 0 2px rgba(0, 195, 255, 0.1);
}

.var-input::placeholder {
  color: rgba(224, 240, 255, 0.25);
}

.security-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  background: rgba(46, 191, 144, 0.1);
  border: 1px solid rgba(46, 191, 144, 0.2);
  border-radius: 6px;
  font-size: 12px;
  color: rgba(46, 191, 144, 0.8);
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(0, 195, 255, 0.1);
}

.btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: rgba(224, 240, 255, 0.1);
  color: rgba(224, 240, 255, 0.7);
}

.btn-cancel:hover {
  background: rgba(224, 240, 255, 0.15);
}

.btn-confirm {
  background: linear-gradient(135deg, #00c3ff 0%, #0080ff 100%);
  color: #fff;
}

.btn-confirm:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 195, 255, 0.3);
}
</style>