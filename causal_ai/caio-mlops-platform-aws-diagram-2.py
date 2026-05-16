#!/usr/bin/env python3
"""
CAIO Diagram: The MLOps Platform as Abstraction Layer Over AWS
Topic: mlops-platform-aws
Type: Hub-and-spoke — central platform with 5 capability satellites, each labeled
      with both AWS-native and open-source canonical implementations
Output: caio-mlops-platform-aws-diagram-2.png
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
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')
TAUPE = HexColor('#8A7B6B')
WARM_BLUE = HexColor('#2A5A8A')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-mlops-platform-aws-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'

# Five capability satellites, each labeled with both implementations.
# Position starts at top (90°) and rotates clockwise.
SATELLITES = [
    {
        "title": "Pipeline\nOrchestration",
        "color": SAPPHIRE,
        "aws":  "AWS — SageMaker Pipelines",
        "oss":  "OSS — Kubeflow / Argo",
    },
    {
        "title": "Model\nRegistry",
        "color": BURGUNDY,
        "aws":  "AWS — SageMaker Model Registry",
        "oss":  "OSS — MLflow",
    },
    {
        "title": "Feature\nStore",
        "color": EMERALD,
        "aws":  "AWS — SageMaker Feature Store",
        "oss":  "OSS — Feast",
    },
    {
        "title": "Model\nServing",
        "color": AMETHYST,
        "aws":  "AWS — SageMaker Endpoints / Bedrock",
        "oss":  "OSS — BentoML / KServe",
    },
    {
        "title": "Model\nMonitoring",
        "color": UMBER,
        "aws":  "AWS — SageMaker Model Monitor",
        "oss":  "OSS — Evidently / Prometheus",
    },
]


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # --- Title ---
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W / 2, H - 70, "The MLOps Platform as Abstraction Over AWS")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 100, "Each capability has an AWS-native and an open-source canonical. The platform makes the choice reversible.")

    # --- Layout geometry ---
    cx, cy = W / 2, H / 2 - 30
    hub_r = 145              # central platform hub
    orbit_r = 380            # distance from center to satellite centers
    node_r = 85              # satellite node radius

    n = len(SATELLITES)
    # 5 satellites placed at 90°, 162°, 234°, 306°, 18° (pentagon)
    # Start at top (90°) and go clockwise: 90, 90-72=18, ... but for visual
    # we'll do top, upper-right, lower-right, lower-left, upper-left
    angles_deg = [90, 18, -54, -126, 162]  # top, then clockwise

    # --- Draw connector lines (Taupe) ---
    c.setStrokeColor(TAUPE)
    c.setLineWidth(2.5)
    for ang_deg in angles_deg:
        ang = math.radians(ang_deg)
        # Start at edge of hub, end at edge of satellite
        start_x = cx + hub_r * math.cos(ang)
        start_y = cy + hub_r * math.sin(ang)
        sat_x = cx + orbit_r * math.cos(ang)
        sat_y = cy + orbit_r * math.sin(ang)
        end_x = sat_x - node_r * math.cos(ang)
        end_y = sat_y - node_r * math.sin(ang)
        c.line(start_x, start_y, end_x, end_y)

    # --- Draw satellite circles ---
    for i, ang_deg in enumerate(angles_deg):
        sat = SATELLITES[i]
        ang = math.radians(ang_deg)
        sat_x = cx + orbit_r * math.cos(ang)
        sat_y = cy + orbit_r * math.sin(ang)

        # Satellite circle filled with jewel tone
        c.setFillColor(sat["color"])
        c.setStrokeColor(sat["color"])
        c.circle(sat_x, sat_y, node_r, stroke=0, fill=1)

        # Title in Ivory inside the circle
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 15)
        lines = sat["title"].split("\n")
        for j, line in enumerate(lines):
            c.drawCentredString(sat_x, sat_y + 8 - j * 18, line)

        # External labels — AWS + OSS — placed outside the satellite, radially outward
        # Determine label anchor based on angle
        label_dist = node_r + 16
        label_x = sat_x + label_dist * math.cos(ang)
        label_y = sat_y + label_dist * math.sin(ang)

        # Decide anchor
        cos_a = math.cos(ang)
        if abs(cos_a) < 0.25:
            anchor = 'middle'
        elif cos_a > 0:
            anchor = 'start'
        else:
            anchor = 'end'

        # AWS label — Warm Blue (passes AA on white)
        c.setFillColor(WARM_BLUE)
        c.setFont('Poppins-Medium', 13)
        aws_text = sat["aws"]
        oss_text = sat["oss"]

        # Position: AWS line on top, OSS line below
        if anchor == 'middle':
            c.drawCentredString(label_x, label_y + 10, aws_text)
            c.setFillColor(EMERALD)
            c.drawCentredString(label_x, label_y - 10, oss_text)
        elif anchor == 'start':
            c.drawString(label_x, label_y + 10, aws_text)
            c.setFillColor(EMERALD)
            c.drawString(label_x, label_y - 10, oss_text)
        else:
            c.drawRightString(label_x, label_y + 10, aws_text)
            c.setFillColor(EMERALD)
            c.drawRightString(label_x, label_y - 10, oss_text)

    # --- Central hub (Navy, on top of connectors) ---
    c.setFillColor(NAVY)
    c.setStrokeColor(NAVY)
    c.circle(cx, cy, hub_r, stroke=0, fill=1)

    # Hub text — Ivory on Navy (AAA)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 24)
    c.drawCentredString(cx, cy + 22, "MLOps")
    c.drawCentredString(cx, cy - 8, "Platform")
    c.setFont('Poppins-Light', 12)
    c.setFillColor(OCHRE)
    c.drawCentredString(cx, cy - 38, "the abstraction layer")
    c.setFillColor(IVORY)
    c.setFont('Poppins', 11)
    c.drawCentredString(cx, cy - 58, "EKS / Outposts / on-prem")

    # --- Legend ---
    legend_x = 100
    legend_y = 130
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 12)
    c.drawString(legend_x, legend_y + 18, "Legend")

    # AWS swatch
    c.setFillColor(WARM_BLUE)
    c.circle(legend_x + 10, legend_y - 2, 6, stroke=0, fill=1)
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 11)
    c.drawString(legend_x + 22, legend_y - 6, "AWS-native implementation")

    # OSS swatch
    c.setFillColor(EMERALD)
    c.circle(legend_x + 10, legend_y - 22, 6, stroke=0, fill=1)
    c.setFillColor(GRAPHITE)
    c.drawString(legend_x + 22, legend_y - 26, "Open-source canonical implementation")

    # --- Bottom note ---
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(W / 2, 50, "When the abstraction is in place, SageMaker, Bedrock, EMR, and on-prem GPU clusters all become interchangeable backends. The platform is the asset; the cloud service is the rental.")


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
