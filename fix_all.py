#!/usr/bin/env python3
"""Script para aplicar todas as correções no index.html"""

with open('/home/ubuntu/app-doula/www/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ════════════════════════════════════════════════════════
# FIX 1: Plano de parto — adicionar abas 3 e 4
# ════════════════════════════════════════════════════════
OLD_PLANO = '''      <div class="mfield"><label>1. DURANTE O TRABALHO DE PARTO</label><textarea id="pp-durante" style="width:100%;height:100px;padding:8px;border:1px solid var(--rose-pale);border-radius:8px;resize:vertical;"></textarea></div>
      <div class="mfield"><label>2. EM CASO DE INDUÇÃO</label><textarea id="pp-inducao" style="width:100%;height:100px;padding:8px;border:1px solid var(--rose-pale);border-radius:8px;resize:vertical;"></textarea></div>
      
      <div id="pp-msg" style="font-size:13px;min-height:16px;color:var(--ok);margin-top:8px;text-align:center;"></div>'''

NEW_PLANO = '''      <!-- Abas do Plano de Parto -->
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin:12px 0 4px;">
        <button class="pp-tab active" onclick="switchPPTab(1,this)" style="flex:1;min-width:120px;padding:8px 6px;border:none;border-radius:8px;background:var(--rose);color:white;font-size:12px;font-weight:600;cursor:pointer;">1. Trabalho de Parto</button>
        <button class="pp-tab" onclick="switchPPTab(2,this)" style="flex:1;min-width:120px;padding:8px 6px;border:none;border-radius:8px;background:var(--rose-pale);color:var(--dark);font-size:12px;font-weight:600;cursor:pointer;">2. Indução</button>
        <button class="pp-tab" onclick="switchPPTab(3,this)" style="flex:1;min-width:120px;padding:8px 6px;border:none;border-radius:8px;background:var(--rose-pale);color:var(--dark);font-size:12px;font-weight:600;cursor:pointer;">3. Cesárea</button>
        <button class="pp-tab" onclick="switchPPTab(4,this)" style="flex:1;min-width:120px;padding:8px 6px;border:none;border-radius:8px;background:var(--rose-pale);color:var(--dark);font-size:12px;font-weight:600;cursor:pointer;">4. Recém-Nascido</button>
      </div>
      <div id="pp-tab-1" class="pp-tab-content">
        <div class="mfield"><label>1. DURANTE O TRABALHO DE PARTO</label><textarea id="pp-durante" placeholder="Ex: Quero liberdade de movimento, banho de chuveiro, bola de pilates..." style="width:100%;height:120px;padding:8px;border:1px solid var(--rose-pale);border-radius:8px;resize:vertical;"></textarea></div>
      </div>
      <div id="pp-tab-2" class="pp-tab-content" style="display:none;">
        <div class="mfield"><label>2. EM CASO DE INDUÇÃO</label><textarea id="pp-inducao" placeholder="Ex: Prefiro métodos naturais antes de medicamentosos. Gostaria de ser informada sobre cada etapa..." style="width:100%;height:120px;padding:8px;border:1px solid var(--rose-pale);border-radius:8px;resize:vertical;"></textarea></div>
      </div>
      <div id="pp-tab-3" class="pp-tab-content" style="display:none;">
        <div class="mfield"><label>3. EM CASO DE CESÁREA</label><textarea id="pp-cesarea" placeholder="Ex: Gostaria de cesárea humanizada, contato pele a pele imediato, presença do acompanhante, música ambiente..." style="width:100%;height:120px;padding:8px;border:1px solid var(--rose-pale);border-radius:8px;resize:vertical;"></textarea></div>
      </div>
      <div id="pp-tab-4" class="pp-tab-content" style="display:none;">
        <div class="mfield"><label>4. ASSISTÊNCIA AO RECÉM-NASCIDO</label><textarea id="pp-recem-nascido" placeholder="Ex: Clampeamento tardio do cordão, contato pele a pele imediato, não oferecer chupeta ou mamadeira, amamentação na primeira hora..." style="width:100%;height:120px;padding:8px;border:1px solid var(--rose-pale);border-radius:8px;resize:vertical;"></textarea></div>
      </div>
      
      <div id="pp-msg" style="font-size:13px;min-height:16px;color:var(--ok);margin-top:8px;text-align:center;"></div>'''

if OLD_PLANO in content:
    content = content.replace(OLD_PLANO, NEW_PLANO)
    print("✅ FIX 1: Abas do plano de parto adicionadas")
else:
    print("❌ FIX 1: Bloco do plano de parto não encontrado")

# ════════════════════════════════════════════════════════
# FIX 2: Adicionar função switchPPTab e atualizar savePlanoParto
# ════════════════════════════════════════════════════════
OLD_SAVE_PP = 'async function savePlanoParto(){'
NEW_SAVE_PP = '''function switchPPTab(n, el) {
  document.querySelectorAll('.pp-tab-content').forEach(t => t.style.display = 'none');
  document.querySelectorAll('.pp-tab').forEach(b => {
    b.style.background = 'var(--rose-pale)';
    b.style.color = 'var(--dark)';
  });
  document.getElementById('pp-tab-' + n).style.display = 'block';
  el.style.background = 'var(--rose)';
  el.style.color = 'white';
}
async function savePlanoParto(){'''

if OLD_SAVE_PP in content:
    content = content.replace(OLD_SAVE_PP, NEW_SAVE_PP, 1)
    print("✅ FIX 2: Função switchPPTab adicionada")
else:
    print("❌ FIX 2: savePlanoParto não encontrado")

# Atualizar o savePlanoParto para incluir os novos campos
OLD_SAVE_BODY = "const pp={nome:document.getElementById('pp-nome').value.trim(),acomp:document.getElementById('pp-acomp').value.trim(),relacionamento:[...document.querySelectorAll('input[name=\"pp-rel\"]:checked')].map(x=>x.value),durante:document.getElementById('pp-durante').value.trim(),inducao:document.getElementById('pp-inducao').value.trim()};"
NEW_SAVE_BODY = "const pp={nome:document.getElementById('pp-nome').value.trim(),acomp:document.getElementById('pp-acomp').value.trim(),relacionamento:[...document.querySelectorAll('input[name=\"pp-rel\"]:checked')].map(x=>x.value),durante:document.getElementById('pp-durante').value.trim(),inducao:document.getElementById('pp-inducao').value.trim(),cesarea:document.getElementById('pp-cesarea').value.trim(),recem_nascido:document.getElementById('pp-recem-nascido').value.trim()};"

if OLD_SAVE_BODY in content:
    content = content.replace(OLD_SAVE_BODY, NEW_SAVE_BODY, 1)
    print("✅ FIX 2b: savePlanoParto atualizado com novos campos")
else:
    print("⚠️  FIX 2b: corpo do savePlanoParto não encontrado (pode já estar atualizado)")

# Atualizar loadPlanejamento para preencher os novos campos
OLD_LOAD_PP = "if(pp.durante)document.getElementById('pp-durante').value=pp.durante;"
NEW_LOAD_PP = """if(pp.durante)document.getElementById('pp-durante').value=pp.durante;
      if(pp.inducao)document.getElementById('pp-inducao').value=pp.inducao;
      if(pp.cesarea)document.getElementById('pp-cesarea').value=pp.cesarea;
      if(pp.recem_nascido)document.getElementById('pp-recem-nascido').value=pp.recem_nascido;"""

if OLD_LOAD_PP in content:
    # Remover duplicatas que podem existir
    OLD_LOAD_DUP = """if(pp.durante)document.getElementById('pp-durante').value=pp.durante;
      if(pp.inducao)document.getElementById('pp-inducao').value=pp.inducao;"""
    if OLD_LOAD_DUP in content:
        content = content.replace(OLD_LOAD_DUP, NEW_LOAD_PP, 1)
        print("✅ FIX 2c: loadPlanejamento atualizado (substituindo bloco existente)")
    else:
        content = content.replace(OLD_LOAD_PP, NEW_LOAD_PP, 1)
        print("✅ FIX 2c: loadPlanejamento atualizado com novos campos")
else:
    print("⚠️  FIX 2c: loadPlanejamento não encontrado com padrão esperado")

# ════════════════════════════════════════════════════════
# FIX 3: Botão admin — exigir login antes de redirecionar
# ════════════════════════════════════════════════════════
OLD_ADMIN_BTN = '''<button class="btn-rose" style="background:var(--dark);margin-top:0;" onclick="window.location.href='admin.html'">Acesso Administrador 🔐</button>'''
NEW_ADMIN_BTN = '''<button class="btn-rose" style="background:var(--dark);margin-top:0;" onclick="abrirLoginAdmin()">Acesso Administrador 🔐</button>

<!-- Modal de login admin -->
<div class="modal-overlay" id="modal-admin-login" style="display:none;z-index:9999;">
  <div class="modal" style="max-width:360px;">
    <div class="modal-hdr"><h3>Acesso Administrativo</h3><button class="modal-close" onclick="closeModal('modal-admin-login')">✕</button></div>
    <div class="modal-body" style="padding:20px;">
      <div class="mfield" style="margin-bottom:14px;">
        <label style="font-size:12px;color:var(--mid);text-transform:uppercase;letter-spacing:1px;">Usuário</label>
        <input type="text" id="admin-login-user" placeholder="admin" style="width:100%;padding:10px;border:1px solid var(--rose-pale);border-radius:8px;margin-top:4px;">
      </div>
      <div class="mfield" style="margin-bottom:6px;">
        <label style="font-size:12px;color:var(--mid);text-transform:uppercase;letter-spacing:1px;">Senha</label>
        <input type="password" id="admin-login-pass" placeholder="••••••••" style="width:100%;padding:10px;border:1px solid var(--rose-pale);border-radius:8px;margin-top:4px;" onkeydown="if(event.key==='Enter')confirmarLoginAdmin()">
      </div>
      <div id="admin-login-err" style="font-size:12px;color:var(--err);min-height:16px;margin-bottom:10px;"></div>
    </div>
    <div class="modal-footer" style="display:flex;gap:10px;">
      <button class="btn-full btn-cancel" onclick="closeModal('modal-admin-login')" style="flex:1;">Cancelar</button>
      <button class="btn-full btn-save" onclick="confirmarLoginAdmin()" style="flex:1;">Entrar</button>
    </div>
  </div>
</div>'''

if OLD_ADMIN_BTN in content:
    content = content.replace(OLD_ADMIN_BTN, NEW_ADMIN_BTN)
    print("✅ FIX 3: Botão admin com modal de login")
else:
    print("❌ FIX 3: Botão admin não encontrado")

# Adicionar funções abrirLoginAdmin e confirmarLoginAdmin
OLD_FUNC_ANCHOR = 'function switchPPTab(n, el) {'
NEW_FUNC_ANCHOR = '''function abrirLoginAdmin() {
  document.getElementById('admin-login-user').value = '';
  document.getElementById('admin-login-pass').value = '';
  document.getElementById('admin-login-err').textContent = '';
  document.getElementById('modal-admin-login').style.display = 'flex';
}
async function confirmarLoginAdmin() {
  const user = document.getElementById('admin-login-user').value.trim();
  const pass = document.getElementById('admin-login-pass').value.trim();
  if (!user || !pass) {
    document.getElementById('admin-login-err').textContent = 'Preencha usuário e senha.';
    return;
  }
  try {
    const res = await apiFetch('/api/admin/login', { method: 'POST', body: JSON.stringify({ usuario: user, senha: pass }) });
    if (res && res.ok) {
      closeModal('modal-admin-login');
      window.location.href = 'admin.html';
    } else {
      document.getElementById('admin-login-err').textContent = res?.erro || 'Usuário ou senha incorretos.';
    }
  } catch(e) {
    document.getElementById('admin-login-err').textContent = 'Erro ao conectar com o servidor.';
  }
}
function switchPPTab(n, el) {'''

if OLD_FUNC_ANCHOR in content:
    content = content.replace(OLD_FUNC_ANCHOR, NEW_FUNC_ANCHOR, 1)
    print("✅ FIX 3b: Funções de login admin adicionadas")
else:
    print("❌ FIX 3b: Âncora para funções admin não encontrada")

# ════════════════════════════════════════════════════════
# FIX 4: Ebooks — corrigir abertura (usar Capacitor Browser ou window.open)
# ════════════════════════════════════════════════════════
OLD_OPEN_CONT = "function openConteudo(url){if(url&&url!=='#')window.open(url,'_blank');}"
NEW_OPEN_CONT = """function openConteudo(url){
  if(!url||url==='#'){showToast('Arquivo não disponível ainda.');return;}
  // Tenta usar Capacitor Browser plugin (APK), senão usa window.open
  if(window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Browser){
    window.Capacitor.Plugins.Browser.open({url: url});
  } else {
    window.open(url,'_blank');
  }
}"""

if OLD_OPEN_CONT in content:
    content = content.replace(OLD_OPEN_CONT, NEW_OPEN_CONT)
    print("✅ FIX 4: openConteudo corrigido para ebooks")
else:
    print("❌ FIX 4: openConteudo não encontrado")

# ════════════════════════════════════════════════════════
# FIX 5: Jornada de gestação — corrigir para mostrar TODAS as semanas
# ════════════════════════════════════════════════════════
OLD_RENDER_GEST = '''  for(let w=s;w<=e;w+=2){
    const wd=weeklyInfo[w]||{t:`Semana ${w}`,d:'Desenvolvimento contínuo.',e:'🌱'};
    const isCur=w===currentUser?.semanas||(w+1===currentUser?.semanas);'''
NEW_RENDER_GEST = '''  for(let w=s;w<=e;w++){
    const wd=weeklyInfo[w]||{t:`Semana ${w}`,d:'Desenvolvimento contínuo.',e:'🌱'};
    const isCur=w===currentUser?.semanas;'''

if OLD_RENDER_GEST in content:
    content = content.replace(OLD_RENDER_GEST, NEW_RENDER_GEST)
    print("✅ FIX 5a: Loop de semanas corrigido (w+=1 em vez de w+=2)")
else:
    print("❌ FIX 5a: Loop de semanas não encontrado")

# Expandir o weeklyInfo com TODAS as semanas
OLD_WEEKLY = "const weeklyInfo={1:{t:'Fertilização',d:'O milagre começa.',e:'✨'},4:{t:'Formação',d:'Coração começa a se formar.',e:'💓'},6:{t:'Batimentos',d:'Primeiro batimento detectável!',e:'💗'},8:{t:'Órgãos',d:'Cérebro e coração em desenvolvimento.',e:'🫀'},10:{t:'Reflexos',d:'Bebê pode abrir e fechar os dedos.',e:'🤏'},12:{t:'Fim do 1º Trim.',d:'Risco de aborto reduz significativamente.',e:'🎉'},14:{t:'2º Trimestre',d:'Fase dourada! Enjoos diminuem.',e:'☀️'},16:{t:'Sexo do Bebê',d:'Possível descobrir na ultrassom!',e:'💕'},18:{t:'Primeiros Chutes',d:'Você começa a sentir os movimentos!',e:'🥊'},20:{t:'Metade da gestação',d:'Bebê ouve sons e sua voz.',e:'🎵'},22:{t:'Sobrevivência',d:'Bebê viável fora do útero com suporte.',e:'💪'},24:{t:'Audição',d:'Bebê ouve claramente você!',e:'👂'},26:{t:'Olhos Abrem',d:'Bebê já abre e fecha os olhos.',e:'👁️'},28:{t:'3º Trimestre',d:'Reta final! Bebê ganha peso.',e:'🚀'},30:{t:'Posição',d:'Bebê assume posição cefálica.',e:'🔄'},32:{t:'Sono REM',d:'Bebê tem sono REM e pode sonhar!',e:'💭'},34:{t:'Pulmões',d:'Pulmões quase completamente desenvolvidos.',e:'🫁'},36:{t:'Quase Pronto',d:'Bebê está desenvolvido.',e:'⏰'},38:{t:'A Termo',d:'Pronto para nascer a qualquer momento!',e:'🌟'},40:{t:'Parto Previsto',d:'Seu bebê está pronto para o mundo!',e:'👶'}};"
NEW_WEEKLY = """const weeklyInfo={
  // 1º TRIMESTRE (semanas 1–13)
  1:{t:'Fertilização',d:'O óvulo foi fertilizado e o embrião começa a se implantar no útero. Um novo ser está se formando!',e:'✨'},
  2:{t:'Implantação',d:'O embrião se fixa na parede do útero. Podem aparecer pequenos sangramentos de implantação.',e:'🌱'},
  3:{t:'Embrião Formado',d:'O embrião já tem cerca de 2mm. O coração primitivo começa a se organizar.',e:'💫'},
  4:{t:'Coração se Forma',d:'O coração começa a se formar e dividir em câmaras. O tubo neural está se fechando.',e:'💓'},
  5:{t:'Batimentos Iniciam',d:'O coração começa a bater! O embrião tem cerca de 5mm e parece um grão de arroz.',e:'💗'},
  6:{t:'Batimentos Detectáveis',d:'O batimento cardíaco pode ser visto no ultrassom! Braços e pernas começam a surgir.',e:'🔴'},
  7:{t:'Rosto se Forma',d:'Olhos, narinas e boca começam a se formar. O bebê tem cerca de 1,3cm.',e:'👶'},
  8:{t:'Órgãos em Formação',d:'Todos os órgãos principais estão se desenvolvendo. Dedos das mãos começam a aparecer.',e:'🫀'},
  9:{t:'Movimentos Iniciais',d:'O bebê já se mexe, mas você ainda não sente. Tem cerca de 2,5cm e parece um morango.',e:'🍓'},
  10:{t:'Reflexos',d:'O bebê pode abrir e fechar os dedos. Os órgãos genitais estão se formando.',e:'🤏'},
  11:{t:'Bebê Ativo',d:'O bebê chuta, engole e soluça. Unhas e cabelos começam a crescer.',e:'🌟'},
  12:{t:'Fim do 1º Trimestre',d:'Risco de aborto reduz significativamente! O bebê tem cerca de 6cm e já parece um bebê.',e:'🎉'},
  13:{t:'Transição',d:'O bebê pode sugar o polegar! Impressões digitais únicas já estão se formando.',e:'👍'},
  // 2º TRIMESTRE (semanas 14–26)
  14:{t:'2º Trimestre',d:'Fase dourada! Enjoos costumam diminuir. O bebê faz expressões faciais.',e:'☀️'},
  15:{t:'Ossos Endurecem',d:'Os ossos estão ficando mais rígidos. O bebê já pode ouvir sons do seu corpo.',e:'🦴'},
  16:{t:'Sexo do Bebê',d:'Possível descobrir o sexo na ultrassom! O bebê tem cerca de 11cm e pesa ~100g.',e:'💕'},
  17:{t:'Gordura Corporal',d:'O bebê começa a acumular gordura para regular a temperatura. Movimentos mais fortes.',e:'🧈'},
  18:{t:'Primeiros Chutes',d:'Você começa a sentir os movimentos! O bebê ouve sons externos como música.',e:'🥊'},
  19:{t:'Vernix Caseosa',d:'Uma camada protetora cobre a pele do bebê. O útero cresce bastante esta semana.',e:'🛡️'},
  20:{t:'Metade da Gestação',d:'Parabéns, metade do caminho! O bebê tem cerca de 20cm e pesa ~300g.',e:'🎵'},
  21:{t:'Movimentos Fortes',d:'Os chutes ficam mais fortes e frequentes. O bebê tem sobrancelhas e cílios.',e:'💪'},
  22:{t:'Sobrevivência',d:'O bebê seria viável fora do útero com suporte médico intensivo. Pesa cerca de 430g.',e:'🏥'},
  23:{t:'Audição Aguçada',d:'O bebê reconhece a sua voz! Reage a sons altos com movimentos.',e:'🎶'},
  24:{t:'Audição Clara',d:'O bebê ouve claramente você! Converse, cante e leia histórias para ele.',e:'👂'},
  25:{t:'Resposta a Luz',d:'O bebê reage à luz que passa pelo abdômen. Pulmões continuam amadurecendo.',e:'💡'},
  26:{t:'Olhos Abrem',d:'O bebê já abre e fecha os olhos! Tem cerca de 35cm e pesa ~760g.',e:'👁️'},
  // 3º TRIMESTRE (semanas 27–42)
  27:{t:'Início do 3º Trim.',d:'O cérebro se desenvolve rapidamente. O bebê tem períodos de sono e vigília definidos.',e:'🧠'},
  28:{t:'3º Trimestre',d:'Reta final! O bebê ganha peso rapidamente. Pulmões quase prontos para respirar.',e:'🚀'},
  29:{t:'Ossos Completos',d:'Os ossos estão totalmente formados, mas ainda flexíveis. O bebê pesa cerca de 1,2kg.',e:'💎'},
  30:{t:'Posição Cefálica',d:'O bebê começa a se posicionar de cabeça para baixo. Pode sentir soluços dele!',e:'🔄'},
  31:{t:'Ganho de Peso',d:'O bebê ganha cerca de 200g por semana agora. Movimentos podem ser visíveis pelo barrigão.',e:'⚖️'},
  32:{t:'Sono REM',d:'O bebê tem sono REM e pode sonhar! Pulmões quase completamente desenvolvidos.',e:'💭'},
  33:{t:'Imunidade',d:'O bebê recebe anticorpos de você para se proteger após o nascimento. Pesa cerca de 2kg.',e:'🛡️'},
  34:{t:'Pulmões Maduros',d:'Os pulmões estão quase prontos! Se nascer agora, terá boas chances sem suporte intensivo.',e:'🫁'},
  35:{t:'Gordura Final',d:'O bebê acumula gordura nas bochechas e no corpo. Fica menos espaço para se mexer.',e:'🍑'},
  36:{t:'Quase Pronto',d:'O bebê está praticamente desenvolvido. A cabeça pode começar a se encaixar na pelve.',e:'⏰'},
  37:{t:'A Termo Precoce',d:'O bebê é considerado a termo precoce! Pode nascer a qualquer momento com segurança.',e:'🌸'},
  38:{t:'A Termo',d:'Totalmente a termo! O bebê está pronto para nascer. Prepare a bolsa da maternidade!',e:'🌟'},
  39:{t:'Aguardando',d:'Cada dia é um presente! O bebê continua crescendo e se preparando para o grande dia.',e:'⌛'},
  40:{t:'Parto Previsto',d:'Seu bebê está pronto para o mundo! Apenas 5% dos bebês nascem na data prevista — seja paciente.',e:'👶'},
  41:{t:'Pós-Termo',d:'Ainda esperando? Isso é normal! Converse com sua equipe sobre monitoramento.',e:'🌙'},
  42:{t:'Indução',d:'Com 42 semanas, a equipe médica geralmente recomenda a indução do parto.',e:'🏥'}
};"""

if OLD_WEEKLY in content:
    content = content.replace(OLD_WEEKLY, NEW_WEEKLY)
    print("✅ FIX 5b: weeklyInfo expandido com todas as semanas (1-42)")
else:
    print("❌ FIX 5b: weeklyInfo não encontrado")

# ════════════════════════════════════════════════════════
# FIX 6: Layout responsivo do mini curso — corrigir player cortado
# ════════════════════════════════════════════════════════
OLD_CURSO_CSS = """.curso-layout{display:flex;height:calc(100vh - 120px);overflow:hidden;}
.curso-sidebar{width:220px;min-width:180px;background:white;border-right:1px solid var(--rose-pale);overflow-y:auto;flex-shrink:0;}
.curso-main{flex:1;overflow-y:auto;background:#f9f7f5;display:flex;flex-direction:column;}"""

NEW_CURSO_CSS = """.curso-layout{display:flex;height:calc(100vh - 110px);overflow:hidden;}
.curso-sidebar{width:200px;min-width:160px;max-width:220px;background:white;border-right:1px solid var(--rose-pale);overflow-y:auto;flex-shrink:0;}
.curso-main{flex:1;overflow-y:auto;background:#f9f7f5;display:flex;flex-direction:column;min-width:0;}
@media(max-width:480px){
  .curso-layout{flex-direction:column;height:auto;}
  .curso-sidebar{width:100%;max-width:100%;height:220px;border-right:none;border-bottom:1px solid var(--rose-pale);}
  .curso-main{height:auto;}
}"""

if OLD_CURSO_CSS in content:
    content = content.replace(OLD_CURSO_CSS, NEW_CURSO_CSS)
    print("✅ FIX 6: Layout responsivo do mini curso corrigido")
else:
    print("⚠️  FIX 6: CSS do curso não encontrado com padrão exato — tentando alternativa")
    # Tenta encontrar partes do CSS
    if '.curso-layout{display:flex;' in content:
        print("   → .curso-layout encontrado, mas formato diferente")
    else:
        print("   → .curso-layout não encontrado")

# Corrigir o player-area para não cortar
OLD_PLAYER_AREA = """.player-area{flex:1;display:flex;align-items:center;justify-content:center;background:#1a1a1a;min-height:200px;position:relative;cursor:pointer;}"""
NEW_PLAYER_AREA = """.player-area{width:100%;aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;background:#1a1a1a;position:relative;cursor:pointer;flex-shrink:0;}"""

if OLD_PLAYER_AREA in content:
    content = content.replace(OLD_PLAYER_AREA, NEW_PLAYER_AREA)
    print("✅ FIX 6b: player-area com aspect-ratio 16:9")
else:
    print("⚠️  FIX 6b: player-area não encontrado com padrão exato")

with open('/home/ubuntu/app-doula/www/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Script concluído!")
