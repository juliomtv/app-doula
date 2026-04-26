"""Script para atualizar app.html com layout de mini curso e progresso de vídeos"""

with open('www/app.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Atualizar CSS da grade de conteúdo e cards de vídeo
old_css = '''.cont-grid{padding:18px 12px;display:grid;grid-template-columns:repeat(3, 1fr);gap:10px;}
.ccard{background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px var(--shadow-soft);cursor:pointer;transition:transform .15s;display:flex;flex-direction:column;}
.ccard:active{transform:scale(.96);}
.cthumb{aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;background:var(--rose-pale);}
.cthumb .te{font-size:28px;z-index:1;}
.cthumb img{position:absolute;width:100%;height:100%;object-fit:cover;}
.play-btn{position:absolute;width:28px;height:28px;border-radius:50%;background:rgba(255,255,255,.9);display:flex;align-items:center;justify-content:center;font-size:10px;box-shadow:0 2px 8px rgba(0,0,0,.15);z-index:2;}
.cinfo{padding:8px;flex:1;display:flex;flex-direction:column;}
.ctag{font-size:8px;letter-spacing:0.5px;text-transform:uppercase;color:var(--rose);font-weight:600;margin-bottom:2px;}
.ctitle{font-size:11px;font-weight:500;color:var(--dark);line-height:1.2;flex:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.cmeta{font-size:9px;color:var(--light);margin-top:4px;display:flex;gap:6px;}'''

new_css = '''.cont-grid{padding:12px;display:grid;grid-template-columns:repeat(2, 1fr);gap:10px;}
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

if old_css in content:
    content = content.replace(old_css, new_css, 1)
    print('CSS atualizado: OK')
else:
    print('FAIL: CSS não encontrado')

# 2. Atualizar HTML da tela de conteúdo para ter barra de progresso geral
old_cont_screen = '''<!-- ════════════ CONTEÚDO SCREEN ════════════ -->
<div class="screen" id="conteudo">
  <div class="cont-hdr"><h2>Conteúdo</h2><p>Materiais exclusivos para sua jornada</p>
    <div class="tabs">
      <div class="tab active" onclick="switchTab(0,this)">Vídeos</div>
      <div class="tab" onclick="switchTab(1,this)">E-books</div>
      <div class="tab" onclick="switchTab(2,this)">Meditações</div>
    </div>
  </div>
  <div class="scroll"><div class="cont-grid" id="cont-list"></div></div>'''

new_cont_screen = '''<!-- ════════════ CONTEÚDO SCREEN ════════════ -->
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

if old_cont_screen in content:
    content = content.replace(old_cont_screen, new_cont_screen, 1)
    print('HTML da tela de conteúdo atualizado: OK')
else:
    print('FAIL: HTML da tela de conteúdo não encontrado')

# 3. Substituir renderConteudo por versão com seções e progresso
old_render = '''async function renderConteudo(idx){
  currentTab=idx;
  const cat=catMap[idx]||'video';
  let conteudos = [];
  
  if(cat === 'ebook') {
    const apiEbooks = await apiFetch('/api/ebooks') || [];
    conteudos = apiEbooks.map(e => ({
      id: e.id, titulo: e.titulo, categoria: 'ebook', subcategoria: e.descricao || 'Material exclusivo',
      url: API_URL + e.url_pdf, cor: '#c9907a,#a96b55', emoji: '📖'
    }));
  } else {
    const apiCont = await apiFetch('/api/conteudos') || [];
    conteudos = apiCont.filter(c => c.categoria === cat);
  }
  const list=document.getElementById('cont-list');
  list.innerHTML='';
  if(!conteudos.length){
    list.innerHTML=`<div class="empty-state"><div class="ei">📭</div><p>Nenhum conteúdo ainda.</p></div>`;
    return;
  }
  conteudos.forEach(c=>{
    const isPlay=c.categoria!=='ebook';
    const ytId = getYTId(c.url);
    const thumbImg = ytId ? `<img src="https://img.youtube.com/vi/${ytId}/hqdefault.jpg">` : '';
    list.innerHTML+=`
    <div class="ccard" onclick="openConteudo('${c.url}')">
      <div class="cthumb" style="background:linear-gradient(135deg,${c.cor||'#e8b4a0,#c9907a'})">
        ${thumbImg}
        <div class="te" style="${thumbImg ? 'opacity:0.2' : ''}">${c.emoji||'📄'}</div>
        ${isPlay?'<div class="play-btn">▶</div>':''}
      </div>
      <div class="cinfo">
        <div class="ctag">${c.subcategoria||''}</div>
        <div class="ctitle">${c.titulo}</div>
        <div class="cmeta">${c.duracao || c.paginas || ''}</div>
      </div>
    </div>`;
  });
}
function switchTab(idx,el){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  renderConteudo(idx);
  const catName = {0:'Vídeos',1:'E-books',2:'Meditações'}[idx];
  logActivity(`Acessou ${catName}`);
}
function openConteudo(url, titulo = 'Conteúdo'){
  if(url){
    logActivity(`Assistiu/Leu: ${titulo}`);
    window.open(url,'_blank');
  }
}'''

new_render = '''// Cache de progresso de vídeos
let videoProgressoCache = {};

async function carregarProgresso(){
  if(!currentUser) return;
  const rows = await apiFetch(`/api/progresso?user_id=${currentUser.id}`) || [];
  videoProgressoCache = {};
  rows.forEach(r => { videoProgressoCache[r.conteudo_id] = r; });
}

async function marcarVideoAssistido(conteudoId, titulo){
  if(!currentUser) return;
  await apiFetch('/api/progresso', {
    method: 'POST',
    body: JSON.stringify({ user_id: currentUser.id, conteudo_id: conteudoId, assistido: 1, percentual: 100 })
  });
  videoProgressoCache[conteudoId] = { assistido: 1, percentual: 100 };
  logActivity('Assistiu ao vídeo', titulo);
}

function renderCardVideo(c, assistido){
  const ytId = getYTId(c.url);
  const thumbImg = ytId ? `<img src="https://img.youtube.com/vi/${ytId}/hqdefault.jpg" loading="lazy">` : '';
  const checkBadge = assistido ? '<div class="check-badge">✓</div>' : '';
  return `
  <div class="ccard ${assistido ? 'assistido' : ''}" onclick="openConteudo('${c.url}', ${c.id}, '${(c.titulo||'').replace(/'/g,"\\'")}')">
    <div class="cthumb" style="background:linear-gradient(135deg,${c.cor||'#e8b4a0,#c9907a'})">
      ${thumbImg}
      <div class="te" style="${thumbImg ? 'opacity:0.2' : ''}">${c.emoji||'🎬'}</div>
      <div class="play-btn">▶</div>
      ${checkBadge}
    </div>
    <div class="cinfo">
      <div class="ctitle">${c.titulo}</div>
      <div class="cmeta">${c.duracao||''} ${assistido ? '<span style="color:var(--rose);">✓ Assistido</span>' : ''}</div>
    </div>
  </div>`;
}

async function renderConteudo(idx){
  currentTab=idx;
  const cat=catMap[idx]||'video';
  const list=document.getElementById('cont-list');
  const progressWrap = document.getElementById('curso-progress-wrap');
  list.innerHTML='<div style="padding:32px;text-align:center;color:var(--lite);">Carregando...</div>';
  
  if(cat === 'ebook') {
    if(progressWrap) progressWrap.style.display = 'none';
    const apiEbooks = await apiFetch('/api/ebooks') || [];
    list.innerHTML='';
    if(!apiEbooks.length){ list.innerHTML=`<div class="empty-state"><div class="ei">📭</div><p>Nenhum e-book ainda.</p></div>`; return; }
    list.innerHTML = '<div class="cont-grid">' + apiEbooks.map(e => `
      <div class="ccard" onclick="openConteudo('${API_URL + e.url_pdf}', null, '${(e.titulo||'').replace(/'/g,"\\'")}')">
        <div class="cthumb" style="background:linear-gradient(135deg,#c9907a,#a96b55)">
          <div class="te">📖</div>
        </div>
        <div class="cinfo">
          <div class="ctitle">${e.titulo}</div>
          <div class="cmeta">${e.descricao||'Material exclusivo'}</div>
        </div>
      </div>`).join('') + '</div>';
    return;
  }
  
  if(cat === 'meditacao') {
    if(progressWrap) progressWrap.style.display = 'none';
    const apiCont = await apiFetch('/api/conteudos') || [];
    const meds = apiCont.filter(c => c.categoria === 'meditacao');
    list.innerHTML='';
    if(!meds.length){ list.innerHTML=`<div class="empty-state"><div class="ei">🧘</div><p>Nenhuma meditação ainda.</p></div>`; return; }
    list.innerHTML = '<div class="cont-grid">' + meds.map(c => {
      const ytId = getYTId(c.url);
      const thumbImg = ytId ? `<img src="https://img.youtube.com/vi/${ytId}/hqdefault.jpg" loading="lazy">` : '';
      return `<div class="ccard" onclick="openConteudo('${c.url}', null, '${(c.titulo||'').replace(/'/g,"\\'")}')">
        <div class="cthumb" style="background:linear-gradient(135deg,${c.cor||'#e8b4a0,#c9907a'})">${thumbImg}<div class="te" style="${thumbImg?'opacity:.2':''}">${c.emoji||'🧘'}</div><div class="play-btn">▶</div></div>
        <div class="cinfo"><div class="ctitle">${c.titulo}</div><div class="cmeta">${c.duracao||''}</div></div>
      </div>`;
    }).join('') + '</div>';
    return;
  }
  
  // ── VÍDEOS: layout de mini curso com seções ──
  await carregarProgresso();
  const secoes = await apiFetch('/api/secoes') || [];
  const apiCont = await apiFetch('/api/conteudos') || [];
  const todoVideos = apiCont.filter(c => c.categoria === 'video');
  
  // Calcular progresso geral
  const totalVids = todoVideos.length;
  const assistidosCount = todoVideos.filter(c => videoProgressoCache[c.id]?.assistido).length;
  if(progressWrap && totalVids > 0){
    progressWrap.style.display = 'block';
    const pct = Math.round((assistidosCount / totalVids) * 100);
    const fillEl = document.getElementById('curso-progress-fill');
    const txtEl = document.getElementById('curso-progress-txt');
    if(fillEl) fillEl.style.width = pct + '%';
    if(txtEl) txtEl.textContent = `${assistidosCount} de ${totalVids} vídeos assistidos · ${pct}%`;
  } else if(progressWrap) {
    progressWrap.style.display = 'none';
  }
  
  list.innerHTML = '';
  
  if(secoes.length === 0 && todoVideos.length === 0){
    list.innerHTML = `<div class="empty-state"><div class="ei">🎬</div><p>Nenhum vídeo ainda.</p></div>`;
    return;
  }
  
  // Renderizar seções
  secoes.forEach((s, idx) => {
    const videosSecao = (s.videos || []);
    const totalS = videosSecao.length;
    const assistidosS = videosSecao.filter(v => videoProgressoCache[v.id]?.assistido).length;
    const pctS = totalS > 0 ? Math.round((assistidosS / totalS) * 100) : 0;
    
    const secaoDiv = document.createElement('div');
    secaoDiv.className = 'secao-wrap';
    secaoDiv.innerHTML = `
      <div class="secao-hdr" onclick="toggleSecaoApp(${s.id})">
        <div class="secao-num">${idx+1}</div>
        <div class="secao-info">
          <div class="secao-titulo">${s.titulo}</div>
          ${s.descricao ? `<div class="secao-sub">${s.descricao}</div>` : ''}
          <div class="secao-progress-bar"><div class="secao-progress-fill" style="width:${pctS}%"></div></div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;flex-shrink:0;">
          <span style="font-size:10px;color:var(--lite);">${assistidosS}/${totalS}</span>
          <span id="secao-arrow-app-${s.id}" style="font-size:14px;color:var(--lite);">▼</span>
        </div>
      </div>
      <div id="secao-body-app-${s.id}" class="secao-body">
        ${totalS === 0 ? '<div style="padding:12px 16px;text-align:center;color:var(--lite);font-size:12px;">Nenhum vídeo nesta seção ainda.</div>' :
          '<div class="cont-grid" style="padding:8px 12px;">' + videosSecao.map(c => renderCardVideo(c, !!videoProgressoCache[c.id]?.assistido)).join('') + '</div>'}
      </div>`;
    list.appendChild(secaoDiv);
  });
  
  // Vídeos sem seção
  const semSecao = todoVideos.filter(c => !c.secao_id);
  if(semSecao.length > 0){
    const div = document.createElement('div');
    div.innerHTML = '<div class="cont-grid" style="padding:8px 12px;">' + semSecao.map(c => renderCardVideo(c, !!videoProgressoCache[c.id]?.assistido)).join('') + '</div>';
    list.appendChild(div);
  }
}

function toggleSecaoApp(id){
  const body = document.getElementById(`secao-body-app-${id}`);
  const arrow = document.getElementById(`secao-arrow-app-${id}`);
  if(!body) return;
  const hidden = body.style.display === 'none';
  body.style.display = hidden ? '' : 'none';
  if(arrow) arrow.textContent = hidden ? '▼' : '▶';
}

function switchTab(idx,el){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  renderConteudo(idx);
  const catName = {0:'Vídeos',1:'E-books',2:'Meditações'}[idx];
  logActivity(`Acessou ${catName}`);
}

async function openConteudo(url, conteudoId = null, titulo = 'Conteúdo'){
  if(url){
    window.open(url,'_blank');
    if(conteudoId){
      await marcarVideoAssistido(conteudoId, titulo);
      // Atualizar visual do card sem re-renderizar tudo
      const card = document.querySelector(`[onclick*="openConteudo('${url}'"]`);
      if(card){
        card.classList.add('assistido');
        const meta = card.querySelector('.cmeta');
        if(meta && !meta.innerHTML.includes('Assistido')) meta.innerHTML += ' <span style="color:var(--rose);">✓ Assistido</span>';
        const thumb = card.querySelector('.cthumb');
        if(thumb && !thumb.querySelector('.check-badge')){
          const badge = document.createElement('div');
          badge.className = 'check-badge';
          badge.textContent = '✓';
          thumb.appendChild(badge);
        }
      }
      // Atualizar barra de progresso geral
      const apiCont = await apiFetch('/api/conteudos') || [];
      const todoVideos = apiCont.filter(c => c.categoria === 'video');
      const assistidosCount = todoVideos.filter(c => videoProgressoCache[c.id]?.assistido).length;
      const pct = todoVideos.length > 0 ? Math.round((assistidosCount / todoVideos.length) * 100) : 0;
      const fillEl = document.getElementById('curso-progress-fill');
      const txtEl = document.getElementById('curso-progress-txt');
      if(fillEl) fillEl.style.width = pct + '%';
      if(txtEl) txtEl.textContent = `${assistidosCount} de ${todoVideos.length} vídeos assistidos · ${pct}%`;
    }
  }
}'''

if old_render in content:
    content = content.replace(old_render, new_render, 1)
    print('renderConteudo substituído: OK')
else:
    print('FAIL: renderConteudo não encontrado')

with open('www/app.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('app.html salvo.')
