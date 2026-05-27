# scan-to-html

将图片型PDF、扫描件、照片转换为结构化HTML，保留原始布局和文字内容。

## 何时使用

- PDF 文本提取返回空、乱码、或不完整
- 文档包含表格、图表、多栏布局需要视觉重建
- 源文件是扫描件、照片、或图片型PDF

## 依赖

```bash
pip install pymupdf pillow html2image
```

需要系统安装 Chrome、Chromium 或 Edge 浏览器（用于预览生成）。

## 脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `export_pdf.py` | PDF → 高清PNG | `python export_pdf.py input.pdf [zoom]` |
| `auto_crop.py` | 自动网格裁剪 | `python auto_crop.py image.png [rows cols]` |
| `list_templates.py` | 发现可用模板 | `python list_templates.py [--search 关键词]` |
| `generate_previews.py` | 生成模板预览图 | `python generate_previews.py` |
| `package_output.py` | 打包输出为zip | `python package_output.py [目录] [文件名]` |

## 模板库

18个预制模板，覆盖6大类文档：

- **身份证件**: passport, id_card, driver_license, business_card
- **旅行**: visa, boarding_pass, hotel_booking
- **商务**: invoice, receipt, quotation
- **财务**: payslip, bank_statement
- **证书**: birth_certificate, diploma, transcript, police_clearance
- **法律**: power_of_attorney, contract

浏览模板：打开 `templates/index.html`（支持搜索和分类筛选）。
发现模板：`python list_templates.py --search 关键词`
查看占位符：`python list_templates.py --detail 模板名`

## 工作流程

1. **导出图片** — `export_pdf.py` 3x zoom（~4K分辨率）
2. **分析结构** — 确定表格、栏数、图表位置
3. **裁剪检查** — `auto_crop.py` 分区域确认文字内容
4. **重建HTML** — 静态HTML，table布局，`table-layout: fixed`
5. **图表裁剪** — 精确像素裁剪，嵌入表格对齐
6. **确认打包** — 用户确认满意后提醒打包选项（文件夹或zip）

## 约束

- 只输出静态HTML，不加JavaScript、CSS动效、表单
- 优先检查模板库，有现成模板就用，不从零构建
- 图表用 `<tr>` 嵌入表格，空白 `<td>` 占位对齐
