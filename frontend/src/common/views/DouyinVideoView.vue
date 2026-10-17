<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useDouyinStore } from '@/core/stores/douyin'

const douyinStore = useDouyinStore()

const pageLoading = ref(true)
const loadError = ref<string | null>(null)
const busyId = ref<number | null>(null)

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

function flash(kind: 'success' | 'error', text: string) {
  notice.value = { kind, text }
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => {
    notice.value = null
  }, 4000)
}

function formatDate(value: Date) {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) return '—'
  return value.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function load() {
  pageLoading.value = true
  loadError.value = null
  await douyinStore.fetchVideos(1)
  loadError.value = douyinStore.error
  pageLoading.value = false
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
  await douyinStore.goToPage(douyinStore.page - 1)
}

async function goNext() {
  if (!canNext.value) return
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
    const { created, skipped } = await douyinStore.importVideos(text)
    if (created.length > 0) {
      const extra = skipped.length > 0 ? `，跳过 ${skipped.length} 条已存在` : ''
      flash('success', `已导入 ${created.length} 条视频${extra}`)
      modalOpen.value = false
      shareText.value = ''
      await douyinStore.fetchVideos(1)
      loadError.value = douyinStore.error
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
  if (busyId.value !== null) return
  if (!window.confirm(`确定删除「${label}」？此操作不可撤销。`)) return

  busyId.value = id
  try {
    await douyinStore.deleteVideo(id)
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

onMounted(load)

onBeforeUnmount(() => {
  clearTimeout(noticeTimer)
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

    <p
      v-if="notice"
      class="notice"
      :class="`notice--${notice.kind}`"
      role="status"
      aria-live="polite"
    >
      {{ notice.text }}
    </p>

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
                <th scope="col">视频</th>
                <th scope="col">作者</th>
                <th scope="col">链接</th>
                <th scope="col">导入时间</th>
                <th scope="col" class="table__actions-head">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="video in douyinStore.videos" :key="video.id">
                <td data-label="视频">
                  <span class="cell-title" :title="video.title ?? undefined">
                    {{ videoLabel(video.author, video.title) }}
                  </span>
                </td>
                <td data-label="作者" class="cell-author">{{ video.author || '—' }}</td>
                <td data-label="链接">
                  <a class="cell-link" :href="video.url" target="_blank" rel="noopener noreferrer">
                    {{ video.url }}
                  </a>
                </td>
                <td data-label="导入时间" class="cell-date">{{ formatDate(video.createdAt) }}</td>
                <td data-label="操作" class="cell-actions">
                  <button
                    class="btn btn--danger"
                    type="button"
                    :disabled="busyId !== null"
                    @click="removeVideo(video.id, videoLabel(video.author, video.title))"
                  >
                    {{ busyId === video.id ? '删除中…' : '删除' }}
                  </button>
                </td>
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
  </div>
</template>

<style scoped>
/* ---------- 页头操作 ---------- */
.page__actions {
  display: flex;
  gap: 0.5rem;
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

.table__actions-head {
  text-align: right;
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

.cell-date {
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.cell-actions {
  text-align: right;
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

  .cell-actions {
    justify-content: flex-end;
    padding-top: 0.75rem;
  }
}
</style>
