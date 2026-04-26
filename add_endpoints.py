"""Script para adicionar endpoints de mini curso ao app.py"""
import re

with open('nalin_api/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Corrigir toggle_conteudo (estava atualizando users em vez de conteudos)
old_toggle = """@app.route('/api/conteudos/<int:cont_id>/toggle', methods=['POST'])
def toggle_conteudo(cont_id):
    db = get_db()
    db.execute('UPDATE users SET ativo = NOT ativo WHERE id = ?', (cont_id,))
    db.commit()
    return jsonify({"status": "success"})"""

new_toggle = """@app.route('/api/conteudos/<int:cont_id>/toggle', methods=['POST'])
def toggle_conteudo(cont_id):
    db = get_db()
    db.execute('UPDATE conteudos SET ativo = NOT ativo WHERE id = ?', (cont_id,))
    db.commit()
    return jsonify({"status": "success"})"""

if old_toggle in content:
    content = content.replace(old_toggle, new_toggle, 1)
    print('toggle_conteudo corrigido: OK')
else:
    print('WARN: toggle_conteudo já corrigido ou padrão diferente')

# 2. Corrigir save_conteudo para incluir secao_id e ordem
old_save = """@app.route('/api/conteudos', methods=['POST'])
def save_conteudo():
    data = request.json
    db = get_db()
    if 'id' in data and data['id']:
        db.execute('UPDATE conteudos SET titulo=?, categoria=?, subcategoria=?, emoji=?, descricao=?, duracao=?, paginas=?, url=?, cor=? WHERE id=?',
                   (data['titulo'], data['categoria'], data['subcategoria'], data['emoji'], data['descricao'], data['duracao'], data['paginas'], data['url'], data['cor'], data['id']))
    else:
        db.execute('INSERT INTO conteudos (titulo, categoria, subcategoria, emoji, descricao, duracao, paginas, url, cor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (data['titulo'], data['categoria'], data['subcategoria'], data['emoji'], data['descricao'], data['duracao'], data['paginas'], data['url'], data['cor']))
    db.commit()
    return jsonify({"status": "success"})"""

new_save = """@app.route('/api/conteudos', methods=['POST'])
def save_conteudo():
    data = request.json
    db = get_db()
    secao_id = data.get('secao_id') or None
    ordem = data.get('ordem', 0)
    if 'id' in data and data['id']:
        db.execute('UPDATE conteudos SET titulo=?, categoria=?, subcategoria=?, emoji=?, descricao=?, duracao=?, paginas=?, url=?, cor=?, secao_id=?, ordem=? WHERE id=?',
                   (data['titulo'], data['categoria'], data['subcategoria'], data['emoji'], data['descricao'], data['duracao'], data['paginas'], data['url'], data['cor'], secao_id, ordem, data['id']))
    else:
        db.execute('INSERT INTO conteudos (titulo, categoria, subcategoria, emoji, descricao, duracao, paginas, url, cor, secao_id, ordem) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (data['titulo'], data['categoria'], data['subcategoria'], data['emoji'], data['descricao'], data['duracao'], data['paginas'], data['url'], data['cor'], secao_id, ordem))
    db.commit()
    return jsonify({"status": "success"})"""

if old_save in content:
    content = content.replace(old_save, new_save, 1)
    print('save_conteudo atualizado: OK')
else:
    print('WARN: save_conteudo padrão não encontrado')

# 3. Corrigir list_conteudos para ordenar por secao e ordem
old_list = """@app.route('/api/conteudos', methods=['GET'])
def list_conteudos():
    db = get_db()
    try:
        cont = db.execute('SELECT * FROM conteudos WHERE ativo = 1 ORDER BY criado_em DESC').fetchall()
        return jsonify([dict(c) for c in cont])
    except sqlite3.OperationalError:
        return jsonify([])"""

new_list = """@app.route('/api/conteudos', methods=['GET'])
def list_conteudos():
    db = get_db()
    try:
        cont = db.execute('SELECT * FROM conteudos WHERE ativo = 1 ORDER BY secao_id ASC, ordem ASC, criado_em ASC').fetchall()
        return jsonify([dict(c) for c in cont])
    except sqlite3.OperationalError:
        return jsonify([])"""

if old_list in content:
    content = content.replace(old_list, new_list, 1)
    print('list_conteudos atualizado: OK')
else:
    print('WARN: list_conteudos padrão não encontrado')

# 4. Adicionar endpoints de seções e progresso antes do if __name__ == '__main__'
new_endpoints = """
# ── SEÇÕES DO MINI CURSO ──────────────────────────────────────────────────────
@app.route('/api/admin/secoes', methods=['GET', 'POST', 'OPTIONS'])
def admin_secoes():
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    if request.method == 'GET':
        secoes = db.execute('SELECT * FROM curso_secoes ORDER BY ordem ASC, id ASC').fetchall()
        result = []
        for s in secoes:
            s_dict = dict(s)
            videos = db.execute(
                'SELECT * FROM conteudos WHERE secao_id = ? AND ativo = 1 ORDER BY ordem ASC, criado_em ASC',
                (s['id'],)
            ).fetchall()
            s_dict['videos'] = [dict(v) for v in videos]
            result.append(s_dict)
        return jsonify(result)
    else:
        data = request.json or {}
        titulo = data.get('titulo', '').strip()
        if not titulo:
            return jsonify({'status': 'error', 'message': 'Título obrigatório'}), 400
        if data.get('id'):
            db.execute('UPDATE curso_secoes SET titulo=?, descricao=?, ordem=?, ativo=? WHERE id=?',
                       (titulo, data.get('descricao', ''), data.get('ordem', 0), data.get('ativo', 1), data['id']))
        else:
            max_ordem = db.execute('SELECT COALESCE(MAX(ordem), 0) FROM curso_secoes').fetchone()[0]
            db.execute('INSERT INTO curso_secoes (titulo, descricao, ordem) VALUES (?, ?, ?)',
                       (titulo, data.get('descricao', ''), max_ordem + 1))
        db.commit()
        return jsonify({'status': 'success'})

@app.route('/api/admin/secoes/<int:secao_id>', methods=['DELETE', 'OPTIONS'])
def admin_delete_secao(secao_id):
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    # Desvincula os vídeos da seção (não exclui os vídeos)
    db.execute('UPDATE conteudos SET secao_id = NULL WHERE secao_id = ?', (secao_id,))
    db.execute('DELETE FROM curso_secoes WHERE id = ?', (secao_id,))
    db.commit()
    return jsonify({'status': 'success'})

@app.route('/api/secoes', methods=['GET', 'OPTIONS'])
def secoes_publicas():
    # Endpoint publico para o app das clientes buscar as secoes com videos
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    try:
        secoes = db.execute('SELECT * FROM curso_secoes WHERE ativo = 1 ORDER BY ordem ASC, id ASC').fetchall()
        result = []
        for s in secoes:
            s_dict = dict(s)
            videos = db.execute(
                'SELECT * FROM conteudos WHERE secao_id = ? AND ativo = 1 AND categoria = "video" ORDER BY ordem ASC, criado_em ASC',
                (s['id'],)
            ).fetchall()
            s_dict['videos'] = [dict(v) for v in videos]
            result.append(s_dict)
        return jsonify(result)
    except Exception as e:
        return jsonify([])

# ── PROGRESSO DE VÍDEOS ───────────────────────────────────────────────────────
@app.route('/api/progresso', methods=['GET', 'POST', 'OPTIONS'])
def video_progresso_endpoint():
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify([])
        rows = db.execute(
            'SELECT * FROM video_progresso WHERE user_id = ?', (user_id,)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    else:
        data = request.json or {}
        user_id = data.get('user_id')
        conteudo_id = data.get('conteudo_id')
        assistido = data.get('assistido', 1)
        percentual = data.get('percentual', 100)
        if not user_id or not conteudo_id:
            return jsonify({'status': 'error', 'message': 'user_id e conteudo_id obrigatórios'}), 400
        db.execute(
            'INSERT OR REPLACE INTO video_progresso (user_id, conteudo_id, assistido, percentual, atualizado_em) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)',
            (user_id, conteudo_id, assistido, percentual)
        )
        db.commit()
        # Registra no log de atividade
        cont = db.execute('SELECT titulo FROM conteudos WHERE id = ?', (conteudo_id,)).fetchone()
        titulo = cont['titulo'] if cont else f'Vídeo #{conteudo_id}'
        log_activity(user_id, f'Assistiu ao vídeo', titulo)
        return jsonify({'status': 'success'})

@app.route('/api/admin/progresso', methods=['GET', 'OPTIONS'])
def admin_progresso():
    # Retorna o progresso de todas as usuarias em todos os videos
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    try:
        rows = db.execute('''
            SELECT vp.user_id, u.nome as user_nome, vp.conteudo_id, c.titulo as video_titulo,
                   vp.assistido, vp.percentual, vp.atualizado_em
            FROM video_progresso vp
            JOIN users u ON u.id = vp.user_id
            JOIN conteudos c ON c.id = vp.conteudo_id
            ORDER BY vp.atualizado_em DESC
        ''').fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify([])

@app.route('/api/admin/progresso/<int:user_id>', methods=['GET', 'OPTIONS'])
def admin_progresso_usuario(user_id):
    # Retorna o progresso de uma usuaria especifica
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    try:
        total_videos = db.execute(
            "SELECT COUNT(*) FROM conteudos WHERE categoria = 'video' AND ativo = 1"
        ).fetchone()[0]
        assistidos = db.execute(
            'SELECT COUNT(*) FROM video_progresso WHERE user_id = ? AND assistido = 1', (user_id,)
        ).fetchone()[0]
        percentual_geral = round((assistidos / total_videos * 100) if total_videos > 0 else 0)
        rows = db.execute('''
            SELECT vp.conteudo_id, c.titulo, c.secao_id, vp.assistido, vp.percentual, vp.atualizado_em
            FROM video_progresso vp
            JOIN conteudos c ON c.id = vp.conteudo_id
            WHERE vp.user_id = ?
            ORDER BY vp.atualizado_em DESC
        ''', (user_id,)).fetchall()
        return jsonify({
            'total_videos': total_videos,
            'assistidos': assistidos,
            'percentual_geral': percentual_geral,
            'detalhes': [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({'total_videos': 0, 'assistidos': 0, 'percentual_geral': 0, 'detalhes': []})

"""

if "if __name__ == '__main__':" in content:
    content = content.replace("if __name__ == '__main__':", new_endpoints + "if __name__ == '__main__':", 1)
    print('Novos endpoints adicionados: OK')
else:
    print('FAIL: marcador __main__ não encontrado')

with open('nalin_api/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('app.py salvo.')
