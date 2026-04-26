"""
Script para aplicar a lógica de auto-descoberta de URL do servidor nos arquivos HTML.

Estratégia:
- O app guarda a URL BASE do servidor (IP local, ex: http://192.168.1.15:5000)
  configurada uma única vez pelo usuário no campo de login.
- Ao iniciar, o app chama GET /server-info na URL base e recebe a url_publica do tunnel.
- Se a url_publica estiver disponível, usa ela automaticamente como API_URL.
- Isso acontece em background, sem mostrar nada na tela para o usuário.
- O campo de URL no login passa a ser "URL Base do Servidor" (IP local) — configurado
  uma única vez e raramente muda.
"""

import re

# ─────────────────────────────────────────────────────────────────────────────
# BLOCO DE CONFIGURAÇÃO DE API — substituído nos 3 arquivos
# ─────────────────────────────────────────────────────────────────────────────

NEW_API_BLOCK = """// ════ CONFIGURAÇÃO DINÂMICA DA API ════
// URL_BASE: IP local do servidor (ex: http://192.168.1.15:5000) — configurado uma vez
// API_URL: URL ativa usada nas requisições (pode ser a url_publica do tunnel)
let URL_BASE = localStorage.getItem('url_base') || '';
let API_URL  = localStorage.getItem('api_url')  || URL_BASE;

const DB = {
  get:(k)=>{ try{return JSON.parse(localStorage.getItem(k));}catch{return null;}},
  set:(k,v)=>localStorage.setItem(k,JSON.stringify(v)),
  del:(k)=>localStorage.removeItem(k)
};

function normalizeUrl(url) {
  if(!url) return '';
  url = url.trim();
  if(!url.startsWith('http')) url = 'http://' + url;
  return url.replace(/\\/$/, '');
}

function setUrlBase(url) {
  url = normalizeUrl(url);
  if(!url) return;
  URL_BASE = url;
  localStorage.setItem('url_base', url);
  // Ao definir a base, usa ela como API_URL até descobrir a pública
  if(!API_URL) {
    API_URL = url;
    localStorage.setItem('api_url', url);
  }
  console.log('[API] URL Base definida:', URL_BASE);
}

function setApiUrl(url) {
  url = normalizeUrl(url);
  if(!url) return;
  API_URL = url;
  localStorage.setItem('api_url', url);
  console.log('[API] URL ativa atualizada:', API_URL);
}

/**
 * Busca /server-info na URL_BASE e atualiza API_URL com a url_publica do tunnel.
 * Chamada silenciosamente ao iniciar o app — sem interação do usuário.
 */
async function descobrirUrlPublica() {
  if(!URL_BASE) return;
  try {
    const res = await fetch(`${URL_BASE}/server-info`, {
      signal: AbortSignal.timeout(8000)
    });
    if(!res.ok) return;
    const info = await res.json();
    if(info && info.url_publica) {
      setApiUrl(info.url_publica);
      console.log('[API] URL pública do tunnel obtida:', info.url_publica);
    } else {
      // Tunnel não ativo: usa URL_BASE diretamente
      setApiUrl(URL_BASE);
      console.log('[API] Tunnel inativo, usando URL base:', URL_BASE);
    }
  } catch(e) {
    console.warn('[API] Não foi possível obter URL pública, usando URL base:', URL_BASE);
    if(URL_BASE && !API_URL) setApiUrl(URL_BASE);
  }
}"""

# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÃO apiFetch — mesma para todos os arquivos
# ─────────────────────────────────────────────────────────────────────────────

NEW_APIFETCH = """async function apiFetch(endpoint, options = {}) {
  try {
    if(!API_URL) return { status: 'error', message: 'Servidor não configurado.' };
    const url = `${API_URL}/${endpoint.replace(/^\\//, '')}`;
    const res = await fetch(url, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
      signal: AbortSignal.timeout(15000)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error('[API] Erro:', e, 'URL:', API_URL);
    return {
      status: 'error',
      message: `Não foi possível conectar ao servidor. Verifique se ele está ligado.`
    };
  }
}"""

# ─────────────────────────────────────────────────────────────────────────────
# index.html
# ─────────────────────────────────────────────────────────────────────────────

def patch_index(content):
    # 1. Campo de URL no login: de "URL do Servidor" para "URL Base do Servidor (IP local)"
    old = '''    <div class="field">
      <label>URL do Servidor</label>
      <input type="text" id="l-api-url" placeholder="https://xxxx.trycloudflare.com" value="" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false">
      <small style="font-size:11px;color:var(--light);margin-top:4px;display:block;line-height:1.5;">Cole a URL que aparece no terminal do servidor ao iniciar.<br>Ex: <strong>https://xxxx.trycloudflare.com</strong> (funciona em qualquer rede)<br>Ou: <strong>http://192.168.1.15:5000</strong> (somente Wi-Fi local)</small>
    </div>'''
    new = '''    <div class="field" id="campo-url-servidor" style="display:none;">
      <label>URL Base do Servidor (IP local)</label>
      <input type="text" id="l-api-url" placeholder="http://192.168.1.15:5000" value="" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false">
      <small style="font-size:11px;color:var(--light);margin-top:4px;display:block;line-height:1.5;">IP local do computador onde o servidor roda.<br>Configure uma única vez. Ex: <strong>http://192.168.1.15:5000</strong></small>
    </div>'''
    if old in content:
        content = content.replace(old, new, 1)
        print('[index.html] Edit 1 (campo URL): OK')
    else:
        print('[index.html] Edit 1: FAIL')

    # 2. Substituir bloco de configuração da API
    old2_pattern = r'// ════ CONFIGURAÇÃO DINÂMICA DA API ════.*?if \(document\.readyState !== .loading.\) preencherCampoUrl\(\);'
    match = re.search(old2_pattern, content, re.DOTALL)
    if match:
        content = content[:match.start()] + NEW_API_BLOCK + content[match.end():]
        print('[index.html] Edit 2 (bloco API): OK')
    else:
        print('[index.html] Edit 2: FAIL')

    # 3. Substituir apiFetch
    old3_pattern = r'// ════ API FETCH HELPERS ════\nasync function apiFetch\(endpoint.*?\n\}'
    match3 = re.search(old3_pattern, content, re.DOTALL)
    if match3:
        content = content[:match3.start()] + '// ════ API FETCH HELPERS ════\n' + NEW_APIFETCH + content[match3.end():]
        print('[index.html] Edit 3 (apiFetch): OK')
    else:
        print('[index.html] Edit 3: FAIL')

    # 4. Substituir doLogin para usar URL_BASE e descoberta automática
    old4 = '''async function doLogin(){
  const email=document.getElementById('l-email').value.trim().toLowerCase();
  const senha=document.getElementById('l-senha').value;
  const customUrl=document.getElementById('l-api-url').value.trim();
  const errEl=document.getElementById('l-err');
  // Validação: URL do servidor é obrigatória
  if(!customUrl && !API_URL){
    errEl.textContent='⚠️ Informe a URL do servidor antes de entrar.';
    errEl.style.color='#c0392b';
    document.getElementById('l-api-url').focus();
    return;
  }
  if(customUrl){
    setApiUrl(customUrl);
    errEl.textContent='🔄 Conectando ao servidor...';
    errEl.style.color='var(--mid)';
  }
  // Tentar login via API
  const res = await apiFetch('/api/login', {
    method: 'POST',
    body: JSON.stringify({ email, senha })
  });
  if(res && res.status === 'success'){
    currentUser = res.user;
    DB.set('nn_session', currentUser.id);
    errEl.textContent='';
    goApp();
  } else {
    // Fallback para localStorage se API falhar (modo offline parcial)
    const users=DB.get('nn_users')||[];
    const u=users.find(x=>x.email.toLowerCase()===email && x.senha===senha && x.ativo);
    if(u){
      currentUser=u;
      DB.set('nn_session',u.id);
      errEl.textContent='';
      goApp();
    } else {
      // Mensagem de erro clara para o usuário
      let msg;
      if(res && res.status === 'error' && res.message && res.message.includes('conectar')){
        msg = '❌ Não foi possível conectar ao servidor. Verifique se o servidor está ligado e se a URL está correta.';
      } else if(res && res.status === 'error'){
        msg = res.message;
      } else {
        msg = 'E-mail ou senha incorretos.';
      }
      errEl.textContent = msg;
      errEl.style.color = '#c0392b';
    }
  }
}'''
    new4 = '''async function doLogin(){
  const email=document.getElementById('l-email').value.trim().toLowerCase();
  const senha=document.getElementById('l-senha').value;
  const campoUrl=document.getElementById('l-api-url');
  const customUrl=campoUrl ? campoUrl.value.trim() : '';
  const errEl=document.getElementById('l-err');

  // Se o usuário digitou uma URL base manualmente, salva e tenta descobrir a pública
  if(customUrl){
    setUrlBase(customUrl);
    errEl.textContent='🔄 Conectando ao servidor...';
    errEl.style.color='var(--mid)';
    await descobrirUrlPublica();
  }

  if(!API_URL){
    errEl.textContent='⚠️ Configure a URL do servidor. Toque no ícone ⚙️ abaixo.';
    errEl.style.color='#c0392b';
    return;
  }

  errEl.textContent='🔄 Entrando...';
  errEl.style.color='var(--mid)';

  const res = await apiFetch('/api/login', {
    method: 'POST',
    body: JSON.stringify({ email, senha })
  });
  if(res && res.status === 'success'){
    currentUser = res.user;
    DB.set('nn_session', currentUser.id);
    errEl.textContent='';
    goApp();
  } else {
    // Fallback para localStorage se API falhar
    const users=DB.get('nn_users')||[];
    const u=users.find(x=>x.email.toLowerCase()===email && x.senha===senha && x.ativo);
    if(u){
      currentUser=u;
      DB.set('nn_session',u.id);
      errEl.textContent='';
      goApp();
    } else {
      const msg = (res && res.status === 'error') ? res.message : 'E-mail ou senha incorretos.';
      errEl.textContent = msg;
      errEl.style.color = '#c0392b';
    }
  }
}'''
    if old4 in content:
        content = content.replace(old4, new4, 1)
        print('[index.html] Edit 4 (doLogin): OK')
    else:
        print('[index.html] Edit 4: FAIL')

    # 5. Substituir bloco INIT para chamar descobrirUrlPublica
    old5 = '''// ════ INIT ════
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&document.getElementById('login').classList.contains('active'))doLogin();});
seedData();
loadDicas();
// Preenche o campo de URL com o valor salvo no localStorage
preencherCampoUrl();
// Tenta restaurar sessão salva (somente se houver URL configurada)
(async function initSession(){
  const savedSession=DB.get('nn_session');
  if(savedSession && API_URL){
    // Tenta validar sessão via API
    const users = await apiFetch('/api/users');
    if(users && Array.isArray(users)){
      const u=users.find(x=>x.id===savedSession&&x.ativo);
      if(u){currentUser=u;goApp();syncUserData();return;}
    }
    // Fallback: usa dados locais se API não responder
    const localUsers=DB.get('nn_users')||[];
    const u=localUsers.find(x=>x.id===savedSession&&x.ativo);
    if(u){currentUser=u;goApp();syncUserData();}
  }
})();
setInterval(syncUserData, 30000);
setInterval(loadDicas, 60000);'''
    new5 = '''// ════ INIT ════
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&document.getElementById('login').classList.contains('active'))doLogin();});
seedData();
// Inicialização assíncrona: descobre URL pública e restaura sessão
(async function init(){
  // 1. Tenta atualizar a URL pública do tunnel silenciosamente
  await descobrirUrlPublica();

  // 2. Preenche o campo de URL base (oculto) com o valor salvo
  const campoUrl = document.getElementById('l-api-url');
  if(campoUrl && URL_BASE) campoUrl.value = URL_BASE;

  // 3. Carrega dicas
  loadDicas();

  // 4. Tenta restaurar sessão salva
  const savedSession=DB.get('nn_session');
  if(savedSession && API_URL){
    const users = await apiFetch('/api/users');
    if(users && Array.isArray(users)){
      const u=users.find(x=>x.id===savedSession&&x.ativo);
      if(u){currentUser=u;goApp();syncUserData();return;}
    }
    // Fallback: usa dados locais se API não responder
    const localUsers=DB.get('nn_users')||[];
    const u=localUsers.find(x=>x.id===savedSession&&x.ativo);
    if(u){currentUser=u;goApp();syncUserData();}
  }
})();
// Atualiza URL pública a cada 5 minutos (caso o tunnel reinicie)
setInterval(descobrirUrlPublica, 5 * 60 * 1000);
setInterval(syncUserData, 30000);
setInterval(loadDicas, 60000);'''
    if old5 in content:
        content = content.replace(old5, new5, 1)
        print('[index.html] Edit 5 (INIT): OK')
    else:
        print('[index.html] Edit 5: FAIL')

    # 6. Adicionar botão de configuração de servidor no login (ícone ⚙️ discreto)
    old6 = '''    <button class="btn-rose" onclick="doLogin()">Entrar</button>
    <div class="login-err" id="l-err"></div>
    <div class="login-note">Não tem conta? Peça à sua doula para criar seu acesso 🌺</div>'''
    new6 = '''    <button class="btn-rose" onclick="doLogin()">Entrar</button>
    <div class="login-err" id="l-err"></div>
    <div class="login-note">Não tem conta? Peça à sua doula para criar seu acesso 🌺</div>
    <div style="text-align:center;margin-top:8px;">
      <button onclick="toggleCampoUrl()" style="background:none;border:none;color:var(--light);font-size:11px;cursor:pointer;padding:4px 8px;">⚙️ Configurar servidor</button>
    </div>'''
    if old6 in content:
        content = content.replace(old6, new6, 1)
        print('[index.html] Edit 6 (botão config): OK')
    else:
        print('[index.html] Edit 6: FAIL')

    # 7. Adicionar função toggleCampoUrl após setApiUrl
    old7 = '''function setApiUrl(url) {
  url = normalizeUrl(url);
  if(!url) return;
  API_URL = url;
  localStorage.setItem('api_url', url);
  console.log('[API] URL ativa atualizada:', API_URL);
}'''
    new7 = '''function setApiUrl(url) {
  url = normalizeUrl(url);
  if(!url) return;
  API_URL = url;
  localStorage.setItem('api_url', url);
  console.log('[API] URL ativa atualizada:', API_URL);
}
function toggleCampoUrl() {
  const campo = document.getElementById('campo-url-servidor');
  if(!campo) return;
  campo.style.display = campo.style.display === 'none' ? 'block' : 'none';
}'''
    if old7 in content:
        content = content.replace(old7, new7, 1)
        print('[index.html] Edit 7 (toggleCampoUrl): OK')
    else:
        print('[index.html] Edit 7: FAIL')

    return content


# ─────────────────────────────────────────────────────────────────────────────
# app.html
# ─────────────────────────────────────────────────────────────────────────────

def patch_app(content):
    # 1. Campo de URL no login
    old = '''    <div class="field">
      <label>URL do Servidor</label>
      <input type="text" id="l-api-url" placeholder="https://xxxx.trycloudflare.com" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false">
      <small style="font-size:11px;color:var(--light);margin-top:4px;display:block;line-height:1.5;">Cole a URL que aparece no terminal do servidor.<br>Ex: <strong>https://xxxx.trycloudflare.com</strong></small>
    </div>'''
    new = '''    <div class="field" id="campo-url-servidor" style="display:none;">
      <label>URL Base do Servidor (IP local)</label>
      <input type="text" id="l-api-url" placeholder="http://192.168.1.15:5000" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false">
      <small style="font-size:11px;color:var(--light);margin-top:4px;display:block;line-height:1.5;">IP local do computador onde o servidor roda.<br>Configure uma única vez. Ex: <strong>http://192.168.1.15:5000</strong></small>
    </div>'''
    if old in content:
        content = content.replace(old, new, 1)
        print('[app.html] Edit 1 (campo URL): OK')
    else:
        print('[app.html] Edit 1: FAIL')

    # 2. Substituir bloco de configuração da API
    old2_pattern = r'// ════ STORAGE HELPERS ════\n// URL do servidor.*?function preencherCampoUrl\(\) \{.*?\}'
    match = re.search(old2_pattern, content, re.DOTALL)
    if match:
        content = content[:match.start()] + '// ════ STORAGE HELPERS ════\n' + NEW_API_BLOCK + content[match.end():]
        print('[app.html] Edit 2 (bloco API): OK')
    else:
        print('[app.html] Edit 2: FAIL')

    # 3. Substituir apiFetch
    old3_pattern = r'// ════ API FETCH HELPERS ════\nasync function apiFetch\(endpoint.*?\n\}'
    match3 = re.search(old3_pattern, content, re.DOTALL)
    if match3:
        content = content[:match3.start()] + '// ════ API FETCH HELPERS ════\n' + NEW_APIFETCH + content[match3.end():]
        print('[app.html] Edit 3 (apiFetch): OK')
    else:
        print('[app.html] Edit 3: FAIL')

    # 4. Substituir doLogin
    old4 = '''async function doLogin(){
  const email=document.getElementById('l-email').value.trim().toLowerCase();
  const senha=document.getElementById('l-senha').value;
  const customUrl=document.getElementById('l-api-url').value.trim();
  const errEl=document.getElementById('l-err');

  if(!customUrl && !API_URL){
    errEl.textContent='⚠️ Informe a URL do servidor antes de entrar.';
    document.getElementById('l-api-url').focus();
    return;
  }
  if(customUrl) setApiUrl(customUrl);

  errEl.textContent='🔄 Conectando...';
  const res = await apiFetch('/api/login', { method: 'POST', body: JSON.stringify({ email, senha }) });
  if(res && res.status === 'success'){
    currentUser = res.user;
    DB.set('nn_session', currentUser.id);
    errEl.textContent='';
    goApp();
  } else {
    const msg = (res && res.message) ? res.message : 'E-mail ou senha incorretos.';
    errEl.textContent = msg;
  }
}'''
    new4 = '''async function doLogin(){
  const email=document.getElementById('l-email').value.trim().toLowerCase();
  const senha=document.getElementById('l-senha').value;
  const campoUrl=document.getElementById('l-api-url');
  const customUrl=campoUrl ? campoUrl.value.trim() : '';
  const errEl=document.getElementById('l-err');

  if(customUrl){
    setUrlBase(customUrl);
    errEl.textContent='🔄 Conectando ao servidor...';
    await descobrirUrlPublica();
  }

  if(!API_URL){
    errEl.textContent='⚠️ Configure a URL do servidor. Toque em ⚙️ Configurar servidor.';
    return;
  }

  errEl.textContent='🔄 Entrando...';
  const res = await apiFetch('/api/login', { method: 'POST', body: JSON.stringify({ email, senha }) });
  if(res && res.status === 'success'){
    currentUser = res.user;
    DB.set('nn_session', currentUser.id);
    errEl.textContent='';
    goApp();
  } else {
    const msg = (res && res.message) ? res.message : 'E-mail ou senha incorretos.';
    errEl.textContent = msg;
  }
}'''
    if old4 in content:
        content = content.replace(old4, new4, 1)
        print('[app.html] Edit 4 (doLogin): OK')
    else:
        print('[app.html] Edit 4: FAIL')

    # 5. Substituir bloco de init (window.addEventListener load)
    old5_pattern = r'\t\twindow\.addEventListener\(\'load\', async \(\) => \{.*?\}\);'
    match5 = re.search(old5_pattern, content, re.DOTALL)
    if match5:
        new5 = """\t\twindow.addEventListener('load', async () => {
\t\t  const splashText = document.getElementById('splash-text');
\t\t  const splashVersion = document.getElementById('splash-version');
\t\t  if (splashVersion) splashVersion.textContent = `Versão ${APP_VERSION}`;
\t\t  if (splashText) splashText.textContent = "Conectando ao servidor...";
\t\t  seedData();

\t\t  // Preenche o campo de URL base (oculto) com o valor salvo
\t\t  const campoUrl = document.getElementById('l-api-url');
\t\t  if(campoUrl && URL_BASE) campoUrl.value = URL_BASE;

\t\t  // Descobre a URL pública do tunnel automaticamente
\t\t  await descobrirUrlPublica();

\t\t  const savedSession=DB.get('nn_session');
\t\t  if(savedSession && API_URL){
\t\t    if (splashText) splashText.textContent = "Validando sessão...";
\t\t    try {
\t\t      const users = await apiFetch('/api/users');
\t\t      if (Array.isArray(users)) {
\t\t        const u = users.find(x => x.id === savedSession);
\t\t        if(u){ currentUser=u; goApp(); }
\t\t      }
\t\t    } catch (err) {
\t\t      console.error("Erro ao validar sessão:", err);
\t\t    }
\t\t  }

\t\t  if (splashText) splashText.textContent = "Verificando atualizações...";
\t\t  if (API_URL) await checkAppUpdate();

\t\t  // Atualiza URL pública a cada 5 minutos
\t\t  setInterval(descobrirUrlPublica, 5 * 60 * 1000);

\t\t  const splash = document.getElementById('splash');
\t\t  if (splash) {
\t\t    splash.style.opacity = '0';
\t\t    setTimeout(() => splash.remove(), 500);
\t\t  }
\t\t});"""
        content = content[:match5.start()] + new5 + content[match5.end():]
        print('[app.html] Edit 5 (init): OK')
    else:
        print('[app.html] Edit 5: FAIL')

    # 6. Adicionar botão ⚙️ e toggleCampoUrl no login
    old6 = '''    <button class="btn-rose" onclick="doLogin()">Entrar no App</button>
    <div class="login-err" id="l-err"></div>
  </div>
  <p class="login-note">Ainda não tem acesso? <br>Entre em contato com a Nalin.</p>'''
    new6 = '''    <button class="btn-rose" onclick="doLogin()">Entrar no App</button>
    <div class="login-err" id="l-err"></div>
    <div style="text-align:center;margin-top:8px;">
      <button onclick="toggleCampoUrl()" style="background:none;border:none;color:var(--light);font-size:11px;cursor:pointer;padding:4px 8px;">⚙️ Configurar servidor</button>
    </div>
  </div>
  <p class="login-note">Ainda não tem acesso? <br>Entre em contato com a Nalin.</p>'''
    if old6 in content:
        content = content.replace(old6, new6, 1)
        print('[app.html] Edit 6 (botão config): OK')
    else:
        print('[app.html] Edit 6: FAIL')

    # 7. Adicionar toggleCampoUrl após setApiUrl
    old7 = '''function setApiUrl(url) {
  if(!url) return;
  if(!url.startsWith('http')) url = 'http://' + url;
  API_URL = url;
  localStorage.setItem('api_url', url);
  console.log('API URL atualizada para:', API_URL);
}
// Preenche o campo de URL com o valor salvo
function preencherCampoUrl() {
  const saved = localStorage.getItem('api_url');
  const input = document.getElementById('l-api-url');
  if (input && saved) input.value = saved;
}'''
    new7 = '''function toggleCampoUrl() {
  const campo = document.getElementById('campo-url-servidor');
  if(!campo) return;
  campo.style.display = campo.style.display === 'none' ? 'block' : 'none';
}'''
    if old7 in content:
        content = content.replace(old7, new7, 1)
        print('[app.html] Edit 7 (toggleCampoUrl): OK')
    else:
        print('[app.html] Edit 7: FAIL')

    return content


# ─────────────────────────────────────────────────────────────────────────────
# admin.html
# ─────────────────────────────────────────────────────────────────────────────

def patch_admin(content):
    # 1. Campo de URL no login admin
    old = '''      <label>URL do Servidor</label>
      <input type="text" id="a-api-url" placeholder="https://xxxx.trycloudflare.com" value="" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false">
      <small style="font-size:11px;color:var(--lite);margin-top:4px;display:block;line-height:1.5;">Cole a URL que aparece no terminal do servidor.<br>Ex: <strong>https://xxxx.trycloudflare.com</strong></small>'''
    new = '''      <label>URL Base do Servidor (IP local)</label>
      <input type="text" id="a-api-url" placeholder="http://192.168.1.15:5000" value="" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false">
      <small style="font-size:11px;color:var(--lite);margin-top:4px;display:block;line-height:1.5;">IP local do computador onde o servidor roda.<br>Configure uma única vez. Ex: <strong>http://192.168.1.15:5000</strong></small>'''
    if old in content:
        content = content.replace(old, new, 1)
        print('[admin.html] Edit 1 (campo URL): OK')
    else:
        print('[admin.html] Edit 1: FAIL')

    # 2. Substituir bloco de configuração da API
    old2_pattern = r'// ════ CONFIGURAÇÃO DINÂMICA DA API ════\n// URL do servidor.*?function preencherCampoUrl\(\) \{.*?\}'
    match = re.search(old2_pattern, content, re.DOTALL)
    if match:
        content = content[:match.start()] + '// ════ CONFIGURAÇÃO DINÂMICA DA API ════\n' + NEW_API_BLOCK + content[match.end():]
        print('[admin.html] Edit 2 (bloco API): OK')
    else:
        print('[admin.html] Edit 2: FAIL')

    # 3. Substituir apiFetch
    old3_pattern = r'async function apiFetch\(endpoint, options = \{\}\) \{.*?console\.error\("URL tentada:", API_URL \+ endpoint\);\n    return null;\n  \}\n\}'
    match3 = re.search(old3_pattern, content, re.DOTALL)
    if match3:
        content = content[:match3.start()] + NEW_APIFETCH + content[match3.end():]
        print('[admin.html] Edit 3 (apiFetch): OK')
    else:
        print('[admin.html] Edit 3: FAIL')

    # 4. Substituir adminLogin
    old4 = '''async function adminLogin(){
  const user=document.getElementById('a-user').value.trim().toLowerCase();
  const pass=document.getElementById('a-pass').value;
  const customUrl=document.getElementById('a-api-url').value.trim();
  const errEl=document.getElementById('a-err');

  if(!customUrl && !API_URL){
    errEl.textContent='⚠️ Informe a URL do servidor antes de entrar.';
    document.getElementById('a-api-url').focus();
    return;
  }

  if(customUrl){
    setApiUrl(customUrl);
    errEl.textContent='🔄 Conectando ao servidor...';
    errEl.style.color='var(--mid)';
  }

  const res = await apiFetch('/api/admin/login', {
    method: 'POST',
    body: JSON.stringify({ user, pass })
  });
  if(res && res.status === 'success'){
    DB.set('nn_admin_session',true);
    document.getElementById('admin-login').style.display='none';
    document.getElementById('admin-shell').classList.add('active');
    renderDashboard();
  } else {
    errEl.textContent = res ? (res.message || 'Credenciais incorretas.') : '❌ Não foi possível conectar ao servidor. Verifique a URL.';
    errEl.style.color = '#c0392b';
  }
}'''
    new4 = '''async function adminLogin(){
  const user=document.getElementById('a-user').value.trim().toLowerCase();
  const pass=document.getElementById('a-pass').value;
  const campoUrl=document.getElementById('a-api-url');
  const customUrl=campoUrl ? campoUrl.value.trim() : '';
  const errEl=document.getElementById('a-err');

  if(customUrl){
    setUrlBase(customUrl);
    errEl.textContent='🔄 Conectando ao servidor...';
    await descobrirUrlPublica();
  }

  if(!API_URL){
    errEl.textContent='⚠️ Informe o IP do servidor no campo acima.';
    if(campoUrl) campoUrl.focus();
    return;
  }

  errEl.textContent='🔄 Entrando...';
  const res = await apiFetch('/api/admin/login', {
    method: 'POST',
    body: JSON.stringify({ user, pass })
  });
  if(res && res.status === 'success'){
    DB.set('nn_admin_session',true);
    document.getElementById('admin-login').style.display='none';
    document.getElementById('admin-shell').classList.add('active');
    renderDashboard();
  } else {
    errEl.textContent = res ? (res.message || 'Credenciais incorretas.') : '❌ Não foi possível conectar ao servidor.';
    errEl.style.color = '#c0392b';
  }
}'''
    if old4 in content:
        content = content.replace(old4, new4, 1)
        print('[admin.html] Edit 4 (adminLogin): OK')
    else:
        print('[admin.html] Edit 4: FAIL')

    # 5. Substituir setApiUrl e preencherCampoUrl no admin
    old5 = '''function setApiUrl(url) {
  if(!url) return;
  if(!url.startsWith('http')) url = 'http://' + url;
  API_URL = url;
  localStorage.setItem('api_url', url);
  console.log('API URL atualizada para:', API_URL);
}
// Preenche o campo de URL com o valor salvo
function preencherCampoUrl() {
  const saved = localStorage.getItem('api_url');
  const input = document.getElementById('a-api-url');
  if (input && saved) input.value = saved;
}'''
    new5 = '''// setApiUrl e setUrlBase já definidos no bloco de configuração da API acima'''
    if old5 in content:
        content = content.replace(old5, new5, 1)
        print('[admin.html] Edit 5 (setApiUrl duplicado): OK')
    else:
        print('[admin.html] Edit 5: FAIL (pode já estar correto)')

    # 6. Substituir init do admin
    old6 = '''// Preenche o campo de URL com o valor salvo
preencherCampoUrl();
if(DB.get('nn_admin_session') && API_URL){
  document.getElementById('admin-login').style.display='none';
  document.getElementById('admin-shell').classList.add('active');
  renderDashboard();
}'''
    new6 = '''// Inicialização: descobre URL pública e restaura sessão
(async function initAdmin(){
  // Preenche o campo de URL base com o valor salvo
  const campoUrl = document.getElementById('a-api-url');
  if(campoUrl && URL_BASE) campoUrl.value = URL_BASE;

  // Descobre a URL pública do tunnel automaticamente
  await descobrirUrlPublica();

  if(DB.get('nn_admin_session') && API_URL){
    document.getElementById('admin-login').style.display='none';
    document.getElementById('admin-shell').classList.add('active');
    renderDashboard();
  }

  // Atualiza URL pública a cada 5 minutos
  setInterval(descobrirUrlPublica, 5 * 60 * 1000);
})();'''
    if old6 in content:
        content = content.replace(old6, new6, 1)
        print('[admin.html] Edit 6 (init): OK')
    else:
        print('[admin.html] Edit 6: FAIL')

    return content


# ─────────────────────────────────────────────────────────────────────────────
# Aplicar patches
# ─────────────────────────────────────────────────────────────────────────────

import os
os.chdir('/home/ubuntu/app-doula')

print('\n=== Processando www/index.html ===')
with open('www/index.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = patch_index(c)
with open('www/index.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('\n=== Processando www/app.html ===')
with open('www/app.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = patch_app(c)
with open('www/app.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('\n=== Processando www/admin.html ===')
with open('www/admin.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = patch_admin(c)
with open('www/admin.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('\nConcluído!')
