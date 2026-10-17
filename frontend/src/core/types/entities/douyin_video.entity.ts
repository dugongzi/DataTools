export class DouyinVideo {
  id: number
  url: string
  author: string | null
  title: string | null
  rawText: string | null
  createdAt: Date
  updatedAt: Date

  constructor(
    id: number,
    url: string,
    author: string | null,
    title: string | null,
    rawText: string | null,
    createdAt: Date,
    updatedAt: Date
  ) {
    this.id = id
    this.url = url
    this.author = author
    this.title = title
    this.rawText = rawText
    this.createdAt = createdAt
    this.updatedAt = updatedAt
  }
}
