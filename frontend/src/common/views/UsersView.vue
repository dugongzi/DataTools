<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/core/stores/user'

const userStore = useUserStore()

onMounted(() => {
  userStore.fetchUsers()
})
</script>

<template>
  <div class="user-list">
    <h2>用户列表</h2>
    
    <div v-if="userStore.loading" class="loading">加载中...</div>
    
    <div v-else-if="userStore.error" class="error">
      {{ userStore.error }}
    </div>
    
    <div v-else class="users">
      <div v-for="user in userStore.users" :key="user.id" class="user-card">
        <h3>{{ user.username }}</h3>
        <p>{{ user.email }}</p>
        <small>创建于: {{ user.createdAt.toLocaleString() }}</small>
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-list {
  padding: 2rem;
}

.loading,
.error {
  text-align: center;
  padding: 2rem;
}

.error {
  color: #e74c3c;
}

.users {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.user-card {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.user-card h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.user-card p {
  margin: 0 0 0.5rem 0;
  color: #7f8c8d;
}

.user-card small {
  color: #95a5a6;
}
</style>
