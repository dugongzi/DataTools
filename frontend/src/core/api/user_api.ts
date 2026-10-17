import apiClient from '@/core/api/client'
import { UserDto, CreateUserDto, UpdateUserDto } from '@/core/types/dto/user.dto'

export const userApi = {
  getAll: async () => {
    const response = await apiClient.get('/users')
    return response.data.map((json: any) => UserDto.fromJson(json))
  },
  
  getById: async (id: number) => {
    const response = await apiClient.get(`/users/${id}`)
    return UserDto.fromJson(response.data)
  },
  
  create: async (data: CreateUserDto) => {
    const response = await apiClient.post('/users', data.toJson())
    return UserDto.fromJson(response.data)
  },
  
  update: async (id: number, data: UpdateUserDto) => {
    const response = await apiClient.put(`/users/${id}`, data.toJson())
    return UserDto.fromJson(response.data)
  },
  
  delete: (id: number) => apiClient.delete(`/users/${id}`),
  
  health: () => apiClient.get('/health')
}
