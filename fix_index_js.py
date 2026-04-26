with open('www/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar linha de inicio (catMap) e fim (openConteudo + linha seguinte)
start = None
end = None
for i, line in enumerate(lines):
    if "const catMap={0:'video'" in line:
        start = i
    if start and "function openConteudo(url){if(url&&url!=='#')window.open(url,'_blank');}" in line:
        end = i
        break

if start is None or end is None:
    print(f'FAIL: start={start}, end={end}')
else:
    print(f'Bloco JS encontrado: linhas {start+1} a {end+1}')

    new_js = r"""const catMap={0:'video',1:'ebook',2:'meditacao',3:'outro'};
function getYTId(url) {
  if (!url) return null;
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11) ? match[2] : null;
}
function getYTEmbed(url) {
  const id = getYTId(url);
  return id ? `https://www.youtube.com/embed/${id}?autoplay=1&rel=0` : null;
}

// ── Variáveis do mini curso ──
let _videoAtualId = null;
let _progressoCache = {};

async function renderConteudo(idx){
  currentTab = idx;
  const layout = document.getElementById('curso-layout');
  const scroll = document.getElementById('cont-scroll');
  if (!layout || !scroll) return;

  if (idx === 0) {
    // Aba de vídeos — layout de dois painéis
    layout.style.display = 'flex';
    scroll.style.display = 'none';
    await renderMiniCurso();
  } else {
    // Outras abas — grade normal
    layout.style.display = 'none';
    scroll.style.display = 'flex';
    await renderGrade(idx);
  }
}

async function renderMiniCurso() {
  // Carregar seções e vídeos
  const secoes = await apiFetch('/api/curso/secoes') || [];
  const allVideos = await apiFetch('/api/conteudos') || [];
  const videos = allVideos.filter(v => v.categoria === 'video' && v.ativo);

  // Carregar progresso do usuário
  if (currentUser) {
    const prog = await apiFetch(`/api/curso/progresso/${currentUser.id}`) || {};
    _progressoCache = prog;
  }

  // Atualizar barra de progresso no sidebar
  const total = videos.length;
  const assistidos = Object.values(_progressoCache).filter(v => v).length;
  const pct = total > 0 ? Math.round((assistidos / total) * 100) : 0;
  const fill = document.getElementById('sidebar-progress-fill');
  const txt = document.getElementById('sidebar-progress-txt');
  if (fill) fill.style.width = pct + '%';
  if (txt) txt.textContent = `${assistidos} de ${total} vídeos · ${pct}%`;

  // Renderizar sidebar
  await renderSidebar(secoes, videos);
}

async function renderSidebar(secoes, videos) {
  const inner = document.getElementById('curso-sidebar-inner');
  if (!inner) return;

  if (!secoes.length && !videos.length) {
    inner.innerHTML = '<div style="padding:24px 14px;text-align:center;color:var(--lite);font-size:12px;">Nenhum vídeo disponível ainda.</div>';
    return;
  }

  // Vídeos sem seção
  const semSecao = videos.filter(v => !v.secao_id);
  // Vídeos por seção
  const porSecao = {};
  videos.forEach(v => { if (v.secao_id) { if (!porSecao[v.secao_id]) porSecao[v.secao_id] = []; porSecao[v.secao_id].push(v); } });

  let html = '';

  // Seções com vídeos
  secoes.forEach((s, idx) => {
    const vids = (porSecao[s.id] || []).sort((a,b) => (a.ordem||0)-(b.ordem||0));
    if (!vids.length) return;
    const bodyId = `sb-body-${s.id}`;
    const arrowId = `sb-arrow-${s.id}`;
    const assistidosNaSecao = vids.filter(v => _progressoCache[v.id]).length;
    html += `
    <div class="sb-secao">
      <div class="sb-secao-hdr" onclick="toggleSbSecao('${bodyId}','${arrowId}')">
        <div class="sb-secao-num">${idx+1}</div>
        <div class="sb-secao-info">
          <div class="sb-secao-titulo">${s.titulo}</div>
          <div class="sb-secao-sub">${assistidosNaSecao}/${vids.length} assistidos</div>
        </div>
        <div class="sb-secao-arrow open" id="${arrowId}">▼</div>
      </div>
      <div class="sb-secao-body" id="${bodyId}">
        ${vids.map(v => renderSbVideoItem(v)).join('')}
      </div>
    </div>`;
  });

  // Vídeos sem seção
  if (semSecao.length) {
    const bodyId = 'sb-body-sem-secao';
    const arrowId = 'sb-arrow-sem-secao';
    html += `
    <div class="sb-secao">
      <div class="sb-secao-hdr" onclick="toggleSbSecao('${bodyId}','${arrowId}')">
        <div class="sb-secao-num">+</div>
        <div class="sb-secao-info">
          <div class="sb-secao-titulo">Outros vídeos</div>
          <div class="sb-secao-sub">${semSecao.length} vídeos</div>
        </div>
        <div class="sb-secao-arrow open" id="${arrowId}">▼</div>
      </div>
      <div class="sb-secao-body" id="${bodyId}">
        ${semSecao.map(v => renderSbVideoItem(v)).join('')}
      </div>
    </div>`;
  }

  inner.innerHTML = html || '<div style="padding:24px 14px;text-align:center;color:var(--lite);font-size:12px;">Nenhum vídeo disponível ainda.</div>';
}

function renderSbVideoItem(v) {
  const ytId = getYTId(v.url);
  const thumb = ytId
    ? `<img src="https://img.youtube.com/vi/${ytId}/default.jpg" alt="">`
    : (v.capa ? `<img src="${v.capa}" alt="">` : '🎬');
  const assistido = _progressoCache[v.id];
  const activeClass = _videoAtualId === v.id ? ' active' : '';
  const assistidoClass = assistido ? ' assistido-item' : '';
  const tituloEsc = (v.titulo||'').replace(/'/g, "\\'");
  const durEsc = (v.duracao||'').replace(/'/g, "\\'");
  return `
  <div class="sb-video-item${activeClass}${assistidoClass}" id="sb-item-${v.id}" onclick="selecionarVideo(${v.id},'${v.url}','${tituloEsc}','${durEsc}')">
    <div class="sb-vid-thumb">${thumb}</div>
    <div class="sb-vid-info">
      <div class="sb-vid-title">${v.titulo||'Sem título'}</div>
      ${v.duracao ? `<div class="sb-vid-dur">⏱ ${v.duracao}</div>` : ''}
    </div>
    ${assistido ? '<div class="sb-vid-check">✓</div>' : ''}
  </div>`;
}

function toggleSbSecao(bodyId, arrowId) {
  const body = document.getElementById(bodyId);
  const arrow = document.getElementById(arrowId);
  if (!body) return;
  const isOpen = body.style.display !== 'none';
  body.style.display = isOpen ? 'none' : 'block';
  if (arrow) arrow.classList.toggle('open', !isOpen);
}

function selecionarVideo(conteudoId, url, titulo, duracao) {
  // Remover active anterior
  document.querySelectorAll('.sb-video-item.active').forEach(el => el.classList.remove('active'));
  const item = document.getElementById(`sb-item-${conteudoId}`);
  if (item) item.classList.add('active');
  _videoAtualId = conteudoId;

  const playerArea = document.getElementById('player-area');
  const playerInfo = document.getElementById('player-info');
  const playerTitulo = document.getElementById('player-titulo');
  const playerMeta = document.getElementById('player-meta');
  const playerBtn = document.getElementById('player-check-btn');
  if (!playerArea) return;

  // Montar player
  const embedUrl = getYTEmbed(url);
  if (embedUrl) {
    playerArea.innerHTML = `<iframe src="${embedUrl}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
  } else if (url && url.match(/\.(mp4|webm|ogg)$/i)) {
    playerArea.innerHTML = `<video src="${url}" controls autoplay></video>`;
  } else if (url && url !== '#') {
    playerArea.innerHTML = `<div class="player-placeholder"><div class="pp-icon">🎬</div><p>Clique para abrir o vídeo</p><button onclick="window.open('${url}','_blank')" style="margin-top:12px;padding:8px 20px;background:var(--rose);color:white;border:none;border-radius:20px;cursor:pointer;">Abrir vídeo ↗</button></div>`;
  } else {
    playerArea.innerHTML = `<div class="player-placeholder"><div class="pp-icon">⚠️</div><p>URL do vídeo não disponível</p></div>`;
  }

  // Info do vídeo
  if (playerInfo) playerInfo.style.display = 'block';
  if (playerTitulo) playerTitulo.textContent = titulo || 'Sem título';
  if (playerMeta && duracao) playerMeta.textContent = '⏱ ' + duracao;
  else if (playerMeta) playerMeta.textContent = '';

  // Botão de marcar assistido
  const jaAssistido = _progressoCache[conteudoId];
  if (playerBtn) {
    playerBtn.textContent = jaAssistido ? '✓ Assistido' : '✓ Marcar como assistido';
    playerBtn.className = 'player-check-btn' + (jaAssistido ? ' done' : '');
    playerBtn.disabled = !!jaAssistido;
  }

  // Marcar automaticamente após 3 segundos
  setTimeout(() => marcarAtualAssistido(), 3000);
}

async function marcarAtualAssistido() {
  if (!_videoAtualId || !currentUser) return;
  if (_progressoCache[_videoAtualId]) return; // já marcado
  const res = await apiFetch(`/api/curso/progresso`, {
    method: 'POST',
    body: JSON.stringify({ usuario_id: currentUser.id, conteudo_id: _videoAtualId, percentual: 100 })
  });
  if (res) {
    _progressoCache[_videoAtualId] = true;
    // Atualizar botão
    const btn = document.getElementById('player-check-btn');
    if (btn) { btn.textContent = '✓ Assistido'; btn.className = 'player-check-btn done'; btn.disabled = true; }
    // Atualizar badge no sidebar
    const item = document.getElementById(`sb-item-${_videoAtualId}`);
    if (item) {
      item.classList.add('assistido-item');
      if (!item.querySelector('.sb-vid-check')) {
        item.insertAdjacentHTML('beforeend', '<div class="sb-vid-check">✓</div>');
      }
    }
    // Atualizar barra de progresso
    const allVideos = await apiFetch('/api/conteudos') || [];
    const videos = allVideos.filter(v => v.categoria === 'video' && v.ativo);
    const total = videos.length;
    const assistidos = Object.values(_progressoCache).filter(v => v).length;
    const pct = total > 0 ? Math.round((assistidos / total) * 100) : 0;
    const fill = document.getElementById('sidebar-progress-fill');
    const txt = document.getElementById('sidebar-progress-txt');
    if (fill) fill.style.width = pct + '%';
    if (txt) txt.textContent = `${assistidos} de ${total} vídeos · ${pct}%`;
  }
}

async function renderGrade(idx) {
  const cat = catMap[idx] || 'outro';
  const apiCont = await apiFetch('/api/conteudos') || [];
  const apiEbooks = await apiFetch('/api/ebooks') || [];
  const mappedEbooks = apiEbooks.map(e => ({
    id: 'eb'+e.id, titulo: e.titulo, categoria: 'ebook',
    subcategoria: e.descricao || 'Material exclusivo',
    url: API_URL + e.url_pdf, capa: e.url_capa ? API_URL + e.url_capa : null,
    cor: '#c9907a,#a96b55', emoji: '📖', ativo: 1
  }));
  const allCont = [...apiCont, ...mappedEbooks];
  DB.set('nn_conteudos', allCont);
  const conteudos = allCont.filter(c => c.categoria === cat && c.ativo);
  const list = document.getElementById('cont-list');
  if (!list) return;
  list.innerHTML = '';
  if (!conteudos.length) {
    list.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="ei">📭</div><p>Nenhum conteúdo ainda.<br>A Nalin está preparando algo especial!</p></div>`;
    return;
  }
  conteudos.forEach(c => {
    const isEbook = c.categoria === 'ebook';
    const meta = isEbook ? (c.paginas ? `<span>📄 ${c.paginas}</span>` : `<span>📄 PDF</span>`) : (c.duracao ? `<span>⏱ ${c.duracao}</span>` : '');
    const ytId = getYTId(c.url);
    let thumbImg = '';
    if (ytId) thumbImg = `<img src="https://img.youtube.com/vi/${ytId}/hqdefault.jpg" alt="Capa">`;
    else if (c.capa) thumbImg = `<img src="${c.capa}" alt="Capa">`;
    list.innerHTML += `
    <div class="ccard" onclick="openConteudo('${c.url}')" title="${c.titulo}">
      <div class="cthumb" style="background:linear-gradient(135deg,${c.cor||'#e8b4a0,#c9907a'})">
        ${thumbImg}
        <div class="te" style="${thumbImg?'opacity:0.2':''}">${c.emoji||'📄'}</div>
        ${!isEbook ? '<div class="play-btn">▶</div>' : ''}
      </div>
      <div class="cinfo">
        <div class="ctag">${c.subcategoria||''}</div>
        <div class="ctitle">${c.titulo}</div>
        <div class="cmeta">${meta}</div>
      </div>
    </div>`;
  });
}

function switchTab(idx,el){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  renderConteudo(idx);
}
function openConteudo(url){if(url&&url!=='#')window.open(url,'_blank');}
"""
    lines[start:end+1] = [new_js]
    with open('www/index.html', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('JS substituido: OK')
