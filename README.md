# Let's Talk - 多学科视角Agent

以「一个问题，N 种视角」为核心，用多学科思维拆解问题，通过互动式引导让用户感受跨学科魅力。

## 功能特性

- 🎁 **学科盲盒开局**：随机解锁3个学科视角（冷门+热门组合）
- ⚔️ **视角PK互动**：两个学科辩论式解答，用户投票
- 🎮 **知识点小游戏**：游戏化学习，加深理解
- 🔗 **跨学科串联**：用生活场景类比串联不同学科
- 💬 **反向提问**：双向对话，引导深度思考

## 快速开始

### 方式一：自动配置（推荐）

```bash
# 运行环境配置脚本
chmod +x scripts/setup.sh
./scripts/setup.sh

# 编辑环境配置文件
nano .env

# 启动应用
./scripts/run.sh
```

### 方式二：手动配置

#### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置环境变量

复制并编辑环境配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置你的 LLM API：

```bash
# 选择 LLM 提供方：openai | gemini | huiyuan
LLM_PROVIDER=openai

# OpenAI 配置
OPENAI_API_KEY=sk-your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# 或者使用 Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

#### 3. 运行应用

```bash
# 基本启动
python main.py

# 指定端口
python main.py --port 8080

# 强制LLM模式（禁止演示）
python main.py --llm-only

# 开启调试模式
python main.py --debug
```

## 项目结构

```
letstalk/
├── main.py                 # 主程序入口
├── app.py                  # Flask Web应用
├── agents/                 # Agent相关代码
│   ├── __init__.py
│   ├── subject_agent.py   # 学科Agent
│   └── subject_library.py # 学科库
├── utils/                  # 工具函数
│   ├── __init__.py
│   └── llm_client.py      # LLM客户端
├── config/                 # 配置文件
│   ├── subjects.json      # 学科配置
│   └── logging.py         # 日志配置
├── templates/              # Web模板
│   ├── index.html         # 对话界面
│   └── landing.html       # 产品首页
├── scripts/                # 脚本文件
│   ├── setup.sh           # 环境配置脚本
│   ├── run.sh             # 快速启动脚本
│   ├── check_env.py       # 环境检查脚本
│   └── monitor.py         # 系统监控脚本
├── .env                    # 环境变量配置
├── .env.example           # 环境变量示例
├── INSTALL.md             # 安装指南
├── DEPLOYMENT.md          # 部署指南
└── requirements.txt       # Python依赖
```

## 环境配置说明

### LLM 提供方支持

- **OpenAI**: 支持 GPT-3.5/GPT-4 系列模型
- **Google Gemini**: 支持 Gemini 1.5 系列模型  
- **腾讯慧言**: 支持混元系列模型

### 运行模式

1. **演示模式** (默认): 使用预设回答，无需API配置
2. **LLM模式**: 使用真实LLM API生成回答
3. **LLM专用模式**: 强制使用LLM，禁止回退到演示模式

### 环境变量说明

| 变量名 | 说明 | 示例值 |
|-------|------|--------|
| `LLM_PROVIDER` | LLM提供方 | `openai` / `gemini` / `huiyuan` |
| `OPENAI_API_KEY` | OpenAI API密钥 | `sk-...` |
| `OPENAI_MODEL` | OpenAI模型名称 | `gpt-3.5-turbo` |
| `GEMINI_API_KEY` | Gemini API密钥 | `AI...` |
| `GEMINI_MODEL` | Gemini模型名称 | `gemini-1.5-flash` |
| `HUIYUAN_API_KEY` | 慧言API密钥 | `your_key` |
| `HUIYUAN_BASE_URL` | 慧言API地址 | `https://api.hunyuan...` |
| `LLM_ONLY` | 强制LLM模式 | `true` / `false` |

## 系统监控与运维

### 健康检查

```bash
# 检查应用健康状态
curl http://localhost:5002/health

# 检查系统状态
curl http://localhost:5002/erra-api/status
```

### 系统监控

```bash
# 一次性监控检查
python3 scripts/monitor.py

# 持续监控（每60秒检查一次）
python3 scripts/monitor.py --continuous --interval 60

# 监控远程服务器
python3 scripts/monitor.py --url http://your-server.com
```

### 日志管理

应用日志自动保存在 `logs/` 目录：
- `letstalk.log` - 主应用日志
- `error.log` - 错误日志
- `llm.log` - LLM调用日志

## MVP开发进度

- [x] 项目初始化
- [x] 环境配置完善
- [x] 学科盲盒开局功能
- [x] Agent简单一句话回答
- [x] Web界面开发
- [x] 深入单聊功能
- [x] 视角PK功能
- [x] 日志系统
- [x] 监控系统
- [x] 部署文档
- [ ] 知识点小游戏
- [ ] 跨学科串联
- [ ] 其他功能...

