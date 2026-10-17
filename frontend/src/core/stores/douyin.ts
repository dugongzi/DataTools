import { defineStore } from 'pinia'
import { ref } from 'vue'
import { douyinApi } from '@/core/api/douyin_api.ts'
import { DouyinVideo } from '@/core/types/entities/douyin_video.entity'
import { DouyinVideoDto } from '@/core/types/dto/douyin_video.dto'

export const DEFAULT_PER_PAGE = 20

export const useDouyinStore = defineStore('douyin', () => {
  const videos = ref<DouyinVideo[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const page = ref(1)
  const perPage = ref(DEFAULT_PER_PAGE)
  const total = ref(0)
  const pages = ref(0)

  async function fetchVideos(targetPage = page.value) {
    loading.value = true
    error.value = null
    const requested = Math.max(1, Math.floor(targetPage))
    try {
      const result = await douyinApi.getAll(requested, perPage.value)
      videos.value = result.items.map((dto: DouyinVideoDto) => dto.toEntity())
      page.value = result.page
      perPage.value = result.per_page
      total.value = result.total
      pages.value = result.pages
    } catch (e) {
      error.value = 'Failed to fetch douyin videos'
      console.error(e)
    } finally {
      loading.value = false
    }
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
      return { created, skipped: result.skipped }
    } catch (e) {
      error.value = 'Failed to import douyin videos'
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
      // If the current page emptied, step back and refetch.
      if (videos.value.length === 0 && page.value > 1) {
        await fetchVideos(page.value - 1)
      }
    } catch (e) {
      error.value = 'Failed to delete douyin video'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    videos,
    loading,
    error,
    page,
    perPage,
    total,
    pages,
    fetchVideos,
    goToPage,
    importVideos,
    deleteVideo
  }
})
