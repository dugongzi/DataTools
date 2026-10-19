<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useSettingsStore } from '@/core/stores/settings'
import type { MonitorScheduleType } from '@/core/types/entities/douyin_monitor_config.entity'
import type { UpdateDouyinMonitorConfigJson } from '@/core/types/dto/douyin_monitor_config.dto'

const settingsStore = useSettingsStore()

interface MonitorForm {
  enabled: boolean
  scheduleType: MonitorScheduleType
  intervalMinutes: number
  cronExpression: string
  concurrency: number
  retryTimes: number
  retryDelaySeconds: number
  fetchOnImport: boolean
  staleMinutes: number
}

const DEFAULTS: MonitorForm = {
  enabled: false,
  scheduleType: 'interval',
  intervalMinutes: 30,
  cronExpression: '0 */2 * * *',
  concurrency: 3,
  retryTimes: 2,
  retryDelaySeconds: 5,
  fetchOnImport: true,
  staleMinutes: 15
}

const form = reactive<MonitorForm>({ ...DEFAULTS })
const baseline = ref(JSON.stringify(DEFAULTS))
const localErrors = ref<Record<string, string>>({})

const pageLoading = ref(true)
const loadError = ref<string | null>(null)

const notice = ref<{ kind: 'success' | 'error'; text: string } | null>(null)
let noticeTimer: ReturnType<typeof setTimeout> | undefined
let pollTimer: ReturnType<typeof setInterval> | undefined

const status = computed(() => settingsStore.status)
const currentRun = computed(() => status.value?.currentRun ?? null)
const lastRun = computed(() => status.value?.lastRun ?? null)
const running = computed(() => Boolean(status.value?.running))
const totalVideos = computed(() => status.value?.totalVideos ?? 0)

const errors = computed<Record<string, string>>(() => ({
  ...settingsStore.fieldErrors,
  ...localErrors.value
}))

const dirty = computed(() => JSON.stringify(form) !== baseline.value)

const progress = computed(() => {
  const run = currentRun.value
  if (!run || !run.total) return 0
  const done = run.successCount + run.failedCount
  return Math.min(100, Math.round((done / run.total) * 100))
})

const canTrigger = computed(
  () => !running.value && !settingsStore.triggering && totalVideos.value > 0
)

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

function applyConfig() {
  const cfg = settingsStore.config
  if (!cfg) return
  Object.assign(form, {
    enabled: cfg.enabled,
    scheduleType: cfg.scheduleType,
    intervalMinutes: cfg.intervalMinutes,
    cronExpression: cfg.cronExpression,
    concurrency: cfg.concurrency,
    retryTimes: cfg.retryTimes,
    retryDelaySeconds: cfg.retryDelaySeconds,
    fetchOnImport: cfg.fetchOnImport,
    staleMinutes: cfg.staleMinutes
  })
  baseline.value = JSON.stringify(form)
  localErrors.value = {}
}

async function load() {
  pageLoading.value = true
  loadError.value = null
  await settingsStore.load()
  loadError.value = settingsStore.error
  applyConfig()
  pageLoading.value = false
  if (running.value) startPolling()
}

function validate() {
  const next: Record<string, string> = {}

  const interval = Number(form.intervalMinutes)
  if (!Number.isInteger(interval) || interval < 5 || interval > 1440) {
    next.interval_minutes = '必须是 5 ~ 1440 之间的整数'
  }

  if (form.scheduleType === 'cron') {
    const parts = form.cronExpression.trim().split(/\s+/)
    if (parts.length !== 5) {
      next.cron_expression = '需要 5 段 Cron 表达式，例如 0 */2 * * *'
    }
  }

  const concurrency = Number(form.concurrency)
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 5) {
    next.concurrency = '必须是 1 ~ 5 之间的整数'
  }

  const retryTimes = Number(form.retryTimes)
  if (!Number.isInteger(retryTimes) || retryTimes < 0 || retryTimes > 5) {
    next.retry_times = '必须是 0 ~ 5 之间的整数'
  }

  const retryDelay = Number(form.retryDelaySeconds)
  if (!Number.isInteger(retryDelay) || retryDelay < 1 || retryDelay > 60) {
    next.retry_delay_seconds = '必须是 1 ~ 60 之间的整数'
  }

  const stale = Number(form.staleMinutes)
  if (!Number.isInteger(stale) || stale < 1 || stale > 1440) {
    next.stale_minutes = '必须是 1 ~ 1440 之间的整数'
  }

  localErrors.value = next
  return Object.keys(next).length === 0
}

function toPayload(): UpdateDouyinMonitorConfigJson {
  return {
    enabled: form.enabled,
    schedule_type: form.scheduleType,
    interval_minutes: Number(form.intervalMinutes),
    cron_expression: form.cronExpression.trim(),
    concurrency: Number(form.concurrency),
    retry_times: Number(form.retryTimes),
    retry_delay_seconds: Number(form.retryDelaySeconds),
    fetch_on_import: form.fetchOnImport,
    stale_minutes: Number(form.staleMinutes)
  }
}

async function submit() {
  if (settingsStore.saving) return
  if (!validate()) {
    flash('error', '请先修正标红的配置项')
    return
  }

  try {
    await settingsStore.save(toPayload())
    applyConfig()
    flash('success', '配置已保存')
  } catch (e) {
    const code = (e as { response?: { status?: number } })?.response?.status
    if (code === 400) flash('error', '配置校验失败，请检查标红字段')
    else flash('error', '保存失败，请稍后重试')
  }
}

function restoreDefaults() {
  Object.assign(form, { ...DEFAULTS })
  localErrors.value = {}
}

async function triggerNow() {
  if (!canTrigger.value) return

  try {
    const { run } = await settingsStore.triggerRun()
    flash('success', `已启动采集（#${run.id}），共 ${run.total} 条视频`)
    startPolling()
  } catch (e) {
    const code = (e as { response?: { status?: number } })?.response?.status
    if (code === 409) {
      flash('error', '已有采集任务在运行，请等待其结束')
      await settingsStore.refreshStatus()
      startPolling()
    } else {
      flash('error', '启动采集失败，请稍后重试')
    }
  }
}

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    await settingsStore.refreshStatus()
    if (!settingsStore.status?.running) {
      stopPolling()
      const last = settingsStore.status?.lastRun
      if (last) {
        const kind = last.status === 'failed' ? 'error' : 'success'
        flash(kind, `采集完成：成功 ${last.successCount} 条，失败 ${last.failedCount} 条`)
      }
    }
  }, 2000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = undefined
  }
}

onMounted(load)

onBeforeUnmount(() => {
  clearTimeout(noticeTimer)
  stopPolling()
})
</script>

<template>
  <div class="page">
    <div class="page__head">
      <div>
        <h1 class="page__title">设置</h1>
        <p class="page__lead">配置抖音监控的采集时机、并发与重试策略</p>
      </div>

      <div class="page__actions">
        <span v-if="dirty" class="dirty">未保存</span>
        <button class="btn btn--quiet" type="button" :disabled="pageLoading" @click="load">
          刷新
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

    <section class="panel">
      <header class="panel__head">
        <div>
          <h2 class="panel__title">抖音监控</h2>
          <p class="panel__lead">修改后点击「保存配置」生效，无需重启服务</p>
        </div>
      </header>

      <div v-if="pageLoading" class="skeleton" aria-hidden="true">
        <div v-for="row in 5" :key="row" class="skeleton__row">
          <span class="skeleton__cell skeleton__cell--short"></span>
          <span class="skeleton__cell"></span>
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
        <h2 class="state__title">无法加载监控配置</h2>
        <p class="state__lead">{{ loadError }}</p>
        <button class="btn btn--primary" type="button" @click="load">重试</button>
      </div>

      <form v-else class="form" @submit.prevent="submit">
        <div class="row">
          <div class="row__label">
            <span class="row__title">自动采集</span>
            <span class="row__hint">关闭后不再定时采集，手动采集仍可使用</span>
          </div>
          <div class="row__control">
            <label class="switch">
              <input v-model="form.enabled" type="checkbox" />
              <span class="switch__track"></span>
            </label>
          </div>
        </div>

        <div class="row">
          <div class="row__label">
            <span class="row__title">采集频率</span>
            <span class="row__hint">固定间隔或 Cron 表达式，时区固定 Asia/Shanghai</span>
          </div>
          <div class="row__control row__control--stack">
            <label class="choice">
              <input v-model="form.scheduleType" type="radio" value="interval" />
              <span>每隔</span>
              <span class="num">
                <input
                  v-model.number="form.intervalMinutes"
                  type="number"
                  min="5"
                  max="1440"
                  step="1"
                  :disabled="form.scheduleType !== 'interval'"
                />
                <span class="num__unit">分钟</span>
              </span>
            </label>

            <label class="choice">
              <input v-model="form.scheduleType" type="radio" value="cron" />
              <span>Cron</span>
              <input
                v-model="form.cronExpression"
                class="text-input"
                type="text"
                placeholder="0 */2 * * *"
                spellcheck="false"
                :disabled="form.scheduleType !== 'cron'"
              />
            </label>

            <p v-if="errors.interval_minutes" class="field-error">{{ errors.interval_minutes }}</p>
            <p v-if="errors.cron_expression" class="field-error">{{ errors.cron_expression }}</p>
          </div>
        </div>

        <div class="row">
          <div class="row__label">
            <span class="row__title">并发页面数</span>
            <span class="row__hint">越高越快，过高可能触发抖音风控，建议 2 ~ 3</span>
          </div>
          <div class="row__control">
            <div class="range">
              <input v-model.number="form.concurrency" type="range" min="1" max="5" step="1" />
              <span class="range__value">{{ form.concurrency }}</span>
            </div>
            <p v-if="errors.concurrency" class="field-error">{{ errors.concurrency }}</p>
          </div>
        </div>

        <div class="row">
          <div class="row__label">
            <span class="row__title">失败重试</span>
            <span class="row__hint">单条视频请求失败后的重试策略</span>
          </div>
          <div class="row__control row__control--stack">
            <div class="inline">
              <span class="num">
                <input
                  v-model.number="form.retryTimes"
                  type="number"
                  min="0"
                  max="5"
                  step="1"
                />
                <span class="num__unit">次</span>
              </span>
              <span class="inline__text">间隔</span>
              <span class="num">
                <input
                  v-model.number="form.retryDelaySeconds"
                  type="number"
                  min="1"
                  max="60"
                  step="1"
                />
                <span class="num__unit">秒</span>
              </span>
            </div>
            <p v-if="errors.retry_times" class="field-error">{{ errors.retry_times }}</p>
            <p v-if="errors.retry_delay_seconds" class="field-error">
              {{ errors.retry_delay_seconds }}
            </p>
          </div>
        </div>

        <div class="row">
          <div class="row__label">
            <span class="row__title">导入后立即采集</span>
            <span class="row__hint">新导入的视频马上采集一次互动指标</span>
          </div>
          <div class="row__control">
            <label class="switch">
              <input v-model="form.fetchOnImport" type="checkbox" />
              <span class="switch__track"></span>
            </label>
          </div>
        </div>

        <div class="row">
          <div class="row__label">
            <span class="row__title">数据新鲜度</span>
            <span class="row__hint">超过该时长的数据视为过期，打开列表时可在后台刷新</span>
          </div>
          <div class="row__control row__control--stack">
            <span class="num">
              <input v-model.number="form.staleMinutes" type="number" min="1" max="1440" step="1" />
              <span class="num__unit">分钟</span>
            </span>
            <p v-if="errors.stale_minutes" class="field-error">{{ errors.stale_minutes }}</p>
          </div>
        </div>

        <div class="form__actions">
          <button class="btn btn--quiet" type="button" :disabled="settingsStore.saving" @click="restoreDefaults">
            恢复默认
          </button>
          <button class="btn btn--primary" type="submit" :disabled="settingsStore.saving">
            {{ settingsStore.saving ? '保存中…' : '保存配置' }}
          </button>
        </div>
      </form>
    </section>

    <section class="panel">
      <header class="panel__head">
        <div>
          <h2 class="panel__title">运行状态</h2>
          <p class="panel__lead">查看调度器状态并手动触发一轮采集</p>
        </div>
        <span
          class="pill"
          :class="running ? 'pill--busy' : status?.enabled ? 'pill--on' : 'pill--off'"
        >
          {{ running ? '采集中' : status?.enabled ? '调度已开启' : '调度已关闭' }}
        </span>
      </header>

      <div class="status">
        <div class="stat">
          <span class="stat__label">监控视频</span>
          <span class="stat__value">{{ totalVideos }} 条</span>
        </div>

        <div class="stat">
          <span class="stat__label">上次采集</span>
          <span class="stat__value">
            {{ lastRun ? formatDate(lastRun.finishedAt ?? lastRun.startedAt) : '暂无记录' }}
          </span>
          <span v-if="lastRun" class="stat__hint">
            成功 {{ lastRun.successCount }} · 失败 {{ lastRun.failedCount }}
          </span>
        </div>

        <div class="stat">
          <span class="stat__label">下次采集</span>
          <span class="stat__value">
            {{ status?.nextRunAt ? formatDate(status.nextRunAt) : '—' }}
          </span>
          <span class="stat__hint">
            {{ status?.enabled ? '按当前配置自动执行' : '自动采集已关闭' }}
          </span>
        </div>
      </div>

      <div v-if="currentRun" class="run">
        <div class="run__head">
          <span>采集 #{{ currentRun.id }}</span>
          <span class="run__count">
            {{ currentRun.successCount + currentRun.failedCount }} / {{ currentRun.total }}
          </span>
        </div>
        <div
          class="progress"
          role="progressbar"
          :aria-valuenow="progress"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <div class="progress__bar" :style="{ width: `${progress}%` }"></div>
        </div>
      </div>

      <div class="status__actions">
        <button
          class="btn btn--primary"
          type="button"
          :disabled="!canTrigger"
          @click="triggerNow"
        >
          {{ running ? '采集中…' : settingsStore.triggering ? '启动中…' : '立即采集' }}
        </button>
        <span class="status__note">
          {{
            totalVideos === 0
              ? '监控列表为空，先导入视频后再采集'
              : running
                ? '采集进行中，完成后自动刷新状态'
                : '将对全部监控视频采集一次互动指标'
          }}
        </span>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ---------- 页头 ---------- */
.page__actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.dirty {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-subtle);
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

/* ---------- 面板 ---------- */
.panel__head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1.25rem 1.25rem 1rem;
}

.panel__title {
  margin: 0;
  font-size: 1.0625rem;
  font-weight: 600;
  letter-spacing: -0.022em;
}

.panel__lead {
  margin: 0.25rem 0 0;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

/* ---------- 表单 ---------- */
.form {
  display: grid;
  border-top: 1px solid var(--separator);
}

.row {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(0, 1.35fr);
  align-items: start;
  gap: 1.25rem;
  padding: 1rem 1.25rem;
}

.row + .row {
  border-top: 1px solid var(--separator);
}

.row__label {
  display: grid;
  gap: 0.1875rem;
}

.row__title {
  font-size: 0.9375rem;
  font-weight: 500;
  letter-spacing: -0.01em;
}

.row__hint {
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--text-muted);
}

.row__control {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-width: 0;
}

.row__control--stack {
  gap: 0.5rem;
}

/* ---------- 开关 ---------- */
.switch {
  position: relative;
  display: inline-flex;
  width: 44px;
  height: 26px;
}

.switch input {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}

.switch__track {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: var(--radius-pill);
  background: var(--field-bg-hover);
  transition: background 0.2s ease;
}

.switch__track::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.24);
  transition: transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}

.switch input:checked + .switch__track {
  background: var(--accent);
}

.switch input:checked + .switch__track::after {
  transform: translateX(18px);
}

.switch input:focus-visible + .switch__track {
  box-shadow: 0 0 0 4px var(--accent-ring);
}

/* ---------- 频率 ---------- */
.choice {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text);
}

.choice input[type='radio'] {
  width: 16px;
  height: 16px;
  margin: 0;
  accent-color: var(--accent);
  cursor: pointer;
}

.num {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.num input {
  width: 88px;
  height: 36px;
  padding: 0 0.625rem;
  font-size: 0.875rem;
  color: var(--text);
  background: var(--field-bg);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  outline: none;
  font-variant-numeric: tabular-nums;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.num input:hover:not(:disabled) {
  background: var(--field-bg-hover);
}

.num input:focus {
  background: var(--field-bg-focus);
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-ring);
}

.num input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.num__unit {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.text-input {
  flex: 1;
  min-width: 160px;
  height: 36px;
  padding: 0 0.75rem;
  font-size: 0.875rem;
  color: var(--text);
  background: var(--field-bg);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  outline: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.text-input::placeholder {
  color: var(--text-subtle);
}

.text-input:hover:not(:disabled) {
  background: var(--field-bg-hover);
}

.text-input:focus {
  background: var(--field-bg-focus);
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-ring);
}

.text-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.inline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.inline__text {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.range {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.range input[type='range'] {
  width: min(220px, 60vw);
  accent-color: var(--accent);
  cursor: pointer;
}

.range__value {
  display: grid;
  place-items: center;
  min-width: 28px;
  height: 28px;
  padding: 0 0.375rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-soft);
  border-radius: var(--radius-sm);
  font-variant-numeric: tabular-nums;
}

.field-error {
  margin: 0;
  font-size: 0.75rem;
  color: var(--danger);
}

.form__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--separator);
}

/* ---------- 运行状态 ---------- */
.pill {
  display: inline-flex;
  align-items: center;
  height: 26px;
  padding: 0 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: var(--radius-pill);
}

.pill--on {
  color: var(--success);
  background: var(--success-bg);
}

.pill--off {
  color: var(--text-muted);
  background: var(--field-bg);
}

.pill--busy {
  color: var(--accent);
  background: var(--accent-soft);
  animation: pulse 1.4s ease-in-out infinite;
}

.status {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  background: var(--separator);
  border-top: 1px solid var(--separator);
}

.stat {
  display: grid;
  gap: 0.25rem;
  padding: 1rem 1.25rem;
  background: var(--surface-solid);
}

.stat__label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-subtle);
}

.stat__value {
  font-size: 0.9375rem;
  font-weight: 500;
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
}

.stat__hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.run {
  display: grid;
  gap: 0.5rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--separator);
}

.run__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.run__count {
  font-variant-numeric: tabular-nums;
}

.progress {
  height: 6px;
  overflow: hidden;
  background: var(--field-bg);
  border-radius: var(--radius-pill);
}

.progress__bar {
  height: 100%;
  background: var(--accent);
  border-radius: inherit;
  transition: width 0.3s ease;
}

.status__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--separator);
}

.status__note {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ---------- 骨架 / 状态 ---------- */
.skeleton {
  display: grid;
  gap: 1px;
  background: var(--separator);
  border-top: 1px solid var(--separator);
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

.skeleton__cell--short {
  flex: 0.5;
}

.state {
  display: grid;
  justify-items: center;
  gap: 0.5rem;
  padding: clamp(2.5rem, 8vw, 4rem) 1.5rem;
  text-align: center;
  border-top: 1px solid var(--separator);
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

/* ---------- 响应式 ---------- */
@media (max-width: 720px) {
  .page__head {
    align-items: flex-start;
  }

  .row {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .status {
    grid-template-columns: 1fr;
  }

  .form__actions {
    justify-content: stretch;
  }

  .form__actions .btn {
    flex: 1;
  }
}
</style>
