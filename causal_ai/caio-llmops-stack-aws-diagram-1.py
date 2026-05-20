#!/usr/bin/env python3
"""
CAIO Diagram: The LLMOps Stack on AWS
Topic: llmops-stack-aws
Type: Segmented wheel with central hub (5 operational domains around AWS Bedrock core,
      each annotated with AWS native services)
Output: caio-llmops-stack-aws-diagram-1.png
"""

import math
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette (CAIO standard) ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
UMBER = HexColor('#6B4226')
TAUPE = HexColor('#8A7B6B')
WHITE = HexColor('#FFFFFF')

# --- Font Registration ---
FONTS = '/usr/share/fonts/truetype/google-fonts'
pdfmetrics.registerFont(TTFont('Poppins', f'{FONTS}/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', f'{FONTS}/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', f'{FONTS}/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', f'{FONTS}/Poppins-Light.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Italic', f'{FONTS}/Poppins-Italic.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-llmops-stack-aws-diagram-1.png'
OUTPUT_PDF = '/tmp/_llmops_aws_stack.pdf'


def draw_diagram(c):
    """Main diagram drawing function."""
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title block
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 38)
    c.drawCentredString(W / 2, H - 80, "The LLMOps Stack on AWS")

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 17)
    c.drawCentredString(W / 2, H - 115,
                        "Five operational domains wrapping the generation core")

    # Geometry
    cx, cy = W / 2, H / 2 - 40
    outer_r = 425
    hub_r = 140

    # Sectors: (name, fill_color, [items with AWS services])
    sectors = [
        ('KNOWLEDGE', EMERALD, [
            'Bedrock Knowledge Bases',
            'OpenSearch Serverless',
            'Titan / Cohere embeddings',
            'S3 source documents',
            'Hybrid retrieval',
        ]),
        ('GUARDRAILS', BURGUNDY, [
            'Bedrock Guardrails',
            'Contextual grounding',
            'PII redaction',
            'Automated Reasoning',
        ]),
        ('PERFORMANCE', SAPPHIRE, [
            'Intelligent Prompt Routing',
            'Prompt caching',
            'Cross-region inference',
            'Provisioned throughput',
        ]),
        ('OBSERVABILITY', AMETHYST, [
            'CloudWatch metrics',
            'Model invocation logs',
            'X-Ray traces',
            'Cost attribution tags',
        ]),
        ('EVALUATION', UMBER, [
            'Bedrock Model Evaluation',
            'SageMaker Clarify',
            'RAGAS via Lambda',
        ]),
    ]

    n = len(sectors)
    sweep = 360.0 / n

    for i, (name, color, items) in enumerate(sectors):
        center_deg = 90 - i * sweep
        start_deg = center_deg - sweep / 2

        c.setFillColor(color)
        c.setStrokeColor(WHITE)
        c.setLineWidth(5)
        c.wedge(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                start_deg, sweep, stroke=1, fill=1)

        center_rad = math.radians(center_deg)

        # Column at sector centroid
        col_distance = (outer_r + hub_r) / 2
        col_x = cx + col_distance * math.cos(center_rad)
        col_y = cy + col_distance * math.sin(center_rad)

        n_items = len(items)
        name_height = 22
        item_line = 22
        gap_below_name = 26

        total_height = name_height + gap_below_name + n_items * item_line
        top_y = col_y + total_height / 2
        name_y = top_y - name_height + 2
        items_top_y = top_y - name_height - gap_below_name

        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 19)
        c.drawCentredString(col_x, name_y, name)

        underline_y = name_y - 6
        c.setStrokeColor(OCHRE)
        c.setLineWidth(1.5)
        c.line(col_x - 28, underline_y, col_x + 28, underline_y)

        c.setFillColor(IVORY)
        c.setFont('Poppins', 12)
        for j, item in enumerate(items):
            iy = items_top_y - j * item_line
            c.drawCentredString(col_x, iy, item)

    # Central hub — Bedrock as runtime
    c.setFillColor(NAVY)
    c.setStrokeColor(WHITE)
    c.setLineWidth(5)
    c.circle(cx, cy, hub_r, stroke=1, fill=1)

    c.setStrokeColor(OCHRE)
    c.setLineWidth(1.5)
    c.circle(cx, cy, hub_r - 12, stroke=1, fill=0)

    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 28, "AWS")
    c.drawCentredString(cx, cy + 2, "BEDROCK")

    c.setFillColor(OCHRE)
    c.setFont('Poppins-Medium', 12)
    c.drawCentredString(cx, cy - 22, "RUNTIME")

    c.setFillColor(IVORY)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(cx, cy - 50, "Claude · Nova · Llama · Mistral")

    # Bottom legend strip: business benefit per domain
    legend_y = 90
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 11)
    c.drawCentredString(W / 2, legend_y + 22, "BUSINESS BENEFIT")

    legend_items = [
        ('Knowledge', '50-90% hallucination reduction via RAG', EMERALD),
        ('Guardrails', '88% harmful content blocked', BURGUNDY),
        ('Performance', 'Up to 90% cost cut via prompt caching', SAPPHIRE),
        ('Observability', 'Per-trace cost and quality attribution', AMETHYST),
        ('Evaluation', 'Continuous regression detection', UMBER),
    ]

    col_width = W / 3
    row1 = legend_items[:3]
    row2 = legend_items[3:]

    row1_y = legend_y - 2
    for k, (label, tools, dot_color) in enumerate(row1):
        x_center = col_width * (k + 0.5)
        c.setFillColor(dot_color)
        c.circle(x_center - 165, row1_y + 4, 5, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 11)
        c.drawString(x_center - 153, row1_y + 1, label)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 10.5)
        c.drawString(x_center - 153, row1_y - 14, tools)

    row2_y = legend_y - 38
    col_width_2 = W / 2
    for k, (label, tools, dot_color) in enumerate(row2):
        x_center = col_width_2 * (k + 0.5)
        c.setFillColor(dot_color)
        c.circle(x_center - 170, row2_y + 4, 5, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 11)
        c.drawString(x_center - 158, row2_y + 1, label)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 10.5)
        c.drawString(x_center - 158, row2_y - 14, tools)

    c.setFillColor(TAUPE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 22, "Art Koval — Chief AI Officer Insights")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()

    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
