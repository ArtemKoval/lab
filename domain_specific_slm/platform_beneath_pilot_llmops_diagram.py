#!/usr/bin/env python3
"""
CAIO Diagram: The ML Platform Layer Stack
Topic: platform-beneath-the-pilot
Type: Concentric Rings (layered architecture)
Output: caio-platform-beneath-the-pilot-diagram-1.png
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
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')
TAUPE = HexColor('#8A7B6B')

# --- Font Registration ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio/caio-platform-beneath-the-pilot-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W/2, H - 80, "The ML Platform Layer Stack")

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 110, "Each layer is a prerequisite for the one above it — skip any, and everything above compounds fragility")

    # Centered circle — sized to fit between title and footer
    cx = W / 2
    cy = 560

    # Ring bands (outermost first for drawing)
    rings = [
        (460, 378, SAPPHIRE, "LLM SYSTEMS", "RAG  .  Prompt management  .  Vector stores",
         "Semantic evaluation  .  Guardrails"),
        (378, 296, AMETHYST, "APPLIED ML", "Feature engineering  .  Model training",
         "Validation  .  Hyperparameter tuning"),
        (296, 214, EMERALD, "PLATFORM CAPABILITIES",
         "Experiment tracking  .  Model registry", "Feature store  .  Pipelines  .  Serving"),
        (214, 132, BURGUNDY, "ORCHESTRATION",
         "Kubernetes  .  CI/CD  .  Observability", "Monitoring  .  Drift detection"),
        (132, 0,   NAVY,     "INFRASTRUCTURE",
         "Compute  .  Storage  .  Network", ""),
    ]

    # Draw rings from outermost to innermost (nested fills)
    for outer_r, inner_r, fill, title, d1, d2 in rings:
        c.setFillColor(fill)
        c.setStrokeColor(HexColor('#FFFFFF'))
        c.setLineWidth(4)
        c.circle(cx, cy, outer_r, stroke=1, fill=1)

    # Labels at 12 o'clock of each band
    for outer_r, inner_r, fill, title, d1, d2 in rings:
        if inner_r == 0:
            # Innermost — centered
            c.setFillColor(IVORY)
            c.setFont('Poppins-Bold', 22)
            c.drawCentredString(cx, cy + 10, title)
            c.setFont('Poppins', 12)
            c.drawCentredString(cx, cy - 18, d1)
        else:
            mid_r = (outer_r + inner_r) / 2
            title_y = cy + mid_r + 14
            c.setFillColor(IVORY)
            c.setFont('Poppins-Bold', 19)
            c.drawCentredString(cx, title_y, title)
            c.setFont('Poppins', 12)
            c.drawCentredString(cx, title_y - 20, d1)
            if d2:
                c.drawCentredString(cx, title_y - 36, d2)

    # Key insight below the circle — positioned clear of the rings (bottom of circle = cy - outer_r = 560 - 460 = 100)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(
        W/2, 75, "Read from the inside out — each inner layer is a prerequisite for every layer above it.")

    # Attribution
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(W/2, 40, "Art Koval  .  CAIO")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                   OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
