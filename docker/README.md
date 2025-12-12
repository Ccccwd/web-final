# Docker 配置说明

## 快速启动

### 1. 启动数据库服务
```bash
cd docker
docker-compose up -d mysql redis
```

### 2. 启动完整开发环境(包含前后端)
```bash
cd docker
docker-compose --profile dev up -d
```

### 3. 查看服务状态
```bash
docker-compose ps
```

### 4. 查看日志
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs mysql
docker-compose logs backend
docker-compose logs frontend
```

### 5. 停止服务
```bash
docker-compose down
```

### 6. 停止服务并删除数据卷
```bash
docker-compose down -v
```

## 服务说明

### MySQL (端口: 3306)
- 数据库: finance_system
- 用户名: finance_user
- 密码: finance_password
- Root密码: root123456

### Redis (端口: 6379)
- 无密码认证

### 后端服务 (端口: 8000)
- FastAPI应用
- 自动重载开发模式
- API文档: http://localhost:8000/docs

### 前端服务 (端口: 3000)
- Vue3应用
- 开发模式自动重载

## 数据持久化

- MySQL数据存储在 `mysql_data` 卷中
- Redis数据存储在 `redis_data` 卷中

## 生产环境部署

生产环境请修改以下配置：
1. 更改默认密码
2. 使用强密码的JWT密钥
3. 配置SSL证书
4. 设置合适的资源限制
5. 添加日志轮转配置

## 故障排除

### 数据库连接失败
1. 检查MySQL容器是否正常启动
2. 确认端口3306未被占用
3. 查看MySQL容器日志

### Redis连接失败
1. 检查Redis容器状态
2. 确认端口6379未被占用

### 前端无法访问后端
1. 检查后端服务是否正常启动
2. 确认CORS配置正确
3. 查看网络连接状态