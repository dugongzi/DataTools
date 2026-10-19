export class DouyinVideoStats {
  awemeId: string | null
  diggCount: number
  commentCount: number
  shareCount: number
  collectCount: number
  playCount: number
  capturedAt: Date | null
  lastError: string | null

  constructor(
    awemeId: string | null,
    diggCount: number,
    commentCount: number,
    shareCount: number,
    collectCount: number,
    playCount: number,
    capturedAt: Date | null,
    lastError: string | null
  ) {
    this.awemeId = awemeId
    this.diggCount = diggCount
    this.commentCount = commentCount
    this.shareCount = shareCount
    this.collectCount = collectCount
    this.playCount = playCount
    this.capturedAt = capturedAt
    this.lastError = lastError
  }
}

export class DouyinTotals {
  diggCount: number
  commentCount: number
  shareCount: number
  collectCount: number
  interaction: number

  constructor(
    diggCount = 0,
    commentCount = 0,
    shareCount = 0,
    collectCount = 0
  ) {
    this.diggCount = diggCount
    this.commentCount = commentCount
    this.shareCount = shareCount
    this.collectCount = collectCount
    this.interaction = diggCount + commentCount + shareCount + collectCount
  }
}

export class DouyinGrowth extends DouyinTotals {
  window: string
  available: boolean
  from: Date | null
  to: Date | null
  rate: number | null
  points: number

  constructor(
    window: string,
    available: boolean,
    from: Date | null,
    to: Date | null,
    diggCount = 0,
    commentCount = 0,
    shareCount = 0,
    collectCount = 0,
    rate: number | null = null,
    points = 0
  ) {
    super(diggCount, commentCount, shareCount, collectCount)
    this.window = window
    this.available = available
    this.from = from
    this.to = to
    this.rate = rate
    this.points = points
  }
}

export class DouyinGrowthTotals extends DouyinTotals {
  rate: number | null

  constructor(
    diggCount = 0,
    commentCount = 0,
    shareCount = 0,
    collectCount = 0,
    rate: number | null = null
  ) {
    super(diggCount, commentCount, shareCount, collectCount)
    this.rate = rate
  }
}

export class DouyinVideo {
  id: number
  url: string
  author: string | null
  title: string | null
  rawText: string | null
  createdAt: Date
  updatedAt: Date
  latest: DouyinVideoStats | null
  growth: DouyinGrowth | null

  constructor(
    id: number,
    url: string,
    author: string | null,
    title: string | null,
    rawText: string | null,
    createdAt: Date,
    updatedAt: Date,
    latest: DouyinVideoStats | null = null,
    growth: DouyinGrowth | null = null
  ) {
    this.id = id
    this.url = url
    this.author = author
    this.title = title
    this.rawText = rawText
    this.createdAt = createdAt
    this.updatedAt = updatedAt
    this.latest = latest
    this.growth = growth
  }
}

export class DouyinSnapshot {
  id: number
  awemeId: string | null
  diggCount: number
  commentCount: number
  shareCount: number
  collectCount: number
  playCount: number
  capturedAt: Date | null
  error: string | null
  growth: DouyinTotals | null

  constructor(
    id: number,
    awemeId: string | null,
    diggCount: number,
    commentCount: number,
    shareCount: number,
    collectCount: number,
    playCount: number,
    capturedAt: Date | null,
    error: string | null,
    growth: DouyinTotals | null = null
  ) {
    this.id = id
    this.awemeId = awemeId
    this.diggCount = diggCount
    this.commentCount = commentCount
    this.shareCount = shareCount
    this.collectCount = collectCount
    this.playCount = playCount
    this.capturedAt = capturedAt
    this.error = error
    this.growth = growth
  }
}

export class DouyinTrendPoint {
  time: Date | null
  diggCount: number
  commentCount: number
  shareCount: number
  collectCount: number
  interaction: number

  constructor(
    time: Date | null,
    diggCount = 0,
    commentCount = 0,
    shareCount = 0,
    collectCount = 0,
    interaction = 0
  ) {
    this.time = time
    this.diggCount = diggCount
    this.commentCount = commentCount
    this.shareCount = shareCount
    this.collectCount = collectCount
    this.interaction = interaction
  }
}

export class DouyinAuthorRank {
  author: string
  interaction: number

  constructor(author: string, interaction = 0) {
    this.author = author
    this.interaction = interaction
  }
}

export class DouyinCharts {
  window: string
  bucketSeconds: number
  trend: DouyinTrendPoint[]
  composition: DouyinTotals
  topVideos: DouyinVideo[]
  authors: DouyinAuthorRank[]

  constructor(
    window: string,
    bucketSeconds: number,
    trend: DouyinTrendPoint[],
    composition: DouyinTotals,
    topVideos: DouyinVideo[],
    authors: DouyinAuthorRank[]
  ) {
    this.window = window
    this.bucketSeconds = bucketSeconds
    this.trend = trend
    this.composition = composition
    this.topVideos = topVideos
    this.authors = authors
  }
}

export class DouyinOverview {
  window: string
  windowStart: Date | null
  totalVideos: number
  capturedVideos: number
  failedVideos: number
  pendingVideos: number
  totals: DouyinTotals
  growth: DouyinGrowthTotals
  lastCapturedAt: Date | null
  topVideos: DouyinVideo[]

  constructor(
    window: string,
    windowStart: Date | null,
    totalVideos: number,
    capturedVideos: number,
    failedVideos: number,
    pendingVideos: number,
    totals: DouyinTotals,
    growth: DouyinGrowthTotals,
    lastCapturedAt: Date | null,
    topVideos: DouyinVideo[]
  ) {
    this.window = window
    this.windowStart = windowStart
    this.totalVideos = totalVideos
    this.capturedVideos = capturedVideos
    this.failedVideos = failedVideos
    this.pendingVideos = pendingVideos
    this.totals = totals
    this.growth = growth
    this.lastCapturedAt = lastCapturedAt
    this.topVideos = topVideos
  }
}
