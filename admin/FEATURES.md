# Hydra 后台管理功能清单

## 📊 仪表盘 (Dashboard) - `/`
- ✅ 系统状态监控（引擎状态、LLM健康、生成状态）
- ✅ 统计数据展示（总文章数、总站点数、活跃站点、今日生成）
- ✅ 一键生成站点功能
- ✅ 实时状态刷新

## 🌐 站点管理 (Sites) - `/sites`
- ✅ 查看所有站点列表
- ✅ 添加新站点
- ✅ 编辑站点信息
- ✅ 删除站点
- ✅ 搜索站点功能

## ⚡ 内容生产工厂 (Generator) - `/generator`

### 单篇精修模式
- ✅ 输入文章标题
- ✅ 输入关键词
- ✅ 选择目标站点
- ✅ 实时预览生成结果
- ✅ 自动保存到站点

### 批量站群模式
- ✅ 批量添加关键词任务
- ✅ 选择目标站点
- ✅ 设置生成语调
- ✅ 查看任务队列
- ✅ 启动批量生成
- ✅ 清空已完成任务

## 🎨 AI 模板引擎 (Templates) - `/templates`
- ✅ 查看模板库
- ✅ 生成模板变体
- ✅ 模板指纹管理
- ✅ 比较模板相似度
- ✅ 代码混淆功能

## ⚙️ 系统设置 (Settings) - `/settings`
- ✅ 项目信息配置
- ✅ LLM 配置（Ollama/OpenAI）
- ✅ 输出配置
- ✅ 默认内容策略
- ✅ 域名拓扑配置（Composite Mode）
- ✅ Swarm Mode 配置
- ✅ SEO 配置
- ✅ Cloudflare 配置
- ✅ 日志配置

## 📜 运行日志 (Logs) - `/logs`
- ✅ 实时日志查看
- ✅ WebSocket 日志流
- ✅ 日志清空功能

## 🔌 API 端点

### 站点管理 API
- `GET /api/sites` - 获取站点列表
- `POST /api/sites` - 添加新站点
- `GET /api/sites/{id}` - 获取单个站点
- `PUT /api/sites/{id}` - 更新站点
- `DELETE /api/sites/{id}` - 删除站点

### 内容生成 API
- `POST /api/generator/single` - 单篇内容生成
- `POST /api/generator/batch` - 添加批量任务
- `POST /api/generator/start` - 启动批量生成
- `GET /api/generator/queue` - 获取队列状态
- `POST /api/generator/queue/clear` - 清空已完成任务

### 模板混淆 API
- `POST /api/templates/generate` - 生成模板变体
- `POST /api/templates/compare` - 比较模板相似度

### 系统 API
- `GET /api/stats` - 获取统计数据
- `GET /status` - 获取系统状态
- `POST /settings/update` - 更新配置
- `POST /toggle/{path}` - 切换功能开关

## 🔐 认证
- HTTP Basic Authentication
- 默认用户名: `admin`
- 默认密码: `hydra`
- 可通过环境变量 `ADMIN_USER` 和 `ADMIN_PASS` 修改

## 📝 使用说明

1. **访问后台**: 打开浏览器访问 `http://localhost:8000`
2. **登录**: 使用默认账号密码登录（admin/hydra）
3. **添加站点**: 在"站点管理"页面添加第一个站点
4. **生成内容**: 在"内容生产工厂"页面生成单篇或批量内容
5. **查看统计**: 在"仪表盘"查看系统统计和状态

## ⚠️ 注意事项

- 首次使用需要先添加站点才能生成内容
- 确保 LLM 服务（Ollama 或 OpenAI）已配置并可用
- 批量生成会消耗较多资源，建议分批处理

