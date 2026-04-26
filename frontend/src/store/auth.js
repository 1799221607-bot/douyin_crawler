import { defineStore } from 'pinia'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
  },
  actions: {
    async login(loginData) {
      const res = await authApi.login(loginData)
      this.token = res.access_token
      this.user = res.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
      return res
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    },
    async fetchUser() {
      try {
        const user = await authApi.me()
        this.user = user
        localStorage.setItem('user', JSON.stringify(user))
      } catch (err) {
        this.logout()
      }
    }
  }
})
