<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/core/api/client'

const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  if (loading.value) return

  if (!username.value.trim() || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.post('/auth/login', {
      username: username.value,
      password: password.value
    })
    localStorage.setItem('access_token', response.data.access_token)
    await router.push('/users')
  } catch {
    error.value = '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>


<template>
  <div class="auth">
    <div class="auth__glow" aria-hidden="true"></div>

    <main class="auth__panel">
      <div class="brand">
        <span class="brand__mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M6 12.5l4 4 8-9"
              stroke="currentColor"
              stroke-width="2.4"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <span class="brand__name">DataTools</span>
      </div>

      <h1 class="auth__title">登录</h1>
      <p class="auth__lead">使用你的账号继续</p>

      <form class="form" novalidate @submit.prevent="handleSubmit">
        <div class="field">
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder=" "
            autocomplete="username"
            spellcheck="false"
            :disabled="loading"
          />
          <label for="username">用户名</label>
        </div>

        <div class="field">
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder=" "
            autocomplete="current-password"
            :disabled="loading"
          />
          <label for="password">密码</label>
        </div>

        <p v-if="error" class="form__error" role="alert">{{ error }}</p>

        <button class="submit" type="submit" :disabled="loading">
          <span v-if="!loading">继续</span>
          <span v-else class="submit__spinner" aria-label="登录中">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <circle
                cx="10"
                cy="10"
                r="8"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-opacity="0.25"
              />
              <path
                d="M10 2a8 8 0 018 8"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
              />
            </svg>
          </span>
        </button>
      </form>

      <div class="auth__links">
        <a href="#">忘记密码？</a>
        <a href="#">创建账号</a>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ---------- 设计变量（浅色） ---------- */
.auth {
  --bg: #f5f5f7;
  --glow-a: rgba(0, 113, 227, 0.16);
  --glow-b: rgba(255, 45, 85, 0.12);
  --panel-bg: rgba(255, 255, 255, 0.72);
  --panel-border: rgba(255, 255, 255, 0.7);
  --text: #1d1d1f;
  --text-muted: #6e6e73;
  --field-bg: rgba(120, 120, 128, 0.08);
  --field-bg-hover: rgba(120, 120, 128, 0.12);
  --field-bg-focus: #ffffff;
  --field-border: transparent;
  --field-border-focus: #0071e3;
  --field-ring: rgba(0, 113, 227, 0.15);
  --accent: #0071e3;
  --accent-hover: #0077ed;
  --accent-active: #006edb;
  --danger-bg: rgba(255, 59, 48, 0.08);
  --danger: #d70015;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.04), 0 24px 60px rgba(0, 0, 0, 0.1);

  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: clamp(1.25rem, 4vw, 2.5rem);
  background: var(--bg);
  overflow: hidden;
  color: var(--text);
}

/* ---------- 背景光晕 ---------- */
.auth__glow {
  position: absolute;
  inset: -20%;
  background:
    radial-gradient(38vw 38vw at 18% 12%, var(--glow-a), transparent 70%),
    radial-gradient(34vw 34vw at 82% 88%, var(--glow-b), transparent 70%);
  filter: blur(20px);
  pointer-events: none;
}

/* ---------- 面板 ---------- */
.auth__panel {
  position: relative;
  width: 100%;
  max-width: 380px;
  padding: clamp(2rem, 6vw, 2.5rem);
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 20px;
  box-shadow: var(--shadow);
  backdrop-filter: saturate(180%) blur(30px);
  -webkit-backdrop-filter: saturate(180%) blur(30px);
  animation: rise 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
}

/* ---------- 品牌 ---------- */
.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 2rem;
}

.brand__mark {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--accent);
  color: #fff;
}

.brand__mark svg {
  width: 18px;
  height: 18px;
}

.brand__name {
  font-size: 0.9375rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

/* ---------- 标题 ---------- */
.auth__title {
  margin: 0;
  font-size: clamp(1.75rem, 5vw, 2rem);
  font-weight: 600;
  letter-spacing: -0.022em;
  line-height: 1.12;
}

.auth__lead {
  margin: 0.375rem 0 0;
  font-size: 0.9375rem;
  color: var(--text-muted);
  letter-spacing: -0.01em;
}

/* ---------- 表单 ---------- */
.form {
  display: grid;
  gap: 0.75rem;
  margin-top: 1.75rem;
}

.field {
  position: relative;
}

.field input {
  width: 100%;
  height: 54px;
  padding: 1.35rem 1rem 0.45rem;
  font-size: 1rem;
  color: var(--text);
  background: var(--field-bg);
  border: 1px solid var(--field-border);
  border-radius: 12px;
  outline: none;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.field input:hover:not(:disabled) {
  background: var(--field-bg-hover);
}

.field input:focus {
  background: var(--field-bg-focus);
  border-color: var(--field-border-focus);
  box-shadow: 0 0 0 4px var(--field-ring);
}

.field input:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.field label {
  position: absolute;
  top: 50%;
  left: 1rem;
  transform: translateY(-50%);
  font-size: 1rem;
  color: var(--text-muted);
  pointer-events: none;
  transition:
    top 0.18s ease,
    font-size 0.18s ease,
    color 0.18s ease;
}

.field input:focus + label,
.field input:not(:placeholder-shown) + label {
  top: 15px;
  font-size: 0.6875rem;
  letter-spacing: 0.01em;
}

.field input:focus + label {
  color: var(--accent);
}

/* ---------- 错误 ---------- */
.form__error {
  margin: 0;
  padding: 0.625rem 0.875rem;
  font-size: 0.8125rem;
  line-height: 1.4;
  color: var(--danger);
  background: var(--danger-bg);
  border-radius: 10px;
}

/* ---------- 提交按钮 ---------- */
.submit {
  display: grid;
  place-items: center;
  height: 52px;
  margin-top: 0.5rem;
  font-size: 1.0625rem;
  font-weight: 500;
  letter-spacing: -0.01em;
  color: #fff;
  background: var(--accent);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition:
    background 0.2s ease,
    transform 0.12s ease;
}

.submit:hover:not(:disabled) {
  background: var(--accent-hover);
}

.submit:active:not(:disabled) {
  background: var(--accent-active);
  transform: scale(0.985);
}

.submit:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.submit__spinner svg {
  width: 20px;
  height: 20px;
  display: block;
  animation: spin 0.75s linear infinite;
}

/* ---------- 底部链接 ---------- */
.auth__links {
  display: flex;
  justify-content: center;
  gap: 1.25rem;
  margin-top: 1.75rem;
  font-size: 0.875rem;
}

.auth__links a {
  color: var(--accent);
  text-decoration: none;
}

.auth__links a:hover {
  text-decoration: underline;
}

/* ---------- 动效 ---------- */
@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.99);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ---------- 深色（跟随系统） ---------- */
@media (prefers-color-scheme: dark) {
  .auth {
    --bg: #000000;
    --glow-a: rgba(10, 132, 255, 0.22);
    --glow-b: rgba(255, 69, 58, 0.14);
    --panel-bg: rgba(28, 28, 30, 0.72);
    --panel-border: rgba(255, 255, 255, 0.08);
    --text: #f5f5f7;
    --text-muted: #98989d;
    --field-bg: rgba(120, 120, 128, 0.24);
    --field-bg-hover: rgba(120, 120, 128, 0.32);
    --field-bg-focus: rgba(120, 120, 128, 0.32);
    --field-border-focus: #0a84ff;
    --field-ring: rgba(10, 132, 255, 0.25);
    --accent: #0a84ff;
    --accent-hover: #2a95ff;
    --accent-active: #0071e3;
    --danger-bg: rgba(255, 69, 58, 0.12);
    --danger: #ff6961;
    --shadow: 0 2px 8px rgba(0, 0, 0, 0.4), 0 24px 60px rgba(0, 0, 0, 0.6);
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth__panel {
    animation: none;
  }

  .submit__spinner svg {
    animation-duration: 1.6s;
  }
}
</style>
