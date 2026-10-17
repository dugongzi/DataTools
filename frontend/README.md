# Frontend 项目结构

## 目录结构

```
frontend/
├── src/
│   ├── api/                 # API 接口层
│   │   ├── client.ts        # Axios 实例配置
│   │   ├── user_api.ts         # 用户 API
│   │   └── index.ts         # 统一导出
│   ├── assets/              # 静态资源
│   ├── components/          # 可复用组件
│   ├── router/              # 路由配置
│   │   └── index.ts
│   ├── stores/              # Pinia 状态管理
│   │   ├── counter.ts       # 示例 store
│   │   └── user.ts          # 用户 store
│   ├── types/               # TypeScript 类型定义
│   │   ├── user.ts
│   │   └── index.ts
│   ├── views/               # 页面组件
│   │   ├── HomeView.vue
│   │   ├── UsersView.vue
│   │   └── AboutView.vue
│   ├── App.vue
│   └── main.ts
├── .env.development         # 开发环境变量
├── .env.production          # 生产环境变量
└── package.json

```

## 技术栈

- **Vue 3** - 渐进式框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端

## 架构模式

### API 层
- `api/client.ts` - 统一的 Axios 配置，包含拦截器
- `api/user_api.ts` - 按业务模块划分的 API 接口

### 状态管理
- 使用 Pinia Composition API 风格
- 每个 store 负责一个业务领域
- 包含 loading 和 error 状态

### 类型系统
- 统一的类型定义在 `types/` 目录
- DTO (Data Transfer Object) 类型用于 API 请求
- 严格的类型检查

## 环境变量

开发环境 (`.env.development`):
```
VITE_API_BASE_URL=http://localhost:5000/api
```

生产环境 (`.env.production`):
```
VITE_API_BASE_URL=http://localhost:3000/api
```

## 快速开始

```bash
# 安装依赖
pnpm install

# 开发模式
pnpm dev

# 构建生产
pnpm build

# 类型检查
pnpm type-check

# 代码格式化
pnpm format
```

## 路由

- `/` - 首页
- `/users` - 用户列表
- `/about` - 关于页面

## 开发规范

1. **组件命名** - 使用 PascalCase (如 `UserList.vue`)
2. **组合式 API** - 统一使用 `<script setup>` 语法
3. **类型安全** - 为所有 props、emits 定义类型
4. **状态管理** - 复杂状态用 Pinia，局部状态用 ref/reactive
5. **API 调用** - 统一在 store 中调用，组件只负责展示
