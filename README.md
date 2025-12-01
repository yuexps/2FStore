# 2FStore

为 FNOS 生态创建的第三方中心化应用仓库。开发者可通过 Pull Request 提交应用，用户可便捷浏览与下载各类应用。

> 本仓库的核心作用是维护 `app_details` 和 `fnpack_details` 两个元数据文件。

> ⚠️ **注意**：项目仍在开发中，欢迎一起完善！摸鱼~

## 🌟 功能特点

- 应用搜索和分类浏览
- 应用信息自动从 GitHub 仓库获取
- 自动更新应用信息
- 快速下载应用

## 🚀 如何提交应用

开发者可以通过以下方式提交应用到仓库：

### 1. 通过 Issues 提交（推荐）

1. 点击仓库中的"Issues"标签
2. 点击"New issue"按钮
3. 选择"应用提交"模板
4. 填写应用信息（应用ID、应用名称、GitHub仓库URL）
5. 提交 Issue，系统将自动处理并更新元数据

### 2. 通过 Pull Request 提交

1. Fork 本仓库
2. 在项目根目录的 [apps.json](https://github.com/yuexps/2FStore/apps.json) 文件的 `apps` 数组中添加你的应用信息，示例如下：

```json
{
    "id": "your-app-id", // 应用ID，必须唯一
    "name": "你的应用名称", // 应用名称，随便取
    "repository": "https://github.com/user/your-repo" // 应用GitHub仓库URL
}
```

3. 创建 Pull Request 到主分支
4. 等待合并

## 📦 应用信息获取

系统会自动从 GitHub 仓库获取以下信息：

- 应用描述
- 作者信息
- 星标数和分支数
- 最后更新时间
- 最新版本
- 下载链接（从 GitHub Release 获取）
- 应用图标
- 应用分类（自动完成）

## 📁 应用仓库结构

### 建议包含的文件

```
app_id/
├── ICON.PNG
├── manifest
└── README.md
```

示例仓库：https://github.com/yuexps/reader-fnos

应用需遵循 fnOS 规范，包含 manifest 文件，详细规范请参考：[FNOS文档](https://developer.fnnas.com/docs/core-concepts/manifest)


## 🔗 兼容：如何将 FnDepot 应用仓库添加到 2FStore ?

通过提交 PR 在 [fnpacks.json](https://github.com/yuexps/2FStore/fnpacks.json) 文件的 `fnpacks` 数组中添加你的 FnDepot 仓库信息：

```json
{
  "key": "你的GitHub用户名",
  "repo": "https://github.com/你的用户名/FnDepot"
}
```

FnDepot 示例仓库：https://github.com/EWEDLCM/FnDepot

FnDepot 文档：[飞书文档](https://ecn6sp7e44q3.feishu.cn/wiki/VSrmwqtjhigaygkWkyoceEvvnlb)

## ⚙️ GitHub Actions

本项目使用 GitHub Actions 实现自动化处理。
