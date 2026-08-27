# 更新日志 (ChangeLog)

本项目所有值得记录的变更都记录在此文件中。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

## [0.1.1] - 2026-08-27

### 修复

- 修复格式化工具栏图标显示异常。
- 增加常见国内模型提供商。
- 增加自定义提示词功能。


## [0.1.0] - 2026-08-27

### 新增

- `build.py` 打包输出目录调整为 `bin` 文件夹，打包时自动创建 `bin` 目录，并在忽略列表中排除 `bin`。

### 修复

- 修复 `build.py` 打包时 docs 文件夹未被正确忽略的问题：`os.walk` 返回的目录名不带末尾斜杠，
  原先 `IGNORE_PATTERNS` 中的 `"docs/"` 无法与目录名 `"docs"` 匹配，导致 docs 文件夹被打入 ankiaddon 包；
  现改为 `"docs"`，打包时正确忽略。
