# 2FStore

一个为FNOS创建的中心化应用仓库，开发者可以通过PR提交应用，用户可以浏览和下载应用。

## 注意：项目未完善，摸鱼中~

## 功能特点

- 应用搜索和分类浏览
- 应用信息自动从GitHub仓库获取
- 自动更新应用信息
- 快速下载应用

## 如何提交应用

开发者可以通过以下方式提交应用到仓库：

### 1. 通过Issues提交（推荐）
1. 点击仓库中的"Issues"标签
2. 点击"New issue"按钮
3. 选择"应用提交"模板
4. 填写应用信息（应用ID、应用名称、GitHub仓库URL）
5. 提交Issue，系统将自动处理并更新元数据

### 2. 通过Pull Request提交
1. Fork 本仓库
2. 在项目根目录的 `apps.json` 文件的 `apps` 数组中添加你的应用信息，示例如下：
{
    "id": "your-app-id", // 应用ID，必须唯一
    "name": "你的应用名称", // 应用名称，随便取
    "repository": "https://github.com/user/your-repo" // 应用GitHub仓库URL
}
3. 创建 Pull Request 到主分支
4. 等待合并

## 应用信息获取

系统会自动从GitHub仓库获取以下信息：

- 应用描述
- 作者信息
- 星标数和分支数
- 最后更新时间
- 最新版本
- 下载链接（从GitHub Release获取）
- 应用图标
- 应用分类（自动完成）

## 应用仓库结构

### 建议包含的文件

```
app_id/
├── ICON.PNG
├── ICON_256.PNG
├── manifest
└── README.md
```

示例仓库：https://github.com/yuexps/v2raya-fnos

应用需遵循FNOS规范，包含manifest文件，详细规范请参考：[飞牛文档](https://developer.fnnas.com/docs/core-concepts/manifest)


## 兼容：如何将 FnDepot 应用仓库添加到 2FStore

通过提交PR在`fnpacks.json`文件的`fnpacks`数组中添加你的 FnDepot 仓库信息：

```json
{
  "key": "你的GitHub用户名",
  "repo": "https://github.com/你的用户名/FnDepot"
}
```

FnDepot示例仓库：https://github.com/EWEDLCM/FnDepot

FnDepot文档：https://ecn6sp7e44q3.feishu.cn/wiki/VSrmwqtjhigaygkWkyoceEvvnlb



## GitHub Actions

本项目使用GitHub Actions实现自动化处理

更多信息请参考：[GitHub Actions文档](https://docs.github.com/zh/actions)