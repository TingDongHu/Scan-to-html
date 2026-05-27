# scan-to-html

将图片型PDF、扫描件、照片转换为结构化HTML，保留原始布局和文字内容。

## 何时使用

- PDF 文本提取返回空、乱码、或不完整
- 文档包含表格、图表、多栏布局需要视觉重建
- 源文件是扫描件、照片、或图片型PDF

## 依赖

```bash
pip install pymupdf pillow html2image
npm install -g mineru-open-api
```

需要系统安装 Chrome、Chromium 或 Edge 浏览器（用于预览生成）。

## 脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `pipeline/export_pdf.py` | PDF → 高清PNG | `python pipeline/export_pdf.py input.pdf [zoom]` |
| `pipeline/auto_crop.py` | 自动网格裁剪 | `python pipeline/auto_crop.py image.png [rows cols]` |
| `pipeline/list_templates.py` | 发现可用模板 | `python pipeline/list_templates.py [--search 关键词]` |
| `pipeline/generate_previews.py` | 生成模板预览图 | `python pipeline/generate_previews.py` |
| `pipeline/package_output.py` | 打包输出为zip | `python pipeline/package_output.py [目录] [文件名]` |

### Skeleton-Driven Scripts (Vision-First)

| 脚本 | 用途 | 用法 |
|------|------|------|
| `pipeline/render_skeleton.py` | 骨架→HTML | `python pipeline/render_skeleton.py skeleton.json` |
| `pipeline/mineru_parse.py` | MinerU HTML→骨架 | `python pipeline/mineru_parse.py doc.html --template tmpl.json` |

### MinerU增强工作流（默认）

所有文档统一使用MinerU提取内容，Claude负责语义排版和OCR修正：

```bash
# Step 0: MinerU提取
mineru-open-api extract document.pdf -f html -o mineru_output/ \
  --language cyrillic --model vlm

# Step 1: 解析为骨架
python pipeline/mineru_parse.py mineru_output/document.html \
  --template templates/cmr/skeleton.json \
  --output partial_skeleton.json

# Step 2: Claude审核修正
# - 修正OCR错误
# - 重新分配字段内容
# - 添加pair_id实现双栏配对
# - 标记full_width全宽区域

# Step 3: 渲染HTML
python pipeline/render_skeleton.py filled_skeleton.json --output document.html
```

如有模板（如CMR）用 `--template` 获得精确字段映射；无模板则自动生成通用骨架，Claude在Step 2重构。

### 降级方案（MinerU不可用时）

```
PDF → export_pdf.py → 高清PNG → Claude Vision分析布局 → skeleton.json
  → auto_crop.py裁剪 → Claude Vision逐区域识别 → filled_skeleton.json
  → render_skeleton.py → document.html
```

### 输入模式

- **全自动**: `/scan-to-html @document.pdf` — PDF转图→Vision分析→填充→HTML
- **手动切割**: `/scan-to-html @sections/*.png` — 用户已切割→直接识别→HTML
- **混合**: 两者都提供 → 合并识别

## 模板库

18个预制模板，覆盖6大类文档：

- **身份证件**: passport, id_card, driver_license, business_card
- **旅行**: visa, boarding_pass, hotel_booking
- **商务**: invoice, receipt, quotation
- **财务**: payslip, bank_statement
- **证书**: birth_certificate, diploma, transcript, police_clearance
- **法律**: power_of_attorney, contract

浏览模板：打开 `templates/index.html`（支持搜索和分类筛选）。
发现模板：`python pipeline/list_templates.py --search 关键词`
查看占位符：`python pipeline/list_templates.py --detail 模板名`

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
