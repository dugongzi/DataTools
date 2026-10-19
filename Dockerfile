# ---------- 阶段 1：构建前端 ----------
FROM node:22-alpine AS frontend-builder

WORKDIR /app

# 安装 pnpm（与 pnpm-lock.yaml v9 兼容）
RUN npm install -g pnpm@9

# 复制依赖清单（lockfile 已纳入版本控制，保证构建可复现）
COPY frontend/package.json frontend/pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile

COPY frontend/ ./

# 前端请求统一走同容器内的 nginx 反向代理
ENV VITE_API_BASE_URL=/api
RUN pnpm run build

# ---------- 阶段 2：运行时（nginx + gunicorn 同一镜像） ----------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium \
    && apt-get update \
    && apt-get install -y --no-install-recommends nginx supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

COPY backend ./backend
COPY --from=frontend-builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 同一容器内同时管理 nginx 与 gunicorn
RUN printf '%s\n' \
    '[supervisord]' \
    'nodaemon=true' \
    'logfile=/dev/null' \
    'logfile_maxbytes=0' \
    'pidfile=/tmp/supervisord.pid' \
    '' \
    '[program:nginx]' \
    'command=nginx -g "daemon off;"' \
    'priority=10' \
    'stdout_logfile=/dev/stdout' \
    'stdout_logfile_maxbytes=0' \
    'stderr_logfile=/dev/stderr' \
    'stderr_logfile_maxbytes=0' \
    '' \
    '[program:gunicorn]' \
    'command=gunicorn --chdir /app --bind 0.0.0.0:5000 --workers 2 --timeout 120 backend.main:app' \
    'priority=20' \
    'stdout_logfile=/dev/stdout' \
    'stdout_logfile_maxbytes=0' \
    'stderr_logfile=/dev/stderr' \
    'stderr_logfile_maxbytes=0' \
    > /etc/supervisor/conf.d/datatools.conf

EXPOSE 80 5000

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/datatools.conf"]
