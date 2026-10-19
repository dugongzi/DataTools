<script setup lang="ts">
import { computed } from 'vue'
import type { DouyinOverview, DouyinVideo } from '@/core/types/entities/douyin_video.entity'
import type { DouyinWindow } from '@/core/types/dto/douyin_video.dto'

const props = defineProps<{
  overview: DouyinOverview | null
  loading?: boolean
  window: DouyinWindow
}>()

const emit = defineEmits<{
  open: [video: DouyinVideo]
}>()

const WINDOW_LABELS: Record<DouyinWindow, string> = {
  '1h': '近 1 小时',
  '6h': '近 6 小时',
  '24h': '近 24 小时',
  '7d': '近 7 天',
  all: '全部时间'
}

const windowLabel = computed(() => WINDOW_LABELS[props.window])

const topVideos = computed(() => props.overview?.topVideos ?? [])

function formatCount(value?: number | null) {
  if (value === undefined || value === null) return '—'
  return value.toLocaleString('zh-CN')
}

function formatRate(value?: number | null) {
  if (value === undefined || value === null) return '—'
  return `${(value * 100).toFixed(1)}%`
}

function formatDate(value?: Date | null) {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) return '—'
  return value.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function interactionOf(video: DouyinVideo) {
  const latest = video.latest
  if (!latest) return 0
  return latest.diggCount + latest.commentCount + latest.shareCount + latest.collectCount
}

function videoLabel(video: DouyinVideo) {
  return video.title || video.author || '未命名视频'
}
</script>

<template>
  <section class="overview" aria-label="监控概览">
    <div class="overview__stats">
      <article class="stat">
        <span class="stat__label">监控视频</span>
        <strong class="stat__value">{{ formatCount(overview?.totalVideos) }}</strong>
        <span class="stat__hint">
          已采集 {{ formatCount(overview?.capturedVideos) }}
          <template v-if="overview?.failedVideos"> · 失败 {{ overview.failedVideos }}</template>
          <template v-if="overview?.pendingVideos"> · 待采集 {{ overview.pendingVideos }}</template>
        </span>
      </article>

      <article class="stat">
        <span class="stat__label">累计互动</span>
        <strong class="stat__value">{{ formatCount(overview?.totals.interaction) }}</strong>
        <span class="stat__hint">点赞 / 评论 / 分享 / 收藏合计</span>
      </article>

      <article class="stat stat--accent">
        <span class="stat__label">{{ windowLabel }}增长</span>
        <strong class="stat__value">+{{ formatCount(overview?.growth.interaction) }}</strong>
        <span class="stat__hint">增长率 {{ formatRate(overview?.growth.rate) }}</span>
      </article>

      <article class="stat">
        <span class="stat__label">最近采集</span>
        <strong class="stat__value stat__value--sm">
          {{ formatDate(overview?.lastCapturedAt) }}
        </strong>
        <span class="stat__hint">
          <template v-if="overview?.failedVideos">
            {{ overview.failedVideos }} 条采集失败
          </template>
          <template v-else>采集状态正常</template>
        </span>
      </article>
    </div>

    <div class="hot">
      <div class="hot__head">
        <h2 class="hot__title">爆款视频</h2>
        <span class="hot__badge">{{ windowLabel }}增长</span>
      </div>

      <div v-if="loading && !overview" class="hot__skeleton" aria-hidden="true">
        <span v-for="row in 3" :key="row" class="hot__skeleton-row"></span>
      </div>

      <ol v-else-if="topVideos.length" class="hot__list">
        <li v-for="(video, index) in topVideos" :key="video.id">
          <button class="hot-item" type="button" @click="emit('open', video)">
            <span class="hot-item__rank" :class="{ 'hot-item__rank--top': index === 0 }">
              {{ index + 1 }}
            </span>
            <span class="hot-item__body">
              <span class="hot-item__title">{{ videoLabel(video) }}</span>
              <span class="hot-item__meta">
                {{ video.author || '未知作者' }} · 互动 {{ formatCount(interactionOf(video)) }}
              </span>
            </span>
            <span class="hot-item__growth">+{{ formatCount(video.growth?.interaction) }}</span>
          </button>
        </li>
      </ol>

      <p v-else class="hot__empty">暂无窗口内增长数据，等待下一轮采集。</p>
    </div>
  </section>
</template>

<style scoped>
.overview {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr);
  gap: 1rem;
}

/* ---------- 统计卡 ---------- */
.overview__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.stat {
  display: grid;
  gap: 0.25rem;
  padding: 1rem 1.125rem;
  background: var(--surface);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  box-shadow: var(--surface-shadow);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  animation: rise 0.32s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.stat__label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-subtle);
}

.stat__value {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.stat__value--sm {
  font-size: 1rem;
  padding: 0.25rem 0;
}

.stat__hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.stat--accent .stat__value {
  color: var(--accent);
}

/* ---------- 爆款榜 ---------- */
.hot {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem 1.125rem;
  background: var(--surface);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  box-shadow: var(--surface-shadow);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  animation: rise 0.36s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.hot__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.hot__title {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.hot__badge {
  padding: 0.1875rem 0.5rem;
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--field-bg);
  border-radius: var(--radius-pill);
  white-space: nowrap;
}

.hot__list {
  display: grid;
  gap: 0.25rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.hot-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  width: 100%;
  padding: 0.5rem 0.5rem 0.5rem 0.375rem;
  font: inherit;
  text-align: left;
  color: inherit;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.16s ease;
}

.hot-item:hover {
  background: var(--field-bg);
}

.hot-item__rank {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 20px;
  height: 20px;
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--text-subtle);
  background: var(--field-bg);
  border-radius: var(--radius-pill);
  font-variant-numeric: tabular-nums;
}

.hot-item__rank--top {
  color: #fff;
  background: var(--accent);
}

.hot-item__body {
  display: grid;
  gap: 0.125rem;
  flex: 1;
  min-width: 0;
}

.hot-item__title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.8125rem;
  font-weight: 500;
}

.hot-item__meta {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.6875rem;
  color: var(--text-subtle);
}

.hot-item__growth {
  flex: 0 0 auto;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--success);
  font-variant-numeric: tabular-nums;
}

.hot__empty {
  margin: 0;
  padding: 1rem 0;
  font-size: 0.8125rem;
  color: var(--text-subtle);
}

.hot__skeleton {
  display: grid;
  gap: 0.5rem;
}

.hot__skeleton-row {
  height: 34px;
  border-radius: var(--radius-sm);
  background: var(--field-bg);
  animation: pulse 1.4s ease-in-out infinite;
}

@media (max-width: 900px) {
  .overview {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .overview__stats {
    grid-template-columns: 1fr;
  }
}
</style>
