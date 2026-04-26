<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>⚙️ 系统设置</h1>
      <p class="subtitle">管理平台的全局配置，如 Cookie、代理等</p>
    </div>

    <div class="settings-container">
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>🌐 抖音配置</span>
            <el-button type="primary" size="small" @click="saveCookie" :loading="saving">保存配置</el-button>
          </div>
        </template>
        
        <el-form label-position="top">
          <el-form-item label="抖音 Cookie (dy_cookie)">
            <el-input
              v-model="cookie"
              type="textarea"
              :rows="6"
              placeholder="请粘贴从浏览器获取的完整 Cookie..."
            />
            <div class="input-tip">
              用于 API 鉴权的敏感信息。更新后下次采集任务将自动生效，无需重启后端。
            </div>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="settings-card mt-20">
        <template #header>
          <div class="card-header">
            <span>🤖 自动化工具：浏览器自动获取 Cookie</span>
          </div>
        </template>
        <div class="tool-section">
          <p class="tool-desc">
            点击下方按钮将启动一个临时的浏览器窗口。您只需在弹出的窗口中登录抖音，系统将自动捕获登录状态（含 HttpOnly Cookie）并完成同步。
          </p>
          <div class="bookmarklet-wrap">
            <el-button type="success" :loading="fetching" @click="handleAutoFetch">
              🚀 启动自动获取窗口
            </el-button>
          </div>
          <el-alert title="注意事项" type="warning" :closable="false" show-icon style="margin-top:12px">
            1. 需要在后端环境中安装 DrissionPage：<b>pip install DrissionPage</b><br/>
            2. 点击后请留意桌面是否弹出了新的 Chrome/Edge 窗口。<br/>
            3. 在弹出窗口中完成登录后，请稍等片刻，窗口会自动关闭并同步数据。
          </el-alert>
        </div>
      </el-card>

      <el-card class="settings-card mt-20">
        <div class="info-list">
          <div class="info-item">
            <span class="label">平台版本</span>
            <span class="value">v1.1.0</span>
          </div>
          <div class="info-item">
            <span class="label">运行模式</span>
            <span class="value">Production</span>
          </div>
          <div class="info-item">
            <span class="label">数据库状态</span>
            <span class="value success">Connected</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { settingApi } from '@/api'

const cookie = ref('')
const saving = ref(false)
const fetching = ref(false)

const loadSettings = async () => {
  try {
    const res = await settingApi.get('dy_cookie')
    cookie.value = res.value || ''
  } catch (err) {
    console.error('加载设置失败:', err)
  }
}

const handleAutoFetch = async () => {
  fetching.value = true
  ElMessage.info('正在启动自动化窗口，请留意您的任务栏...')
  try {
    const res = await settingApi.autoFetch()
    cookie.value = res.cookie
    ElMessage.success('自动同步成功！')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '自动化获取失败，请检查后端是否安装了 DrissionPage')
  } finally {
    fetching.value = false
  }
}

const saveCookie = async () => {
  if (!cookie.value) {
    return ElMessage.warning('请输入 Cookie 内容')
  }
  
  saving.value = true
  try {
    await settingApi.set('dy_cookie', {
      value: cookie.value,
      description: '抖音 Web 端 API 采集 Cookie'
    })
    ElMessage.success('配置已保存，下次采集任务将生效')
  } catch (err) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-page { max-width: 800px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }

.settings-card { border-radius: var(--radius); }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.input-tip { font-size: 12px; color: var(--text-secondary); margin-top: 8px; line-height: 1.5; }

.mt-20 { margin-top: 20px; }

.tool-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 16px; }
.bookmarklet-wrap { display: flex; justify-content: center; padding: 10px 0; }
.bookmark-btn {
  background: var(--el-color-primary);
  color: white;
  padding: 10px 24px;
  border-radius: 20px;
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
  cursor: grab;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transition: all 0.3s;
}
.bookmark-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4); }

.info-list { display: flex; flex-direction: column; gap: 12px; }
.info-item { display: flex; justify-content: space-between; font-size: 14px; }
.info-item .label { color: var(--text-secondary); }
.info-item .value { font-weight: 500; }
.info-item .value.success { color: var(--el-color-success); }
</style>
