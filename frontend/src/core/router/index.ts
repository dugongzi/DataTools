import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/common/views/LoginView.vue')
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('@/common/views/UsersView.vue')
    },
    {
      path: '/',
      redirect: '/login'
    }
  ]
})

export default router
