#!/usr/bin/env python3
"""
CAIO Diagram: The Platform-First Stack
Topic: observable-agents
Type: Concentric rings - durable control-plane core, interchangeable deployment outer layer
Output: caio-observable-agents-diagram-2.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TAUPE = HexColor('#8A7B6B')
MUSTARD = HexColor('#C4952A')

pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-observable-agents-diagram-2.png'
OUTPUT_PDF = '/tmp/_d2.pdf'


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W / 2, H - 70, "The Platform-First Stack")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 102, "The control plane is the durable asset. The cloud beneath it is an interchangeable target.")

    cx, cy = W / 2, (H - 150) / 2 + 30

    # Draw largest first so inner rings render on top
    r_outer, r_mid, r_core = 410, 280, 165

    # Outer ring (deployment targets) - Taupe
    c.setFillColor(TAUPE)
    c.circle(cx, cy, r_outer, stroke=0, fill=1)
    # Mid ring (portable platform) - Emerald
    c.setFillColor(EMERALD)
    c.circle(cx, cy, r_mid, stroke=0, fill=1)
    # Core (control plane) - Navy
    c.setFillColor(NAVY)
    c.circle(cx, cy, r_core, stroke=0, fill=1)

    # thin Ivory separators for ring distinction
    c.setStrokeColor(IVORY)
    c.setLineWidth(3)
    for r in (r_outer, r_mid, r_core):
        c.circle(cx, cy, r, stroke=1, fill=0)

    # --- Core label (Ivory on Navy) ---
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 21)
    c.drawCentredString(cx, cy + 30, "CONTROL PLANE")
    c.setFont('Poppins', 15)
    c.drawCentredString(cx, cy + 6, "Tracing · Evaluation")
    c.drawCentredString(cx, cy - 14, "Optimization (GEPA)")
    c.setFillColor(MUSTARD)
    c.setFont('Poppins-Medium', 15)
    c.drawCentredString(cx, cy - 44, "THE DURABLE ASSET")

    # --- Mid band label (Ivory on Emerald), near top of band ---
    mid_band_y = cy + (r_mid + r_core) / 2
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(cx, mid_band_y + 4, "PORTABLE PLATFORM")
    c.setFont('Poppins', 14)
    c.drawCentredString(cx, mid_band_y - 18, "Kubernetes · MLflow · IDP")
    # bottom of mid band echo
    c.setFont('Poppins', 14)
    c.setFillColor(IVORY)
    c.drawCentredString(cx, cy - (r_mid + r_core) / 2 - 6, "open, exportable trace format")

    # --- Outer band label (Navy on Taupe) near top of band ---
    outer_band_y = cy + (r_outer + r_mid) / 2
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(cx, outer_band_y + 6, "DEPLOYMENT TARGETS")
    c.setFont('Poppins', 13)
    c.drawCentredString(cx, outer_band_y - 16, "interchangeable / no lock-in")

    # Four target badges around the outer band (N-E-S-W diagonal positions)
    targets = [("On-Prem GPU", 135), ("AWS SageMaker", 45), ("Azure", -45), ("GCP", -135)]
    band_r = (r_outer + r_mid) / 2
    for label, deg in targets:
        ang = math.radians(deg)
        bx = cx + band_r * math.cos(ang)
        by = cy + band_r * math.sin(ang)
        c.setFillColor(NAVY)
        c.circle(bx, by, 58, stroke=0, fill=1)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2)
        c.circle(bx, by, 58, stroke=1, fill=0)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Medium', 13)
        # wrap two-word labels onto two lines
        words = label.split()
        if len(words) == 2:
            c.drawCentredString(bx, by + 4, words[0])
            c.drawCentredString(bx, by - 14, words[1])
        else:
            c.drawCentredString(bx, by - 5, label)


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    import subprocess
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                    OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
