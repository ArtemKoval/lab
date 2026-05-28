#!/usr/bin/env python3
"""
CAIO Diagram: Optimizer Performance Profile across Benchmarks
Topic: gepa-prompt-evolution
Type: Radar / Spider Overlay
Output: caio-gepa-prompt-evolution-diagram-2.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
TAUPE = HexColor('#8A7B6B')
OCHRE = HexColor('#C49A2A')

# --- Fonts ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-gepa-prompt-evolution-diagram-2.png'
OUTPUT_PDF = '/tmp/_diag2_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W/2, H - 60, "Optimizer Performance Profile — Qwen3 8B")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W/2, H - 90, "Test-set scores across four benchmarks plus aggregate")

    # Radar geometry
    cx, cy = W/2, 520
    max_r = 290

    # Dimensions: 5 axes (Aggregate first, then 4 benchmarks)
    dims = [
        ("Aggregate", 100),
        ("HotpotQA", 100),
        ("IFBench", 60),
        ("HoVer", 80),
        ("PUPA", 100),
    ]
    n_axes = len(dims)

    # Series scores (Qwen3 8B test set, from Table 1)
    # Drawing order: largest polygon first so smaller render on top (painter's algorithm)
    series_list = [
        {
            'name': 'GEPA',
            'color': EMERALD,
            'fill_alpha': 0.30,
            'stroke_alpha': 1.0,
            'values': [61.28, 62.33, 38.61, 52.33, 91.85]
        },
        {
            'name': 'MIPROv2',
            'color': AMETHYST,
            'fill_alpha': 0.18,
            'stroke_alpha': 1.0,
            'values': [55.11, 55.33, 36.22, 47.33, 81.55]
        },
        {
            'name': 'GRPO (RL, 24,000 rollouts)',
            'color': BURGUNDY,
            'fill_alpha': 0.18,
            'stroke_alpha': 1.0,
            'values': [51.14, 43.33, 35.88, 38.67, 86.66]
        },
        {
            'name': 'Baseline',
            'color': TAUPE,
            'fill_alpha': 0.15,
            'stroke_alpha': 1.0,
            'values': [48.85, 42.33, 36.90, 35.33, 80.82]
        },
    ]

    # Max scale (normalize per axis using max_scale per dim)
    max_scales = [d[1] for d in dims]

    # Draw gridline polygons (concentric pentagons)
    c.setStrokeColor(TAUPE)
    c.setLineWidth(1)
    for ring_frac in [0.25, 0.5, 0.75, 1.0]:
        p = c.beginPath()
        for i in range(n_axes):
            angle = math.radians(90 - i * (360 / n_axes))
            r = max_r * ring_frac
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            if i == 0:
                p.moveTo(x, y)
            else:
                p.lineTo(x, y)
        p.close()
        c.setStrokeAlpha(0.4)
        c.drawPath(p, stroke=1, fill=0)
    c.setStrokeAlpha(1.0)

    # Axis spokes
    c.setStrokeColor(TAUPE)
    c.setLineWidth(1)
    c.setStrokeAlpha(0.5)
    for i in range(n_axes):
        angle = math.radians(90 - i * (360 / n_axes))
        x = cx + max_r * math.cos(angle)
        y = cy + max_r * math.sin(angle)
        c.line(cx, cy, x, y)
    c.setStrokeAlpha(1.0)

    # Draw series polygons (back-to-front: smaller area first wouldn't work since they cross — draw baseline first)
    for s in series_list:
        points = []
        for i, val in enumerate(s['values']):
            angle = math.radians(90 - i * (360 / n_axes))
            r = max_r * (val / max_scales[i])
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            p.lineTo(x, y)
        p.close()
        c.setFillAlpha(s['fill_alpha'])
        c.setStrokeAlpha(s['stroke_alpha'])
        c.setFillColor(s['color'])
        c.setStrokeColor(s['color'])
        c.setLineWidth(2.5)
        c.drawPath(p, stroke=1, fill=1)
    c.setFillAlpha(1.0)
    c.setStrokeAlpha(1.0)

    # Axis labels at outer ends (with quadrant-aware alignment)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    for i, (label, scale) in enumerate(dims):
        angle = math.radians(90 - i * (360 / n_axes))
        lx = cx + (max_r + 35) * math.cos(angle)
        ly = cy + (max_r + 35) * math.sin(angle)
        cos_v = math.cos(angle)
        if cos_v > 0.3:
            c.drawString(lx, ly - 5, label)
        elif cos_v < -0.3:
            c.drawRightString(lx, ly - 5, label)
        else:
            c.drawCentredString(lx, ly - 5, label)

        # Scale label below in smaller text
        c.setFont('Poppins-Light', 11)
        c.setFillColor(GRAPHITE)
        scale_label = f"(0–{scale})"
        if cos_v > 0.3:
            c.drawString(lx, ly - 22, scale_label)
        elif cos_v < -0.3:
            c.drawRightString(lx, ly - 22, scale_label)
        else:
            c.drawCentredString(lx, ly - 22, scale_label)
        c.setFont('Poppins-Bold', 16)
        c.setFillColor(NAVY)

    # Legend in lower-left corner (in conceptual order: Baseline → GEPA, not drawing order)
    legend_order = [
        ('Baseline', TAUPE),
        ('MIPROv2', AMETHYST),
        ('GRPO (RL, 24,000 rollouts)', BURGUNDY),
        ('GEPA', EMERALD),
    ]
    legend_x = 110
    legend_y = 230
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawString(legend_x, legend_y + 20, "Optimization Method")
    for i, (label, color) in enumerate(legend_order):
        # Color swatch
        c.setFillColor(color)
        c.setFillAlpha(0.6)
        c.rect(legend_x, legend_y - i * 26 - 12, 28, 16, stroke=0, fill=1)
        c.setFillAlpha(1.0)
        c.setStrokeColor(color)
        c.setLineWidth(1.5)
        c.rect(legend_x, legend_y - i * 26 - 12, 28, 16, stroke=1, fill=0)
        # Label
        c.setFillColor(NAVY)
        c.setFont('Poppins', 13)
        c.drawString(legend_x + 38, legend_y - i * 26 - 7, label)

    # Bottom attribution
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W/2, 60, "Agrawal et al., arXiv:2507.19457 — ICLR 2026 Oral. Test scores from Table 1. Axis scales reflect benchmark range.")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    import subprocess
    subprocess.run([
        'pdftoppm', '-png', '-r', '150', '-singlefile',
        OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
