#!/usr/bin/env python3
"""
CAIO Diagram: Pearl's Ladder of Causation as Concentric Rings
Topic: causal-ai-decision-layer
Type: Concentric rings (innermost = highest rung, outermost = lowest rung)
Output: caio-causal-ai-decision-layer-diagram-1.png
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
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
TAUPE = HexColor('#8A7B6B')
WHITE = HexColor('#FFFFFF')

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
OUTPUT_PNG = '/home/claude/caio/caio-causal-ai-decision-layer-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    """Concentric rings showing Pearl's three rungs of causation."""
    # White background
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # --- Title ---
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 70, "Pearl's Ladder of Causation")

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 100, "Three rungs of causal reasoning — each rung answers questions a lower rung cannot")

    # Layout zones:
    # Left text column: x=60 to x=380
    # Center rings: cx=780, r_outer=300 (rings span 480 to 1080)
    # Right text column: x=1140 to x=1540
    cx = 780
    cy = H / 2 - 60  # 540

    r_outer = 300
    r_middle = 215
    r_inner = 130

    # Outer ring - Sapphire
    c.setFillColor(SAPPHIRE)
    c.circle(cx, cy, r_outer, stroke=0, fill=1)
    # Middle ring - Emerald
    c.setFillColor(EMERALD)
    c.circle(cx, cy, r_middle, stroke=0, fill=1)
    # Inner ring - Burgundy
    c.setFillColor(BURGUNDY)
    c.circle(cx, cy, r_inner, stroke=0, fill=1)

    # Outer ring label - Association
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 18)
    label_y_outer = cy + (r_outer + r_middle) / 2  # midpoint of outer band
    c.drawCentredString(cx, label_y_outer + 8, "RUNG 1")
    c.setFont('Poppins-Medium', 22)
    c.drawCentredString(cx, label_y_outer - 18, "Association")
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(cx, label_y_outer - 38, "What is correlated with what")

    # Middle ring label - Intervention
    label_y_middle = cy + (r_middle + r_inner) / 2  # midpoint of middle band
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(cx, label_y_middle + 6, "RUNG 2")
    c.setFont('Poppins-Medium', 19)
    c.drawCentredString(cx, label_y_middle - 16, "Intervention")
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(cx, label_y_middle - 33, "What happens when I act")

    # Inner ring label - Counterfactual
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(cx, cy + 30, "RUNG 3")
    c.setFont('Poppins-Medium', 17)
    c.drawCentredString(cx, cy + 8, "Counterfactual")
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(cx, cy - 14, "What would have")
    c.drawCentredString(cx, cy - 28, "happened if")

    # --- Left side: example questions per rung ---
    left_x = 60

    c.setFillColor(SAPPHIRE)
    c.setFont('Poppins-Bold', 14)
    c.drawString(left_x, cy + 240, "RUNG 1 EXAMPLE")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawString(left_x, cy + 218, "Which customers are likely")
    c.drawString(left_x, cy + 200, "to churn next quarter?")
    c.setFillColor(NAVY)
    c.setFont('Poppins-Light', 11)
    c.drawString(left_x, cy + 178, "Method: supervised learning")

    c.setFillColor(EMERALD)
    c.setFont('Poppins-Bold', 14)
    c.drawString(left_x, cy + 50, "RUNG 2 EXAMPLE")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawString(left_x, cy + 28, "If we offer this discount,")
    c.drawString(left_x, cy + 10, "what is the lift in retention?")
    c.setFillColor(NAVY)
    c.setFont('Poppins-Light', 11)
    c.drawString(left_x, cy - 12, "Method: causal inference")

    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 14)
    c.drawString(left_x, cy - 140, "RUNG 3 EXAMPLE")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawString(left_x, cy - 162, "Would this customer have")
    c.drawString(left_x, cy - 180, "purchased without our ad?")
    c.setFillColor(NAVY)
    c.setFont('Poppins-Light', 11)
    c.drawString(left_x, cy - 204, "Method: counterfactual SCM")

    # --- Right side: AI/ML stack mapping ---
    right_x = 1140
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 14)
    c.drawString(right_x, cy + 240, "WHAT THE STACK ANSWERS")

    c.setFillColor(SAPPHIRE)
    c.circle(right_x + 8, cy + 200, 7, stroke=0, fill=1)
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 13)
    c.drawString(right_x + 26, cy + 196, "Rung 1: Most predictive ML")
    c.setFont('Poppins', 12)
    c.drawString(right_x + 26, cy + 178, "Classification, regression,")
    c.drawString(right_x + 26, cy + 162, "recommendation, forecasting")

    c.setFillColor(EMERALD)
    c.circle(right_x + 8, cy + 110, 7, stroke=0, fill=1)
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 13)
    c.drawString(right_x + 26, cy + 106, "Rung 2: Causal inference")
    c.setFont('Poppins', 12)
    c.drawString(right_x + 26, cy + 88, "Uplift modeling, A/B tests,")
    c.drawString(right_x + 26, cy + 72, "geo-experiments, do-calculus")

    c.setFillColor(BURGUNDY)
    c.circle(right_x + 8, cy + 20, 7, stroke=0, fill=1)
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 13)
    c.drawString(right_x + 26, cy + 16, "Rung 3: Structural causal")
    c.setFont('Poppins', 12)
    c.drawString(right_x + 26, cy - 2, "Parallel-world reasoning,")
    c.drawString(right_x + 26, cy - 18, "twin networks, attribution")

    # Key insight box
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawString(right_x, cy - 80, "THE STRUCTURAL RULE")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 12)
    c.drawString(right_x, cy - 102, "Information at a lower rung")
    c.drawString(right_x, cy - 118, "cannot answer questions at")
    c.drawString(right_x, cy - 134, "a higher rung. A bigger Rung 1")
    c.drawString(right_x, cy - 150, "model never reaches Rung 2.")

    # Footer attribution
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(
        W / 2, 40, "Framework: Pearl & Mackenzie, The Book of Why (2018)")


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
