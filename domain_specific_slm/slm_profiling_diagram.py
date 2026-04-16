#!/usr/bin/env python3
"""
CAIO Diagram: The Profiling-Optimization Loop
Topic: model-profiling
Type: Circular Flow (Process Wheel)
Output: caio-model-profiling-diagram-2.png
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
BRICK = HexColor('#A04A2A')
TERRACOTTA = HexColor('#C4613A')
BRONZE = HexColor('#8C6E3A')

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
OUTPUT_PNG = '/home/claude/caio-model-profiling-diagram-2.png'
OUTPUT_PDF = '/tmp/_d2_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W / 2, H - 70, "The Profiling-Optimization Loop")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(
        W / 2, H - 100, "Each profiling pass surfaces the next bottleneck, which drives the next optimization pass")

    # Layout
    cx, cy = W / 2, 540
    orbit_r = 290
    node_r = 95

    steps = [
        ("1", "Profile", "Capture operator\nduration and counts", EMERALD),
        ("2", "Identify", "Find the bottleneck\nin the graph", SAPPHIRE),
        ("3", "Optimize", "Apply fusion and\nquantization", AMETHYST),
        ("4", "Validate", "Confirm accuracy\nis preserved", BURGUNDY),
        ("5", "Benchmark", "Measure the\nnew baseline", TEAL),
    ]

    n = len(steps)
    positions = []
    for i in range(n):
        angle = math.radians(90 - i * (360 / n))
        x = cx + orbit_r * math.cos(angle)
        y = cy + orbit_r * math.sin(angle)
        positions.append((x, y))

    # Draw curved connectors between consecutive nodes (along the orbit)
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(2.5)
    arc_gap = 10  # gap between node edge and arc end
    for i in range(n):
        x1, y1 = positions[i]
        x2, y2 = positions[(i + 1) % n]
        # Angles from centre
        a1 = math.atan2(y1 - cy, x1 - cx)
        a2 = math.atan2(y2 - cy, x2 - cx)
        # Normalise so that a2 is less than a1 (we go clockwise)
        if a2 > a1:
            a2 -= 2 * math.pi
        # Shorten the arc on each side by a small angular amount
        angular_gap = (node_r + arc_gap) / orbit_r
        a1_adj = a1 - angular_gap
        a2_adj = a2 + angular_gap
        # Draw arc as polyline
        steps_arc = 40
        path = c.beginPath()
        for s in range(steps_arc + 1):
            t = s / steps_arc
            ang = a1_adj + (a2_adj - a1_adj) * t
            px = cx + orbit_r * math.cos(ang)
            py = cy + orbit_r * math.sin(ang)
            if s == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        c.drawPath(path, stroke=1, fill=0)

        # Arrowhead at end — replaced with small circle marker (no arrow chars)
        end_ang = a2_adj
        mx = cx + orbit_r * math.cos(end_ang)
        my = cy + orbit_r * math.sin(end_ang)
        c.setFillColor(GRAPHITE)
        c.circle(mx, my, 6, stroke=0, fill=1)

    # Draw nodes on top
    for (x, y), (num, title, subtitle, color) in zip(positions, steps):
        c.setFillColor(color)
        c.circle(x, y, node_r, stroke=0, fill=1)
        # Number
        c.setFillColor(OCHRE)
        c.setFont('Poppins-Bold', 26)
        c.drawCentredString(x, y + 28, num)
        # Title
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 20)
        c.drawCentredString(x, y + 2, title)
        # Subtitle
        c.setFont('Poppins-Light', 11)
        for idx, line in enumerate(subtitle.split("\n")):
            c.drawCentredString(x, y - 22 - idx * 14, line)

    # Central text
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 18, "Continuous")
    c.drawCentredString(cx, cy - 10, "Runtime")
    c.drawCentredString(cx, cy - 38, "Governance")


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
