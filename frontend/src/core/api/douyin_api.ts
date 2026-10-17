import apiClient from '@/core/api/client'
import {
  ImportDouyinVideosDto,
  PaginatedDouyinVideosDto,
  type ImportDouyinVideosJson,
  type PaginatedDouyinVideosJson
} from '@/core/types/dto/douyin_video.dto'

export const douyinApi = {
  getAll: async (page = 1, perPage = 20) => {
    const response = await apiClient.get<PaginatedDouyinVideosJson>('/douyin/videos', {
      params: { page, per_page: perPage }
    })
    return PaginatedDouyinVideosDto.fromJson(response.data)
  },

  import: async (text: string) => {
    const response = await apiClient.post<ImportDouyinVideosJson>('/douyin/videos', { text })
    return ImportDouyinVideosDto.fromJson(response.data)
  },

  delete: (id: number) => apiClient.delete(`/douyin/videos/${id}`)
}
