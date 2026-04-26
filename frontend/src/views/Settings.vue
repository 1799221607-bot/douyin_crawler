<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>⚙️ 系统设置</h1>
      <p class="subtitle">管理平台的全局环境参数与系统信息</p>
    </div>

    <div class="settings-container">
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>💻 运行环境</span>
          </div>
        </template>
        <div class="info-list">
          <div class="info-item">
            <span class="label">平台版本</span>
            <span class="value">v1.2.0 (Account Pool Ready)</span>
          </div>
          <div class="info-item">
            <span class="label">前端框架</span>
            <span class="value">Vue 3.x + Element Plus</span>
          </div>
          <div class="info-item">
            <span class="label">后端引擎</span>
            <span class="value">FastAPI + SQLAlchemy</span>
          </div>
          <div class="info-item">
            <span class="label">采集驱动</span>
            <span class="value">Python ABogus + httpx</span>
          </div>
          <div class="info-item">
            <span class="label">数据库状态</span>
            <span class="value success">Connected (SQLite)</span>
          </div>
        </div>
      </el-card>

      <el-card class="settings-card mt-20">
        <template #header>
          <div class="card-header">
            <span>💾 存储管理</span>
          </div>
        </template>
        <div class="setting-item-inline">
          <div class="item-info">
            <span class="label">自动清理过期视频</span>
            <span class="desc">超出保留天数的视频及其记录将被永久删除（0 表示不清理）</span>
          </div>
          <div class="item-action">
            <el-input-number v-model="retentionDays" :min="0" :max="365" size="small" />
            <span class="unit">天</span>
            <el-button type="primary" size="small" @click="saveRetention" :loading="saving">保存</el-button>
          </div>
        </div>
      </el-card>

      <el-card class="settings-card mt-20">
        <template #header>
          <div class="card-header">
            <span>🛡️ 系统安全</span>
          </div>
        </template>
        <p class="tool-desc">
          所有 Cookie 数据均经过 AES 加密存储于本地数据库。请妥善保管您的 JWT 密钥和管理员账号。
        </p>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { settingApi } from '@/api'

const retentionDays = ref(0)
const saving = ref(false)

const loadSettings = async () => {
  try {
    const res = await settingApi.get('video_retention_days')
    retentionDays.value = parseInt(res.value) || 0
  } catch (err) {
    console.error('加载设置失败', err)
  }
}

const saveRetention = async () => {
  saving.value = true
  try {
    await settingApi.set('video_retention_days', { 
      value: String(retentionDays.value),
      description: '视频自动保留天数策略'
    })
    ElMessage.success('存储策略已更新')
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-page { width: 100%; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }

.settings-card { border-radius: var(--radius); }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }

.mt-20 { margin-top: 20px; }

.tool-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }

.info-list { display: flex; flex-direction: column; gap: 16px; }
.info-item { display: flex; justify-content: space-between; font-size: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.info-item:last-child { border-bottom: none; }
.info-item .label { color: var(--text-secondary); }
.info-item .value { font-weight: 500; }
.info-item .value.success { color: var(--el-color-success); }

.setting-item-inline { display: flex; justify-content: space-between; align-items: center; }
.item-info { display: flex; flex-direction: column; gap: 4px; }
.item-info .label { font-size: 14px; font-weight: 500; }
.item-info .desc { font-size: 12px; color: var(--text-secondary); }
.item-action { display: flex; align-items: center; gap: 8px; }
.unit { font-size: 13px; color: var(--text-secondary); }
</style>
