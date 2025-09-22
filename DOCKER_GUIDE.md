# VMatch Backend Docker 部署指南

## 快速开始

### 1. 环境准备
确保已安装 Docker 和 Docker Compose。

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的配置项
```

### 3. 构建和启动服务
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 验证服务
访问 http://localhost:8000/docs 查看 API 文档。

## 配置说明

### 必要的环境变量
- `SECRET_KEY`: 应用密钥，必须设置为随机字符串
- `LLM_API_KEY`: LLM 服务 API 密钥

### 可选配置
- `DATABASE_URL`: 数据库连接字符串（默认使用 SQLite）
- `LLM_*`: LLM 相关配置
- `MAX_*`: 文件大小限制配置

## 数据持久化

### 数据库文件
SQLite 数据库文件 `vmatch_production.db` 会被挂载到主机，确保数据持久化。

### 上传文件
上传的文件会保存在 `./uploads` 目录，也会被持久化。

## 生产环境建议

### 1. 使用外部数据库
建议在生产环境使用 PostgreSQL 或 MySQL：
```yaml
environment:
  - DATABASE_URL=postgresql://user:password@db:5432/vmatch
```

### 2. 使用反向代理
配置 Nginx 作为反向代理，添加 HTTPS 支持。

### 3. 资源限制
在 docker-compose.yml 中添加资源限制：
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## 常用命令

```bash
# 查看容器状态
docker-compose ps

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 查看日志
docker-compose logs vmatch-backend

# 进入容器
docker-compose exec vmatch-backend bash

# 备份数据库
docker-compose exec vmatch-backend sqlite3 vmatch_production.db ".backup backup.db"
```

## 故障排查

### 容器无法启动
1. 检查端口是否被占用
2. 查看日志：`docker-compose logs vmatch-backend`
3. 检查环境变量配置

### 数据库连接问题
1. 检查数据库文件权限
2. 验证数据库连接字符串
3. 检查磁盘空间

### 性能问题
1. 检查容器资源使用情况
2. 优化数据库查询
3. 考虑使用外部数据库