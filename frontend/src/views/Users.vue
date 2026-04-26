<template>
  <div class="users-page">
    <div class="page-header">
      <div>
        <h1>👥 用户管理</h1>
        <p class="subtitle">管理系统账号及权限控制</p>
      </div>
      <el-button type="primary" icon="Plus" @click="showAddDialog = true">添加用户</el-button>
    </div>

    <el-card class="table-card">
      <el-table :data="users" v-loading="loading" style="width: 100%" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="role" label="角色">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center">
          <template #default="{ row }">
            <el-popconfirm title="确定删除该用户吗？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link icon="Delete" :disabled="row.username === 'admin'">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加用户弹窗 -->
    <el-dialog v-model="showAddDialog" title="添加新用户" width="400px">
      <el-form :model="addForm" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="addForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input v-model="addForm.password" type="password" placeholder="请输入初始密码" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="addForm.role" style="width: 100%">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleAddUser">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { userApi } from '@/api'
import { ElMessage } from 'element-plus'

const users = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const submitting = ref(false)

const addForm = ref({
  username: '',
  password: '',
  role: 'user'
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await userApi.list()
    users.value = res.data
  } finally {
    loading.value = false
  }
}

const handleAddUser = async () => {
  if (!addForm.value.username || !addForm.value.password) {
    return ElMessage.warning('请填写完整信息')
  }
  submitting.value = true
  try {
    await userApi.create(addForm.value)
    ElMessage.success('用户创建成功')
    showAddDialog.value = false
    addForm.value = { username: '', password: '', role: 'user' }
    fetchUsers()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await userApi.delete(id)
    ElMessage.success('用户已删除')
    fetchUsers()
  } catch (err) {}
}

onMounted(fetchUsers)
</script>

<style scoped>
.users-page { width: 100%; }
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
</style>
