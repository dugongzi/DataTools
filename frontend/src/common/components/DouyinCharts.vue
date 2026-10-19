<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { ECharts, EChartsOption } from 'echarts'
import type {
  DouyinCharts,
  DouyinVideo
} from '@/core/types/entities/douyin_video.entity'
import type { DouyinWindow } from '@/core/types/dto/douyin_video.dto'

echarts.use([
  LineChart,
  BarChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  CanvasRenderer
])

const props = defineProps<{
  charts: DouyinCharts | null
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

const SERIES = [
  { key: 'diggCount', name: '点赞', color: '#0071e3' },
  { key: 'commentCount', name: '评论', color: '#34c759' },
  { key: 'shareCount', name: '分享', color: '#ff9500' },
  { key: 'collectCount', name: '收藏', color: '#af52de' }
] as const

const rootEl = ref<HTMLElement | null>(null)
const trendEl = ref<HTMLDivElement | null>(null)
const compositionEl = ref<HTMLDivElement | null>(null)
const topEl = ref<HTMLDivElement | null>(null)
const authorEl = ref<HTMLDivElement | null>(null)

const instances = new Map<string, ECharts>()
const observers = new Map<string, ResizeObserver>()

const windowLabel = computed(() => WINDOW_LABELS[props.window])
const trendPoints = computed(() => props.charts?.trend ?? [])
const composition = computed(() => props.charts?.composition ?? null)
const topVideos = computed(() => props.charts?.topVideos ?? [])
const topVideosAsc = computed(() => [...topVideos.value].reverse())
const authors = computed(() => props.charts?.authors ?? [])
const authorsAsc = computed(() => [...authors.value].reverse())

const totalGrowth = computed(() =>
  trendPoints.value.reduce((sum, point) => sum + point.interaction, 0)
)
const totalInteraction = computed(() => composition.value?.interaction ?? 0)

const bucketLabel = computed(() => {
  const seconds = props.charts?.bucketSeconds ?? 0
  if (seconds <= 0) return '个时间点'
  if (seconds < 3600) return `${Math.round(seconds / 60)} 分钟`
  if (seconds < 86400) return `${Math.round(seconds / 3600)} 小时`
  return `${Math.round(seconds / 86400)} 天`
})

function token(name: string, fallback: string) {
  if (!rootEl.value) return fallback
  const value = getComputedStyle(rootEl.value).getPropertyValue(name).trim()
  return value || fallback
}

function formatCompact(value: number) {
  if (value >= 10000) return `${(value / 10000).toFixed(1)}w`
  return value.toLocaleString('zh-CN')
}

function chartLabel(value: Date | null) {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) return ''
  const pad = (input: number) => String(input).padStart(2, '0')
  return `${pad(value.getMonth() + 1)}-${pad(value.getDate())} ${pad(value.getHours())}:${pad(value.getMinutes())}`
}

function shortLabel(value: string, max = 14) {
  return value.length > max ? `${value.slice(0, max)}…` : value
}

function videoLabel(video: DouyinVideo) {
  return video.title || video.author || '未命名视频'
}

function mountChart(key: string, el: HTMLDivElement | null): ECharts | null {
  if (!el) return null

  const existing = instances.get(key)
  if (existing) {
    if (existing.getDom() === el) return existing
    observers.get(key)?.disconnect()
    existing.dispose()
    instances.delete(key)
    observers.delete(key)
  }

  const instance = echarts.init(el)
  const observer = new ResizeObserver(() => instance.resize())
  observer.observe(el)
  instances.set(key, instance)
  observers.set(key, observer)
  return instance
}

function renderTrend() {
  const chart = mountChart('trend', trendEl.value)
  if (!chart) return

  const points = trendPoints.value
  const textColor = token('--text-muted', '#6e6e73')
  const subtleColor = token('--text-subtle', '#86868b')
  const lineColor = token('--separator', 'rgba(0, 0, 0, 0.1)')

  const option: EChartsOption = {
    animationDuration: 320,
    grid: { left: 4, right: 8, top: 40, bottom: 4, containLabel: true },
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
      data: points.map((point) => chartLabel(point.time)),
      axisLine: { lineStyle: { color: lineColor } },
      axisTick: { show: false },
      axisLabel: { color: subtleColor, fontSize: 10, hideOverlap: true }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: subtleColor,
        fontSize: 10,
        formatter: (value: number) => formatCompact(value)
      },
      splitLine: { lineStyle: { color: lineColor } }
    },
    series: SERIES.map((item) => ({
      name: item.name,
      type: 'line',
      stack: 'growth',
      smooth: true,
      showSymbol: false,
      areaStyle: { opacity: 0.18 },
      lineStyle: { width: 2, color: item.color },
      itemStyle: { color: item.color },
      data: points.map((point) => point[item.key])
    }))
  }

  chart.setOption(option, true)
}

function renderComposition() {
  const chart = mountChart('composition', compositionEl.value)
  if (!chart) return

  const totals = composition.value
  const textColor = token('--text-muted', '#6e6e73')
  const subtleColor = token('--text-subtle', '#86868b')

  const data = totals
    ? SERIES.map((item) => ({
        name: item.name,
        value:
          item.key === 'diggCount'
            ? totals.diggCount
            : item.key === 'commentCount'
              ? totals.commentCount
              : item.key === 'shareCount'
                ? totals.shareCount
                : totals.collectCount,
        itemStyle: { color: item.color }
      }))
    : []

  const option: EChartsOption = {
    animationDuration: 320,
    title: {
      text: totalInteraction.value.toLocaleString('zh-CN'),
      subtext: '累计互动',
      left: 'center',
      top: '32%',
      textStyle: { fontSize: 20, fontWeight: 600, color: textColor },
      subtextStyle: { fontSize: 11, color: subtleColor }
    },
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      bottom: 0,
      left: 'center',
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      itemGap: 14,
      textStyle: { color: textColor, fontSize: 11 }
    },
    series: [
      {
        type: 'pie',
        radius: ['56%', '80%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderWidth: 2,
          borderColor: token('--surface-solid', '#ffffff')
        },
        label: { show: false },
        labelLine: { show: false },
        emphasis: {
          scaleSize: 6,
          label: {
            show: true,
            fontSize: 12,
            fontWeight: 600,
            color: textColor,
            formatter: '{b}\n{d}%'
          }
        },
        data
      }
    ]
  }

  chart.setOption(option, true)
}

function renderTopVideos() {
  const chart = mountChart('top', topEl.value)
  if (!chart) return

  const items = topVideosAsc.value
  const textColor = token('--text-muted', '#6e6e73')
  const subtleColor = token('--text-subtle', '#86868b')
  const lineColor = token('--separator', 'rgba(0, 0, 0, 0.1)')
  const accent = token('--accent', '#0071e3')

  const option: EChartsOption = {
    animationDuration: 320,
    grid: { left: 4, right: 44, top: 8, bottom: 4, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (value) => Number(value).toLocaleString('zh-CN')
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: subtleColor,
        fontSize: 10,
        formatter: (value: number) => formatCompact(value)
      },
      splitLine: { lineStyle: { color: lineColor } }
    },
    yAxis: {
      type: 'category',
      data: items.map((video) => shortLabel(videoLabel(video))),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: textColor, fontSize: 11 }
    },
    series: [
      {
        type: 'bar',
        data: items.map((video) => video.growth?.interaction ?? 0),
        barMaxWidth: 16,
        itemStyle: { color: accent, borderRadius: [0, 4, 4, 0] },
        label: {
          show: true,
          position: 'right',
          color: subtleColor,
          fontSize: 10,
          formatter: (params) => formatCompact(Number(params.value))
        }
      }
    ]
  }

  chart.setOption(option, true)
  chart.off('click')
  chart.on('click', (params) => {
    const index = Number(params.dataIndex ?? -1)
    const video = items[index]
    if (video) emit('open', video)
  })
}

function renderAuthors() {
  const chart = mountChart('author', authorEl.value)
  if (!chart) return

  const items = authorsAsc.value
  const textColor = token('--text-muted', '#6e6e73')
  const subtleColor = token('--text-subtle', '#86868b')
  const lineColor = token('--separator', 'rgba(0, 0, 0, 0.1)')
  const color = token('--success', '#34c759')

  const option: EChartsOption = {
    animationDuration: 320,
    grid: { left: 4, right: 44, top: 8, bottom: 4, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (value) => Number(value).toLocaleString('zh-CN')
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: subtleColor,
        fontSize: 10,
        formatter: (value: number) => formatCompact(value)
      },
      splitLine: { lineStyle: { color: lineColor } }
    },
    yAxis: {
      type: 'category',
      data: items.map((item) => shortLabel(item.author, 10)),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: textColor, fontSize: 11 }
    },
    series: [
      {
        type: 'bar',
        data: items.map((item) => item.interaction),
        barMaxWidth: 16,
        itemStyle: { color, borderRadius: [0, 4, 4, 0] },
        label: {
          show: true,
          position: 'right',
          color: subtleColor,
          fontSize: 10,
          formatter: (params) => formatCompact(Number(params.value))
        }
      }
    ]
  }

  chart.setOption(option, true)
}

function renderAll() {
  renderTrend()
  renderComposition()
  renderTopVideos()
  renderAuthors()
}

watch(
  () => props.charts,
  async () => {
    await nextTick()
    renderAll()
  }
)

onMounted(async () => {
  await nextTick()
  renderAll()
})

onBeforeUnmount(() => {
  observers.forEach((observer) => observer.disconnect())
  observers.clear()
  instances.forEach((instance) => instance.dispose())
  instances.clear()
})
</script>

<template>
  <section ref="rootEl" class="charts" aria-label="数据图表">
    <div v-if="loading && !charts" class="charts__loading">正在加载图表…</div>

    <article class="chart-card chart-card--wide">
      <header class="chart-card__head">
        <div class="chart-card__heading">
          <h2 class="chart-card__title">互动增长趋势</h2>
          <p class="chart-card__hint">{{ windowLabel }} · 每{{ bucketLabel }}新增互动</p>
        </div>
        <span class="chart-card__badge">+{{ formatCompact(totalGrowth) }}</span>
      </header>
      <div ref="trendEl" class="chart chart--trend"></div>
      <p v-if="!loading && !trendPoints.length" class="chart-card__empty">
        窗口内暂无采集快照
      </p>
    </article>

    <article class="chart-card chart-card--third">
      <header class="chart-card__head">
        <h2 class="chart-card__title">互动构成</h2>
        <span class="chart-card__hint">累计值</span>
      </header>
      <div ref="compositionEl" class="chart chart--donut"></div>
      <p v-if="!loading && !totalInteraction" class="chart-card__empty">暂无采集数据</p>
    </article>

    <article class="chart-card chart-card--third">
      <header class="chart-card__head">
        <h2 class="chart-card__title">增长 Top 视频</h2>
        <span class="chart-card__hint">点击查看详情</span>
      </header>
      <div ref="topEl" class="chart chart--bar"></div>
      <p v-if="!loading && !topVideos.length" class="chart-card__empty">
        窗口内暂无增长数据
      </p>
    </article>

    <article class="chart-card chart-card--third">
      <header class="chart-card__head">
        <h2 class="chart-card__title">作者互动排行</h2>
        <span class="chart-card__hint">累计互动</span>
      </header>
      <div ref="authorEl" class="chart chart--bar"></div>
      <p v-if="!loading && !authors.length" class="chart-card__empty">暂无作者数据</p>
    </article>
  </section>
</template>

<style scoped>
.charts {
  position: relative;
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 1rem;
}

.chart-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
  padding: 1rem 1.125rem;
  background: var(--surface);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  box-shadow: var(--surface-shadow);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  animation: rise 0.34s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.chart-card--wide {
  grid-column: span 12;
}

.chart-card--third {
  grid-column: span 4;
}

.chart-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.chart-card__heading {
  display: grid;
  gap: 0.125rem;
  min-width: 0;
}

.chart-card__title {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.chart-card__hint {
  margin: 0;
  font-size: 0.6875rem;
  color: var(--text-subtle);
}

.chart-card__badge {
  flex: 0 0 auto;
  padding: 0.1875rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--success);
  background: var(--field-bg);
  border-radius: var(--radius-pill);
  font-variant-numeric: tabular-nums;
}

.chart {
  width: 100%;
}

.chart--trend {
  height: 300px;
}

.chart--donut,
.chart--bar {
  height: 260px;
}

.chart-card__empty {
  position: absolute;
  inset: 3rem 0 1rem;
  display: grid;
  place-items: center;
  margin: 0;
  font-size: 0.8125rem;
  color: var(--text-subtle);
  pointer-events: none;
}

.charts__loading {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: grid;
  place-items: center;
  font-size: 0.8125rem;
  color: var(--text-subtle);
  background: var(--surface);
  border-radius: var(--radius-md);
  animation: pulse 1.4s ease-in-out infinite;
}

@media (max-width: 1100px) {
  .chart-card--third {
    grid-column: span 6;
  }
}

@media (max-width: 760px) {
  .chart-card--third {
    grid-column: span 12;
  }

  .chart--trend {
    height: 240px;
  }
}
</style>
