<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>📊 仪表盘</h1>
      <p class="subtitle">采集任务概览</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="card in statCards" :key="card.key" class="stat-card hover-card">
        <div class="stat-icon" :style="{ background: card.gradient }">
          <el-icon :size="24"><component :is="card.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats[card.key] ?? '—' }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
      </div>
    </div>

    <!-- 最近采集日志 -->
    <el-card class="logs-card">
      <template #header>
        <div class="card-header">
          <span>最近采集记录</span>
          <el-button text @click="$router.push('/logs')">查看全部 →</el-button>
        </div>
      </template>
      <el-table :data="recentLogs" size="small" style="width: 100%">
        <el-table-column prop="creator_name" label="博主" width="140" />
        <el-table-column prop="run_at" label="采集时间" width="180">
          <template #default="{ row }">{{ formatTime(row.run_at) }}</template>
        </el-table-column>
        <el-table-column prop="new_count" label="新增视频" width="100" align="center" />
        <el-table-column prop="total_count" label="检查数量" width="100" align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时" align="right">
          <template #default="{ row }">
            {{ row.duration_ms ? `${(row.duration_ms / 1000).toFixed(1)}s` : '—' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { statsApi, logApi } from '@/api'

const stats = ref({})
const recentLogs = ref([])

const statCards = [
  { key: 'creator_count', label: '监控博主', icon: 'User', gradient: 'linear-gradient(135deg,#fe2c55,#ff7043)' },
  { key: 'video_count', label: '采集视频', icon: 'VideoPlay', gradient: 'linear-gradient(135deg,#6366f1,#8b5cf6)' },
  { key: 'downloaded_count', label: '已下载', icon: 'Download', gradient: 'linear-gradient(135deg,#00c566,#00b4d8)' },
  { key: 'today_new', label: '今日新增', icon: 'Star', gradient: 'linear-gradient(135deg,#ffb800,#ff7c00)' },
]

const formatTime = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

onMounted(async () => {
  try {
    stats.value = await statsApi.get()
  } catch {}
  try {
    const res = await logApi.list({ page_size: 10 })
    recentLogs.value = res.data || []
  } catch {}
})
</script>

<style scoped>
.dashboard { max-width: 1200px; }
.page-header { margin-bottom: 28px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-icon {
  width: 52px; height: 52px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: white;
  flex-shrink: 0;
}
.stat-value { font-size: 28px; font-weight: 700; line-height: 1; }
.stat-label { color: var(--text-secondary); font-size: 13px; margin-top: 4px; }

.logs-card { margin-top: 8px; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
</style>
