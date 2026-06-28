"""Diagram 2 - Two Paradigms, One Production System (Venn).
Autoregressive (structure) and diffusion (fidelity) overlap as hybrid systems.
Self-rasterizing standalone script.
"""
import os
import subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
for _name, _file in {
    "Poppins-Bold": "Poppins-Bold.ttf",
    "Poppins-Medium": "Poppins-Medium.ttf",
    "Poppins-Regular": "Poppins-Regular.ttf",
    "Poppins-Italic": "Poppins-Italic.ttf",
    "Poppins-MediumItalic": "Poppins-MediumItalic.ttf",
}.items():
    pdfmetrics.registerFont(TTFont(_name, os.path.join(FONT_DIR, _file)))

NAVY = HexColor("#1E2A4A")
SAPPHIRE = HexColor("#1A3A6B")
GRAPHITE = HexColor("#3A3A3A")
IVORY = HexColor("#F0EAD6")
BURGUNDY = HexColor("#6B1C2A")
WHITE = HexColor("#FFFFFF")

W, H = 1600, 1200


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(here, "caio-generative-media-stack-diagram-2_tmp.pdf")
    png_path = os.path.join(here, "caio-generative-media-stack-diagram-2.png")

    c = canvas.Canvas(pdf_path, pagesize=(W, H))
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(NAVY)
    c.setFont("Poppins-Bold", 46)
    c.drawCentredString(W / 2, H - 92, "Two Paradigms, One Production System")
    c.setFillColor(GRAPHITE)
    c.setFont("Poppins-Medium", 25)
    c.drawCentredString(W / 2, H - 130, "Autoregressive plans the structure. Diffusion renders the surface.")

    lx, rx, cyc, r = 625, 975, 520, 335

    # Overlapping lobes (symmetric alpha keeps both equally bright)
    c.setFillColor(SAPPHIRE)
    c.setFillAlpha(0.85)
    c.circle(lx, cyc, r, fill=1, stroke=0)
    c.setFillColor(BURGUNDY)
    c.setFillAlpha(0.85)
    c.circle(rx, cyc, r, fill=1, stroke=0)
    c.setFillAlpha(1)

    # Crisp white outlines delineate the lens
    c.setStrokeColor(WHITE)
    c.setLineWidth(3)
    c.circle(lx, cyc, r, fill=0, stroke=1)
    c.circle(rx, cyc, r, fill=0, stroke=1)

    def bullet(x, y, text, size=19):
        c.setFillColor(IVORY)
        c.circle(x + 5, y + 6, 4.5, fill=1, stroke=0)
        c.setFont("Poppins-Regular", size)
        c.drawString(x + 20, y, text)

    # Left lobe - Autoregressive
    c.setFillColor(IVORY)
    c.setFont("Poppins-Bold", 30)
    c.drawCentredString(468, cyc + 168, "AUTOREGRESSIVE")
    c.setFillColor(IVORY)
    c.setFont("Poppins-MediumItalic", 18)
    c.drawCentredString(468, cyc + 140, "sequence, token by token")
    for i, t in enumerate(["Instruction following",
                            "Structure & layout",
                            "Semantic consistency",
                            "Compositional accuracy"]):
        bullet(344, cyc + 86 - i * 52, t)

    # Right lobe - Diffusion
    c.setFillColor(IVORY)
    c.setFont("Poppins-Bold", 30)
    c.drawCentredString(1132, cyc + 168, "DIFFUSION")
    c.setFont("Poppins-MediumItalic", 18)
    c.drawCentredString(1132, cyc + 140, "denoise, refine in latent space")
    for i, t in enumerate(["Texture & fine detail",
                           "High visual fidelity",
                           "Audio-visual coherence",
                           "Latent refinement"]):
        bullet(1016, cyc + 86 - i * 52, t)

    # Intersection - Hybrid
    c.setFillColor(IVORY)
    c.setFont("Poppins-Bold", 26)
    c.drawCentredString(800, cyc + 18, "HYBRID")
    c.setFont("Poppins-Medium", 17)
    c.drawCentredString(800, cyc - 12, "modern")
    c.drawCentredString(800, cyc - 34, "production")
    c.drawCentredString(800, cyc - 56, "systems")

    # Caption
    c.setFillColor(GRAPHITE)
    c.setFont("Poppins-Italic", 19)
    c.drawCentredString(W / 2, 78, "The production decision is not either-or. It is how you combine and route them.")

    c.showPage()
    c.save()

    tmp_prefix = png_path[:-4] + "_raster"
    subprocess.run(
        ["/usr/bin/pdftoppm", "-png", "-r", "150", "-singlefile", pdf_path, tmp_prefix],
        check=True,
    )
    tmp_png = tmp_prefix + ".png"
    img = Image.open(tmp_png).convert("RGB").resize((W, H), Image.LANCZOS)
    img.save(png_path)
    os.remove(tmp_png)
    os.remove(pdf_path)
    print("wrote", png_path)


if __name__ == "__main__":
    main()
