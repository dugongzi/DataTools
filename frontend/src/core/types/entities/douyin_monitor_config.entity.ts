export type MonitorScheduleType = 'interval' | 'cron'
export type MonitorRunStatus = 'running' | 'success' | 'partial' | 'failed'
export type MonitorTriggerType = 'schedule' | 'manual' | 'import'

export class DouyinMonitorConfig {
  enabled: boolean
  scheduleType: MonitorScheduleType
  intervalMinutes: number
  cronExpression: string
  concurrency: number
  retryTimes: number
  retryDelaySeconds: number
  fetchOnImport: boolean
  staleMinutes: number
  nextRunAt: Date | null
  updatedAt: Date | null
  updatedBy: string | null

  constructor(
    enabled: boolean,
    scheduleType: MonitorScheduleType,
    intervalMinutes: number,
    cronExpression: string,
    concurrency: number,
    retryTimes: number,
    retryDelaySeconds: number,
    fetchOnImport: boolean,
    staleMinutes: number,
    nextRunAt: Date | null,
    updatedAt: Date | null,
    updatedBy: string | null
  ) {
    this.enabled = enabled
    this.scheduleType = scheduleType
    this.intervalMinutes = intervalMinutes
    this.cronExpression = cronExpression
    this.concurrency = concurrency
    this.retryTimes = retryTimes
    this.retryDelaySeconds = retryDelaySeconds
    this.fetchOnImport = fetchOnImport
    this.staleMinutes = staleMinutes
    this.nextRunAt = nextRunAt
    this.updatedAt = updatedAt
    this.updatedBy = updatedBy
  }
}

export class DouyinMonitorRun {
  id: number
  triggerType: MonitorTriggerType
  status: MonitorRunStatus
  total: number
  successCount: number
  failedCount: number
  startedAt: Date | null
  finishedAt: Date | null
  message: string | null

  constructor(
    id: number,
    triggerType: MonitorTriggerType,
    status: MonitorRunStatus,
    total: number,
    successCount: number,
    failedCount: number,
    startedAt: Date | null,
    finishedAt: Date | null,
    message: string | null
  ) {
    this.id = id
    this.triggerType = triggerType
    this.status = status
    this.total = total
    this.successCount = successCount
    this.failedCount = failedCount
    this.startedAt = startedAt
    this.finishedAt = finishedAt
    this.message = message
  }
}

export class DouyinMonitorStatus {
  enabled: boolean
  running: boolean
  currentRun: DouyinMonitorRun | null
  lastRun: DouyinMonitorRun | null
  nextRunAt: Date | null
  totalVideos: number

  constructor(
    enabled: boolean,
    running: boolean,
    currentRun: DouyinMonitorRun | null,
    lastRun: DouyinMonitorRun | null,
    nextRunAt: Date | null,
    totalVideos: number
  ) {
    this.enabled = enabled
    this.running = running
    this.currentRun = currentRun
    this.lastRun = lastRun
    this.nextRunAt = nextRunAt
    this.totalVideos = totalVideos
  }
}
