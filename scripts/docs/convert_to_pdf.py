#!/usr/bin/env python3
"""
PDF Conversion Script for CodeSentinel External Documents
Converts markdown files to PDF while preserving formatting and links

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.
"""

import re
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import sys

def parse_markdown_to_elements(md_content):
    """Parse markdown content into ReportLab elements"""
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Center
        textColor=colors.darkblue
    )

    heading2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.darkblue
    )

    heading3_style = ParagraphStyle(
        'Heading3',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=15,
        textColor=colors.darkblue
    )

    normal_style = styles['Normal']
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=10,
        backColor=colors.lightgrey,
        borderPadding=5,
        leftIndent=20,
        rightIndent=20
    )

    # Split content into lines
    lines = md_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Headers
        if line.startswith('# '):
            elements.append(Paragraph(line[2:], title_style))
            elements.append(Spacer(1, 12))
        elif line.startswith('## '):
            elements.append(Paragraph(line[3:], heading2_style))
            elements.append(Spacer(1, 12))
        elif line.startswith('### '):
            elements.append(Paragraph(line[4:], heading3_style))
            elements.append(Spacer(1, 12))

        # Code blocks
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code_content = '<br/>'.join(code_lines)
            elements.append(Paragraph(f'<code>{code_content}</code>', code_style))
            elements.append(Spacer(1, 12))

        # Tables (basic support)
        elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1] and re.match(r'^\s*\|.*\|\s*$', lines[i + 1]):
            table_data = []
            # Header row
            header_cells = [cell.strip() for cell in line.split('|')[1:-1]]
            table_data.append(header_cells)

            # Separator row
            i += 1

            # Data rows
            i += 1
            while i < len(lines) and '|' in lines[i]:
                row_cells = [cell.strip() for cell in lines[i].split('|')[1:-1]]
                if row_cells and any(cell for cell in row_cells):
                    table_data.append(row_cells)
                else:
                    break
                i += 1
            i -= 1  # Adjust for the outer loop

            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 12))

        # Lists
        elif line.startswith('- ') or line.startswith('* '):
            list_items = []
            while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ')):
                item_text = lines[i].strip()[2:]
                list_items.append(f"• {item_text}")
                i += 1
            i -= 1  # Adjust for the outer loop
            for item in list_items:
                elements.append(Paragraph(item, normal_style))
                elements.append(Spacer(1, 6))

        # Numbered lists
        elif re.match(r'^\d+\.\s', line):
            list_items = []
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                match = re.match(r'^\d+\.\s(.*)', lines[i].strip())
                if match:
                    item_text = match.group(1)
                    list_items.append(item_text)
                i += 1
            i -= 1  # Adjust for the outer loop
            for idx, item in enumerate(list_items, 1):
                elements.append(Paragraph(f"{idx}. {item}", normal_style))
                elements.append(Spacer(1, 6))

        # Regular paragraphs
        elif line:
            # Handle inline code and links
            line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
            # Convert markdown links to plain text (remove the URL part)
            line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', line)
            # Remove internal reference links like [text](#anchor)
            line = re.sub(r'\[([^\]]+)\]\(#([^)]+)\)', r'\1', line)
            elements.append(Paragraph(line, normal_style))
            elements.append(Spacer(1, 12))

        i += 1

    return elements

def convert_md_to_pdf(md_file_path, pdf_file_path):
    """Convert a markdown file to PDF with proper styling"""

    # Read markdown content
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_file_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Parse markdown to elements
    elements = parse_markdown_to_elements(md_content)

    # Build PDF
    doc.build(elements)
    print(f"Successfully converted {md_file_path} to {pdf_file_path}")

def main():
    """Main conversion function"""
    if len(sys.argv) != 3:
        print("Usage: python convert_to_pdf.py <input_md_file> <output_pdf_file>")
        sys.exit(1)

    md_file = sys.argv[1]
    pdf_file = sys.argv[2]

    if not Path(md_file).exists():
        print(f"Error: Input file {md_file} does not exist")
        sys.exit(1)

    try:
        convert_md_to_pdf(md_file, pdf_file)
    except Exception as e:
        print(f"Error converting {md_file} to PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
