"""Redesenha a tela de vídeos do app.html com layout de dois painéis"""

with open('www/app.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ─── 1. Substituir CSS da tela de conteúdo ───────────────────────────────────
old_css = '''.cont-grid{padding:12px;display:grid;grid-template-columns:repeat(2, 1fr);gap:10px;}
.ccard{background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px var(--shadow-soft);cursor:pointer;transition:transform .15s;display:flex;flex-direction:column;}
.ccard:active{transform:scale(.96);}
.ccard.assistido{opacity:.75;}
.cthumb{aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;background:var(--rose-pale);}
.cthumb .te{font-size:24px;z-index:1;}
.cthumb img{position:absolute;width:100%;height:100%;object-fit:cover;}
.play-btn{position:absolute;width:32px;height:32px;border-radius:50%;background:rgba(255,255,255,.9);display:flex;align-items:center;justify-content:center;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,.2);z-index:2;}
.check-badge{position:absolute;top:6px;right:6px;width:20px;height:20px;border-radius:50%;background:var(--rose);display:flex;align-items:center;justify-content:center;font-size:10px;color:white;z-index:3;}
.cinfo{padding:8px;flex:1;display:flex;flex-direction:column;}
.ctag{font-size:8px;letter-spacing:0.5px;text-transform:uppercase;color:var(--rose);font-weight:600;margin-bottom:2px;}
.ctitle{font-size:11px;font-weight:500;color:var(--dark);line-height:1.3;flex:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.cmeta{font-size:9px;color:var(--light);margin-top:4px;display:flex;gap:6px;align-items:center;}
/* Seções do mini curso */
.secao-wrap{margin-bottom:16px;}
.secao-hdr{background:white;border-radius:12px;padding:14px 16px;box-shadow:0 2px 8px var(--shadow-soft);cursor:pointer;display:flex;align-items:center;justify-content:space-between;margin-bottom:2px;}
.secao-num{width:28px;height:28px;border-radius:50%;background:var(--rose);color:white;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.secao-info{flex:1;margin:0 10px;}
.secao-titulo{font-size:13px;font-weight:600;color:var(--dark);}
.secao-sub{font-size:11px;color:var(--lite);margin-top:1px;}
.secao-progress-bar{height:4px;background:#f0e8e4;border-radius:2px;overflow:hidden;margin-top:6px;}
.secao-progress-fill{height:100%;background:linear-gradient(90deg,var(--rose),#c9907a);border-radius:2px;transition:width .4s;}
.secao-body{padding:0 0 4px;}
/* Barra de progresso geral */
.curso-progress-card{background:white;border-radius:12px;padding:14px 16px;box-shadow:0 2px 8px var(--shadow-soft);margin:12px 12px 4px;}
.curso-progress-title{font-size:13px;font-weight:600;color:var(--dark);margin-bottom:8px;}
.curso-progress-bar{height:8px;background:#f0e8e4;border-radius:4px;overflow:hidden;}
.curso-progress-fill{height:100%;background:linear-gradient(90deg,var(--rose),#c9907a);border-radius:4px;transition:width .5s;}
.curso-progress-txt{font-size:11px;color:var(--lite);margin-top:4px;text-align:right;}'''

new_css = '''/* ══ LAYOUT DE DOIS PAINÉIS — MINI CURSO ══ */
#conteudo{display:flex;flex-direction:column;}
.cont-hdr{flex-shrink:0;}
.curso-layout{display:flex;flex:1;overflow:hidden;min-height:0;}
/* Painel lateral esquerdo — lista de seções/vídeos */
.curso-sidebar{width:260px;min-width:220px;max-width:300px;background:#faf7f5;border-right:1px solid #f0e8e4;display:flex;flex-direction:column;overflow:hidden;}
.curso-sidebar-inner{flex:1;overflow-y:auto;padding:8px 0;}
/* Barra de progresso no topo do sidebar */
.sidebar-progress{padding:12px 14px 8px;border-bottom:1px solid #f0e8e4;flex-shrink:0;}
.sidebar-progress-title{font-size:11px;font-weight:600;color:var(--dark);margin-bottom:6px;}
.sidebar-progress-bar{height:6px;background:#f0e8e4;border-radius:3px;overflow:hidden;}
.sidebar-progress-fill{height:100%;background:linear-gradient(90deg,var(--rose),#c9907a);border-radius:3px;transition:width .5s;}
.sidebar-progress-txt{font-size:10px;color:var(--lite);margin-top:4px;}
/* Seções no sidebar */
.sb-secao{margin-bottom:2px;}
.sb-secao-hdr{padding:10px 14px;cursor:pointer;display:flex;align-items:center;gap:8px;background:transparent;transition:background .15s;}
.sb-secao-hdr:hover{background:rgba(201,144,122,.08);}
.sb-secao-num{width:22px;height:22px;border-radius:50%;background:var(--rose);color:white;font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.sb-secao-info{flex:1;min-width:0;}
.sb-secao-titulo{font-size:12px;font-weight:600;color:var(--dark);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.sb-secao-sub{font-size:10px;color:var(--lite);}
.sb-secao-arrow{font-size:10px;color:var(--lite);flex-shrink:0;transition:transform .2s;}
.sb-secao-arrow.open{transform:rotate(180deg);}
.sb-secao-body{overflow:hidden;}
/* Item de vídeo no sidebar */
.sb-video-item{padding:8px 14px 8px 44px;cursor:pointer;display:flex;align-items:center;gap:8px;transition:background .15s;border-left:3px solid transparent;}
.sb-video-item:hover{background:rgba(201,144,122,.08);}
.sb-video-item.active{background:rgba(201,144,122,.15);border-left-color:var(--rose);}
.sb-video-item.assistido-item .sb-vid-title{color:var(--lite);}
.sb-vid-thumb{width:44px;height:28px;border-radius:4px;object-fit:cover;background:#e8d8d0;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:12px;overflow:hidden;}
.sb-vid-thumb img{width:100%;height:100%;object-fit:cover;}
.sb-vid-info{flex:1;min-width:0;}
.sb-vid-title{font-size:11px;font-weight:500;color:var(--dark);line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.sb-vid-dur{font-size:9px;color:var(--lite);margin-top:1px;}
.sb-vid-check{font-size:12px;color:var(--rose);flex-shrink:0;}
/* Área principal do player */
.curso-main{flex:1;display:flex;flex-direction:column;overflow:hidden;background:#fff;}
.player-area{flex-shrink:0;background:#000;position:relative;}
.player-area iframe{width:100%;display:block;border:none;}
.player-placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 20px;background:linear-gradient(135deg,#f5ede8,#e8d8d0);text-align:center;}
.player-placeholder .pp-icon{font-size:48px;margin-bottom:12px;}
.player-placeholder p{font-size:13px;color:var(--mid);line-height:1.5;}
.player-info{padding:14px 16px;border-bottom:1px solid #f0e8e4;flex-shrink:0;}
.player-titulo{font-size:15px;font-weight:600;color:var(--dark);line-height:1.3;}
.player-meta{font-size:11px;color:var(--lite);margin-top:4px;display:flex;align-items:center;gap:8px;}
.player-check-btn{margin-top:10px;padding:8px 16px;background:var(--rose);color:white;border:none;border-radius:20px;font-size:12px;cursor:pointer;font-weight:500;}
.player-check-btn.done{background:#9ec49e;cursor:default;}
/* Grid para ebooks/meditações */
.cont-grid{padding:12px;display:grid;grid-template-columns:repeat(2, 1fr);gap:10px;}
.ccard{background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px var(--shadow-soft);cursor:pointer;transition:transform .15s;display:flex;flex-direction:column;}
.ccard:active{transform:scale(.96);}
.ccard.assistido{opacity:.75;}
.cthumb{aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;background:var(--rose-pale);}
.cthumb .te{font-size:24px;z-index:1;}
.cthumb img{position:absolute;width:100%;height:100%;object-fit:cover;}
.play-btn{position:absolute;width:32px;height:32px;border-radius:50%;background:rgba(255,255,255,.9);display:flex;align-items:center;justify-content:center;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,.2);z-index:2;}
.check-badge{position:absolute;top:6px;right:6px;width:20px;height:20px;border-radius:50%;background:var(--rose);display:flex;align-items:center;justify-content:center;font-size:10px;color:white;z-index:3;}
.cinfo{padding:8px;flex:1;display:flex;flex-direction:column;}
.ctag{font-size:8px;letter-spacing:0.5px;text-transform:uppercase;color:var(--rose);font-weight:600;margin-bottom:2px;}
.ctitle{font-size:11px;font-weight:500;color:var(--dark);line-height:1.3;flex:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.cmeta{font-size:9px;color:var(--light);margin-top:4px;display:flex;gap:6px;align-items:center;}
/* Barra de progresso geral (usada em ebooks/meditações) */
.curso-progress-card{background:white;border-radius:12px;padding:14px 16px;box-shadow:0 2px 8px var(--shadow-soft);margin:12px 12px 4px;}
.curso-progress-title{font-size:13px;font-weight:600;color:var(--dark);margin-bottom:8px;}
.curso-progress-bar{height:8px;background:#f0e8e4;border-radius:4px;overflow:hidden;}
.curso-progress-fill{height:100%;background:linear-gradient(90deg,var(--rose),#c9907a);border-radius:4px;transition:width .5s;}
.curso-progress-txt{font-size:11px;color:var(--lite);margin-top:4px;text-align:right;}'''

if old_css in content:
    content = content.replace(old_css, new_css, 1)
    print('CSS substituído: OK')
else:
    print('FAIL: CSS não encontrado')

# ─── 2. Substituir HTML da tela de conteúdo ──────────────────────────────────
old_html = '''<!-- ════════════ CONTEÚDO SCREEN ════════════ -->
<div class="screen" id="conteudo">
  <div class="cont-hdr"><h2>Mini Curso</h2><p>Sua jornada de aprendizado</p>
    <div class="tabs">
      <div class="tab active" onclick="switchTab(0,this)">Vídeos</div>
      <div class="tab" onclick="switchTab(1,this)">E-books</div>
      <div class="tab" onclick="switchTab(2,this)">Meditações</div>
    </div>
  </div>
  <div class="scroll">
    <div id="curso-progress-wrap" style="display:none;">
      <div class="curso-progress-card">
        <div class="curso-progress-title">Seu progresso no curso</div>
        <div class="curso-progress-bar"><div class="curso-progress-fill" id="curso-progress-fill" style="width:0%"></div></div>
        <div class="curso-progress-txt" id="curso-progress-txt">0 de 0 vídeos assistidos</div>
      </div>
    </div>
    <div id="cont-list"></div>
  </div>'''

new_html = '''<!-- ════════════ CONTEÚDO SCREEN ════════════ -->
<div class="screen" id="conteudo">
  <div class="cont-hdr"><h2>Mini Curso</h2><p>Sua jornada de aprendizado</p>
    <div class="tabs">
      <div class="tab active" onclick="switchTab(0,this)">Vídeos</div>
      <div class="tab" onclick="switchTab(1,this)">E-books</div>
      <div class="tab" onclick="switchTab(2,this)">Meditações</div>
    </div>
  </div>
  <!-- Layout de dois painéis — só visível na aba de vídeos -->
  <div class="curso-layout" id="curso-layout" style="display:none;">
    <!-- Painel lateral esquerdo -->
    <div class="curso-sidebar">
      <div class="sidebar-progress">
        <div class="sidebar-progress-title">Seu progresso</div>
        <div class="sidebar-progress-bar"><div class="sidebar-progress-fill" id="sidebar-progress-fill" style="width:0%"></div></div>
        <div class="sidebar-progress-txt" id="sidebar-progress-txt">0 de 0 vídeos</div>
      </div>
      <div class="curso-sidebar-inner" id="curso-sidebar-inner">
        <div style="padding:24px 14px;text-align:center;color:var(--lite);font-size:12px;">Carregando...</div>
      </div>
    </div>
    <!-- Área principal do player -->
    <div class="curso-main" id="curso-main">
      <div class="player-area" id="player-area">
        <div class="player-placeholder">
          <div class="pp-icon">🎬</div>
          <p>Selecione um vídeo<br>no painel ao lado para começar</p>
        </div>
      </div>
      <div class="player-info" id="player-info" style="display:none;">
        <div class="player-titulo" id="player-titulo"></div>
        <div class="player-meta" id="player-meta"></div>
        <button class="player-check-btn" id="player-check-btn" onclick="marcarAtualAssistido()">✓ Marcar como assistido</button>
      </div>
    </div>
  </div>
  <!-- Área de scroll para ebooks/meditações -->
  <div class="scroll" id="cont-scroll" style="display:none;">
    <div id="cont-list"></div>
  </div>'''

if old_html in content:
    content = content.replace(old_html, new_html, 1)
    print('HTML da tela substituído: OK')
else:
    print('FAIL: HTML da tela não encontrado')

# ─── 3. Substituir a função renderConteudo e relacionadas ────────────────────
# Localizar início e fim do bloco JS
import re

# Encontrar início de "// Cache de progresso de vídeos"
start_marker = '// Cache de progresso de vídeos'
end_marker = '// ════ GESTAÇÃO ════'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print(f'FAIL: marcadores JS não encontrados (start={start_idx}, end={end_idx})')
else:
    new_js = '''// ═══ MINI CURSO — ESTADO ═══
let videoProgressoCache = {};
let currentVideoId = null;
let currentVideoUrl = null;
let currentVideoTitulo = null;

async function carregarProgresso(){
  if(!currentUser) return;
  const rows = await apiFetch(`/api/progresso?user_id=${currentUser.id}`) || [];
  videoProgressoCache = {};
  rows.forEach(r => { videoProgressoCache[r.conteudo_id] = r; });
}

async function marcarVideoAssistido(conteudoId, titulo){
  if(!currentUser || !conteudoId) return;
  await apiFetch('/api/progresso', {
    method: 'POST',
    body: JSON.stringify({ user_id: currentUser.id, conteudo_id: conteudoId, assistido: 1, percentual: 100 })
  });
  videoProgressoCache[conteudoId] = { assistido: 1, percentual: 100 };
  logActivity('Assistiu ao vídeo', titulo);
}

async function marcarAtualAssistido(){
  if(!currentVideoId) return;
  await marcarVideoAssistido(currentVideoId, currentVideoTitulo);
  const btn = document.getElementById('player-check-btn');
  if(btn){ btn.textContent = '✓ Assistido!'; btn.classList.add('done'); btn.disabled = true; }
  // Atualizar item no sidebar
  const item = document.querySelector(`.sb-video-item[data-id="${currentVideoId}"]`);
  if(item){
    item.classList.add('assistido-item');
    const chk = item.querySelector('.sb-vid-check');
    if(chk) chk.textContent = '✓';
  }
  atualizarBarraProgresso();
}

function atualizarBarraProgresso(){
  // Contar total e assistidos a partir do cache do sidebar
  const allItems = document.querySelectorAll('.sb-video-item[data-id]');
  const total = allItems.length;
  const assistidos = Object.values(videoProgressoCache).filter(v => v.assistido).length;
  const pct = total > 0 ? Math.round((assistidos / total) * 100) : 0;
  const fill = document.getElementById('sidebar-progress-fill');
  const txt = document.getElementById('sidebar-progress-txt');
  if(fill) fill.style.width = pct + '%';
  if(txt) txt.textContent = `${assistidos} de ${total} vídeos · ${pct}%`;
}

function getYTEmbedUrl(url){
  if(!url) return null;
  // youtube.com/watch?v=ID ou youtu.be/ID
  const m = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
  return m ? `https://www.youtube.com/embed/${m[1]}?rel=0&modestbranding=1` : null;
}

function selecionarVideo(conteudoId, url, titulo, duracao){
  currentVideoId = conteudoId;
  currentVideoUrl = url;
  currentVideoTitulo = titulo;

  // Atualizar destaque no sidebar
  document.querySelectorAll('.sb-video-item').forEach(el => el.classList.remove('active'));
  const item = document.querySelector(`.sb-video-item[data-id="${conteudoId}"]`);
  if(item) item.classList.add('active');

  // Montar player
  const playerArea = document.getElementById('player-area');
  const embedUrl = getYTEmbedUrl(url);
  if(embedUrl){
    playerArea.innerHTML = `<iframe src="${embedUrl}" allowfullscreen style="width:100%;aspect-ratio:16/9;border:none;display:block;"></iframe>`;
  } else {
    // Vídeo direto (mp4 etc.)
    playerArea.innerHTML = `<video controls style="width:100%;aspect-ratio:16/9;background:#000;display:block;" src="${url}"></video>`;
  }

  // Atualizar info
  const infoEl = document.getElementById('player-info');
  const tituloEl = document.getElementById('player-titulo');
  const metaEl = document.getElementById('player-meta');
  const btnEl = document.getElementById('player-check-btn');
  if(infoEl) infoEl.style.display = '';
  if(tituloEl) tituloEl.textContent = titulo;
  if(metaEl) metaEl.textContent = duracao || '';
  const jaAssistido = videoProgressoCache[conteudoId]?.assistido;
  if(btnEl){
    if(jaAssistido){ btnEl.textContent = '✓ Já assistido'; btnEl.classList.add('done'); btnEl.disabled = true; }
    else { btnEl.textContent = '✓ Marcar como assistido'; btnEl.classList.remove('done'); btnEl.disabled = false; }
  }
}

async function renderConteudo(idx){
  currentTab = idx;
  const cat = catMap[idx] || 'video';
  const layout = document.getElementById('curso-layout');
  const scrollArea = document.getElementById('cont-scroll');
  const list = document.getElementById('cont-list');

  // Mostrar layout correto
  if(cat === 'video'){
    if(layout) layout.style.display = 'flex';
    if(scrollArea) scrollArea.style.display = 'none';
    await renderSidebar();
    return;
  } else {
    if(layout) layout.style.display = 'none';
    if(scrollArea) scrollArea.style.display = '';
  }

  list.innerHTML = '<div style="padding:32px;text-align:center;color:var(--lite);">Carregando...</div>';

  if(cat === 'ebook'){
    const apiEbooks = await apiFetch('/api/ebooks') || [];
    list.innerHTML = '';
    if(!apiEbooks.length){ list.innerHTML=`<div class="empty-state"><div class="ei">📭</div><p>Nenhum e-book ainda.</p></div>`; return; }
    list.innerHTML = '<div class="cont-grid">' + apiEbooks.map(e => `
      <div class="ccard" onclick="openConteudo('${API_URL + e.url_pdf}', null, '${(e.titulo||'').replace(/'/g,"\\'")}')">
        <div class="cthumb" style="background:linear-gradient(135deg,#c9907a,#a96b55)"><div class="te">📖</div></div>
        <div class="cinfo"><div class="ctitle">${e.titulo}</div><div class="cmeta">${e.descricao||'Material exclusivo'}</div></div>
      </div>`).join('') + '</div>';
    return;
  }

  if(cat === 'meditacao'){
    const apiCont = await apiFetch('/api/conteudos') || [];
    const meds = apiCont.filter(c => c.categoria === 'meditacao');
    list.innerHTML = '';
    if(!meds.length){ list.innerHTML=`<div class="empty-state"><div class="ei">🧘</div><p>Nenhuma meditação ainda.</p></div>`; return; }
    list.innerHTML = '<div class="cont-grid">' + meds.map(c => {
      const ytId = c.url && c.url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/)?.[1];
      const thumbImg = ytId ? `<img src="https://img.youtube.com/vi/${ytId}/hqdefault.jpg" loading="lazy">` : '';
      return `<div class="ccard" onclick="openConteudo('${c.url}', null, '${(c.titulo||'').replace(/'/g,"\\'")}')">
        <div class="cthumb" style="background:linear-gradient(135deg,${c.cor||'#e8b4a0,#c9907a'})">${thumbImg}<div class="te" style="${thumbImg?'opacity:.2':''}">${c.emoji||'🧘'}</div><div class="play-btn">▶</div></div>
        <div class="cinfo"><div class="ctitle">${c.titulo}</div><div class="cmeta">${c.duracao||''}</div></div>
      </div>`;
    }).join('') + '</div>';
    return;
  }
}

async function renderSidebar(){
  const sidebarInner = document.getElementById('curso-sidebar-inner');
  if(!sidebarInner) return;
  sidebarInner.innerHTML = '<div style="padding:24px 14px;text-align:center;color:var(--lite);font-size:12px;">Carregando...</div>';

  await carregarProgresso();
  const secoes = await apiFetch('/api/secoes') || [];
  const apiCont = await apiFetch('/api/conteudos') || [];
  const todoVideos = apiCont.filter(c => c.categoria === 'video');

  sidebarInner.innerHTML = '';

  if(secoes.length === 0 && todoVideos.length === 0){
    sidebarInner.innerHTML = '<div style="padding:24px 14px;text-align:center;color:var(--lite);font-size:12px;">Nenhum vídeo disponível ainda.</div>';
    return;
  }

  // Renderizar seções com seus vídeos
  secoes.forEach((s, sIdx) => {
    const videosSecao = s.videos || [];
    const totalS = videosSecao.length;
    const assistidosS = videosSecao.filter(v => videoProgressoCache[v.id]?.assistido).length;

    const secaoDiv = document.createElement('div');
    secaoDiv.className = 'sb-secao';
    const bodyId = `sb-body-${s.id}`;
    const arrowId = `sb-arrow-${s.id}`;

    const videosHtml = totalS === 0
      ? '<div style="padding:8px 14px 8px 44px;font-size:11px;color:var(--lite);">Nenhum vídeo nesta seção.</div>'
      : videosSecao.map(v => {
          const ytId = v.url && v.url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/)?.[1];
          const thumbHtml = ytId
            ? `<div class="sb-vid-thumb"><img src="https://img.youtube.com/vi/${ytId}/mqdefault.jpg"></div>`
            : `<div class="sb-vid-thumb">${v.emoji||'🎬'}</div>`;
          const assistido = videoProgressoCache[v.id]?.assistido;
          const tituloEsc = (v.titulo||'').replace(/'/g,"\\'").replace(/"/g,'&quot;');
          const durEsc = (v.duracao||'').replace(/'/g,"\\'");
          return `<div class="sb-video-item${assistido?' assistido-item':''}" data-id="${v.id}" onclick="selecionarVideo(${v.id},'${v.url}','${tituloEsc}','${durEsc}')">
            ${thumbHtml}
            <div class="sb-vid-info">
              <div class="sb-vid-title">${v.titulo}</div>
              ${v.duracao ? `<div class="sb-vid-dur">${v.duracao}</div>` : ''}
            </div>
            <div class="sb-vid-check">${assistido ? '✓' : ''}</div>
          </div>`;
        }).join('');

    secaoDiv.innerHTML = `
      <div class="sb-secao-hdr" onclick="toggleSbSecao('${bodyId}','${arrowId}')">
        <div class="sb-secao-num">${sIdx+1}</div>
        <div class="sb-secao-info">
          <div class="sb-secao-titulo">${s.titulo}</div>
          <div class="sb-secao-sub">${assistidosS}/${totalS} vídeos</div>
        </div>
        <span id="${arrowId}" class="sb-secao-arrow open">▾</span>
      </div>
      <div id="${bodyId}" class="sb-secao-body">${videosHtml}</div>`;
    sidebarInner.appendChild(secaoDiv);
  });

  // Vídeos sem seção
  const semSecao = todoVideos.filter(c => !c.secao_id);
  if(semSecao.length > 0){
    const div = document.createElement('div');
    div.className = 'sb-secao';
    const videosHtml = semSecao.map(v => {
      const ytId = v.url && v.url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/)?.[1];
      const thumbHtml = ytId
        ? `<div class="sb-vid-thumb"><img src="https://img.youtube.com/vi/${ytId}/mqdefault.jpg"></div>`
        : `<div class="sb-vid-thumb">${v.emoji||'🎬'}</div>`;
      const assistido = videoProgressoCache[v.id]?.assistido;
      const tituloEsc = (v.titulo||'').replace(/'/g,"\\'").replace(/"/g,'&quot;');
      const durEsc = (v.duracao||'').replace(/'/g,"\\'");
      return `<div class="sb-video-item${assistido?' assistido-item':''}" data-id="${v.id}" onclick="selecionarVideo(${v.id},'${v.url}','${tituloEsc}','${durEsc}')">
        ${thumbHtml}
        <div class="sb-vid-info">
          <div class="sb-vid-title">${v.titulo}</div>
          ${v.duracao ? `<div class="sb-vid-dur">${v.duracao}</div>` : ''}
        </div>
        <div class="sb-vid-check">${assistido ? '✓' : ''}</div>
      </div>`;
    }).join('');
    div.innerHTML = `<div class="sb-secao-hdr" onclick="toggleSbSecao('sb-body-sem','sb-arrow-sem')">
      <div class="sb-secao-num">+</div>
      <div class="sb-secao-info"><div class="sb-secao-titulo">Outros vídeos</div></div>
      <span id="sb-arrow-sem" class="sb-secao-arrow open">▾</span>
    </div>
    <div id="sb-body-sem" class="sb-secao-body">${videosHtml}</div>`;
    sidebarInner.appendChild(div);
  }

  atualizarBarraProgresso();
}

function toggleSbSecao(bodyId, arrowId){
  const body = document.getElementById(bodyId);
  const arrow = document.getElementById(arrowId);
  if(!body) return;
  const isOpen = body.style.display !== 'none';
  body.style.display = isOpen ? 'none' : '';
  if(arrow){ arrow.classList.toggle('open', !isOpen); arrow.textContent = isOpen ? '▸' : '▾'; }
}

function switchTab(idx, el){
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  renderConteudo(idx);
  const catName = {0:'Vídeos',1:'E-books',2:'Meditações'}[idx];
  logActivity(`Acessou ${catName}`);
}

async function openConteudo(url, conteudoId = null, titulo = 'Conteúdo'){
  if(url){
    window.open(url, '_blank');
    if(conteudoId){
      await marcarVideoAssistido(conteudoId, titulo);
    }
  }
}

'''
    content = content[:start_idx] + new_js + content[end_idx:]
    print('JS do mini curso substituído: OK')

with open('www/app.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('app.html salvo.')
