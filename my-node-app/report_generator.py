"""
SMR Motors - Professional PDF and Excel Report Generator
Produces branded, formatted reports for Inventory, Sold-Out Vehicles, and Superadmin Financials.
"""

import io
import datetime

# Graceful ReportLab import handling
try:
    from reportlab.lib.pagesizes import letter, A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    )
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
    _reportlab_err = None
except ImportError as e:
    REPORTLAB_AVAILABLE = False
    _reportlab_err = str(e)
    colors = None
    canvas = None

# Graceful openpyxl import handling
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
    _openpyxl_err = None
except ImportError as e:
    OPENPYXL_AVAILABLE = False
    _openpyxl_err = str(e)

if REPORTLAB_AVAILABLE and canvas:
    class NumberedCanvas(canvas.Canvas):
        """
        Two-pass canvas to dynamically compute and render total page count 'Page X of Y'.
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(num_pages)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def draw_page_number(self, page_count):
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            
            # Header rule & mini watermark
            page_width, page_height = self._pagesize
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, page_height - 30, page_width - 36, page_height - 30)
            self.drawString(36, page_height - 24, "SMR MOTORS — AUTOMOTIVE INVENTORY & REPORTING SYSTEM")
            
            # Footer rule & text
            self.line(36, 36, page_width - 36, 36)
            footer_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(page_width - 36, 24, footer_text)
            self.drawString(36, 24, "CONFIDENTIAL & PROPRIETARY — SMR MOTORS INTERNAL DOCUMENT")
            self.restoreState()
else:
    class NumberedCanvas:
        pass


def format_inr(val):
    """Formats numeric value to Indian currency representation with proper negative loss display."""
    if val is None or val == "":
        return "₹0"
    try:
        f = float(val)
        if f < 0:
            return f"-₹{abs(f):,.2f}"
        return f"₹{f:,.2f}"
    except (ValueError, TypeError):
        return f"₹{val}"


def generate_pdf_report(report_type, items, filters, generated_by="Administrator", is_superadmin=False):
    """
    Generates a high-quality PDF report using ReportLab.
    report_type: 'listings', 'sold', 'financial'
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError(f"ReportLab PDF engine is not available: {_reportlab_err}. Please ensure reportlab is installed via requirements.txt.")

    if report_type == "financial" and not is_superadmin:
        raise PermissionError("Access Forbidden: Financial reports are restricted to SUPERADMIN.")

    buffer = io.BytesIO()
    # Use landscape A4 for listings and financials to ensure high readability
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    
    title_style = ParagraphStyle(
        "DocTitle",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A")
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#EA580C") # SMR Motors Orange Accent
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=normal_style,
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#475569")
    )

    cell_style = ParagraphStyle(
        "CellText",
        parent=normal_style,
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1E293B")
    )

    cell_bold_style = ParagraphStyle(
        "CellBoldText",
        parent=cell_style,
        fontName="Helvetica-Bold"
    )

    cell_header_style = ParagraphStyle(
        "HeaderCellText",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    elements = []

    # Title & Metadata
    if report_type == "listings":
        report_title = "MOTORCYCLE INVENTORY & LISTINGS REPORT"
        report_sub = "Active, Pending, Rejected & Sold-Out Catalog"
    elif report_type == "sold":
        report_title = "SOLD MOTORCYCLES & FULFILLMENT REPORT"
        report_sub = "Completed Transactions and Vehicle Departures"
    elif report_type == "financial":
        report_title = "CONFIDENTIAL FINANCIAL PERFORMANCE & PROFIT AUDIT"
        report_sub = "Superadmin Executive Ledger: Revenues, Payouts, Expenses & Margins"
    else:
        report_title = f"{report_type.upper()} REPORT"
        report_sub = "Dealership Management Operations"

    now_str = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
    filter_parts = []
    if filters.get("preset"):
        filter_parts.append(f"Period: {filters['preset'].replace('_', ' ').title()}")
    if filters.get("start_date") or filters.get("end_date"):
        filter_parts.append(f"Date: {filters.get('start_date', 'Start')} to {filters.get('end_date', 'Present')}")
    if filters.get("status") and filters.get("status") != "all":
        filter_parts.append(f"Status: {filters['status'].title()}")
    if filters.get("brand") and filters.get("brand") != "all":
        filter_parts.append(f"Brand: {filters['brand']}")
    if filters.get("search"):
        filter_parts.append(f"Search: '{filters['search']}'")

    filters_summary = " | ".join(filter_parts) if filter_parts else "All Records (No Filters)"

    elements.append(Paragraph(report_title, title_style))
    elements.append(Paragraph(f"SMR MOTORS — {report_sub}", subtitle_style))
    elements.append(Spacer(1, 6))

    meta_html = f"<b>Generated On:</b> {now_str} &nbsp;|&nbsp; <b>Authorized User:</b> {generated_by} &nbsp;|&nbsp; <b>Active Filters:</b> {filters_summary}"
    elements.append(Paragraph(meta_html, meta_style))
    elements.append(Spacer(1, 12))

    # Build Table
    table_data = []
    col_widths = []

    if report_type == "listings":
        headers = ["ID", "Vehicle Title", "Brand & Model", "Year", "Listed Price", "Status", "Seller Info", "Kilometers", "Date"]
        col_widths = [32, 160, 110, 45, 80, 75, 120, 65, 75]
        table_data.append([Paragraph(h, cell_header_style) for h in headers])

        total_inventory_val = 0.0
        for b in items:
            p_val = float(b.get("price") or 0)
            total_inventory_val += p_val
            st = str(b.get("listing_status") or b.get("status") or "pending").title()
            seller = f"{b.get('seller_name') or '-'}<br/><font size='7' color='#64748B'>{b.get('seller_phone') or ''}</font>"
            kms = f"{(int(b.get('kilometers_driven') or 0)):,} km"
            dt = str(b.get("created_at") or "")[:10]

            row = [
                Paragraph(str(b.get("id")), cell_style),
                Paragraph(f"<b>{b.get('title') or '-'}</b>", cell_style),
                Paragraph(f"{b.get('brand', '')} {b.get('model', '')}", cell_style),
                Paragraph(str(b.get("year") or "-"), cell_style),
                Paragraph(format_inr(p_val), cell_bold_style),
                Paragraph(st, cell_style),
                Paragraph(seller, cell_style),
                Paragraph(kms, cell_style),
                Paragraph(dt, cell_style),
            ]
            table_data.append(row)

        # Summary Row
        summary_row = [
            Paragraph("<b>TOTAL</b>", cell_bold_style),
            Paragraph(f"<b>{len(items)} Vehicles</b>", cell_bold_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph(f"<b>{format_inr(total_inventory_val)}</b>", cell_bold_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
        ]
        table_data.append(summary_row)

    elif report_type == "sold":
        headers = ["ID", "Motorcycle", "Brand & Year", "Sale Price", "Seller Payout", "Gross Margin", "Buyer Name", "Seller Info", "Sold Date"]
        col_widths = [32, 150, 80, 80, 80, 75, 95, 105, 65]
        table_data.append([Paragraph(h, cell_header_style) for h in headers])

        tot_sale = 0.0
        tot_payout = 0.0
        tot_margin = 0.0
        for t in items:
            sale_p = float(t.get("actual_sale_price") or 0)
            payout_p = float(t.get("seller_payout") or 0)
            margin = float(t.get("realized_profit") or (sale_p - payout_p))
            tot_sale += sale_p
            tot_payout += payout_p
            tot_margin += margin

            # Redact if not superadmin
            payout_str = format_inr(payout_p) if is_superadmin else "[RESTRICTED]"
            margin_str = format_inr(margin) if is_superadmin else "[RESTRICTED]"

            row = [
                Paragraph(str(t.get("bike_id") or t.get("id")), cell_style),
                Paragraph(f"<b>{t.get('bike_title') or t.get('title') or '-'}</b>", cell_style),
                Paragraph(f"{t.get('brand', '')} ({t.get('year', '')})", cell_style),
                Paragraph(format_inr(sale_p), cell_bold_style),
                Paragraph(payout_str, cell_style),
                Paragraph(margin_str, cell_style),
                Paragraph(t.get("buyer_name") or "Retail Buyer", cell_style),
                Paragraph(f"{t.get('seller_name') or '-'}<br/><font size='7' color='#64748B'>{t.get('seller_phone') or ''}</font>", cell_style),
                Paragraph(str(t.get("sold_at") or t.get("created_at") or "")[:10], cell_style)
            ]
            table_data.append(row)

        summary_row = [
            Paragraph("<b>TOTAL</b>", cell_bold_style),
            Paragraph(f"<b>{len(items)} Units Sold</b>", cell_bold_style),
            Paragraph("", cell_style),
            Paragraph(f"<b>{format_inr(tot_sale)}</b>", cell_bold_style),
            Paragraph(f"<b>{format_inr(tot_payout) if is_superadmin else '[RESTRICTED]'}</b>", cell_bold_style),
            Paragraph(f"<b>{format_inr(tot_margin) if is_superadmin else '[RESTRICTED]'}</b>", cell_bold_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style)
        ]
        table_data.append(summary_row)

    elif report_type == "financial":
        headers = ["ID", "Motorcycle Title", "Sale Revenue", "Seller Payout", "Service/Repairs", "Total Expenses", "Net Profit", "Margin %", "Sold Date"]
        col_widths = [32, 170, 85, 85, 80, 80, 85, 60, 65]
        table_data.append([Paragraph(h, cell_header_style) for h in headers])

        tot_rev = 0.0
        tot_pay = 0.0
        tot_exp = 0.0
        tot_prof = 0.0

        for t in items:
            rev = float(t.get("actual_sale_price") or 0)
            pay = float(t.get("seller_payout") or t.get("buying_price") or 0)
            rep_v = float(t.get("repair_expense") or 0)
            srv_v = float(t.get("service_expense") or 0)
            if rep_v > 0 and srv_v == rep_v and float(t.get("total_expenses") or 0) < (rep_v + srv_v):
                repairs = rep_v
            else:
                repairs = rep_v + srv_v
            exp = float(t.get("total_expenses") if t.get("total_expenses") is not None else (repairs + float(t.get("other_expense") or 0)))
            prof = float(t.get("realized_profit") if t.get("realized_profit") is not None else (rev - pay - exp))
            margin_pct = (prof / pay * 100.0) if pay > 0 else 0.0

            tot_rev += rev
            tot_pay += pay
            tot_exp += exp
            tot_prof += prof

            row = [
                Paragraph(str(t.get("bike_id") or t.get("id")), cell_style),
                Paragraph(f"<b>{t.get('bike_title') or t.get('title') or '-'}</b>", cell_style),
                Paragraph(format_inr(rev), cell_bold_style),
                Paragraph(format_inr(pay), cell_style),
                Paragraph(format_inr(repairs), cell_style),
                Paragraph(format_inr(exp), cell_style),
                Paragraph(format_inr(prof), cell_bold_style),
                Paragraph(f"{margin_pct:.1f}%", cell_style),
                Paragraph(str(t.get("sold_at") or t.get("created_at") or "")[:10], cell_style)
            ]
            table_data.append(row)

        overall_margin = (tot_prof / tot_pay * 100.0) if tot_pay > 0 else 0.0
        summary_row = [
            Paragraph("<b>TOTAL</b>", cell_bold_style),
            Paragraph(f"<b>{len(items)} Transactions</b>", cell_bold_style),
            Paragraph(f"<b>{format_inr(tot_rev)}</b>", cell_bold_style),
            Paragraph(f"<b>{format_inr(tot_pay)}</b>", cell_bold_style),
            Paragraph("", cell_style),
            Paragraph(f"<b>{format_inr(tot_exp)}</b>", cell_bold_style),
            Paragraph(f"<b>{format_inr(tot_prof)}</b>", cell_bold_style),
            Paragraph(f"<b>{overall_margin:.1f}%</b>", cell_bold_style),
            Paragraph("", cell_style)
        ]
        table_data.append(summary_row)

    # Style Table
    report_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]

    # Alternating row background
    for row_idx in range(1, len(table_data) - 1):
        bg = colors.HexColor("#F8FAFC") if row_idx % 2 == 1 else colors.white
        t_style.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))

    # Highlight summary row
    last_idx = len(table_data) - 1
    t_style.append(("BACKGROUND", (0, last_idx), (-1, last_idx), colors.HexColor("#F1F5F9")))
    t_style.append(("LINEABOVE", (0, last_idx), (-1, last_idx), 1.5, colors.HexColor("#0F172A")))

    report_table.setStyle(TableStyle(t_style))
    elements.append(report_table)

    # Build Document with NumberedCanvas
    doc.build(elements, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def generate_excel_report(report_type, items, filters, generated_by="Administrator", is_superadmin=False):
    """
    Generates a beautifully styled Excel (.xlsx) report using openpyxl.
    """
    if not OPENPYXL_AVAILABLE:
        raise RuntimeError(f"openpyxl Excel engine is not available: {_openpyxl_err}. Please ensure openpyxl is installed via requirements.txt.")

    if report_type == "financial" and not is_superadmin:
        raise PermissionError("Access Forbidden: Financial reports are restricted to SUPERADMIN.")

    wb = openpyxl.Workbook()
    ws = wb.active

    # Title & Subtitle styling
    navy_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    orange_fill = PatternFill(start_color="EA580C", end_color="EA580C", fill_type="solid")
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    summary_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

    font_banner = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    font_subtitle = Font(name="Calibri", size=10, bold=False, color="F8FAFC")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_regular = Font(name="Calibri", size=10, color="000000")
    font_bold = Font(name="Calibri", size=10, bold=True, color="000000")

    border_thin = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )
    border_summary = Border(
        top=Side(style="medium", color="0F172A"),
        bottom=Side(style="double", color="0F172A"),
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1")
    )

    if report_type == "listings":
        ws.title = "Motorcycle Inventory"
        report_title = "SMR MOTORS — VEHICLE INVENTORY REPORT"
        headers = ["Bike ID", "Title", "Brand", "Model", "Year", "Listed Price (INR)", "Status", "Seller Name", "Seller Phone", "Kilometers", "Fuel Type", "Transmission", "Created Date"]
    elif report_type == "sold":
        ws.title = "Sold Out Vehicles"
        report_title = "SMR MOTORS — SOLD MOTORCYCLES REPORT"
        headers = ["Tx ID", "Bike ID", "Vehicle Title", "Brand", "Year", "Actual Sale Price (INR)", "Seller Agreed Payout (INR)", "Gross Margin (INR)", "Buyer Name", "Buyer Phone", "Seller Name", "Seller Phone", "Sold Date"]
    elif report_type == "financial":
        ws.title = "Financial Audit"
        report_title = "SMR MOTORS — CONFIDENTIAL FINANCIAL & PROFIT AUDIT"
        headers = ["Tx ID", "Bike ID", "Vehicle Title", "Brand", "Year", "Sale Price (INR)", "Seller Payout (INR)", "Service/Repairs (INR)", "Total Expenses (INR)", "Net Profit (INR)", "Margin %", "Sold Date", "Notes"]
    else:
        ws.title = "Report"
        report_title = f"SMR MOTORS — {report_type.upper()} REPORT"
        headers = ["ID", "Title", "Details", "Date"]

    num_cols = len(headers)

    # 1. Main Banner
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_cols)
    cell_b = ws.cell(row=1, column=1, value=report_title)
    cell_b.fill = navy_fill
    cell_b.font = font_banner
    cell_b.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    # 2. Metadata Subtitle
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sub_text = f"Generated On: {now_str}  |  Authorized Operator: {generated_by}  |  Filters: {filters}"
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=num_cols)
    cell_sub = ws.cell(row=2, column=1, value=sub_text)
    cell_sub.fill = orange_fill
    cell_sub.font = font_subtitle
    cell_sub.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    # 3. Blank row
    ws.row_dimensions[3].height = 8

    # 4. Table Headers (Row 4)
    for col_idx, h in enumerate(headers, 1):
        c = ws.cell(row=4, column=col_idx, value=h)
        c.fill = header_fill
        c.font = font_header
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border_thin
    ws.row_dimensions[4].height = 26

    # 5. Populate Data Rows
    current_row = 5

    if report_type == "listings":
        tot_val = 0.0
        for b in items:
            p = float(b.get("price") or 0)
            tot_val += p
            row_vals = [
                b.get("id"),
                b.get("title") or "",
                b.get("brand") or "",
                b.get("model") or "",
                b.get("year") or "",
                p,
                str(b.get("listing_status") or b.get("status") or "pending").title(),
                b.get("seller_name") or "",
                b.get("seller_phone") or "",
                int(b.get("kilometers_driven") or 0),
                b.get("fuel_type") or "Petrol",
                b.get("transmission") or "Manual",
                str(b.get("created_at") or "")[:10]
            ]
            for col_idx, val in enumerate(row_vals, 1):
                c = ws.cell(row=current_row, column=col_idx, value=val)
                c.font = font_regular
                c.border = border_thin
                if current_row % 2 == 0:
                    c.fill = zebra_fill
                if col_idx == 6:
                    c.number_format = '"₹"#,##0.00'
                if col_idx in (1, 5, 10):
                    c.alignment = Alignment(horizontal="center")
            current_row += 1

        # Summary Row
        sum_row = ws.cell(row=current_row, column=1, value="TOTAL")
        sum_row.font = font_bold
        sum_row.border = border_summary
        sum_row.fill = summary_fill

        cnt_cell = ws.cell(row=current_row, column=2, value=f"{len(items)} Vehicles")
        cnt_cell.font = font_bold
        cnt_cell.border = border_summary
        cnt_cell.fill = summary_fill

        for col_idx in range(3, num_cols + 1):
            c = ws.cell(row=current_row, column=col_idx)
            c.border = border_summary
            c.fill = summary_fill
            if col_idx == 6:
                c.value = tot_val
                c.font = font_bold
                c.number_format = '"₹"#,##0.00'

    elif report_type == "sold":
        tot_sale = 0.0
        tot_payout = 0.0
        tot_margin = 0.0
        for t in items:
            sale_p = float(t.get("actual_sale_price") or 0)
            payout_p = float(t.get("seller_payout") or 0)
            margin = float(t.get("realized_profit") or (sale_p - payout_p))
            tot_sale += sale_p
            tot_payout += payout_p
            tot_margin += margin

            row_vals = [
                t.get("id"),
                t.get("bike_id"),
                t.get("bike_title") or t.get("title") or "",
                t.get("brand") or "",
                t.get("year") or "",
                sale_p,
                payout_p if is_superadmin else "[RESTRICTED]",
                margin if is_superadmin else "[RESTRICTED]",
                t.get("buyer_name") or "",
                t.get("buyer_phone") or "",
                t.get("seller_name") or "",
                t.get("seller_phone") or "",
                str(t.get("sold_at") or t.get("created_at") or "")[:10]
            ]
            for col_idx, val in enumerate(row_vals, 1):
                c = ws.cell(row=current_row, column=col_idx, value=val)
                c.font = font_regular
                c.border = border_thin
                if current_row % 2 == 0:
                    c.fill = zebra_fill
                if col_idx in (6, 7, 8) and isinstance(val, (int, float)):
                    c.number_format = '"₹"#,##0.00'
                if col_idx in (1, 2, 5, 13):
                    c.alignment = Alignment(horizontal="center")
            current_row += 1

        # Summary Row
        ws.cell(row=current_row, column=1, value="TOTAL").font = font_bold
        ws.cell(row=current_row, column=3, value=f"{len(items)} Units Sold").font = font_bold
        for col_idx in range(1, num_cols + 1):
            c = ws.cell(row=current_row, column=col_idx)
            c.border = border_summary
            c.fill = summary_fill
            if col_idx == 6:
                c.value = tot_sale
                c.font = font_bold
                c.number_format = '"₹"#,##0.00'
            elif col_idx == 7:
                c.value = tot_payout if is_superadmin else "[RESTRICTED]"
                c.font = font_bold
                if is_superadmin: c.number_format = '"₹"#,##0.00'
            elif col_idx == 8:
                c.value = tot_margin if is_superadmin else "[RESTRICTED]"
                c.font = font_bold
                if is_superadmin: c.number_format = '"₹"#,##0.00'

    elif report_type == "financial":
        tot_rev = 0.0
        tot_pay = 0.0
        tot_rep = 0.0
        tot_exp = 0.0
        tot_prof = 0.0

        for t in items:
            rev = float(t.get("actual_sale_price") or 0)
            pay = float(t.get("seller_payout") or t.get("buying_price") or 0)
            rep_v = float(t.get("repair_expense") or 0)
            srv_v = float(t.get("service_expense") or 0)
            if rep_v > 0 and srv_v == rep_v and float(t.get("total_expenses") or 0) < (rep_v + srv_v):
                rep = rep_v
            else:
                rep = rep_v + srv_v
            exp = float(t.get("total_expenses") if t.get("total_expenses") is not None else (rep + float(t.get("other_expense") or 0)))
            prof = float(t.get("realized_profit") if t.get("realized_profit") is not None else (rev - pay - exp))
            m_pct = (prof / pay) if pay > 0 else 0.0

            tot_rev += rev
            tot_pay += pay
            tot_rep += rep
            tot_exp += exp
            tot_prof += prof

            row_vals = [
                t.get("id"),
                t.get("bike_id"),
                t.get("bike_title") or t.get("title") or "",
                t.get("brand") or "",
                t.get("year") or "",
                rev,
                pay,
                rep,
                exp,
                prof,
                m_pct,
                str(t.get("sold_at") or t.get("created_at") or "")[:10],
                t.get("notes") or ""
            ]
            for col_idx, val in enumerate(row_vals, 1):
                c = ws.cell(row=current_row, column=col_idx, value=val)
                c.font = font_regular
                c.border = border_thin
                if current_row % 2 == 0:
                    c.fill = zebra_fill
                if col_idx in (6, 7, 8, 9, 10):
                    c.number_format = '"₹"#,##0.00;[Red]-"₹"#,##0.00;"₹"0.00'
                elif col_idx == 11:
                    c.number_format = '0.0%'
                if col_idx in (1, 2, 5, 12):
                    c.alignment = Alignment(horizontal="center")
            current_row += 1

        overall_margin = (tot_prof / tot_pay) if tot_pay > 0 else 0.0
        ws.cell(row=current_row, column=1, value="TOTAL").font = font_bold
        ws.cell(row=current_row, column=3, value=f"{len(items)} Transactions").font = font_bold
        for col_idx in range(1, num_cols + 1):
            c = ws.cell(row=current_row, column=col_idx)
            c.border = border_summary
            c.fill = summary_fill
            if col_idx == 6:
                c.value = tot_rev
                c.font = font_bold
                c.number_format = '"₹"#,##0.00'
            elif col_idx == 7:
                c.value = tot_pay
                c.font = font_bold
                c.number_format = '"₹"#,##0.00'
            elif col_idx == 8:
                c.value = tot_rep
                c.font = font_bold
                c.number_format = '"₹"#,##0.00'
            elif col_idx == 9:
                c.value = tot_exp
                c.font = font_bold
                c.number_format = '"₹"#,##0.00'
            elif col_idx == 10:
                c.value = tot_prof
                c.font = font_bold
                c.number_format = '"₹"#,##0.00'
            elif col_idx == 11:
                c.value = overall_margin
                c.font = font_bold
                c.number_format = '0.0%'

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            # Skip title merged banner in width calculation
            if cell.row in (1, 2, 3):
                continue
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # Freeze panes at Row 5 so header row is always visible when scrolling
    ws.freeze_panes = "A5"

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
