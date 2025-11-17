# Let's Talk 部署指南

## 部署方式概览

Let's Talk 支持多种部署方式，适应不同的环境需求：

1. **开发环境部署** - 本地开发和测试
2. **生产环境部署** - 服务器直接部署
3. **云服务部署** - 云平台部署

## 开发环境部署

### 系统要求

- Python 3.6+
- pip
- 至少 512MB 内存
- 至少 1GB 磁盘空间

### 快速部署

```bash
# 1. 克隆代码
git clone <repository-url>
cd letstalk

# 2. 自动环境配置
./scripts/setup.sh

# 3. 配置环境变量
nano .env

# 4. 启动应用
./scripts/run.sh
```

### 手动部署

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
cp .env.example .env
nano .env  # 配置API密钥

# 4. 启动应用
python3 main.py
```

## 生产环境部署

### 系统要求

- Linux服务器 (Ubuntu 18.04+ / CentOS 7+)
- Python 3.6+
- Nginx (推荐)
- 至少 1GB 内存
- 至少 2GB 磁盘空间

### 1. 服务器准备

```bash
# Ubuntu
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx git

# CentOS
sudo yum update
sudo yum install python3 python3-pip git nginx
```

### 2. 应用部署

```bash
# 创建应用目录
sudo mkdir -p /opt/letstalk
sudo chown $USER:$USER /opt/letstalk

# 部署代码
cd /opt/letstalk
git clone <repository-url> .

# 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境
cp .env.example .env
nano .env  # 配置生产环境参数
```

### 3. 系统服务配置

创建 systemd 服务文件：

```bash
sudo nano /etc/systemd/system/letstalk.service
```

```ini
[Unit]
Description=Let's Talk Multi-Subject Agent
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/letstalk
Environment=PATH=/opt/letstalk/venv/bin
ExecStart=/opt/letstalk/venv/bin/python main.py --host 127.0.0.1 --port 5002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable letstalk
sudo systemctl start letstalk
sudo systemctl status letstalk
```

### 4. Nginx反向代理配置

```bash
sudo nano /etc/nginx/sites-available/letstalk
```

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名
    
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 健康检查端点
    location /health {
        proxy_pass http://127.0.0.1:5002/health;
        access_log off;
    }
    
    # 静态文件缓存
    location /static {
        proxy_pass http://127.0.0.1:5002/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/letstalk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL证书配置（可选）

使用Let's Encrypt免费SSL证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 云服务部署

### AWS部署

#### EC2部署

1. 创建EC2实例（推荐t3.small或更高配置）
2. 配置安全组开放80/443端口
3. 按照生产环境部署步骤操作

### 腾讯云部署

#### CVM部署

1. 购买CVM实例
2. 配置安全组
3. 按照生产环境部署步骤操作
        - containerPort: 5002
        env:
        - name: FLASK_ENV
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5002
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: letstalk-service
spec:
  selector:
    app: letstalk
  ports:
  - port: 80
    targetPort: 5002
  type: LoadBalancer
```

## 监控和日志

### 应用监控

```bash
# 使用内置监控脚本
python3 scripts/monitor.py

# 持续监控
python3 scripts/monitor.py --continuous --interval 60
```

### 日志管理

应用日志位置：
- 主日志：`logs/letstalk.log`
- 错误日志：`logs/error.log`
- LLM日志：`logs/llm.log`

日志轮转配置已内置，每个日志文件最大10MB，保留5个备份。

### 健康检查

应用提供健康检查端点：
- URL: `/health`
- 返回格式: JSON
- 状态码: 200 (健康) / 500 (异常)

## 性能优化

### 应用层优化

1. **启用生产模式**：
   ```bash
   export FLASK_ENV=production
   export FLASK_DEBUG=False
   ```

2. **调整工作进程**：
   使用Gunicorn替代开发服务器：
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5002 app:app
   ```

3. **缓存配置**：
   - 启用Redis缓存（可选）
   - 配置静态文件缓存

### 系统层优化

1. **内存优化**：
   - 调整Python垃圾回收
   - 监控内存使用

2. **网络优化**：
   - 启用gzip压缩
   - 配置CDN（可选）

## 故障排除

### 常见问题

1. **端口被占用**：
   ```bash
   sudo lsof -i :5002
   sudo kill -9 <PID>
   ```

2. **权限问题**：
   ```bash
   sudo chown -R www-data:www-data /opt/letstalk
   sudo chmod +x scripts/*.sh
   ```

3. **依赖问题**：
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **LLM API问题**：
   - 检查API密钥
   - 验证网络连接
   - 查看LLM日志

### 检查清单

部署前检查：
- [ ] Python版本 >= 3.6
- [ ] 所有依赖已安装
- [ ] 环境变量已配置
- [ ] 端口未被占用
- [ ] 防火墙规则正确
- [ ] SSL证书有效（如使用HTTPS）

部署后验证：
- [ ] 应用正常启动
- [ ] 健康检查通过
- [ ] API响应正常
- [ ] 日志记录正常
- [ ] 监控指标正常

## 安全注意事项

1. **API密钥安全**：
   - 使用环境变量存储
   - 定期轮换密钥
   - 限制API访问权限

2. **网络安全**：
   - 配置防火墙
   - 使用HTTPS
   - 限制管理端口访问

3. **应用安全**：
   - 定期更新依赖
   - 监控安全漏洞
   - 配置访问控制

4. **数据安全**：
   - 加密敏感数据
   - 定期备份
   - 监控数据访问