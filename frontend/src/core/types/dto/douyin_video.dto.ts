import { DouyinVideo } from '@/core/types/entities/douyin_video.entity'

export interface DouyinVideoJson {
  id: number
  url: string
  author: string | null
  title: string | null
  raw_text: string | null
  created_at: string
  updated_at: string
}

export interface ImportDouyinVideosJson {
  created: DouyinVideoJson[]
  skipped: string[]
}

export interface PaginatedDouyinVideosJson {
  items: DouyinVideoJson[]
  total: number
  page: number
  per_page: number
  pages: number
}

export class DouyinVideoDto {
  id: number
  url: string
  author: string | null
  title: string | null
  raw_text: string | null
  created_at: string
  updated_at: string

  constructor(
    id: number,
    url: string,
    author: string | null,
    title: string | null,
    raw_text: string | null,
    created_at: string,
    updated_at: string
  ) {
    this.id = id
    this.url = url
    this.author = author
    this.title = title
    this.raw_text = raw_text
    this.created_at = created_at
    this.updated_at = updated_at
  }

  static fromJson(json: DouyinVideoJson): DouyinVideoDto {
    return new DouyinVideoDto(
      json.id,
      json.url,
      json.author,
      json.title,
      json.raw_text,
      json.created_at,
      json.updated_at
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
      updated_at: this.updated_at
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
      new Date(this.updated_at)
    )
  }
}

export class PaginatedDouyinVideosDto {
  items: DouyinVideoDto[]
  total: number
  page: number
  per_page: number
  pages: number

  constructor(
    items: DouyinVideoDto[],
    total: number,
    page: number,
    per_page: number,
    pages: number
  ) {
    this.items = items
    this.total = total
    this.page = page
    this.per_page = per_page
    this.pages = pages
  }

  static fromJson(json: PaginatedDouyinVideosJson): PaginatedDouyinVideosDto {
    return new PaginatedDouyinVideosDto(
      json.items.map((item) => DouyinVideoDto.fromJson(item)),
      json.total,
      json.page,
      json.per_page,
      json.pages
    )
  }

  toJson(): PaginatedDouyinVideosJson {
    return {
      items: this.items.map((dto) => dto.toJson()),
      total: this.total,
      page: this.page,
      per_page: this.per_page,
      pages: this.pages
    }
  }
}

export class ImportDouyinVideosDto {
  created: DouyinVideoDto[]
  skipped: string[]

  constructor(created: DouyinVideoDto[], skipped: string[]) {
    this.created = created
    this.skipped = skipped
  }

  static fromJson(json: ImportDouyinVideosJson): ImportDouyinVideosDto {
    return new ImportDouyinVideosDto(
      json.created.map((item) => DouyinVideoDto.fromJson(item)),
      json.skipped
    )
  }

  toJson(): ImportDouyinVideosJson {
    return {
      created: this.created.map((dto) => dto.toJson()),
      skipped: this.skipped
    }
  }
}
