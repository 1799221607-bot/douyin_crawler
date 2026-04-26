<template>
  <div class="creators-page">
    <div class="page-header">
      <div>
        <h1>👤 博主管理</h1>
        <p class="subtitle">管理采集目标，调整采集频率</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="showAddDialog = true">添加博主</el-button>
    </div>

    <!-- 博主卡片列表 -->
    <div v-if="loading" class="loading-wrap">
      <el-skeleton :rows="3" animated />
    </div>
    <div v-else class="creators-grid">
      <div v-for="c in creators" :key="c.id" class="creator-card hover-card">
        <div class="creator-header">
          <div class="creator-avatar">
            <img v-if="c.avatar_url" :src="c.avatar_url" alt="avatar" />
            <span v-else>{{ c.name[0] }}</span>
          </div>
          <div class="creator-info">
            <div class="creator-name">{{ c.name }}</div>
            <div class="creator-meta">
              <el-tag :type="c.enabled ? 'success' : 'info'" size="small">
                {{ c.enabled ? '采集中' : '已暂停' }}
              </el-tag>
              <span class="interval-text">每 {{ c.interval_min }} 分钟</span>
            </div>
          </div>
          <el-dropdown @command="(cmd) => handleCommand(cmd, c)">
            <el-button text :icon="MoreFilled" circle />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="run">立即采集</el-dropdown-item>
                <el-dropdown-item :command="c.enabled ? 'pause' : 'resume'">
                  {{ c.enabled ? '暂停' : '恢复' }}
                </el-dropdown-item>
                <el-dropdown-item command="edit">编辑博主</el-dropdown-item>
                <el-dropdown-item command="videos">查看视频</el-dropdown-item>
                <el-dropdown-item command="delete" class="danger-item">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="creator-stats">
          <div class="stat-item">
            <span class="stat-val">{{ c.follower_count ? formatNum(c.follower_count) : '—' }}</span>
            <span class="stat-lbl">粉丝</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-val">{{ c.interval_min }}m</span>
            <span class="stat-lbl">采集间隔</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-val">{{ c.download_video ? '是' : '否' }}</span>
            <span class="stat-lbl">下载视频</span>
          </div>
        </div>

        <div class="creator-footer">
          <span class="time-text">
            上次采集：{{ c.last_run_at ? formatTime(c.last_run_at) : '未采集' }}
          </span>
          <span class="time-text" v-if="c.next_run_at">
            下次：{{ formatTime(c.next_run_at) }}
          </span>
        </div>
      </div>

      <div class="add-card hover-card" @click="showAddDialog = true">
        <el-icon :size="32"><Plus /></el-icon>
        <span>添加博主</span>
      </div>
    </div>

    <!-- 添加博主对话框 -->
    <el-dialog v-model="showAddDialog" title="添加博主" width="480px">
      <el-form :model="addForm" label-width="100px" label-position="left">
        <el-form-item label="博主昵称" required>
          <el-input v-model="addForm.name" placeholder="例：技术博主张三" />
        </el-form-item>
        <el-form-item label="主页 URL" required>
          <el-input v-model="addForm.user_url" placeholder="https://www.douyin.com/user/..." />
        </el-form-item>
        <el-form-item label="采集间隔">
          <el-input-number v-model="addForm.interval_min" :min="5" :max="1440" />
          <span style="margin-left:8px;color:var(--text-secondary)">分钟</span>
        </el-form-item>
        <el-form-item label="下载视频">
          <el-switch v-model="addForm.download_video" />
        </el-form-item>
        <el-form-item label="立即启用">
          <el-switch v-model="addForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleAdd">确认添加</el-button>
      </template>
    </el-dialog>

    <!-- 编辑博主对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑博主信息" width="480px">
      <el-form :model="editForm" label-width="100px" label-position="left">
        <el-form-item label="博主昵称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="主页 URL">
          <el-input v-model="editForm.user_url" placeholder="支持粘贴分享文案" />
        </el-form-item>
        <el-form-item label="采集间隔">
          <el-input-number v-model="editForm.interval_min" :min="5" :max="1440" />
          <span style="margin-left:8px;color:var(--text-secondary)">分钟</span>
        </el-form-item>
        <el-form-item label="下载视频">
          <el-switch v-model="editForm.download_video" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleUpdate">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled } from '@element-plus/icons-vue'
import { creatorApi } from '@/api'

const router = useRouter()
const creators = ref([])
const loading = ref(true)
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const submitting = ref(false)
const editingCreator = ref(null)

const addForm = ref({
  name: '', user_url: '', interval_min: 60, download_video: true, enabled: true
})

const editForm = ref({
  name: '', user_url: '', interval_min: 60, download_video: true
})

const formatTime = (iso) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '—'
const formatNum = (n) => n >= 10000 ? `${(n / 10000).toFixed(1)}w` : n

const loadCreators = async () => {
  loading.value = true
  try {
    const res = await creatorApi.list()
    creators.value = res.data || []
  } finally {
    loading.value = false
  }
}

const handleAdd = async () => {
  if (!addForm.value.name || !addForm.value.user_url) {
    ElMessage.warning('请填写博主昵称和主页 URL')
    return
  }
  submitting.value = true
  try {
    await creatorApi.create(addForm.value)
    ElMessage.success('添加成功，采集任务已启动')
    showAddDialog.value = false
    addForm.value = { name: '', user_url: '', interval_min: 60, download_video: true, enabled: true }
    await loadCreators()
  } finally {
    submitting.value = false
  }
}

const handleCommand = async (cmd, creator) => {
  if (cmd === 'run') {
    await creatorApi.runNow(creator.id)
    ElMessage.success('采集任务已触发')
  } else if (cmd === 'pause') {
    await creatorApi.pause(creator.id)
    await creatorApi.update(creator.id, { enabled: false })
    ElMessage.success('已暂停')
    await loadCreators()
  } else if (cmd === 'resume') {
    await creatorApi.resume(creator.id)
    await creatorApi.update(creator.id, { enabled: true })
    ElMessage.success('已恢复')
    await loadCreators()
  } else if (cmd === 'edit') {
    editingCreator.value = creator
    editForm.value = {
      name: creator.name,
      user_url: creator.user_url,
      interval_min: creator.interval_min,
      download_video: creator.download_video
    }
    showEditDialog.value = true
  } else if (cmd === 'videos') {
    router.push({ path: '/videos', query: { creator_id: creator.id } })
  } else if (cmd === 'delete') {
    await ElMessageBox.confirm(`确认删除博主「${creator.name}」？`, '提示', { type: 'warning' })
    await creatorApi.delete(creator.id)
    ElMessage.success('已删除')
    await loadCreators()
  }
}

const handleUpdate = async () => {
  submitting.value = true
  try {
    await creatorApi.update(editingCreator.value.id, editForm.value)
    ElMessage.success('修改成功')
    showEditDialog.value = false
    await loadCreators()
  } finally {
    submitting.value = false
  }
}

onMounted(loadCreators)
</script>

<style scoped>
.creators-page { max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }

.creators-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.creator-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
}

.creator-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.creator-avatar {
  width: 44px; height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #fe2c55, #ff7043);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700; color: white;
  overflow: hidden; flex-shrink: 0;
}
.creator-avatar img { width: 100%; height: 100%; object-fit: cover; }
.creator-info { flex: 1; min-width: 0; }
.creator-name { font-weight: 600; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.creator-meta { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.interval-text { font-size: 12px; color: var(--text-secondary); }

.creator-stats {
  display: flex;
  align-items: center;
  background: rgba(255,255,255,0.03);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}
.stat-item { flex: 1; text-align: center; }
.stat-val { display: block; font-weight: 600; font-size: 16px; }
.stat-lbl { font-size: 11px; color: var(--text-secondary); margin-top: 2px; display: block; }
.stat-divider { width: 1px; height: 30px; background: var(--border); }

.creator-footer {
  display: flex; justify-content: space-between;
  font-size: 12px; color: var(--text-secondary);
}

.add-card {
  background: rgba(254,44,85,0.05);
  border: 2px dashed rgba(254,44,85,0.3);
  border-radius: var(--radius);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 8px; min-height: 180px;
  color: var(--primary); cursor: pointer;
  font-size: 14px; font-weight: 500;
  transition: all 0.2s;
}
.add-card:hover { background: rgba(254,44,85,0.1); border-color: var(--primary); }
.loading-wrap { padding: 40px 0; }
.danger-item { color: var(--danger) !important; }
</style>
