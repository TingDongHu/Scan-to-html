# Scan-to-HTML

将图片型PDF、扫描件、照片转换为结构化HTML，保留原始布局和文字内容。

## Quick Start

### 1. 安装

```bash
pip install pymupdf pillow html2image
```

### 2. 复制到 Claude Code skills 目录

```bash
# macOS / Linux
cp -r scan-to-html ~/.claude/skills/

# Windows
xcopy /E /I scan-to-html %USERPROFILE%\.claude\skills\scan-to-html
```

### 3. 一句话触发

在 Claude Code 中直接说：

```
/scan-to-html 把这个PDF转成HTML：C:\path\to\document.pdf
```

或者更自然地描述：

```
这个扫描件读不出来，帮我用 scan-to-html 转成HTML：./invoice_scan.pdf
```

Claude 会自动完成：导出高清图片 → 分析结构 → 裁剪检查 → 重建HTML → 确认打包。

### 4. 用模板快速生成

```
/scan-to-html 用 passport 模板生成一个护照HTML，姓名张三，护照号E12345678
```

```
/scan-to-html 用 invoice 模板做一份发票，公司名Acme Corp，金额$1,200
```

## 功能

- **PDF → 高清图片**：PyMuPDF 3x zoom 导出 ~4K 分辨率 PNG
- **智能裁剪检查**：自动网格裁剪，逐区域确认文字内容
- **静态HTML重建**：table布局，精确对齐，无JavaScript依赖
- **18个预制模板**：覆盖身份证件、旅行、商务、财务、证书、法律6大类
- **跨平台**：支持 Windows / macOS / Linux

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

## 常用命令

```bash
# 查看所有模板
python list_templates.py

# 搜索模板
python list_templates.py --search 发票

# 查看模板占位符（含说明）
python list_templates.py --detail invoice

# 导出PDF为高清图片
python export_pdf.py input.pdf 3

# 自动裁剪图片用于检查
python auto_crop.py image.png 2 2

# 打包输出为zip
python package_output.py . output.zip
```

## 工作流程

1. **导出图片** — `export_pdf.py` 3x zoom（~4K分辨率）
2. **分析结构** — 确定表格、栏数、图表位置
3. **裁剪检查** — `auto_crop.py` 分区域确认文字内容
4. **重建HTML** — 静态HTML，table布局，`table-layout: fixed`
5. **图表裁剪** — 精确像素裁剪，嵌入表格对齐
6. **确认打包** — 用户确认满意后提醒打包选项（文件夹或zip）

## License

MIT
