<p align="center">
  <strong>为 FNOS 生态打造的第三方中心化应用仓库</strong>
</p>

<p align="center">
  开发者可通过 Issue 或 Pull Request 提交应用，用户可便捷浏览与下载各类应用
</p>

> ⚠️ **注意**：本项目仍在摸鱼中，目前由Bug驱动！欢迎大家共同参与完善！
>
> **主要作用：**
>
> - 自动维护两个应用元数据文件：  
>   - `app_details.json`：https://gh.2fstore.cfd/app_details.json
>   - `fnpack_details.json`：https://gh.2fstore.cfd/fnpack_details.json
> - 持续提升应用收录与元数据更新的便捷性和准确性

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
├── ICON.PNG              # 应用图标（必须大写）
├── ICON_256.PNG          # 256x256图标（可选，优先使用）
├── manifest              # fnOS 应用清单文件（必须）
└── README.md             # 应用说明
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

📂 示例仓库：[Reader](https://github.com/yuexps/reader-fnos)

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
| Issue 提交（应用提交模板） | 自动验证应用信息并更新 `apps.json` , `fnpacks.json` |
| PR 合并到 main | 自动验证应用格式 |
| 每日定时（北京时间 00:00） | 批量更新所有应用元数据 |
| `apps.json` 变更 | 触发元数据更新 |
| `fnpacks.json` 变更 | 触发 FnDepot 仓库更新 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

- 🐛 发现问题？[提交 Issue](https://github.com/yuexps/2FStore/issues/new)
- 💡 有新想法？欢迎讨论
- 📦 提交应用？按照上述指南操作

---

## 🛠️ 技术栈 & 资源致谢

### 前端技术
- 纯原生 HTML / CSS / JavaScript
- [Miuix](https://compose-miuix-ui.github.io/miuix) 风格 UI 设计灵感
- CSS Variables 实现亮/暗主题

### 后端 & 自动化
- [GitHub Actions](https://github.com/features/actions) - CI/CD 自动化
- [GitHub Pages](https://pages.github.com/) - 静态站点托管
- [Vercel](https://vercel.com/) - 备用部署平台
- Python 3.11 - 数据处理脚本

### 第三方服务
- [Bing 每日壁纸 API](https://bing.biturl.top/) - 背景图片
- GitHub API - 仓库元数据获取

### 相关项目
- [FnDepot](https://github.com/EWEDLCM/FnDepot) - 去中心化应用源规范
- [fnOS 开发文档](https://developer.fnnas.com/) - 包含应用规范、开发指南等

---

## ⚠️ 免责声明

1. **非官方项目**  
   本项目为社区驱动的第三方应用仓库，与广州铁刃智造技术有限公司（fnOS 官方）无任何关联。

2. **应用安全**  
   本仓库仅提供应用索引和下载链接聚合服务，**不对任何第三方应用的安全性、稳定性、合法性负责**。用户下载和安装任何应用前，请自行评估风险。

3. **数据来源**  
   所有应用信息均来自开发者提交的 GitHub 公开仓库，本项目不存储任何应用安装包。

4. **版权声明**  
   各应用的版权归其原作者所有。如有侵权，请通过 [Issue](https://github.com/yuexps/2FStore/issues) 联系我们，我们将及时处理。

5. **服务可用性**  
   本项目为开源免费服务，不保证服务的持续可用性。GitHub API 限制、网络问题等可能影响服务正常运行。

6. **使用风险**  
   使用本仓库提供的任何应用造成的数据丢失、设备损坏或其他损失，本项目及贡献者不承担任何责任。

---

## 📄 开源许可证

本项目采用 [MIT 许可证](LICENSE) 开源。

```
MIT License

Copyright (c) 2024 2FStore Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/yuexps/2FStore">2FStore</a> Contributors
</p>