import {
  DouyinAuthorRank,
  DouyinChartVideo,
  DouyinCharts,
  DouyinGrowth,
  DouyinGrowthTotals,
  DouyinOverview,
  DouyinSnapshot,
  DouyinTotals,
  DouyinTrendPoint,
  DouyinTrendSeries,
  DouyinVideo,
  DouyinVideoStats
} from '@/core/types/entities/douyin_video.entity'

export type DouyinWindow = '1h' | '6h' | '24h' | '7d' | 'all'
export type DouyinStatusFilter = 'all' | 'captured' | 'failed' | 'pending'
export type DouyinSortField =
  | 'created_at'
  | 'captured_at'
  | 'digg'
  | 'comment'
  | 'share'
  | 'collect'
  | 'interaction'
  | 'growth'
  | 'growth_digg'
  | 'growth_comment'
  | 'growth_share'
  | 'growth_collect'
  | 'growth_rate'
export type DouyinSortOrder = 'asc' | 'desc'

export interface DouyinVideoQuery {
  q?: string
  status?: DouyinStatusFilter
  sort?: DouyinSortField
  order?: DouyinSortOrder
  window?: DouyinWindow
}

function parseDate(value: string | null | undefined): Date | null {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export interface DouyinVideoStatsJson {
  aweme_id: string | null
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  play_count: number
  captured_at: string | null
  last_error: string | null
}

export interface DouyinTotalsJson {
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  interaction: number
}

export interface DouyinGrowthJson {
  window: string
  available: boolean
  from: string | null
  to: string | null
  digg_count: number | null
  comment_count: number | null
  share_count: number | null
  collect_count: number | null
  interaction: number | null
  rate: number | null
  points: number
}

export interface DouyinGrowthTotalsJson {
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  interaction: number
  rate: number | null
}

export interface DouyinVideoJson {
  id: number
  url: string
  author: string | null
  title: string | null
  raw_text: string | null
  created_at: string
  updated_at: string
  latest?: DouyinVideoStatsJson | null
  growth?: DouyinGrowthJson | null
}

export interface ImportDouyinVideosJson {
  created: DouyinVideoJson[]
  skipped: string[]
  run_id?: number | null
}

export interface PaginatedDouyinVideosJson {
  items: DouyinVideoJson[]
  total: number
  page: number
  per_page: number
  pages: number
  window?: string
  sort?: string
  order?: string
}

export interface DouyinSnapshotJson {
  id: number
  aweme_id: string | null
  digg_count: number | null
  comment_count: number | null
  share_count: number | null
  collect_count: number | null
  play_count: number | null
  captured_at: string | null
  error: string | null
  growth: DouyinTotalsJson | null
}

export interface DouyinSnapshotsJson {
  items: DouyinSnapshotJson[]
  window: string | null
  growth: DouyinGrowthJson
}

export interface DouyinOverviewJson {
  window: string
  window_start: string | null
  total_videos: number
  captured_videos: number
  failed_videos: number
  pending_videos: number
  totals: DouyinTotalsJson
  growth: DouyinGrowthTotalsJson
  last_captured_at: string | null
  top_videos: DouyinVideoJson[]
}

export interface DouyinTrendPointJson {
  time: string | null
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  interaction: number
}

export interface DouyinTrendJson {
  bucket_seconds: number
  points: DouyinTrendPointJson[]
}

export interface DouyinTrendSeriesJson {
  video_id: number
  title: string | null
  author: string | null
  bucket_seconds: number
  points: DouyinTrendPointJson[]
}

export interface DouyinChartVideoJson {
  id: number
  url: string
  title: string | null
  author: string | null
}

export interface DouyinAuthorRankJson {
  author: string
  interaction: number
}

export interface DouyinChartsJson {
  window: string
  trend: DouyinTrendJson
  trends?: DouyinTrendSeriesJson[]
  videos?: DouyinChartVideoJson[]
  composition: DouyinTotalsJson
  top_videos: DouyinVideoJson[]
  authors: DouyinAuthorRankJson[]
}

export class DouyinVideoStatsDto {
  aweme_id: string | null
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  play_count: number
  captured_at: string | null
  last_error: string | null

  constructor(json: DouyinVideoStatsJson) {
    this.aweme_id = json.aweme_id ?? null
    this.digg_count = json.digg_count ?? 0
    this.comment_count = json.comment_count ?? 0
    this.share_count = json.share_count ?? 0
    this.collect_count = json.collect_count ?? 0
    this.play_count = json.play_count ?? 0
    this.captured_at = json.captured_at ?? null
    this.last_error = json.last_error ?? null
  }

  static fromJson(json: DouyinVideoStatsJson): DouyinVideoStatsDto {
    return new DouyinVideoStatsDto(json)
  }

  toJson(): DouyinVideoStatsJson {
    return {
      aweme_id: this.aweme_id,
      digg_count: this.digg_count,
      comment_count: this.comment_count,
      share_count: this.share_count,
      collect_count: this.collect_count,
      play_count: this.play_count,
      captured_at: this.captured_at,
      last_error: this.last_error
    }
  }

  toEntity(): DouyinVideoStats {
    return new DouyinVideoStats(
      this.aweme_id,
      this.digg_count,
      this.comment_count,
      this.share_count,
      this.collect_count,
      this.play_count,
      parseDate(this.captured_at),
      this.last_error
    )
  }
}

export class DouyinTotalsDto {
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  interaction: number

  constructor(json: DouyinTotalsJson) {
    this.digg_count = json.digg_count ?? 0
    this.comment_count = json.comment_count ?? 0
    this.share_count = json.share_count ?? 0
    this.collect_count = json.collect_count ?? 0
    this.interaction = json.interaction ?? 0
  }

  static fromJson(json: DouyinTotalsJson): DouyinTotalsDto {
    return new DouyinTotalsDto(json)
  }

  toEntity(): DouyinTotals {
    return new DouyinTotals(
      this.digg_count,
      this.comment_count,
      this.share_count,
      this.collect_count
    )
  }
}

export class DouyinGrowthDto {
  window: string
  available: boolean
  from: string | null
  to: string | null
  digg_count: number | null
  comment_count: number | null
  share_count: number | null
  collect_count: number | null
  interaction: number | null
  rate: number | null
  points: number

  constructor(json: DouyinGrowthJson) {
    this.window = json.window
    this.available = json.available ?? false
    this.from = json.from ?? null
    this.to = json.to ?? null
    this.digg_count = json.digg_count ?? null
    this.comment_count = json.comment_count ?? null
    this.share_count = json.share_count ?? null
    this.collect_count = json.collect_count ?? null
    this.interaction = json.interaction ?? null
    this.rate = json.rate ?? null
    this.points = json.points ?? 0
  }

  static fromJson(json: DouyinGrowthJson): DouyinGrowthDto {
    return new DouyinGrowthDto(json)
  }

  toJson(): DouyinGrowthJson {
    return {
      window: this.window,
      available: this.available,
      from: this.from,
      to: this.to,
      digg_count: this.digg_count,
      comment_count: this.comment_count,
      share_count: this.share_count,
      collect_count: this.collect_count,
      interaction: this.interaction,
      rate: this.rate,
      points: this.points
    }
  }

  toEntity(): DouyinGrowth {
    return new DouyinGrowth(
      this.window,
      this.available,
      parseDate(this.from),
      parseDate(this.to),
      this.digg_count ?? 0,
      this.comment_count ?? 0,
      this.share_count ?? 0,
      this.collect_count ?? 0,
      this.rate,
      this.points
    )
  }
}

export class DouyinGrowthTotalsDto {
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  interaction: number
  rate: number | null

  constructor(json: DouyinGrowthTotalsJson) {
    this.digg_count = json.digg_count ?? 0
    this.comment_count = json.comment_count ?? 0
    this.share_count = json.share_count ?? 0
    this.collect_count = json.collect_count ?? 0
    this.interaction = json.interaction ?? 0
    this.rate = json.rate ?? null
  }

  static fromJson(json: DouyinGrowthTotalsJson): DouyinGrowthTotalsDto {
    return new DouyinGrowthTotalsDto(json)
  }

  toEntity(): DouyinGrowthTotals {
    return new DouyinGrowthTotals(
      this.digg_count,
      this.comment_count,
      this.share_count,
      this.collect_count,
      this.rate
    )
  }
}

export class DouyinVideoDto {
  id: number
  url: string
  author: string | null
  title: string | null
  raw_text: string | null
  created_at: string
  updated_at: string
  latest: DouyinVideoStatsDto | null
  growth: DouyinGrowthDto | null

  constructor(
    id: number,
    url: string,
    author: string | null,
    title: string | null,
    raw_text: string | null,
    created_at: string,
    updated_at: string,
    latest: DouyinVideoStatsDto | null,
    growth: DouyinGrowthDto | null = null
  ) {
    this.id = id
    this.url = url
    this.author = author
    this.title = title
    this.raw_text = raw_text
    this.created_at = created_at
    this.updated_at = updated_at
    this.latest = latest
    this.growth = growth
  }

  static fromJson(json: DouyinVideoJson): DouyinVideoDto {
    return new DouyinVideoDto(
      json.id,
      json.url,
      json.author,
      json.title,
      json.raw_text,
      json.created_at,
      json.updated_at,
      json.latest ? DouyinVideoStatsDto.fromJson(json.latest) : null,
      json.growth ? DouyinGrowthDto.fromJson(json.growth) : null
    )
  }

  toJson(): DouyinVideoJson {
    return {
      id: this.id,
      url: this.url,
      author: this.author,
      title: this.title,
      raw_text: this.raw_text,
      created_at: this.created_at,
      updated_at: this.updated_at,
      latest: this.latest ? this.latest.toJson() : null,
      growth: this.growth ? this.growth.toJson() : null
    }
  }

  toEntity(): DouyinVideo {
    return new DouyinVideo(
      this.id,
      this.url,
      this.author,
      this.title,
      this.raw_text,
      new Date(this.created_at),
      new Date(this.updated_at),
      this.latest ? this.latest.toEntity() : null,
      this.growth ? this.growth.toEntity() : null
    )
  }
}

export class PaginatedDouyinVideosDto {
  items: DouyinVideoDto[]
  total: number
  page: number
  per_page: number
  pages: number
  window: string
  sort: string
  order: string

  constructor(
    items: DouyinVideoDto[],
    total: number,
    page: number,
    per_page: number,
    pages: number,
    window = '24h',
    sort = 'created_at',
    order = 'desc'
  ) {
    this.items = items
    this.total = total
    this.page = page
    this.per_page = per_page
    this.pages = pages
    this.window = window
    this.sort = sort
    this.order = order
  }

  static fromJson(json: PaginatedDouyinVideosJson): PaginatedDouyinVideosDto {
    return new PaginatedDouyinVideosDto(
      json.items.map((item) => DouyinVideoDto.fromJson(item)),
      json.total,
      json.page,
      json.per_page,
      json.pages,
      json.window ?? '24h',
      json.sort ?? 'created_at',
      json.order ?? 'desc'
    )
  }

  toJson(): PaginatedDouyinVideosJson {
    return {
      items: this.items.map((dto) => dto.toJson()),
      total: this.total,
      page: this.page,
      per_page: this.per_page,
      pages: this.pages,
      window: this.window,
      sort: this.sort,
      order: this.order
    }
  }
}

export class ImportDouyinVideosDto {
  created: DouyinVideoDto[]
  skipped: string[]
  runId: number | null

  constructor(created: DouyinVideoDto[], skipped: string[], runId: number | null = null) {
    this.created = created
    this.skipped = skipped
    this.runId = runId
  }

  static fromJson(json: ImportDouyinVideosJson): ImportDouyinVideosDto {
    return new ImportDouyinVideosDto(
      json.created.map((item) => DouyinVideoDto.fromJson(item)),
      json.skipped,
      json.run_id ?? null
    )
  }

  toJson(): ImportDouyinVideosJson {
    return {
      created: this.created.map((dto) => dto.toJson()),
      skipped: this.skipped,
      run_id: this.runId
    }
  }
}

export class DouyinSnapshotDto {
  id: number
  aweme_id: string | null
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  play_count: number
  captured_at: string | null
  error: string | null
  growth: DouyinTotalsDto | null

  constructor(json: DouyinSnapshotJson) {
    this.id = json.id
    this.aweme_id = json.aweme_id ?? null
    this.digg_count = json.digg_count ?? 0
    this.comment_count = json.comment_count ?? 0
    this.share_count = json.share_count ?? 0
    this.collect_count = json.collect_count ?? 0
    this.play_count = json.play_count ?? 0
    this.captured_at = json.captured_at ?? null
    this.error = json.error ?? null
    this.growth = json.growth ? DouyinTotalsDto.fromJson(json.growth) : null
  }

  static fromJson(json: DouyinSnapshotJson): DouyinSnapshotDto {
    return new DouyinSnapshotDto(json)
  }

  toEntity(): DouyinSnapshot {
    return new DouyinSnapshot(
      this.id,
      this.aweme_id,
      this.digg_count,
      this.comment_count,
      this.share_count,
      this.collect_count,
      this.play_count,
      parseDate(this.captured_at),
      this.error,
      this.growth ? this.growth.toEntity() : null
    )
  }
}

export class DouyinSnapshotsDto {
  items: DouyinSnapshotDto[]
  window: string | null
  growth: DouyinGrowthDto

  constructor(items: DouyinSnapshotDto[], window: string | null, growth: DouyinGrowthDto) {
    this.items = items
    this.window = window
    this.growth = growth
  }

  static fromJson(json: DouyinSnapshotsJson): DouyinSnapshotsDto {
    return new DouyinSnapshotsDto(
      json.items.map((item) => DouyinSnapshotDto.fromJson(item)),
      json.window ?? null,
      DouyinGrowthDto.fromJson(json.growth)
    )
  }

  toEntity() {
    return {
      items: this.items.map((dto) => dto.toEntity()),
      window: this.window,
      growth: this.growth.toEntity()
    }
  }
}

export class DouyinOverviewDto {
  window: string
  window_start: string | null
  total_videos: number
  captured_videos: number
  failed_videos: number
  pending_videos: number
  totals: DouyinTotalsDto
  growth: DouyinGrowthTotalsDto
  last_captured_at: string | null
  top_videos: DouyinVideoDto[]

  constructor(json: DouyinOverviewJson) {
    this.window = json.window
    this.window_start = json.window_start ?? null
    this.total_videos = json.total_videos ?? 0
    this.captured_videos = json.captured_videos ?? 0
    this.failed_videos = json.failed_videos ?? 0
    this.pending_videos = json.pending_videos ?? 0
    this.totals = DouyinTotalsDto.fromJson(json.totals)
    this.growth = DouyinGrowthTotalsDto.fromJson(json.growth)
    this.last_captured_at = json.last_captured_at ?? null
    this.top_videos = json.top_videos.map((item) => DouyinVideoDto.fromJson(item))
  }

  static fromJson(json: DouyinOverviewJson): DouyinOverviewDto {
    return new DouyinOverviewDto(json)
  }

  toEntity(): DouyinOverview {
    return new DouyinOverview(
      this.window,
      parseDate(this.window_start),
      this.total_videos,
      this.captured_videos,
      this.failed_videos,
      this.pending_videos,
      this.totals.toEntity(),
      this.growth.toEntity(),
      parseDate(this.last_captured_at),
      this.top_videos.map((dto) => dto.toEntity())
    )
  }
}

export class DouyinTrendPointDto {
  time: string | null
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  interaction: number

  constructor(json: DouyinTrendPointJson) {
    this.time = json.time ?? null
    this.digg_count = json.digg_count ?? 0
    this.comment_count = json.comment_count ?? 0
    this.share_count = json.share_count ?? 0
    this.collect_count = json.collect_count ?? 0
    this.interaction = json.interaction ?? 0
  }

  static fromJson(json: DouyinTrendPointJson): DouyinTrendPointDto {
    return new DouyinTrendPointDto(json)
  }

  toEntity(): DouyinTrendPoint {
    return new DouyinTrendPoint(
      parseDate(this.time),
      this.digg_count,
      this.comment_count,
      this.share_count,
      this.collect_count,
      this.interaction
    )
  }
}

export class DouyinAuthorRankDto {
  author: string
  interaction: number

  constructor(json: DouyinAuthorRankJson) {
    this.author = json.author
    this.interaction = json.interaction ?? 0
  }

  static fromJson(json: DouyinAuthorRankJson): DouyinAuthorRankDto {
    return new DouyinAuthorRankDto(json)
  }

  toEntity(): DouyinAuthorRank {
    return new DouyinAuthorRank(this.author, this.interaction)
  }
}

export class DouyinTrendSeriesDto {
  video_id: number
  title: string | null
  author: string | null
  bucket_seconds: number
  points: DouyinTrendPointDto[]

  constructor(json: DouyinTrendSeriesJson) {
    this.video_id = json.video_id
    this.title = json.title ?? null
    this.author = json.author ?? null
    this.bucket_seconds = json.bucket_seconds ?? 0
    this.points = (json.points ?? []).map((item) => DouyinTrendPointDto.fromJson(item))
  }

  static fromJson(json: DouyinTrendSeriesJson): DouyinTrendSeriesDto {
    return new DouyinTrendSeriesDto(json)
  }

  toEntity(): DouyinTrendSeries {
    return new DouyinTrendSeries(
      this.video_id,
      this.title,
      this.author,
      this.points.map((dto) => dto.toEntity())
    )
  }
}

export class DouyinChartVideoDto {
  id: number
  url: string
  title: string | null
  author: string | null

  constructor(json: DouyinChartVideoJson) {
    this.id = json.id
    this.url = json.url
    this.title = json.title ?? null
    this.author = json.author ?? null
  }

  static fromJson(json: DouyinChartVideoJson): DouyinChartVideoDto {
    return new DouyinChartVideoDto(json)
  }

  toEntity(): DouyinChartVideo {
    return new DouyinChartVideo(this.id, this.url, this.title, this.author)
  }
}

export class DouyinChartsDto {
  window: string
  bucket_seconds: number
  trend: DouyinTrendPointDto[]
  composition: DouyinTotalsDto
  top_videos: DouyinVideoDto[]
  authors: DouyinAuthorRankDto[]
  trends: DouyinTrendSeriesDto[]
  videos: DouyinChartVideoDto[]

  constructor(json: DouyinChartsJson) {
    this.window = json.window
    this.bucket_seconds = json.trend?.bucket_seconds ?? 0
    this.trend = (json.trend?.points ?? []).map((item) => DouyinTrendPointDto.fromJson(item))
    this.composition = DouyinTotalsDto.fromJson(json.composition)
    this.top_videos = (json.top_videos ?? []).map((item) => DouyinVideoDto.fromJson(item))
    this.authors = (json.authors ?? []).map((item) => DouyinAuthorRankDto.fromJson(item))
    this.trends = (json.trends ?? []).map((item) => DouyinTrendSeriesDto.fromJson(item))
    this.videos = (json.videos ?? []).map((item) => DouyinChartVideoDto.fromJson(item))
  }

  static fromJson(json: DouyinChartsJson): DouyinChartsDto {
    return new DouyinChartsDto(json)
  }

  toEntity(): DouyinCharts {
    return new DouyinCharts(
      this.window,
      this.bucket_seconds,
      this.trend.map((dto) => dto.toEntity()),
      this.composition.toEntity(),
      this.top_videos.map((dto) => dto.toEntity()),
      this.authors.map((dto) => dto.toEntity()),
      this.trends.map((dto) => dto.toEntity()),
      this.videos.map((dto) => dto.toEntity())
    )
  }
}
