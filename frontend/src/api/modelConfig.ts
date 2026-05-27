import axios from 'axios'

export interface ApiResponse<T = any> {
  e: string
  d: T
  m: string
}

export interface ModelConfigData {
  id?: number
  category: string
  sub_category?: string
  model_name: string
  provider: string
  call_method: string
  api_key?: string
  has_api_key?: boolean
  base_url: string
  is_default: boolean
  is_public: boolean
}

export interface ModelCategory {
  label: string
  sub_categories: Record<string, string> | null
}

function extractError(err: any): Error {
  if (err.response?.data) {
    const data = err.response.data
    if (data.e && data.m) {
      return new Error(data.m)
    }
  }
  return new Error(err.message || '请求失败')
}

export async function fetchModelConfigs(): Promise<ModelConfigData[]> {
  try {
    const res = await axios.get<ApiResponse<ModelConfigData[]>>('/api/models/configs')
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function createModelConfig(config: ModelConfigData): Promise<ModelConfigData> {
  try {
    const res = await axios.post<ApiResponse<ModelConfigData>>('/api/models/configs', config)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function updateModelConfig(id: number, config: ModelConfigData): Promise<ModelConfigData> {
  try {
    const res = await axios.put<ApiResponse<ModelConfigData>>(`/api/models/configs/${id}`, config)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function deleteModelConfig(id: number): Promise<void> {
  try {
    const res = await axios.delete<ApiResponse>(`/api/models/configs/${id}`)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function fetchModelCategories(): Promise<Record<string, ModelCategory>> {
  try {
    const res = await axios.get<ApiResponse<Record<string, ModelCategory>>>('/api/models/categories')
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function fetchProviders(category: string, subCategory?: string): Promise<{ value: string; label: string }[]> {
  try {
    const params = new URLSearchParams({ category })
    if (subCategory) {
      params.append('sub_category', subCategory)
    }
    const res = await axios.get<ApiResponse<{ value: string; label: string }[]>>(`/api/models/providers?${params.toString()}`)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function fetchCallMethods(category: string, provider: string, subCategory?: string): Promise<{ value: string; label: string }[]> {
  try {
    const params = new URLSearchParams({ category, provider })
    if (subCategory) {
      params.append('sub_category', subCategory)
    }
    const res = await axios.get<ApiResponse<{ value: string; label: string }[]>>(`/api/models/call-methods?${params.toString()}`)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}

export async function fetchModelNames(category: string, provider: string, callMethod: string, subCategory?: string): Promise<string[]> {
  try {
    const params = new URLSearchParams({ category, provider, call_method: callMethod })
    if (subCategory) {
      params.append('sub_category', subCategory)
    }
    const res = await axios.get<ApiResponse<string[]>>(`/api/models/model-names?${params.toString()}`)
    if (res.data.e) {
      throw new Error(res.data.m)
    }
    return res.data.d
  } catch (e: any) {
    throw extractError(e)
  }
}
