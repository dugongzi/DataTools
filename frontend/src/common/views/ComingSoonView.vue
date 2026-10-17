<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const title = computed(() => route.meta.title ?? '即将上线')
const lead = computed(() => route.meta.lead ?? '该模块正在建设中，敬请期待。')
</script>

<template>
  <div class="page">
    <div class="page__head">
      <div>
        <h1 class="page__title">{{ title }}</h1>
        <p class="page__lead">{{ lead }}</p>
      </div>
    </div>

    <section class="panel coming">
      <span class="coming__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="26" height="26" fill="none">
          <path
            d="M12 3c4.42 0 8 1.57 8 3.5S16.42 10 12 10 4 8.43 4 6.5 7.58 3 12 3m8 8.5c0 1.93-3.58 3.5-8 3.5s-8-1.57-8-3.5m16 4.5c0 1.93-3.58 3.5-8 3.5s-8-1.57-8-3.5"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
          />
        </svg>
      </span>
      <h2 class="coming__title">该模块正在建设中</h2>
      <p class="coming__text">
        我们正在打磨 <strong>{{ title }}</strong> 的功能，稍后即可在此使用。
      </p>
    </section>
  </div>
</template>

<style scoped>
.coming {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3.5rem 2rem;
  text-align: center;
}

.coming__icon {
  display: grid;
  place-items: center;
  width: 54px;
  height: 54px;
  color: var(--accent);
  background: var(--accent-soft);
  border-radius: var(--radius-md);
}

.coming__title {
  margin: 0.5rem 0 0;
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.coming__text {
  max-width: 34ch;
  margin: 0;
  font-size: 0.9375rem;
  color: var(--text-muted);
}

.coming__text strong {
  font-weight: 600;
  color: var(--text);
}
</style>
