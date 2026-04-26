<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-circle">
          <el-icon><VideoCameraFilled /></el-icon>
        </div>
        <h1>抖音采集平台</h1>
        <p>数据驱动 · 智启未来</p>
      </div>

      <el-form :model="form" :rules="rules" ref="loginForm" label-position="top" @keyup.enter="handleLogin">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
        </el-form-item>

        <div class="form-footer">
          <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
            立即登录
          </el-button>
        </div>
      </el-form>
      
      <div class="login-footer">
        <p>© 2024 Douyin Crawler Platform</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const loginForm = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginForm.value) return
  
  await loginForm.value.validate(async (valid) => {
    if (valid) {
      loading.ref = true
      try {
        await authStore.login(form)
        ElMessage.success('登录成功，欢迎回来')
        router.push('/')
      } catch (err) {
        // 报错由拦截器处理
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  overflow: hidden;
  position: relative;
}

.login-container::before {
  content: "";
  position: absolute;
  width: 400px;
  height: 400px;
  background: rgba(254, 44, 85, 0.2);
  border-radius: 50%;
  top: -100px;
  right: -100px;
  filter: blur(80px);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
  animation: fadeIn 0.8s ease-out;
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-circle {
  width: 60px;
  height: 60px;
  background: #fe2c55;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto 20px;
  font-size: 30px;
  color: white;
  box-shadow: 0 0 20px rgba(254, 44, 85, 0.5);
}

.login-header h1 {
  color: white;
  font-size: 24px;
  margin: 0;
  letter-spacing: 1px;
}

.login-header p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  margin-top: 8px;
}

:deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.8) !important;
}

:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.1) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-input__inner) {
  color: white !important;
}

.login-btn {
  width: 100%;
  height: 45px;
  border-radius: 10px;
  background: #fe2c55 !important;
  border: none !important;
  font-size: 16px;
  font-weight: 600;
  margin-top: 20px;
  transition: all 0.3s;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(254, 44, 85, 0.3);
}

.login-footer {
  margin-top: 40px;
  text-align: center;
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
