import { defineStore } from 'pinia'
import { ref } from 'vue'
import { douyinApi } from '@/core/api/douyin_api.ts'
import { DouyinCharts, DouyinOverview, DouyinVideo } from '@/core/types/entities/douyin_video.entity'
import type {
  DouyinMonitorRun,
  DouyinMonitorStatus
} from '@/core/types/entities/douyin_monitor_config.entity'
import {
  DouyinVideoDto,
  type DouyinSortField,
  type DouyinSortOrder,
  type DouyinStatusFilter,
  type DouyinWindow
} from '@/core/types/dto/douyin_video.dto'


export const DEFAULT_PER_PAGE = 20

export const useDouyinStore = defineStore('douyin', () => {
  const videos = ref<DouyinVideo[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const page = ref(1)
  const perPage = ref(DEFAULT_PER_PAGE)
  const total = ref(0)
  const pages = ref(0)

  const keyword = ref('')
  const status = ref<DouyinStatusFilter>('all')
  const sort = ref<DouyinSortField>('created_at')
  const order = ref<DouyinSortOrder>('desc')
  const window = ref<DouyinWindow>('24h')

  const overview = ref<DouyinOverview | null>(null)
  const overviewLoading = ref(false)

  const charts = ref<DouyinCharts | null>(null)
  const chartsLoading = ref(false)
  const chartVideoIds = ref<number[]>([])

  const monitorStatus = ref<DouyinMonitorStatus | null>(null)
  const runs = ref<DouyinMonitorRun[]>([])
  const runsLoading = ref(false)

  async function fetchVideos(targetPage = page.value) {
    loading.value = true
    error.value = null
    const requested = Math.max(1, Math.floor(targetPage))
    try {
      const result = await douyinApi.getAll(requested, perPage.value, {
        q: keyword.value.trim(),
        status: status.value,
        sort: sort.value,
        order: order.value,
        window: window.value
      })
      videos.value = result.items.map((dto: DouyinVideoDto) => dto.toEntity())
      page.value = result.page
      perPage.value = result.per_page
      total.value = result.total
      pages.value = result.pages
    } catch (e) {
      error.value = '加载视频列表失败'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchOverview() {
    overviewLoading.value = true
    try {
      overview.value = await douyinApi.getOverview(window.value)
    } catch (e) {
      console.error(e)
    } finally {
      overviewLoading.value = false
    }
  }

  async function fetchCharts() {
    chartsLoading.value = true
    try {
      charts.value = await douyinApi.getCharts(window.value, 8, chartVideoIds.value)
    } catch (e) {
      console.error(e)
    } finally {
      chartsLoading.value = false
    }
  }

  async function setChartVideoIds(ids: number[]) {
    const next = Array.from(new Set(ids)).slice(0, 5)
    const same =
      next.length === chartVideoIds.value.length &&
      next.every((id, index) => id === chartVideoIds.value[index])
    if (same) return
    chartVideoIds.value = next
    await fetchCharts()
  }

  async function applyFilters() {
    page.value = 1
    await fetchVideos(1)
  }

  async function setWindow(next: DouyinWindow) {
    if (window.value === next) return
    window.value = next
    page.value = 1
    await Promise.all([fetchVideos(1), fetchOverview(), fetchCharts()])
  }

  async function goToPage(targetPage: number) {
    const clamped = Math.min(Math.max(1, Math.floor(targetPage)), Math.max(1, pages.value || 1))
    if (clamped === page.value) return
    await fetchVideos(clamped)
  }

  async function importVideos(text: string) {
    loading.value = true
    error.value = null
    try {
      const result = await douyinApi.import(text)
      const created = result.created.map((dto) => dto.toEntity())
      return { created, skipped: result.skipped, runId: result.runId }
    } catch (e) {
      error.value = '导入视频失败'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteVideo(id: number) {
    loading.value = true
    error.value = null
    try {
      await douyinApi.delete(id)
      videos.value = videos.value.filter((v) => v.id !== id)
      total.value = Math.max(0, total.value - 1)
      if (chartVideoIds.value.includes(id)) {
        chartVideoIds.value = chartVideoIds.value.filter((item) => item !== id)
        await fetchCharts()
      }
      // If the current page emptied, step back and refetch.
      if (videos.value.length === 0 && page.value > 1) {
        await fetchVideos(page.value - 1)
      }
    } catch (e) {
      error.value = '删除视频失败'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchMonitorStatus() {
    try {
      monitorStatus.value = await douyinApi.getMonitorStatus()
    } catch (e) {
      console.error(e)
    }
  }

  async function fetchRuns(limit = 20) {
    runsLoading.value = true
    try {
      runs.value = await douyinApi.getRuns(limit)
    } catch (e) {
      console.error(e)
    } finally {
      runsLoading.value = false
    }
  }

  async function retryFailed() {
    const result = await douyinApi.retryFailed()
    await fetchMonitorStatus()
    return result
  }

  async function exportVideos() {
    await douyinApi.exportVideos({
      q: keyword.value.trim(),
      status: status.value,
      sort: sort.value,
      order: order.value,
      window: window.value
    })
  }

  async function exportSnapshots(videoId: number) {
    await douyinApi.exportSnapshots(videoId, window.value)
  }

  async function refreshData(targetPage = page.value) {
    await Promise.all([
      fetchVideos(targetPage),
      fetchOverview(),
      fetchCharts(),
      fetchMonitorStatus()
    ])
  }

  return {
    videos,
    loading,
    error,
    page,
    perPage,
    total,
    pages,
    keyword,
    status,
    sort,
    order,
    window,
    overview,
    overviewLoading,
    charts,
    chartsLoading,
    chartVideoIds,
    monitorStatus,
    runs,
    runsLoading,
    fetchVideos,
    fetchOverview,
    fetchCharts,
    setChartVideoIds,
    fetchMonitorStatus,
    fetchRuns,
    retryFailed,
    exportVideos,
    exportSnapshots,
    refreshData,
    applyFilters,
    setWindow,
    goToPage,
    importVideos,
    deleteVideo
  }
})
