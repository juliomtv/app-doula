#!/usr/bin/env python3
"""Corrige 3 problemas no index.html:
1. OTA: lógica de comparação semântica de versões + salvar versão após update
2. Modal admin: fechar via style.display em vez de classList
3. Maternidade: fechar modal após salvar
"""

with open('www/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

fixes = 0

# ══════════════════════════════════════════════════════════════════
# FIX 1 — OTA: comparação semântica de versões
# Problema: versaoServidor !== versaoLocal usa string comparison
# e o hash local nunca foi salvo, então sempre dispara
# Solução: comparar versões como tuplas numéricas (semver)
# ══════════════════════════════════════════════════════════════════
old = """async function verificarAtualizacao() {
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
}"""

new = """function compararVersao(a, b) {
  // Retorna true se versão a > versão b (ex: "1.0.3" > "1.0.2")
  const pa = a.split('.').map(Number);
  const pb = b.split('.').map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const na = pa[i] || 0, nb = pb[i] || 0;
    if (na > nb) return true;
    if (na < nb) return false;
  }
  return false; // iguais
}
async function verificarAtualizacao() {
  if (!API_URL) return; // Sem servidor configurado, pula
  try {
    const res = await fetch(`${API_URL}/ota/versao`, { signal: AbortSignal.timeout(8000) });
    if (!res.ok) return;
    const dados = await res.json();
    const versaoServidor = dados.versao || '1.0.0';
    const versaoLocal    = localStorage.getItem(OTA_VERSION_KEY) || '0.0.0';
    const skipVersao     = localStorage.getItem(OTA_SKIP_KEY)    || '';
    // Se o usuário escolheu "Agora não" para esta versão exata, não mostra de novo
    if (skipVersao === versaoServidor) return;
    // Só mostra se a versão do servidor for MAIOR que a local
    if (compararVersao(versaoServidor, versaoLocal)) {
      mostrarModalOTA(versaoServidor, versaoLocal, dados.notas || 'Melhorias e correções de bugs.', dados.obrigatoria || false);
    }
  } catch (e) {
    // Silencioso — sem servidor ou sem internet, ignora
  }
}"""

if old in c:
    c = c.replace(old, new, 1)
    print("✅ FIX 1: OTA com comparação semântica de versões")
    fixes += 1
else:
    print("❌ FIX 1: padrão OTA não encontrado")

# ══════════════════════════════════════════════════════════════════
# FIX 2 — Modal admin: unificar mecanismo de abertura/fechamento
# Problema: modal usa style="display:none" mas closeModal usa classList
# Solução: remover o style inline e usar a classe .active como todos os outros modais
# ══════════════════════════════════════════════════════════════════
old = '<div class="modal-overlay" id="modal-admin-login" style="display:none;z-index:9999;">'
new = '<div class="modal-overlay" id="modal-admin-login" style="z-index:9999;">'
if old in c:
    c = c.replace(old, new, 1)
    print("✅ FIX 2a: Removido style display:none do modal admin (usa .active agora)")
    fixes += 1
else:
    print("❌ FIX 2a: padrão modal-admin-login não encontrado")

# Corrigir abrirLoginAdmin para usar classList.add('active') em vez de style.display
old = """function abrirLoginAdmin() {
  document.getElementById('admin-login-user').value = '';
  document.getElementById('admin-login-pass').value = '';
  document.getElementById('admin-login-err').textContent = '';
  document.getElementById('modal-admin-login').style.display = 'flex';
}"""
new = """function abrirLoginAdmin() {
  document.getElementById('admin-login-user').value = '';
  document.getElementById('admin-login-pass').value = '';
  document.getElementById('admin-login-err').textContent = '';
  document.getElementById('modal-admin-login').classList.add('active');
}"""
if old in c:
    c = c.replace(old, new, 1)
    print("✅ FIX 2b: abrirLoginAdmin usa classList.add('active')")
    fixes += 1
else:
    print("❌ FIX 2b: abrirLoginAdmin não encontrado")

# Corrigir confirmarLoginAdmin para usar closeModal em vez de style
old = """      closeModal('modal-admin-login');
      window.location.href = 'admin.html';"""
new = """      closeModal('modal-admin-login');
      setTimeout(() => { window.location.href = 'admin.html'; }, 200);"""
if old in c:
    c = c.replace(old, new, 1)
    print("✅ FIX 2c: redirecionamento com delay após fechar modal")
    fixes += 1
else:
    print("❌ FIX 2c: padrão confirmarLoginAdmin não encontrado")

# ══════════════════════════════════════════════════════════════════
# FIX 3 — Maternidade: fechar modal após salvar + feedback visual
# ══════════════════════════════════════════════════════════════════
old = """function saveMaternidade(){
  const mat = DB.get(`nn_mat_${currentUser.id}`) || { checklists: JSON.parse(JSON.stringify(defaultMatChecklist)) };
  mat.nome = document.getElementById('mat-nome').value;
  mat.cidade = document.getElementById('mat-cidade').value;
  
  const key=`nn_mat_${currentUser.id}`;
  DB.set(key, mat);
  document.getElementById('mat-msg').textContent='Informações salvas com sucesso!';
  document.getElementById('mat-msg').style.color='var(--ok)';
  setTimeout(()=>{document.getElementById('mat-msg').textContent='';},2000);
}"""
new = """function saveMaternidade(){
  const mat = DB.get(`nn_mat_${currentUser.id}`) || { checklists: JSON.parse(JSON.stringify(defaultMatChecklist)) };
  mat.nome = document.getElementById('mat-nome').value;
  mat.cidade = document.getElementById('mat-cidade').value;
  const key=`nn_mat_${currentUser.id}`;
  DB.set(key, mat);
  showToast('Maternidade salva! 🏥');
  setTimeout(() => closeModal('modal-maternidade'), 400);
}"""
if old in c:
    c = c.replace(old, new, 1)
    print("✅ FIX 3: saveMaternidade fecha modal após salvar")
    fixes += 1
else:
    print("❌ FIX 3: saveMaternidade não encontrado")

# ══════════════════════════════════════════════════════════════════
# FIX 4 — Plano de Parto: fechar modal após salvar
# ══════════════════════════════════════════════════════════════════
old = """  document.getElementById('pp-msg').textContent='Plano salvo com sucesso!';
  document.getElementById('pp-msg').style.color='var(--ok)';
  setTimeout(()=>{document.getElementById('pp-msg').textContent='';},2000);
}"""
new = """  showToast('Plano de parto salvo! 📋');
  setTimeout(() => closeModal('modal-plano-parto'), 400);
}"""
if old in c:
    c = c.replace(old, new, 1)
    print("✅ FIX 4: savePlanoParto fecha modal após salvar")
    fixes += 1
else:
    print("❌ FIX 4: savePlanoParto msg não encontrado")

with open('www/index.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n✅ {fixes} correções aplicadas. Arquivo salvo!")
