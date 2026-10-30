"""Gera o icone do app (icone.ico com varios tamanhos + icone.png para a tela)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PASTA = Path(__file__).resolve().parent
TAM = 512
img = Image.new("RGBA", (TAM, TAM), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Fundo: quadrado arredondado em degrade azul.
fundo = Image.new("RGBA", (TAM, TAM))
for y in range(TAM):
    t = y / TAM
    cor = (int(42 + (24 - 42) * t), int(91 + (56 - 91) * t), int(215 + (160 - 215) * t), 255)
    ImageDraw.Draw(fundo).line([(0, y), (TAM, y)], fill=cor)
mascara = Image.new("L", (TAM, TAM), 0)
ImageDraw.Draw(mascara).rounded_rectangle([16, 16, TAM - 16, TAM - 16], radius=110, fill=255)
img.paste(fundo, (0, 0), mascara)

# Texto "PS" e uma lupa (consulta).
fonte = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 230)
d.text((TAM * 0.40, TAM * 0.45), "PS", font=fonte, fill="white", anchor="mm")
cx, cy, r = 360, 360, 62
d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="white", width=26)
d.line([(cx + 44, cy + 44), (cx + 105, cy + 105)], fill="white", width=34)

img.save(PASTA / "icone.png")
img.save(PASTA / "icone.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("ok")
