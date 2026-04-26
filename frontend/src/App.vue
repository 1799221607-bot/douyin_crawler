<template>
  <el-config-provider :locale="zhCn">
    <div class="app-layout">
      <!-- 侧边栏 -->
      <aside v-if="authStore.isLoggedIn" class="sidebar">
        <div class="sidebar-logo">
          <span class="logo-icon">🎬</span>
          <span class="logo-text">抖音采集</span>
        </div>
        <nav class="sidebar-nav">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ active: $route.path === item.path }"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </router-link>
          <!-- 仅管理员可见 -->
          <router-link v-if="authStore.isAdmin" to="/users" class="nav-item" :class="{ active: $route.path === '/users' }">
            <el-icon><UserFilled /></el-icon>
            <span>用户管理</span>
          </router-link>
        </nav>

        <!-- 用户头像与退出 -->
        <div class="user-section">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" class="avatar-pink">{{ authStore.user?.username?.charAt(0).toUpperCase() }}</el-avatar>
              <div class="user-meta">
                <span class="username">{{ authStore.user?.username }}</span>
                <span class="role-tag">{{ authStore.user?.role === 'admin' ? '管理员' : '用户' }}</span>
              </div>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="sidebar-footer">
          <div class="status-dot" :class="backendOnline ? 'online' : 'offline'"></div>
          <span>{{ backendOnline ? '服务运行中' : '服务离线' }}</span>
        </div>
      </aside>

      <!-- 主内容区 -->
      <main class="main-content" :class="{ 'full-width': !authStore.isLoggedIn }">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { statsApi } from '@/api'
import { useAuthStore } from '@/store/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const backendOnline = ref(false)

const navItems = [
  { path: '/dashboard', label: '仪表盘', icon: 'DataAnalysis' },
  { path: '/creators', label: '博主管理', icon: 'User' },
  { path: '/videos', label: '视频库', icon: 'VideoPlay' },
  { path: '/queue', label: '采集队列', icon: 'Timer' },
  { path: '/notifications', label: '通知配置', icon: 'Bell' },
  { path: '/logs', label: '采集日志', icon: 'Document' },
  { path: '/settings', label: '系统设置', icon: 'Setting' },
]

const handleCommand = (cmd) => {
  if (cmd === 'logout') {
    authStore.logout()
  } else if (cmd === 'password') {
    router.push('/settings')
  }
}

onMounted(async () => {
  if (authStore.isLoggedIn) {
    authStore.fetchUser()
  }
  try {
    await statsApi.get()
    backendOnline.value = true
  } catch {
    backendOnline.value = false
  }
})
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  min-width: 220px;
  background: #0d0d16;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 20px 0;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 100;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px 24px;
  border-bottom: 1px solid var(--border);
}
.logo-icon { font-size: 28px; }
.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #fe2c55, #ff7043);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}
.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.nav-item.active {
  background: rgba(254, 44, 85, 0.15);
  color: var(--primary);
}
.nav-item .el-icon { font-size: 18px; }

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}
.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
}
.status-dot.online { background: var(--success); box-shadow: 0 0 6px var(--success); }
.status-dot.offline { background: var(--danger); }

.main-content {
  margin-left: 220px;
  flex: 1;
  padding: 28px;
  min-height: 100vh;
}

.main-content.full-width {
  margin-left: 0;
  padding: 0;
}

.user-section {
  padding: 16px 12px;
  border-top: 1px solid var(--border);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.user-info:hover {
  background: var(--bg-hover);
}

.avatar-pink {
  background: #fe2c55 !important;
  color: white !important;
  font-weight: bold;
}

.user-meta {
  display: flex;
  flex-direction: column;
  flex: 1;
  max-width: 100px;
}

.username {
  font-size: 14px;
  color: white;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-tag {
  font-size: 10px;
  color: #909399;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
