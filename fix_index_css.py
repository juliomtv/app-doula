with open('www/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start = None
end = None
for i, line in enumerate(lines):
    if '/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 CONTE\u00daD' in line:
        start = i
    if start and '.empty-state .ei{font-size:48px;margin-bottom:12px;}' in line:
        end = i
        break

if start is None or end is None:
    print(f'FAIL: start={start}, end={end}')
else:
    print(f'Bloco CSS encontrado: linhas {start+1} a {end+1}')
    new_css_block = r"""/* ══════════════════════ CONTEÚDO ══════════════════════ */
#conteudo{display:flex;flex-direction:column;height:100vh;overflow:hidden;}
.cont-hdr{background:linear-gradient(135deg,var(--rose-pale),var(--cream));padding:16px 22px 22px;flex-shrink:0;}
.cont-hdr h2{font-family:'Cormorant Garamond',serif;font-size:28px;font-style:italic;color:var(--dark);}
.cont-hdr p{font-size:13px;color:var(--mid);margin-top:3px;}
.tabs{display:flex;gap:8px;margin-top:14px;overflow-x:auto;scrollbar-width:none;}
.tabs::-webkit-scrollbar{display:none;}
.tab{flex-shrink:0;padding:8px 18px;border-radius:50px;border:1.5px solid var(--rose-pale);font-size:13px;font-weight:500;color:var(--mid);cursor:pointer;background:white;transition:all .2s;}
.tab.active{background:var(--rose);color:white;border-color:var(--rose);}
/* ══ LAYOUT DE DOIS PAINÉIS — MINI CURSO ══ */
.curso-layout{display:flex;flex:1;overflow:hidden;min-height:0;}
.curso-sidebar{width:260px;min-width:220px;max-width:300px;background:#faf7f5;border-right:1px solid #f0e8e4;display:flex;flex-direction:column;overflow:hidden;}
.curso-sidebar-inner{flex:1;overflow-y:auto;padding:8px 0;}
.sidebar-progress{padding:12px 14px 8px;border-bottom:1px solid #f0e8e4;flex-shrink:0;}
.sidebar-progress-title{font-size:11px;font-weight:600;color:var(--dark);margin-bottom:6px;}
.sidebar-progress-bar{height:6px;background:#f0e8e4;border-radius:3px;overflow:hidden;}
.sidebar-progress-fill{height:100%;background:linear-gradient(90deg,var(--rose),#c9907a);border-radius:3px;transition:width .5s;}
.sidebar-progress-txt{font-size:10px;color:var(--lite);margin-top:4px;}
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
.sb-video-item{padding:8px 14px 8px 44px;cursor:pointer;display:flex;align-items:center;gap:8px;transition:background .15s;border-left:3px solid transparent;}
.sb-video-item:hover{background:rgba(201,144,122,.08);}
.sb-video-item.active{background:rgba(201,144,122,.15);border-left-color:var(--rose);}
.sb-video-item.assistido-item .sb-vid-title{color:var(--lite);}
.sb-vid-thumb{width:44px;height:28px;border-radius:4px;background:#e8d8d0;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:12px;overflow:hidden;}
.sb-vid-thumb img{width:100%;height:100%;object-fit:cover;}
.sb-vid-info{flex:1;min-width:0;}
.sb-vid-title{font-size:11px;font-weight:500;color:var(--dark);line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.sb-vid-dur{font-size:9px;color:var(--lite);margin-top:1px;}
.sb-vid-check{font-size:12px;color:var(--rose);flex-shrink:0;}
.curso-main{flex:1;display:flex;flex-direction:column;overflow:hidden;background:#fff;}
.player-area{flex-shrink:0;background:#000;position:relative;}
.player-area iframe,.player-area video{width:100%;aspect-ratio:16/9;display:block;border:none;}
.player-placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 20px;background:linear-gradient(135deg,#f5ede8,#e8d8d0);text-align:center;aspect-ratio:16/9;}
.player-placeholder .pp-icon{font-size:48px;margin-bottom:12px;}
.player-placeholder p{font-size:13px;color:var(--mid);line-height:1.5;}
.player-info{padding:14px 16px;border-bottom:1px solid #f0e8e4;flex-shrink:0;overflow-y:auto;}
.player-titulo{font-size:15px;font-weight:600;color:var(--dark);line-height:1.3;}
.player-meta{font-size:11px;color:var(--lite);margin-top:4px;}
.player-check-btn{margin-top:10px;padding:8px 16px;background:var(--rose);color:white;border:none;border-radius:20px;font-size:12px;cursor:pointer;font-weight:500;}
.player-check-btn.done{background:#9ec49e;cursor:default;}
/* Grade para e-books/meditacoes/outros */
.cont-scroll{overflow-y:auto;flex:1;}
.cont-grid{padding:14px 12px;display:grid;grid-template-columns:repeat(2,1fr);gap:10px;}
.ccard{background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px var(--shadow-soft);cursor:pointer;transition:transform .15s;display:flex;flex-direction:column;}
.ccard:active{transform:scale(.96);}
.cthumb{aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;background:var(--rose-pale);}
.cthumb .te{font-size:24px;z-index:1;}
.cthumb img{position:absolute;width:100%;height:100%;object-fit:cover;}
.play-btn{position:absolute;width:28px;height:28px;border-radius:50%;background:rgba(255,255,255,.9);display:flex;align-items:center;justify-content:center;font-size:10px;box-shadow:0 2px 8px rgba(0,0,0,.15);z-index:2;}
.cinfo{padding:8px;flex:1;display:flex;flex-direction:column;}
.ctag{font-size:8px;letter-spacing:0.5px;text-transform:uppercase;color:var(--rose);font-weight:600;margin-bottom:2px;}
.ctitle{font-size:11px;font-weight:500;color:var(--dark);line-height:1.2;flex:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.cmeta{font-size:9px;color:var(--light);margin-top:4px;display:flex;gap:6px;}
.empty-state{text-align:center;padding:48px 22px;color:var(--light);}
.empty-state .ei{font-size:48px;margin-bottom:12px;}
"""
    lines[start:end+1] = [new_css_block]
    with open('www/index.html', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('CSS substituido: OK')
