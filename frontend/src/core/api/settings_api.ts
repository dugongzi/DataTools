import apiClient from '@/core/api/client'
import {
  DouyinMonitorConfigDto,
  type DouyinMonitorConfigJson,
  type UpdateDouyinMonitorConfigJson
} from '@/core/types/dto/douyin_monitor_config.dto'

export const settingsApi = {
  getMonitorConfig: async () => {
    const response = await apiClient.get<DouyinMonitorConfigJson>('/douyin/monitor/config')
    return DouyinMonitorConfigDto.fromJson(response.data)
  },

  updateMonitorConfig: async (payload: UpdateDouyinMonitorConfigJson) => {
    const response = await apiClient.put<DouyinMonitorConfigJson>('/douyin/monitor/config', payload)
    return DouyinMonitorConfigDto.fromJson(response.data)
  }
}
