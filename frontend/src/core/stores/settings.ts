import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi } from '@/core/api/settings_api'
import { douyinApi } from '@/core/api/douyin_api'
import {
  DouyinMonitorConfig,
  DouyinMonitorStatus
} from '@/core/types/entities/douyin_monitor_config.entity'
import type { UpdateDouyinMonitorConfigJson } from '@/core/types/dto/douyin_monitor_config.dto'

export const useSettingsStore = defineStore('settings', () => {
  const config = ref<DouyinMonitorConfig | null>(null)
  const status = ref<DouyinMonitorStatus | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const triggering = ref(false)
  const error = ref<string | null>(null)
  const fieldErrors = ref<Record<string, string>>({})

  async function load() {
    loading.value = true
    error.value = null
    try {
      const [configDto, monitorStatus] = await Promise.all([
        settingsApi.getMonitorConfig(),
        douyinApi.getMonitorStatus()
      ])
      config.value = configDto.toEntity()
      status.value = monitorStatus
    } catch (e) {
      error.value = 'Failed to load monitor settings'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function save(payload: UpdateDouyinMonitorConfigJson) {
    saving.value = true
    fieldErrors.value = {}
    try {
      const configDto = await settingsApi.updateMonitorConfig(payload)
      config.value = configDto.toEntity()
      await refreshStatus()
      return config.value
    } catch (e) {
      const fields = (e as { response?: { data?: { fields?: Record<string, string> } } })?.response
        ?.data?.fields
      if (fields) fieldErrors.value = fields
      throw e
    } finally {
      saving.value = false
    }
  }

  async function refreshStatus() {
    try {
      status.value = await douyinApi.getMonitorStatus()
    } catch (e) {
      console.error(e)
    }
  }

  async function triggerRun(videoIds?: number[]) {
    triggering.value = true
    try {
      const result = await douyinApi.triggerRun(videoIds)
      await refreshStatus()
      return result
    } finally {
      triggering.value = false
    }
  }

  return {
    config,
    status,
    loading,
    saving,
    triggering,
    error,
    fieldErrors,
    load,
    save,
    refreshStatus,
    triggerRun
  }
})
