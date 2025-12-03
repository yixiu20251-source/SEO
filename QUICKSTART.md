# Hydra 快速开始指南

## 安装

1. 安装 Python 3.10 或更高版本
2. 安装依赖：

```bash
pip install -r requirements.txt
```

## 配置

1. 复制配置文件模板：

```bash
cp config.yaml.example config.yaml
```

2. 编辑 `config.yaml`，配置以下内容：

- **LLM 提供者**：选择 `ollama`（本地）或 `openai`（云端）
  - Ollama：确保本地运行 Ollama 服务（默认端口 11434）
  - OpenAI：设置 `OPENAI_API_KEY` 环境变量或在配置文件中提供 API Key

- **域名拓扑**：配置你的域名结构
  - Composite Mode：配置多个子域名（如 example.com, docs.example.com）
  - Swarm Mode：提供关键词列表，自动生成 keyword.example.com

## 使用

### 基本使用

```bash
python hydra.py --config config.yaml
```

### 健康检查

```bash
python hydra.py --config config.yaml --health-check
```

## 输出

生成的文件将保存在 `dist/` 目录下，按主机名组织：

```
dist/
├── example.com/
│   └── index.html
├── docs.example.com/
│   └── index.html
└── blog.example.com/
    └── index.html
```

## Nginx 配置

Hydra 会自动生成 `nginx.conf` 文件，包含：

- HTTPS 配置（需要 SSL 证书）
- 通配符域名支持（Swarm Mode）
- 404 重定向处理
- Gzip 压缩
- 安全头设置

## 模板自定义

编辑 `templates/` 目录下的模板文件：

- `base.html`：基础模板
- `article.html`：文章页面模板

## Context Masking 说明

Context Masking 是 Hydra 的核心功能，用于将目标关键词伪装在合法的上下文中：

1. **Target Keyword**：实际要优化的关键词（如 "Game Server"）
2. **Mask Context**：伪装上下文（如 "Industrial Machinery"）
3. **Persona**：人物角色（如 "Senior Engineer"）

LLM 会被指示在 Mask Context 领域内撰写内容，同时将 Target Keyword 作为产品型号、技术术语或隐喻自然地融入内容中。

## 注意事项

- 确保 LLM 服务可用（Ollama 或 OpenAI API）
- 生成的内容需要人工审核
- SSL 证书需要单独配置（可使用 Let's Encrypt）
- 遵守相关法律法规和搜索引擎政策

