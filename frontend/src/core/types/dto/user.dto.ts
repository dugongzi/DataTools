import { User } from '@/core/types/entities/user.entity'

export class UserDto {
  id: number
  username: string
  email: string
  created_at: string
  updated_at: string

  constructor(
    id: number,
    username: string,
    email: string,
    created_at: string,
    updated_at: string
  ) {
    this.id = id
    this.username = username
    this.email = email
    this.created_at = created_at
    this.updated_at = updated_at
  }

  static fromJson(json: any): UserDto {
    return new UserDto(
      json.id,
      json.username,
      json.email,
      json.created_at,
      json.updated_at
    )
  }

  toJson(): Record<string, any> {
    return {
      id: this.id,
      username: this.username,
      email: this.email,
      created_at: this.created_at,
      updated_at: this.updated_at
    }
  }

  toEntity(): User {
    return new User(
      this.id,
      this.username,
      this.email,
      new Date(this.created_at),
      new Date(this.updated_at)
    )
  }
}

export class CreateUserDto {
  username: string
  email: string

  constructor(username: string, email: string) {
    this.username = username
    this.email = email
  }

  static fromJson(json: any): CreateUserDto {
    return new CreateUserDto(json.username, json.email)
  }

  toJson(): Record<string, any> {
    return {
      username: this.username,
      email: this.email
    }
  }
}

export class UpdateUserDto {
  username?: string
  email?: string

  constructor(username?: string, email?: string) {
    this.username = username
    this.email = email
  }

  static fromJson(json: any): UpdateUserDto {
    return new UpdateUserDto(json.username, json.email)
  }

  toJson(): Record<string, any> {
    const result: Record<string, any> = {}
    if (this.username !== undefined) result.username = this.username
    if (this.email !== undefined) result.email = this.email
    return result
  }
}
