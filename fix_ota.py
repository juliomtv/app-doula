#!/usr/bin/env python3
"""
Correções do sistema OTA:
1. index.html: OTA verificado imediatamente (1s) ao abrir o app, na tela de login
2. index.html: Remover OTA duplicado do goApp (evitar dupla verificação)
3. admin.html: Adicionar verificação OTA com banner no topo do painel
"""

# ===== FIX index.html =====
with open('www/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

fixes = 0

# 1. Reduzir o timeout do OTA no init de 3000ms para 1000ms
# (já está na tela de login, não precisa esperar 3s)
old = '  // 4. Verifica atualizações OTA (após 3s para dar tempo de conectar)\n  setTimeout(verificarAtualizacao, 3000);'
new = '  // 4. Verifica atualizações OTA (após 1s — aparece na tela de login)\n  setTimeout(verificarAtualizacao, 1000);'
if old in c:
    c = c.replace(old, new, 1)
    print("✅ FIX 1: OTA timeout reduzido para 1s no init")
    fixes += 1
else:
    print("❌ FIX 1: timeout OTA não encontrado")

# 2. Remover verificarAtualizacao do goApp (já é chamado no init, não precisa duplicar)
old = '''function goApp(){
  navTo('home');
  // Verificar atualizações OTA ao entrar no app
  setTimeout(verificarAtualizacao, 2000);
}'''
new = '''function goApp(){
  navTo('home');
}'''
if old in c:
    c = c.replace(old, new, 1)
    print("✅ FIX 2: OTA removido do goApp (evitar duplicação)")
    fixes += 1
else:
    print("❌ FIX 2: goApp não encontrado")

with open('www/index.html', 'w', encoding='utf-8') as f:
    f.write(c)
print(f"✅ index.html salvo! ({fixes} fixes)")

# ===== FIX admin.html =====
with open('www/admin.html', 'r', encoding='utf-8') as f:
    a = f.read()

fixes_admin = 0

# 3. Adicionar CSS do banner OTA no admin.html
ota_css = """
/* ── OTA UPDATE BANNER ── */
#ota-banner{display:none;position:fixed;top:0;left:0;right:0;z-index:9999;background:linear-gradient(90deg,#2d6a4f,#40916c);color:white;padding:10px 20px;text-align:center;font-size:13px;font-weight:500;box-shadow:0 2px 12px rgba(0,0,0,.2);}
#ota-banner.show{display:flex;align-items:center;justify-content:center;gap:12px;}
#ota-banner button{background:white;color:#2d6a4f;border:none;border-radius:20px;padding:5px 14px;font-size:12px;font-weight:600;cursor:pointer;}
#ota-banner .ota-dismiss{background:transparent;color:rgba(255,255,255,.7);font-size:18px;padding:0 4px;line-height:1;}
"""

# Inserir CSS antes do fechamento do </style>
if '#ota-banner' not in a:
    a = a.replace('</style>', ota_css + '</style>', 1)
    print("✅ FIX 3: CSS do banner OTA adicionado ao admin.html")
    fixes_admin += 1
else:
    print("⚠️ CSS do banner OTA já existe no admin.html")

# 4. Adicionar o div do banner OTA logo após o <body>
ota_banner_html = """<div id="ota-banner">
  <span id="ota-banner-txt">🚀 Nova versão disponível!</span>
  <button onclick="otaAtualizarAdmin()">Atualizar agora</button>
  <button class="ota-dismiss" onclick="document.getElementById('ota-banner').classList.remove('show')">✕</button>
</div>
"""

if 'id="ota-banner"' not in a:
    a = a.replace('<body>', '<body>\n' + ota_banner_html, 1)
    print("✅ FIX 4: Banner OTA adicionado ao admin.html")
    fixes_admin += 1
else:
    print("⚠️ Banner OTA já existe no admin.html")

# 5. Adicionar funções JS de OTA no admin.html antes do </script> final
ota_js = """
// ════ OTA UPDATE (ADMIN) ════
const ADMIN_OTA_VERSION_KEY = 'ota_versao_instalada';
const ADMIN_OTA_SKIP_KEY    = 'ota_skip_versao';
function compararVersaoAdmin(a, b) {
  const pa = String(a).split('.').map(Number);
  const pb = String(b).split('.').map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const na = pa[i] || 0, nb = pb[i] || 0;
    if (na > nb) return true;
    if (na < nb) return false;
  }
  return false;
}
async function verificarAtualizacaoAdmin() {
  if (!API_URL) return;
  try {
    const res = await fetch(`${API_URL}/ota/versao`, { signal: AbortSignal.timeout(8000) });
    if (!res.ok) return;
    const dados = await res.json();
    const versaoServidor = dados.versao || '1.0.0';
    const versaoLocal    = localStorage.getItem(ADMIN_OTA_VERSION_KEY) || '0.0.0';
    const skipVersao     = localStorage.getItem(ADMIN_OTA_SKIP_KEY)    || '';
    if (skipVersao === versaoServidor) return;
    if (compararVersaoAdmin(versaoServidor, versaoLocal)) {
      const banner = document.getElementById('ota-banner');
      const txt    = document.getElementById('ota-banner-txt');
      if (banner) {
        if (txt) txt.textContent = `🚀 Nova versão ${versaoServidor} disponível! (você tem ${versaoLocal})`;
        banner.dataset.versaoNova = versaoServidor;
        banner.classList.add('show');
      }
    }
  } catch (e) { /* silencioso */ }
}
async function otaAtualizarAdmin() {
  const banner = document.getElementById('ota-banner');
  const versaoNova = banner ? banner.dataset.versaoNova : '';
  const txt = document.getElementById('ota-banner-txt');
  if (txt) txt.textContent = '⏳ Baixando atualização...';
  try {
    const res = await fetch(`${API_URL}/ota/index.html`, { signal: AbortSignal.timeout(30000) });
    if (!res.ok) throw new Error('Falha no download');
    if (txt) txt.textContent = '✅ Atualização concluída! Recarregando...';
    localStorage.setItem(ADMIN_OTA_VERSION_KEY, versaoNova || '');
    localStorage.removeItem(ADMIN_OTA_SKIP_KEY);
    setTimeout(() => window.location.reload(true), 1500);
  } catch (e) {
    if (txt) txt.textContent = '❌ Erro ao baixar. Verifique a conexão.';
  }
}
"""

if 'verificarAtualizacaoAdmin' not in a:
    # Inserir antes do último </script>
    last_script = a.rfind('</script>')
    if last_script >= 0:
        a = a[:last_script] + ota_js + '\n' + a[last_script:]
        print("✅ FIX 5: Funções OTA adicionadas ao admin.html")
        fixes_admin += 1
    else:
        print("❌ FIX 5: </script> não encontrado no admin.html")
else:
    print("⚠️ Funções OTA já existem no admin.html")

# 6. Chamar verificarAtualizacaoAdmin após o login bem-sucedido no admin
old_login_success = """    DB.set('nn_admin_session',true);
    document.getElementById('admin-login').style.display='none';
    document.getElementById('admin-shell').classList.add('active');
    renderDashboard();"""
new_login_success = """    DB.set('nn_admin_session',true);
    document.getElementById('admin-login').style.display='none';
    document.getElementById('admin-shell').classList.add('active');
    renderDashboard();
    // Verificar se há atualização disponível
    setTimeout(verificarAtualizacaoAdmin, 1500);"""
if old_login_success in a:
    a = a.replace(old_login_success, new_login_success, 1)
    print("✅ FIX 6: verificarAtualizacaoAdmin chamada após login no admin")
    fixes_admin += 1
else:
    print("❌ FIX 6: trecho do login admin não encontrado")

# 7. Também chamar na inicialização (se já tiver sessão salva)
old_auto_login = """    document.getElementById('admin-login').style.display='none';
    document.getElementById('admin-shell').classList.add('active');
    renderDashboard();"""
if old_auto_login in a:
    new_auto_login = """    document.getElementById('admin-login').style.display='none';
    document.getElementById('admin-shell').classList.add('active');
    renderDashboard();
    setTimeout(verificarAtualizacaoAdmin, 1500);"""
    # Substituir apenas a segunda ocorrência (auto-login na inicialização)
    idx = a.find(old_auto_login)
    idx2 = a.find(old_auto_login, idx + 1)
    if idx2 >= 0:
        a = a[:idx2] + new_auto_login + a[idx2 + len(old_auto_login):]
        print("✅ FIX 7: verificarAtualizacaoAdmin chamada no auto-login do admin")
        fixes_admin += 1
    else:
        print("⚠️ FIX 7: apenas uma ocorrência do trecho encontrada")
else:
    print("❌ FIX 7: trecho auto-login não encontrado")

with open('www/admin.html', 'w', encoding='utf-8') as f:
    f.write(a)
print(f"✅ admin.html salvo! ({fixes_admin} fixes)")
print(f"\n✅ Total: {fixes + fixes_admin} correções aplicadas!")
