<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'

interface NavItem {
  name: string
  label: string
  icon: string
}

const navItems: NavItem[] = [
  {
    name: 'dashboard',
    label: '仪表盘',
    icon: 'M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z'
  },
  {
    name: 'users',
    label: '用户管理',
    icon: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8m0 2c-4.42 0-8 2.24-8 5v1h16v-1c0-2.76-3.58-5-8-5'
  },
  {
    name: 'douyin',
    label: '抖音视频监控',
    icon: 'M4 6h9a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2M17 10.5 21 8v8l-4-2.5z'
  },
  {
    name: 'datasets',
    label: '数据集',
    icon: 'M12 3c4.42 0 8 1.57 8 3.5S16.42 10 12 10 4 8.43 4 6.5 7.58 3 12 3m8 8.5c0 1.93-3.58 3.5-8 3.5s-8-1.57-8-3.5m16 4.5c0 1.93-3.58 3.5-8 3.5s-8-1.57-8-3.5'
  },
  {
    name: 'settings',
    label: '设置',
    icon: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6m7.4-1.6-.9-.5a5.9 5.9 0 0 0 0-1.8l.9-.5a1 1 0 0 0 .4-1.3l-1.3-2.3a1 1 0 0 0-1.3-.4l-.9.5a6 6 0 0 0-1.6-.9V5a1 1 0 0 0-1-1h-2.6a1 1 0 0 0-1 1v1a6 6 0 0 0-1.6.9l-.9-.5a1 1 0 0 0-1.3.4L4.2 9.1a1 1 0 0 0 .4 1.3l.9.5a5.9 5.9 0 0 0 0 1.8l-.9.5a1 1 0 0 0-.4 1.3l1.3 2.3a1 1 0 0 0 1.3.4l.9-.5a6 6 0 0 0 1.6.9v1a1 1 0 0 0 1 1h2.6a1 1 0 0 0 1-1v-1a6 6 0 0 0 1.6-.9l.9.5a1 1 0 0 0 1.3-.4l1.3-2.3a1 1 0 0 0-.4-1.3'
  }
]

const router = useRouter()
const username = ref(localStorage.getItem('username') ?? '')

const initial = computed(() => username.value.trim().charAt(0).toUpperCase() || '?')

function handleLogout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('username')
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="shell">
    <div class="shell__glow" aria-hidden="true"></div>

    <aside class="sidebar">
      <div class="brand">
        <span class="brand__mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
            <path
              d="M12 3c4.42 0 8 1.57 8 3.5S16.42 10 12 10 4 8.43 4 6.5 7.58 3 12 3m8 8.5c0 1.93-3.58 3.5-8 3.5s-8-1.57-8-3.5m16 4.5c0 1.93-3.58 3.5-8 3.5s-8-1.57-8-3.5"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
        </span>
        <span class="brand__text">DataTools</span>
      </div>

      <nav class="nav" aria-label="主导航">
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="nav__item"
          active-class="nav__item--active"
        >
          <svg class="nav__icon" viewBox="0 0 24 24" width="18" height="18" fill="none">
            <path
              :d="item.icon"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <span class="nav__label">{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <div class="shell__main">
      <header class="topbar">
        <div class="who">
          <span class="who__avatar" aria-hidden="true">{{ initial }}</span>
          <span class="who__name">{{ username || '未登录' }}</span>
        </div>
        <button type="button" class="btn btn--ghost" @click="handleLogout">退出登录</button>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  position: relative;
  display: grid;
  grid-template-columns: 248px minmax(0, 1fr);
  min-height: 100vh;
  isolation: isolate;
}

.shell__glow {
  position: fixed;
  inset: -20% -10% auto;
  height: 60vh;
  z-index: -1;
  pointer-events: none;
  background:
    radial-gradient(38% 60% at 18% 0%, var(--accent-soft), transparent 70%),
    radial-gradient(30% 55% at 82% 0%, rgba(120, 90, 255, 0.14), transparent 70%);
}

/* ---------- sidebar ---------- */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem 1rem;
  background: var(--surface);
  border-right: 1px solid var(--surface-border);
  backdrop-filter: saturate(180%) blur(30px);
  -webkit-backdrop-filter: saturate(180%) blur(30px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0 0.5rem;
}

.brand__mark {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  color: #fff;
  background: var(--accent);
  border-radius: var(--radius-sm);
  box-shadow: var(--accent-ring);
}

.brand__text {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 0.1875rem;
}

.nav__item {
  display: flex;
  align-items: center;
  gap: 0.6875rem;
  padding: 0.5625rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-muted);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition:
    background 0.2s ease,
    color 0.2s ease;
}

.nav__item:hover {
  color: var(--text);
  background: var(--field-bg);
}

.nav__item--active {
  color: var(--accent);
  background: var(--accent-soft);
}

.nav__icon {
  flex-shrink: 0;
}

/* ---------- main ---------- */
.shell__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
  height: 60px;
  padding: 0 1.5rem;
  border-bottom: 1px solid var(--separator);
  animation: fade-in 0.4s ease both;
}

.who {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.who__avatar {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text);
  background: var(--field-bg);
  border: 1px solid var(--surface-border);
  border-radius: 50%;
}

.content {
  flex: 1;
  padding: 2rem 1.5rem 3rem;
}

@media (max-width: 860px) {
  .shell {
    grid-template-columns: minmax(0, 1fr);
  }

  .sidebar {
    position: sticky;
    top: 0;
    z-index: 2;
    flex-direction: row;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    border-right: none;
    border-bottom: 1px solid var(--surface-border);
    overflow-x: auto;
  }

  .nav {
    flex-direction: row;
    gap: 0.25rem;
  }

  .nav__item {
    white-space: nowrap;
  }
}
</style>
