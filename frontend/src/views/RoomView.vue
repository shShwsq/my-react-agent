<template>
  <div class="room-container">
    <div class="room-bg-grid"></div>

    <header class="room-header">
      <div class="header-left">
        <div class="header-logo">
          <svg viewBox="0 0 32 32" fill="none" width="28" height="28">
            <rect x="2" y="2" width="28" height="28" rx="6" stroke="currentColor" stroke-width="2" />
            <path d="M10 16L14 20L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h1 class="header-title">Not Toy Anymore</h1>
        <div class="header-divider"></div>
        <div class="header-status">
          <span class="h-status-item">
            <span class="h-status-dot" :class="sending ? 'active' : ''"></span>
            <span class="h-status-text">{{ sending ? '运行中' : '空闲' }}</span>
          </span>
          <span class="h-status-item" v-if="currentTask">
            <span class="h-status-label">任务:</span>
            <span class="h-status-text">{{ currentTask }}</span>
          </span>
          <span class="h-status-item">
            <span class="h-status-label">智能体:</span>
            <span class="h-status-text">{{ activeAgentsCount }}</span>
          </span>
        </div>
        <div class="header-actions">
          <button class="h-action-btn" @click="handlePause" title="暂停" v-if="sending">
            <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
              <rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor"/>
              <rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="header-right">
        <button class="settings-btn" @click="router.push('/')">
          <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
            <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>返回首页</span>
        </button>
        <button class="config-btn" @click="showConfig = true">
          <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
            <path d="M10 13C11.6569 13 13 11.6569 13 10C13 8.34315 11.6569 7 10 7C8.34315 7 7 8.34315 7 10C7 11.6569 8.34315 13 10 13Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M16.18 12.82C16.06 13.24 16.12 13.69 16.36 14.06L16.42 14.16C16.61 14.49 16.67 14.88 16.57 15.25C16.48 15.62 16.24 15.93 15.91 16.12C15.58 16.31 15.19 16.37 14.82 16.28C14.45 16.18 14.14 15.94 13.95 15.61L13.89 15.51C13.65 15.14 13.26 14.89 12.82 14.82C12.39 14.75 11.95 14.85 11.6 15.11C11.25 15.37 11.02 15.77 10.97 16.21V16.36C10.97 17.27 10.24 18 9.33 18C8.42 18 7.69 17.27 7.69 16.36V16.28C7.63 15.83 7.39 15.43 7.02 15.18C6.65 14.93 6.19 14.85 5.76 14.97L5.64 15.01C5.27 15.13 4.87 15.09 4.53 14.9C4.19 14.71 3.94 14.39 3.83 14.01C3.72 13.63 3.76 13.23 3.95 12.89L4.01 12.79C4.21 12.42 4.25 11.98 4.12 11.58C3.99 11.18 3.7 10.85 3.32 10.67L3.21 10.62C2.38 10.24 2 9.27 2.36 8.43C2.72 7.59 3.69 7.19 4.53 7.54L4.64 7.59C5.02 7.76 5.46 7.75 5.83 7.56C6.2 7.37 6.47 7.03 6.58 6.63C6.69 6.23 6.62 5.8 6.4 5.45L6.34 5.35C6.15 5.01 6.1 4.61 6.21 4.24C6.32 3.87 6.57 3.56 6.91 3.37C7.25 3.18 7.65 3.13 8.02 3.24C8.39 3.35 8.7 3.6 8.89 3.94L8.95 4.04C9.19 4.41 9.58 4.66 10.02 4.73C10.45 4.8 10.89 4.7 11.24 4.44C11.59 4.18 11.82 3.78 11.87 3.34V3.19C11.87 2.28 12.6 1.55 13.51 1.55C14.42 1.55 15.15 2.28 15.15 3.19V3.27C15.21 3.72 15.45 4.12 15.82 4.37C16.19 4.62 16.65 4.7 17.08 4.58L17.2 4.54C17.57 4.42 17.97 4.46 18.31 4.65C18.65 4.84 18.9 5.16 19.01 5.54C19.12 5.92 19.08 6.32 18.89 6.66L18.83 6.76C18.63 7.13 18.59 7.57 18.72 7.97C18.85 8.37 19.14 8.7 19.52 8.88L19.63 8.93C20.46 9.31 20.84 10.28 20.48 11.12C20.12 11.96 19.15 12.36 18.31 12.01L18.2 11.96C17.82 11.79 17.38 11.8 17.01 11.99C16.64 12.18 16.37 12.52 16.26 12.92C16.18 13.24 16.18 13.54 16.18 12.82Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
          <span>模型配置</span>
        </button>
        <button class="logout-btn" @click="handleLogout" title="退出">
          <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
            <path d="M13 3H16C16.55 3 17 3.45 17 4V16C17 16.55 16.55 17 16 17H13M8 14L3 10M3 10L8 6M3 10H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </header>

    <main class="room-main">
      <div class="left-panel" :style="{ width: leftPanelWidth + 'px' }">
        <div class="control-room">
          <div class="panel-header">
            <div class="panel-icon">
              <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <span class="panel-title">总控室</span>
            
            <!-- 正在运行的智能体指示器 -->
            <div class="running-agents">
              <span v-for="agent in activeAgents" :key="agent.id" class="running-agent-tag" :class="agent.status">
                <span class="agent-dot"></span>
                {{ agent.name }}
              </span>
            </div>
            
            <!-- 智能体选择下拉框 -->
            <select v-model="selectedAgentId" class="agent-selector">
              <option value="auto">auto</option>
              <option v-for="agent in agents" :key="agent.id" :value="agent.id">
                {{ agent.name }}
              </option>
            </select>
          </div>
          <div class="control-content">
            <!-- 只显示选中的智能体 -->
            <div class="agent-output-section" v-if="selectedAgent">
              <div class="agent-output-header">
                <span class="agent-output-name">{{ selectedAgent.name }}</span>
                <span class="agent-output-status" :class="selectedAgent.status">{{ statusText[selectedAgent.status] }}</span>
              </div>
              <div class="agent-history">
                <div class="agent-output-content" v-for="(record, index) in selectedAgent.history" :key="index">
                  <div class="output-text" v-html="formatContent(record.content)"></div>
                </div>
                <!-- 流式输出 -->
                <div class="agent-output-streaming" v-if="agentStreamContent && agentStreamRole === selectedAgent.type && (selectedAgent.status === 'thinking' || selectedAgent.status === 'working')">
                  <div class="output-text" v-html="formatContent(agentStreamContent)"></div>
                  <span class="streaming-cursor"></span>
                </div>
                <div class="agent-output-streaming" v-else-if="selectedAgent.status === 'thinking' || selectedAgent.status === 'working'">
                  <span class="streaming-dots">处理中...</span>
                </div>
                <div class="agent-output-empty" v-if="!selectedAgent.history.length && selectedAgent.status === 'idle'">
                  <span>等待执行</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="variables-panel">
          <div class="panel-header">
            <div class="panel-icon">
              <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
                <path d="M4 6H20M4 12H20M4 18H14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <span class="panel-title">变量</span>
          </div>
          <div class="variables-content">
            <div v-if="Object.keys(variables).length === 0" class="variables-empty">
              <span>暂无变量</span>
            </div>
            <div v-else class="variable-list">
              <div class="variable-item" v-for="(value, name) in variables" :key="name" @click="openVariableDetail(name, value)">
                <div class="variable-header">
                  <span class="variable-name">{{ name }}</span>
                  <span class="variable-type">{{ typeof value }}</span>
                </div>
                <div class="variable-value">{{ formatVariableValue(value) }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="output-panel">
          <div class="panel-header">
            <div class="panel-icon">
              <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
                <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M14 2V8H20" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <span class="panel-title">文件</span>
          </div>
          <div class="output-content">
            <div v-if="generatedFiles.length === 0" class="output-empty">
              <span>暂无文件</span>
            </div>
            <div v-else class="file-list">
              <!-- Upload 文件夹 -->
              <template v-if="uploadFiles.length > 0">
                <div class="file-folder-label">upload</div>
                <div class="file-item" v-for="file in uploadFiles" :key="'u-' + file.filename" @click="downloadFile(file)">
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16" class="file-icon">
                    <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M14 2V8H20" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  <span class="file-name">{{ file.filename }}</span>
                  <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
                </div>
              </template>
              <!-- Output 文件夹 -->
              <template v-if="outputFiles.length > 0">
                <div class="file-folder-label">output</div>
                <div class="file-item" v-for="file in outputFiles" :key="'o-' + file.filename" @click="downloadFile(file)">
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16" class="file-icon">
                    <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M14 2V8H20" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  <span class="file-name">{{ file.filename }}</span>
                  <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 可拖动分割线 -->
      <div 
        class="resize-handle" 
        @mousedown="startResize"
        :class="{ 'resizing': isResizing }"
      ></div>

      <div class="right-panel">
        <div class="chat-area" ref="messagesRef">
          <div v-if="messages.length === 0" class="welcome-state">
            <div class="welcome-icon">
              <svg viewBox="0 0 64 64" fill="none" width="64" height="64">
                <circle cx="32" cy="32" r="30" stroke="rgba(0,195,255,0.2)" stroke-width="1.5"/>
                <path d="M22 32L29 39L42 25" stroke="#00c3ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h2 class="welcome-title">开始对话</h2>
            <p class="welcome-desc">输入消息，多智能体将协同工作</p>
          </div>

          <div v-for="(msg, idx) in messages" :key="idx" :class="['message-row', msg.role]">
            <div class="message-avatar">
              <div v-if="msg.role === 'user'" class="avatar user-avatar">U</div>
              <div v-else-if="msg.role === 'brain'" class="avatar brain-avatar">B</div>
              <div v-else-if="msg.role === 'task'" class="avatar task-avatar">T</div>
              <div v-else-if="msg.role === 'check'" class="avatar check-avatar">C</div>
              <div v-else class="avatar ai-avatar">
                <svg viewBox="0 0 20 20" fill="none" width="14" height="14">
                  <path d="M4 10L8 14L16 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            <div class="message-content">
              <div class="message-role-label" v-if="msg.role !== 'user' && msg.role !== 'assistant'">
                {{ { brain: 'Brain Agent', task: 'Task Agent', check: 'Check Agent' }[msg.role] }}
              </div>
              <!-- Brain Agent 结构化显示 -->
              <div v-if="msg.role === 'brain' && msg.parsedData" class="agent-structured-output">
                <details class="collapsible-section">
                  <summary class="collapsible-header">
                    <span class="collapsible-title">Thinking</span>
                    <span class="collapsible-icon">▼</span>
                  </summary>
                  <div class="collapsible-content">
                    <div class="output-text" v-html="formatContent(msg.parsedData.thought || '')"></div>
                  </div>
                </details>
                <details class="collapsible-section">
                  <summary class="collapsible-header">
                    <span class="collapsible-title">User Intent</span>
                    <span class="collapsible-icon">▼</span>
                  </summary>
                  <div class="collapsible-content">
                    <div class="output-text" v-html="formatContent(msg.parsedData.intent || '')"></div>
                  </div>
                </details>
              </div>
              <!-- Check Agent 结构化显示 -->
              <div v-else-if="msg.role === 'check' && msg.parsedData" class="agent-structured-output">
                <details class="collapsible-section">
                  <summary class="collapsible-header">
                    <span class="collapsible-title">Summary</span>
                    <span class="collapsible-icon">▼</span>
                  </summary>
                  <div class="collapsible-content">
                    <div class="output-text" v-html="formatContent(
                      msg.parsedData.summary ||
                      (Array.isArray(msg.parsedData.suggestions) ? msg.parsedData.suggestions.map((s: string) => `• ${s}`).join('\n') : msg.parsedData.suggestions) ||
                      ''
                    )"></div>
                  </div>
                </details>
              </div>
              <!-- Task Agent 结构化显示 -->
              <div v-else-if="msg.role === 'task' && msg.parsedData" class="agent-structured-output">
                <div class="task-result">
                  <div v-if="msg.parsedData.e" class="task-error">
                    <span class="task-error-code">{{ msg.parsedData.e }}</span>
                    <span v-if="msg.parsedData.m">{{ msg.parsedData.m }}</span>
                  </div>
                  <div v-else class="task-success">
                    <span class="task-message">{{ msg.parsedData.m }}</span>
                  </div>
                  <details class="collapsible-section" v-if="msg.parsedData.d && Object.keys(msg.parsedData.d).length > 0">
                    <summary class="collapsible-header">
                      <span class="collapsible-title">Output Data</span>
                      <span class="collapsible-icon">▼</span>
                    </summary>
                    <div class="collapsible-content">
                      <pre class="output-json">{{ JSON.stringify(msg.parsedData.d, null, 2) }}</pre>
                    </div>
                  </details>
                </div>
              </div>
              <!-- 其他情况显示原始内容 -->
              <div v-else class="message-bubble" v-html="formatContent(msg.content)"></div>
            </div>
          </div>

          <div v-if="agentStreamContent" class="message-row" :class="agentStreamRole">
            <div class="message-avatar">
              <div v-if="agentStreamRole === 'brain'" class="avatar brain-avatar">B</div>
              <div v-else-if="agentStreamRole === 'check'" class="avatar check-avatar">C</div>
              <div v-else class="avatar task-avatar">T</div>
            </div>
            <div class="message-content">
              <div class="message-role-label">
                {{ { brain: 'Brain Agent', task: 'Task Agent', check: 'Check Agent' }[agentStreamRole] || agentStreamRole }}
              </div>
              <div class="message-bubble streaming" v-html="formatContent(agentStreamContent)"></div>
              <span class="cursor-blink"></span>
            </div>
          </div>

          <div v-if="streamingContent" class="message-row assistant">
            <div class="message-avatar">
              <div class="avatar ai-avatar">
                <svg viewBox="0 0 20 20" fill="none" width="14" height="14">
                  <path d="M4 10L8 14L16 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            <div class="message-content">
              <div class="message-bubble streaming" v-html="formatContent(streamingContent)"></div>
              <span class="cursor-blink"></span>
            </div>
          </div>
        </div>

        <div class="input-area">
          <div class="input-box">
            <div class="input-wrapper">
              <ChatInput ref="chatInputRef" :sending="sending" @send="handleSend" />
            </div>
            <div class="input-actions">
              <div class="model-display">{{ modelDisplayName }}</div>
              <VoiceInput 
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
      </div>
    </main>

    <ModelConfig :visible="showConfig" @close="showConfig = false" />
    
    <!-- 变量详情弹窗 -->
    <div v-if="showVariableDetail && selectedVariable" class="variable-detail-overlay" @click="closeVariableDetail">
      <div class="variable-detail-modal" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">变量详情</h3>
          <button class="modal-close" @click="closeVariableDetail">
            <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
              <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <div class="detail-label">变量名</div>
            <div class="detail-value variable-name-display">
              <span>{{ selectedVariable.name }}</span>
              <button class="copy-btn" @click="copyVariableName(selectedVariable.name)" title="复制变量名">
                <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
                  <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M5 15H4C2.89543 15 2 14.1046 2 13V4C2 2.89543 2.89543 2 4 2H13C14.1046 2 15 2.89543 15 4V5" stroke="currentColor" stroke-width="1.5"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="detail-section">
            <div class="detail-label">类型</div>
            <div class="detail-value">{{ typeof selectedVariable.value }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">值</div>
            <div class="detail-value full-value">
              <pre>{{ typeof selectedVariable.value === 'object' ? JSON.stringify(selectedVariable.value, null, 2) : selectedVariable.value }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 环境变量输入对话框 -->
    <EnvVarDialog
      :visible="showEnvVarDialog"
      title="输入敏感环境变量"
      description="请输入压测所需的敏感信息（如 API Key），这些信息仅在本次请求中使用，不会被保存或记录。"
      :variables="envVarVariables"
      @close="showEnvVarDialog = false"
      @confirm="handleEnvVarConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useModelConfigStore } from '@/stores/modelConfig'
import { runAgentLoop, AgentLoopEvent, getUserPreferences, pauseAgentLoop, submitEnvVars, getDeployConfig } from '@/api/agent'
import ChatInput from '@/components/ChatInput.vue'
import ModelConfig from '@/components/ModelConfig.vue'
import VoiceInput from '@/components/VoiceInput.vue'
import EnvVarDialog from '@/components/EnvVarDialog.vue'
import { getRoomCache, addMessageToRoom, saveRoomCache, RoomMessage, MessageRole } from '@/utils/roomCache'
import { addMessage, getRoomVariables, getRoom, getRoomFiles, uploadFile } from '@/api/room'

interface Agent {
  id: string
  name: string
  type: 'brain' | 'check' | 'task'
  status: 'idle' | 'thinking' | 'working' | 'completed' | 'error'
  progress: number
  currentTask: string
  output: string
  history: { content: string; timestamp: number }[]
}

interface Message {
  role: MessageRole
  content: string
  parsedData?: any
}

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const modelConfigStore = useModelConfigStore()

const roomId = computed(() => route.params.id as string)

const model = ref('')
const subModels = ref<Record<string, any>>({})
const messages = ref<Message[]>([])
const streamingContent = ref('')
const sending = ref(false)
const showConfig = ref(false)
const enabledTools = ref<string[] | undefined>(undefined)
const messagesRef = ref<HTMLDivElement>()
const chatInputRef = ref<InstanceType<typeof ChatInput>>()
const currentTask = ref('')
const abortController = ref<AbortController | null>(null)

const brainAnalysis = ref<{
  thought: string
  intent: string
  tasks: { type: string; description?: string; tool?: string; reason?: string; [key: string]: any }[]
  next_action: string
}>({
  thought: '',
  intent: '',
  tasks: [],
  next_action: ''
})

const brainStreamContent = ref('')
const agentStreamContent = ref('')
const agentStreamRole = ref<'brain' | 'task' | 'check'>('brain')

const generatedFiles = ref<{ filename: string; file_size: number; relative_path: string; folder: string }[]>([])

const uploadFiles = computed(() => generatedFiles.value.filter(f => f.folder === 'uploads'))
const outputFiles = computed(() => generatedFiles.value.filter(f => f.folder === 'outputs'))

const variables = ref<Record<string, any>>({})

const showVariableDetail = ref(false)
const selectedVariable = ref<{ name: string; value: any } | null>(null)

// 环境变量对话框相关
const showEnvVarDialog = ref(false)
const envVarVariables = ref<Record<string, { description?: string; placeholder?: string; required?: boolean }>>({})
const envVarCallback = ref<((values: Record<string, string>) => void) | null>(null)

const selectedAgentId = ref('auto')

// 分割线拖动相关状态
const leftPanelWidth = ref(320)
const isResizing = ref(false)

function startResize(e: MouseEvent) {
  isResizing.value = true
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  e.preventDefault()
}

function handleResize(e: MouseEvent) {
  if (!isResizing.value) return
  const container = document.querySelector('.room-main') as HTMLElement
  if (!container) return
  
  const containerRect = container.getBoundingClientRect()
  const newWidth = e.clientX - containerRect.left
  
  // 限制最小和最大宽度
  if (newWidth >= 200 && newWidth <= 600) {
    leftPanelWidth.value = newWidth
  }
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

const agents = ref<Agent[]>([
  { id: 'brain-001', name: 'Brain Agent', type: 'brain', status: 'idle', progress: 0, currentTask: '', output: '', history: [] },
  { id: 'check-001', name: 'Check Agent', type: 'check', status: 'idle', progress: 0, currentTask: '', output: '', history: [] },
  { id: 'task-001', name: 'Task Agent', type: 'task', status: 'idle', progress: 0, currentTask: '', output: '', history: [] },
])

const statusText: Record<string, string> = {
  idle: '空闲',
  thinking: '思考中',
  working: '工作中',
  completed: '已完成',
  error: '错误'
}

const activeAgentsCount = computed(() => {
  return agents.value.filter(a => a.status === 'working' || a.status === 'thinking').length
})

const activeAgents = computed(() => {
  return agents.value.filter(a => a.status === 'working' || a.status === 'thinking')
})

const selectedAgent = computed(() => {
  // 如果选择的是 auto，自动选择运行中的智能体或默认 brain agent
  if (selectedAgentId.value === 'auto') {
    const runningAgent = agents.value.find(a => a.status === 'working' || a.status === 'thinking')
    if (runningAgent) return runningAgent
    return agents.value.find(a => a.type === 'brain')
  }
  return agents.value.find(a => a.id === selectedAgentId.value)
})

const canSend = computed(() => {
  const text = chatInputRef.value?.inputText?.trim() || ''
  const files = chatInputRef.value?.selectedFiles?.length || 0
  return text.length > 0 || files > 0
})

const modelDisplayName = computed(() => {
  const config = modelConfigStore.getConfigById(Number(model.value))
  if (!config) return model.value
  return config.call_method 
    ? `${config.model_name} (${config.call_method})` 
    : config.model_name
})

const asrConfigId = computed(() => {
  if (subModels.value['voice_asr']) {
    return Number(subModels.value['voice_asr'])
  }
  if (typeof subModels.value['voice'] === 'object' && subModels.value['voice']?.asr) {
    return Number(subModels.value['voice'].asr)
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

function formatContent(content: string): string {
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}

function getTaskParsed(record: { content: string }): { e: string; d: any; m: string } {
  const parsed = tryParseJSON(record.content)
  if (parsed && (parsed.e !== undefined || parsed.d !== undefined || parsed.m !== undefined)) {
    return { e: parsed.e || '', d: parsed.d, m: parsed.m || '' }
  }
  return { e: '', d: null, m: record.content }
}

function tryParseJSON(content: string): any | null {
  try {
    // 尝试直接解析
    return JSON.parse(content)
  } catch {
    // 尝试从内容中提取JSON
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      try {
        return JSON.parse(jsonMatch[0])
      } catch {
        return null
      }
    }
    return null
  }
}

function parseMessagesWithResponse(messages: Message[]): Message[] {
  const result: Message[] = []
  
  for (const msg of messages) {
    // 为 task 消息补充 parsedData
    if (msg.role === 'task' && !msg.parsedData) {
      msg.parsedData = tryParseJSON(msg.content)
    }
    result.push(msg)
    
    // 如果是 brain 或 check 消息，尝试提取 response_to_user 作为独立消息
    if ((msg.role === 'brain' || msg.role === 'check') && msg.parsedData?.response_to_user) {
      result.push({
        role: 'assistant',
        content: msg.parsedData.response_to_user
      })
    }
  }
  
  return result
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatVariableValue(value: any): string {
  if (typeof value === 'string') {
    return value.length > 100 ? value.substring(0, 100) + '...' : value
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

function openVariableDetail(name: string, value: any) {
  selectedVariable.value = { name, value }
  showVariableDetail.value = true
}

function closeVariableDetail() {
  showVariableDetail.value = false
  selectedVariable.value = null
}

function handleEnvVarConfirm(values: Record<string, string>) {
  showEnvVarDialog.value = false
  // 将用户输入的环境变量提交给后端
  if (roomId.value && Object.keys(values).length > 0) {
    submitEnvVars(roomId.value, values).catch(err => {
      console.error('提交环境变量失败:', err)
    })
  }
  if (envVarCallback.value) {
    envVarCallback.value(values)
    envVarCallback.value = null
  }
}

function requestEnvVars(variables: Record<string, { description?: string; placeholder?: string; required?: boolean }>, callback: (values: Record<string, string>) => void) {
  envVarVariables.value = variables
  envVarCallback.value = callback
  showEnvVarDialog.value = true
}

async function copyVariableName(name: string) {
  try {
    await navigator.clipboard.writeText(`{{${name}}}`)
    // 可以添加一个提示
    alert('变量名已复制: ' + name)
  } catch (err) {
    console.error('Failed to copy:', err)
    alert('复制失败')
  }
}

async function downloadFile(file: { filename: string; relative_path: string }) {
  const token = localStorage.getItem('token')
  const url = `/api/files/download/${roomId.value}/${file.filename}`
  
  try {
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error('下载失败')
    }
    
    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = file.filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(downloadUrl)
  } catch (error) {
    console.error('Download error:', error)
    alert('文件下载失败')
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function handleSendClick() {
  if (chatInputRef.value) {
    chatInputRef.value.handleSend()
  }
}

async function handleSend(content: string, files?: File[]) {
  // 构建显示内容（包含文件信息）
  let displayContent = content
  if (files && files.length > 0) {
    const fileInfo = files.map(f => f.name).join(', ')
    displayContent = content ? `${content}\n[附件: ${fileInfo}]` : `[附件: ${fileInfo}]`
  }
  
  messages.value.push({ role: 'user', content: displayContent })
  
  // 保存用户消息到 localStorage
  const userMessage: RoomMessage = {
    id: `msg_${Date.now()}`,
    role: 'user',
    content: displayContent,
    timestamp: Date.now()
  }
  addMessageToRoom(roomId.value, userMessage)
  
  // 保存到数据库 + 上传文件
  try {
    await addMessage(roomId.value, { role: 'user', content: displayContent })
    
    if (files && files.length > 0) {
      for (const file of files) {
        try {
          await uploadFile(roomId.value, file)
        } catch (e) {
          console.error('Failed to upload file:', file.name, e)
        }
      }
    }
  } catch (e) {
    console.error('Failed to save message to database:', e)
  }
  
  scrollToBottom()
  
  // 如果智能体正在运行，用户消息已保存到数据库，
  // agent loop 会在下次 brain/check 时自动重新加载
  if (sending.value) {
    return
  }
  
  sending.value = true
  currentTask.value = '处理用户请求'
  
  resetAgentsStatus()
  agents.value[0].status = 'thinking'
  agents.value[0].currentTask = '分析用户意图'
  
  await startAgentLoop(displayContent)
}

function resetAgentsStatus() {
  agents.value.forEach(a => {
    a.status = 'idle'
    a.progress = 0
    a.currentTask = ''
  })
  brainAnalysis.value = { thought: '', intent: '', tasks: [], next_action: '' }
  brainStreamContent.value = ''
  agentStreamContent.value = ''
  agentStreamRole.value = 'brain'
}

function handleAgentEvent(event: AgentLoopEvent, currentContent: string) {
  switch (event.type) {
    case 'start':
      currentTask.value = '开始处理任务'
      break
    case 'iteration':
      currentTask.value = `第 ${event.iteration} 轮迭代`
      break
    case 'request_env_vars':
      // 后端请求环境变量输入，弹出对话框
      if (event.variables && typeof event.variables === 'object') {
        const requiredVars: Record<string, { description?: string; placeholder?: string; required?: boolean }> = {}
        Object.keys(event.variables).forEach(key => {
          const varInfo = event.variables[key]
          requiredVars[key] = {
            description: typeof varInfo === 'object' ? varInfo.description : varInfo,
            placeholder: `输入 ${key}`,
            required: true
          }
        })
        
        showEnvVarDialog.value = true
        envVarVariables.value = requiredVars
        envVarCallback.value = null  // 由 handleEnvVarConfirm 统一处理提交
      }
      break
    case 'agent_status':
      const agentIndex = event.agent === 'brain' ? 0 : event.agent === 'check' ? 1 : 2
      if (event.status === 'thinking') {
        agents.value[agentIndex].status = 'thinking'
      } else if (event.status === 'working') {
        agents.value[agentIndex].status = 'working'
      } else if (event.status === 'checking') {
        agents.value[agentIndex].status = 'working'
      }
      if (event.task) {
        agents.value[agentIndex].currentTask = event.task.type || event.status
      }
      break
    case 'brain_stream':
      // 流式 Brain 输出 - 显示在左侧面板和聊天区域
      brainStreamContent.value += event.content || ''
      agentStreamContent.value += event.content || ''
      agentStreamRole.value = 'brain'
      scrollToBottom()
      break
    case 'check_stream':
      // 流式 Check 输出 - 显示在聊天区域
      agentStreamContent.value += event.content || ''
      agentStreamRole.value = 'check'
      scrollToBottom()
      break
    case 'llm_generate_stream':
      agentStreamContent.value += event.content || ''
      agentStreamRole.value = 'task'
      scrollToBottom()
      break
    case 'image_understand_stream':
      agentStreamContent.value += event.content || ''
      agentStreamRole.value = 'task'
      scrollToBottom()
      break
    case 'file_created':
      // 文件创建事件
      if (event.data) {
        const newFile = {
          filename: event.data.filename,
          file_size: event.data.file_size || 0,
          relative_path: event.data.relative_path || '',
          folder: event.data.folder || 'outputs'
        }
        const exists = generatedFiles.value.find(f => f.filename === newFile.filename)
        if (!exists) {
          generatedFiles.value.push(newFile)
        }
        // 更新变量列表
        fetchVariables()
      }
      break
    case 'variable_set':
      // 变量设置事件
      if (event.data) {
        // 更新变量列表
        fetchVariables()
      }
      break
    case 'brain_result':
      agents.value[0].status = 'completed'
      agents.value[0].progress = 100
      if (agentStreamContent.value) {
        const parsedData = tryParseJSON(agentStreamContent.value)
        messages.value.push({
          role: 'brain',
          content: agentStreamContent.value,
          parsedData: parsedData
        })
        // 如果有 response_to_user，作为独立消息显示
        if (parsedData?.response_to_user) {
          messages.value.push({
            role: 'assistant',
            content: parsedData.response_to_user
          })
        }
        // 添加到历史记录
        agents.value[0].history.push({
          content: agentStreamContent.value,
          timestamp: Date.now()
        })
        agents.value[0].output = agentStreamContent.value
        // 保存到缓存 + 数据
        saveAgentHistoryToCache()
        addMessageToRoom(roomId.value, {
          id: `msg_${Date.now()}_brain_${Math.random().toString(36).slice(2, 6)}`,
          role: 'brain',
          content: agentStreamContent.value,
          timestamp: Date.now()
        })
      }
      brainStreamContent.value = ''
      agentStreamContent.value = ''
      if (event.data) {
        brainAnalysis.value = {
          thought: event.data.thought || '',
          intent: event.data.intent || '',
          tasks: event.data.tasks || [],
          next_action: event.data.next_action || ''
        }
        if (!agents.value[0].output) {
          const brainOutput = event.data.response_to_user || event.data.thought || JSON.stringify(event.data, null, 2)
          agents.value[0].output = brainOutput
          agents.value[0].history.push({
            content: brainOutput,
            timestamp: Date.now()
          })
          saveAgentHistoryToCache()
        }
      }
      break
    case 'task_result':
      agents.value[2].status = 'completed'
      agents.value[2].progress = 100
      if (event.data) {
        const taskOutput = typeof event.data === 'string'
          ? event.data
          : JSON.stringify({ e: event.data.e || '', d: event.data.d, m: event.data.m || '' })
        const parsedData = tryParseJSON(taskOutput)
        agents.value[2].output = taskOutput
        agents.value[2].history.push({
          content: taskOutput,
          timestamp: Date.now()
        })
        messages.value.push({
          role: 'task',
          content: taskOutput,
          parsedData
        })
        saveAgentHistoryToCache()
        addMessageToRoom(roomId.value, {
          id: `msg_${Date.now()}_task_${Math.random().toString(36).slice(2, 6)}`,
          role: 'task',
          content: taskOutput,
          timestamp: Date.now()
        })
      }
      agentStreamContent.value = ''
      break
    case 'check_result':
      agents.value[1].status = 'completed'
      agents.value[1].progress = 100
      if (agentStreamContent.value) {
        const parsedData = tryParseJSON(agentStreamContent.value)
        messages.value.push({
          role: 'check',
          content: agentStreamContent.value,
          parsedData: parsedData
        })
        // 如果有 response_to_user，作为独立消息显示
        if (parsedData?.response_to_user) {
          messages.value.push({
            role: 'assistant',
            content: parsedData.response_to_user
          })
        }
        // 添加到历史记录
        agents.value[1].history.push({
          content: agentStreamContent.value,
          timestamp: Date.now()
        })
        agents.value[1].output = agentStreamContent.value
        // 保存到缓存 + 数据
        saveAgentHistoryToCache()
        addMessageToRoom(roomId.value, {
          id: `msg_${Date.now()}_check_${Math.random().toString(36).slice(2, 6)}`,
          role: 'check',
          content: agentStreamContent.value,
          timestamp: Date.now()
        })
      }
      agentStreamContent.value = ''
      if (event.data && !agents.value[1].output) {
        const checkOutput = event.data.feedback || event.data.summary || JSON.stringify(event.data, null, 2)
        agents.value[1].output = checkOutput
        agents.value[1].history.push({
          content: checkOutput,
          timestamp: Date.now()
        })
        saveAgentHistoryToCache()
      }
      if (event.data?.is_complete) {
        currentTask.value = '任务完成'
      }
      break
    case 'summary':
      break
    case 'warning':
      console.warn('Warning:', event.message)
      break
    case 'done':
      currentTask.value = ''
      break
    case 'paused':
      currentTask.value = ''
      break
  }
}

async function handlePause() {
  // 调用后端暂停API
  try {
    await pauseAgentLoop(roomId.value)
  } catch (e) {
    console.error('Failed to pause agent loop:', e)
  }
  
  // 中断前端SSE连接
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  
  agents.value.forEach(a => {
    if (a.status === 'working' || a.status === 'thinking') {
      a.status = 'idle'
    }
  })
  sending.value = false
  currentTask.value = ''
  agentStreamContent.value = ''
  brainStreamContent.value = ''
}

function saveAgentHistoryToCache() {
  const roomCache = getRoomCache(roomId.value)
  if (roomCache) {
    roomCache.agents = agents.value.map(a => ({
      id: a.id,
      name: a.name,
      type: a.type,
      status: a.status,
      history: a.history
    }))
    saveRoomCache(roomCache)
  }
}

function restoreAgentHistoryFromCache() {
  const roomCache = getRoomCache(roomId.value)
  if (roomCache && roomCache.agents) {
    roomCache.agents.forEach((agentCache, index) => {
      if (agents.value[index]) {
        agents.value[index].history = agentCache.history || []
        agents.value[index].status = agentCache.status as any
        // 如果有历史记录，设置output为最后一条
        if (agentCache.history.length > 0) {
          agents.value[index].output = agentCache.history[agentCache.history.length - 1].content
        }
      }
    })
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  
  await authStore.fetchUserInfo()
  await modelConfigStore.loadConfigs()

  // 获取部署配置（外部访问地址等）
  try {
    const deployCfg = await getDeployConfig()
  } catch { /* ignore */ }
  
  // 加载启用的工具列表
  try {
    const prefs = await getUserPreferences()
    const stored = prefs['enabled_tools']
    if (stored) {
      try {
        enabledTools.value = JSON.parse(stored)
      } catch { /* ignore */ }
    }
  } catch (e) {
    console.error('Failed to load user preferences:', e)
  }
  
  // 加载变量
  await fetchVariables()
  
  const id = route.params.id as string
  const roomCache = getRoomCache(id)
  
  if (roomCache) {
    // 从缓存加载房间信息（立即可见）
    model.value = roomCache.models?.text || ''
    subModels.value = roomCache.models || {}
    
    // 加载历史消息
    const rawMessages = roomCache.messages.map(m => ({
      role: m.role,
      content: m.content,
      parsedData: (m.role === 'brain' || m.role === 'check') ? tryParseJSON(m.content) : undefined
    }))
    
    // 解析消息，提取 response_to_user 作为独立消息
    messages.value = parseMessagesWithResponse(rawMessages)
    
    // 恢复agent历史记录
    restoreAgentHistoryFromCache()
    
    // 如果有消息，说明是已有房间，直接显示
    if (messages.value.length > 0) {
      scrollToBottom()
    }
    
    // 加载输出文件列表 + 后台静默同步后端数据
    fetchRoomFiles()
    revalidateFromBackend(id)
    
    // 如果最后一条是用户消息，说明需要继续处理（新创建的房间）
    const lastMsg = roomCache.messages[roomCache.messages.length - 1]
    if (lastMsg && lastMsg.role === 'user') {
      sending.value = true
      currentTask.value = '处理用户请求'
      
      resetAgentsStatus()
      agents.value[0].status = 'thinking'
      agents.value[0].currentTask = '分析用户意图'
      
      scrollToBottom()
      
      await startAgentLoop(lastMsg.content)
    }
  } else {
    // 缓存不存在，从后端加载
    await loadRoomFromBackend(id)
  }
})

async function revalidateFromBackend(roomId: string) {
  try {
    const roomData = await getRoom(roomId)
    const cache = getRoomCache(roomId)
    const backendCount = roomData.messages.length
    const cacheCount = cache?.messages.length || 0
    
    if (backendCount > cacheCount) {
      console.log(`[Revalidate] Backend has ${backendCount} msgs, cache has ${cacheCount}, syncing...`)
      
      const rawMessages = roomData.messages.map(m => ({
        role: m.role as MessageRole,
        content: m.content,
        parsedData: (m.role === 'brain' || m.role === 'check') ? tryParseJSON(m.content) : undefined
      }))
      messages.value = parseMessagesWithResponse(rawMessages)
      restoreAgentHistoryFromMessages(roomData.messages)
      
      // 更新缓存
      cache!.messages = roomData.messages.map(m => ({
        id: String(m.id || ''),
        role: m.role as MessageRole,
        content: m.content,
        timestamp: Date.now()
      }))
      saveRoomCache(cache!)
    }
  } catch (e) {
    console.warn('[Revalidate] Failed to sync with backend:', e)
  }
}

async function loadRoomFromBackend(roomId: string) {
  try {
    const roomData = await getRoom(roomId)
    
    // 加载房间信息
    model.value = roomData.models?.text || ''
    subModels.value = roomData.models || {}
    
    // 加载历史消息
    const rawMessages = roomData.messages.map(m => ({
      role: m.role as MessageRole,
      content: m.content,
      parsedData: (m.role === 'brain' || m.role === 'check') ? tryParseJSON(m.content) : undefined
    }))
    
    // 解析消息，提取 response_to_user 作为独立消息
    messages.value = parseMessagesWithResponse(rawMessages)
    
    // 从messages中恢复agent历史记录
    restoreAgentHistoryFromMessages(roomData.messages)
    
    // 保存到前端缓存
    const cacheData = {
      id: roomData.id,
      title: roomData.title,
      models: roomData.models || {},
      messages: roomData.messages.map(m => ({
        id: String(m.id || ''),
        role: m.role as MessageRole,
        content: m.content,
        timestamp: Date.now()
      })),
      agents: agents.value.map(a => ({
        id: a.id,
        name: a.name,
        type: a.type,
        status: a.status,
        history: a.history
      })),
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
    saveRoomCache(cacheData)

    // 加载文件列表
    fetchRoomFiles()
    
    if (messages.value.length > 0) {
      scrollToBottom()
    }
  } catch (e) {
    console.error('Failed to load room from backend:', e)
  }
}

function restoreAgentHistoryFromMessages(messages: any[]) {
  messages.forEach(msg => {
    if (msg.role === 'brain') {
      agents.value[0].history.push({
        content: msg.content,
        timestamp: Date.now()
      })
      agents.value[0].output = msg.content
    } else if (msg.role === 'task') {
      agents.value[2].history.push({
        content: msg.content,
        timestamp: Date.now()
      })
      agents.value[2].output = msg.content
    } else if (msg.role === 'check') {
      agents.value[1].history.push({
        content: msg.content,
        timestamp: Date.now()
      })
      agents.value[1].output = msg.content
    }
  })
}

async function fetchVariables() {
  try {
    const vars = await getRoomVariables(roomId.value)
    variables.value = vars
  } catch (e) {
    console.error('Failed to fetch variables:', e)
  }
}

async function fetchRoomFiles() {
  try {
    const files = await getRoomFiles(roomId.value)
    generatedFiles.value = files.map(f => ({
      filename: f.filename,
      file_size: f.file_size,
      relative_path: f.relative_path,
      folder: (f as any).folder || 'outputs'
    }))
  } catch (e) {
    console.error('Failed to fetch output files:', e)
  }
}

async function startAgentLoop(content: string) {
  const config = modelConfigStore.getConfigById(Number(model.value))
  
  // 创建 AbortController 用于暂停
  const controller = new AbortController()
  abortController.value = controller
  
  try {
    let fullContent = ''
    
    await runAgentLoop(
      {
        user_input: content,
        room_id: roomId.value,
        context: {
          config_id: Number(model.value),
          model: config?.model_name || 'qwen-plus',
        },
        max_iterations: 10,
        enabled_tools: enabledTools.value
      },
      (event: AgentLoopEvent) => {
        handleAgentEvent(event, fullContent)
        if (event.type === 'summary' && event.content) {
          fullContent = event.content
        }
        if (event.type === 'brain_result' && event.data) {
          streamingContent.value = ''
          scrollToBottom()
        }
        if (event.type === 'task_result' && event.data) {
          streamingContent.value = ''
          scrollToBottom()
        }
        if (event.type === 'check_result' && event.data) {
          scrollToBottom()
        }
      },
      (error: Error) => {
        console.error('Agent loop error:', error)
        streamingContent.value = `错误: ${error.message}`
        agents.value.forEach(a => {
          a.status = 'error'
        })
      },
      controller.signal
    )
    
    streamingContent.value = ''
    sending.value = false
    currentTask.value = ''
    
    scrollToBottom()
    
    setTimeout(() => {
      resetAgentsStatus()
    }, 1000)
    
  } catch (error: any) {
    // 如果是用户主动暂停导致的abort，不视为错误
    if (error.name === 'AbortError') {
      console.log('Agent loop aborted by user')
      sending.value = false
      streamingContent.value = ''
      return
    }
    console.error('Error:', error)
    sending.value = false
    streamingContent.value = ''
    agents.value.forEach(a => {
      a.status = 'error'
    })
  }
}
</script>

<style scoped>
.room-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0a0e1a;
  position: relative;
  overflow: hidden;
}

.room-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 195, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 195, 255, 0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
}

.room-header {
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

.header-divider {
  width: 1px;
  height: 20px;
  background: rgba(0, 195, 255, 0.15);
  margin: 0 4px;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 16px;
}

.h-status-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.h-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(224, 240, 255, 0.3);
}

.h-status-dot.active {
  background: #00ff88;
  box-shadow: 0 0 6px rgba(0, 255, 136, 0.5);
}

.h-status-label {
  font-size: 11px;
  color: rgba(224, 240, 255, 0.4);
}

.h-status-text {
  font-size: 12px;
  color: rgba(224, 240, 255, 0.7);
}

.header-actions {
  display: flex;
  gap: 4px;
  margin-left: 4px;
}

.h-action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 195, 255, 0.06);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 6px;
  color: rgba(224, 240, 255, 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
}

.h-action-btn:hover {
  border-color: rgba(0, 195, 255, 0.3);
  color: #00c3ff;
  background: rgba(0, 195, 255, 0.1);
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
  gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.4);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.settings-btn:hover {
  color: #00c3ff;
  border-color: rgba(0, 195, 255, 0.3);
}

.settings-btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.room-main {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.left-panel {
  display: flex;
  flex-direction: column;
  background: rgba(12, 18, 36, 0.6);
  position: relative;
  z-index: 1;
}

.resize-handle {
  width: 4px;
  cursor: col-resize;
  background: transparent;
  transition: background 0.2s ease;
  flex-shrink: 0;
  position: relative;
  height: 100%;
  align-self: stretch;
}

.resize-handle::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  background: rgba(0, 195, 255, 0.15);
  transition: all 0.2s ease;
}

.resize-handle:hover::before,
.resize-handle.resizing::before {
  background: rgba(0, 195, 255, 0.5);
  box-shadow: 0 0 12px rgba(0, 195, 255, 0.4);
  width: 3px;
}

.resize-handle:hover,
.resize-handle.resizing {
  background: rgba(0, 195, 255, 0.05);
}

.control-room {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 16px 12px;
  flex-shrink: 0;
  background: rgba(12, 18, 36, 0.8);
  backdrop-filter: blur(8px);
  flex-wrap: wrap;
}

.panel-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 195, 255, 0.1);
  border: 1px solid rgba(0, 195, 255, 0.2);
  border-radius: 8px;
  color: #00c3ff;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #e0f0ff;
  letter-spacing: 1px;
}

.running-agents {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-left: auto;
}

.running-agent-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 12px;
  background: rgba(0, 195, 255, 0.1);
  border: 1px solid rgba(0, 195, 255, 0.3);
  color: #00c3ff;
}

.running-agent-tag.thinking {
  background: rgba(255, 193, 7, 0.1);
  border-color: rgba(255, 193, 7, 0.3);
  color: #ffc107;
}

.running-agent-tag.working {
  background: rgba(76, 175, 80, 0.1);
  border-color: rgba(76, 175, 80, 0.3);
  color: #4caf50;
}

.agent-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 0.4; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

.agent-selector {
  padding: 4px 2px;
  font-size: 11px;
  background: rgba(0, 195, 255, 0.1);
  border: 1px solid rgba(0, 195, 255, 0.3);
  border-radius: 6px;
  color: #e0f0ff;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
  max-width: 100px;
}

.agent-selector:hover {
  background: rgba(0, 195, 255, 0.2);
  border-color: rgba(0, 195, 255, 0.5);
}

.agent-selector option {
  background: #1a2438;
  color: #e0f0ff;
}

.control-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.agent-output-section {
  padding: 12px;
  background: rgba(0, 195, 255, 0.03);
  border: 1px solid rgba(0, 195, 255, 0.1);
  border-radius: 10px;
}

.agent-output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.agent-output-name {
  font-size: 12px;
  font-weight: 600;
  color: #e0f0ff;
}

.agent-output-status {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.agent-output-status.idle {
  background: rgba(128, 128, 128, 0.2);
  color: #888;
}

.agent-output-status.thinking {
  background: rgba(255, 200, 0, 0.2);
  color: #ffc800;
}

.agent-output-status.working {
  background: rgba(0, 195, 255, 0.2);
  color: #00c3ff;
}

.agent-output-status.completed {
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
}

.agent-output-status.error {
  background: rgba(255, 80, 80, 0.2);
  color: #ff5050;
}

.agent-output-content {
  font-size: 12px;
  color: rgba(224, 240, 255, 0.8);
  line-height: 1.5;
  margin-bottom: 12px;
  padding: 8px;
  background: rgba(0, 195, 255, 0.03);
  border-radius: 6px;
}

.agent-output-content:last-child {
  margin-bottom: 0;
}

.output-text {
  word-break: break-word;
  white-space: pre-wrap;
}

.agent-history {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.agent-output-streaming {
  font-size: 12px;
  color: rgba(0, 195, 255, 0.6);
}

.streaming-dots {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.agent-output-empty {
  font-size: 11px;
  color: rgba(128, 128, 128, 0.5);
}

.variables-panel {
  flex: 0 0 25%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-top: 1px solid rgba(0, 195, 255, 0.08);
  background: rgba(12, 18, 36, 0.4);
}

.variables-panel .panel-header {
  background: rgba(12, 18, 36, 0.8);
}

.variables-content {
  flex: 1;
  overflow-y: auto;
  padding: 2px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.variables-empty {
  font-size: 11px;
  color: rgba(128, 128, 128, 0.5);
  text-align: center;
  padding: 16px;
}

.variable-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.variable-item {
  padding: 10px 12px;
  background: rgba(0, 195, 255, 0.05);
  border: 1px solid rgba(0, 195, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.variable-item:hover {
  background: rgba(0, 195, 255, 0.1);
  border-color: rgba(0, 195, 255, 0.3);
  transform: translateY(-1px);
}

.variable-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.variable-name {
  font-size: 12px;
  font-weight: 600;
  color: #00c3ff;
}

.variable-type {
  font-size: 10px;
  color: rgba(128, 128, 128, 0.6);
  padding: 2px 6px;
  background: rgba(0, 195, 255, 0.1);
  border-radius: 4px;
}

.variable-value {
  font-size: 11px;
  color: #e0f0ff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.output-panel {
  flex: 0 0 25%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-top: 1px solid rgba(0, 195, 255, 0.08);
  background: rgba(12, 18, 36, 0.4);
}

.output-panel .panel-header {
  background: rgba(12, 18, 36, 0.8);
}

.output-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.output-empty {
  font-size: 11px;
  color: rgba(128, 128, 128, 0.5);
  text-align: center;
  padding: 16px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-folder-label {
  font-size: 11px;
  color: rgba(0, 195, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 8px 0 2px 4px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.08);
  margin-top: 4px;
}

.file-folder-label:first-child {
  margin-top: 0;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(0, 195, 255, 0.05);
  border: 1px solid rgba(0, 195, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.file-item:hover {
  background: rgba(0, 195, 255, 0.1);
  border-color: rgba(0, 195, 255, 0.3);
}

.file-icon {
  color: #00c3ff;
  flex-shrink: 0;
}

.file-name {
  flex: 1;
  font-size: 12px;
  color: #e0f0ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 10px;
  color: rgba(128, 128, 128, 0.6);
}

.control-content::-webkit-scrollbar,
.output-content::-webkit-scrollbar,
.variables-content::-webkit-scrollbar {
  width: 4px;
}

.control-content::-webkit-scrollbar-track,
.output-content::-webkit-scrollbar-track,
.variables-content::-webkit-scrollbar-track {
  background: transparent;
}

.control-content::-webkit-scrollbar-thumb,
.output-content::-webkit-scrollbar-thumb,
.variables-content::-webkit-scrollbar-thumb {
  background: rgba(0, 195, 255, 0.2);
  border-radius: 2px;
}

.control-content::-webkit-scrollbar-thumb:hover,
.output-content::-webkit-scrollbar-thumb:hover,
.variables-content::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 195, 255, 0.4);
}

.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: #ffc800;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursor-blink 0.8s ease-in-out infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  scroll-behavior: smooth;
}

.chat-area::-webkit-scrollbar {
  width: 4px;
}

.chat-area::-webkit-scrollbar-track {
  background: transparent;
}

.chat-area::-webkit-scrollbar-thumb {
  background: rgba(0, 195, 255, 0.15);
  border-radius: 2px;
}

.welcome-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.welcome-icon {
  margin-bottom: 24px;
  animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}

.welcome-title {
  font-size: 24px;
  font-weight: 600;
  color: #e0f0ff;
  margin: 0 0 8px;
  letter-spacing: 3px;
}

.welcome-desc {
  font-size: 14px;
  color: rgba(224, 240, 255, 0.3);
  margin: 0;
}

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}

.user-avatar {
  background: linear-gradient(135deg, #00c3ff, #0080ff);
  color: #fff;
}

.ai-avatar {
  background: rgba(0, 195, 255, 0.1);
  border: 1px solid rgba(0, 195, 255, 0.2);
  color: #00c3ff;
}

.brain-avatar {
  background: rgba(255, 200, 0, 0.15);
  border: 1px solid rgba(255, 200, 0, 0.3);
  color: #ffc800;
  font-size: 12px;
  font-weight: 700;
}

.task-avatar {
  background: rgba(0, 195, 255, 0.15);
  border: 1px solid rgba(0, 195, 255, 0.3);
  color: #00c3ff;
  font-size: 12px;
  font-weight: 700;
}

.check-avatar {
  background: rgba(0, 255, 136, 0.15);
  border: 1px solid rgba(0, 255, 136, 0.3);
  color: #00ff88;
  font-size: 12px;
  font-weight: 700;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.message-row.user .message-bubble {
  background: linear-gradient(135deg, rgba(0, 195, 255, 0.15), rgba(0, 128, 255, 0.15));
  border: 1px solid rgba(0, 195, 255, 0.15);
  color: #e0f0ff;
}

.message-row.assistant .message-bubble {
  background: rgba(0, 195, 255, 0.06);
  border: 1px solid rgba(0, 195, 255, 0.12);
  color: #e0f0ff;
  font-size: 15px;
}

.message-role-label {
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 4px;
  letter-spacing: 0.5px;
}

.message-row.brain .message-role-label {
  color: #ffc800;
}

.message-row.task .message-role-label {
  color: #00c3ff;
}

.message-row.check .message-role-label {
  color: #00ff88;
}

.message-row.brain .message-bubble {
  background: rgba(255, 200, 0, 0.04);
  border: 1px solid rgba(255, 200, 0, 0.1);
  color: rgba(224, 240, 255, 0.8);
}

.message-row.task .message-bubble {
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.1);
  color: rgba(224, 240, 255, 0.8);
}

.message-row.check .message-bubble {
  background: rgba(0, 255, 136, 0.04);
  border: 1px solid rgba(0, 255, 136, 0.1);
  color: rgba(224, 240, 255, 0.8);
}

.message-bubble :deep(code) {
  background: rgba(0, 195, 255, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #00c3ff;
}

/* 结构化输出样式 */
.agent-structured-output {
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  padding: 12px 16px;
  max-width: 800px;
}

.collapsible-section {
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.08);
  padding-bottom: 8px;
}

.collapsible-section:not([open]) {
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: none;
}

.collapsible-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  list-style: none;
  padding: 8px 0;
  margin: 0;
  color: #00c3ff;
  font-weight: 600;
  font-size: 14px;
}

.collapsible-header::-webkit-details-marker {
  display: none;
}

.collapsible-header::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-right: 2px solid #00c3ff;
  border-bottom: 2px solid #00c3ff;
  transform: rotate(45deg);
  margin-right: 8px;
  transition: transform 0.2s ease;
}

.collapsible-section[open] .collapsible-header::before {
  transform: rotate(-45deg);
}

.collapsible-title {
  flex: 1;
}

.collapsible-icon {
  font-size: 10px;
  opacity: 0.6;
}

.collapsible-content {
  padding: 8px 0 8px 14px;
  color: #c0d8f0;
  font-size: 14px;
  line-height: 1.6;
}

.output-section {
  margin-bottom: 8px;
}

.output-section:last-child {
  margin-bottom: 0;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: #00c3ff;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.output-text {
  color: #c0d8f0;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.output-text :deep(code) {
  background: rgba(0, 195, 255, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #00c3ff;
}

.output-text :deep(br) {
  margin: 0;
}

.streaming {
  animation: fadeGlow 1.5s ease-in-out infinite;
}

@keyframes fadeGlow {
  0%, 100% { box-shadow: 0 0 0 transparent; }
  50% { box-shadow: 0 0 12px rgba(0, 195, 255, 0.06); }
}

.cursor-blink {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: #00c3ff;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.input-area {
  padding: 16px 24px 24px;
  background: rgba(10, 14, 26, 0.6);
  border-top: 1px solid rgba(0, 195, 255, 0.06);
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
  margin: 0 auto;
}

.input-box:focus-within {
  border-color: rgba(0, 195, 255, 0.35);
  box-shadow: 0 0 20px rgba(0, 195, 255, 0.08);
}

.input-wrapper {
  width: 100%;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-display {
  font-size: 12px;
  color: rgba(0, 195, 255, 0.6);
  padding: 4px 8px;
  background: rgba(0, 195, 255, 0.06);
  border-radius: 4px;
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

/* 变量详情弹窗样式 */
.variable-detail-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.variable-detail-modal {
  background: linear-gradient(135deg, rgba(20, 30, 50, 0.98), rgba(12, 18, 36, 0.98));
  border: 1px solid rgba(0, 195, 255, 0.3);
  border-radius: 16px;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(0, 195, 255, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.15);
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #e0f0ff;
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 195, 255, 0.1);
  border: 1px solid rgba(0, 195, 255, 0.2);
  border-radius: 8px;
  color: #00c3ff;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close:hover {
  background: rgba(0, 195, 255, 0.2);
  border-color: rgba(0, 195, 255, 0.4);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(128, 128, 128, 0.8);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 14px;
  color: #e0f0ff;
  background: rgba(0, 195, 255, 0.05);
  border: 1px solid rgba(0, 195, 255, 0.1);
  border-radius: 8px;
  padding: 12px 16px;
}

.variable-name-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.variable-name-display span {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #00c3ff;
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(0, 195, 255, 0.1);
  border: 1px solid rgba(0, 195, 255, 0.3);
  border-radius: 6px;
  color: #00c3ff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: rgba(0, 195, 255, 0.2);
  border-color: rgba(0, 195, 255, 0.5);
}

.full-value {
  max-height: 400px;
  overflow-y: auto;
}

.full-value pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #e0f0ff;
  white-space: pre-wrap;
  word-break: break-all;
}
.task-success {
  color: #80e0a0;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.task-message {
  font-weight: 500;
}

.task-error {
  color: #ff8080;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 8px;
  display: flex;
  gap: 8px;
  align-items: baseline;
}

.task-error-code {
  background: rgba(255, 128, 128, 0.12);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.output-json {
  color: #c0d8f0;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

</style>
