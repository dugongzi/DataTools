import apiClient from '@/core/api/client'
import {
  DouyinChartsDto,
  DouyinOverviewDto,
  DouyinSnapshotsDto,
  ImportDouyinVideosDto,
  PaginatedDouyinVideosDto,
  type DouyinChartsJson,
  type DouyinOverviewJson,
  type DouyinSnapshotsJson,
  type DouyinVideoQuery,
  type DouyinWindow,
  type ImportDouyinVideosJson,
  type PaginatedDouyinVideosJson
} from '@/core/types/dto/douyin_video.dto'
import {
  DouyinMonitorRunDto,
  DouyinMonitorStatusDto,
  type DouyinMonitorRunJson,
  type DouyinMonitorRunListJson,
  type DouyinMonitorStatusJson,
  type RetryMonitorRunJson,
  type TriggerMonitorRunJson
} from '@/core/types/dto/douyin_monitor_config.dto'
import type { DouyinMonitorRun } from '@/core/types/entities/douyin_monitor_config.entity'

function queryParams(query: DouyinVideoQuery) {
  return {
    q: query.q || undefined,
    status: query.status && query.status !== 'all' ? query.status : undefined,
    sort: query.sort,
    order: query.order,
    window: query.window
  }
}

function filenameFrom(disposition?: string) {
  if (!disposition) return null
  const match = /filename="?([^";]+)"?/.exec(disposition)
  return match ? match[1] : null
}

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export const douyinApi = {
  getAll: async (page = 1, perPage = 20, query: DouyinVideoQuery = {}) => {
    const response = await apiClient.get<PaginatedDouyinVideosJson>('/douyin/videos', {
      params: {
        page,
        per_page: perPage,
        ...queryParams(query)
      }
    })
    return PaginatedDouyinVideosDto.fromJson(response.data)
  },

  getOverview: async (window: DouyinWindow = '24h', top = 3) => {
    const response = await apiClient.get<DouyinOverviewJson>('/douyin/monitor/overview', {
      params: { window, top }
    })
    return DouyinOverviewDto.fromJson(response.data).toEntity()
  },

  getCharts: async (window: DouyinWindow = '24h', top = 8, videoIds: number[] = []) => {
    const response = await apiClient.get<DouyinChartsJson>('/douyin/monitor/charts', {
      params: {
        window,
        top,
        video_ids: videoIds.length > 0 ? videoIds.join(',') : undefined
      }
    })
    return DouyinChartsDto.fromJson(response.data).toEntity()
  },

  getSnapshots: async (videoId: number, window?: DouyinWindow, limit = 200) => {
    const response = await apiClient.get<DouyinSnapshotsJson>(
      `/douyin/videos/${videoId}/snapshots`,
      { params: { window, limit } }
    )
    return DouyinSnapshotsDto.fromJson(response.data).toEntity()
  },

  import: async (text: string) => {
    const response = await apiClient.post<ImportDouyinVideosJson>('/douyin/videos', { text })
    return ImportDouyinVideosDto.fromJson(response.data)
  },

  delete: (id: number) => apiClient.delete(`/douyin/videos/${id}`),

  getMonitorStatus: async () => {
    const response = await apiClient.get<DouyinMonitorStatusJson>('/douyin/monitor/status')
    return DouyinMonitorStatusDto.fromJson(response.data).toEntity()
  },

  triggerRun: async (videoIds?: number[]) => {
    const response = await apiClient.post<TriggerMonitorRunJson>(
      '/douyin/monitor/run',
      videoIds && videoIds.length > 0 ? { video_ids: videoIds } : {}
    )
    return {
      runId: response.data.run_id,
      run: DouyinMonitorRunDto.fromJson(response.data.run).toEntity()
    }
  },

  getRun: async (runId: number) => {
    const response = await apiClient.get<DouyinMonitorRunJson>(`/douyin/monitor/runs/${runId}`)
    return DouyinMonitorRunDto.fromJson(response.data).toEntity()
  },

  getRuns: async (limit = 20): Promise<DouyinMonitorRun[]> => {
    const response = await apiClient.get<DouyinMonitorRunListJson>('/douyin/monitor/runs', {
      params: { limit }
    })
    return response.data.items.map((json) => DouyinMonitorRunDto.fromJson(json).toEntity())
  },

  retryFailed: async () => {
    const response = await apiClient.post<RetryMonitorRunJson>('/douyin/monitor/run/failed')
    return {
      runId: response.data.run_id,
      total: response.data.total,
      run: DouyinMonitorRunDto.fromJson(response.data.run).toEntity()
    }
  },

  exportVideos: async (query: DouyinVideoQuery = {}) => {
    const response = await apiClient.get<Blob>('/douyin/videos/export', {
      params: queryParams(query),
      responseType: 'blob',
      timeout: 60000
    })
    download(
      response.data,
      filenameFrom(response.headers['content-disposition']) ?? 'douyin_videos.csv'
    )
  },

  exportSnapshots: async (videoId: number, window?: DouyinWindow) => {
    const response = await apiClient.get<Blob>(
      `/douyin/videos/${videoId}/snapshots/export`,
      {
        params: { window },
        responseType: 'blob',
        timeout: 60000
      }
    )
    download(
      response.data,
      filenameFrom(response.headers['content-disposition']) ??
        `douyin_video_${videoId}_snapshots.csv`
    )
  }
}

