# Backend README

## 项目结构

```
backend/
├── app/
│   ├── __init__.py          # 应用工厂
│   ├── api/                 # API 蓝图
│   │   ├── __init__.py
│   │   └── users.py         # 用户路由
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── user.py
│   └── schemas/             # 序列化模式
│       ├── __init__.py
│       └── user.py
├── config.py                # 配置文件
├── main.py                  # 应用入口
├── requirements.txt         # 依赖列表
└── .env                     # 环境变量（不提交）

```

## 安装依赖

```bash
# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

## 运行应用

```bash
# 开发模式
python main.py

# 或使用 Flask CLI
flask run
```

## API 端点

- `GET /api/health` - 健康检查
- `GET /api/users` - 获取所有用户
- `GET /api/users/<id>` - 获取单个用户
- `POST /api/users` - 创建用户
- `PUT /api/users/<id>` - 更新用户
- `DELETE /api/users/<id>` - 删除用户

## 环境变量

在根目录的 `.env` 文件中配置：

```
MYSQL_USER=datatools_user
MYSQL_PASSWORD=datatools_password
MYSQL_DATABASE=datatools
MYSQL_PORT=3306
```
