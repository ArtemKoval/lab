#!/usr/bin/env python3
"""
CAIO Diagram: The Five-Step Causal Inference Workflow
Topic: caio-causal-inference-workflow
Type: Circular flow (process wheel) — closed loop with five numbered nodes connected by arcs
Output: caio-causal-inference-workflow-diagram-1.png
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
TEAL = HexColor('#1A7A7A')
MUSTARD = HexColor('#C4952A')
TAUPE = HexColor('#8A7B6B')
WHITE = HexColor('#FFFFFF')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-causal-inference-workflow-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'

STEPS = [
    {'num': 1, 'title': 'Specify Query', 'desc': 'State the causal\nquantity of interest', 'color': NAVY},
    {'num': 2, 'title': 'Encode Model', 'desc': 'Express assumptions\nas a causal DAG', 'color': SAPPHIRE},
    {'num': 3, 'title': 'Identify', 'desc': 'Recover the quantity\nfrom observable data', 'color': EMERALD},
    {'num': 4, 'title': 'Estimate', 'desc': 'Apply statistical\nor ML estimator', 'color': BURGUNDY},
    {'num': 5, 'title': 'Refute', 'desc': 'Actively attempt\nto break the result', 'color': AMETHYST},
]


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W / 2, H - 75, 'The Five-Step Causal Inference Workflow')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 110, 'Each step makes assumptions explicit; refutation closes the loop')

    cx, cy = W / 2, H / 2 - 30
    orbit_r = 240
    node_r = 78
    label_r = orbit_r + node_r + 70  # 388 — well clear of node edges

    n = len(STEPS)
    angle_per = 360 / n

    positions = []
    for i in range(n):
        angle_deg = 90 - i * angle_per
        angle_rad = math.radians(angle_deg)
        x = cx + orbit_r * math.cos(angle_rad)
        y = cy + orbit_r * math.sin(angle_rad)
        positions.append((x, y, angle_deg, angle_rad))

    # Connector arcs
    gap_deg = math.degrees(math.atan2(node_r * 1.05, orbit_r))
    c.setStrokeColor(TAUPE)
    c.setLineWidth(3)
    for i in range(n):
        start_angle = 90 - i * angle_per - gap_deg
        end_angle = 90 - (i + 1) * angle_per + gap_deg
        extent = end_angle - start_angle
        c.arc(
            cx - orbit_r, cy - orbit_r,
            cx + orbit_r, cy + orbit_r,
            start_angle, extent
        )
        # Arrowhead at end
        end_rad = math.radians(end_angle)
        ex = cx + orbit_r * math.cos(end_rad)
        ey = cy + orbit_r * math.sin(end_rad)
        # Clockwise tangent direction
        tx = math.sin(end_rad)
        ty = -math.cos(end_rad)
        ah = 13
        c.setFillColor(TAUPE)
        p = c.beginPath()
        p.moveTo(ex + tx * 4, ey + ty * 4)
        p.lineTo(ex - tx * ah - ty * (ah * 0.5), ey - ty * ah + tx * (ah * 0.5))
        p.lineTo(ex - tx * ah + ty * (ah * 0.5), ey - ty * ah - tx * (ah * 0.5))
        p.close()
        c.drawPath(p, stroke=0, fill=1)

    # Draw nodes
    for i, (x, y, angle_deg, angle_rad) in enumerate(positions):
        step = STEPS[i]
        c.setFillColor(step['color'])
        c.setStrokeColor(WHITE)
        c.setLineWidth(3)
        c.circle(x, y, node_r, stroke=1, fill=1)

        # Number
        c.setFillColor(MUSTARD)
        c.setFont('Poppins-Bold', 34)
        c.drawCentredString(x, y + 4, str(step['num']))

        # Title inside node
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 12)
        c.drawCentredString(x, y - 22, step['title'])

        # Description radially outside the node
        lx = cx + label_r * math.cos(angle_rad)
        ly = cy + label_r * math.sin(angle_rad)

        c.setFillColor(NAVY)
        c.setFont('Poppins', 14)
        desc_lines = step['desc'].split('\n')
        line_height = 18
        total_h = (len(desc_lines) - 1) * line_height
        for j, line in enumerate(desc_lines):
            y_offset = total_h / 2 - j * line_height
            c.drawCentredString(lx, ly + y_offset - 4, line)

    # Center hub
    hub_r = 70
    c.setFillColor(IVORY)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2)
    c.circle(cx, cy, hub_r, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(cx, cy + 14, 'Decision-Grade')
    c.drawCentredString(cx, cy - 2, 'AI Workflow')
    c.setFont('Poppins-Light', 10)
    c.setFillColor(GRAPHITE)
    c.drawCentredString(cx, cy - 22, 'DoWhy / PyWhy')

    # Footer
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 40, 'Five-step workflow per Sharma & Kıcıman, "DoWhy: An End-to-End Library for Causal Inference"')


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
