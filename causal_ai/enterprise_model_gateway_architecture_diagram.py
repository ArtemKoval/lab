#!/usr/bin/env python3
"""
CAIO Diagram: The Enterprise Model Gateway
Topic: model-gateway-architecture
Type: Hub-and-Spoke
Output: caio-model-gateway-architecture-diagram-3.png
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
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
OCHRE = HexColor('#C49A2A')
MUSTARD = HexColor('#C4952A')
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')

# --- Font Registration ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-model-gateway-architecture-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'


def draw_diagram(c):
    """Hub-and-spoke gateway architecture — central gateway routing to provider satellites."""
    # White canvas
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 80, "The Enterprise Model Gateway")

    # Subtitle
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 110, "One unified API. Eight provider routes. Uniform governance across the catalog.")

    # Center
    cx, cy = W / 2, H / 2 - 30
    hub_r = 125
    orbit_r = 340
    sat_r = 72

    # Eight provider satellites
    providers = [
        ("Anthropic",    "Claude family",      NAVY),
        ("OpenAI",       "GPT family",         SAPPHIRE),
        ("Meta",         "Llama family",       EMERALD),
        ("Mistral",      "Mistral / Ministral", AMETHYST),
        ("Qwen",         "Alibaba Cloud",      BURGUNDY),
        ("DeepSeek",     "V3 / R1",            UMBER),
        ("Cohere",       "Command / Embed",    TEAL),
        ("Amazon",       "Nova / Titan",       MOSS),
    ]
    n = len(providers)
    angle_per = 360 / n

    # --- Draw connector lines first (behind satellites) ---
    c.setStrokeColor(TAUPE)
    c.setLineWidth(2)
    c.setDash(6, 4)
    for i in range(n):
        ang_deg = 90 - i * angle_per
        ang = math.radians(ang_deg)
        # Line from hub edge to satellite edge
        x_hub_edge = cx + hub_r * math.cos(ang)
        y_hub_edge = cy + hub_r * math.sin(ang)
        sx = cx + orbit_r * math.cos(ang)
        sy = cy + orbit_r * math.sin(ang)
        x_sat_edge = sx - sat_r * math.cos(ang)
        y_sat_edge = sy - sat_r * math.sin(ang)
        c.line(x_hub_edge, y_hub_edge, x_sat_edge, y_sat_edge)
    c.setDash(1, 0)  # Reset

    # --- Draw outer functional ring (gateway capabilities) ---
    func_ring_r = orbit_r + sat_r + 70
    c.setStrokeColor(OCHRE)
    c.setLineWidth(1.5)
    c.setDash(3, 5)
    c.circle(cx, cy, func_ring_r, stroke=1, fill=0)
    c.setDash(1, 0)

    # Functional labels at four cardinal positions on outer ring
    func_labels = [
        ("Routing",    90),
        ("Guardrails", 0),
        ("Evaluation", 270),
        ("Audit",      180),
    ]
    for label, ang_deg in func_labels:
        ang = math.radians(ang_deg)
        # Label sits on the outer ring with a small white background plate
        lx = cx + func_ring_r * math.cos(ang)
        ly = cy + func_ring_r * math.sin(ang)
        c.setFillColor(HexColor('#FFFFFF'))
        # Background plate
        plate_w = 130
        plate_h = 32
        c.rect(lx - plate_w / 2, ly - plate_h / 2,
               plate_w, plate_h, stroke=0, fill=1)
        c.setFillColor(OCHRE)
        c.setFont('Poppins-Bold', 18)
        c.drawCentredString(lx, ly - 6, label)

    # --- Draw central hub ---
    c.setFillColor(NAVY)
    c.circle(cx, cy, hub_r, stroke=0, fill=1)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 26)
    c.drawCentredString(cx, cy + 18, "Model")
    c.drawCentredString(cx, cy - 12, "Gateway")
    c.setFillColor(MUSTARD)
    c.setFont('Poppins-Medium', 13)
    c.drawCentredString(cx, cy - 42, "unified API")

    # --- Draw provider satellites ---
    for i, (name, descriptor, fill) in enumerate(providers):
        ang_deg = 90 - i * angle_per
        ang = math.radians(ang_deg)
        sx = cx + orbit_r * math.cos(ang)
        sy = cy + orbit_r * math.sin(ang)

        # Satellite circle
        c.setFillColor(fill)
        c.circle(sx, sy, sat_r, stroke=0, fill=1)
        # Border
        c.setStrokeColor(HexColor('#FFFFFF'))
        c.setLineWidth(3)
        c.circle(sx, sy, sat_r, stroke=1, fill=0)

        # Provider name (Ivory inside dark fills)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 17)
        c.drawCentredString(sx, sy + 4, name)
        c.setFont('Poppins', 10)
        c.drawCentredString(sx, sy - 14, descriptor)

    # --- Bottom attribution ---
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(
        W / 2, 50, "AWS Bedrock exposes nearly 100 serverless foundation models from 13 providers behind one API")
    c.drawCentredString(
        W / 2, 32, "Bedrock Marketplace adds 100+ specialty and domain-tuned models — same governance perimeter applies")


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
