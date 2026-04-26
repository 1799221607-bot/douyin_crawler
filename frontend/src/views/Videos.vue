<template>
  <div class="videos-page">
    <div class="page-header">
      <div>
        <h1>🎬 视频库</h1>
        <p class="subtitle">共 {{ total }} 条视频</p>
      </div>
      <div class="filters">
        <el-select v-model="filterCreatorId" placeholder="全部博主" clearable style="width:160px; margin-right:12px" @change="onSearch">
          <el-option v-for="c in creatorOptions" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-input v-model="searchKeyword" placeholder="搜索标题..." clearable
          style="width:180px" @change="onSearch" />
      </div>
    </div>

    <!-- 视频网格 -->
    <div v-if="loading" class="loading-wrap">
      <el-skeleton :rows="4" animated />
    </div>
    <div v-else class="videos-grid">
      <div v-for="v in videos" :key="v.aweme_id"
        class="video-card hover-card" @click="openPlayer(v)">
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
        </div>
        <div class="video-info">
          <div class="video-title" :title="v.title">{{ v.title || '（无标题）' }}</div>
          <div class="video-meta">
            <span class="video-creator">{{ v.creator_name }}</span>
            <div class="meta-stats">
              <span>❤️ {{ formatNum(v.like_count) }}</span>
              <span>💬 {{ formatNum(v.comment_count) }}</span>
            </div>
            <span class="video-date">{{ formatDate(v.published_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrap">
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
    <el-dialog v-model="showPlayer" :title="currentVideo?.title || '视频播放'" width="800px"
      destroy-on-close @close="closePlayer" @opened="onPlayerOpened">
      <div class="player-wrap">
        <video ref="videoEl" class="plyr-video" controls playsinline referrerpolicy="no-referrer"></video>
      </div>
      <div class="video-detail" v-if="currentVideo">
        <div class="detail-stats">
          <span>❤️ {{ formatNum(currentVideo.like_count) }}</span>
          <span>💬 {{ formatNum(currentVideo.comment_count) }}</span>
          <span>↗️ {{ formatNum(currentVideo.share_count) }}</span>
        </div>
        <p class="video-desc">{{ currentVideo.desc }}</p>
        <div class="ai-section" v-if="currentVideo.ai_summary">
          <div class="ai-badge">🤖 AI 总结</div>
          <p class="ai-summary">{{ currentVideo.ai_summary.summary }}</p>
          <div class="ai-keywords" v-if="currentVideo.ai_summary.keywords?.length">
            <el-tag v-for="kw in parseKeywords(currentVideo.ai_summary.keywords)"
              :key="kw" size="small" style="margin-right:6px">{{ kw }}</el-tag>
          </div>
        </div>
        <div class="ai-section" v-else-if="currentVideo.downloaded">
          <el-button size="small" @click="triggerAI(currentVideo.aweme_id)">
            🤖 生成 AI 总结
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import Plyr from 'plyr'
import { videoApi, aiApi, creatorApi } from '@/api'

const route = useRoute()
const videos = ref([])
const loading = ref(true)
const page = ref(1)
const pageSize = 24
const total = ref(0)
const searchKeyword = ref('')
const filterCreatorId = ref(null)
const creatorOptions = ref([])
const showPlayer = ref(false)
const currentVideo = ref(null)
const videoEl = ref(null)
let player = null

const formatDuration = (s) => `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`
const formatNum = (n) => n >= 10000 ? `${(n/10000).toFixed(1)}w` : (n ?? '—')
const formatDate = (iso) => iso ? new Date(iso).toLocaleDateString('zh-CN') : '—'
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
      downloaded: true
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
.videos-page { max-width: 1400px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }

.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

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
  position: absolute; bottom: 6px; right: 6px;
  background: rgba(0,0,0,0.7);
  color: white; font-size: 11px;
  padding: 2px 6px; border-radius: 4px;
}
.video-badges {
  position: absolute; top: 6px; left: 6px;
  display: flex; gap: 4px;
}
.badge {
  padding: 2px 6px; border-radius: 4px;
  font-size: 10px; font-weight: 600;
}
.badge-success { background: rgba(0,197,102,0.8); color: white; }
.badge-ai { background: rgba(99,102,241,0.8); color: white; }

.video-info { padding: 10px 12px; }
.video-title {
  font-size: 13px; font-weight: 500; line-height: 1.4;
  overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  height: 2.8em;
}
.video-meta { display: flex; flex-direction: column; gap: 4px; font-size: 11px; color: var(--text-secondary); margin-top: 6px; }
.video-creator { color: var(--el-color-primary); font-weight: 600; font-size: 12px; margin-bottom: 2px; }
.meta-stats { display: flex; gap: 8px; }
.video-date { align-self: flex-end; margin-top: -14px; opacity: 0.8; }

.pagination-wrap { display: flex; justify-content: center; margin-top: 28px; }

.player-wrap { width: 100%; border-radius: 8px; overflow: hidden; background: black; display: flex; justify-content: center; align-items: center; }

/* 局部样式，用于弹窗内展示 */
.player-wrap :deep(.plyr) { width: 100%; max-height: 65vh; }
.player-wrap :deep(video) { object-fit: contain; }

.video-detail { padding: 12px 0 0; }
.detail-stats { display: flex; gap: 16px; font-size: 14px; margin-bottom: 10px; color: var(--text-secondary); }
.video-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; max-height: 80px; overflow-y: auto; }
.ai-section { margin-top: 14px; background: rgba(99,102,241,0.08); border-radius: 8px; padding: 12px; }
.ai-badge { font-size: 12px; color: #818cf8; font-weight: 600; margin-bottom: 6px; }
.ai-summary { font-size: 13px; line-height: 1.6; margin-bottom: 8px; }
.ai-keywords { display: flex; flex-wrap: wrap; gap: 4px; }
.loading-wrap { padding: 40px 0; }
</style>

<!-- 全局样式：解决全屏模式下的显示问题 -->
<style>
.plyr--fullscreen-active video {
  max-height: none !important;
  height: 100vh !important;
  width: 100vw !important;
  object-fit: contain !important;
}
</style>
