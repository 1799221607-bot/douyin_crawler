<template>
  <div class="videos-page">
    <div class="page-header">
      <div class="header-left">
        <h1>🎬 视频库</h1>
        <p class="subtitle">共 {{ total }} 条视频</p>
      </div>
      <div class="header-right">
        <el-button 
          :type="isManageMode ? 'warning' : 'default'" 
          :icon="isManageMode ? Close : Operation"
          size="small"
          @click="toggleManageMode"
        >
          {{ isManageMode ? '取消管理' : '批量管理' }}
        </el-button>
        <el-button type="primary" :icon="Refresh" size="small" @click="fetchVideos">刷新</el-button>
      </div>
    </div>
    
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filterCreatorId" placeholder="按博主筛选" clearable @change="onSearch" style="width: 200px">
        <el-option v-for="c in creatorOptions" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索视频标题..."
        :prefix-icon="Search"
        clearable
        @keyup.enter="onSearch"
        @clear="onSearch"
        style="width: 300px"
      >
        <template #append>
          <el-button @click="onSearch">搜索</el-button>
        </template>
      </el-input>
    </div>

    <!-- 分类标签页 -->
    <el-tabs v-model="activeTab" class="video-tabs" @tab-change="onTabChange">
      <el-tab-pane label="🔥 今日上新" name="today">
        <div v-if="loading" class="loading-wrap">
          <el-skeleton :rows="4" animated />
        </div>
        <div v-else-if="videos.length > 0" class="videos-grid">
          <div v-for="v in videos" :key="v.aweme_id"
            class="video-card hover-card" @click="openPlayer(v)">
            <!-- 封面图区域 -->
            <div class="video-cover">
              <img v-if="v.cover_url" :src="v.cover_url" :alt="v.title"
                @error="(e) => e.target.style.display='none'" />
              <div class="cover-placeholder" v-else>
                <el-icon :size="32"><VideoPlay /></el-icon>
              </div>
              <div class="video-duration" v-if="v.duration">{{ formatDuration(v.duration) }}</div>
              <div class="video-badges">
                <span v-if="v.downloaded" class="badge badge-success">已下载</span>
                <span v-if="v.ai_processed" class="badge badge-ai">AI</span>
              </div>
              <div class="play-overlay">
                <el-icon :size="40"><VideoPlay /></el-icon>
              </div>
              <!-- 管理模式下的勾选框 -->
              <div class="video-checkbox" v-if="isManageMode" @click.stop>
                <el-checkbox v-model="selectedIds" :label="v.aweme_id"><span></span></el-checkbox>
              </div>
              <!-- 单个删除按钮 -->
              <div class="video-delete-btn" @click.stop="handleDelete(v)">
                <el-icon><Delete /></el-icon>
              </div>
            </div>
            <!-- 信息区域 -->
            <div class="video-info">
              <div class="video-title" :title="v.title">{{ v.title || '（无标题）' }}</div>
              <div class="video-meta">
                <span class="video-creator">{{ v.creator_name }}</span>
                <div class="meta-stats">
                  <span>❤️ {{ formatNum(v.like_count) }}</span>
                  <span>💬 {{ formatNum(v.comment_count) }}</span>
                </div>
                <div class="video-date-row">
                  <el-icon><Calendar /></el-icon>
                  <span class="video-date">{{ formatDate(v.published_at) }}</span>
                </div>
                <!-- 列表页 AI 摘要预览 -->
                <div class="video-ai-preview" v-if="v.ai_summary">
                  <span class="ai-tag-mini">AI</span>
                  {{ v.ai_summary.summary }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="今日暂无新视频" :image-size="120" />
      </el-tab-pane>

      <el-tab-pane label="📜 历史档案" name="history">
        <div v-if="loading" class="loading-wrap">
          <el-skeleton :rows="4" animated />
        </div>
        <div v-else-if="videos.length > 0" class="videos-grid">
          <!-- 同样的视频卡片循环 -->
          <div v-for="v in videos" :key="v.aweme_id"
            class="video-card hover-card" @click="openPlayer(v)">
            <div class="video-cover">
              <img v-if="v.cover_url" :src="v.cover_url" :alt="v.title" />
              <div class="video-duration" v-if="v.duration">{{ formatDuration(v.duration) }}</div>
              <div class="video-badges">
                <span v-if="v.downloaded" class="badge badge-success">已下载</span>
                <span v-if="v.ai_processed" class="badge badge-ai">AI</span>
              </div>
              <div class="play-overlay"><el-icon :size="40"><VideoPlay /></el-icon></div>
              <div class="video-checkbox" v-if="isManageMode" @click.stop>
                <el-checkbox v-model="selectedIds" :label="v.aweme_id"><span></span></el-checkbox>
              </div>
              <div class="video-delete-btn" @click.stop="handleDelete(v)">
                <el-icon><Delete /></el-icon>
              </div>
            </div>
            <div class="video-info">
              <div class="video-title">{{ v.title || '（无标题）' }}</div>
              <div class="video-meta">
                <span class="video-creator">{{ v.creator_name }}</span>
                <div class="meta-stats">
                  <span>❤️ {{ formatNum(v.like_count) }}</span>
                  <span>💬 {{ formatNum(v.comment_count) }}</span>
                </div>
                <div class="video-date-row">
                  <el-icon><Calendar /></el-icon>
                  <span class="video-date">{{ formatDate(v.published_at) }}</span>
                </div>
                <!-- 列表页 AI 摘要预览 -->
                <div class="video-ai-preview" v-if="v.ai_summary">
                  <span class="ai-tag-mini">AI</span>
                  {{ v.ai_summary.summary }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无历史数据" :image-size="120" />
      </el-tab-pane>
    </el-tabs>

    <!-- 批量管理浮动工具栏 -->
    <transition name="el-zoom-in-bottom">
      <div class="batch-toolbar" v-if="isManageMode && selectedIds.length > 0">
        <div class="toolbar-info">
          已选中 <span>{{ selectedIds.length }}</span> 个视频
        </div>
        <div class="toolbar-actions">
          <el-button @click="selectedIds = []">取消选择</el-button>
          <el-button type="danger" :icon="Delete" @click="handleBatchDelete">批量删除</el-button>
        </div>
      </div>
    </transition>

    <!-- 分页 (现在它是针对当前 Tab 的总数) -->
    <div class="pagination-wrap" v-if="total > 0">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, total"
        @current-change="loadVideos"
        background
      />
    </div>

    <!-- 视频播放对话框 -->
    <el-dialog v-model="showPlayer" :title="currentVideo?.title || '视频播放'" 
      width="600px"
      destroy-on-close @close="closePlayer" @opened="onPlayerOpened">
      <div class="player-modal-content">
        <div class="player-wrap-centered">
          <video ref="videoEl" class="plyr-video" controls playsinline referrerpolicy="no-referrer"></video>
        </div>
        <div class="video-detail-info" v-if="currentVideo">
          <div class="detail-stats">
            <span>❤️ {{ formatNum(currentVideo.like_count) }}</span>
            <span>💬 {{ formatNum(currentVideo.comment_count) }}</span>
            <span>↗️ {{ formatNum(currentVideo.share_count) }}</span>
          </div>
          <div class="detail-time">
            发布于 {{ formatDate(currentVideo.published_at) }}
          </div>
          <p class="video-desc">{{ currentVideo.desc }}</p>
          
          <div class="ai-summary-box" v-if="currentVideo.downloaded">
            <div class="ai-box-header">
              <span class="ai-box-title">🤖 AI 核心总结</span>
              <el-button size="small" type="primary" text :icon="Refresh" 
                @click="triggerAI(currentVideo.aweme_id)">更新</el-button>
            </div>
            
            <div v-if="currentVideo.ai_summary" class="ai-box-content">
              <p>{{ currentVideo.ai_summary.summary }}</p>
              <div class="ai-box-tags">
                <el-tag v-for="kw in parseKeywords(currentVideo.ai_summary.keywords)"
                  :key="kw" size="small" effect="plain">{{ kw }}</el-tag>
              </div>
            </div>
            <div v-else class="ai-box-empty">尚未生成 AI 总结，点击更新开始分析</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, Calendar, Operation, Close, Delete, Refresh, Search } from '@element-plus/icons-vue'
import Plyr from 'plyr'
import { videoApi, aiApi, creatorApi } from '@/api'
import request from '@/api'

const route = useRoute()
const videos = ref([])
const loading = ref(true)
const page = ref(1)
const pageSize = 24
const total = ref(0)
const searchKeyword = ref('')
const filterCreatorId = ref(null)
const activeTab = ref('today') // 默认显示今日
const creatorOptions = ref([])
const showPlayer = ref(false)
const currentVideo = ref(null)
const videoEl = ref(null)
let player = null

const isManageMode = ref(false)
const selectedIds = ref([])

const toggleManageMode = () => {
  isManageMode.value = !isManageMode.value
  selectedIds.value = []
}

const handleDelete = async (video) => {
  try {
    await ElMessageBox.confirm('确定要删除该视频吗？（本地文件将同步清理）', '提示', { type: 'warning' })
    await request.delete(`/videos/${video.aweme_id}`)
    ElMessage.success('已删除')
    loadVideos()
  } catch {}
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 个视频吗？`, '警告', { type: 'danger' })
    await request.post('/videos/batch-delete', { aweme_ids: selectedIds.value })
    ElMessage.success('批量删除成功')
    isManageMode.value = false
    selectedIds.value = []
    loadVideos()
  } catch {}
}

// 视频逻辑分组
const todayVideos = computed(() => {
  const today = new Date().toDateString()
  return videos.value.filter(v => {
    if (!v.created_at) return false
    return new Date(v.created_at).toDateString() === today
  })
})

const historyVideos = computed(() => {
  const today = new Date().toDateString()
  return videos.value.filter(v => {
    if (!v.created_at) return true
    return new Date(v.created_at).toDateString() !== today
  })
})

const formatDuration = (s) => {
  const mins = Math.floor(s / 60)
  const secs = Math.floor(s % 60)
  return `${mins}:${String(secs).padStart(2, '0')}`
}
const formatNum = (n) => n >= 10000 ? `${(n/10000).toFixed(1)}w` : (n ?? '—')
const formatDate = (iso) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '—'
const parseKeywords = (kw) => {
  try { return typeof kw === 'string' ? JSON.parse(kw) : kw } catch { return [] }
}

const loadVideos = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize,
      keyword: searchKeyword.value || undefined,
      creator_id: filterCreatorId.value || route.query.creator_id || undefined,
      downloaded: true,
      period: activeTab.value // 传入当前 Tab 对应的周期
    }
    const res = await videoApi.list(params)
    videos.value = res.data || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

const loadCreators = async () => {
  try {
    const res = await creatorApi.list()
    creatorOptions.value = res.data || []
  } catch {}
}

const initPage = () => {
  if (route.query.creator_id) {
    filterCreatorId.value = parseInt(route.query.creator_id)
  }
  loadCreators()
  loadVideos()
}

const onSearch = () => { page.value = 1; loadVideos() }

const onTabChange = () => {
  page.value = 1
  loadVideos()
}

const openPlayer = (video) => {
  currentVideo.value = video
  showPlayer.value = true
}

const onPlayerOpened = () => {
  if (videoEl.value && currentVideo.value) {
    const src = currentVideo.value.downloaded
      ? videoApi.streamUrl(currentVideo.value.aweme_id)
      : currentVideo.value.play_url
    if (player) { player.destroy(); player = null }
    player = new Plyr(videoEl.value, { controls: ['play','progress','current-time','mute','volume','fullscreen'] })
    videoEl.value.src = src
    player.play().catch(e => console.warn('Auto-play blocked:', e))
  }
}

const closePlayer = () => {
  if (player) { player.destroy(); player = null }
  currentVideo.value = null
}

const triggerAI = async (awemeId) => {
  try {
    await aiApi.trigger(awemeId)
    ElMessage.success('AI 总结任务已提交，完成后将推送通知')
  } catch {}
}

onMounted(initPage)
watch(() => route.query, initPage)
</script>

<style scoped>
.videos-page { 
  width: 100%; 
  padding: 0 10px;
}
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 12px;
}

.video-section { margin-bottom: 30px; }
.section-header { 
  display: flex; align-items: center; gap: 8px; 
  margin-bottom: 12px; padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}
.section-header h2 { font-size: 16px; font-weight: 700; margin: 0; }
.header-icon { font-size: 18px; }
.history-section { margin-top: 20px; opacity: 0.9; }

.video-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  cursor: pointer;
}

.video-cover {
  position: relative;
  aspect-ratio: 9/16;
  background: #1a1a2e;
  overflow: hidden;
}
.video-cover img {
  width: 100%; height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}
.video-card:hover .video-cover img { transform: scale(1.05); }
.cover-placeholder {
  height: 100%;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-secondary);
}
.play-overlay {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.4);
  color: white; opacity: 0;
  transition: opacity 0.2s;
}
.video-card:hover .play-overlay { opacity: 1; }
.video-duration {
  position: absolute; bottom: 4px; right: 4px;
  background: rgba(0,0,0,0.7);
  color: white; font-size: 10px;
  padding: 1px 4px; border-radius: 3px;
}
.video-badges {
  position: absolute; top: 4px; left: 4px;
  display: flex; gap: 3px;
}
.badge {
  padding: 1px 4px; border-radius: 3px;
  font-size: 9px; font-weight: 600;
}
.badge-success { background: rgba(0,197,102,0.8); color: white; }
.badge-ai { background: rgba(99,102,241,0.8); color: white; }

.video-info { padding: 8px 10px; }
.video-title {
  font-size: 12px; font-weight: 500; line-height: 1.3;
  overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  height: 2.6em;
}
.video-meta { 
  display: flex; flex-direction: column; gap: 2px;
  margin-top: 4px;
}
.video-creator { color: var(--el-color-primary); font-weight: 600; font-size: 11px; margin-bottom: 1px; }
.meta-stats { display: flex; gap: 6px; font-size: 10px; opacity: 0.8; }
.video-date-row { 
  display: flex; align-items: center; gap: 4px; 
  font-size: 10px; opacity: 0.7; margin-top: 2px;
}

.detail-info-row {
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}
.info-label { opacity: 0.8; }
.info-value { color: var(--text-primary); font-weight: 500; }

.pagination-wrap { display: flex; justify-content: center; margin-top: 28px; }

.player-modal-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.player-wrap-centered {
  width: 100%;
  background: #000;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  max-height: 60vh; /* 弹窗模式下的限制 */
}

/* 关键修复：全屏模式下彻底释放所有高度限制 */
:fullscreen .player-wrap-centered,
:-webkit-full-screen .player-wrap-centered,
.plyr--fullscreen-active .player-wrap-centered {
  max-height: none !important;
  height: 100vh !important;
  width: 100vw !important;
  border-radius: 0 !important;
}

:fullscreen video,
:-webkit-full-screen video,
.plyr--fullscreen-active video {
  max-height: 100vh !important;
  height: 100vh !important;
  width: 100vw !important;
  object-fit: contain !important;
}

.player-wrap-centered :deep(.plyr) {
  width: 100%;
  height: 100%;
}

.player-wrap-centered :deep(video) {
  max-height: 60vh;
  width: auto !important;
  margin: 0 auto;
}

.video-detail-info {
  padding: 0 10px;
}

.detail-stats {
  display: flex;
  gap: 20px;
  font-size: 15px;
  margin-bottom: 8px;
  color: var(--text-primary);
  font-weight: 600;
}

.detail-time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.video-desc {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: 20px;
  white-space: pre-wrap;
}

.ai-summary-box {
  background: var(--bg-card);
  border: 1px solid var(--el-color-primary-light-8);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.05);
}

.ai-box-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.ai-box-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--el-color-primary);
}

.ai-box-content p {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.ai-box-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-box-empty {
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
  padding: 10px 0;
}

.video-ai-preview {
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  background: rgba(99, 102, 241, 0.05);
  padding: 4px 6px;
  border-radius: 4px;
}
.ai-tag-mini {
  background: var(--el-color-primary);
  color: white;
  font-size: 9px;
  padding: 0 3px;
  border-radius: 2px;
  margin-right: 4px;
  font-weight: bold;
}
.loading-wrap { padding: 40px 0; }

/* 批量管理样式 */
.header-right { display: flex; gap: 10px; }
.video-checkbox {
  position: absolute; top: 8px; left: 8px;
  z-index: 10;
  background: white; border-radius: 4px;
  width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
}
.video-delete-btn {
  position: absolute; top: 8px; right: 8px;
  z-index: 10;
  width: 28px; height: 28px;
  background: rgba(245,108,108,0.9);
  color: white; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.2s;
  cursor: pointer;
}
.video-card:hover .video-delete-btn { opacity: 1; }

.batch-toolbar {
  position: fixed; bottom: 30px; left: 50%;
  transform: translateX(-50%);
  background: var(--bg-card);
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  border: 1px solid var(--el-color-primary);
  border-radius: 40px;
  padding: 10px 24px;
  display: flex; align-items: center; gap: 24px;
  z-index: 1000;
}
.toolbar-info { font-size: 14px; font-weight: 500; }
.toolbar-info span { color: var(--el-color-primary); font-size: 18px; font-weight: 700; margin: 0 4px; }
.toolbar-actions { display: flex; gap: 12px; }
</style>

<!-- 全局样式：解决全屏模式下的显示问题 -->
<style>
/* 强制解除全屏时的所有容器限制 */
.plyr--fullscreen-active, 
.plyr--fullscreen-active .plyr__video-wrapper,
.plyr--fullscreen-active video {
  max-height: none !important;
  max-width: none !important;
  height: 100vh !important;
  width: 100vw !important;
  object-fit: contain !important;
  background: #000 !important;
}

/* 确保 Plyr 控制条在全屏时可见 */
.plyr--fullscreen-active .plyr__controls {
  z-index: 2147483647 !important;
}
</style>
