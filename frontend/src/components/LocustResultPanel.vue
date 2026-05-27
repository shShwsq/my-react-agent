<template>
  <div v-if="visible" class="locust-panel-overlay" @click="handleClose">
    <div class="locust-panel" @click.stop>
      <div class="panel-header">
        <div class="panel-icon">
          <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h3 class="panel-title">Locust 压测结果</h3>
        <button class="panel-close" @click="handleClose">
          <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      
      <div class="panel-body">
        <!-- 配置信息 -->
        <div class="config-section">
          <div class="section-header">
            <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="section-title">压测配置</span>
          </div>
          <div class="config-grid">
            <div class="config-item">
              <span class="config-label">目标地址</span>
              <span class="config-value">{{ result?.config?.host }}</span>
            </div>
            <div class="config-item">
              <span class="config-label">并发用户</span>
              <span class="config-value highlight">{{ result?.config?.users }}</span>
            </div>
            <div class="config-item">
              <span class="config-label">启动速率</span>
              <span class="config-value">{{ result?.config?.spawn_rate }}/秒</span>
            </div>
            <div class="config-item">
              <span class="config-label">运行时间</span>
              <span class="config-value">{{ result?.config?.run_time }}</span>
            </div>
            <div class="config-item">
              <span class="config-label">请求数</span>
              <span class="config-value">{{ result?.config?.request_count }}</span>
            </div>
          </div>
        </div>

        <!-- Web UI 访问链接 -->
        <div class="webui-section" v-if="result?.web_ui_url">
          <div class="section-header">
            <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
              <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="section-title">Locust Web UI</span>
          </div>
          <div class="webui-content">
            <p class="webui-hint">压测正在运行中，点击下方链接查看实时面板：</p>
            <a :href="locustWebUrl" target="_blank" rel="noopener" class="webui-link">
              <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
                <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ locustWebUrl }}
            </a>
            <button class="btn btn-stop" @click="handleStopLocust" v-if="result?.process_id">
              <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
                <rect x="6" y="6" width="12" height="12" rx="1" stroke="currentColor" stroke-width="1.5"/>
              </svg>
              <span>停止压测</span>
            </button>
          </div>
        </div>

        <!-- 关键指标 -->
        <div class="metrics-section" v-if="result?.parsed">
          <div class="section-header">
            <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
              <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="section-title">关键指标</span>
          </div>
          <div class="metrics-grid">
            <div class="metric-card success">
              <div class="metric-value">{{ result?.parsed?.total_requests || 0 }}</div>
              <div class="metric-label">总请求数</div>
            </div>
            <div class="metric-card warning" v-if="result?.parsed?.total_failures">
              <div class="metric-value">{{ result?.parsed?.total_failures || 0 }}</div>
              <div class="metric-label">失败数</div>
            </div>
            <div class="metric-card primary">
              <div class="metric-value">{{ (result?.parsed?.requests_per_second || 0).toFixed(1) }}<span class="metric-unit">/s</span></div>
              <div class="metric-label">吞吐量 (QPS)</div>
            </div>
            <div class="metric-card info">
              <div class="metric-value">{{ (result?.parsed?.avg_response_time || 0).toFixed(1) }}<span class="metric-unit">ms</span></div>
              <div class="metric-label">平均响应时间</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">{{ (result?.parsed?.min_response_time || 0).toFixed(1) }}<span class="metric-unit">ms</span></div>
              <div class="metric-label">最小响应时间</div>
            </div>
            <div class="metric-card danger">
              <div class="metric-value">{{ (result?.parsed?.max_response_time || 0).toFixed(1) }}<span class="metric-unit">ms</span></div>
              <div class="metric-label">最大响应时间</div>
            </div>
          </div>
        </div>
        
        <!-- LLM 专属指标 -->
        <div class="metrics-section" v-if="result?.parsed?.llm_metrics">
          <div class="section-header">
            <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
              <path d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M19 14.5l-2.47 2.47a2.25 2.25 0 01-1.59.659H9.06a2.25 2.25 0 01-1.591-.659L5 14.5m14 0V17a2.25 2.25 0 01-2.25 2.25H7.25A2.25 2.25 0 015 17v-2.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="section-title">LLM 指标</span>
          </div>
          <div class="metrics-grid">
            <div class="metric-card llm-ttft">
              <div class="metric-value">{{ (result?.parsed?.llm_metrics?.avg_ttft_ms || 0).toFixed(1) }}<span class="metric-unit">ms</span></div>
              <div class="metric-label">平均首Token延迟 (TTFT)</div>
            </div>
            <div class="metric-card llm-tps">
              <div class="metric-value">{{ (result?.parsed?.llm_metrics?.avg_tokens_per_sec || 0).toFixed(1) }}<span class="metric-unit">t/s</span></div>
              <div class="metric-label">平均生成速度 (Tokens/s)</div>
            </div>
            <div class="metric-card llm-tokens">
              <div class="metric-value">{{ result?.parsed?.llm_metrics?.total_output_tokens || 0 }}</div>
              <div class="metric-label">总输出 Tokens</div>
            </div>
            <div class="metric-card llm-samples">
              <div class="metric-value">{{ result?.parsed?.llm_metrics?.ttft_samples || 0 }}</div>
              <div class="metric-label">采样数</div>
            </div>
          </div>
        </div>
        
        <!-- 响应时间百分位数 -->
        <div class="percentile-section" v-if="result?.parsed">
          <div class="section-header">
            <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="9 22 9 12 15 12 15 22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="section-title">响应时间百分位数</span>
          </div>
          <div class="percentile-bars">
            <div class="percentile-item">
              <div class="percentile-label">P50</div>
              <div class="percentile-bar-wrapper">
                <div 
                  class="percentile-bar p50" 
                  :style="{ width: getPercentileWidth(result?.parsed?.p50_response_time) }"
                ></div>
              </div>
              <div class="percentile-value">{{ (result?.parsed?.p50_response_time || 0).toFixed(1) }}ms</div>
            </div>
            <div class="percentile-item">
              <div class="percentile-label">P95</div>
              <div class="percentile-bar-wrapper">
                <div 
                  class="percentile-bar p95" 
                  :style="{ width: getPercentileWidth(result?.parsed?.p95_response_time) }"
                ></div>
              </div>
              <div class="percentile-value">{{ (result?.parsed?.p95_response_time || 0).toFixed(1) }}ms</div>
            </div>
            <div class="percentile-item">
              <div class="percentile-label">P99</div>
              <div class="percentile-bar-wrapper">
                <div 
                  class="percentile-bar p99" 
                  :style="{ width: getPercentileWidth(result?.parsed?.p99_response_time) }"
                ></div>
              </div>
              <div class="percentile-value">{{ (result?.parsed?.p99_response_time || 0).toFixed(1) }}ms</div>
            </div>
          </div>
        </div>
        
        <!-- 原始输出 -->
        <div class="output-section">
          <details class="collapsible-section">
            <summary class="collapsible-header">
              <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span class="collapsible-title">原始输出</span>
              <span class="collapsible-icon">▼</span>
            </summary>
            <div class="collapsible-content">
              <pre class="output-text">{{ result?.summary }}</pre>
            </div>
          </details>
        </div>
      </div>
      
      <div class="panel-footer">
        <button class="btn btn-copy" @click="handleCopy">
          <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
            <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <path d="M5 15H4C2.89543 15 2 14.1046 2 13V4C2 2.89543 2.89543 2 4 2H13C14.1046 2 15 2.89543 15 4V5" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span>复制结果</span>
        </button>
        <button class="btn btn-close" @click="handleClose">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface LocustResult {
  summary?: string
  web_ui_url?: string
  web_ui_port?: number
  process_id?: number
  parsed?: {
    total_requests: number
    total_failures: number
    requests_per_second: number
    avg_response_time: number
    min_response_time: number
    max_response_time: number
    p50_response_time: number
    p95_response_time: number
    p99_response_time: number
    llm_metrics?: {
      avg_ttft_ms: number
      avg_tokens_per_sec: number
      total_output_tokens: number
      ttft_samples: number
      tps_samples: number
    }
  }
  config: {
    host: string
    users: number
    spawn_rate: number
    run_time: string
    request_count: number
    has_llm_requests?: boolean
    headless?: boolean
  }
}

const props = defineProps<{
  visible: boolean
  result?: LocustResult
  locustWebProxyPath?: string
  frontendExternalUrl?: string
}>()

const emit = defineEmits<{
  close: []
  stopLocust: [processId: number]
}>()

const locustWebUrl = computed(() => {
  // 如果配置了 nginx 代理路径，使用外部地址 + 代理路径
  if (props.locustWebProxyPath) {
    const base = props.locustWebProxyPath.endsWith('/') ? props.locustWebProxyPath : props.locustWebProxyPath + '/'
    // 优先使用配置的外部地址，否则用当前页面 origin
    const origin = props.frontendExternalUrl || window.location.origin
    return `${origin}${base}`
  }
  // 否则直接使用后端返回的 URL
  return props.result?.web_ui_url || ''
})

function getPercentileWidth(value?: number): string {
  if (!value) return '0%'
  const maxValue = Math.max(
    props.result?.parsed?.p50_response_time || 0,
    props.result?.parsed?.p95_response_time || 0,
    props.result?.parsed?.p99_response_time || 0,
    1
  )
  return `${Math.min((value / maxValue) * 100, 100)}%`
}

async function handleCopy() {
  try {
    const jsonStr = JSON.stringify(props.result, null, 2)
    await navigator.clipboard.writeText(jsonStr)
    alert('结果已复制到剪贴板')
  } catch (err) {
    console.error('复制失败:', err)
    alert('复制失败')
  }
}

function handleStopLocust() {
  if (props.result?.process_id) {
    emit('stopLocust', props.result.process_id)
  }
}

function handleClose() {
  emit('close')
}
</script>

<style scoped>
.locust-panel-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  overflow-y: auto;
}

.locust-panel {
  width: 90%;
  max-width: 720px;
  max-height: 85vh;
  background: linear-gradient(135deg, #1a2332 0%, #0f1419 100%);
  border: 1px solid rgba(0, 195, 255, 0.15);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: rgba(0, 195, 255, 0.05);
  border-bottom: 1px solid rgba(0, 195, 255, 0.1);
  flex-shrink: 0;
}

.panel-icon {
  color: #00c3ff;
}

.panel-title {
  flex: 1;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #e0f0ff;
}

.panel-close {
  background: none;
  border: none;
  color: rgba(224, 240, 255, 0.5);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: color 0.2s;
}

.panel-close:hover {
  color: #e0f0ff;
}

.panel-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  color: rgba(224, 240, 255, 0.7);
  font-size: 13px;
  font-weight: 500;
}

.section-title {
  margin-left: 4px;
}

/* 配置信息 */
.config-section {
  margin-bottom: 20px;
}

/* Web UI 区域 */
.webui-section {
  margin-bottom: 20px;
  padding: 14px;
  background: rgba(34, 197, 94, 0.06);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 10px;
}

.webui-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.webui-hint {
  margin: 0;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.5);
}

.webui-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 8px;
  color: #4ade80;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
  width: fit-content;
}

.webui-link:hover {
  background: rgba(34, 197, 94, 0.2);
  border-color: rgba(34, 197, 94, 0.5);
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.config-label {
  font-size: 12px;
  color: rgba(224, 240, 255, 0.4);
}

.config-value {
  font-size: 14px;
  color: #e0f0ff;
  font-family: 'Monaco', 'Consolas', monospace;
}

.config-value.highlight {
  color: #00c3ff;
  font-weight: 600;
}

/* 关键指标 */
.metrics-section {
  margin-bottom: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.metric-card {
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  text-align: center;
  border: 1px solid rgba(0, 195, 255, 0.1);
}

.metric-card.success {
  border-color: rgba(46, 191, 144, 0.3);
}

.metric-card.warning {
  border-color: rgba(255, 193, 7, 0.3);
}

.metric-card.primary {
  border-color: rgba(0, 195, 255, 0.3);
  background: rgba(0, 195, 255, 0.05);
}

.metric-card.info {
  border-color: rgba(100, 181, 246, 0.3);
}

.metric-card.danger {
  border-color: rgba(255, 77, 106, 0.3);
}

.metric-card.llm-ttft {
  border-color: rgba(168, 85, 247, 0.4);
  background: rgba(168, 85, 247, 0.05);
}

.metric-card.llm-tps {
  border-color: rgba(34, 197, 94, 0.4);
  background: rgba(34, 197, 94, 0.05);
}

.metric-card.llm-tokens {
  border-color: rgba(251, 146, 60, 0.3);
}

.metric-card.llm-samples {
  border-color: rgba(148, 163, 184, 0.3);
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #e0f0ff;
  font-family: 'Monaco', 'Consolas', monospace;
}

.metric-unit {
  font-size: 12px;
  font-weight: 400;
  color: rgba(224, 240, 255, 0.5);
}

.metric-label {
  font-size: 11px;
  color: rgba(224, 240, 255, 0.5);
  margin-top: 4px;
}

/* 百分位数 */
.percentile-section {
  margin-bottom: 20px;
}

.percentile-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.percentile-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.percentile-label {
  width: 40px;
  font-size: 12px;
  font-weight: 600;
  color: #00c3ff;
}

.percentile-bar-wrapper {
  flex: 1;
  height: 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  overflow: hidden;
}

.percentile-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.percentile-bar.p50 {
  background: linear-gradient(90deg, #2ebf90, #2ebf90);
}

.percentile-bar.p95 {
  background: linear-gradient(90deg, #00c3ff, #0080ff);
}

.percentile-bar.p99 {
  background: linear-gradient(90deg, #ffc107, #ff9800);
}

.percentile-value {
  width: 70px;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.7);
  text-align: right;
  font-family: 'Monaco', 'Consolas', monospace;
}

/* 原始输出 */
.output-section {
  margin-bottom: 10px;
}

.collapsible-section {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(0, 195, 255, 0.1);
  overflow: hidden;
}

.collapsible-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  color: rgba(224, 240, 255, 0.7);
  font-size: 13px;
  transition: background 0.2s;
}

.collapsible-header:hover {
  background: rgba(0, 195, 255, 0.05);
}

.collapsible-title {
  flex: 1;
}

.collapsible-icon {
  font-size: 10px;
  color: rgba(224, 240, 255, 0.4);
  transition: transform 0.2s;
}

.collapsible-section[open] .collapsible-icon {
  transform: rotate(180deg);
}

.collapsible-content {
  padding: 12px;
  border-top: 1px solid rgba(0, 195, 255, 0.1);
}

.output-text {
  margin: 0;
  padding: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.8);
  font-family: 'Monaco', 'Consolas', monospace;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

/* 底部按钮 */
.panel-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(0, 195, 255, 0.1);
  flex-shrink: 0;
}

.btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-copy {
  background: rgba(0, 195, 255, 0.1);
  color: #00c3ff;
  border: 1px solid rgba(0, 195, 255, 0.2);
}

.btn-copy:hover {
  background: rgba(0, 195, 255, 0.15);
}

.btn-close {
  background: rgba(224, 240, 255, 0.1);
  color: rgba(224, 240, 255, 0.7);
}

.btn-close:hover {
  background: rgba(224, 240, 255, 0.15);
}

.btn-stop {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 7px 14px;
  background: rgba(255, 77, 106, 0.1);
  color: #ff4d6a;
  border: 1px solid rgba(255, 77, 106, 0.3);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  width: fit-content;
}

.btn-stop:hover {
  background: rgba(255, 77, 106, 0.2);
  border-color: rgba(255, 77, 106, 0.5);
}
</style>