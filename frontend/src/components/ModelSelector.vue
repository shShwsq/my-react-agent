<template>
  <div class="model-selector">
    <div class="selector-dropdown" @click="toggleDropdown">
      <span class="selector-value">{{ selectedModelDisplay || '文本模型选择' }}</span>
      <svg class="selector-arrow" viewBox="0 0 12 12" fill="none">
        <path d="M3 5L6 8L9 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div v-if="open" class="selector-menu">
      <div
        v-for="m in textModels"
        :key="m.id"
        class="menu-item"
        :class="{ active: selectedModel === m.id }"
        @click="selectModel(m.id)"
      >
        {{ m.name }}
      </div>
      <div v-if="textModels.length === 0" class="menu-empty">
        暂无配置
      </div>
    </div>

    <button class="other-models-btn" @click="openOtherModels">
      其它模型
    </button>

    <div v-if="showOtherModels" class="modal-overlay" @click.self="showOtherModels = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>选择其它模型</h3>
          <button class="modal-close" @click="showOtherModels = false">
            <svg viewBox="0 0 12 12" fill="none" width="14" height="14">
              <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="sidebar">
            <div 
              v-for="(cat, catKey) in otherCategories" 
              :key="catKey" 
              class="sidebar-group"
            >
              <div 
                v-if="!cat.sub_categories || Object.keys(cat.sub_categories).length === 0"
                class="sidebar-item single"
                :class="{ active: activeCategory === catKey }"
                @click="selectCategory(catKey, null)"
              >
                {{ cat.label }}
              </div>
              <template v-else>
                <div class="sidebar-title">
                  {{ cat.label }}
                </div>
                <div class="sidebar-items">
                  <div
                    v-for="(subLabel, subKey) in cat.sub_categories"
                    :key="subKey"
                    class="sidebar-item"
                    :class="{ active: activeCategory === catKey && activeSubCategory === subKey }"
                    @click="selectCategory(catKey, subKey)"
                  >
                    {{ subLabel }}
                  </div>
                </div>
              </template>
            </div>
          </div>
          <div class="main-content">
            <div v-if="currentCategory" class="model-list">
              <div class="model-list-title">
                {{ currentCategory.label }}
                <span v-if="activeSubCategory"> / {{ currentCategory.sub_categories?.[activeSubCategory] }}</span>
              </div>
              <div class="model-options">
                <div
                  v-for="m in currentModels"
                  :key="m.id"
                  class="model-option"
                  :class="{ active: currentSelectedModel === m.id }"
                  @click="selectCurrentModel(m.id)"
                >
                  {{ m.name }}
                </div>
                <div v-if="currentModels.length === 0" class="model-empty">暂无配置</div>
              </div>
            </div>
            <div v-else class="model-list-placeholder">
              请在左侧选择分类
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-btn cancel" @click="showOtherModels = false">取消</button>
          <button class="modal-btn confirm" @click="confirmOtherModels">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useModelConfigStore } from '@/stores/modelConfig'
import { fetchModelCategories, type ModelCategory } from '@/api/modelConfig'

const props = defineProps<{
  selectedModel: string
}>()

const emit = defineEmits<{
  'update:selectedModel': [value: string]
  'update:subModels': [value: Record<string, string>]
}>()

const modelConfigStore = useModelConfigStore()

const open = ref(false)
const showOtherModels = ref(false)
const categories = ref<Record<string, ModelCategory>>({})
const selectedModels = ref<Record<string, string>>({})
const activeCategory = ref<string | null>(null)
const activeSubCategory = ref<string | null>(null)

const textModels = computed(() => 
  modelConfigStore.textConfigs.map(c => ({ 
    id: String(c.id), 
    name: c.call_method ? `${c.model_name} (${c.call_method})` : c.model_name,
    modelName: c.model_name,
    callMethod: c.call_method
  }))
)

const selectedModelDisplay = computed(() => {
  if (!props.selectedModel) return ''
  const config = modelConfigStore.getConfigById(Number(props.selectedModel))
  if (!config) return props.selectedModel
  return config.call_method 
    ? `${config.model_name} (${config.call_method})` 
    : config.model_name
})

const otherCategories = computed(() => {
  const result: Record<string, ModelCategory> = {}
  for (const [key, cat] of Object.entries(categories.value)) {
    if (key !== 'text') {
      result[key] = cat
    }
  }
  return result
})

const currentCategory = computed(() => {
  if (!activeCategory.value) return null
  return categories.value[activeCategory.value] || null
})

const currentModels = computed(() => {
  if (!activeCategory.value) return []
  return modelConfigStore.getConfigsByCategory(activeCategory.value, activeSubCategory.value || undefined)
    .map(c => ({ 
      id: String(c.id), 
      name: c.call_method ? `${c.model_name} (${c.call_method})` : c.model_name,
      modelName: c.model_name,
      callMethod: c.call_method
    }))
})

const currentSelectedModel = computed({
  get: () => {
    if (!activeCategory.value) return ''
    const key = activeSubCategory.value 
      ? `${activeCategory.value}_${activeSubCategory.value}` 
      : activeCategory.value
    return selectedModels.value[key] || ''
  },
  set: (value: string) => {
    if (!activeCategory.value) return
    const key = activeSubCategory.value 
      ? `${activeCategory.value}_${activeSubCategory.value}` 
      : activeCategory.value
    selectedModels.value[key] = value
  }
})

function toggleDropdown() {
  open.value = !open.value
}

function selectModel(id: string) {
  emit('update:selectedModel', id)
  open.value = false
}

function selectCategory(catKey: string, subKey: string | null) {
  activeCategory.value = catKey
  activeSubCategory.value = subKey
}

function selectCurrentModel(modelId: string) {
  currentSelectedModel.value = modelId
}

async function openOtherModels() {
  if (Object.keys(categories.value).length === 0) {
    try {
      categories.value = await fetchModelCategories()
    } catch {
      categories.value = {}
    }
  }
  
  initSelectedModels()
  
  const firstCat = Object.keys(otherCategories.value)[0]
  if (firstCat) {
    activeCategory.value = firstCat
    const cat = otherCategories.value[firstCat]
    if (cat.sub_categories && Object.keys(cat.sub_categories).length > 0) {
      activeSubCategory.value = Object.keys(cat.sub_categories)[0]
    } else {
      activeSubCategory.value = null
    }
  } else {
    activeCategory.value = null
    activeSubCategory.value = null
  }
  
  showOtherModels.value = true
}

function initSelectedModels() {
  for (const [catKey, cat] of Object.entries(categories.value)) {
    if (catKey === 'text') continue
    
    if (cat.sub_categories) {
      for (const subKey of Object.keys(cat.sub_categories)) {
        const key = `${catKey}_${subKey}`
        if (!selectedModels.value[key]) {
          const defaultConfig = modelConfigStore.getDefaultConfig(catKey, subKey)
          if (defaultConfig) {
            selectedModels.value[key] = String(defaultConfig.id)
          }
        }
      }
    } else {
      if (!selectedModels.value[catKey]) {
        const defaultConfig = modelConfigStore.getDefaultConfig(catKey)
        if (defaultConfig) {
          selectedModels.value[catKey] = String(defaultConfig.id)
        }
      }
    }
  }
}

function confirmOtherModels() {
  emit('update:subModels', { ...selectedModels.value })
  showOtherModels.value = false
}

function handleClickOutside(e: MouseEvent) {
  const el = (e.target as HTMLElement).closest('.model-selector')
  if (!el) open.value = false
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.model-selector {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
}

.selector-dropdown {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(0, 195, 255, 0.06);
  border: 1px solid rgba(0, 195, 255, 0.15);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.selector-dropdown:hover {
  border-color: rgba(0, 195, 255, 0.3);
}

.selector-value {
  font-size: 13px;
  color: #00c3ff;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selector-arrow {
  width: 12px;
  height: 12px;
  color: rgba(0, 195, 255, 0.5);
  transition: transform 0.2s ease;
}

.selector-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  min-width: 180px;
  background: rgba(12, 18, 36, 0.98);
  border: 1px solid rgba(0, 195, 255, 0.2);
  border-radius: 10px;
  padding: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  z-index: 100;
  max-height: 280px;
  overflow-y: auto;
}

.menu-item {
  padding: 8px 12px;
  font-size: 13px;
  color: rgba(224, 240, 255, 0.7);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.menu-item:hover {
  background: rgba(0, 195, 255, 0.1);
  color: #00c3ff;
}

.menu-item.active {
  background: rgba(0, 195, 255, 0.15);
  color: #00c3ff;
}

.menu-empty {
  padding: 8px 12px;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.3);
}

.other-models-btn {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid rgba(0, 195, 255, 0.15);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.other-models-btn:hover {
  border-color: rgba(0, 195, 255, 0.3);
  color: #00c3ff;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  background: rgba(12, 18, 36, 0.98);
  border: 1px solid rgba(0, 195, 255, 0.2);
  border-radius: 12px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.1);
  flex-shrink: 0;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #e0f0ff;
  letter-spacing: 1px;
}

.modal-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: rgba(224, 240, 255, 0.4);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  color: #ff4d6a;
  background: rgba(255, 77, 106, 0.1);
}

.modal-body {
  display: flex;
  flex: 1;
  min-height: 300px;
  overflow: hidden;
}

.sidebar {
  width: 160px;
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.2);
  border-right: 1px solid rgba(0, 195, 255, 0.1);
  overflow-y: auto;
  padding: 12px 0;
}

.sidebar-group {
  margin-bottom: 8px;
}

.sidebar-title {
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 500;
  color: rgba(224, 240, 255, 0.5);
  letter-spacing: 1px;
}

.sidebar-items {
  padding-left: 8px;
}

.sidebar-item {
  padding: 8px 16px 8px 24px;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
}

.sidebar-item.single {
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 500;
}

.sidebar-item:hover {
  color: #00c3ff;
  background: rgba(0, 195, 255, 0.05);
}

.sidebar-item.active {
  color: #00c3ff;
  background: rgba(0, 195, 255, 0.1);
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.model-list-title {
  font-size: 14px;
  font-weight: 500;
  color: #e0f0ff;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.1);
}

.model-list-title span {
  color: rgba(0, 195, 255, 0.6);
}

.model-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-option {
  padding: 12px 16px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 8px;
  font-size: 13px;
  color: rgba(224, 240, 255, 0.7);
  cursor: pointer;
  transition: all 0.2s ease;
}

.model-option:hover {
  border-color: rgba(0, 195, 255, 0.3);
  color: #00c3ff;
  background: rgba(0, 195, 255, 0.06);
}

.model-option.active {
  background: rgba(0, 195, 255, 0.12);
  border-color: rgba(0, 195, 255, 0.4);
  color: #00c3ff;
}

.model-empty {
  padding: 20px;
  text-align: center;
  font-size: 13px;
  color: rgba(224, 240, 255, 0.3);
}

.model-list-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(224, 240, 255, 0.3);
  font-size: 13px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid rgba(0, 195, 255, 0.1);
  flex-shrink: 0;
}

.modal-btn {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.modal-btn.cancel {
  background: transparent;
  border: 1px solid rgba(224, 240, 255, 0.15);
  color: rgba(224, 240, 255, 0.6);
}

.modal-btn.cancel:hover {
  border-color: rgba(224, 240, 255, 0.3);
  color: #e0f0ff;
}

.modal-btn.confirm {
  background: linear-gradient(135deg, #00c3ff, #0080ff);
  border: none;
  color: #fff;
}

.modal-btn.confirm:hover {
  box-shadow: 0 0 16px rgba(0, 195, 255, 0.3);
}
</style>
