#!/usr/bin/env python3
"""
CAIO Diagram: Domain-Specific SLM vs General-Purpose LLM — Enterprise Profile
Topic: slm-production-systems
Type: Radar overlay — two polygons on 6 axes comparing operational profiles
Output: caio-slm-production-systems-diagram-2.png
"""

import math
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

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
OUTPUT_PNG = '/home/claude/caio-slm-production-systems-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'

# --- Data ---
# Six axes — each scored 0 to 10 for SLM (domain-specific, fine-tuned) and LLM (general-purpose)
AXES = [
    "Domain Accuracy",
    "Cost Efficiency",
    "Data Sovereignty",
    "Governance Control",
    "Response Latency",
    "Hallucination Resistance",
]
SLM_SCORES = [9, 9, 9, 8, 8, 8]
LLM_SCORES = [7, 3, 3, 4, 5, 5]
MAX_SCORE = 10


def polygon_points(cx, cy, scores, max_score, max_r, n_axes):
    """Return list of (x, y) points on radar polygon."""
    points = []
    for i, v in enumerate(scores):
        # 12 o'clock start, clockwise
        angle = math.radians(90 - i * (360 / n_axes))
        r = max_r * (v / max_score)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    return points


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(
        W/2, H - 70, "Domain-Specific SLM vs General-Purpose LLM")

    # Subtitle
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 105, "Operational profile across six enterprise dimensions")

    # Radar parameters
    cx, cy = 700, 560
    max_r = 340
    n_axes = len(AXES)

    # Draw concentric gridlines (5 levels) as light polygons
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.setLineWidth(1)
    for level in range(1, 6):
        level_r = max_r * (level / 5)
        p = c.beginPath()
        for i in range(n_axes):
            angle = math.radians(90 - i * (360 / n_axes))
            x = cx + level_r * math.cos(angle)
            y = cy + level_r * math.sin(angle)
            if i == 0:
                p.moveTo(x, y)
            else:
                p.lineTo(x, y)
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    # Draw spokes from center
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.setLineWidth(1)
    for i in range(n_axes):
        angle = math.radians(90 - i * (360 / n_axes))
        x = cx + max_r * math.cos(angle)
        y = cy + max_r * math.sin(angle)
        c.line(cx, cy, x, y)

    # Scale labels on vertical axis (2, 4, 6, 8, 10) — inside polygon, small
    c.setFillColor(HexColor('#999999'))
    c.setFont('Poppins-Light', 9)
    for level in range(1, 6):
        val = 2 * level
        r_level = max_r * (level / 5)
        c.drawString(cx + 4, cy + r_level - 3, str(val))

    # Alpha-composited colors using Color(r, g, b, alpha) — more reliable than setFillAlpha
    # Emerald (#1A5C3A) → r=0.102, g=0.361, b=0.227
    # Burgundy (#6B1C2A) → r=0.420, g=0.110, b=0.165
    emerald_fill = Color(0.102, 0.361, 0.227, alpha=0.22)
    burgundy_fill = Color(0.420, 0.110, 0.165, alpha=0.55)

    # --- SLM polygon drawn FIRST (back) — large, translucent ---
    slm_pts = polygon_points(cx, cy, SLM_SCORES, MAX_SCORE, max_r, n_axes)
    p = c.beginPath()
    p.moveTo(slm_pts[0][0], slm_pts[0][1])
    for x, y in slm_pts[1:]:
        p.lineTo(x, y)
    p.close()
    c.setFillColor(emerald_fill)
    c.setStrokeColor(EMERALD)
    c.setLineWidth(3)
    c.drawPath(p, stroke=1, fill=1)

    # SLM point markers — solid emerald
    for x, y in slm_pts:
        c.setFillColor(EMERALD)
        c.circle(x, y, 6, stroke=0, fill=1)

    # --- LLM polygon drawn SECOND (front) — smaller, more opaque so it shows clearly ---
    llm_pts = polygon_points(cx, cy, LLM_SCORES, MAX_SCORE, max_r, n_axes)
    p = c.beginPath()
    p.moveTo(llm_pts[0][0], llm_pts[0][1])
    for x, y in llm_pts[1:]:
        p.lineTo(x, y)
    p.close()
    c.setFillColor(burgundy_fill)
    c.setStrokeColor(BURGUNDY)
    c.setLineWidth(3)
    c.drawPath(p, stroke=1, fill=1)

    # LLM point markers — solid burgundy
    for x, y in llm_pts:
        c.setFillColor(BURGUNDY)
        c.circle(x, y, 6, stroke=0, fill=1)

    # Axis labels — placed outside the outer polygon
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 14)
    label_offset = 42
    for i, label in enumerate(AXES):
        angle = math.radians(90 - i * (360 / n_axes))
        lx = cx + (max_r + label_offset) * math.cos(angle)
        ly = cy + (max_r + label_offset) * math.sin(angle)

        # Center the text based on angle — use drawCentredString for symmetry
        # Adjust alignment based on approximate position
        # Top
        if 60 < (90 - i * 60) % 360 or i == 0:
            pass
        # Use simple centered placement, with slight vertical offset for top/bottom
        dy = 0
        if abs(math.sin(angle)) > 0.8:  # near top or bottom
            dy = 0 if math.sin(angle) > 0 else -12
        c.drawCentredString(lx, ly + dy, label)

    # --- Legend (right side) ---
    lx_legend = 1120
    ly_legend = 700

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawString(lx_legend, ly_legend, "Legend")

    # SLM legend — translucent emerald fill
    c.setFillColor(emerald_fill)
    c.rect(lx_legend, ly_legend - 40, 28, 20, stroke=0, fill=1)
    c.setStrokeColor(EMERALD)
    c.setLineWidth(2)
    c.rect(lx_legend, ly_legend - 40, 28, 20, stroke=1, fill=0)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawString(lx_legend + 38, ly_legend - 34, "Domain-Specific SLM")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 11)
    c.drawString(lx_legend + 38, ly_legend - 50,
                 "Fine-tuned, on-prem, quantized")

    # LLM legend — burgundy fill
    c.setFillColor(burgundy_fill)
    c.rect(lx_legend, ly_legend - 90, 28, 20, stroke=0, fill=1)
    c.setStrokeColor(BURGUNDY)
    c.setLineWidth(2)
    c.rect(lx_legend, ly_legend - 90, 28, 20, stroke=1, fill=0)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawString(lx_legend + 38, ly_legend - 84, "General-Purpose LLM")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 11)
    c.drawString(lx_legend + 38, ly_legend - 100, "Off-the-shelf, API-served")

    # Notes block
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 14)
    c.drawString(lx_legend, ly_legend - 150, "Key signals")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 11)

    notes = [
        "Domain accuracy gap has shrunk to",
        "as low as 2% on focused tasks",
        "",
        "35% fewer critical errors in",
        "regulated-sector deployments",
        "",
        "10-30x lower inference cost",
        "for fine-tuned SLMs at scale",
        "",
        "Data never leaves the enterprise",
        "boundary — full sovereignty",
    ]
    for i, line in enumerate(notes):
        c.drawString(lx_legend, ly_legend - 175 - i * 15, line)

    # Bottom caption
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(
        W/2, 60, "Sources: Alithya 2025 (accuracy gap, error rates); Gartner 2026 (inference economics); enterprise SLM deployment data.")


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
