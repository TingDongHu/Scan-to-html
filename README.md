# Scan-to-HTML

将图片型PDF、扫描件、照片转换为结构化HTML，保留原始布局和文字内容。

## 功能

- **PDF → 高清图片**：PyMuPDF 3x zoom 导出 ~4K 分辨率 PNG
- **智能裁剪检查**：自动网格裁剪，逐区域确认文字内容
- **静态HTML重建**：table布局，精确对齐，无JavaScript依赖
- **18个预制模板**：覆盖身份证件、旅行、商务、财务、证书、法律6大类
- **跨平台**：支持 Windows / macOS / Linux

## 安装

```bash
pip install pymupdf pillow html2image
```

需要系统安装 Chrome、Chromium 或 Edge 浏览器（用于预览生成）。

## 快速开始

### 扫描件转HTML

```bash
# 1. 导出高清图片
python export_pdf.py input.pdf 3

# 2. 自动裁剪检查
python auto_crop.py pdf_pages/page_1.png 2 2

# 3. 重建HTML（手动或由agent完成）
# 4. 打包输出
python package_output.py . output.zip
```

### 使用模板

```bash
# 查看所有模板
python list_templates.py

# 搜索模板
python list_templates.py --search 发票

# 查看模板占位符
python list_templates.py --detail invoice

# 生成模板预览图
python generate_previews.py
```

## 模板库

| 分类 | 模板 |
|------|------|
| 身份证件 | passport, id_card, driver_license, business_card |
| 旅行 | visa, boarding_pass, hotel_booking |
| 商务 | invoice, receipt, quotation |
| 财务 | payslip, bank_statement |
| 证书 | birth_certificate, diploma, transcript, police_clearance |
| 法律 | power_of_attorney, contract |

浏览模板：打开 `templates/index.html`（支持搜索和分类筛选）。

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `export_pdf.py` | PDF → 高清PNG（默认3x zoom） |
| `auto_crop.py` | 自动网格裁剪图片用于检查 |
| `list_templates.py` | 发现和查看模板 |
| `generate_previews.py` | 生成模板预览缩略图 |
| `package_output.py` | 打包HTML+图片为zip |

## 工作流程

1. **导出图片** — `export_pdf.py` 3x zoom（~4K分辨率）
2. **分析结构** — 确定表格、栏数、图表位置
3. **裁剪检查** — `auto_crop.py` 分区域确认文字内容
4. **重建HTML** — 静态HTML，table布局，`table-layout: fixed`
5. **图表裁剪** — 精确像素裁剪，嵌入表格对齐
6. **确认打包** — 用户确认满意后提醒打包选项（文件夹或zip）

## 作为Claude Code Skill使用

将此目录放到 `~/.claude/skills/` 下，Claude Code会自动识别并调用。

触发条件：
- PDF文本提取返回空、乱码、或不完整
- 文档包含表格、图表、多栏布局
- 源文件是扫描件、照片、或图片型PDF

## License

MIT
