<template>
  <div class="notifications-page">
    <div class="page-header">
      <div>
        <h1>🔔 通知配置</h1>
        <p class="subtitle">配置新视频推送渠道</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openAddDialog">添加渠道</el-button>
    </div>

    <div class="channels-grid">
      <div v-for="nc in configs" :key="nc.id" class="channel-card hover-card">
        <div class="channel-header">
          <div class="channel-icon" :style="{ background: channelStyle(nc.channel).bg }">
            {{ channelStyle(nc.channel).icon }}
          </div>
          <div class="channel-info">
            <div class="channel-name">{{ nc.name }}</div>
            <div class="channel-type">{{ channelStyle(nc.channel).label }}</div>
          </div>
          <el-switch v-model="nc.enabled" @change="(v) => toggleEnabled(nc, v)" />
        </div>
        <div class="channel-events">
          <el-tag v-for="ev in nc.events" :key="ev" size="small" type="info">
            {{ eventLabel(ev) }}
          </el-tag>
        </div>
        <div class="channel-actions">
          <el-button size="small" @click="testSend(nc)">测试发送</el-button>
          <el-button size="small" type="danger" text @click="deleteConfig(nc)">删除</el-button>
        </div>
      </div>

      <div class="add-channel-card hover-card" @click="openAddDialog">
        <el-icon :size="32"><Plus /></el-icon>
        <span>添加通知渠道</span>
      </div>
    </div>

    <!-- 添加渠道对话框 -->
    <el-dialog v-model="showDialog" title="添加通知渠道" width="520px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="渠道类型">
          <el-select v-model="form.channel" @change="onChannelChange" placeholder="选择渠道">
            <el-option v-for="(sch, key) in channelSchemas" :key="key"
              :label="sch.label" :value="key">
              <span>{{ channelStyle(key).icon }} {{ sch.label }}</span>
            </el-option>
          </el-select>
          <div v-if="channelSchemas[form.channel]?.note" class="field-note">
            ⚠️ {{ channelSchemas[form.channel].note }}
          </div>
        </el-form-item>
        <el-form-item label="配置名称">
          <el-input v-model="form.name" placeholder="例：研发团队飞书群" />
        </el-form-item>
        <el-form-item label="订阅事件">
          <el-checkbox-group v-model="form.events">
            <el-checkbox label="new_video">新视频</el-checkbox>
            <el-checkbox label="crawl_error">采集出错</el-checkbox>
            <el-checkbox label="ai_summary_done">AI总结完成</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <!-- 动态渲染渠道字段 -->
        <el-form-item v-for="field in currentFields" :key="field.key"
          :label="field.label">
          <el-input
            v-model="form.config_json[field.key]"
            :type="field.type === 'password' ? 'password' : field.type === 'number' ? 'number' : 'text'"
            :placeholder="field.required ? '必填' : '可选'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleAdd">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { notificationApi } from '@/api'

const configs = ref([])
const channelSchemas = ref({})
const showDialog = ref(false)
const submitting = ref(false)
const form = ref({ channel: '', name: '', events: ['new_video'], config_json: {} })

const currentFields = computed(() => channelSchemas.value[form.value.channel]?.fields || [])

const channelStyle = (ch) => ({
  feishu: { icon: '💬', label: '飞书', bg: 'linear-gradient(135deg,#1ba3ff,#0077ff)' },
  email: { icon: '📧', label: '邮件', bg: 'linear-gradient(135deg,#f59e0b,#ef4444)' },
  wechat_mp: { icon: '💚', label: '微信公众号', bg: 'linear-gradient(135deg,#07c160,#019c49)' },
  telegram: { icon: '✈️', label: 'Telegram', bg: 'linear-gradient(135deg,#2aabee,#229ed9)' },
}[ch] || { icon: '🔔', label: ch, bg: 'linear-gradient(135deg,#6366f1,#8b5cf6)' })

const eventLabel = (ev) => ({
  new_video: '新视频', crawl_error: '采集出错', ai_summary_done: 'AI完成'
}[ev] || ev)

const loadData = async () => {
  const [cfgRes, schRes] = await Promise.all([
    notificationApi.list(),
    notificationApi.channels(),
  ])
  configs.value = cfgRes.data || []
  channelSchemas.value = schRes.data || {}
}

const openAddDialog = () => {
  form.value = { channel: '', name: '', events: ['new_video'], config_json: {} }
  showDialog.value = true
}

const onChannelChange = () => { form.value.config_json = {} }

const handleAdd = async () => {
  submitting.value = true
  try {
    await notificationApi.create(form.value)
    ElMessage.success('添加成功')
    showDialog.value = false
    await loadData()
  } finally {
    submitting.value = false
  }
}

const toggleEnabled = async (nc, val) => {
  await notificationApi.update(nc.id, { enabled: val })
  ElMessage.success(val ? '已启用' : '已停用')
}

const testSend = async (nc) => {
  const res = await notificationApi.test(nc.id)
  ElMessage[res.success ? 'success' : 'error'](res.message)
}

const deleteConfig = async (nc) => {
  await ElMessageBox.confirm(`确认删除「${nc.name}」？`, '提示', { type: 'warning' })
  await notificationApi.delete(nc.id)
  ElMessage.success('已删除')
  await loadData()
}

onMounted(loadData)
</script>

<style scoped>
.notifications-page { max-width: 1100px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }

.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.channel-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
}
.channel-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.channel-icon {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; flex-shrink: 0;
}
.channel-info { flex: 1; }
.channel-name { font-weight: 600; font-size: 15px; }
.channel-type { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.channel-events { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
.channel-actions { display: flex; gap: 8px; }

.add-channel-card {
  background: rgba(99,102,241,0.05);
  border: 2px dashed rgba(99,102,241,0.3);
  border-radius: var(--radius);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 8px; min-height: 160px;
  color: #818cf8; cursor: pointer; font-size: 14px;
  transition: all 0.2s;
}
.add-channel-card:hover { background: rgba(99,102,241,0.1); border-color: #818cf8; }
.field-note { font-size: 12px; color: var(--warning); margin-top: 6px; }
</style>
