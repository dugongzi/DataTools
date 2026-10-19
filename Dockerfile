# 构建阶段
FROM node:22-alpine AS builder

WORKDIR /app

# 安装 pnpm（与 pnpm-lock.yaml v9 兼容）
RUN npm install -g pnpm@9

# 复制依赖清单（lockfile 已纳入版本控制，保证构建可复现）
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY frontend/ ./

# 构建应用
RUN pnpm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物到 nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置（可选）
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
