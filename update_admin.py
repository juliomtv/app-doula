"""Script para atualizar admin.html com gerenciamento de seções do mini curso"""

with open('www/admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Substituir a página de vídeos (p-videos) por nova versão com seções
old_videos_page = '''    <div class="page" id="p-videos">
      <div class="page-hdr" style="display:flex;align-items:flex-start;justify-content:space-between;">
        <div><h1>Videoaulas</h1><p>Gerencie seus vídeos</p></div>
        <button class="btn-sm btn-rose-sm" onclick="openAddConteudo('video')">+ Adicionar Vídeo</button>
      </div>
      <div class="table-card"><table><thead><tr><th>Título</th><th>Categoria</th><th>Duração</th><th>Status</th><th>Ações</th></tr></thead><tbody id="videos-tbody"></tbody></table></div>
    </div>'''

new_videos_page = '''    <div class="page" id="p-videos">
      <div class="page-hdr" style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:8px;">
        <div><h1>Mini Curso</h1><p>Gerencie as seções e videoaulas</p></div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button class="btn-sm btn-ghost" onclick="openAddSecao()">+ Nova Seção</button>
          <button class="btn-sm btn-rose-sm" onclick="openAddConteudo('video')">+ Adicionar Vídeo</button>
        </div>
      </div>
      <!-- Barra de progresso geral do curso -->
      <div id="curso-stats" style="display:none;margin-bottom:16px;padding:14px 18px;background:white;border-radius:12px;box-shadow:0 2px 8px var(--shadow-soft);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <span style="font-size:13px;font-weight:600;color:var(--dark);">Progresso Geral das Doulandas</span>
          <span id="curso-stats-txt" style="font-size:12px;color:var(--lite);">—</span>
        </div>
      </div>
      <!-- Seções do mini curso -->
      <div id="secoes-container"></div>
      <!-- Vídeos sem seção -->
      <div id="videos-sem-secao-wrap" style="display:none;margin-top:16px;">
        <div class="table-card">
          <div class="tc-hdr" style="display:flex;justify-content:space-between;align-items:center;">
            <h3>📹 Vídeos sem seção</h3>
          </div>
          <table><thead><tr><th>Título</th><th>Duração</th><th>Status</th><th>Ações</th></tr></thead><tbody id="videos-sem-secao-tbody"></tbody></table>
        </div>
      </div>
    </div>'''

if old_videos_page in content:
    content = content.replace(old_videos_page, new_videos_page, 1)
    print('Página de vídeos substituída: OK')
else:
    print('FAIL: página de vídeos não encontrada')

# 2. Adicionar modal de seção após o modal de conteúdo
modal_cont_end = '''  </div>
</div>
<div class="modal-overlay" id="modal-ebook">'''

new_modal_secao = '''  </div>
</div>
<!-- Modal de Seção do Mini Curso -->
<div class="modal-overlay" id="modal-secao">
  <div class="modal">
    <div class="modal-hdr"><h3 id="msecao-title">Nova Seção</h3><button class="modal-close" onclick="closeModal('modal-secao')">✕</button></div>
    <div class="modal-body">
      <input type="hidden" id="ms-id">
      <div class="mfield"><label>Título da Seção</label><input type="text" id="ms-titulo" placeholder="Ex: Módulo 1 — Preparação para o Parto"></div>
      <div class="mfield"><label>Descrição (opcional)</label><textarea id="ms-descricao" placeholder="Breve descrição do que será abordado nesta seção"></textarea></div>
      <div class="mfield"><label>Ordem</label><input type="number" id="ms-ordem" value="1" min="1"></div>
      <div id="ms-err" style="color:var(--err);font-size:13px;"></div>
    </div>
    <div class="modal-footer"><button class="btn-full btn-cancel" onclick="closeModal('modal-secao')">Cancelar</button><button class="btn-full btn-save" onclick="saveSecao()">Salvar Seção</button></div>
  </div>
</div>
<div class="modal-overlay" id="modal-ebook">'''

if modal_cont_end in content:
    content = content.replace(modal_cont_end, new_modal_secao, 1)
    print('Modal de seção adicionado: OK')
else:
    print('FAIL: posição do modal de seção não encontrada')

# 3. Adicionar campo de seção no modal de conteúdo (mc-url)
old_mc_url = '      <div class="mfield"><label>URL</label><input type="url" id="mc-url"></div>'
new_mc_url = '''      <div class="mfield" id="mc-secao-wrap"><label>Seção do Mini Curso</label>
        <select id="mc-secao" style="width:100%;padding:10px 12px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;background:white;">
          <option value="">— Sem seção —</option>
        </select>
      </div>
      <div class="mfield" id="mc-ordem-wrap"><label>Ordem dentro da seção</label><input type="number" id="mc-ordem" value="1" min="1"></div>
      <div class="mfield"><label>URL</label><input type="url" id="mc-url"></div>'''

if old_mc_url in content:
    content = content.replace(old_mc_url, new_mc_url, 1)
    print('Campo de seção no modal de conteúdo: OK')
else:
    print('FAIL: campo mc-url não encontrado')

# 4. Atualizar renderConteudoTable para a nova função renderVideosPage
old_render_func = '''async function renderConteudoTable(cat){
  const cont = await apiFetch('/api/admin/conteudos') || [];
  const filtered = cont.filter(c=>c.categoria===cat);
  const tbodyId={video:'videos-tbody',ebook:'ebooks-tbody',meditacao:'meditacoes-tbody'}[cat];
  if(!tbodyId)return;
  document.getElementById(tbodyId).innerHTML=filtered.map(c=>`
    <tr>
      <td><div class="td-name">${c.emoji||''} ${c.titulo}</div><div style="font-size:11px;color:var(--lite);">${c.descricao||''}</div></td>
      <td><span class="badge badge-rose">${c.subcategoria||'—'}</span></td>
      <td>${c.duracao||c.paginas||'—'}</td>
      <td><span class="badge ${c.ativo?'badge-ok':'badge-err'}">${c.ativo?'Publicado':'Oculto'}</span></td>
      <td><div class="td-actions">
        <button class="btn-sm btn-ghost" onclick="editConteudo(${c.id})">✏️ Editar</button>
        <button class="btn-sm btn-danger" onclick="toggleConteudo(${c.id})">${c.ativo?'🚫 Ocultar':'✅ Publicar'}</button>
        <button class="btn-sm btn-danger" onclick="deleteConteudo(${c.id})">🗑️</button>
      </div></td>
    </tr>
  `).join('');
}'''

new_render_func = '''async function renderConteudoTable(cat){
  if(cat === 'video') { await renderVideosPage(); return; }
  const cont = await apiFetch('/api/admin/conteudos') || [];
  const filtered = cont.filter(c=>c.categoria===cat);
  const tbodyId={ebook:'ebooks-tbody',meditacao:'meditacoes-tbody'}[cat];
  if(!tbodyId)return;
  document.getElementById(tbodyId).innerHTML=filtered.map(c=>`
    <tr>
      <td><div class="td-name">${c.emoji||''} ${c.titulo}</div><div style="font-size:11px;color:var(--lite);">${c.descricao||''}</div></td>
      <td><span class="badge badge-rose">${c.subcategoria||'—'}</span></td>
      <td>${c.duracao||c.paginas||'—'}</td>
      <td><span class="badge ${c.ativo?'badge-ok':'badge-err'}">${c.ativo?'Publicado':'Oculto'}</span></td>
      <td><div class="td-actions">
        <button class="btn-sm btn-ghost" onclick="editConteudo(${c.id})">✏️ Editar</button>
        <button class="btn-sm btn-danger" onclick="toggleConteudo(${c.id})">${c.ativo?'🚫 Ocultar':'✅ Publicar'}</button>
        <button class="btn-sm btn-danger" onclick="deleteConteudo(${c.id})">🗑️</button>
      </div></td>
    </tr>
  `).join('');
}

async function renderVideosPage(){
  const secoes = await apiFetch('/api/admin/secoes') || [];
  const allCont = await apiFetch('/api/admin/conteudos') || [];
  const todoVideos = allCont.filter(c => c.categoria === 'video');
  const progresso = await apiFetch('/api/admin/progresso') || [];
  
  // Stats gerais
  const statsEl = document.getElementById('curso-stats');
  const statsTxt = document.getElementById('curso-stats-txt');
  if(statsEl && todoVideos.length > 0){
    statsEl.style.display = 'block';
    statsTxt.textContent = `${todoVideos.length} vídeos · ${secoes.length} seções`;
  }
  
  // Renderizar seções
  const container = document.getElementById('secoes-container');
  container.innerHTML = '';
  if(secoes.length === 0){
    container.innerHTML = '<div class="empty-state" style="padding:32px;text-align:center;"><div style="font-size:32px;margin-bottom:8px;">📚</div><p style="color:var(--lite);">Nenhuma seção criada ainda. Clique em "+ Nova Seção" para começar.</p></div>';
  }
  secoes.forEach((s, idx) => {
    const videosSecao = s.videos || [];
    const div = document.createElement('div');
    div.className = 'table-card';
    div.style.marginBottom = '16px';
    div.innerHTML = `
      <div class="tc-hdr" style="display:flex;justify-content:space-between;align-items:center;cursor:pointer;" onclick="toggleSecaoCollapse(${s.id})">
        <div style="display:flex;align-items:center;gap:10px;">
          <span style="font-size:18px;font-weight:700;color:var(--rose);">${idx+1}</span>
          <div>
            <h3 style="margin:0;">${s.titulo}</h3>
            ${s.descricao ? `<p style="margin:2px 0 0;font-size:12px;color:var(--lite);">${s.descricao}</p>` : ''}
          </div>
          <span class="badge badge-rose">${videosSecao.length} vídeo${videosSecao.length !== 1 ? 's' : ''}</span>
        </div>
        <div style="display:flex;gap:6px;align-items:center;">
          <button class="btn-sm btn-ghost" onclick="event.stopPropagation();editSecao(${s.id})" title="Editar seção">✏️</button>
          <button class="btn-sm btn-danger" onclick="event.stopPropagation();deleteSecao(${s.id})" title="Excluir seção">🗑️</button>
          <span id="secao-arrow-${s.id}" style="font-size:16px;transition:.2s;">▼</span>
        </div>
      </div>
      <div id="secao-body-${s.id}">
        ${videosSecao.length === 0 ? '<div style="padding:16px;text-align:center;color:var(--lite);font-size:13px;">Nenhum vídeo nesta seção. Adicione um vídeo e selecione esta seção.</div>' : ''}
        ${videosSecao.length > 0 ? `
        <table style="margin-top:0;"><thead><tr><th>Título</th><th>Duração</th><th>Status</th><th>Ações</th></tr></thead><tbody>
        ${videosSecao.map(c => `
          <tr>
            <td><div class="td-name">🎬 ${c.titulo}</div><div style="font-size:11px;color:var(--lite);">${c.descricao||''}</div></td>
            <td>${c.duracao||'—'}</td>
            <td><span class="badge ${c.ativo?'badge-ok':'badge-err'}">${c.ativo?'Publicado':'Oculto'}</span></td>
            <td><div class="td-actions">
              <button class="btn-sm btn-ghost" onclick="editConteudo(${c.id})">✏️</button>
              <button class="btn-sm btn-danger" onclick="toggleConteudo(${c.id})">${c.ativo?'🚫':'✅'}</button>
              <button class="btn-sm btn-danger" onclick="deleteConteudo(${c.id})">🗑️</button>
            </div></td>
          </tr>`).join('')}
        </tbody></table>` : ''}
      </div>`;
    container.appendChild(div);
  });
  
  // Vídeos sem seção
  const semSecao = todoVideos.filter(c => !c.secao_id);
  const wrapEl = document.getElementById('videos-sem-secao-wrap');
  if(wrapEl){
    wrapEl.style.display = semSecao.length > 0 ? 'block' : 'none';
    const tbody = document.getElementById('videos-sem-secao-tbody');
    if(tbody) tbody.innerHTML = semSecao.map(c => `
      <tr>
        <td><div class="td-name">🎬 ${c.titulo}</div></td>
        <td>${c.duracao||'—'}</td>
        <td><span class="badge ${c.ativo?'badge-ok':'badge-err'}">${c.ativo?'Publicado':'Oculto'}</span></td>
        <td><div class="td-actions">
          <button class="btn-sm btn-ghost" onclick="editConteudo(${c.id})">✏️</button>
          <button class="btn-sm btn-danger" onclick="toggleConteudo(${c.id})">${c.ativo?'🚫':'✅'}</button>
          <button class="btn-sm btn-danger" onclick="deleteConteudo(${c.id})">🗑️</button>
        </div></td>
      </tr>`).join('');
  }
}

function toggleSecaoCollapse(id){
  const body = document.getElementById(`secao-body-${id}`);
  const arrow = document.getElementById(`secao-arrow-${id}`);
  if(!body) return;
  const hidden = body.style.display === 'none';
  body.style.display = hidden ? '' : 'none';
  if(arrow) arrow.textContent = hidden ? '▼' : '▶';
}

function openAddSecao(){
  document.getElementById('msecao-title').textContent = 'Nova Seção';
  document.getElementById('ms-id').value = '';
  document.getElementById('ms-titulo').value = '';
  document.getElementById('ms-descricao').value = '';
  document.getElementById('ms-ordem').value = '1';
  document.getElementById('ms-err').textContent = '';
  openModal('modal-secao');
}

async function editSecao(id){
  const secoes = await apiFetch('/api/admin/secoes') || [];
  const s = secoes.find(x => x.id === id);
  if(!s) return;
  document.getElementById('msecao-title').textContent = 'Editar Seção';
  document.getElementById('ms-id').value = s.id;
  document.getElementById('ms-titulo').value = s.titulo || '';
  document.getElementById('ms-descricao').value = s.descricao || '';
  document.getElementById('ms-ordem').value = s.ordem || 1;
  document.getElementById('ms-err').textContent = '';
  openModal('modal-secao');
}

async function saveSecao(){
  const titulo = document.getElementById('ms-titulo').value.trim();
  const errEl = document.getElementById('ms-err');
  if(!titulo){ errEl.textContent = 'Título obrigatório.'; return; }
  const obj = {
    id: document.getElementById('ms-id').value,
    titulo,
    descricao: document.getElementById('ms-descricao').value,
    ordem: parseInt(document.getElementById('ms-ordem').value) || 1
  };
  const res = await apiFetch('/api/admin/secoes', { method: 'POST', body: JSON.stringify(obj) });
  if(res && res.status === 'success'){
    showToastA('Seção salva! ✨');
    closeModal('modal-secao');
    renderVideosPage();
  } else {
    errEl.textContent = (res && res.message) || 'Erro ao salvar seção.';
  }
}

async function deleteSecao(id){
  if(!confirm('Excluir esta seção? Os vídeos dentro dela NÃO serão excluídos — apenas desvinculados.')) return;
  const res = await apiFetch(`/api/admin/secoes/${id}`, { method: 'DELETE' });
  if(res && res.status === 'success'){
    showToastA('Seção excluída.');
    renderVideosPage();
  }
}'''

if old_render_func in content:
    content = content.replace(old_render_func, new_render_func, 1)
    print('renderConteudoTable atualizado: OK')
else:
    print('FAIL: renderConteudoTable não encontrado')

# 5. Atualizar openAddConteudo para carregar seções no select
old_openAdd = '''function openAddConteudo(cat){
  document.getElementById('mcont-title').textContent={video:'Novo Vídeo',ebook:'Novo E-book',meditacao:'Nova Meditação'}[cat]||'Novo Conteúdo';
  document.getElementById('mc-cat').value=cat;
  document.getElementById('mc-id').value='';
  ['mc-titulo','mc-subcat','mc-emoji','mc-desc','mc-dur','mc-pag','mc-url'].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
  document.getElementById('mc-cor').value='#e8b4a0,#c9907a';
  document.getElementById('mc-dur-wrap').style.display=cat!=='ebook'?'block':'none';
  document.getElementById('mc-pag-wrap').style.display=cat==='ebook'?'block':'none';
  openModal('modal-cont');
}'''

new_openAdd = '''async function openAddConteudo(cat){
  document.getElementById('mcont-title').textContent={video:'Novo Vídeo',ebook:'Novo E-book',meditacao:'Nova Meditação'}[cat]||'Novo Conteúdo';
  document.getElementById('mc-cat').value=cat;
  document.getElementById('mc-id').value='';
  ['mc-titulo','mc-subcat','mc-emoji','mc-desc','mc-dur','mc-pag','mc-url'].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
  document.getElementById('mc-cor').value='#e8b4a0,#c9907a';
  document.getElementById('mc-dur-wrap').style.display=cat!=='ebook'?'block':'none';
  document.getElementById('mc-pag-wrap').style.display=cat==='ebook'?'block':'none';
  // Carregar seções no select (apenas para vídeos)
  const secaoWrap = document.getElementById('mc-secao-wrap');
  const ordemWrap = document.getElementById('mc-ordem-wrap');
  if(secaoWrap) secaoWrap.style.display = cat === 'video' ? 'block' : 'none';
  if(ordemWrap) ordemWrap.style.display = cat === 'video' ? 'block' : 'none';
  if(cat === 'video'){
    await carregarSecoesSelect('');
    const ordemEl = document.getElementById('mc-ordem');
    if(ordemEl) ordemEl.value = '1';
  }
  openModal('modal-cont');
}

async function carregarSecoesSelect(secaoIdSelecionada){
  const select = document.getElementById('mc-secao');
  if(!select) return;
  const secoes = await apiFetch('/api/admin/secoes') || [];
  select.innerHTML = '<option value="">— Sem seção —</option>' + 
    secoes.map(s => `<option value="${s.id}" ${String(s.id) === String(secaoIdSelecionada) ? 'selected' : ''}>${s.titulo}</option>`).join('');
}'''

if old_openAdd in content:
    content = content.replace(old_openAdd, new_openAdd, 1)
    print('openAddConteudo atualizado: OK')
else:
    print('FAIL: openAddConteudo não encontrado')

# 6. Atualizar editConteudo para carregar seções e preencher secao_id
old_editCont = '''async function editConteudo(id){
  const cont = await apiFetch('/api/admin/conteudos') || [];
  const c=cont.find(x=>x.id===id);if(!c)return;
  document.getElementById('mcont-title').textContent='Editar Conteúdo';
  document.getElementById('mc-id').value=c.id;
  document.getElementById('mc-cat').value=c.categoria;
  document.getElementById('mc-titulo').value=c.titulo||'';
  document.getElementById('mc-subcat').value=c.subcategoria||'';
  document.getElementById('mc-emoji').value=c.emoji||'';
  document.getElementById('mc-desc').value=c.descricao||'';
  document.getElementById('mc-dur').value=c.duracao||'';
  document.getElementById('mc-pag').value=c.paginas||'';
  document.getElementById('mc-url').value=c.url||'';
  document.getElementById('mc-cor').value=c.cor||'#e8b4a0,#c9907a';
  document.getElementById('mc-dur-wrap').style.display=c.categoria!=='ebook'?'block':'none';
  document.getElementById('mc-pag-wrap').style.display=c.categoria==='ebook'?'block':'none';
  openModal('modal-cont');
}'''

new_editCont = '''async function editConteudo(id){
  const cont = await apiFetch('/api/admin/conteudos') || [];
  const c=cont.find(x=>x.id===id);if(!c)return;
  document.getElementById('mcont-title').textContent='Editar Conteúdo';
  document.getElementById('mc-id').value=c.id;
  document.getElementById('mc-cat').value=c.categoria;
  document.getElementById('mc-titulo').value=c.titulo||'';
  document.getElementById('mc-subcat').value=c.subcategoria||'';
  document.getElementById('mc-emoji').value=c.emoji||'';
  document.getElementById('mc-desc').value=c.descricao||'';
  document.getElementById('mc-dur').value=c.duracao||'';
  document.getElementById('mc-pag').value=c.paginas||'';
  document.getElementById('mc-url').value=c.url||'';
  document.getElementById('mc-cor').value=c.cor||'#e8b4a0,#c9907a';
  document.getElementById('mc-dur-wrap').style.display=c.categoria!=='ebook'?'block':'none';
  document.getElementById('mc-pag-wrap').style.display=c.categoria==='ebook'?'block':'none';
  // Seção e ordem (apenas para vídeos)
  const secaoWrap = document.getElementById('mc-secao-wrap');
  const ordemWrap = document.getElementById('mc-ordem-wrap');
  if(secaoWrap) secaoWrap.style.display = c.categoria === 'video' ? 'block' : 'none';
  if(ordemWrap) ordemWrap.style.display = c.categoria === 'video' ? 'block' : 'none';
  if(c.categoria === 'video'){
    await carregarSecoesSelect(c.secao_id || '');
    const ordemEl = document.getElementById('mc-ordem');
    if(ordemEl) ordemEl.value = c.ordem || 1;
  }
  openModal('modal-cont');
}'''

if old_editCont in content:
    content = content.replace(old_editCont, new_editCont, 1)
    print('editConteudo atualizado: OK')
else:
    print('FAIL: editConteudo não encontrado')

# 7. Atualizar saveConteudo para incluir secao_id e ordem
old_saveCont = '''async function saveConteudo(){
  const titulo=document.getElementById('mc-titulo').value.trim();
  const url = document.getElementById('mc-url').value;
  if(!titulo || !url){document.getElementById('mc-err').textContent='Preencha título e URL.';return;}
  
  const obj={
    id: document.getElementById('mc-id').value,
    titulo,
    categoria:document.getElementById('mc-cat').value,
    subcategoria:document.getElementById('mc-subcat').value,
    emoji:document.getElementById('mc-emoji').value||'📄',
    descricao:document.getElementById('mc-desc').value,
    duracao:document.getElementById('mc-dur').value,
    paginas:document.getElementById('mc-pag').value,
    url:url,
    cor:document.getElementById('mc-cor').value
  };
  const res = await apiFetch('/api/conteudos', {
    method: 'POST',
    body: JSON.stringify(obj)
  });
  if(res && res.status === 'success'){
    showToastA('Conteúdo salvo! ✨');
    closeModal('modal-cont');
    renderConteudoTable(obj.categoria);
  }
}'''

new_saveCont = '''async function saveConteudo(){
  const titulo=document.getElementById('mc-titulo').value.trim();
  const url = document.getElementById('mc-url').value;
  if(!titulo || !url){document.getElementById('mc-err').textContent='Preencha título e URL.';return;}
  const cat = document.getElementById('mc-cat').value;
  const secaoEl = document.getElementById('mc-secao');
  const ordemEl = document.getElementById('mc-ordem');
  const obj={
    id: document.getElementById('mc-id').value,
    titulo,
    categoria: cat,
    subcategoria:document.getElementById('mc-subcat').value,
    emoji:document.getElementById('mc-emoji').value||'📄',
    descricao:document.getElementById('mc-desc').value,
    duracao:document.getElementById('mc-dur').value,
    paginas:document.getElementById('mc-pag').value,
    url:url,
    cor:document.getElementById('mc-cor').value,
    secao_id: (secaoEl && cat === 'video') ? (secaoEl.value || null) : null,
    ordem: (ordemEl && cat === 'video') ? (parseInt(ordemEl.value) || 1) : 0
  };
  const res = await apiFetch('/api/conteudos', {
    method: 'POST',
    body: JSON.stringify(obj)
  });
  if(res && res.status === 'success'){
    showToastA('Conteúdo salvo! ✨');
    closeModal('modal-cont');
    renderConteudoTable(obj.categoria);
  }
}'''

if old_saveCont in content:
    content = content.replace(old_saveCont, new_saveCont, 1)
    print('saveConteudo atualizado: OK')
else:
    print('FAIL: saveConteudo não encontrado')

# 8. Atualizar renderDashboard para mostrar progresso de vídeos nas atividades
old_acts = '''  const acts = logs.slice(0, 10).map(l => {
    const date = new Date(l.criado_em);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    let tm = 'Agora';
    if (diffMins > 0 && diffMins < 60) tm = `${diffMins}m atrás`;
    else if (diffHours > 0 && diffHours < 24) tm = `${diffHours}h atrás`;
    else if (diffDays > 0) tm = `${diffDays}d atrás`;
    
    return {
      t: `${l.user_nome}: ${l.acao}${l.detalhes ? ' - ' + l.detalhes : ''}`,
      tm: tm
    };
  });
  
  document.getElementById('dash-activity').innerHTML=acts.map(a=>`
    <div class="act-item"><div class="act-dot"></div><div><div class="act-txt">${a.t||'—'}</div><div class="act-time">${a.tm}</div></div></div>
  `).join('');
}'''

new_acts = '''  const acts = logs.slice(0, 15).map(l => {
    const date = new Date(l.criado_em);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    let tm = 'Agora';
    if (diffMins > 0 && diffMins < 60) tm = `${diffMins}m atrás`;
    else if (diffHours > 0 && diffHours < 24) tm = `${diffHours}h atrás`;
    else if (diffDays > 0) tm = `${diffDays}d atrás`;
    
    // Ícone por tipo de ação
    let icon = '📌';
    const acao = l.acao || '';
    if(acao.includes('vídeo') || acao.includes('Assistiu')) icon = '🎬';
    else if(acao.includes('diário') || acao.includes('Diário')) icon = '📖';
    else if(acao.includes('Acessou')) icon = '📱';
    else if(acao.includes('cadastrada')) icon = '🤰';
    
    const detalhe = l.detalhes ? `<span style="color:var(--rose);font-size:11px;"> — ${l.detalhes}</span>` : '';
    return {
      t: `<strong>${l.user_nome}</strong>: ${l.acao}${detalhe}`,
      tm: tm,
      icon: icon
    };
  });
  
  document.getElementById('dash-activity').innerHTML = acts.length > 0 ? acts.map(a=>`
    <div class="act-item">
      <div class="act-dot" style="font-size:14px;background:none;width:20px;height:20px;display:flex;align-items:center;justify-content:center;">${a.icon}</div>
      <div style="flex:1;"><div class="act-txt">${a.t||'—'}</div><div class="act-time">${a.tm}</div></div>
    </div>
  `).join('') : '<div style="padding:16px;text-align:center;color:var(--lite);font-size:13px;">Nenhuma atividade ainda.</div>';
  
  // Progresso de vídeos por doulanda
  const progresso = await apiFetch('/api/admin/progresso') || [];
  const users2 = users.filter(u => u.ativo);
  const progressoMap = {};
  progresso.forEach(p => {
    if(!progressoMap[p.user_id]) progressoMap[p.user_id] = { assistidos: 0, nome: p.user_nome };
    if(p.assistido) progressoMap[p.user_id].assistidos++;
  });
  const totalVideos = cont.filter(c=>c.categoria==='video').length;
  const progressoHtml = users2.slice(0,5).map(u => {
    const p = progressoMap[u.id] || { assistidos: 0 };
    const pct = totalVideos > 0 ? Math.round((p.assistidos / totalVideos) * 100) : 0;
    return `<div style="margin-bottom:10px;">
      <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;">
        <span style="font-weight:500;">${u.nome}</span>
        <span style="color:var(--lite);">${p.assistidos}/${totalVideos} vídeos · ${pct}%</span>
      </div>
      <div style="height:6px;background:#f0e8e4;border-radius:3px;overflow:hidden;">
        <div style="height:100%;width:${pct}%;background:linear-gradient(90deg,var(--rose),#c9907a);border-radius:3px;transition:width .4s;"></div>
      </div>
    </div>`;
  }).join('');
  const progEl = document.getElementById('dash-progresso');
  if(progEl) progEl.innerHTML = progressoHtml || '<div style="color:var(--lite);font-size:13px;">Nenhuma doulanda ativa.</div>';
}'''

if old_acts in content:
    content = content.replace(old_acts, new_acts, 1)
    print('renderDashboard atualizado: OK')
else:
    print('FAIL: renderDashboard não encontrado')

# 9. Adicionar card de progresso no dashboard HTML
old_dash_recent = '        <div class="table-card"><div class="tc-hdr"><h3>Doulandas Recentes</h3></div><div id="dash-recent"></div></div>'
new_dash_recent = '''        <div class="table-card"><div class="tc-hdr"><h3>Doulandas Recentes</h3></div><div id="dash-recent"></div></div>
        <div class="table-card" style="margin-top:16px;"><div class="tc-hdr"><h3>📊 Progresso no Mini Curso</h3></div><div id="dash-progresso" style="padding:12px 16px;"></div></div>'''

if old_dash_recent in content:
    content = content.replace(old_dash_recent, new_dash_recent, 1)
    print('Card de progresso no dashboard: OK')
else:
    print('FAIL: dash-recent não encontrado')

with open('www/admin.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('admin.html salvo.')
