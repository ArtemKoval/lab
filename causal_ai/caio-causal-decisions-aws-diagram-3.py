#!/usr/bin/env python3
"""
CAIO Diagram: The Causal Hierarchy of Enterprise Decisions on AWS
Topic: causal-decisions-aws
Type: Concentric rings (Pearl's 3-level hierarchy with AWS context per level)
Output: caio-causal-decisions-aws-diagram-3.png
"""

import math
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
TAUPE = HexColor('#8A7B6B')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
MUSTARD = HexColor('#C4952A')
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')
BRONZE = HexColor('#8C6E3A')
TERRACOTTA = HexColor('#C4613A')

# --- Fonts ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-causal-decisions-aws-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W / 2, H - 70, "The Causal Hierarchy of Enterprise Decisions")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 100, "Three levels of reasoning — mapped to where they live in an AWS decision stack")

    # --- Concentric rings ---
    # Position the rings on the LEFT side so we have room for AWS context legend on the right
    cx, cy = 530, 570
    rings = [
        # (outer_radius, color, level_short, level_long, query_form)
        (380, TAUPE,    "L1", "Association",     "P(Y | X)"),
        (270, AMETHYST, "L2", "Intervention",    "P(Y | do(X))"),
        (165, EMERALD,  "L3", "Counterfactual",  "P(Y_x | X', Y')"),
    ]

    # Draw rings (largest first so they nest correctly)
    for r, color, _, _, _ in rings:
        c.setFillColor(color)
        c.circle(cx, cy, r, stroke=0, fill=1)

    # L3 inner label (Emerald ring, innermost)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 24)
    c.drawCentredString(cx, cy + 30, "L3")
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(cx, cy + 5, "Counterfactual")
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(cx, cy - 20, "what would have")
    c.drawCentredString(cx, cy - 36, "been if...")
    c.setFillColor(OCHRE)
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(cx, cy - 62, "P(Y_x | X', Y')")

    # L2 label — placed on Amethyst ring (upper portion)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 210, "L2")
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(cx, cy + 187, "Intervention")
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(cx, cy + 167, "what if we act?")
    c.setFillColor(OCHRE)
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(cx, cy + 145, "P(Y | do(X))")

    # L1 label — outermost (Taupe ring, upper). All elements live in r=270..380 band.
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 358, "L1")
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(cx, cy + 336, "Association")
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(cx, cy + 316, "what tends to happen?")
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(cx, cy + 294, "P(Y | X)")

    # --- Right-side AWS context panel ---
    panel_x = 1010
    panel_y_top = H - 180
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 20)
    c.drawString(panel_x, panel_y_top, "Where each level lives on AWS")

    levels = [
        (TAUPE,    "L1  Association",
         "Standard SageMaker recommenders.",
         "Personalize default contextual bandits.",
         "Offline lift numbers without confounder adjustment.",
         "Most enterprise AI ships here.",
         BURGUNDY),
        (AMETHYST, "L2  Intervention",
         "Causal bandits with do-operator queries.",
         "A/B tests as deliberate interventions.",
         "Bedrock Agent policies evaluated under do(X).",
         "Requires a structural model of the DGP.",
         AMETHYST),
        (EMERALD,  "L3  Counterfactual",
         "Off-policy evaluation with adjustment.",
         "Counterfactual regret minimization.",
         "Comparing what a logged policy did to what",
         "a new policy would have done on same traffic.",
         EMERALD),
    ]

    block_h = 230
    for i, (color, header, *lines, accent) in enumerate(levels):
        block_top = panel_y_top - 45 - i * block_h
        # Swatch
        c.setFillColor(color)
        c.circle(panel_x + 14, block_top + 4, 14, stroke=0, fill=1)
        # Header
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 17)
        c.drawString(panel_x + 40, block_top, header)
        # Body lines
        c.setFont('Poppins', 12)
        c.setFillColor(GRAPHITE)
        body_lines = [l for l in lines if l]
        for li, line in enumerate(body_lines):
            c.drawString(panel_x + 40, block_top - 30 - li * 22, "• " + line)

    # Bottom caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 14)
    c.drawCentredString(W / 2, 70, "Climbing the hierarchy requires structural assumptions about the data-generating process.")
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Medium', 13)
    c.drawCentredString(W / 2, 45, "The platform supplies the data. The CAIO supplies the assumptions.")


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
