<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useUserStore } from '@/core/stores/user'
import { CreateUserDto, UpdateUserDto } from '@/core/types/dto/user.dto'
import type { User } from '@/core/types/entities/user.entity'

const userStore = useUserStore()

const pageLoading = ref(true)
const loadError = ref<string | null>(null)
const busyId = ref<number | null>(null)

const showCreate = ref(false)
const creating = ref(false)
const newUsername = ref('')
const newPassword = ref('')

const editingId = ref<number | null>(null)
const updating = ref(false)
const editUsername = ref('')
const editPassword = ref('')

const notice = ref<{ kind: 'success' | 'error'; text: string } | null>(null)
let noticeTimer: ReturnType<typeof setTimeout> | undefined

function flash(kind: 'success' | 'error', text: string) {
  notice.value = { kind, text }
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => {
    notice.value = null
  }, 4000)
}

function formatDate(value: Date) {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) return '—'
  return value.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function initial(name: string) {
  return name.trim().charAt(0).toUpperCase() || '?'
}

async function load() {
  pageLoading.value = true
  loadError.value = null
  await userStore.fetchUsers()
  loadError.value = userStore.error
  pageLoading.value = false
}

function resetForm() {
  newUsername.value = ''
  newPassword.value = ''
}

function toggleCreate() {
  if (!showCreate.value) closeEdit()
  showCreate.value = !showCreate.value
  if (!showCreate.value) resetForm()
}

function openEdit(user: User) {
  showCreate.value = false
  resetForm()
  editingId.value = user.id
  editUsername.value = user.username
  editPassword.value = ''
}

function closeEdit() {
  editingId.value = null
  editUsername.value = ''
  editPassword.value = ''
}

async function submitCreate() {
  if (creating.value) return

  const username = newUsername.value.trim()
  const password = newPassword.value

  if (!username || !password) {
    flash('error', '请填写用户名和密码')
    return
  }

  if (password.length < 6) {
    flash('error', '密码至少需要 6 位字符')
    return
  }

  creating.value = true
  try {
    await userStore.createUser(new CreateUserDto(username, password))
    flash('success', `已创建用户 ${username}，可用该密码登录后台`)
    resetForm()
    showCreate.value = false
  } catch {
    flash('error', '创建失败，请检查输入后重试')
  } finally {
    creating.value = false
  }
}

async function submitEdit() {
  if (updating.value || editingId.value === null) return

  const id = editingId.value
  const username = editUsername.value.trim()
  const password = editPassword.value

  if (!username) {
    flash('error', '请填写用户名')
    return
  }

  if (password && password.length < 6) {
    flash('error', '新密码至少需要 6 位字符')
    return
  }

  updating.value = true
  try {
    await userStore.updateUser(id, new UpdateUserDto(username, password || undefined))
    flash('success', `已更新用户 ${username}`)
    closeEdit()
  } catch (e) {
    const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error
    if (msg === 'Username already exists') flash('error', '用户名已存在')
    else flash('error', '更新失败，请检查输入后重试')
  } finally {
    updating.value = false
  }
}

async function removeUser(id: number, username: string) {
  if (busyId.value !== null) return
  if (!window.confirm(`确定删除用户「${username}」？此操作不可撤销。`)) return

  busyId.value = id
  try {
    await userStore.deleteUser(id)
    if (editingId.value === id) closeEdit()
    flash('success', `已删除用户 ${username}`)
  } catch {
    flash('error', '删除失败，请稍后重试')
  } finally {
    busyId.value = null
  }
}

onMounted(load)

onBeforeUnmount(() => {
  clearTimeout(noticeTimer)
})
</script>

<template>
  <div class="page">
    <div class="page__head">
      <div>
        <h1 class="page__title">用户管理</h1>
        <p class="page__lead">创建账号、分配权限并维护用户资料</p>
      </div>

      <div class="page__actions">
        <button class="btn btn--quiet" type="button" :disabled="pageLoading" @click="load">
          刷新
        </button>
        <button class="btn btn--primary" type="button" @click="toggleCreate">
          {{ showCreate ? '取消' : '新建用户' }}
        </button>
      </div>
    </div>

    <p
      v-if="notice"
      class="notice"
      :class="`notice--${notice.kind}`"
      role="status"
      aria-live="polite"
    >
      {{ notice.text }}
    </p>

    <form v-if="showCreate" class="create" @submit.prevent="submitCreate">
      <div class="create__field">
        <input
          id="new-username"
          v-model="newUsername"
          type="text"
          placeholder=" "
          autocomplete="off"
          spellcheck="false"
          :disabled="creating"
        />
        <label for="new-username">用户名</label>
      </div>

      <div class="create__field">
        <input
          id="new-password"
          v-model="newPassword"
          type="password"
          placeholder=" "
          autocomplete="new-password"
          :disabled="creating"
        />
        <label for="new-password">密码</label>
      </div>

      <button class="btn btn--primary create__submit" type="submit" :disabled="creating">
        {{ creating ? '创建中…' : '创建' }}
      </button>
    </form>

    <form v-if="editingId !== null" class="create" @submit.prevent="submitEdit">
      <div class="create__field">
        <input
          id="edit-username"
          v-model="editUsername"
          type="text"
          placeholder=" "
          autocomplete="off"
          spellcheck="false"
          :disabled="updating"
        />
        <label for="edit-username">用户名</label>
      </div>

      <div class="create__field">
        <input
          id="edit-password"
          v-model="editPassword"
          type="password"
          placeholder=" "
          autocomplete="new-password"
          :disabled="updating"
        />
        <label for="edit-password">新密码（留空不改）</label>
      </div>

      <div class="create__actions">
        <button class="btn btn--primary" type="submit" :disabled="updating">
          {{ updating ? '保存中…' : '保存' }}
        </button>
        <button class="btn btn--quiet" type="button" :disabled="updating" @click="closeEdit">
          取消
        </button>
      </div>
    </form>

    <section class="panel" :aria-busy="pageLoading">
      <div v-if="pageLoading" class="skeleton" aria-hidden="true">
        <div v-for="row in 4" :key="row" class="skeleton__row">
          <span class="skeleton__cell skeleton__cell--wide"></span>
          <span class="skeleton__cell"></span>
          <span class="skeleton__cell skeleton__cell--short"></span>
        </div>
      </div>

      <div v-else-if="loadError" class="state">
        <span class="state__icon state__icon--danger" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M12 8v5m0 3.5v.01M10.29 3.86L2.82 17a2 2 0 001.74 3h14.88a2 2 0 001.74-3L13.71 3.86a2 2 0 00-3.42 0z"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <h2 class="state__title">无法加载用户</h2>
        <p class="state__lead">{{ loadError }}</p>
        <button class="btn btn--primary" type="button" @click="load">重试</button>
      </div>

      <div v-else-if="!userStore.users.length" class="state">
        <span class="state__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M16 20v-1.5a3.5 3.5 0 00-3.5-3.5h-5A3.5 3.5 0 004 18.5V20M10 11.5a3.75 3.75 0 100-7.5 3.75 3.75 0 000 7.5zM19 20v-1.5a3.5 3.5 0 00-2.6-3.38M15.5 4.2a3.75 3.75 0 010 7.1"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <h2 class="state__title">还没有用户</h2>
        <p class="state__lead">创建第一个账号，或先刷新查看最新数据。</p>
        <button class="btn btn--primary" type="button" @click="toggleCreate">新建用户</button>
      </div>

      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th scope="col">用户</th>
              <th scope="col">创建时间</th>
              <th scope="col">更新时间</th>
              <th scope="col" class="table__actions-head">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in userStore.users" :key="user.id">
              <td data-label="用户">
                <span class="cell-user">
                  <span class="cell-user__avatar" aria-hidden="true">
                    {{ initial(user.username) }}
                  </span>
                  <span class="cell-user__name">{{ user.username }}</span>
                </span>
              </td>
              <td data-label="创建时间" class="cell-date">{{ formatDate(user.createdAt) }}</td>
              <td data-label="更新时间" class="cell-date">{{ formatDate(user.updatedAt) }}</td>
              <td data-label="操作" class="cell-actions">
                <button
                  class="btn btn--quiet"
                  type="button"
                  :disabled="busyId !== null || updating"
                  @click="openEdit(user)"
                >
                  编辑
                </button>
                <button
                  class="btn btn--danger"
                  type="button"
                  :disabled="busyId !== null"
                  @click="removeUser(user.id, user.username)"
                >
                  {{ busyId === user.id ? '删除中…' : '删除' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ---------- 页头操作 ---------- */
.page__actions {
  display: flex;
  gap: 0.5rem;
}

/* ---------- 提示条 ---------- */
.notice {
  margin: 0;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  border-radius: var(--radius-md);
  animation: fade-in 0.28s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.notice--success {
  color: var(--success);
  background: var(--success-bg);
}

.notice--error {
  color: var(--danger);
  background: var(--danger-bg);
}

/* ---------- 新建表单 ---------- */
.create {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr)) auto;
  gap: 0.75rem;
  align-items: center;
  padding: 1rem;
  background: var(--surface);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--surface-shadow);
  backdrop-filter: saturate(180%) blur(30px);
  -webkit-backdrop-filter: saturate(180%) blur(30px);
  animation: rise 0.32s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.create__field {
  position: relative;
}

.create__field input {
  width: 100%;
  height: 44px;
  padding: 1.125rem 0.875rem 0.375rem;
  font-size: 0.9375rem;
  color: var(--text);
  background: var(--field-bg);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  outline: none;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.create__field input:hover:not(:disabled) {
  background: var(--field-bg-hover);
}

.create__field input:focus {
  background: var(--field-bg-focus);
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-ring);
}

.create__field label {
  position: absolute;
  top: 50%;
  left: 0.875rem;
  transform: translateY(-50%);
  font-size: 0.9375rem;
  color: var(--text-muted);
  pointer-events: none;
  transition:
    top 0.18s ease,
    font-size 0.18s ease,
    color 0.18s ease;
}

.create__field input:focus + label,
.create__field input:not(:placeholder-shown) + label {
  top: 12px;
  font-size: 0.625rem;
  letter-spacing: 0.01em;
}

.create__field input:focus + label {
  color: var(--accent);
}

.create__submit {
  height: 44px;
  padding: 0 1.25rem;
  border-radius: var(--radius-md);
}

.create__actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.create__actions .btn {
  height: 44px;
  padding: 0 1.25rem;
  border-radius: var(--radius-md);
}

/* ---------- 骨架 ---------- */
.skeleton {
  display: grid;
  gap: 1px;
  background: var(--separator);
}

.skeleton__row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--surface-solid);
}

.skeleton__cell {
  flex: 1;
  height: 10px;
  border-radius: var(--radius-pill);
  background: var(--field-bg);
  animation: pulse 1.4s ease-in-out infinite;
}

.skeleton__cell--wide {
  flex: 1.4;
}

.skeleton__cell--short {
  flex: 0.7;
}

/* ---------- 状态 ---------- */
.state {
  display: grid;
  justify-items: center;
  gap: 0.5rem;
  padding: clamp(2.5rem, 8vw, 4rem) 1.5rem;
  text-align: center;
}

.state__icon {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  margin-bottom: 0.5rem;
  border-radius: var(--radius-md);
  background: var(--field-bg);
  color: var(--text-subtle);
}

.state__icon--danger {
  background: var(--danger-bg);
  color: var(--danger);
}

.state__icon svg {
  width: 24px;
  height: 24px;
}

.state__title {
  margin: 0;
  font-size: 1.0625rem;
  font-weight: 600;
  letter-spacing: -0.022em;
}

.state__lead {
  margin: 0 0 0.75rem;
  max-width: 34ch;
  font-size: 0.875rem;
  color: var(--text-muted);
}

/* ---------- 表格 ---------- */
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.table thead th {
  padding: 0.75rem 1.25rem;
  text-align: left;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-subtle);
  background: transparent;
  border-bottom: 1px solid var(--separator);
  white-space: nowrap;
}

.table__actions-head {
  text-align: right;
}

.table tbody tr {
  transition: background 0.16s ease;
}

.table tbody tr:nth-child(n + 2) td {
  border-top: 1px solid var(--separator);
}

.table tbody tr:hover {
  background: var(--field-bg);
}

.table td {
  padding: 0.875rem 1.25rem;
  vertical-align: middle;
  color: var(--text);
}

.cell-user {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.cell-user__avatar {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: var(--radius-pill);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 600;
}

.cell-user__name {
  font-weight: 500;
  letter-spacing: -0.01em;
}

.cell-date {
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.cell-actions {
  text-align: right;
}

/* ---------- 响应式：表格 → 卡片 ---------- */
@media (max-width: 720px) {
  .page__head {
    align-items: flex-start;
  }

  .create {
    grid-template-columns: 1fr;
  }

  .table thead {
    display: none;
  }

  .table,
  .table tbody,
  .table tr,
  .table td {
    display: block;
    width: 100%;
  }

  .table tbody tr {
    padding: 0.5rem 0;
  }

  .table tbody tr:nth-child(n + 2) {
    border-top: 1px solid var(--separator);
  }

  .table tbody tr:nth-child(n + 2) td {
    border-top: none;
  }

  .table td {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.4375rem 1.25rem;
    text-align: right;
  }

  .table td::before {
    content: attr(data-label);
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-subtle);
  }

  .cell-actions {
    justify-content: flex-end;
    padding-top: 0.75rem;
  }
}
</style>
