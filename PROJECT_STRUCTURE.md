# Hydra 项目结构说明

## 目录结构

```
hydra/
├── core/                    # 核心组件
│   ├── __init__.py
│   ├── logger.py           # 日志管理器
│   ├── config_loader.py    # 配置加载器
│   └── pipeline.py         # 管道管理器
│
├── interfaces/             # 抽象接口定义
│   ├── __init__.py
│   ├── llm_provider.py     # LLM 提供者接口
│   ├── content_strategy.py # 内容策略接口
│   ├── template_renderer.py # 模板渲染器接口
│   └── domain_dispatcher.py # 域名分发器接口
│
├── plugins/                # 插件实现
│   ├── llm/               # LLM 插件
│   │   ├── __init__.py
│   │   ├── ollama_provider.py    # Ollama 本地 LLM
│   │   ├── openai_provider.py    # OpenAI API
│   │   └── factory.py            # LLM 工厂
│   │
│   ├── templates/         # 模板插件
│   │   ├── __init__.py
│   │   └── jinja_renderer.py    # Jinja2 渲染器
│   │
│   └── domain/            # 域名插件
│       ├── __init__.py
│       └── domain_dispatcher.py  # 域名分发器实现
│
├── modules/                # 业务逻辑模块
│   ├── mimicry/           # 模仿内容引擎
│   │   ├── __init__.py
│   │   ├── prompt_builder.py     # 提示词构建器
│   │   └── content_strategy.py   # 内容策略实现
│   │
│   ├── seo/               # SEO 功能
│   │   ├── __init__.py
│   │   ├── link_mesh.py          # 链接网络
│   │   ├── traffic_filter.py     # 流量过滤器
│   │   ├── seo_data_builder.py   # SEO 数据构建器
│   │   └── nginx_generator.py    # Nginx 配置生成器
│   │
│   ├── content/           # 内容处理
│   │   ├── __init__.py
│   │   └── markdown_converter.py # Markdown 转换器
│   │
│   └── topology/          # 域名拓扑
│       └── __init__.py
│
├── templates/             # Jinja2 模板
│   ├── base.html         # 基础模板
│   └── article.html      # 文章模板
│
├── hydra.py              # 主入口文件
├── config.yaml.example  # 配置文件模板
├── requirements.txt     # Python 依赖
├── setup.py            # 安装脚本
├── README.md           # 项目说明
├── QUICKSTART.md       # 快速开始指南
└── PROJECT_STRUCTURE.md # 本文件
```

## 核心功能模块

### 1. 核心架构 (core/)
- **Logger**: 统一的日志管理系统
- **ConfigLoader**: YAML 配置加载和解析
- **Pipeline**: 异步处理管道管理器

### 2. 接口层 (interfaces/)
定义了所有核心接口，支持插件化架构：
- `LLMProvider`: LLM 提供者接口
- `ContentStrategy`: 内容生成策略接口
- `TemplateRenderer`: 模板渲染接口
- `DomainDispatcher`: 域名分发接口

### 3. LLM 引擎 (plugins/llm/)
- **OllamaProvider**: 本地 Ollama 服务支持
- **OpenAIProvider**: OpenAI API 支持
- **LLMFactory**: 根据配置自动选择 LLM 提供者

### 4. 模仿内容引擎 (modules/mimicry/)
- **PromptBuilder**: 构建包含 Context Masking 的提示词
- **MimicryContentStrategy**: 实现语义伪装的内容生成

### 5. 模板系统 (plugins/templates/)
- **JinjaRenderer**: Jinja2 模板渲染器
- 支持 SEO 数据注入（JSON-LD）
- 响应式设计（Tailwind CSS）

### 6. 域名拓扑 (plugins/domain/)
- **HydraDomainDispatcher**: 处理多域名/子域名路由
- 支持 Composite Mode 和 Swarm Mode
- 自动生成文件组织结构

### 7. SEO 功能 (modules/seo/)
- **LinkMesh**: 上下文内部链接网络
- **TrafficFilter**: 404 重定向处理
- **SEODataBuilder**: 生成结构化数据（JSON-LD）
- **NginxGenerator**: 自动生成 Nginx 配置

## 工作流程

1. **初始化**: 加载配置，初始化所有组件
2. **健康检查**: 验证 LLM 服务可用性
3. **内容生成**: 
   - 规划大纲
   - 使用 Context Masking 生成内容
   - 转换为 HTML
4. **页面渲染**: 使用 Jinja2 模板渲染页面
5. **SEO 优化**: 注入结构化数据，生成内部链接
6. **文件输出**: 按域名组织输出到 dist/ 目录
7. **Nginx 配置**: 生成服务器配置文件

## 扩展性

项目采用插件化架构，易于扩展：

- **添加新的 LLM 提供者**: 实现 `LLMProvider` 接口
- **添加新的内容策略**: 实现 `ContentStrategy` 接口
- **自定义模板**: 在 `templates/` 目录添加新模板
- **扩展 SEO 功能**: 在 `modules/seo/` 添加新模块

## 技术栈

- **Python 3.10+**: 核心语言
- **Jinja2**: 模板引擎
- **Tailwind CSS**: 样式框架（CDN）
- **Markdown**: 内容格式
- **SQLAlchemy**: ORM（预留，当前未使用）
- **httpx**: 异步 HTTP 客户端
- **PyYAML**: 配置文件解析

