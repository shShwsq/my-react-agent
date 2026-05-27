import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  fetchModelConfigs,
  createModelConfig,
  updateModelConfig,
  deleteModelConfig,
  type ModelConfigData,
} from '@/api/modelConfig'

export const useModelConfigStore = defineStore('modelConfig', () => {
  const configs = ref<ModelConfigData[]>([])
  const loaded = ref(false)

  const textConfigs = computed(() => configs.value.filter((c) => c.category === 'text'))
  const voiceConfigs = computed(() => configs.value.filter((c) => c.category === 'voice'))
  const visionConfigs = computed(() => configs.value.filter((c) => c.category === 'vision'))

  function getDefaultConfig(category: string, subCategory?: string): ModelConfigData | undefined {
    return configs.value.find((c) => {
      if (c.category !== category || !c.is_default) return false
      if (subCategory && c.sub_category !== subCategory) return false
      return true
    })
  }

  function getConfigByModel(modelName: string): ModelConfigData | undefined {
    return configs.value.find((c) => c.model_name === modelName)
  }

  function getConfigById(id: number): ModelConfigData | undefined {
    return configs.value.find((c) => c.id === id)
  }

  function getConfigsByCategory(category: string, subCategory?: string): ModelConfigData[] {
    return configs.value.filter((c) => {
      if (c.category !== category) return false
      if (subCategory && c.sub_category !== subCategory) return false
      return true
    })
  }

  async function loadConfigs() {
    if (loaded.value) return
    try {
      configs.value = await fetchModelConfigs()
      loaded.value = true
    } catch {
      configs.value = []
    }
  }

  async function addConfig(config: ModelConfigData) {
    const newConfig = await createModelConfig(config)
    configs.value.push(newConfig)
    return newConfig
  }

  async function editConfig(id: number, config: ModelConfigData) {
    const updated = await updateModelConfig(id, config)
    const idx = configs.value.findIndex((c) => c.id === id)
    if (idx !== -1) {
      configs.value[idx] = updated
    }
    return updated
  }

  async function removeConfig(id: number) {
    await deleteModelConfig(id)
    configs.value = configs.value.filter((c) => c.id !== id)
  }

  return {
    configs,
    loaded,
    textConfigs,
    voiceConfigs,
    visionConfigs,
    getDefaultConfig,
    getConfigByModel,
    getConfigById,
    getConfigsByCategory,
    loadConfigs,
    addConfig,
    editConfig,
    removeConfig,
  }
})
