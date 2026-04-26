<template>
  <div class="logs-page">
    <div class="page-header">
      <h1>📋 采集日志</h1>
    </div>

    <el-card>
      <el-table :data="logs" v-loading="loading" style="width:100%">
        <el-table-column prop="creator_name" label="博主" width="140" />
        <el-table-column prop="run_at" label="采集时间" width="200">
          <template #default="{ row }">{{ formatTime(row.run_at) }}</template>
        </el-table-column>
        <el-table-column prop="new_count" label="新增" width="80" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.new_count > 0 ? 'var(--success)' : 'var(--text-secondary)' }">
              +{{ row.new_count }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="total_count" label="总数" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'running' ? 'warning' : 'danger'" size="small">
              {{ { success:'成功', failed:'失败', running:'进行中' }[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时" width="90" align="right">
          <template #default="{ row }">
            {{ row.duration_ms ? `${(row.duration_ms/1000).toFixed(1)}s` : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="error_msg" label="错误信息">
          <template #default="{ row }">
            <span v-if="row.error_msg" class="error-text">{{ row.error_msg }}</span>
            <span v-else class="ok-text">—</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination v-model:current-page="page" :page-size="pageSize"
          :total="total" layout="prev, pager, next, total"
          @current-change="loadLogs" background />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { logApi } from '@/api'

const logs = ref([])
const loading = ref(true)
const page = ref(1)
const pageSize = 30
const total = ref(0)

const formatTime = (iso) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '—'

const loadLogs = async () => {
  loading.value = true
  try {
    const res = await logApi.list({ page: page.value, page_size: pageSize })
    logs.value = res.data || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

onMounted(loadLogs)
</script>

<style scoped>
.logs-page { max-width: 1200px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
.error-text { color: var(--danger); font-size: 12px; }
.ok-text { color: var(--text-secondary); }
</style>
