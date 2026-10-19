<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { douyinApi } from '@/core/api/douyin_api'
import { useDouyinStore } from '@/core/stores/douyin'
import DouyinCharts from '@/common/components/DouyinCharts.vue'
import DouyinOverview from '@/common/components/DouyinOverview.vue'
import DouyinVideoDrawer from '@/common/components/DouyinVideoDrawer.vue'
import type { DouyinVideo } from '@/core/types/entities/douyin_video.entity'
import type { DouyinMonitorRun } from '@/core/types/entities/douyin_monitor_config.entity'
import type {
  DouyinSortField,
  DouyinStatusFilter,
  DouyinWindow
} from '@/core/types/dto/douyin_video.dto'

const douyinStore = useDouyinStore()

const STATUS_OPTIONS: { value: DouyinStatusFilter; label: string }[] = [
  { value: 'all', label: '全部状态' },
  { value: 'captured', label: '已采集' },
  { value: 'failed', label: '采集失败' },
  { value: 'pending', label: '待采集' }
]

const SORT_GROUPS: {
  key: string
  label: string
  options: { value: DouyinSortField; label: string }[]
}[] = [
  {
    key: 'time',
    label: '时间',
    options: [
      { value: 'created_at', label: '导入时间' },
      { value: 'captured_at', label: '采集时间' }
    ]
  },
  {
    key: 'total',
    label: '累计互动',
    options: [
      { value: 'digg', label: '点赞数' },
      { value: 'comment', label: '评论数' },
      { value: 'share', label: '分享数' },
      { value: 'collect', label: '收藏数' },
      { value: 'interaction', label: '总互动' }
    ]
  },
  {
    key: 'growth',
    label: '窗口内增长',
    options: [
      { value: 'growth', label: '总互动增长' },
      { value: 'growth_digg', label: '点赞增长' },
      { value: 'growth_comment', label: '评论增长' },
      { value: 'growth_share', label: '分享增长' },
      { value: 'growth_collect', label: '收藏增长' },
      { value: 'growth_rate', label: '增长率' }
    ]
  }
]

const sortGroupKey = computed<string>({
  get: () =>
    SORT_GROUPS.find((group) =>
      group.options.some((option) => option.value === douyinStore.sort)
    )?.key ?? 'time',
  set: (key: string) => {
    const group = SORT_GROUPS.find((item) => item.key === key)
    const first = group?.options[0]
    if (!first) return
    douyinStore.sort = first.value
    void applyFilters()
  }
})

const sortOptions = computed(
  () => SORT_GROUPS.find((group) => group.key === sortGroupKey.value)?.options ?? []
)

const WINDOW_OPTIONS: { value: DouyinWindow; label: string }[] = [
  { value: '1h', label: '1 小时' },
  { value: '6h', label: '6 小时' },
  { value: '24h', label: '24 小时' },
  { value: '7d', label: '7 天' },
  { value: 'all', label: '全部' }
]

const drawerVideo = ref<DouyinVideo | null>(null)

const menuVideoId = ref<number | null>(null)
const menuPos = ref({ top: 0, left: 0 })

const pageLoading = ref(true)
const loadError = ref<string | null>(null)
const busyId = ref<number | null>(null)
const collecting = ref(false)
const currentRun = ref<DouyinMonitorRun | null>(null)
const collectingIds = ref<number[]>([])
const selectedVideoIds = ref<number[]>([])
let collectTimer: ReturnType<typeof setInterval> | undefined
let collectClearTimer: ReturnType<typeof setTimeout> | undefined
const COLLECT_POLL_TIMEOUT_MS = 10 * 60 * 1000

const historyOpen = ref(false)
const retrying = ref(false)
const exporting = ref(false)
const autoRefresh = ref(true)
const AUTO_REFRESH_MS = 60 * 1000
let autoTimer: ReturnType<typeof setInterval> | undefined

const RUN_STATUS_LABELS: Record<string, string> = {
  running: '采集中',
  success: '成功',
  partial: '部分失败',
  failed: '失败'
}

const TRIGGER_LABELS: Record<string, string> = {
  schedule: '定时',
  manual: '手动',
  import: '导入'
}

const shareText = ref('')
const importing = ref(false)
const modalOpen = ref(false)
const modalInput = ref<HTMLTextAreaElement | null>(null)

const notice = ref<{ kind: 'success' | 'error'; text: string } | null>(null)
let noticeTimer: ReturnType<typeof setTimeout> | undefined

const canImport = computed(() => shareText.value.trim().length > 0 && !importing.value)

const pageInfo = computed(() => {
  const totalPages = Math.max(1, douyinStore.pages)
  return `第 ${douyinStore.page} / ${totalPages} 页 · 共 ${douyinStore.total} 条`
})

const canPrev = computed(() => douyinStore.page > 1 && !douyinStore.loading)
const canNext = computed(() => douyinStore.page < douyinStore.pages && !douyinStore.loading)

const monitor = computed(() => douyinStore.monitorStatus)
const monitorRunning = computed(() => Boolean(monitor.value?.running) || collecting.value)
const monitorTitle = computed(() => {
  if (collecting.value) return '正在采集'
  const status = monitor.value
  if (!status) return '采集状态加载中'
  if (status.running) return '正在采集'
  return status.enabled ? '自动采集已开启' : '自动采集已关闭'
})

const progressRun = computed<DouyinMonitorRun | null>(() => {
  if (currentRun.value) return currentRun.value
  return monitor.value?.running ? monitor.value.currentRun : null
})
const progressDone = computed(() => {
  const run = progressRun.value
  return run ? run.successCount + run.failedCount : 0
})
const progressTotal = computed(() => progressRun.value?.total ?? 0)
const progressPercent = computed(() => {
  if (!progressTotal.value) return 0
  return Math.min(100, Math.round((progressDone.value / progressTotal.value) * 100))
})

const selectedCount = computed(() => selectedVideoIds.value.length)
const allSelected = computed(
  () =>
    douyinStore.videos.length > 0 &&
    douyinStore.videos.every((video) => selectedVideoIds.value.includes(video.id))
)
const someSelected = computed(() => selectedCount.value > 0 && !allSelected.value)

function toggleSelect(id: number) {
  selectedVideoIds.value = selectedVideoIds.value.includes(id)
    ? selectedVideoIds.value.filter((item) => item !== id)
    : [...selectedVideoIds.value, id]
}

function toggleSelectAll() {
  selectedVideoIds.value = allSelected.value
    ? []
    : douyinStore.videos.map((video) => video.id)
}

function clearSelection() {
  selectedVideoIds.value = []
}

function pruneSelection() {
  const ids = new Set(douyinStore.videos.map((video) => video.id))
  selectedVideoIds.value = selectedVideoIds.value.filter((id) => ids.has(id))
}

function videoStatus(video: DouyinVideo): {
  label: string
  tone: 'running' | 'success' | 'failed' | 'pending'
} {
  if (collecting.value && collectingIds.value.includes(video.id)) {
    return { label: '采集中', tone: 'running' }
  }
  if (video.latest?.lastError) return { label: '采集失败', tone: 'failed' }
  if (video.latest?.capturedAt) return { label: '已采集', tone: 'success' }
  return { label: '待采集', tone: 'pending' }
}

function flash(kind: 'success' | 'error', text: string) {
  notice.value = { kind, text }
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => {
    notice.value = null
  }, 4000)
}

function formatDate(value: Date | null) {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) return '—'
  return value.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatCount(value?: number | null) {
  if (value === undefined || value === null) return '—'
  return value.toLocaleString('zh-CN')
}

function formatDuration(startedAt: Date | null, finishedAt: Date | null) {
  if (!(startedAt instanceof Date) || !(finishedAt instanceof Date)) return '—'
  const seconds = Math.max(0, Math.round((finishedAt.getTime() - startedAt.getTime()) / 1000))
  if (seconds < 60) return `${seconds} 秒`
  return `${Math.floor(seconds / 60)} 分 ${seconds % 60} 秒`
}

async function applyFilters() {
  clearSelection()
  await douyinStore.applyFilters()
  loadError.value = douyinStore.error
}

async function toggleOrder() {
  douyinStore.order = douyinStore.order === 'desc' ? 'asc' : 'desc'
  await applyFilters()
}

async function selectWindow(next: DouyinWindow) {
  await douyinStore.setWindow(next)
}

function openDrawer(video: DouyinVideo) {
  drawerVideo.value = video
}

const MENU_WIDTH = 168
const MENU_HEIGHT = 96

function closeMenu() {
  menuVideoId.value = null
}

function toggleMenu(event: MouseEvent, video: DouyinVideo) {
  if (menuVideoId.value === video.id) {
    closeMenu()
    return
  }

  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const left = Math.max(8, Math.min(rect.left, window.innerWidth - MENU_WIDTH - 8))
  const top =
    rect.bottom + 6 + MENU_HEIGHT > window.innerHeight
      ? Math.max(8, rect.top - MENU_HEIGHT - 6)
      : rect.bottom + 6
  menuPos.value = { top, left }
  menuVideoId.value = video.id
}

function onGlobalKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  if (historyOpen.value) {
    historyOpen.value = false
    return
  }
  closeMenu()
}

function stopCollectPolling() {
  if (collectTimer) {
    clearInterval(collectTimer)
    collectTimer = undefined
  }
  clearTimeout(collectClearTimer)
  collectClearTimer = undefined
}

function scheduleProgressClear() {
  clearTimeout(collectClearTimer)
  collectClearTimer = setTimeout(() => {
    currentRun.value = null
  }, 4000)
}

function startCollectPolling(runId: number) {
  stopCollectPolling()
  collecting.value = true
  const startedAt = Date.now()

  const poll = async () => {
    if (Date.now() - startedAt > COLLECT_POLL_TIMEOUT_MS) {
      stopCollectPolling()
      collecting.value = false
      collectingIds.value = []
      currentRun.value = null
      flash('error', '采集状态同步超时，请刷新页面查看结果')
      return
    }
    try {
      const run = await douyinApi.getRun(runId)
      currentRun.value = run
      if (run.status === 'running') {
        if (run.videoIds.length > 0) collectingIds.value = run.videoIds
        return
      }

      stopCollectPolling()
      collecting.value = false
      collectingIds.value = []
      await Promise.all([
        douyinStore.fetchVideos(douyinStore.page),
        douyinStore.fetchOverview(),
        douyinStore.fetchCharts(),
        douyinStore.fetchMonitorStatus()
      ])
      loadError.value = douyinStore.error
      pruneSelection()

      const kind = run.status === 'failed' ? 'error' : 'success'
      flash(kind, `采集完成：成功 ${run.successCount} 条，失败 ${run.failedCount} 条`)
      scheduleProgressClear()
    } catch {
      // 轮询期间出现瞬时错误时继续等待，不中断采集
    }
  }

  void poll()
  collectTimer = setInterval(() => void poll(), 2000)
}

async function startCollect(videoIds?: number[]): Promise<boolean> {
  try {
    const { runId, run } = await douyinApi.triggerRun(videoIds)
    collectingIds.value = videoIds ?? douyinStore.videos.map((video) => video.id)
    currentRun.value = run
    const text = videoIds
      ? videoIds.length > 1
        ? `已启动批量采集（#${runId}），共 ${videoIds.length} 条视频`
        : `已启动单条采集（#${runId}）`
      : `已启动采集（#${runId}），共 ${run.total} 条视频`
    flash('success', text)
    startCollectPolling(runId)
    return true
  } catch (e) {
    const code = (e as { response?: { status?: number } })?.response?.status
    if (code === 409) {
      flash('error', '已有采集任务在运行，正在同步进度')
      try {
        const status = await douyinApi.getMonitorStatus()
        if (status.currentRun) {
          currentRun.value = status.currentRun
          collectingIds.value = status.currentRun.videoIds
          startCollectPolling(status.currentRun.id)
          return false
        }
      } catch {
        // 忽略同步失败
      }
    } else {
      flash('error', '启动采集失败，请稍后重试')
    }
    return false
  }
}

async function collectSelected() {
  if (collecting.value) {
    flash('error', '已有采集任务在运行')
    return
  }
  if (!selectedVideoIds.value.length) {
    flash('error', '请先勾选要采集的视频')
    return
  }
  const ids = [...selectedVideoIds.value]
  if (await startCollect(ids)) clearSelection()
}

async function refreshAll() {
  if (collecting.value) return
  if (!douyinStore.videos.length) {
    flash('error', '监控列表为空，请先添加视频')
    return
  }
  await startCollect()
}

async function openHistory() {
  historyOpen.value = true
  await douyinStore.fetchRuns(20)
}

async function retryFailedVideos() {
  if (retrying.value) return
  retrying.value = true
  try {
    const { runId, total } = await douyinStore.retryFailed()
    collectingIds.value = douyinStore.videos
      .filter((video) => video.latest?.lastError)
      .map((video) => video.id)
    flash('success', `已启动失败重采（#${runId}），共 ${total} 条视频`)
    startCollectPolling(runId)
  } catch (e) {
    const code = (e as { response?: { status?: number } })?.response?.status
    flash('error', code === 400 ? '没有采集失败的视频' : '启动重采失败，请稍后重试')
  } finally {
    retrying.value = false
  }
}

async function exportList() {
  if (exporting.value) return
  exporting.value = true
  try {
    await douyinStore.exportVideos()
    flash('success', '已导出当前筛选结果')
  } catch {
    flash('error', '导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

async function autoRefreshTick() {
  if (!autoRefresh.value || document.hidden || collecting.value) return
  await douyinStore.refreshData()
  loadError.value = douyinStore.error
  pruneSelection()
  const status = douyinStore.monitorStatus
  if (status?.running && status.currentRun) {
    currentRun.value = status.currentRun
    collectingIds.value = status.currentRun.videoIds
    startCollectPolling(status.currentRun.id)
  }
}

async function collectVideo(video: DouyinVideo) {
  closeMenu()
  if (collecting.value) {
    flash('error', '已有采集任务在运行')
    return
  }
  await startCollect([video.id])
}

async function load() {
  pageLoading.value = true
  loadError.value = null
  await Promise.all([
    douyinStore.fetchVideos(1),
    douyinStore.fetchOverview(),
    douyinStore.fetchCharts()
  ])
  loadError.value = douyinStore.error
  pageLoading.value = false

  if (loadError.value) return
  await douyinStore.fetchMonitorStatus()
  const status = douyinStore.monitorStatus
  if (status?.running && status.currentRun) {
    currentRun.value = status.currentRun
    collectingIds.value = status.currentRun.videoIds
    startCollectPolling(status.currentRun.id)
  }
}

function openModal() {
  shareText.value = ''
  modalOpen.value = true
  void nextTick(() => modalInput.value?.focus())
}

function closeModal() {
  if (importing.value) return
  modalOpen.value = false
  shareText.value = ''
}

function onModalKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') closeModal()
}

async function goPrev() {
  if (!canPrev.value) return
  clearSelection()
  await douyinStore.goToPage(douyinStore.page - 1)
}

async function goNext() {
  if (!canNext.value) return
  clearSelection()
  await douyinStore.goToPage(douyinStore.page + 1)
}

async function submitImport() {
  if (importing.value) return

  const text = shareText.value.trim()
  if (!text) {
    flash('error', '请先粘贴抖音分享内容')
    return
  }

  importing.value = true
  try {
    const { created, skipped, runId } = await douyinStore.importVideos(text)
    if (created.length > 0) {
      const extra = skipped.length > 0 ? `，跳过 ${skipped.length} 条已存在` : ''
      flash('success', `已导入 ${created.length} 条视频${extra}`)
      modalOpen.value = false
      shareText.value = ''
      await Promise.all([
        douyinStore.fetchVideos(1),
        douyinStore.fetchOverview(),
        douyinStore.fetchCharts()
      ])
      loadError.value = douyinStore.error
      if (runId) {
        collectingIds.value = created.map((video) => video.id)
        startCollectPolling(runId)
      }
    } else {
      flash('error', `未新增视频${skipped.length > 0 ? `，${skipped.length} 条已存在` : ''}`)
    }
  } catch {
    flash('error', '导入失败，请检查分享内容后重试')
  } finally {
    importing.value = false
  }
}

async function removeVideo(id: number, label: string) {
  closeMenu()
  if (busyId.value !== null) return
  if (!window.confirm(`确定删除「${label}」？此操作不可撤销。`)) return

  busyId.value = id
  try {
    await douyinStore.deleteVideo(id)
    pruneSelection()
    await Promise.all([douyinStore.fetchOverview(), douyinStore.fetchCharts()])
    flash('success', '已删除该视频')
  } catch {
    flash('error', '删除失败，请稍后重试')
  } finally {
    busyId.value = null
  }
}

function videoLabel(author: string | null, title: string | null) {
  return title || author || '未命名视频'
}

onMounted(() => {
  document.addEventListener('click', closeMenu)
  document.addEventListener('keydown', onGlobalKeydown)
  window.addEventListener('scroll', closeMenu, true)
  autoTimer = setInterval(() => void autoRefreshTick(), AUTO_REFRESH_MS)
  void load()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeMenu)
  document.removeEventListener('keydown', onGlobalKeydown)
  window.removeEventListener('scroll', closeMenu, true)
  clearTimeout(noticeTimer)
  clearInterval(autoTimer)
  stopCollectPolling()
})
</script>

<template>
  <div class="page">
    <div class="page__head">
      <div>
        <h1 class="page__title">抖音视频监控</h1>
        <p class="page__lead">粘贴抖音分享文本，自动解析链接并收录到监控列表</p>
      </div>

      <div class="page__actions">
        <button class="btn btn--quiet" type="button" :disabled="pageLoading" @click="load">
          刷新
        </button>
        <button
          class="btn btn--quiet"
          type="button"
          :disabled="collecting || pageLoading"
          @click="refreshAll"
        >
          {{ collecting ? '采集中…' : '刷新数据' }}
        </button>
        <button
          class="btn btn--quiet"
          type="button"
          :disabled="exporting || pageLoading"
          @click="exportList"
        >
          {{ exporting ? '导出中…' : '导出 CSV' }}
        </button>
        <button class="btn btn--primary btn--add" type="button" @click="openModal">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M12 5v14M5 12h14"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
          添加视频
        </button>
      </div>
    </div>

    <section class="monitor-bar" :class="{ 'monitor-bar--running': monitorRunning }">
      <div class="monitor-bar__main">
        <span
          class="monitor-bar__dot"
          :class="{
            'monitor-bar__dot--running': monitorRunning,
            'monitor-bar__dot--on': !monitorRunning && monitor?.enabled
          }"
          aria-hidden="true"
        ></span>
        <span class="monitor-bar__title">{{ monitorTitle }}</span>
        <span v-if="monitor" class="monitor-bar__meta">共 {{ monitor.totalVideos }} 条视频</span>
      </div>

      <div v-if="monitor" class="monitor-bar__stats">
        <template v-if="progressRun">
          <span>
            本轮进度
            <strong>{{ progressDone }} / {{ progressTotal }}</strong>
          </span>
          <span>成功 {{ progressRun.successCount }}</span>
          <span v-if="progressRun.failedCount > 0" class="monitor-bar__failed">
            失败 {{ progressRun.failedCount }}
          </span>
        </template>
        <template v-else-if="monitor.lastRun">
          <span>
            上次采集
            <strong>{{ RUN_STATUS_LABELS[monitor.lastRun.status] ?? monitor.lastRun.status }}</strong>
          </span>
          <span>成功 {{ monitor.lastRun.successCount }}</span>
          <span v-if="monitor.lastRun.failedCount > 0" class="monitor-bar__failed">
            失败 {{ monitor.lastRun.failedCount }}
          </span>
          <span>{{ formatDate(monitor.lastRun.finishedAt ?? monitor.lastRun.startedAt) }}</span>
        </template>
        <span v-else>还没有采集记录</span>
      </div>

      <div class="monitor-bar__actions">
        <span v-if="monitor?.enabled && monitor.nextRunAt" class="monitor-bar__next">
          下次执行 {{ formatDate(monitor.nextRunAt) }}
        </span>
        <button
          class="btn btn--quiet btn--sm monitor-bar__toggle"
          :class="{ 'is-on': autoRefresh }"
          type="button"
          @click="autoRefresh = !autoRefresh"
        >
          自动刷新 {{ autoRefresh ? '开' : '关' }}
        </button>
        <button
          class="btn btn--quiet btn--sm"
          type="button"
          :disabled="retrying || collecting"
          @click="retryFailedVideos"
        >
          {{ retrying ? '启动中…' : '失败重采' }}
        </button>
        <button class="btn btn--quiet btn--sm" type="button" @click="openHistory">
          采集历史
        </button>
      </div>

      <div
        v-if="progressRun"
        class="monitor-progress"
        role="progressbar"
        :aria-valuenow="progressPercent"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="`采集进度 ${progressPercent}%`"
      >
        <div class="monitor-progress__head">
          <span>已处理 <strong>{{ progressDone }} / {{ progressTotal }}</strong></span>
          <span>{{ progressPercent }}%</span>
        </div>
        <div class="monitor-progress__track">
          <span
            class="monitor-progress__bar"
            :class="{ 'monitor-progress__bar--done': progressPercent >= 100 }"
            :style="{ width: `${progressPercent}%` }"
          ></span>
        </div>
      </div>
    </section>

    <p
      v-if="notice"
      class="notice"
      :class="`notice--${notice.kind}`"
      role="status"
      aria-live="polite"
    >
      {{ notice.text }}
    </p>

    <DouyinOverview
      :overview="douyinStore.overview"
      :loading="douyinStore.overviewLoading"
      :window="douyinStore.window"
      @open="openDrawer"
    />

    <DouyinCharts
      :charts="douyinStore.charts"
      :loading="douyinStore.chartsLoading"
      :window="douyinStore.window"
      :video-ids="douyinStore.chartVideoIds"
      :videos="douyinStore.videos"
      @open="openDrawer"
      @select-videos="douyinStore.setChartVideoIds"
    />

    <section class="panel toolbar">
      <div class="toolbar__row">
        <div class="toolbar__search">
          <input
            v-model="douyinStore.keyword"
            class="toolbar__input"
            type="search"
            placeholder="搜索标题或作者"
            spellcheck="false"
            @keyup.enter="applyFilters"
          />
          <button class="btn btn--quiet" type="button" @click="applyFilters">查询</button>
        </div>

        <div class="toolbar__group">
          <label class="toolbar__label" for="douyin-status">状态</label>
          <select
            id="douyin-status"
            v-model="douyinStore.status"
            class="toolbar__select"
            @change="applyFilters"
          >
            <option v-for="option in STATUS_OPTIONS" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="toolbar__group">
          <label class="toolbar__label" for="douyin-sort-group">排序</label>
          <select
            id="douyin-sort-group"
            v-model="sortGroupKey"
            class="toolbar__select"
            aria-label="排序维度"
          >
            <option v-for="group in SORT_GROUPS" :key="group.key" :value="group.key">
              {{ group.label }}
            </option>
          </select>
          <select
            id="douyin-sort"
            v-model="douyinStore.sort"
            class="toolbar__select"
            aria-label="排序指标"
            @change="applyFilters"
          >
            <option v-for="option in sortOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <button class="btn btn--quiet btn--order" type="button" @click="toggleOrder">
            {{ douyinStore.order === 'desc' ? '降序 ↓' : '升序 ↑' }}
          </button>
        </div>
      </div>

      <div class="toolbar__row toolbar__row--windows">
        <span class="toolbar__label">时间窗口</span>
        <div class="segmented" role="group" aria-label="时间窗口">
          <button
            v-for="option in WINDOW_OPTIONS"
            :key="option.value"
            class="segmented__item"
            :class="{ 'segmented__item--active': douyinStore.window === option.value }"
            type="button"
            @click="selectWindow(option.value)"
          >
            {{ option.label }}
          </button>
        </div>
        <span class="toolbar__hint">增长值 = 窗口内最后一次采集 − 第一次采集</span>
      </div>
    </section>

    <section class="panel" :aria-busy="pageLoading">
      <div v-if="pageLoading" class="skeleton" aria-hidden="true">
        <div v-for="row in 4" :key="row" class="skeleton__row">
          <span class="skeleton__cell skeleton__cell--wide"></span>
          <span class="skeleton__cell"></span>
          <span class="skeleton__cell skeleton__cell--short"></span>
        </div>
      </div>

      <div v-else-if="loadError" class="state">
        <span class="state__icon state__icon--danger" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M12 8v5m0 3.5v.01M10.29 3.86L2.82 17a2 2 0 001.74 3h14.88a2 2 0 001.74-3L13.71 3.86a2 2 0 00-3.42 0z"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <h2 class="state__title">无法加载视频列表</h2>
        <p class="state__lead">{{ loadError }}</p>
        <button class="btn btn--primary" type="button" @click="load">重试</button>
      </div>

      <div v-else-if="!douyinStore.videos.length" class="state">
        <span class="state__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M15 8.5V6.2a2 2 0 00-2.6-1.92l-5.6 1.6A2 2 0 005.4 7.8v8.4a2 2 0 001.4 1.92l5.6 1.6A2 2 0 0015 17.8v-2.3m0-7 5 3.5-5 3.5"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <h2 class="state__title">还没有视频</h2>
        <p class="state__lead">点击右上角「添加视频」，粘贴抖音分享文本即可导入监控列表。</p>
      </div>

      <div v-else>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th scope="col" class="table__check-head">
                  <input
                    class="cell-check__input"
                    type="checkbox"
                    :checked="allSelected"
                    :indeterminate.prop="someSelected"
                    :disabled="collecting"
                    aria-label="全选当前页视频"
                    @change="toggleSelectAll"
                  />
                </th>
                <th scope="col" class="table__menu-head" aria-label="操作菜单"></th>
                <th scope="col">视频</th>
                <th scope="col">作者</th>
                <th scope="col" class="table__num">点赞</th>
                <th scope="col" class="table__num">评论</th>
                <th scope="col" class="table__num">分享</th>
                <th scope="col" class="table__num">收藏</th>
                <th scope="col" class="table__num">增长</th>
                <th scope="col">采集状态</th>
                <th scope="col">链接</th>
                <th scope="col">导入时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="video in douyinStore.videos" :key="video.id">
                <td class="cell-check" data-label="选择">
                  <input
                    class="cell-check__input"
                    type="checkbox"
                    :checked="selectedVideoIds.includes(video.id)"
                    :disabled="collecting"
                    :aria-label="`选择：${videoLabel(video.author, video.title)}`"
                    @change="toggleSelect(video.id)"
                  />
                </td>
                <td class="cell-menu">
                  <button
                    class="menu-trigger"
                    type="button"
                    aria-haspopup="menu"
                    :aria-expanded="menuVideoId === video.id"
                    :aria-label="`操作：${videoLabel(video.author, video.title)}`"
                    @click.stop="toggleMenu($event, video)"
                  >
                    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <path
                        d="M12 6.5h.01M12 12h.01M12 17.5h.01"
                        stroke="currentColor"
                        stroke-width="2.4"
                        stroke-linecap="round"
                      />
                    </svg>
                  </button>

                  <Teleport to="body">
                    <div
                      v-if="menuVideoId === video.id"
                      class="menu"
                      role="menu"
                      :style="{ top: `${menuPos.top}px`, left: `${menuPos.left}px` }"
                      @click.stop
                    >
                      <button
                        class="menu__item"
                        type="button"
                        role="menuitem"
                        :disabled="collecting || busyId !== null"
                        @click="collectVideo(video)"
                      >
                        {{ collecting ? '已有采集任务在运行' : '单条采集' }}
                      </button>
                      <button
                        class="menu__item menu__item--danger"
                        type="button"
                        role="menuitem"
                        :disabled="busyId !== null"
                        @click="removeVideo(video.id, videoLabel(video.author, video.title))"
                      >
                        {{ busyId === video.id ? '删除中…' : '删除' }}
                      </button>
                    </div>
                  </Teleport>
                </td>
                <td data-label="视频">
                  <button class="cell-title cell-title--button" type="button" @click="openDrawer(video)">
                    {{ videoLabel(video.author, video.title) }}
                  </button>
                </td>
                <td data-label="作者" class="cell-author">{{ video.author || '—' }}</td>
                <td data-label="点赞" class="cell-num">{{ formatCount(video.latest?.diggCount) }}</td>
                <td data-label="评论" class="cell-num">{{ formatCount(video.latest?.commentCount) }}</td>
                <td data-label="分享" class="cell-num">{{ formatCount(video.latest?.shareCount) }}</td>
                <td data-label="收藏" class="cell-num">{{ formatCount(video.latest?.collectCount) }}</td>
                <td data-label="增长" class="cell-num cell-growth">
                  <template v-if="video.growth?.available">
                    +{{ formatCount(video.growth.interaction) }}
                  </template>
                  <template v-else>—</template>
                </td>
                <td data-label="采集状态" class="cell-status">
                  <span class="cell-status__body">
                    <span
                      class="badge"
                      :class="`badge--${videoStatus(video).tone}`"
                      :title="video.latest?.lastError ?? undefined"
                    >
                      {{ videoStatus(video).label }}
                    </span>
                    <span
                      v-if="video.latest?.capturedAt && !video.latest?.lastError"
                      class="cell-status__time"
                    >
                      {{ formatDate(video.latest.capturedAt) }}
                    </span>
                  </span>
                </td>
                <td data-label="链接">
                  <a class="cell-link" :href="video.url" target="_blank" rel="noopener noreferrer">
                    {{ video.url }}
                  </a>
                </td>
                <td data-label="导入时间" class="cell-date">{{ formatDate(video.createdAt) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="douyinStore.pages > 1" class="pager">
          <button class="btn btn--quiet" type="button" :disabled="!canPrev" @click="goPrev">
            上一页
          </button>
          <span class="pager__info">{{ pageInfo }}</span>
          <button class="btn btn--quiet" type="button" :disabled="!canNext" @click="goNext">
            下一页
          </button>
        </div>
      </div>
    </section>

    <div
      v-if="modalOpen"
      class="modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="import-modal-title"
      @keydown="onModalKeydown"
    >
      <div class="modal__scrim" @click="closeModal"></div>
      <div class="modal__card">
        <h2 id="import-modal-title" class="modal__title">添加抖音视频</h2>
        <p class="modal__lead">粘贴抖音分享文本，支持一次多行，逐行解析链接。</p>

        <textarea
          ref="modalInput"
          v-model="shareText"
          class="modal__input"
          rows="6"
          placeholder="例如：2.58 复制打开抖音，看看【折光AI的作品】…… https://v.douyin.com/0tmeYVuCfVU/ ……"
          spellcheck="false"
          :disabled="importing"
          @keydown.esc="closeModal"
        ></textarea>

        <div class="modal__actions">
          <button class="btn btn--quiet" type="button" :disabled="importing" @click="closeModal">
            取消
          </button>
          <button
            class="btn btn--primary"
            type="button"
            :disabled="!canImport"
            @click="submitImport"
          >
            {{ importing ? '导入中…' : '解析并导入' }}
          </button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="historyOpen"
        class="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="history-modal-title"
      >
        <div class="modal__scrim" @click="historyOpen = false"></div>
        <div class="modal__card modal__card--wide">
          <div class="modal__head">
            <h2 id="history-modal-title" class="modal__title">采集历史</h2>
            <button
              class="modal__close"
              type="button"
              aria-label="关闭"
              @click="historyOpen = false"
            >
              ×
            </button>
          </div>
          <p class="modal__lead">最近 20 次采集记录，包含定时、手动与导入触发的任务。</p>

          <div v-if="douyinStore.runsLoading" class="history__empty">加载中…</div>
          <div v-else-if="!douyinStore.runs.length" class="history__empty">暂无采集记录</div>
          <div v-else class="history__scroll">
            <table class="history">
              <thead>
                <tr>
                  <th scope="col">状态</th>
                  <th scope="col">任务</th>
                  <th scope="col">触发方式</th>
                  <th scope="col">开始时间</th>
                  <th scope="col">耗时</th>
                  <th scope="col">成功 / 失败</th>
                  <th scope="col">说明</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="run in douyinStore.runs" :key="run.id">
                  <td>
                    <span class="badge" :class="`badge--${run.status}`">
                      {{ RUN_STATUS_LABELS[run.status] ?? run.status }}
                    </span>
                  </td>
                  <td>#{{ run.id }}</td>
                  <td>{{ TRIGGER_LABELS[run.triggerType] ?? run.triggerType }}</td>
                  <td>{{ formatDate(run.startedAt) }}</td>
                  <td>{{ formatDuration(run.startedAt, run.finishedAt) }}</td>
                  <td>{{ run.successCount }} / {{ run.failedCount }}</td>
                  <td class="history__message" :title="run.message ?? ''">
                    {{ run.message || '—' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="modal__actions">
            <button class="btn btn--quiet" type="button" @click="historyOpen = false">
              关闭
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="selectedCount > 0" class="bulk-bar" role="region" aria-label="批量操作">
        <span class="bulk-bar__count">
          已选 <strong>{{ selectedCount }}</strong> 条
        </span>
        <button
          class="btn btn--primary btn--sm"
          type="button"
          :disabled="collecting"
          @click="collectSelected"
        >
          {{ collecting ? '采集中…' : `采集选中（${selectedCount}）` }}
        </button>
        <button
          class="btn btn--quiet btn--sm"
          type="button"
          :disabled="collecting"
          @click="clearSelection"
        >
          取消选择
        </button>
      </div>
    </Teleport>

    <Teleport to="body">
      <DouyinVideoDrawer
        v-if="drawerVideo"
        :video="drawerVideo"
        :window="douyinStore.window"
        @close="drawerVideo = null"
      />
    </Teleport>
  </div>
</template>

<style scoped>
/* ---------- 页头操作 ---------- */
.page__actions {
  display: flex;
  gap: 0.5rem;
}

.btn--sm {
  padding: 0.3125rem 0.625rem;
  font-size: 0.75rem;
}

/* ---------- 多选批量操作条 ---------- */
.bulk-bar {
  position: fixed;
  bottom: 1.5rem;
  left: 50%;
  z-index: 80;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.5rem 0.5rem 1rem;
  background: var(--surface-solid);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-pill);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.28);
  transform: translateX(-50%);
  animation: bulk-rise 0.18s ease both;
}

.bulk-bar__count {
  font-size: 0.8125rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.bulk-bar__count strong {
  color: var(--text);
  font-weight: 600;
}

@keyframes bulk-rise {
  from {
    opacity: 0;
    transform: translate(-50%, 8px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

/* ---------- 采集状态条 ---------- */
.monitor-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.625rem 1rem;
  padding: 0.75rem 1.25rem;
  background: var(--surface);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.monitor-bar--running {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-ring);
}

.monitor-bar__main {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.monitor-bar__dot {
  flex: none;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-subtle);
}

.monitor-bar__dot--on {
  background: var(--success);
}

.monitor-bar__dot--running {
  background: var(--accent);
  animation: monitor-pulse 1.4s ease-in-out infinite;
}

@keyframes monitor-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 var(--accent-ring);
  }
  50% {
    box-shadow: 0 0 0 5px var(--accent-ring);
  }
}

.monitor-bar__title {
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.monitor-bar__meta,
.monitor-bar__stats,
.monitor-bar__next {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.monitor-bar__stats {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.monitor-bar__stats strong {
  color: var(--text);
  font-weight: 600;
}

.monitor-bar__failed {
  color: var(--danger);
}

.monitor-bar__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

.monitor-bar__next {
  white-space: nowrap;
}

.monitor-bar__toggle.is-on {
  color: var(--accent);
}

.monitor-progress {
  display: grid;
  flex: 1 1 100%;
  gap: 0.375rem;
}

.monitor-progress__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.monitor-progress__head strong {
  color: var(--text);
  font-weight: 600;
}

.monitor-progress__track {
  height: 6px;
  overflow: hidden;
  background: var(--field-bg);
  border-radius: var(--radius-pill);
}

.monitor-progress__bar {
  display: block;
  height: 100%;
  background: var(--accent);
  border-radius: inherit;
  transition:
    width 0.4s ease,
    background 0.2s ease;
}

.monitor-progress__bar--done {
  background: var(--success);
}

/* ---------- 工具栏 ---------- */
.toolbar {
  display: grid;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
}

.toolbar__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.toolbar__search {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1 1 220px;
  min-width: 0;
}

.toolbar__input {
  flex: 1;
  min-width: 0;
  padding: 0.5rem 0.75rem;
  font-family: inherit;
  font-size: 0.875rem;
  color: var(--text);
  background: var(--field-bg);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  outline: none;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.toolbar__input::placeholder {
  color: var(--text-subtle);
}

.toolbar__input:hover {
  background: var(--field-bg-hover);
}

.toolbar__input:focus {
  background: var(--field-bg-focus);
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-ring);
}

.toolbar__group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.toolbar__label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-subtle);
  white-space: nowrap;
}

.toolbar__select {
  padding: 0.4375rem 1.75rem 0.4375rem 0.625rem;
  font-family: inherit;
  font-size: 0.8125rem;
  color: var(--text);
  background-color: var(--field-bg);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  outline: none;
  cursor: pointer;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.toolbar__select:hover {
  background-color: var(--field-bg-hover);
}

.toolbar__select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-ring);
}

.btn--order {
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.toolbar__hint {
  margin-left: auto;
  font-size: 0.6875rem;
  color: var(--text-subtle);
}

.segmented {
  display: inline-flex;
  gap: 2px;
  padding: 2px;
  background: var(--field-bg);
  border-radius: var(--radius-pill);
}

.segmented__item {
  padding: 0.3125rem 0.75rem;
  font-family: inherit;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
  background: transparent;
  border: none;
  border-radius: var(--radius-pill);
  cursor: pointer;
  white-space: nowrap;
  transition:
    color 0.16s ease,
    background 0.16s ease,
    box-shadow 0.16s ease;
}

.segmented__item:hover {
  color: var(--text);
}

.segmented__item--active {
  color: var(--text);
  background: var(--surface-solid);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}


/* ---------- 提示条 ---------- */
.notice {
  margin: 0;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  border-radius: var(--radius-md);
  animation: fade-in 0.28s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.notice--success {
  color: var(--success);
  background: var(--success-bg);
}

.notice--error {
  color: var(--danger);
  background: var(--danger-bg);
}

/* ---------- 页头「添加」按钮 ---------- */
.btn--add {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.btn--add svg {
  width: 16px;
  height: 16px;
}

/* ---------- 分页 ---------- */
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 0.875rem 1.25rem;
  border-top: 1px solid var(--separator);
}

.pager__info {
  font-size: 0.8125rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

/* ---------- 弹窗 ---------- */
.modal {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.25rem;
  z-index: 100;
}

.modal__scrim {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.42);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  animation: fade-in 0.2s ease both;
}

.modal__card {
  position: relative;
  display: grid;
  gap: 0.75rem;
  width: min(560px, 100%);
  padding: 1.5rem;
  background: var(--surface-solid);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
  animation: rise 0.28s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.modal__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: -0.022em;
}

.modal__lead {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.modal__input {
  width: 100%;
  padding: 0.75rem 0.875rem;
  font-family: inherit;
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--text);
  background: var(--field-bg);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  outline: none;
  resize: vertical;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.modal__input::placeholder {
  color: var(--text-subtle);
}

.modal__input:hover:not(:disabled) {
  background: var(--field-bg-hover);
}

.modal__input:focus {
  background: var(--field-bg-focus);
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-ring);
}

.modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.modal__card--wide {
  width: min(820px, 100%);
}

.modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.modal__close {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  padding: 0;
  font-size: 1.25rem;
  line-height: 1;
  color: var(--text-muted);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition:
    color 0.16s ease,
    background 0.16s ease;
}

.modal__close:hover {
  color: var(--text);
  background: var(--field-bg-hover);
}

/* ---------- 采集历史 ---------- */
.history__empty {
  padding: 2rem 1rem;
  font-size: 0.875rem;
  text-align: center;
  color: var(--text-muted);
}

.history__scroll {
  max-height: min(52vh, 420px);
  overflow: auto;
  border: 1px solid var(--separator);
  border-radius: var(--radius-md);
}

.history {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.history th {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 0.5rem 0.75rem;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  text-align: left;
  white-space: nowrap;
  color: var(--text-subtle);
  background: var(--surface-solid);
  border-bottom: 1px solid var(--separator);
}

.history td {
  padding: 0.5rem 0.75rem;
  white-space: nowrap;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.history tbody tr + tr td {
  border-top: 1px solid var(--separator);
}

.history__message {
  max-width: 24ch;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-muted);
}

.badge {
  display: inline-flex;
  padding: 0.125rem 0.5rem;
  font-size: 0.6875rem;
  font-weight: 600;
  border-radius: var(--radius-pill);
  white-space: nowrap;
}

.badge--running {
  color: var(--accent);
  background: var(--accent-soft);
}

.badge--success {
  color: var(--success);
  background: var(--success-bg);
}

.badge--partial {
  color: #b25000;
  background: rgba(255, 149, 0, 0.16);
}

.badge--failed {
  color: var(--danger);
  background: var(--danger-bg);
}

.badge--pending {
  color: var(--text-muted);
  background: var(--field-bg);
}

/* ---------- 骨架 ---------- */
.skeleton {
  display: grid;
  gap: 1px;
  background: var(--separator);
}

.skeleton__row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--surface-solid);
}

.skeleton__cell {
  flex: 1;
  height: 10px;
  border-radius: var(--radius-pill);
  background: var(--field-bg);
  animation: pulse 1.4s ease-in-out infinite;
}

.skeleton__cell--wide {
  flex: 1.4;
}

.skeleton__cell--short {
  flex: 0.7;
}

/* ---------- 状态 ---------- */
.state {
  display: grid;
  justify-items: center;
  gap: 0.5rem;
  padding: clamp(2.5rem, 8vw, 4rem) 1.5rem;
  text-align: center;
}

.state__icon {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  margin-bottom: 0.5rem;
  border-radius: var(--radius-md);
  background: var(--field-bg);
  color: var(--text-subtle);
}

.state__icon--danger {
  background: var(--danger-bg);
  color: var(--danger);
}

.state__icon svg {
  width: 24px;
  height: 24px;
}

.state__title {
  margin: 0;
  font-size: 1.0625rem;
  font-weight: 600;
  letter-spacing: -0.022em;
}

.state__lead {
  margin: 0 0 0.75rem;
  max-width: 34ch;
  font-size: 0.875rem;
  color: var(--text-muted);
}

/* ---------- 表格 ---------- */
.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.table thead th {
  padding: 0.75rem 1.25rem;
  text-align: left;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-subtle);
  background: transparent;
  border-bottom: 1px solid var(--separator);
  white-space: nowrap;
}

.table__num {
  text-align: right;
}

.table__check-head,
.cell-check {
  width: 1%;
  padding-right: 0.25rem;
  padding-left: 1.25rem;
  white-space: nowrap;
}

.cell-check__input {
  width: 15px;
  height: 15px;
  accent-color: var(--accent);
  cursor: pointer;
}

.cell-check__input:disabled {
  cursor: not-allowed;
}

.table__menu-head,
.cell-menu {
  width: 1%;
  padding-right: 0.25rem;
  padding-left: 1rem;
  white-space: nowrap;
}

.menu-trigger {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  padding: 0;
  color: var(--text-muted);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition:
    color 0.16s ease,
    background 0.16s ease;
}

.menu-trigger:hover {
  color: var(--text);
  background: var(--field-bg-hover);
}

.menu-trigger svg {
  width: 18px;
  height: 18px;
}

.menu {
  position: fixed;
  z-index: 60;
  display: grid;
  min-width: 160px;
  padding: 0.25rem;
  background: var(--surface-solid);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.24);
  animation: fade-in 0.16s ease both;
}

.menu__item {
  padding: 0.5rem 0.625rem;
  font-family: inherit;
  font-size: 0.8125rem;
  text-align: left;
  color: var(--text);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.16s ease;
}

.menu__item:hover:not(:disabled) {
  background: var(--field-bg-hover);
}

.menu__item:disabled {
  color: var(--text-subtle);
  cursor: not-allowed;
}

.menu__item--danger {
  color: var(--danger);
}

.table tbody tr {
  transition: background 0.16s ease;
}

.table tbody tr:nth-child(n + 2) td {
  border-top: 1px solid var(--separator);
}

.table tbody tr:hover {
  background: var(--field-bg);
}

.table td {
  padding: 0.875rem 1.25rem;
  vertical-align: middle;
  color: var(--text);
}

.cell-title {
  display: block;
  max-width: 28ch;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
  letter-spacing: -0.01em;
}

.cell-title--button {
  padding: 0;
  font-family: inherit;
  font-size: inherit;
  text-align: left;
  color: var(--text);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color 0.16s ease;
}

.cell-title--button:hover {
  color: var(--accent);
  text-decoration: underline;
}

.cell-author {
  color: var(--text-muted);
  white-space: nowrap;
}

.cell-link {
  display: block;
  max-width: 32ch;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--accent);
  text-decoration: none;
}

.cell-link:hover {
  text-decoration: underline;
}

.cell-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.cell-growth {
  font-weight: 600;
  color: var(--success);
}

.cell-date {
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.cell-status {
  white-space: nowrap;
}

.cell-status__body {
  display: inline-grid;
  justify-items: start;
  gap: 0.25rem;
}

.cell-status__time {
  font-size: 0.6875rem;
  color: var(--text-subtle);
  font-variant-numeric: tabular-nums;
}

/* ---------- 响应式：表格 → 卡片 ---------- */
@media (max-width: 720px) {
  .page__head {
    align-items: flex-start;
  }

  .page__actions {
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .bulk-bar {
    bottom: 0.75rem;
    width: calc(100% - 1.5rem);
    justify-content: center;
    border-radius: var(--radius-lg);
  }

  .monitor-bar__actions {
    width: 100%;
    margin-left: 0;
  }

  .monitor-bar__next {
    flex: 1 1 100%;
  }

  .toolbar__row {
    align-items: stretch;
  }

  .toolbar__search,
  .toolbar__group {
    flex: 1 1 100%;
  }

  .toolbar__hint {
    margin-left: 0;
  }

  .segmented {
    flex-wrap: wrap;
    border-radius: var(--radius-md);
  }

  .pager {
    gap: 0.5rem;
  }

  .table thead {
    display: none;
  }

  .table,
  .table tbody,
  .table tr,
  .table td {
    display: block;
    width: 100%;
  }

  .table tbody tr {
    padding: 0.5rem 0;
  }

  .table tbody tr:nth-child(n + 2) {
    border-top: 1px solid var(--separator);
  }

  .table tbody tr:nth-child(n + 2) td {
    border-top: none;
  }

  .table td {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.4375rem 1.25rem;
    text-align: right;
  }

  .table td::before {
    content: attr(data-label);
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-subtle);
  }

  .cell-title,
  .cell-link {
    max-width: 60vw;
  }

  .cell-check {
    justify-content: flex-start;
    padding-top: 0.5rem;
    padding-bottom: 0.25rem;
  }

  .cell-check::before {
    display: none;
  }

  .cell-menu {
    justify-content: flex-start;
    padding-top: 0.5rem;
    padding-bottom: 0.25rem;
  }

  .cell-menu::before {
    display: none;
  }
}
</style>
