#!/usr/bin/env python3
"""
CAIO Diagram: Fine-Tuning Techniques Compared
Topic: domain-fine-tuning
Type: Radar Overlay (multi-dimensional comparison)
Output: caio-domain-fine-tuning-diagram-2.png
"""
import math
import subprocess
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
TAUPE = HexColor('#8A7B6B')
OCHRE = HexColor('#C49A2A')
MUSTARD = HexColor('#C4952A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
TERRACOTTA = HexColor('#C4613A')
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')
WHITE = HexColor('#FFFFFF')

pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-domain-fine-tuning-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2.pdf'


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(
        W / 2, H - 70, 'Fine-Tuning Techniques: Enterprise Tradeoffs')

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 100, 'Eight dimensions. Three strategies. The right choice depends on the deployment context.')

    cx, cy = W / 2, 580
    max_r = 320
    n_axes = 8
    dimensions = [
        'Memory efficiency',
        'Train speed',
        'Quality retention',
        'Catastrophic-forgetting safety',
        'Inference overhead',
        'Sample efficiency',
        'Tooling maturity',
        'Cost (cloud)',
    ]
    # Scale 1-5 (5 = best)
    techniques = [
        {
            'name': 'Full SFT',
            'short': 'Full supervised fine-tune',
            'color': BURGUNDY,
            'scores': [1, 1, 5, 1, 5, 4, 5, 1],
        },
        {
            'name': 'PEFT (LoRA / QLoRA / DoRA)',
            'short': 'Adapter-based default',
            'color': EMERALD,
            'scores': [5, 4, 4, 4, 4, 5, 5, 5],
        },
        {
            'name': 'RL post-train (GRPO)',
            'short': 'For verifiable rewards',
            'color': SAPPHIRE,
            'scores': [3, 1, 5, 4, 5, 2, 3, 2],
        },
    ]

    # Gridlines (octagonal)
    c.setStrokeColor(TAUPE)
    c.setLineWidth(0.8)
    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(n_axes):
            ang = math.radians(90 - i * (360 / n_axes))
            r = max_r * level
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        path = c.beginPath()
        path.moveTo(*pts[0])
        for p in pts[1:]:
            path.lineTo(*p)
        path.close()
        c.drawPath(path, stroke=1, fill=0)

    # Axes
    c.setStrokeColor(TAUPE)
    c.setLineWidth(0.6)
    for i in range(n_axes):
        ang = math.radians(90 - i * (360 / n_axes))
        c.line(cx, cy, cx + max_r * math.cos(ang), cy + max_r * math.sin(ang))

    def draw_polygon(scores, color, alpha):
        pts = []
        for i, s in enumerate(scores):
            ang = math.radians(90 - i * (360 / n_axes))
            r = max_r * (s / 5)
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        path = c.beginPath()
        path.moveTo(*pts[0])
        for p in pts[1:]:
            path.lineTo(*p)
        path.close()
        c.setFillAlpha(alpha)
        c.setFillColor(color)
        c.setStrokeColor(color)
        c.setLineWidth(2.5)
        c.setStrokeAlpha(0.85)
        c.drawPath(path, stroke=1, fill=1)
        c.setFillAlpha(1.0)
        c.setStrokeAlpha(1.0)
        for px, py in pts:
            c.setFillColor(color)
            c.circle(px, py, 4, stroke=0, fill=1)

    for t in techniques:
        draw_polygon(t['scores'], t['color'], 0.20)

    # Axis labels
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 14)
    for i, dim in enumerate(dimensions):
        ang_deg = 90 - i * (360 / n_axes)
        ang = math.radians(ang_deg)
        lr = max_r + 38
        lx = cx + lr * math.cos(ang)
        ly = cy + lr * math.sin(ang)
        if abs(math.cos(ang)) < 0.2:
            # top or bottom — split into 2 lines if long
            words = dim.split()
            if len(words) > 1:
                mid = len(words) // 2
                line1 = ' '.join(words[:mid])
                line2 = ' '.join(words[mid:])
                if math.sin(ang) > 0:
                    c.drawCentredString(lx, ly + 6, line1)
                    c.drawCentredString(lx, ly - 12, line2)
                else:
                    c.drawCentredString(lx, ly + 6, line1)
                    c.drawCentredString(lx, ly - 12, line2)
            else:
                c.drawCentredString(lx, ly, dim)
        elif math.cos(ang) > 0:
            c.drawString(lx, ly - 4, dim)
        else:
            c.drawRightString(lx, ly - 4, dim)

    # Legend (right side)
    legend_x = 1230
    legend_y = 720
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawString(legend_x, legend_y + 60, 'Strategies')
    for i, t in enumerate(techniques):
        ly = legend_y - i * 56
        c.setFillColor(t['color'])
        c.circle(legend_x + 14, ly, 13, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 14)
        c.drawString(legend_x + 36, ly + 2, t['name'])
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 12)
        c.drawString(legend_x + 36, ly - 16, t['short'])

    # Decision footer
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 13)
    c.drawCentredString(
        W / 2, 100, 'Default: QLoRA + DoRA, rank 16, alpha 32, all-linear targets, lr 2e-4, 1-3 epochs.')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(
        W / 2, 78, 'Full SFT only when forgetting is acceptable. GRPO when verifiable rewards exist.')
    c.drawCentredString(
        W / 2, 60, 'Over 80% of HuggingFace fine-tuning jobs now use LoRA or QLoRA.')


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f'Rendered: {OUTPUT_PNG}')


if __name__ == '__main__':
    main()
