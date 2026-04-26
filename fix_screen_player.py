with open('www/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ── Fix 1: .screen nao deve ter height quando display:none ──
content = content.replace(
    '.screen{display:none;flex-direction:column;height:100vh;background:var(--warm);overflow:hidden;}',
    '.screen{display:none;flex-direction:column;background:var(--warm);}'
)
content = content.replace(
    '.screen.active{display:flex;flex-direction:column;height:100vh;overflow:hidden;}',
    '.screen.active{display:flex;flex-direction:column;height:100vh;overflow:hidden;}'
)
# Caso o .screen.active ainda seja o simples
content = content.replace(
    '.screen.active{display:flex;}',
    '.screen.active{display:flex;flex-direction:column;height:100vh;overflow:hidden;}'
)

# ── Fix 2: #conteudo nao deve ter display:flex fixo ──
content = content.replace(
    '#conteudo{display:flex;flex-direction:column;height:100vh;overflow:hidden;}',
    '#conteudo.active{flex-direction:column;height:100vh;overflow:hidden;}'
)
# Caso já tenha sido corrigido para .active
content = content.replace(
    '#conteudo.active{flex-direction:column;height:100vh;overflow:hidden;}',
    '#conteudo.active{flex-direction:column;height:100vh;overflow:hidden;}'
)

print('CSS corrigido: OK')

# ── Fix 3: substituir o bloco do player por thumbnail clicável ──
# Encontrar o bloco exato
marker_start = '  // Montar player'
marker_end_options = [
    "playerArea.innerHTML = `<div class=\"player-placeholder\"><div class=\"pp-icon\">\u26a0\ufe0f</div><p>URL do v\u00eddeo n\u00e3o dispon\u00edvel</p></div>`;\n  }",
]

idx_start = content.find(marker_start)
if idx_start == -1:
    print('FAIL: marcador de inicio do player nao encontrado')
else:
    # Encontrar o fim do bloco (próximo "}" após o último innerHTML do player)
    search_from = idx_start
    idx_end = -1
    for marker_end in marker_end_options:
        pos = content.find(marker_end, search_from)
        if pos != -1:
            idx_end = pos + len(marker_end)
            break

    if idx_end == -1:
        # Tentar encontrar pelo padrão genérico
        import re
        m = re.search(r'// Montar player.*?playerArea\.innerHTML = `<div class="player-placeholder"><div class="pp-icon">.*?</div>`;\n  \}', content[idx_start:], re.DOTALL)
        if m:
            idx_end = idx_start + m.end()
        else:
            print('FAIL: fim do bloco do player nao encontrado')
            idx_end = -1

    if idx_end != -1:
        new_player_block = '''  // Montar player — abre no YouTube/link externo (sem iframe para evitar erro 153)
  const ytId2 = getYTId(url);
  const ytThumb2 = ytId2 ? `https://img.youtube.com/vi/${ytId2}/hqdefault.jpg` : null;
  const openUrl2 = ytId2 ? `https://www.youtube.com/watch?v=${ytId2}` : url;
  if (url && url !== '#') {
    const thumbStyle = ytThumb2 ? `background-image:url('${ytThumb2}');background-size:cover;background-position:center;` : 'background:linear-gradient(135deg,#3a2820,#7a5a50);';
    playerArea.innerHTML = `
      <div class="player-placeholder" style="cursor:pointer;${thumbStyle}" onclick="window.open('${openUrl2}','_blank')">
        <div style="position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;gap:12px;background:rgba(0,0,0,0.35);padding:24px 20px;border-radius:12px;">
          <div style="width:60px;height:60px;border-radius:50%;background:rgba(255,255,255,.92);display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 4px 16px rgba(0,0,0,.3);">&#9654;</div>
          <div style="font-size:14px;font-weight:600;color:white;text-shadow:0 1px 4px rgba(0,0,0,.6);">Toque para assistir</div>
          <div style="font-size:11px;color:rgba(255,255,255,.85);text-shadow:0 1px 3px rgba(0,0,0,.5);">${ytId2 ? 'Abre no YouTube' : 'Abre o v&iacute;deo'}</div>
        </div>
      </div>`;
  } else {
    playerArea.innerHTML = `<div class="player-placeholder"><div class="pp-icon">&#9888;&#65039;</div><p>URL do v&iacute;deo n&atilde;o dispon&iacute;vel</p></div>`;
  }'''
        content = content[:idx_start] + new_player_block + content[idx_end:]
        print('Player substituido: OK')

with open('www/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('index.html salvo.')
