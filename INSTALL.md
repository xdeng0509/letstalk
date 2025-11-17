# Let's Talk 安装指南

## 环境要求

- Python 3.6+ 
- pip (Python包管理器)

## 快速安装

### 1. 使用自动化脚本（推荐）

```bash
# 给脚本执行权限
chmod +x scripts/setup.sh

# 运行安装脚本
./scripts/setup.sh
```

### 2. 手动安装

```bash
# 1. 创建虚拟环境（可选但推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. 安装依赖
python3 -m pip install -r requirements.txt

# 3. 复制环境配置文件
cp .env.example .env

# 4. 编辑环境配置（可选）
nano .env  # 或使用其他编辑器
```

## 配置说明

### 基本配置

项目可以在三种模式下运行：

1. **演示模式**（默认）：使用预设回答，无需API配置
2. **LLM模式**：使用真实的LLM API
3. **LLM专用模式**：强制使用LLM，禁止回退到演示模式

### LLM API 配置

编辑 `.env` 文件，选择并配置你的LLM提供方：

#### OpenAI 配置
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

#### Google Gemini 配置  
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

#### 腾讯慧言配置
```bash
LLM_PROVIDER=huiyuan
HUIYUAN_API_KEY=your_api_key_here
HUIYUAN_BASE_URL=https://api.hunyuan.tencentcloudapi.com
HUIYUAN_MODEL=hunyuan-lite
```

## 启动应用

### 使用脚本启动
```bash
./scripts/run.sh
```

### 直接启动
```bash
python3 main.py
```

### 启动参数
```bash
# 指定端口
python3 main.py --port 8080

# 强制LLM模式
python3 main.py --llm-only

# 开启调试模式
python3 main.py --debug
```

## 访问应用

启动成功后，在浏览器中访问：

- 产品介绍页：http://localhost:5002/
- 对话界面：http://localhost:5002/chat

## 故障排除

### 1. 依赖安装失败

```bash
# 升级pip
python3 -m pip install --upgrade pip

# 使用清华源安装（国内用户）
python3 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 2. 端口被占用

```bash
# 使用其他端口
python3 main.py --port 8080
```

### 3. LLM API调用失败

- 检查API密钥是否正确
- 检查网络连接
- 可以先在演示模式下测试功能

### 4. 检查环境配置

```bash
python3 scripts/check_env.py
```

## 开发模式

如果你想参与开发：

```bash
# 安装开发依赖
python3 -m pip install -r requirements.txt

# 启动开发服务器
python3 main.py --debug

# 运行测试
python3 scripts/check_env.py
```