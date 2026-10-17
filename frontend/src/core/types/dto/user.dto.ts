import { User } from '@/core/types/entities/user.entity'

export interface UserJson {
  id: number
  username: string
  created_at: string
  updated_at: string
}

export interface CreateUserJson {
  username: string
  password: string
}

export interface UpdateUserJson {
  username?: string
  password?: string
}

export class UserDto {
  id: number
  username: string
  created_at: string
  updated_at: string

  constructor(id: number, username: string, created_at: string, updated_at: string) {
    this.id = id
    this.username = username
    this.created_at = created_at
    this.updated_at = updated_at
  }

  static fromJson(json: UserJson): UserDto {
    return new UserDto(json.id, json.username, json.created_at, json.updated_at)
  }

  toJson(): UserJson {
    return {
      id: this.id,
      username: this.username,
      created_at: this.created_at,
      updated_at: this.updated_at
    }
  }

  toEntity(): User {
    return new User(this.id, this.username, new Date(this.created_at), new Date(this.updated_at))
  }
}

export class CreateUserDto {
  username: string
  password: string

  constructor(username: string, password: string) {
    this.username = username
    this.password = password
  }

  static fromJson(json: CreateUserJson): CreateUserDto {
    return new CreateUserDto(json.username, json.password)
  }

  toJson(): CreateUserJson {
    return {
      username: this.username,
      password: this.password
    }
  }
}

export class UpdateUserDto {
  username?: string
  password?: string

  constructor(username?: string, password?: string) {
    this.username = username
    this.password = password
  }

  static fromJson(json: UpdateUserJson): UpdateUserDto {
    return new UpdateUserDto(json.username, json.password)
  }

  toJson(): UpdateUserJson {
    const result: UpdateUserJson = {}
    if (this.username !== undefined) result.username = this.username
    if (this.password !== undefined) result.password = this.password
    return result
  }
}
