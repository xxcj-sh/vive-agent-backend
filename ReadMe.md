# VMatch Backend

VMatch是一个基于FastAPI的后端服务，为微信小程序提供匹配功能。

## 功能特点

- 用户管理：注册、查询、更新和删除用户
- 匹配管理：创建、查询、更新和删除匹配记录
- 数据库支持：支持SQLite（开发环境）和MySQL（生产环境）

## 环境要求

- Python 3.7+
- FastAPI
- SQLAlchemy
- 数据库：SQLite（开发）或MySQL（生产）

## 安装

1. 克隆仓库
```bash
git clone <repository-url>
cd vmatch-backend
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，设置环境变量
```

## 数据库配置

### SQLite（开发环境默认）

无需额外配置，项目默认使用SQLite数据库。

### MySQL配置

1. 确保MySQL服务已启动
2. 在.env文件中配置MySQL连接：
```bash
ENVIRONMENT=production
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=vmatch
MYSQL_USERNAME=root
MYSQL_PASSWORD=your_password
```

3. 初始化MySQL数据库：
```bash
cd scripts
python init_mysql_database.py
```

4. 测试MySQL连接：
```bash
python init_mysql_database.py --test
```

### 线上服务器配置

参考 `/Users/liukun/Documents/workspace/codebase/VMatch/vmatch-dev-reference/database-config.md` 中的配置：

```bash
ENVIRONMENT=production
MYSQL_HOST=rm-uf672o44x147i9c2p9o.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_DATABASE=vmatch
MYSQL_USERNAME=your_username
MYSQL_PASSWORD=your_password
```

## 运行

### 开发环境（SQLite）
```bash
uvicorn app.main:app --reload
```

### 生产环境（MySQL）
```bash
ENVIRONMENT=production uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看API文档。

## 数据库初始化脚本

### SQLite初始化
```bash
cd scripts
python init_database.py
```

### MySQL初始化
```bash
cd scripts
python init_mysql_database.py
```

### 重置数据库
```bash
# SQLite
python init_database.py --reset --force

# MySQL
python init_mysql_database.py --reset --force
```

## 数据库迁移

项目支持自动数据库切换：

- 开发环境（ENVIRONMENT=development）：自动使用SQLite
- 生产环境（ENVIRONMENT=production）：自动使用MySQL
- 也可通过DATABASE_URL环境变量强制指定数据库连接

## 云服务部署

本项目设计支持云服务部署，配置相应的环境变量：

1. 设置ENVIRONMENT=production
2. 配置MySQL连接参数
3. 设置其他必要的环境变量（如SECRET_KEY）

## API文档

启动服务后，访问以下URL查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

运行测试套件：
```bash
pytest tests/
```

测试数据库连接：
```bash
python scripts/init_mysql_database.py --test
```