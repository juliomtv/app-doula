#!/usr/bin/env python3
"""
Gera todos os tamanhos de ícone Android a partir da logo original.
Substitui os arquivos nos diretórios mipmap do projeto Android.
"""
from PIL import Image
import os
import shutil

LOGO_SRC = '/home/ubuntu/upload/Logo+cores_20260426_013048_0000.png'
ANDROID_RES = '/home/ubuntu/app-doula/android/app/src/main/res'

# Tamanhos padrão Android para cada densidade
SIZES = {
    'mipmap-mdpi':    48,
    'mipmap-hdpi':    72,
    'mipmap-xhdpi':   96,
    'mipmap-xxhdpi':  144,
    'mipmap-xxxhdpi': 192,
}

# Tamanho para o ícone de foreground (adaptive icon) — maior para ter margem
FOREGROUND_SIZES = {
    'mipmap-mdpi':    108,
    'mipmap-hdpi':    162,
    'mipmap-xhdpi':   216,
    'mipmap-xxhdpi':  324,
    'mipmap-xxxhdpi': 432,
}

def gerar_icone(img, tamanho, destino):
    """Redimensiona e salva o ícone."""
    icone = img.resize((tamanho, tamanho), Image.LANCZOS)
    icone.save(destino, 'PNG', optimize=True)
    print(f'  ✓ {destino} ({tamanho}x{tamanho})')

# Abrir a imagem original
img_orig = Image.open(LOGO_SRC).convert('RGBA')
print(f'Logo original: {img_orig.size[0]}x{img_orig.size[1]}px')

# Gerar ícone padrão (ic_launcher.png e ic_launcher_round.png)
print('\n── Gerando ícones padrão ──')
for pasta, tamanho in SIZES.items():
    dir_path = os.path.join(ANDROID_RES, pasta)
    os.makedirs(dir_path, exist_ok=True)
    
    # ic_launcher.png — ícone quadrado
    gerar_icone(img_orig, tamanho, os.path.join(dir_path, 'ic_launcher.png'))
    
    # ic_launcher_round.png — ícone redondo (mesma imagem, Android recorta em círculo)
    gerar_icone(img_orig, tamanho, os.path.join(dir_path, 'ic_launcher_round.png'))

# Gerar foreground do adaptive icon (ic_launcher_foreground.png)
# O foreground tem 108dp com 18dp de margem segura em cada lado
print('\n── Gerando ícones foreground (adaptive) ──')
for pasta, tamanho in FOREGROUND_SIZES.items():
    dir_path = os.path.join(ANDROID_RES, pasta)
    os.makedirs(dir_path, exist_ok=True)
    
    # Criar canvas do tamanho do foreground com fundo transparente
    canvas = Image.new('RGBA', (tamanho, tamanho), (0, 0, 0, 0))
    
    # Calcular margem segura (1/6 do tamanho total em cada lado)
    margem = tamanho // 6
    tamanho_logo = tamanho - (margem * 2)
    
    # Redimensionar a logo para caber na área segura
    logo_redim = img_orig.resize((tamanho_logo, tamanho_logo), Image.LANCZOS)
    
    # Colar a logo centralizada no canvas
    canvas.paste(logo_redim, (margem, margem), logo_redim)
    canvas.save(os.path.join(dir_path, 'ic_launcher_foreground.png'), 'PNG', optimize=True)
    print(f'  ✓ {pasta}/ic_launcher_foreground.png ({tamanho}x{tamanho}, logo {tamanho_logo}x{tamanho_logo})')

# Verificar se existe o diretório mipmap-anydpi-v26 para o adaptive icon XML
anydpi_dir = os.path.join(ANDROID_RES, 'mipmap-anydpi-v26')
os.makedirs(anydpi_dir, exist_ok=True)

# Criar/atualizar o ic_launcher.xml para adaptive icon com fundo branco-creme
ic_launcher_xml = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
'''
ic_launcher_round_xml = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
'''

with open(os.path.join(anydpi_dir, 'ic_launcher.xml'), 'w') as f:
    f.write(ic_launcher_xml)
with open(os.path.join(anydpi_dir, 'ic_launcher_round.xml'), 'w') as f:
    f.write(ic_launcher_round_xml)
print(f'\n  ✓ mipmap-anydpi-v26/ic_launcher.xml')
print(f'  ✓ mipmap-anydpi-v26/ic_launcher_round.xml')

# Criar/atualizar o arquivo de cor de fundo (creme do app)
values_dir = os.path.join(ANDROID_RES, 'values')
os.makedirs(values_dir, exist_ok=True)
colors_file = os.path.join(values_dir, 'ic_launcher_background.xml')
colors_xml = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#FBF7F4</color>
</resources>
'''
with open(colors_file, 'w') as f:
    f.write(colors_xml)
print(f'  ✓ values/ic_launcher_background.xml (cor: #FBF7F4 — creme do app)')

print('\n✅ Todos os ícones gerados com sucesso!')
print('\nResumo:')
for pasta, tamanho in SIZES.items():
    print(f'  {pasta}: {tamanho}x{tamanho}px')
