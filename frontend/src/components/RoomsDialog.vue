<template>
  <div class="rooms-overlay" v-if="visible" @click.self="$emit('close')">
    <div class="rooms-panel">
      <div class="panel-header">
        <h2 class="panel-title">我的房间</h2>
        <button class="close-btn" @click="$emit('close')">
          <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="panel-body">
        <div class="search-box">
          <svg viewBox="0 0 20 20" fill="none" width="16" height="16" class="search-icon">
            <path d="M9 17C13.4183 17 17 13.4183 17 9C17 4.58172 13.4183 1 9 1C4.58172 1 1 4.58172 1 9C1 13.4183 4.58172 17 9 17Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M17 17L19 19" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <input
            v-model="searchQuery"
            class="search-input"
            placeholder="搜索房间标题..."
            type="text"
          />
        </div>

        <div v-if="loading" class="loading-state">
          <span class="btn-spinner"></span>
          加载中...
        </div>

        <div v-else-if="filteredRooms.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" width="48" height="48">
            <path d="M3 7C3 5.89543 3.89543 5 5 5H19C20.1046 5 21 5.89543 21 7V17C21 18.1046 20.1046 19 19 19H5C3.89543 19 3 18.1046 3 17V7Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M3 10H21" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <p>{{ searchQuery ? '未找到匹配的房间' : '暂无房间' }}</p>
        </div>

        <div v-else class="rooms-list">
          <div
            v-for="room in filteredRooms"
            :key="room.id"
            class="room-item"
            @click="handleRoomClick(room.id)"
          >
            <div class="room-info">
              <div class="room-title">{{ room.title || '未命名房间' }}</div>
              <div class="room-meta">
                <span class="room-id">{{ room.id }}</span>
                <span class="room-time">{{ formatTime(room.created_at) }}</span>
              </div>
            </div>
            <svg viewBox="0 0 20 20" fill="none" width="16" height="16" class="arrow-icon">
              <path d="M7 4L13 10L7 16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { listRooms, type RoomListItem } from '@/api/room'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ close: [] }>()

const router = useRouter()
const rooms = ref<RoomListItem[]>([])
const loading = ref(false)
const searchQuery = ref('')

watch(() => props.visible, async (val) => {
  if (val) {
    searchQuery.value = ''
    await loadRooms()
  }
})

async function loadRooms() {
  loading.value = true
  try {
    rooms.value = await listRooms()
  } catch (e: any) {
    console.error('Failed to load rooms:', e)
  } finally {
    loading.value = false
  }
}

const filteredRooms = computed(() => {
  if (!searchQuery.value.trim()) {
    return rooms.value
  }
  const query = searchQuery.value.toLowerCase()
  return rooms.value.filter(room => 
    room.title.toLowerCase().includes(query)
  )
})

function handleRoomClick(roomId: string) {
  emit('close')
  router.push(`/room/${roomId}`)
}

function formatTime(isoString: string): string {
  const d = new Date(isoString)
  const Y = d.getFullYear()
  const M = String(d.getMonth() + 1).padStart(2, '0')
  const D = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${Y}-${M}-${D} ${h}:${m}`
}
</script>

<style scoped>
.rooms-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.rooms-panel {
  width: 560px;
  max-height: 85vh;
  background: #141a2e;
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 195, 255, 0.08);
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #e0f0ff;
  margin: 0;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: rgba(224, 240, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e0f0ff;
}

.panel-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(0, 195, 255, 0.04);
  border: 1px solid rgba(0, 195, 255, 0.12);
  border-radius: 10px;
  margin-bottom: 16px;
  transition: all 0.2s ease;
}

.search-box:focus-within {
  border-color: rgba(0, 195, 255, 0.3);
  box-shadow: 0 0 12px rgba(0, 195, 255, 0.08);
}

.search-icon {
  color: rgba(224, 240, 255, 0.4);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #e0f0ff;
  font-size: 14px;
  outline: none;
}

.search-input::placeholder {
  color: rgba(224, 240, 255, 0.3);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px;
  color: rgba(224, 240, 255, 0.5);
  font-size: 14px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px;
  color: rgba(224, 240, 255, 0.3);
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.rooms-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.room-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: rgba(0, 195, 255, 0.03);
  border: 1px solid rgba(0, 195, 255, 0.08);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.room-item:hover {
  background: rgba(0, 195, 255, 0.06);
  border-color: rgba(0, 195, 255, 0.2);
}

.room-info {
  flex: 1;
  min-width: 0;
}

.room-title {
  font-size: 14px;
  font-weight: 600;
  color: #e0f0ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.room-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: rgba(224, 240, 255, 0.4);
}

.room-id {
  font-family: monospace;
}

.room-time {
  color: rgba(224, 240, 255, 0.5);
}

.arrow-icon {
  color: rgba(224, 240, 255, 0.3);
  flex-shrink: 0;
  margin-left: 12px;
}

.room-item:hover .arrow-icon {
  color: #00c3ff;
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
</style>