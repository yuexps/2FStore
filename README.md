# 2FStore

<p align="center">
  <strong>为 FNOS 生态打造的第三方中心化应用仓库</strong>
</p>

<p align="center">
  开发者可通过 Issue 或 Pull Request 提交应用，用户可便捷浏览与下载各类应用
</p>

> ⚠️ **注意**：项目仍在开发中，欢迎一起完善！
主要作用：维护app_details和fnpack_details两个元数据文件

---

## 🌟 功能特点

- 🔍 应用搜索和分类浏览
- 🔄 应用信息自动从 GitHub 仓库获取
- ⏰ 每日自动更新应用元数据
- ⬇️ 一键下载 `.fpk` 安装包
- 🔗 兼容 [FnDepot](https://github.com/EWEDLCM/FnDepot) 应用源

---

## 📂 项目结构

```
2FStore/
├── apps.json                 # 应用索引（开发者提交的应用列表）
├── fnpacks.json              # FnDepot 仓库索引（兼容第三方应用源）
├── data/
│   └── app_details.json      # 应用详细元数据（自动生成）
│   └── fnpack_details.json   # FnDepot 应用详细元数据（自动生成）
├── scripts/                  # 自动化脚本
└── web/                      # 前端页面
```

---

## 🚀 如何提交应用

开发者可以通过以下方式提交应用到仓库：

### 方式一：通过 Issue 提交（推荐）

1. 点击仓库中的 [Issues](https://github.com/yuexps/2FStore/issues) 标签
2. 点击 **New issue** 按钮
3. 选择 **应用提交** 模板
4. 填写应用信息（应用ID、应用名称、GitHub仓库URL）
5. 提交 Issue，系统将自动验证并更新元数据

### 方式二：通过 Pull Request 提交

1. Fork 本仓库
2. 在 [`apps.json`](https://github.com/yuexps/2FStore/blob/main/apps.json) 文件的 `apps` 数组中添加你的应用信息：

```json
{
  "id": "your-app-id",
  "name": "你的应用名称",
  "repository": "https://github.com/user/your-repo"
}
```

| 字段 | 说明 | 要求 |
|------|------|------|
| `id` | 应用唯一标识 | 仅限小写字母、数字和连字符 `-` |
| `name` | 应用显示名称 | 最多 100 个字符 |
| `repository` | GitHub 仓库地址 | 必须是有效的 GitHub 仓库 URL |

3. 创建 Pull Request 到 `main` 分支
4. 等待审核合并

---

## 📦 应用仓库规范

你的应用仓库需要符合 fnOS 应用规范，系统会自动从仓库获取以下信息：

| 信息 | 来源 | 说明 |
|------|------|------|
| 应用描述 | `manifest` 的 `desc` 字段 / 仓库描述 | 优先读取 manifest |
| 版本号 | `manifest` 的 `version` 字段 / Release tag | 优先读取 manifest |
| 应用图标 | `ICON_256.PNG` / `ICON.PNG` | 推荐 256x256 PNG 格式 |
| 下载链接 | GitHub Release 中的 `.fpk` 文件 | 必须发布 Release |
| 作者信息 | 仓库 owner | 自动获取 |
| 星标/分支数 | GitHub API | 自动获取 |
| 应用分类 | `manifest` / 智能分类 | 支持自动分类 |

### 建议的仓库结构

```
your-app-repo/
├── ICON.PNG              # 应用图标（必须大写，建议 256x256）
├── ICON_256.PNG          # 高清图标（可选，优先使用）
├── manifest              # fnOS 应用清单文件（必须）
├── README.md             # 应用说明
├── app/                  # 应用程序文件
├── cmd/                  # 启动脚本
├── config/               # 配置文件
└── wizard/               # 安装向导
```

### manifest 文件示例

```ini
appname=myapp
version=1.0.0
display_name=我的应用
desc=这是一个示例应用
arch=x86_64
source=thirdparty
maintainer=开发者名称
maintainer_url=https://github.com/username
os_min_version=0.9.0
service_port=8080
```

📖 详细规范请参考：[fnOS 开发文档 - Manifest](https://developer.fnnas.com/docs/core-concepts/manifest)

📂 示例仓库：[v2raya-fnos](https://github.com/yuexps/v2raya-fnos)

---

## 🔗 兼容 FnDepot 应用源

2FStore 兼容 [FnDepot](https://github.com/EWEDLCM/FnDepot) 去中心化应用源规范。

### 如何添加你的 FnDepot 仓库

通过提交 PR 在 [`fnpacks.json`](https://github.com/yuexps/2FStore/blob/main/fnpacks.json) 文件的 `fnpacks` 数组中添加你的仓库信息：

```json
{
  "key": "你的GitHub用户名",
  "repo": "https://github.com/你的用户名/FnDepot"
}
```

### FnDepot 仓库要求

| 要求 | 说明 |
|------|------|
| 仓库名称 | 必须为 `FnDepot`（大小写敏感） |
| 可见性 | 必须为 Public |
| 索引文件 | 根目录必须包含 `fnpack.json` |

### FnDepot 目录结构

```
FnDepot/
├── fnpack.json           # 全局元数据索引文件
├── {app_name}/           # 应用目录
│   ├── ICON.PNG          # 应用图标（必须大写）
│   ├── {app_name}.fpk    # 安装包
│   ├── README.md         # 应用说明
│   └── Preview/          # 预览图目录
└── ...
```

📖 FnDepot 规范文档：[FnDepot README](https://github.com/EWEDLCM/FnDepot)

---

## ⚙️ 自动化流程

本项目使用 GitHub Actions 实现以下自动化：

| 触发条件 | 操作 |
|----------|------|
| Issue 提交（应用提交模板） | 自动验证应用信息并更新 `apps.json` |
| PR 合并到 main | 自动验证应用格式 |
| 每日定时（北京时间 00:00） | 批量更新所有应用元数据 |
| `apps.json` 变更 | 触发元数据更新 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

- 🐛 发现问题？[提交 Issue](https://github.com/yuexps/2FStore/issues/new)
- 💡 有新想法？欢迎讨论
- 📦 提交应用？按照上述指南操作

---

## 📄 许可证

本项目采用 MIT 许可证。