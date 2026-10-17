import apiClient from '@/core/api/client'
import { UserDto, CreateUserDto, UpdateUserDto } from '@/core/types/dto/user.dto'
import type { UserJson } from '@/core/types/dto/user.dto'

export const userApi = {
  getAll: async () => {
    const response = await apiClient.get<UserJson[]>('/users')
    return response.data.map((json) => UserDto.fromJson(json))
  },

  getById: async (id: number) => {
    const response = await apiClient.get<UserJson>(`/users/${id}`)
    return UserDto.fromJson(response.data)
  },

  create: async (data: CreateUserDto) => {
    const response = await apiClient.post<UserJson>('/users', data.toJson())
    return UserDto.fromJson(response.data)
  },

  update: async (id: number, data: UpdateUserDto) => {
    const response = await apiClient.put<UserJson>(`/users/${id}`, data.toJson())
    return UserDto.fromJson(response.data)
  },

  delete: (id: number) => apiClient.delete(`/users/${id}`),

  health: () => apiClient.get('/health')
}
