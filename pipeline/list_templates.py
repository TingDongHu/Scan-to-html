#!/usr/bin/env python3
"""Scan templates directory and list all available templates with their placeholders.

Usage: python list_templates.py [--json]
Output: Table of templates with categories, placeholders, and file paths.
"""

import sys
import os
import re
import json
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Category mapping
CATEGORIES = {
    "passport": "身份证件",
    "id_card": "身份证件",
    "driver_license": "身份证件",
    "business_card": "身份证件",
    "visa": "旅行",
    "boarding_pass": "旅行",
    "hotel_booking": "旅行",
    "invoice": "商务",
    "receipt": "商务",
    "quotation": "商务",
    "payslip": "财务",
    "bank_statement": "财务",
    "birth_certificate": "证书",
    "diploma": "证书",
    "transcript": "证书",
    "police_clearance": "证书",
    "power_of_attorney": "法律",
    "contract": "法律",
}

def extract_placeholders(html_content):
    """Extract {{PLACEHOLDER}} from HTML content."""
    return sorted(set(re.findall(r'\{\{([A-Z_0-9]+)\}\}', html_content)))

# Placeholder descriptions for common fields
PLACEHOLDER_DESC = {
    # Identity
    "SURNAME": "姓 / Surname",
    "GIVEN_NAME": "名 / Given Name",
    "FULL_NAME": "全名 / Full Name",
    "SEX": "性别 / Sex (M/F)",
    "DOB": "出生日期 / Date of Birth",
    "POB": "出生地 / Place of Birth",
    "NATIONALITY": "国籍 / Nationality",
    "ID_NUMBER": "证件号码 / ID Number",
    "PASSPORT_NUMBER": "护照号码 / Passport Number",
    "ADDRESS": "地址 / Address",
    "PHOTO": "照片占位 / Photo placeholder",
    "AUTHORITY": "签发机关 / Authority",
    "TYPE": "证件类型 / Document Type",
    "DOE": "有效期至 / Date of Expiry",
    "DOI": "签发日期 / Date of Issue",
    "MRZ_LINE_1": "机读区第1行 / MRZ Line 1",
    "MRZ_LINE_2": "机读区第2行 / MRZ Line 2",
    # Travel
    "COUNTRY_CODE": "国家代码 / Country Code",
    "VISA_TYPE": "签证类型 / Visa Type",
    "VISA_NUMBER": "签证号码 / Visa Number",
    "ENTRY_DATE": "入境日期 / Entry Date",
    "EXIT_DATE": "出境日期 / Exit Date",
    "ENTRIES": "入境次数 / Number of Entries",
    "DURATION": "停留天数 / Duration (days)",
    "ISSUING_AUTHORITY": "签发机关 / Issuing Authority",
    "ISSUE_DATE": "签发日期 / Issue Date",
    "AIRLINE": "航空公司 / Airline",
    "FLIGHT_NUMBER": "航班号 / Flight Number",
    "FLIGHT_DATE": "航班日期 / Flight Date",
    "DEPART_CODE": "出发城市代码 / Departure Code",
    "DEPART_CITY": "出发城市 / Departure City",
    "ARRIVE_CODE": "到达城市代码 / Arrival Code",
    "ARRIVE_CITY": "到达城市 / Arrival City",
    "SEAT": "座位号 / Seat",
    "CLASS": "舱位 / Class",
    "GATE": "登机口 / Gate",
    "BOARDING_TIME": "登机时间 / Boarding Time",
    "PASSENGER_NAME": "乘客姓名 / Passenger Name",
    "HOTEL_NAME": "酒店名称 / Hotel Name",
    "HOTEL_ADDRESS": "酒店地址 / Hotel Address",
    "CONFIRMATION_NUMBER": "确认号 / Confirmation Number",
    "GUEST_NAME": "住客姓名 / Guest Name",
    "GUEST_PHONE": "住客电话 / Guest Phone",
    "GUEST_EMAIL": "住客邮箱 / Guest Email",
    "CHECK_IN": "入住日期 / Check-in Date",
    "CHECK_OUT": "退房日期 / Check-out Date",
    "ROOM_TYPE": "房型 / Room Type",
    "NIGHTS": "住宿天数 / Number of Nights",
    "ROOM_COUNT": "房间数 / Room Count",
    "BREAKFAST": "早餐 / Breakfast (Y/N)",
    "ROOM_TOTAL": "房费小计 / Room Total",
    "TAX": "税费 / Tax",
    "TOTAL": "合计 / Total",
    "NOTES": "备注 / Notes",
    # Business
    "COMPANY_NAME": "公司名称 / Company Name",
    "COMPANY_ADDRESS": "公司地址 / Company Address",
    "COMPANY_PHONE": "公司电话 / Company Phone",
    "COMPANY_EMAIL": "公司邮箱 / Company Email",
    "COMPANY_CITY": "公司城市 / Company City",
    "CUSTOMER_NAME": "客户名称 / Customer Name",
    "CUSTOMER_ADDRESS": "客户地址 / Customer Address",
    "CUSTOMER_TAX_ID": "客户税号 / Customer Tax ID",
    "CUSTOMER_PHONE": "客户电话 / Customer Phone",
    "INVOICE_NUMBER": "发票编号 / Invoice Number",
    "INVOICE_DATE": "开票日期 / Invoice Date",
    "DUE_DATE": "到期日 / Due Date",
    "QUOTE_NUMBER": "报价编号 / Quote Number",
    "QUOTE_DATE": "报价日期 / Quote Date",
    "VALID_UNTIL": "有效期至 / Valid Until",
    "PROJECT_NAME": "项目名称 / Project Name",
    "PROJECT_LOCATION": "项目地点 / Project Location",
    "ITEM_1_DESC": "项目1描述 / Item 1 Description",
    "ITEM_1_QTY": "项目1数量 / Item 1 Qty",
    "ITEM_1_PRICE": "项目1单价 / Item 1 Unit Price",
    "ITEM_1_TOTAL": "项目1小计 / Item 1 Total",
    "ITEM_1_UNIT": "项目1单位 / Item 1 Unit",
    "ITEM_2_DESC": "项目2描述 / Item 2 Description",
    "ITEM_2_QTY": "项目2数量 / Item 2 Qty",
    "ITEM_2_PRICE": "项目2单价 / Item 2 Unit Price",
    "ITEM_2_TOTAL": "项目2小计 / Item 2 Total",
    "ITEM_2_UNIT": "项目2单位 / Item 2 Unit",
    "ITEM_3_DESC": "项目3描述 / Item 3 Description",
    "ITEM_3_QTY": "项目3数量 / Item 3 Qty",
    "ITEM_3_PRICE": "项目3单价 / Item 3 Unit Price",
    "ITEM_3_TOTAL": "项目3小计 / Item 3 Total",
    "ITEM_3_UNIT": "项目3单位 / Item 3 Unit",
    "SUBTOTAL": "小计 / Subtotal",
    "TAX_RATE": "税率 / Tax Rate (%)",
    "PAYMENT_METHOD": "付款方式 / Payment Method",
    "PAYMENT_TERMS": "付款条款 / Payment Terms",
    "BANK_NAME": "银行名称 / Bank Name",
    "BANK_ACCOUNT": "银行账号 / Bank Account",
    "BANK_SWIFT": "SWIFT代码 / SWIFT Code",
    "SHIP_TO_NAME": "收货方名称 / Ship To Name",
    "SHIP_TO_ADDRESS": "收货地址 / Ship To Address",
    "TERM_1": "条款1 / Term 1",
    "TERM_2": "条款2 / Term 2",
    "TERM_3": "条款3 / Term 3",
    # Finance
    "PAY_PERIOD": "工资期间 / Pay Period",
    "PAYSLIP_NUMBER": "工资单编号 / Payslip Number",
    "EMPLOYEE_NAME": "员工姓名 / Employee Name",
    "EMPLOYEE_ID": "员工工号 / Employee ID",
    "DEPARTMENT": "部门 / Department",
    "POSITION": "职位 / Position",
    "BASE_SALARY": "基本工资 / Base Salary",
    "OVERTIME": "加班费 / Overtime",
    "BONUS": "奖金 / Bonus",
    "ALLOWANCE": "津贴 / Allowance",
    "TOTAL_EARNINGS": "收入合计 / Total Earnings",
    "PENSION": "养老保险 / Pension",
    "MEDICAL": "医疗保险 / Medical",
    "UNEMPLOYMENT": "失业保险 / Unemployment",
    "HOUSING_FUND": "住房公积金 / Housing Fund",
    "INCOME_TAX": "个人所得税 / Income Tax",
    "TOTAL_DEDUCTIONS": "扣减合计 / Total Deductions",
    "NET_PAY": "实发工资 / Net Pay",
    "BANK_BRANCH": "银行支行 / Bank Branch",
    "STATEMENT_PERIOD": "账单期间 / Statement Period",
    "ACCOUNT_NAME": "账户名称 / Account Name",
    "ACCOUNT_NUMBER": "账号 / Account Number",
    "CURRENCY": "币种 / Currency",
    "OPENING_BALANCE": "期初余额 / Opening Balance",
    "CLOSING_BALANCE": "期末余额 / Closing Balance",
    "TOTAL_CREDITS": "贷方合计 / Total Credits",
    "TOTAL_DEBITS": "借方合计 / Total Debits",
    # Certificate
    "CERT_NUMBER": "证书编号 / Certificate Number",
    "FATHER_NAME": "父亲姓名 / Father's Name",
    "FATHER_NATIONALITY": "父亲国籍 / Father's Nationality",
    "FATHER_OCCUPATION": "父亲职业 / Father's Occupation",
    "MOTHER_NAME": "母亲姓名 / Mother's Name",
    "MOTHER_NATIONALITY": "母亲国籍 / Mother's Nationality",
    "MOTHER_OCCUPATION": "母亲职业 / Mother's Occupation",
    "REG_DATE": "登记日期 / Registration Date",
    "REG_NUMBER": "登记号 / Registration Number",
    "TIME": "出生时间 / Time of Birth",
    "INSTITUTION": "学校名称 / Institution Name",
    "INSTITUTION_ADDRESS": "学校地址 / Institution Address",
    "GRADUATE_NAME": "毕业生姓名 / Graduate Name",
    "DEGREE": "学位 / Degree",
    "MAJOR": "专业 / Major",
    "GRAD_DATE": "毕业日期 / Graduation Date",
    "DEAN_NAME": "院长姓名 / Dean Name",
    "RECTORS_NAME": "校长姓名 / Rector's Name",
    "STUDENT_NAME": "学生姓名 / Student Name",
    "STUDENT_ID": "学号 / Student ID",
    "ENROLL_DATE": "入学日期 / Enrollment Date",
    "TOTAL_CREDITS": "总学分 / Total Credits",
    "OVERALL_GPA": "总绩点 / Overall GPA",
    "TRANSCRIPT_NUMBER": "成绩单编号 / Transcript Number",
    # Legal
    "CONTRACT_TITLE": "合同标题 / Contract Title",
    "CONTRACT_TYPE": "合同类型 / Contract Type",
    "CONTRACT_NUMBER": "合同编号 / Contract Number",
    "PARTY_A_NAME": "甲方名称 / Party A Name",
    "PARTY_A_REP": "甲方法定代表人 / Party A Representative",
    "PARTY_A_ADDRESS": "甲方地址 / Party A Address",
    "PARTY_A_PHONE": "甲方电话 / Party A Phone",
    "PARTY_B_NAME": "乙方名称 / Party B Name",
    "PARTY_B_REP": "乙方法定代表人 / Party B Representative",
    "PARTY_B_ADDRESS": "乙方地址 / Party B Address",
    "PARTY_B_PHONE": "乙方电话 / Party B Phone",
    "ARTICLE_1": "第一条内容 / Article 1 Content",
    "ARTICLE_2": "第二条内容 / Article 2 Content",
    "ARTICLE_3": "第三条内容 / Article 3 Content",
    "ARTICLE_4": "第四条内容 / Article 4 Content",
    "ARTICLE_5": "第五条内容 / Article 5 Content",
    "PARTY_A_DATE": "甲方签署日期 / Party A Date",
    "PARTY_B_DATE": "乙方签署日期 / Party B Date",
    "PRINCIPAL_NAME": "委托人姓名 / Principal Name",
    "PRINCIPAL_ID": "委托人证件号 / Principal ID",
    "AGENT_NAME": "受托人姓名 / Agent Name",
    "AGENT_ID": "受托人证件号 / Agent ID",
    "AUTHORITY_1": "授权事项1 / Authority 1",
    "AUTHORITY_2": "授权事项2 / Authority 2",
    "AUTHORITY_3": "授权事项3 / Authority 3",
    "VALID_FROM": "有效期自 / Valid From",
    "VALID_TO": "有效期至 / Valid To",
    "PRINCIPAL_DATE": "委托人签署日期 / Principal Date",
    "AGENT_DATE": "受托人签署日期 / Agent Date",
    # Common
    "DATE": "日期 / Date",
    "NUMBER": "编号 / Number",
    "NAME": "姓名 / Name",
    "SEAL": "公章 / Seal",
    "SIGNATURE": "签名 / Signature",
}

def scan_templates():
    """Scan all template directories and extract info."""
    results = []
    for item in sorted(TEMPLATES_DIR.iterdir()):
        if not item.is_dir():
            continue
        template_file = item / "template.html"
        if not template_file.exists():
            continue

        html_content = template_file.read_text(encoding="utf-8")
        placeholders = extract_placeholders(html_content)
        has_preview = (item / "preview.png").exists()

        # Extract title from HTML
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        title = title_match.group(1) if title_match else item.name

        results.append({
            "name": item.name,
            "title": title,
            "category": CATEGORIES.get(item.name, "未分类"),
            "placeholders": placeholders,
            "placeholder_count": len(placeholders),
            "has_preview": has_preview,
            "path": str(item),
            "template_file": str(template_file),
        })

    return results

def print_table(templates):
    """Print templates as a formatted table."""
    print(f"\n{'='*80}")
    print(f"  模板库扫描结果 / Template Library Scan")
    print(f"  路径: {TEMPLATES_DIR}")
    print(f"  共 {len(templates)} 个模板")
    print(f"{'='*80}\n")

    # Group by category
    by_category = {}
    for t in templates:
        cat = t["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(t)

    for cat, items in by_category.items():
        print(f"【{cat}】({len(items)}个)")
        print(f"  {'名称':<20} {'占位符数':<8} {'预览':<4} {'路径'}")
        print(f"  {'-'*20} {'-'*8} {'-'*4} {'-'*40}")
        for t in items:
            preview = "Y" if t["has_preview"] else "N"
            print(f"  {t['name']:<20} {t['placeholder_count']:<8} {preview:<4} {t['path']}")
        print()

    print(f"{'='*80}")
    print("  用法 / Usage:")
    print("  1. python list_templates.py          # 显示表格")
    print("  2. python list_templates.py --json    # JSON格式输出")
    print("  3. 在模板中搜索: python list_templates.py --search 护照")
    print(f"{'='*80}\n")

def print_template_detail(templates, name):
    """Print detail for a specific template."""
    for t in templates:
        if t["name"] == name:
            print(f"\n模板: {t['title']}")
            print(f"分类: {t['category']}")
            print(f"路径: {t['template_file']}")
            print(f"\n占位符 ({t['placeholder_count']}个):")
            for p in t["placeholders"]:
                desc = PLACEHOLDER_DESC.get(p, "")
                if desc:
                    print(f"  {{{{  {p}  }}}}  → {desc}")
                else:
                    print(f"  {{{{  {p}  }}}}")
            print()
            return
    print(f"未找到模板: {name}")

def main():
    templates = scan_templates()

    if "--json" in sys.argv:
        print(json.dumps(templates, ensure_ascii=False, indent=2))
        return

    if "--search" in sys.argv:
        idx = sys.argv.index("--search")
        if idx + 1 < len(sys.argv):
            query = sys.argv[idx + 1].lower()
            matches = [t for t in templates if query in t["name"].lower() or query in t["title"].lower() or query in t["category"].lower()]
            if matches:
                print(f"\n搜索 '{query}' - 找到 {len(matches)} 个结果:\n")
                for t in matches:
                    print(f"  {t['name']:<20} {t['title']:<30} [{t['category']}]")
            else:
                print(f"未找到匹配 '{query}' 的模板")
            return

    if "--detail" in sys.argv:
        idx = sys.argv.index("--detail")
        if idx + 1 < len(sys.argv):
            print_template_detail(templates, sys.argv[idx + 1])
            return

    print_table(templates)

if __name__ == "__main__":
    main()
