import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表盘' }
  },
  {
    path: '/creators',
    name: 'Creators',
    component: () => import('@/views/Creators.vue'),
    meta: { title: '博主管理' }
  },
  {
    path: '/videos',
    name: 'Videos',
    component: () => import('@/views/Videos.vue'),
    meta: { title: '视频库' }
  },
  {
    path: '/queue',
    name: 'Queue',
    component: () => import('@/views/Queue.vue'),
    meta: { title: '采集队列' }
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/views/Notifications.vue'),
    meta: { title: '通知配置' }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('@/views/Logs.vue'),
    meta: { title: '采集日志' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('@/views/Users.vue'),
    meta: { title: '用户管理', admin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导航守卫：防止未登录访问私有页面
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  // 如果不是公共页面且没有 token，跳转到登录页
  if (!to.meta.public && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    // 如果已登录还访问登录页，跳转到首页
    next('/dashboard')
  } else {
    next()
  }
})

router.afterEach((to) => {
  document.title = `${to.meta.title || ''} — 抖音采集平台`
})

export default router
