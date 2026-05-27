<template>
  <div class="login-container">
    <div class="login-bg-grid"></div>
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="2" width="36" height="36" rx="8" stroke="currentColor" stroke-width="2" />
            <path d="M12 20L18 26L28 14" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h1 class="login-title">Not Toy Anymore</h1>
        <p class="login-subtitle">Aiagent Platform</p>
      </div>

      <div class="login-tabs">
        <button
          :class="['tab-btn', { active: mode === 'login' }]"
          @click="mode = 'login'"
        >登录</button>
        <button
          :class="['tab-btn', { active: mode === 'register' }]"
          @click="mode = 'register'"
        >注册</button>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">用户名</label>
          <input
            v-model="username"
            type="text"
            class="form-input"
            placeholder="请输入用户名"
            required
          />
        </div>
        <div class="form-group">
          <label class="form-label">密码</label>
          <input
            v-model="password"
            type="password"
            class="form-input"
            placeholder="请输入密码"
            required
          />
        </div>
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="btn-spinner"></span>
          <span v-else>{{ mode === 'login' ? '登 录' : '注 册' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') {
      await authStore.login(username.value, password.value)
    } else {
      await authStore.register(username.value, password.value)
    }
    router.push('/')
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    error.value = typeof detail === 'string' ? detail : '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0a0e1a;
  position: relative;
  overflow: hidden;
}

.login-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 195, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 195, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(40px, 40px); }
}

.login-card {
  position: relative;
  width: 420px;
  padding: 48px 40px;
  background: rgba(12, 18, 36, 0.9);
  border: 1px solid rgba(0, 195, 255, 0.15);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  box-shadow:
    0 0 40px rgba(0, 195, 255, 0.05),
    inset 0 1px 0 rgba(0, 195, 255, 0.1);
}

.login-card::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 20%;
  right: 20%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00c3ff, transparent);
  border-radius: 2px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  color: #00c3ff;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 6px;
  color: #e0f0ff;
  margin: 0 0 8px;
}

.login-subtitle {
  font-size: 14px;
  color: rgba(0, 195, 255, 0.6);
  margin: 0;
  letter-spacing: 2px;
}

.login-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 28px;
  background: rgba(0, 195, 255, 0.05);
  border-radius: 8px;
  padding: 3px;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: none;
  background: transparent;
  color: rgba(224, 240, 255, 0.5);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.tab-btn.active {
  background: rgba(0, 195, 255, 0.15);
  color: #00c3ff;
  box-shadow: 0 0 12px rgba(0, 195, 255, 0.1);
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 13px;
  color: rgba(224, 240, 255, 0.6);
  margin-bottom: 8px;
  letter-spacing: 1px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  color: #e0f0ff;
  font-size: 14px;
  outline: none;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.form-input::placeholder {
  color: rgba(224, 240, 255, 0.25);
}

.form-input:focus {
  border-color: rgba(0, 195, 255, 0.4);
  box-shadow: 0 0 16px rgba(0, 195, 255, 0.08);
  background: rgba(0, 195, 255, 0.06);
}

.error-msg {
  color: #ff4d6a;
  font-size: 13px;
  margin: -8px 0 16px;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #00c3ff, #0080ff);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.submit-btn:hover:not(:disabled) {
  box-shadow: 0 0 24px rgba(0, 195, 255, 0.3);
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
