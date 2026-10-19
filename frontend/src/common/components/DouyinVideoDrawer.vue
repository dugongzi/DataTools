<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { ECharts, EChartsOption } from 'echarts'
import { douyinApi } from '@/core/api/douyin_api'
import type {
  DouyinGrowth,
  DouyinSnapshot,
  DouyinVideo
} from '@/core/types/entities/douyin_video.entity'
import type { DouyinWindow } from '@/core/types/dto/douyin_video.dto'

echarts.use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  video: DouyinVideo
  window: DouyinWindow
}>()

const emit = defineEmits<{
  close: []
}>()

const WINDOW_LABELS: Record<DouyinWindow, string> = {
  '1h': '近 1 小时',
  '6h': '近 6 小时',
  '24h': '近 24 小时',
  '7d': '近 7 天',
  all: '全部时间'
}

const SERIES = [
  { key: 'diggCount', name: '点赞', color: '#0071e3' },
  { key: 'commentCount', name: '评论', color: '#34c759' },
  { key: 'shareCount', name: '分享', color: '#ff9500' },
  { key: 'collectCount', name: '收藏', color: '#af52de' }
] as const

const loading = ref(true)
const error = ref<string | null>(null)
const snapshots = ref<DouyinSnapshot[]>([])
const growth = ref<DouyinGrowth | null>(null)
const chartEl = ref<HTMLDivElement | null>(null)

let chart: ECharts | null = null
let observer: ResizeObserver | null = null

const windowLabel = computed(() => WINDOW_LABELS[props.window])
const title = computed(() => props.video.title || props.video.author || '未命名视频')
const recent = computed(() => [...snapshots.value].reverse())

function formatCount(value?: number | null) {
  if (value === undefined || value === null) return '—'
  return value.toLocaleString('zh-CN')
}

function formatDelta(value?: number | null) {
  if (value === undefined || value === null) return '—'
  return `${value > 0 ? '+' : ''}${value.toLocaleString('zh-CN')}`
}

function formatRate(value?: number | null) {
  if (value === undefined || value === null) return '—'
  return `${(value * 100).toFixed(1)}%`
}

function formatDate(value: Date | null) {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) return '—'
  return value.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function chartLabel(value: Date | null) {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) return ''
  const pad = (input: number) => String(input).padStart(2, '0')
  return `${pad(value.getMonth() + 1)}-${pad(value.getDate())} ${pad(value.getHours())}:${pad(value.getMinutes())}`
}

function token(name: string, fallback: string) {
  if (!chartEl.value) return fallback
  const value = getComputedStyle(chartEl.value).getPropertyValue(name).trim()
  return value || fallback
}

function renderChart() {
  if (!chartEl.value) return
  if (chart && chart.getDom() !== chartEl.value) {
    observer?.disconnect()
    chart.dispose()
    chart = null
  }
  if (!chart) {
    chart = echarts.init(chartEl.value)
    observer = new ResizeObserver(() => chart?.resize())
    observer.observe(chartEl.value)
  }

  const valid = snapshots.value.filter(
    (item) => item.error === null && item.capturedAt instanceof Date
  )
  const textColor = token('--text-muted', '#6e6e73')
  const subtleColor = token('--text-subtle', '#86868b')
  const lineColor = token('--separator', 'rgba(0, 0, 0, 0.1)')

  const option: EChartsOption = {
    animationDuration: 320,
    grid: { left: 4, right: 8, top: 36, bottom: 4, containLabel: true },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value) => Number(value).toLocaleString('zh-CN')
    },
    legend: {
      top: 0,
      left: 0,
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      itemGap: 14,
      textStyle: { color: textColor, fontSize: 11 }
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: valid.map((item) => chartLabel(item.capturedAt)),
      axisLine: { lineStyle: { color: lineColor } },
      axisTick: { show: false },
      axisLabel: { color: subtleColor, fontSize: 10, hideOverlap: true }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: subtleColor,
        fontSize: 10,
        formatter: (value: number) => (value >= 10000 ? `${(value / 10000).toFixed(1)}w` : String(value))
      },
      splitLine: { lineStyle: { color: lineColor } }
    },
    series: SERIES.map((item) => ({
      name: item.name,
      type: 'line',
      smooth: true,
      showSymbol: valid.length < 12,
      symbolSize: 5,
      lineStyle: { width: 2, color: item.color },
      itemStyle: { color: item.color },
      data: valid.map((snapshot) => snapshot[item.key])
    }))
  }

  chart.setOption(option, true)
}

async function loadSnapshots() {
  loading.value = true
  error.value = null
  try {
    const result = await douyinApi.getSnapshots(props.video.id, props.window, 300)
    snapshots.value = result.items
    growth.value = result.growth
    loading.value = false
    await nextTick()
    renderChart()
  } catch (e) {
    error.value = '无法加载该视频的历史采集数据'
    loading.value = false
    console.error(e)
  }
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}

watch(
  () => [props.video.id, props.window] as const,
  () => {
    void loadSnapshots()
  },
  { immediate: true }
)

onMounted(() => {
  document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKeydown)
  observer?.disconnect()
  chart?.dispose()
})
</script>

<template>
  <div class="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
    <div class="drawer__scrim" @click="emit('close')"></div>

    <aside class="drawer__panel">
      <header class="drawer__head">
        <div class="drawer__heading">
          <h2 id="drawer-title" class="drawer__title">{{ title }}</h2>
          <p class="drawer__meta">
            {{ video.author || '未知作者' }} ·
            <a :href="video.url" target="_blank" rel="noopener noreferrer">打开视频</a>
          </p>
        </div>
        <button class="drawer__close" type="button" aria-label="关闭" @click="emit('close')">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M6 6l12 12M18 6L6 18"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </button>
      </header>

      <div class="drawer__body">
        <p v-if="loading && !snapshots.length" class="drawer__state">正在加载历史数据…</p>
        <p v-else-if="error" class="drawer__state drawer__state--error">{{ error }}</p>

        <template v-else>
          <section class="summary">
            <div class="summary__head">
              <h3 class="summary__title">{{ windowLabel }}增长</h3>
              <span v-if="growth?.available" class="summary__rate">
                增长率 {{ formatRate(growth.rate) }}
              </span>
              <span v-else class="summary__rate">快照不足 2 条</span>
            </div>

            <div class="summary__grid">
              <div class="summary__item">
                <span class="summary__label">互动</span>
                <strong class="summary__value">{{ formatDelta(growth?.interaction) }}</strong>
              </div>
              <div class="summary__item">
                <span class="summary__label">点赞</span>
                <strong class="summary__value">{{ formatDelta(growth?.diggCount) }}</strong>
              </div>
              <div class="summary__item">
                <span class="summary__label">评论</span>
                <strong class="summary__value">{{ formatDelta(growth?.commentCount) }}</strong>
              </div>
              <div class="summary__item">
                <span class="summary__label">分享</span>
                <strong class="summary__value">{{ formatDelta(growth?.shareCount) }}</strong>
              </div>
              <div class="summary__item">
                <span class="summary__label">收藏</span>
                <strong class="summary__value">{{ formatDelta(growth?.collectCount) }}</strong>
              </div>
            </div>

            <p v-if="growth?.from && growth?.to" class="summary__range">
              {{ formatDate(growth.from) }} → {{ formatDate(growth.to) }}
            </p>
          </section>

          <section class="chart-block">
            <div class="chart-block__head">
              <h3 class="chart-block__title">互动趋势</h3>
              <span class="chart-block__hint">{{ snapshots.length }} 次采集</span>
            </div>
            <div ref="chartEl" class="chart"></div>
            <p v-if="!snapshots.length" class="chart-block__empty">窗口内暂无采集记录</p>
          </section>

          <section class="snapshots">
            <h3 class="snapshots__title">采集明细</h3>
            <div class="snapshots__wrap">
              <table class="snapshots__table">
                <thead>
                  <tr>
                    <th scope="col" rowspan="2">采集时间</th>
                    <th scope="col" colspan="4" class="is-group">累计数据</th>
                    <th scope="col" colspan="5" class="is-group">本次增长</th>
                  </tr>
                  <tr>
                    <th scope="col" class="is-num">点赞</th>
                    <th scope="col" class="is-num">评论</th>
                    <th scope="col" class="is-num">分享</th>
                    <th scope="col" class="is-num">收藏</th>
                    <th scope="col" class="is-num">点赞</th>
                    <th scope="col" class="is-num">评论</th>
                    <th scope="col" class="is-num">分享</th>
                    <th scope="col" class="is-num">收藏</th>
                    <th scope="col" class="is-num">互动</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="snapshot in recent" :key="snapshot.id">
                    <td class="is-date">{{ formatDate(snapshot.capturedAt) }}</td>
                    <template v-if="snapshot.error">
                      <td colspan="9" class="is-error" :title="snapshot.error">采集失败</td>
                    </template>
                    <template v-else>
                      <td class="is-num">{{ formatCount(snapshot.diggCount) }}</td>
                      <td class="is-num">{{ formatCount(snapshot.commentCount) }}</td>
                      <td class="is-num">{{ formatCount(snapshot.shareCount) }}</td>
                      <td class="is-num">{{ formatCount(snapshot.collectCount) }}</td>
                      <td class="is-num is-growth-sub">
                        {{ snapshot.growth ? formatDelta(snapshot.growth.diggCount) : '—' }}
                      </td>
                      <td class="is-num is-growth-sub">
                        {{ snapshot.growth ? formatDelta(snapshot.growth.commentCount) : '—' }}
                      </td>
                      <td class="is-num is-growth-sub">
                        {{ snapshot.growth ? formatDelta(snapshot.growth.shareCount) : '—' }}
                      </td>
                      <td class="is-num is-growth-sub">
                        {{ snapshot.growth ? formatDelta(snapshot.growth.collectCount) : '—' }}
                      </td>
                      <td class="is-num is-growth">
                        {{ snapshot.growth ? formatDelta(snapshot.growth.interaction) : '—' }}
                      </td>
                    </template>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </template>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.drawer {
  position: fixed;
  inset: 0;
  z-index: 120;
}

.drawer__scrim {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.36);
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
  animation: fade-in 0.2s ease both;
}

.drawer__panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  width: min(560px, 100%);
  background: var(--surface-solid);
  border-left: 1px solid var(--surface-border);
  box-shadow: -24px 0 60px rgba(0, 0, 0, 0.18);
  animation: slide-in 0.3s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes slide-in {
  from {
    transform: translateX(24px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.drawer__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 1.5rem 1rem;
  border-bottom: 1px solid var(--separator);
}

.drawer__heading {
  display: grid;
  gap: 0.25rem;
  min-width: 0;
}

.drawer__title {
  margin: 0;
  font-size: 1.0625rem;
  font-weight: 600;
  letter-spacing: -0.022em;
  line-height: 1.35;
}

.drawer__meta {
  margin: 0;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.drawer__meta a {
  color: var(--accent);
  text-decoration: none;
}

.drawer__meta a:hover {
  text-decoration: underline;
}

.drawer__close {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  color: var(--text-muted);
  background: var(--field-bg);
  border: none;
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: background 0.16s ease;
}

.drawer__close:hover {
  background: var(--field-bg-hover);
}

.drawer__close svg {
  width: 16px;
  height: 16px;
}

.drawer__body {
  display: grid;
  gap: 1rem;
  padding: 1rem 1.5rem 1.5rem;
  overflow-y: auto;
}

.drawer__state {
  margin: 0;
  padding: 2rem 0;
  text-align: center;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.drawer__state--error {
  color: var(--danger);
}

/* ---------- 增长摘要 ---------- */
.summary {
  display: grid;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  background: var(--field-bg);
  border-radius: var(--radius-md);
}

.summary__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}

.summary__title {
  margin: 0;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-muted);
}

.summary__rate {
  font-size: 0.75rem;
  color: var(--text-subtle);
  font-variant-numeric: tabular-nums;
}

.summary__grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.5rem;
}

.summary__item {
  display: grid;
  gap: 0.125rem;
}

.summary__label {
  font-size: 0.6875rem;
  color: var(--text-subtle);
}

.summary__value {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--success);
  font-variant-numeric: tabular-nums;
}

.summary__range {
  margin: 0;
  font-size: 0.6875rem;
  color: var(--text-subtle);
  font-variant-numeric: tabular-nums;
}

/* ---------- 图表 ---------- */
.chart-block {
  position: relative;
  display: grid;
  gap: 0.5rem;
}

.chart-block__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}

.chart-block__title,
.snapshots__title {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.chart-block__hint {
  font-size: 0.75rem;
  color: var(--text-subtle);
}

.chart {
  width: 100%;
  height: 220px;
}

.chart-block__empty {
  position: absolute;
  inset: 2.5rem 0 0;
  display: grid;
  place-items: center;
  margin: 0;
  font-size: 0.8125rem;
  color: var(--text-subtle);
  pointer-events: none;
}

/* ---------- 快照明细 ---------- */
.snapshots {
  display: grid;
  gap: 0.5rem;
}

.snapshots__wrap {
  overflow-x: auto;
  border: 1px solid var(--separator);
  border-radius: var(--radius-sm);
}

.snapshots__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.75rem;
  white-space: nowrap;
}

.snapshots__table th {
  padding: 0.5rem 0.75rem;
  text-align: left;
  font-size: 0.625rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-subtle);
  border-bottom: 1px solid var(--separator);
}

.snapshots__table td {
  padding: 0.5rem 0.75rem;
  font-variant-numeric: tabular-nums;
}

.snapshots__table tbody tr:nth-child(n + 2) td {
  border-top: 1px solid var(--separator);
}

.snapshots__table .is-num {
  text-align: right;
}

.snapshots__table .is-group {
  text-align: center;
  border-bottom: 1px solid var(--separator);
}

.snapshots__table .is-date {
  color: var(--text-muted);
}

.snapshots__table .is-growth-sub {
  color: var(--success);
}

.snapshots__table .is-growth {
  font-weight: 600;
  color: var(--success);
}

.snapshots__table .is-error {
  color: var(--danger);
}

@media (max-width: 560px) {
  .drawer__body {
    padding: 1rem;
  }

  .summary__grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
