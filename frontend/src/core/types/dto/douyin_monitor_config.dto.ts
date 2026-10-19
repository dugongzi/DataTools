import {
  DouyinMonitorConfig,
  DouyinMonitorRun,
  DouyinMonitorStatus,
  type MonitorRunStatus,
  type MonitorScheduleType,
  type MonitorTriggerType
} from '@/core/types/entities/douyin_monitor_config.entity'

export interface DouyinMonitorConfigJson {
  enabled: boolean
  schedule_type: MonitorScheduleType
  interval_minutes: number
  cron_expression: string
  concurrency: number
  retry_times: number
  retry_delay_seconds: number
  fetch_on_import: boolean
  stale_minutes: number
  next_run_at: string | null
  updated_at: string | null
  updated_by: string | null
}

export interface UpdateDouyinMonitorConfigJson {
  enabled: boolean
  schedule_type: MonitorScheduleType
  interval_minutes: number
  cron_expression: string
  concurrency: number
  retry_times: number
  retry_delay_seconds: number
  fetch_on_import: boolean
  stale_minutes: number
}

export interface DouyinMonitorRunJson {
  id: number
  trigger_type: MonitorTriggerType
  status: MonitorRunStatus
  total: number
  success_count: number
  failed_count: number
  started_at: string | null
  finished_at: string | null
  message: string | null
  video_ids: number[]
}

export interface DouyinMonitorStatusJson {
  enabled: boolean
  running: boolean
  current_run: DouyinMonitorRunJson | null
  last_run: DouyinMonitorRunJson | null
  next_run_at: string | null
  total_videos: number
}

export interface TriggerMonitorRunJson {
  run_id: number
  run: DouyinMonitorRunJson
}

export interface DouyinMonitorRunListJson {
  items: DouyinMonitorRunJson[]
}

export interface RetryMonitorRunJson {
  run_id: number
  run: DouyinMonitorRunJson
  total: number
}

function parseDate(value: string | null): Date | null {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export class DouyinMonitorRunDto {
  id: number
  trigger_type: MonitorTriggerType
  status: MonitorRunStatus
  total: number
  success_count: number
  failed_count: number
  started_at: string | null
  finished_at: string | null
  message: string | null
  video_ids: number[]

  constructor(json: DouyinMonitorRunJson) {
    this.id = json.id
    this.trigger_type = json.trigger_type
    this.status = json.status
    this.total = json.total
    this.success_count = json.success_count
    this.failed_count = json.failed_count
    this.started_at = json.started_at
    this.finished_at = json.finished_at
    this.message = json.message
    this.video_ids = json.video_ids ?? []
  }

  static fromJson(json: DouyinMonitorRunJson): DouyinMonitorRunDto {
    return new DouyinMonitorRunDto(json)
  }

  toJson(): DouyinMonitorRunJson {
    return {
      id: this.id,
      trigger_type: this.trigger_type,
      status: this.status,
      total: this.total,
      success_count: this.success_count,
      failed_count: this.failed_count,
      started_at: this.started_at,
      finished_at: this.finished_at,
      message: this.message,
      video_ids: this.video_ids
    }
  }

  toEntity(): DouyinMonitorRun {
    return new DouyinMonitorRun(
      this.id,
      this.trigger_type,
      this.status,
      this.total,
      this.success_count,
      this.failed_count,
      parseDate(this.started_at),
      parseDate(this.finished_at),
      this.message,
      this.video_ids
    )
  }
}

export class DouyinMonitorConfigDto {
  enabled: boolean
  schedule_type: MonitorScheduleType
  interval_minutes: number
  cron_expression: string
  concurrency: number
  retry_times: number
  retry_delay_seconds: number
  fetch_on_import: boolean
  stale_minutes: number
  next_run_at: string | null
  updated_at: string | null
  updated_by: string | null

  constructor(json: DouyinMonitorConfigJson) {
    this.enabled = json.enabled
    this.schedule_type = json.schedule_type
    this.interval_minutes = json.interval_minutes
    this.cron_expression = json.cron_expression
    this.concurrency = json.concurrency
    this.retry_times = json.retry_times
    this.retry_delay_seconds = json.retry_delay_seconds
    this.fetch_on_import = json.fetch_on_import
    this.stale_minutes = json.stale_minutes
    this.next_run_at = json.next_run_at
    this.updated_at = json.updated_at
    this.updated_by = json.updated_by
  }

  static fromJson(json: DouyinMonitorConfigJson): DouyinMonitorConfigDto {
    return new DouyinMonitorConfigDto(json)
  }

  toJson(): DouyinMonitorConfigJson {
    return {
      enabled: this.enabled,
      schedule_type: this.schedule_type,
      interval_minutes: this.interval_minutes,
      cron_expression: this.cron_expression,
      concurrency: this.concurrency,
      retry_times: this.retry_times,
      retry_delay_seconds: this.retry_delay_seconds,
      fetch_on_import: this.fetch_on_import,
      stale_minutes: this.stale_minutes,
      next_run_at: this.next_run_at,
      updated_at: this.updated_at,
      updated_by: this.updated_by
    }
  }

  toUpdateJson(): UpdateDouyinMonitorConfigJson {
    return {
      enabled: this.enabled,
      schedule_type: this.schedule_type,
      interval_minutes: this.interval_minutes,
      cron_expression: this.cron_expression,
      concurrency: this.concurrency,
      retry_times: this.retry_times,
      retry_delay_seconds: this.retry_delay_seconds,
      fetch_on_import: this.fetch_on_import,
      stale_minutes: this.stale_minutes
    }
  }

  toEntity(): DouyinMonitorConfig {
    return new DouyinMonitorConfig(
      this.enabled,
      this.schedule_type,
      this.interval_minutes,
      this.cron_expression,
      this.concurrency,
      this.retry_times,
      this.retry_delay_seconds,
      this.fetch_on_import,
      this.stale_minutes,
      parseDate(this.next_run_at),
      parseDate(this.updated_at),
      this.updated_by
    )
  }
}

export class DouyinMonitorStatusDto {
  enabled: boolean
  running: boolean
  current_run: DouyinMonitorRunDto | null
  last_run: DouyinMonitorRunDto | null
  next_run_at: string | null
  total_videos: number

  constructor(json: DouyinMonitorStatusJson) {
    this.enabled = json.enabled
    this.running = json.running
    this.current_run = json.current_run ? DouyinMonitorRunDto.fromJson(json.current_run) : null
    this.last_run = json.last_run ? DouyinMonitorRunDto.fromJson(json.last_run) : null
    this.next_run_at = json.next_run_at
    this.total_videos = json.total_videos
  }

  static fromJson(json: DouyinMonitorStatusJson): DouyinMonitorStatusDto {
    return new DouyinMonitorStatusDto(json)
  }

  toJson(): DouyinMonitorStatusJson {
    return {
      enabled: this.enabled,
      running: this.running,
      current_run: this.current_run ? this.current_run.toJson() : null,
      last_run: this.last_run ? this.last_run.toJson() : null,
      next_run_at: this.next_run_at,
      total_videos: this.total_videos
    }
  }

  toEntity(): DouyinMonitorStatus {
    return new DouyinMonitorStatus(
      this.enabled,
      this.running,
      this.current_run ? this.current_run.toEntity() : null,
      this.last_run ? this.last_run.toEntity() : null,
      parseDate(this.next_run_at),
      this.total_videos
    )
  }
}
