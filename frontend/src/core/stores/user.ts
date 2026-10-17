import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userApi } from '@/core/api/user_api.ts'
import { User } from '@/core/types/entities/user.entity'
import { UserDto, CreateUserDto, UpdateUserDto } from '@/core/types/dto/user.dto'

export const useUserStore = defineStore('user', () => {
  const users = ref<User[]>([])
  const currentUser = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchUsers() {
    loading.value = true
    error.value = null
    try {
      const dtos = await userApi.getAll()
      users.value = dtos.map((dto: UserDto) => dto.toEntity())
    } catch (e) {
      error.value = 'Failed to fetch users'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchUserById(id: number) {
    loading.value = true
    error.value = null
    try {
      const dto = await userApi.getById(id)
      currentUser.value = dto.toEntity()
    } catch (e) {
      error.value = 'Failed to fetch user'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function createUser(data: CreateUserDto) {
    loading.value = true
    error.value = null
    try {
      const dto = await userApi.create(data)
      const user = dto.toEntity()
      users.value.push(user)
      return user
    } catch (e) {
      error.value = 'Failed to create user'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateUser(id: number, data: UpdateUserDto) {
    loading.value = true
    error.value = null
    try {
      const dto = await userApi.update(id, data)
      const user = dto.toEntity()
      const index = users.value.findIndex(u => u.id === id)
      if (index !== -1) {
        users.value[index] = user
      }
      return user
    } catch (e) {
      error.value = 'Failed to update user'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteUser(id: number) {
    loading.value = true
    error.value = null
    try {
      await userApi.delete(id)
      users.value = users.value.filter(u => u.id !== id)
    } catch (e) {
      error.value = 'Failed to delete user'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    users,
    currentUser,
    loading,
    error,
    fetchUsers,
    fetchUserById,
    createUser,
    updateUser,
    deleteUser
  }
})
