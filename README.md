# Hydra - The Polymorphic SEO Ecosystem

商业级"灰帽"静态站点生成器，能够模拟高质量、多角色网站生态系统。

## 特性

- 🔄 混合 LLM 支持（本地/云端）
- 🎭 语义伪装（Context Masking）
- 🎨 视觉变异（Tailwind CSS）
- 🌐 高级域名拓扑（通配符/复合站点）

## 技术栈

- Python 3.10+
- SQLAlchemy (SQLite/PostgreSQL)
- Jinja2 + Tailwind CSS
- 异步架构

## 快速开始

```bash
pip install -r requirements.txt
python hydra.py --config config.yaml
```

## Web 管理面板

启动 Hydra Command Center（Web 管理界面）：

```bash
python start_admin.py
# 或
start_admin.bat
```

然后访问：http://localhost:8000

## 项目结构

```
hydra/
├── core/           # 核心组件
├── interfaces/     # 抽象接口
├── plugins/        # 插件实现
├── modules/        # 业务逻辑
└── dist/           # 输出目录
```

