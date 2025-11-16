# Let's Talk - 多学科视角Agent

以「一个问题，N 种视角」为核心，用多学科思维拆解问题，通过互动式引导让用户感受跨学科魅力。

## 功能特性

- 🎁 **学科盲盒开局**：随机解锁3个学科视角（冷门+热门组合）
- ⚔️ **视角PK互动**：两个学科辩论式解答，用户投票
- 🎮 **知识点小游戏**：游戏化学习，加深理解
- 🔗 **跨学科串联**：用生活场景类比串联不同学科
- 💬 **反向提问**：双向对话，引导深度思考

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件：

```bash
OPENAI_API_KEY=your_api_key_here
```

### 运行

```bash
python main.py
```

## 项目结构

```
letstalk/
├── main.py                 # 主程序入口
├── agents/                 # Agent相关代码
│   ├── __init__.py
│   ├── subject_agent.py   # 学科Agent
│   └── subject_library.py # 学科库
├── utils/                  # 工具函数
│   ├── __init__.py
│   └── llm_client.py      # LLM客户端
└── config/                 # 配置文件
    └── subjects.json      # 学科配置
```

## MVP开发进度

- [x] 项目初始化
- [x] 学科盲盒开局功能
- [ ] Agent简单一句话回答
- [ ] 互动引导功能
- [ ] 视角PK功能
- [ ] 其他功能...

