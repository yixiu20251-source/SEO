# GitHub 推送指南

## 前提条件

1. **安装 Git**
   - 下载地址：https://git-scm.com/download/win
   - 安装后重启终端或重新加载环境变量

2. **配置 Git**（首次使用）
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

## 推送步骤

### 方法一：使用命令行（推荐）

1. **初始化 Git 仓库**
   ```bash
   git init
   ```

2. **添加所有文件**
   ```bash
   git add .
   ```

3. **创建初始提交**
   ```bash
   git commit -m "Initial commit: Hydra SEO Ecosystem"
   ```

4. **在 GitHub 上创建新仓库**
   - 访问 https://github.com/new
   - 输入仓库名称（如：hydra-seo）
   - **不要**初始化 README、.gitignore 或 license（我们已经有了）
   - 点击 "Create repository"

5. **添加远程仓库并推送**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/hydra-seo.git
   git branch -M main
   git push -u origin main
   ```

### 方法二：使用 GitHub Desktop

1. 下载并安装 GitHub Desktop：https://desktop.github.com/
2. 打开 GitHub Desktop
3. 选择 File > Add Local Repository
4. 选择项目目录
5. 填写提交信息并提交
6. 点击 Publish repository 推送到 GitHub

### 方法三：使用 VS Code

1. 在 VS Code 中打开项目
2. 点击左侧源代码管理图标（或按 Ctrl+Shift+G）
3. 点击 "Initialize Repository"
4. 暂存所有更改（点击 + 号）
5. 输入提交信息并提交
6. 点击 "..." 菜单 > "Publish to GitHub"

## 后续更新

推送新更改：
```bash
git add .
git commit -m "描述你的更改"
git push
```

## 注意事项

- 确保 `.gitignore` 已正确配置，避免提交敏感信息
- 不要提交 `config.yaml`（包含 API 密钥），只提交 `config.yaml.example`
- 如果使用 SSH，将 `https://` 替换为 `git@github.com:`

