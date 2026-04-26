with open('www/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ── 1. Adicionar CSS do modal OTA ──
ota_css = """
/* ── OTA UPDATE MODAL ── */
#ota-modal{position:fixed;inset:0;background:rgba(58,40,32,.6);backdrop-filter:blur(6px);display:none;align-items:center;justify-content:center;z-index:9999;padding:20px;}
#ota-modal.active{display:flex;}
.ota-box{background:white;border-radius:24px;width:100%;max-width:360px;padding:28px 24px;box-shadow:0 24px 64px rgba(0,0,0,.25);text-align:center;}
.ota-icon{font-size:40px;margin-bottom:12px;}
.ota-title{font-family:'Cormorant Garamond',serif;font-size:22px;font-style:italic;color:var(--dark);margin-bottom:6px;}
.ota-version{font-size:12px;color:var(--light);margin-bottom:10px;}
.ota-notas{font-size:13px;color:var(--mid);background:var(--rose-pale);border-radius:10px;padding:10px 14px;margin-bottom:20px;line-height:1.5;text-align:left;}
.ota-progress{height:6px;background:#f0e8e4;border-radius:3px;overflow:hidden;margin-bottom:8px;display:none;}
.ota-progress-fill{height:100%;background:linear-gradient(90deg,var(--rose),#c9907a);border-radius:3px;width:0%;transition:width .3s;}
.ota-progress-txt{font-size:11px;color:var(--light);margin-bottom:16px;display:none;}
.ota-btns{display:flex;gap:10px;}
.ota-btn-update{flex:1;background:var(--rose);color:white;border:none;border-radius:50px;padding:12px;font-size:14px;font-weight:500;cursor:pointer;}
.ota-btn-later{flex:1;background:var(--rose-pale);color:var(--mid);border:none;border-radius:50px;padding:12px;font-size:14px;cursor:pointer;}
"""

# Inserir o CSS antes do fechamento do </style>
if '#ota-modal' not in content:
    # Encontrar o primeiro </style>
    idx = content.find('</style>')
    if idx != -1:
        content = content[:idx] + ota_css + content[idx:]
        print('CSS OTA adicionado: OK')
    else:
        print('FAIL: </style> nao encontrado')
else:
    print('CSS OTA já existe: OK')

# ── 2. Adicionar o modal HTML antes do </body> ──
ota_modal_html = """
<!-- ── OTA UPDATE MODAL ── -->
<div id="ota-modal">
  <div class="ota-box">
    <div class="ota-icon">🚀</div>
    <div class="ota-title">Nova versão disponível!</div>
    <div class="ota-version" id="ota-version-txt"></div>
    <div class="ota-notas" id="ota-notas-txt"></div>
    <div class="ota-progress" id="ota-progress">
      <div class="ota-progress-fill" id="ota-progress-fill"></div>
    </div>
    <div class="ota-progress-txt" id="ota-progress-txt">Baixando atualização...</div>
    <div class="ota-btns" id="ota-btns">
      <button class="ota-btn-later" onclick="otaAdiar()">Agora não</button>
      <button class="ota-btn-update" onclick="otaAtualizar()">✓ Atualizar agora</button>
    </div>
  </div>
</div>
"""

if 'id="ota-modal"' not in content:
    content = content.replace('</body>', ota_modal_html + '\n</body>')
    print('Modal OTA adicionado: OK')
else:
    print('Modal OTA já existe: OK')

# ── 3. Adicionar a lógica JS do OTA ──
ota_js = """
// ════ OTA — ATUALIZAÇÃO OVER THE AIR ════
const OTA_VERSION_KEY = 'ota_versao_instalada';
const OTA_SKIP_KEY    = 'ota_skip_versao';

async function verificarAtualizacao() {
  if (!API_URL) return; // Sem servidor configurado, pula
  try {
    const res = await fetch(`${API_URL}/ota/versao`, { signal: AbortSignal.timeout(8000) });
    if (!res.ok) return;
    const dados = await res.json();
    const versaoServidor = dados.versao || '1.0.0';
    const hashServidor   = dados.hash   || '';
    const versaoLocal    = localStorage.getItem(OTA_VERSION_KEY) || '0.0.0';
    const skipVersao     = localStorage.getItem(OTA_SKIP_KEY)    || '';

    // Se o usuário escolheu "Agora não" para esta versão, não mostra de novo nesta sessão
    if (skipVersao === versaoServidor) return;

    // Compara versões ou hash
    if (versaoServidor !== versaoLocal || (hashServidor && hashServidor !== localStorage.getItem('ota_hash_local'))) {
      // Há atualização disponível — mostrar modal
      mostrarModalOTA(versaoServidor, versaoLocal, dados.notas || 'Melhorias e correções de bugs.', dados.obrigatoria || false);
    }
  } catch (e) {
    // Silencioso — sem servidor ou sem internet, ignora
  }
}

function mostrarModalOTA(versaoNova, versaoAtual, notas, obrigatoria) {
  const modal   = document.getElementById('ota-modal');
  const verTxt  = document.getElementById('ota-version-txt');
  const notasTxt= document.getElementById('ota-notas-txt');
  const btns    = document.getElementById('ota-btns');
  if (!modal) return;

  if (verTxt)   verTxt.textContent  = `Versão ${versaoNova} disponível (você tem ${versaoAtual})`;
  if (notasTxt) notasTxt.textContent = notas;

  // Se atualização obrigatória, esconde o botão "Agora não"
  if (btns && obrigatoria) {
    btns.innerHTML = `<button class="ota-btn-update" style="width:100%" onclick="otaAtualizar()">✓ Atualizar agora</button>`;
  }

  modal.classList.add('active');
  // Salva a versão nova para usar no download
  modal.dataset.versaoNova = versaoNova;
}

function otaAdiar() {
  const modal = document.getElementById('ota-modal');
  if (!modal) return;
  // Marca para não mostrar de novo nesta sessão
  localStorage.setItem(OTA_SKIP_KEY, modal.dataset.versaoNova || '');
  modal.classList.remove('active');
}

async function otaAtualizar() {
  const modal    = document.getElementById('ota-modal');
  const progress = document.getElementById('ota-progress');
  const fill     = document.getElementById('ota-progress-fill');
  const txt      = document.getElementById('ota-progress-txt');
  const btns     = document.getElementById('ota-btns');
  if (!modal || !API_URL) return;

  // Mostrar progresso
  if (btns)     btns.style.display    = 'none';
  if (progress) progress.style.display = 'block';
  if (txt)      txt.style.display     = 'block';
  if (fill)     fill.style.width      = '20%';
  if (txt)      txt.textContent       = 'Baixando atualização...';

  try {
    // Baixar o novo index.html do servidor
    const res = await fetch(`${API_URL}/ota/index.html`, { signal: AbortSignal.timeout(30000) });
    if (!res.ok) throw new Error('Falha no download');
    if (fill) fill.style.width = '60%';

    const novoHtml = await res.text();
    if (fill) fill.style.width = '80%';
    if (txt)  txt.textContent  = 'Aplicando atualização...';

    // Verificar se o Capacitor está disponível (APK)
    if (window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform()) {
      // No APK: usar o plugin de filesystem do Capacitor para sobrescrever o index.html
      try {
        const { Filesystem, Directory } = await import('@capacitor/filesystem');
        await Filesystem.writeFile({
          path: 'index.html',
          data: btoa(unescape(encodeURIComponent(novoHtml))),
          directory: Directory.Data,
          encoding: 'base64'
        });
        if (fill) fill.style.width = '100%';
        if (txt)  txt.textContent  = 'Atualização concluída! Reiniciando...';
        // Salvar nova versão
        const verDados = await (await fetch(`${API_URL}/ota/versao`)).json();
        localStorage.setItem(OTA_VERSION_KEY, verDados.versao || '');
        localStorage.setItem('ota_hash_local', verDados.hash || '');
        localStorage.removeItem(OTA_SKIP_KEY);
        setTimeout(() => window.location.reload(), 1500);
      } catch (capErr) {
        // Fallback: recarregar a página (o servidor serve o novo index)
        if (fill) fill.style.width = '100%';
        localStorage.setItem(OTA_VERSION_KEY, modal.dataset.versaoNova || '');
        localStorage.removeItem(OTA_SKIP_KEY);
        setTimeout(() => window.location.reload(), 1000);
      }
    } else {
      // No navegador (modo desenvolvimento): simular atualização
      if (fill) fill.style.width = '100%';
      if (txt)  txt.textContent  = 'Atualização concluída! Recarregando...';
      localStorage.setItem(OTA_VERSION_KEY, modal.dataset.versaoNova || '');
      localStorage.removeItem(OTA_SKIP_KEY);
      setTimeout(() => window.location.reload(true), 1500);
    }
  } catch (e) {
    if (progress) progress.style.display = 'none';
    if (txt)      txt.style.display      = 'none';
    if (btns)     btns.style.display     = 'flex';
    alert('Erro ao baixar atualização. Verifique a conexão com o servidor.');
  }
}
"""

if 'OTA — ATUALIZAÇÃO OVER THE AIR' not in content:
    # Inserir antes do bloco INIT
    content = content.replace('// ════ INIT ════', ota_js + '\n// ════ INIT ════')
    print('JS OTA adicionado: OK')
else:
    print('JS OTA já existe: OK')

# ── 4. Chamar verificarAtualizacao() no bloco INIT ──
old_init = '  // 1. Tenta atualizar a URL pública do tunnel silenciosamente\n  await descobrirUrlPublica();'
new_init = '''  // 1. Tenta atualizar a URL pública do tunnel silenciosamente
  await descobrirUrlPublica();
  // 1b. Verifica se há atualização disponível (OTA)
  verificarAtualizacao();'''

if 'verificarAtualizacao()' not in content:
    if old_init in content:
        content = content.replace(old_init, new_init)
        print('Chamada OTA no INIT: OK')
    else:
        print('WARN: bloco INIT nao encontrado para inserir verificarAtualizacao()')
else:
    print('Chamada OTA já existe: OK')

with open('www/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('index.html salvo.')
