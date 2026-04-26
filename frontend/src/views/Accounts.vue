<template>
  <div class="accounts-container">
    <div class="page-header">
      <div class="header-left">
        <h2>🔑 账号池管理</h2>
        <p class="subtitle">管理多平台采集账号，确保 Cookie 存活与负载均衡</p>
      </div>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>添加账号
      </el-button>
    </div>

    <el-card class="table-card">
      <el-tabs v-model="activePlatform" @tab-change="fetchAccounts">
        <el-tab-pane label="🎵 抖音" name="douyin" />
      </el-tabs>

      <el-table :data="accounts" v-loading="loading" style="width: 100%">
        <el-table-column label="平台" width="100">
          <template #default="{ row }">
            <el-tag type="danger">抖音</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="账号备注" width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status].type">{{ statusMap[row.status].label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="proxy_url" label="绑定代理" show-overflow-tooltip />
        <el-table-column prop="fail_count" label="失败次数" width="100" align="center">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.fail_count > 0 }">{{ row.fail_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="最后使用" width="180">
          <template #default="{ row }">
            {{ row.last_used_at ? formatTime(row.last_used_at) : '从未' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑账号' : '添加账号'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="平台" required>
          <el-select v-model="form.platform" placeholder="选择平台" :disabled="isEdit">
            <el-option label="抖音" value="douyin" />
          </el-select>
        </el-form-item>
        <el-form-item label="账号备注" required>
          <el-input v-model="form.username" placeholder="如：工作号01" />
        </el-form-item>
        <el-form-item label="Cookie" required>
          <el-input v-model="form.cookie" type="textarea" :rows="4" placeholder="粘贴完整的 Cookie 字符串" />
          <div style="margin-top: 8px;">
            <el-button type="success" size="small" plain @click="handleAutoFetch" :loading="fetchingCookie">
              <el-icon style="margin-right:4px"><Pointer /></el-icon>启动浏览器自动登录获取
            </el-button>
            <span class="input-tip-mini">点击后请在弹出的浏览器中登录抖音</span>
          </div>
        </el-form-item>
        <el-form-item label="固定代理">
          <el-input v-model="form.proxy_url" placeholder="http://user:pass@host:port" />
        </el-form-item>
        <el-form-item label="User-Agent">
          <el-input v-model="form.ua" placeholder="不填则使用系统默认" />
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态">
          <el-select v-model="form.status">
            <el-option label="正常" value="active" />
            <el-option label="失效" value="expired" />
            <el-option label="异常" value="error" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Pointer } from '@element-plus/icons-vue'
import request, { settingApi } from '@/api'

const loading = ref(false)
const accounts = ref([])
const activePlatform = ref('douyin')
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const fetchingCookie = ref(false)

const form = ref({
  platform: 'douyin',
  username: '',
  cookie: '',
  proxy_url: '',
  ua: '',
  status: 'active'
})

const statusMap = {
  active: { label: '正常', type: 'success' },
  expired: { label: '已过期', type: 'warning' },
  banned: { label: '被封禁', type: 'danger' },
  error: { label: '异常', type: 'info' }
}

const fetchAccounts = async () => {
  loading.value = true
  try {
    const res = await request.get('/accounts', { params: { platform: activePlatform.value } })
    accounts.value = res.data
  } catch (err) {
    ElMessage.error('获取账号列表失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = { platform: 'douyin', username: '', cookie: '', proxy_url: '', ua: '', status: 'active' }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

const handleAutoFetch = async () => {
  fetchingCookie.value = true
  ElMessage.info('正在启动自动化窗口，请在弹出的浏览器中完成登录...')
  try {
    const res = await settingApi.autoFetch()
    form.value.cookie = res.cookie
    ElMessage.success('Cookie 获取成功！')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '自动化获取失败，请确保后端已安装 DrissionPage')
  } finally {
    fetchingCookie.value = false
  }
}

const submitForm = async () => {
  try {
    if (isEdit.value) {
      await request.put(`/accounts/${editingId.value}`, form.value)
      ElMessage.success('账号已更新')
    } else {
      await request.post('/accounts', form.value)
      ElMessage.success('账号已添加')
    }
    dialogVisible.value = false
    fetchAccounts()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该账号吗？', '提示', { type: 'warning' }).then(async () => {
    await request.delete(`/accounts/${row.id}`)
    ElMessage.success('账号已删除')
    fetchAccounts()
  })
}

const formatTime = (iso) => {
  return new Date(iso).toLocaleString()
}

onMounted(fetchAccounts)
</script>

<style scoped>
.accounts-container {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.subtitle {
  color: #909399;
  font-size: 14px;
  margin-top: 4px;
}

.table-card {
  border-radius: 12px;
}

.text-danger {
  color: #f56c6c;
  font-weight: bold;
}

.input-tip-mini {
  font-size: 11px;
  color: #909399;
  margin-left: 10px;
}
</style>
