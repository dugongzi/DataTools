import { createRouter, createWebHistory } from 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    lead?: string
    requiresAuth?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/common/views/LoginView.vue')
    },
    {
      path: '/',
      component: () => import('@/common/layout/AppShell.vue'),
      redirect: { name: 'dashboard' },
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/common/views/ComingSoonView.vue'),
          meta: {
            requiresAuth: true,
            title: '仪表盘',
            lead: '概览关键指标与近期动态。'
          }
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/common/views/UsersView.vue'),
          meta: {
            requiresAuth: true,
            title: '用户管理',
            lead: '创建账号、分配权限并维护用户资料。'
          }
        },
        {
          path: 'douyin',
          name: 'douyin',
          component: () => import('@/common/views/DouyinVideoView.vue'),
          meta: {
            requiresAuth: true,
            title: '抖音视频监控',
            lead: '粘贴抖音分享文本，解析链接并收录到监控列表。'
          }
        },
        {
          path: 'datasets',
          name: 'datasets',
          component: () => import('@/common/views/ComingSoonView.vue'),
          meta: {
            requiresAuth: true,
            title: '数据集',
            lead: '浏览、导入与整理数据集合。'
          }
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/common/views/SettingsView.vue'),
          meta: {
            requiresAuth: true,
            title: '设置',
            lead: '配置抖音监控的采集时机、并发与重试策略。'
          }
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: { name: 'dashboard' }
    }
  ]
})

router.beforeEach((to) => {
  const authenticated = Boolean(localStorage.getItem('access_token'))
  if (to.meta.requiresAuth && !authenticated) {
    return { name: 'login' }
  }
  if (to.name === 'login' && authenticated) {
    return { name: 'dashboard' }
  }
})

export default router
