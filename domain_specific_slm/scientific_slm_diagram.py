#!/usr/bin/env python3
"""
CAIO Diagram: Scientific SLM Comparison — Radar Overlay
Topic: scientific-slms
Type: Radar/spider overlay — comparing three models across operational dimensions
Output: caio-scientific-slms-diagram-3.png
"""

import math
from reportlab.lib.units import mm
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
TEAL = HexColor('#1A7A7A')
MUSTARD = HexColor('#C4952A')
BRICK = HexColor('#A04A2A')
TERRACOTTA = HexColor('#C4613A')
BRONZE = HexColor('#8C6E3A')
WARM_BLUE = HexColor('#2A5A8A')

# --- Font Registration ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-scientific-slms-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'


def polar_to_cart(cx, cy, r, angle_deg, n_axes, axis_idx):
    """Convert radar axis index and radius to cartesian coords."""
    angle = math.radians(90 - axis_idx * (360 / n_axes))
    return cx + r * math.cos(angle), cy + r * math.sin(angle)


def draw_diagram(c):
    """Main diagram drawing function."""
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W/2, H - 60, "Scientific SLM Comparison")

    # Subtitle
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 95, "ProtGPT2, AntibodyGPT, and CrystaLLM across operational dimensions")

    cx, cy = W/2, 520
    max_r = 300

    # Axes
    dimensions = [
        "Parameter Count\n(inverse — smaller is higher)",
        "Inference Speed\n(no GPU needed)",
        "Quantization\nBenefit",
        "Validation\nRigor",
        "Hardware\nAccessibility",
        "Domain\nSpecificity",
    ]
    n = len(dimensions)

    # Grid rings
    rings = [0.2, 0.4, 0.6, 0.8, 1.0]
    for ring_val in rings:
        r = max_r * ring_val
        c.setStrokeColor(HexColor('#E0E0E0'))
        c.setLineWidth(1)
        p = c.beginPath()
        for i in range(n):
            x, y = polar_to_cart(cx, cy, r, 0, n, i)
            if i == 0:
                p.moveTo(x, y)
            else:
                p.lineTo(x, y)
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    # Axis lines
    for i in range(n):
        x, y = polar_to_cart(cx, cy, max_r + 10, 0, n, i)
        c.setStrokeColor(HexColor('#C0C0C0'))
        c.setLineWidth(1)
        c.line(cx, cy, x, y)

    # Axis labels
    label_r = max_r + 55
    for i, dim in enumerate(dimensions):
        x, y = polar_to_cart(cx, cy, label_r, 0, n, i)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 11)
        dim_lines = dim.split('\n')
        for j, dl in enumerate(dim_lines):
            c.drawCentredString(x, y - j * 13, dl)

    # Model data (values 0-1)
    # ProtGPT2: 738M params (medium-low), very fast (no GPU), no quantization tested, perplexity-based validation, laptop-runnable, protein-only
    protgpt2_data = [0.55, 0.95, 0.3, 0.5, 0.95, 0.9]
    # AntibodyGPT: 151M-2.7B (variable), GPU needed, strong quantization benefit, ANARCI validation, needs GPU, antibody-specific
    antibody_data = [0.65, 0.45, 0.9, 0.85, 0.5, 0.95]
    # CrystaLLM: 25M (tiny), CPU-fast, not tested, rigorous CIF validation, very accessible, crystal-specific
    crystallm_data = [0.95, 0.9, 0.2, 0.9, 0.95, 0.85]

    models = [
        ("ProtGPT2", protgpt2_data, EMERALD),
        ("AntibodyGPT", antibody_data, BURGUNDY),
        ("CrystaLLM", crystallm_data, AMETHYST),
    ]

    for name, data, color in models:
        points = []
        for i, val in enumerate(data):
            r = max_r * val
            x, y = polar_to_cart(cx, cy, r, 0, n, i)
            points.append((x, y))

        # Filled polygon
        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            p.lineTo(x, y)
        p.close()
        c.setFillColor(color)
        c.setFillAlpha(0.15)
        c.setStrokeColor(color)
        c.setLineWidth(2.5)
        c.drawPath(p, stroke=1, fill=1)
        c.setFillAlpha(1.0)

        # Data points
        c.setFillColor(color)
        for x, y in points:
            c.circle(x, y, 5, stroke=0, fill=1)

    # Legend
    legend_x = 130
    legend_y = 150
    for i, (name, _, color) in enumerate(models):
        lx = legend_x + i * 250

        # Color swatch
        c.setFillColor(color)
        c.circle(lx, legend_y, 10, stroke=0, fill=1)

        # Name
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 14)
        c.drawString(lx + 18, legend_y - 6, name)

    # Bottom annotation
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(
        W/2, 45, "Each model excels in different operational dimensions — no single model dominates all axes")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()

    import subprocess
    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
