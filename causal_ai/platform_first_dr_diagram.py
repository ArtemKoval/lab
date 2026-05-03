#!/usr/bin/env python3
"""
CAIO Diagram: The Portability Stack
Topic: caio-platform-first-aiops
Type: Concentric rings (layered architecture — platform inside, substrate outside)
Output: caio-platform-first-aiops-diagram-2.png
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
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
MUSTARD = HexColor('#C4952A')
UMBER = HexColor('#6B4226')
TAUPE = HexColor('#8A7B6B')
WHITE = HexColor('#FFFFFF')
WARM_BLUE = HexColor('#2A5A8A')
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

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-platform-first-aiops-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # --- Title ---
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 70, "The Portability Stack")

    # --- Subtitle ---
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 100, "What is durable. What is interchangeable. The order matters.")

    # --- Concentric rings ---
    # Center the rings on the canvas — leave room for left-side substrate labels
    cx, cy = W / 2 - 120, H / 2 - 20

    # Ring radii (outermost first)
    r_substrate = 410   # outermost — deployment substrates
    r_kubernetes = 305  # middle — Kubernetes orchestration
    r_platform = 200    # inner — AIOps platform
    r_workload = 95     # innermost — AI workloads

    # --- Ring 4 (outermost): Deployment Substrate ---
    c.setFillColor(TAUPE)
    c.circle(cx, cy, r_substrate, stroke=0, fill=1)

    # --- Ring 3: Kubernetes ---
    c.setFillColor(SAPPHIRE)
    c.circle(cx, cy, r_kubernetes, stroke=0, fill=1)

    # --- Ring 2: AIOps Platform ---
    c.setFillColor(EMERALD)
    c.circle(cx, cy, r_platform, stroke=0, fill=1)

    # --- Ring 1 (innermost): AI Workloads ---
    c.setFillColor(NAVY)
    c.circle(cx, cy, r_workload, stroke=0, fill=1)

    # --- Ring labels (inside each ring) ---

    # Innermost: AI Workloads
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(cx, cy + 6, "AI")
    c.drawCentredString(cx, cy - 14, "Workloads")

    # Ring 2: AIOps Platform — positioned between r_workload and r_platform, top-center
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 19)
    label_y_2 = cy + (r_workload + r_platform) / 2
    c.drawCentredString(cx, label_y_2 - 4, "AIOps Platform")
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(cx, label_y_2 - 22, "Kubeflow  .  MLflow  .  BentoML")
    c.drawCentredString(cx, label_y_2 - 38, "Evidently  .  Feast  .  ArgoCD")

    # Ring 3: Kubernetes — between r_platform and r_kubernetes
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 18)
    label_y_3 = cy + (r_platform + r_kubernetes) / 2
    c.drawCentredString(cx, label_y_3 - 6, "Kubernetes")
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(cx, label_y_3 - 22, "Container orchestration")

    # Ring 4: Deployment Substrate — between r_kubernetes and r_substrate
    c.setFillColor(NAVY)  # darker text on lighter Taupe
    c.setFont('Poppins-Bold', 17)
    label_y_4 = cy + (r_kubernetes + r_substrate) / 2
    c.drawCentredString(cx, label_y_4 - 4, "Deployment Substrate")
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(cx, label_y_4 - 20, "(interchangeable)")

    # --- Right-side legend: substrate options ---
    legend_x = cx + r_substrate + 80
    legend_y_top = cy + 230

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawString(legend_x, legend_y_top, "Substrate options:")

    substrates = [
        ("On-premises", "Owned hardware  .  data sovereignty"),
        ("AWS", "EKS  .  EKS Hybrid Nodes"),
        ("GCP", "GKE  .  Anthos"),
        ("Azure", "AKS  .  Arc"),
        ("Hybrid", "AWS Outposts  .  EKS Anywhere"),
        ("Edge", "K3s  .  MicroK8s clusters"),
    ]

    y_off = legend_y_top - 30
    for name, desc in substrates:
        # bullet circle
        c.setFillColor(EMERALD)
        c.circle(legend_x + 6, y_off + 6, 5, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 13)
        c.drawString(legend_x + 22, y_off + 2, name)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 11)
        c.drawString(legend_x + 22, y_off - 14, desc)
        y_off -= 50

    # --- Caption / framing line at bottom ---
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(
        W / 2, 110, "Inner rings are the strategic asset. Outer ring is sourcing.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(
        W / 2, 82, "Workloads do not move when the substrate changes — because they never knew which substrate they were on.")

    # Attribution
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 10)
    c.drawCentredString(W / 2, 50, "Art Koval  /  Chief AI Officer Insights")


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
