<template>
  <div class="queue-page">
    <div class="page-header">
      <div>
        <h1>⏳ 采集队列</h1>
        <p class="subtitle">待下载或正在处理中的视频 ({{ total }})</p>
      </div>
    </div>

    <div v-if="loading" class="loading-wrap">
      <el-skeleton :rows="4" animated />
    </div>
    <div v-else-if="videos.length === 0" class="empty-state">
      <el-empty description="队列空空如也，所有视频已处理完成" />
    </div>
    <div v-else class="queue-list">
      <el-table :data="videos" style="width: 100%" stripe border>
        <el-table-column label="封面" width="100">
          <template #default="{ row }">
            <img :src="row.cover_url" class="table-cover" @error="(e) => e.target.style.display='none'" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="{ row }">
            <div class="video-title-cell">{{ row.title || '（无标题）' }}</div>
            <div class="video-desc-cell">{{ row.desc }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="博主" width="150" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag type="warning" effect="dark" size="small">待下载</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发布时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.published_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewOriginal(row)">查看原片</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadQueue"
        background
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { videoApi } from '@/api'

const videos = ref([])
const loading = ref(true)
const page = ref(1)
const pageSize = 15
const total = ref(0)

const formatDate = (iso) => iso ? new Date(iso).toLocaleString('zh-CN') : '—'

const loadQueue = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize,
      downloaded: false
    }
    const res = await videoApi.list(params)
    videos.value = res.data || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

const viewOriginal = (video) => {
  if (video.play_url) {
    window.open(video.play_url, '_blank')
  }
}

onMounted(loadQueue)
</script>

<style scoped>
.queue-page { max-width: 1200px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }

.table-cover {
  width: 60px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
}

.video-title-cell { font-weight: 600; font-size: 14px; margin-bottom: 4px; }
.video-desc-cell { 
  font-size: 12px; 
  color: var(--text-secondary); 
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.pagination-wrap { display: flex; justify-content: center; margin-top: 24px; }
.loading-wrap { padding: 40px 0; }
.empty-state { padding: 80px 0; }
</style>
