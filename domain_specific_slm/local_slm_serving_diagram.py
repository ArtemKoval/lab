#!/usr/bin/env python3
"""
CAIO Diagram: The Four Layers of Inference Sovereignty
Topic: slm-deployment-serving
Type: Concentric Rings
Output: caio-slm-deployment-serving-diagram-1.png
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
OUTPUT_PNG = '/home/claude/caio-slm-deployment-serving-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    """Main diagram drawing function."""
    # Background — white
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(
        W/2, H - 70, "The Four Layers of Inference Sovereignty")

    # Subtitle
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(
        W/2, H - 100, "Deployment topology as a first-class strategic decision — each layer trades centralization for control")

    # Center of concentric rings (shifted left to leave room for right-side annotations)
    cx, cy = 560, 580

    # Four concentric rings — outermost to innermost
    # Layer 4 (outermost): Cloud API — lowest sovereignty, highest convenience
    # Layer 3: Centralized GPU cluster
    # Layer 2: FastAPI microservices
    # Layer 1 (innermost): On-device / edge — highest sovereignty

    rings = [
        {'r': 400, 'color': BURGUNDY, 'label_inner': 'Layer 4',
            'label_outer': 'Hyperscale Cloud APIs'},
        {'r': 310, 'color': AMETHYST, 'label_inner': 'Layer 3',
            'label_outer': 'Centralized GPU Clusters'},
        {'r': 220, 'color': SAPPHIRE, 'label_inner': 'Layer 2',
            'label_outer': 'FastAPI Microservices'},
        {'r': 130, 'color': EMERALD, 'label_inner': 'Layer 1',
            'label_outer': 'On-Device and Edge'},
    ]

    # Draw rings outermost first
    for ring in rings:
        c.setFillColor(ring['color'])
        c.setStrokeColor(IVORY)
        c.setLineWidth(3)
        c.circle(cx, cy, ring['r'], stroke=1, fill=1)

    # Draw labels on ring top edges (inside each ring band)
    # Layer 4 label — at top of outermost ring
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(cx, cy + 355, "LAYER 4")
    c.setFont('Poppins-Medium', 15)
    c.drawCentredString(cx, cy + 335, "Hyperscale Cloud APIs")

    # Layer 3
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(cx, cy + 265, "LAYER 3")
    c.setFont('Poppins-Medium', 15)
    c.drawCentredString(cx, cy + 245, "Centralized GPU Clusters")

    # Layer 2
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(cx, cy + 175, "LAYER 2")
    c.setFont('Poppins-Medium', 15)
    c.drawCentredString(cx, cy + 155, "FastAPI Microservices")

    # Layer 1 (innermost — use larger text)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(cx, cy + 20, "LAYER 1")
    c.setFont('Poppins-Medium', 14)
    c.drawCentredString(cx, cy - 5, "On-Device")
    c.drawCentredString(cx, cy - 25, "and Edge")

    # Right-side descriptive panel
    panel_x = 1050
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawString(panel_x, H - 180, "Sovereignty Gradient")

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawString(panel_x, H - 210,
                 "Inner rings trade convenience for control.")
    c.drawString(panel_x, H - 228,
                 "Outer rings trade control for convenience.")

    # Layer descriptions
    layer_info = [
        {
            'num': 'LAYER 4',
            'name': 'Hyperscale Cloud APIs',
            'color': BURGUNDY,
            'use': 'Use for experimentation, low-volume novel cases, frontier reasoning where the model is the bottleneck.',
            'y_offset': 270
        },
        {
            'num': 'LAYER 3',
            'name': 'Centralized GPU Clusters',
            'color': AMETHYST,
            'use': 'Use for high-volume production serving with vLLM. Cost-per-token and throughput dominate.',
            'y_offset': 400
        },
        {
            'num': 'LAYER 2',
            'name': 'FastAPI Microservices',
            'color': SAPPHIRE,
            'use': 'Use for bespoke inference endpoints. Fine-grained control over routing and pre and post-processing.',
            'y_offset': 530
        },
        {
            'num': 'LAYER 1',
            'name': 'On-Device and Edge',
            'color': EMERALD,
            'use': 'Use for data sovereignty, real-time latency, offline resilience. MLC LLM, mllm, Termux enable this.',
            'y_offset': 660
        },
    ]

    for info in layer_info:
        y = H - info['y_offset']
        # Color swatch
        c.setFillColor(info['color'])
        c.rect(panel_x, y - 8, 18, 18, stroke=0, fill=1)
        # Layer number + name
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 13)
        c.drawString(panel_x + 28, y, info['num'])
        c.setFont('Poppins-Medium', 13)
        c.drawString(panel_x + 100, y, info['name'])
        # Use case
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins', 11)
        words = info['use'].split(' ')
        line1 = []
        line2 = []
        line3 = []
        current = line1
        for word in words:
            test = ' '.join(current + [word])
            if len(test) > 48 and current is line1:
                current = line2
            elif len(test) > 48 and current is line2:
                current = line3
            current.append(word)
        c.drawString(panel_x + 28, y - 20, ' '.join(line1))
        if line2:
            c.drawString(panel_x + 28, y - 37, ' '.join(line2))
        if line3:
            c.drawString(panel_x + 28, y - 54, ' '.join(line3))

    # Bottom note
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 14)
    c.drawCentredString(
        W/2, 90, "Mature enterprises operate across all four layers — routing each workload to the topology where its economics and constraints align.")


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
