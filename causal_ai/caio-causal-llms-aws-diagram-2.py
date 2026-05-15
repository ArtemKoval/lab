#!/usr/bin/env python3
"""
CAIO Diagram: Causal LLM Architecture on AWS
Topic: caio-causal-llms-aws
Type: Hub-and-Spoke — central do-operator orchestrator with AWS service spokes
Output: caio-causal-llms-aws-diagram-2.png
"""

import math
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
TAUPE = HexColor('#8A7B6B')
MOSS = HexColor('#4A5A3A')
UMBER = HexColor('#6B4226')

pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-causal-llms-aws/caio-causal-llms-aws-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # --- Title ---
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 80, "The Causal LLM on AWS")
    c.setFont('Poppins-Light', 16)
    c.setFillColor(GRAPHITE)
    c.drawCentredString(W / 2, H - 110,
                        "AWS primitives for composing foundation models over a causal DAG scaffold")

    # --- Hub geometry ---
    cx, cy = W / 2, H / 2 + 30
    hub_r = 100
    spoke_r = 88
    orbit_r = 310

    # Draw the satellites first so spokes look clean
    satellites = [
        {"label": "Amazon\nBedrock",      "sub": "Foundation models",            "color": SAPPHIRE},
        {"label": "SageMaker AI",         "sub": "Fine-tune Markov kernels",     "color": EMERALD},
        {"label": "Step\nFunctions",      "sub": "do-operator orchestration",    "color": AMETHYST},
        {"label": "Bedrock\nGuardrails",  "sub": "Auto Reasoning · grounding",   "color": BURGUNDY},
        {"label": "S3 · MLflow",          "sub": "DAG data · experiment trail",  "color": MOSS},
        {"label": "CloudWatch",           "sub": "Audit · observability",        "color": UMBER},
    ]

    n = len(satellites)
    positions = []
    for i in range(n):
        ang = math.radians(90 - i * (360 / n))
        sx = cx + orbit_r * math.cos(ang)
        sy = cy + orbit_r * math.sin(ang)
        positions.append((sx, sy))

    # Draw connectors from hub edge to satellite edge
    c.setStrokeColor(TAUPE)
    c.setLineWidth(2)
    for (sx, sy) in positions:
        # Direction unit vector from hub center to satellite
        dx, dy = sx - cx, sy - cy
        dist = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / dist, dy / dist
        # Start at hub edge, end at satellite edge
        x1 = cx + ux * hub_r
        y1 = cy + uy * hub_r
        x2 = sx - ux * spoke_r
        y2 = sy - uy * spoke_r
        c.line(x1, y1, x2, y2)

    # Draw satellites
    c.setFont('Poppins-Bold', 14)
    for (sat, (sx, sy)) in zip(satellites, positions):
        c.setFillColor(sat["color"])
        c.circle(sx, sy, spoke_r, stroke=0, fill=1)
        # Ivory text inside
        c.setFillColor(IVORY)
        # Title (split on \n)
        title_lines = sat["label"].split("\n")
        for li, line in enumerate(title_lines):
            c.setFont('Poppins-Bold', 17)
            y_offset = 6 - li * 18 + (len(title_lines) - 1) * 9
            c.drawCentredString(sx, sy + y_offset, line)
        # Sub-label below satellite
        c.setFillColor(NAVY)
        c.setFont('Poppins', 12)
        c.drawCentredString(sx, sy - spoke_r - 22, sat["sub"])

    # Draw hub
    c.setFillColor(NAVY)
    c.circle(cx, cy, hub_r, stroke=0, fill=1)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 14, "Causal")
    c.drawCentredString(cx, cy - 8, "LLM")
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(cx, cy - 30, "DAG-composed")

    # --- Bottom legend / pattern statement ---
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 17)
    c.drawCentredString(W / 2, 130, "The pattern")
    c.setFont('Poppins', 13)
    c.setFillColor(GRAPHITE)
    pattern_lines = [
        "Specify a causal DAG. Fine-tune one foundation model per node (a causal Markov kernel).",
        "Orchestrate the DAG with a do-operator wrapper. Validate outputs against formal causal rules.",
        "The result is a system that answers interventional and counterfactual queries by identification, not generation.",
    ]
    for i, line in enumerate(pattern_lines):
        c.drawCentredString(W / 2, 105 - i * 22, line)


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
