import re
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and display the total page count
    and render professional headers/footers.
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # 1. Running Header (except on page 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#4A5568"))
            self.drawString(54, 748, "SMART LENDER")
            
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#718096"))
            self.drawRightString(letter[0] - 54, 748, "Project Documentation")
            
            # Header line
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 740, letter[0] - 54, 740)
            
        # 2. Running Footer (on all pages)
        # Footer line
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 48, letter[0] - 54, 48)
        
        # Left footer
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#A0AEC0"))
        self.drawString(54, 34, "Confidential — Internal Use Only")
        
        # Right footer: Page X of Y
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawRightString(letter[0] - 54, 34, page_text)
        
        self.restoreState()

def convert_md_inline_tags(text):
    # Escape ampersands not part of HTML entities
    text = text.replace('&', '&amp;')
    text = text.replace('&amp;amp;', '&amp;')
    text = text.replace('&amp;bull;', '&bull;')
    text = text.replace('&amp;nbsp;', '&nbsp;')
    text = text.replace('&amp;lt;', '&lt;')
    text = text.replace('&amp;gt;', '&gt;')
    
    # Bold: **text** -> <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Italic: *text* -> <i>text</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Inline code: `code` -> <font face="Courier" color="#C0392B"><b>\1</b></font>
    text = re.sub(r'`(.*?)`', r'<font face="Courier" color="#C0392B"><b>\1</b></font>', text)
    # Links: [text](url) -> <a href="\2" color="#2A4B7C"><u>\1</u></a>
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" color="#2A4B7C"><u>\1</u></a>', text)
    return text

def create_code_block(code_text, lang, styles):
    p_style = ParagraphStyle(
        name='CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1A202C')
    )
    p = Preformatted(code_text, p_style)
    
    t = Table([[p]], colWidths=[504])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t

def create_table(headers, rows, styles):
    num_cols = len(headers)
    
    if num_cols == 2:
        if headers[0] == "Name" and headers[1] == "Role":
            col_widths = [180, 324]
        else:
            col_widths = [140, 364]
    elif num_cols == 3:
        if headers[0] == "Model":
            col_widths = [160, 172, 172]
        elif headers[0] == "Component":
            col_widths = [140, 110, 254]
        else:
            col_widths = [140, 110, 254]
    else:
        col_widths = [504 / num_cols] * num_cols
        
    header_style = ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )
    
    cell_style = ParagraphStyle(
        name='TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#2D3748')
    )
    
    data = []
    data.append([Paragraph(h, header_style) for h in headers])
    
    for row in rows:
        formatted_row = []
        for cell in row:
            formatted_row.append(Paragraph(cell, cell_style))
        data.append(formatted_row)
        
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A2B4C')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t

def parse_markdown_robust(md_content, styles):
    flowables = []
    lines = md_content.split('\n')
    
    current_block = []
    state = "NONE"
    code_lang = ""
    
    def flush_block():
        nonlocal current_block, state, code_lang
        if not current_block:
            return
            
        block_text = '\n'.join(current_block)
        
        if state == "CODE":
            flowables.append(create_code_block(block_text, code_lang, styles))
        elif state == "TABLE":
            headers = []
            rows = []
            for line in current_block:
                parts = [p.strip() for p in line.split('|')]
                if line.startswith('|'):
                    parts = parts[1:]
                if line.endswith('|'):
                    parts = parts[:-1]
                
                if all(re.match(r'^[-:]+$', p) for p in parts) and len(parts) > 0:
                    continue
                if not headers:
                    headers = parts
                else:
                    row = [convert_md_inline_tags(p) for p in parts]
                    row = row[:len(headers)]
                    while len(row) < len(headers):
                        row.append("")
                    rows.append(row)
            if headers:
                flowables.append(create_table(headers, rows, styles))
        elif state == "LIST":
            for line in current_block:
                line_stripped = line.strip()
                if line_stripped.startswith('- ') or line_stripped.startswith('* '):
                    txt = convert_md_inline_tags(line_stripped[2:])
                    flowables.append(Paragraph(f"&bull;&nbsp;&nbsp;{txt}", styles['DocBullet']))
                elif re.match(r'^\d+\.\s', line_stripped):
                    match = re.match(r'^(\d+)\.\s(.*)', line_stripped)
                    num = match.group(1)
                    txt = convert_md_inline_tags(match.group(2))
                    flowables.append(Paragraph(f"{num}.&nbsp;&nbsp;{txt}", styles['DocNumbered']))
            flowables.append(Spacer(1, 4))
        elif state == "PARAGRAPH":
            full_text = " ".join([l.strip() for l in current_block])
            full_text = convert_md_inline_tags(full_text)
            
            if full_text.startswith('<b>') and full_text.endswith('</b>'):
                flowables.append(Paragraph(full_text, styles['DocSubtitle']))
            else:
                flowables.append(Paragraph(full_text, styles['DocBody']))
            flowables.append(Spacer(1, 6))
            
        current_block = []
        state = "NONE"
        code_lang = ""

    i = 0
    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()
        
        if state == "CODE":
            if line_stripped == "```":
                flush_block()
            else:
                current_block.append(line)
            i += 1
            continue
            
        if line_stripped.startswith("```"):
            flush_block()
            state = "CODE"
            code_lang = line_stripped[3:].strip()
            i += 1
            continue
            
        if not line_stripped:
            if state != "NONE":
                flush_block()
            i += 1
            continue
            
        if line_stripped == "---":
            flush_block()
            flowables.append(Spacer(1, 6))
            flowables.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#CBD5E1'), spaceBefore=4, spaceAfter=10))
            i += 1
            continue
            
        if line_stripped.startswith("### "):
            flush_block()
            text = convert_md_inline_tags(line_stripped[4:])
            flowables.append(Paragraph(text, styles['DocH3']))
            flowables.append(Spacer(1, 4))
            i += 1
            continue
        elif line_stripped.startswith("## "):
            flush_block()
            text = convert_md_inline_tags(line_stripped[3:])
            flowables.append(Paragraph(text, styles['DocH2']))
            flowables.append(Spacer(1, 6))
            i += 1
            continue
        elif line_stripped.startswith("# "):
            flush_block()
            text = convert_md_inline_tags(line_stripped[2:])
            flowables.append(Paragraph(text, styles['DocH1']))
            flowables.append(Spacer(1, 8))
            i += 1
            continue
            
        if line_stripped.startswith("|"):
            if state != "TABLE":
                flush_block()
                state = "TABLE"
            current_block.append(line_stripped)
            i += 1
            continue
            
        if line_stripped.startswith("- ") or line_stripped.startswith('* ') or re.match(r'^\d+\.\s', line_stripped):
            if state != "LIST":
                flush_block()
                state = "LIST"
            current_block.append(line)
            i += 1
            continue
            
        if state != "PARAGRAPH":
            flush_block()
            state = "PARAGRAPH"
        current_block.append(line)
        i += 1
        
    flush_block()
    return flowables

def main():
    doc_path = "docs/Smart_Lender_Project_Documentation.md"
    pdf_path = "docs/Smart_Lender_Project_Documentation.pdf"
    
    if not os.path.exists(doc_path):
        print(f"Error: {doc_path} not found.")
        sys.exit(1)
        
    with open(doc_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
        
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=64
    )
    
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='DocH1',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1A2B4C'),
        spaceBefore=14,
        spaceAfter=10,
        keepWithNext=True
    ))
    
    styles.add(ParagraphStyle(
        name='DocH2',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#2A4B7C'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    ))
    
    styles.add(ParagraphStyle(
        name='DocH3',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2D3748'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    ))
    
    styles.add(ParagraphStyle(
        name='DocBody',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='DocSubtitle',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#4A5568'),
        alignment=1,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='DocBullet',
        parent=styles['DocBody'],
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    ))
    
    styles.add(ParagraphStyle(
        name='DocNumbered',
        parent=styles['DocBody'],
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    ))
    
    flowables = parse_markdown_robust(md_content, styles)
    
    doc.build(flowables, canvasmaker=NumberedCanvas)
    print(f"Success: Generated PDF at {pdf_path}")

if __name__ == "__main__":
    main()
