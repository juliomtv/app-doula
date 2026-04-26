import sqlite3
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
import os
import socket
import subprocess
import threading
import re
import hashlib
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuração de caminhos baseada na localização do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(os.path.dirname(BASE_DIR), 'dados.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')
UPLOAD_FOLDER = os.path.join(os.path.dirname(BASE_DIR), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Criar o diretório de uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# Definição da base_url dinâmica para uso nas rotas
ip_local = get_local_ip()
base_url = f"http://{ip_local}:5000"

# URL pública gerada pelo cloudflared tunnel (preenchida automaticamente ao iniciar)
tunnel_url = None

def start_cloudflared_tunnel():
    """Inicia o cloudflared tunnel em background e captura a URL pública.
    O cloudflared cria um túnel HTTPS gratuito sem necessidade de conta.
    Instale com: winget install Cloudflare.cloudflared (Windows)
                 brew install cloudflared (Mac)
                 sudo apt install cloudflared (Linux/Ubuntu)
    Ou baixe em: https://github.com/cloudflare/cloudflared/releases
    """
    global tunnel_url
    try:
        # Verifica se cloudflared está disponível no PATH
        check = subprocess.run(
            ['cloudflared', '--version'],
            capture_output=True, text=True
        )
        if check.returncode != 0:
            print("[TUNNEL] cloudflared não encontrado no PATH.")
            print("[TUNNEL] Instale em: https://github.com/cloudflare/cloudflared/releases")
            print("[TUNNEL] Sem o tunnel, o app só funciona na mesma rede Wi-Fi.")
            return

        proc = subprocess.Popen(
            ['cloudflared', 'tunnel', '--url', 'http://localhost:5000'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print("[TUNNEL] Iniciando cloudflared tunnel... aguarde alguns segundos.")
        for line in proc.stdout:
            # Captura a URL pública gerada pelo cloudflared
            match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
            if match:
                tunnel_url = match.group(0)
                print(f"\n{'='*60}")
                print(f" 🌍 URL PÚBLICA GERADA COM SUCESSO!")
                print(f" 🔗 {tunnel_url}")
                print(f" 📱 Cole essa URL no app para acessar de qualquer rede")
                print(f"    (5G, Wi-Fi externo, etc.)")
                print(f"{'='*60}\n")
                break
    except FileNotFoundError:
        print("[TUNNEL] cloudflared não encontrado.")
        print("[TUNNEL] Baixe em: https://github.com/cloudflare/cloudflared/releases")
    except Exception as e:
        print(f"[TUNNEL] Erro ao iniciar tunnel: {e}")

# Configuração expandida do CORS para incluir rotas fora de /api/
CORS(app, resources={
    r"/api/*": {"origins": "*", "methods": ["GET", "POST", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type"]},
    r"/versao_app": {"origins": "*", "methods": ["GET", "OPTIONS"], "allow_headers": ["Content-Type"]},
    r"/server-info": {"origins": "*", "methods": ["GET", "OPTIONS"], "allow_headers": ["Content-Type"]},
    r"/api/url-servidor": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]},
    r"/ota/*": {"origins": "*", "methods": ["GET", "OPTIONS"], "allow_headers": ["Content-Type"]}
})

app.add_url_rule("/uploads/<path:filename>", endpoint="uploads", view_func=lambda filename: send_from_directory(app.config["UPLOAD_FOLDER"], filename))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Inicializa o banco de dados usando o schema.sql"""
    with app.app_context():
        db = get_db()
        if os.path.exists(SCHEMA_PATH):
            with open(SCHEMA_PATH, mode='r', encoding='utf-8') as f:
                db.cursor().executescript(f.read())
            db.commit()
            print("Banco de dados inicializado com sucesso.")
        else:
            print(f"Erro: Arquivo {SCHEMA_PATH} não encontrado.")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/status', methods=['GET', 'OPTIONS'])
def status():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({"status": "online", "message": "API Nalin Nazareth rodando localmente"})

@app.route('/server-info', methods=['GET', 'OPTIONS'])
def server_info():
    """Retorna informações do servidor.
    Também retorna url_base_servidor salva pelo admin para novas instalações se configurarem automaticamente.
    """
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    try:
        row = db.execute("SELECT valor FROM config_global WHERE chave = 'url_base_servidor'").fetchone()
        url_base_salva = row['valor'] if row and row['valor'] else None
    except Exception:
        url_base_salva = None
    return jsonify({
        "status": "online",
        "ip_local": ip_local,
        "url_local": f"http://{ip_local}:5000",
        "url_publica": tunnel_url,
        "url_base_servidor": url_base_salva,
        "mensagem": "Use url_publica para acessar de qualquer rede (5G, Wi-Fi externo)"
    })

@app.route('/api/url-servidor', methods=['GET', 'POST', 'OPTIONS'])
def url_servidor():
    """Endpoint público para o app buscar/salvar a URL base do servidor.
    GET  → retorna url_base_servidor e url_publica (sem autenticação, pois o app precisa antes do login)
    POST → salva url_base_servidor (uso do admin)
    """
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    if request.method == 'GET':
        try:
            row = db.execute("SELECT valor FROM config_global WHERE chave = 'url_base_servidor'").fetchone()
            url_base = row['valor'] if row and row['valor'] else None
        except Exception:
            url_base = None
        return jsonify({
            "status": "ok",
            "url_base_servidor": url_base,
            "url_publica": tunnel_url,
            "ip_local": ip_local
        })
    else:
        data = request.json or {}
        nova_url = data.get('url_base_servidor', '').strip()
        if not nova_url:
            return jsonify({"status": "error", "message": "url_base_servidor é obrigatória"}), 400
        try:
            db.execute(
                "INSERT OR REPLACE INTO config_global (chave, valor, descricao, atualizado_em) VALUES ('url_base_servidor', ?, 'URL base do servidor configurada pelo admin', CURRENT_TIMESTAMP)",
                (nova_url,)
            )
            db.commit()
            return jsonify({"status": "success", "url_base_servidor": nova_url})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500


# ════ OTA UPDATE ════
# Caminho do www relativo ao nalin_api
WWW_DIR = os.path.join(os.path.dirname(BASE_DIR), 'www')
VERSION_FILE = os.path.join(WWW_DIR, 'version.json')

def get_app_version():
    """Lê o version.json e retorna os dados de versão."""
    try:
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"versao": "1.0.0", "data": "", "notas": "", "obrigatoria": False}

def get_index_hash():
    """Calcula o hash MD5 do index.html para detectar mudanças."""
    index_path = os.path.join(WWW_DIR, 'index.html')
    try:
        with open(index_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

@app.route('/ota/versao', methods=['GET', 'OPTIONS'])
def ota_versao():
    """Retorna a versão atual do app e o hash do index.html."""
    if request.method == 'OPTIONS':
        return '', 204
    ver = get_app_version()
    ver['hash'] = get_index_hash()
    return jsonify(ver)

@app.route('/ota/index.html', methods=['GET', 'OPTIONS'])
def ota_index():
    """Serve o index.html atualizado para download pelo app."""
    if request.method == 'OPTIONS':
        return '', 204
    return send_from_directory(WWW_DIR, 'index.html')

@app.route('/ota/version.json', methods=['GET', 'OPTIONS'])
def ota_version_json():
    """Serve o version.json para o app verificar a versão."""
    if request.method == 'OPTIONS':
        return '', 204
    return send_from_directory(WWW_DIR, 'version.json')

@app.route('/versao_app', methods=['GET', 'OPTIONS'])
def versao_app():
    if request.method == 'OPTIONS':
        return '', 204
    # Retorno com a base_url agora definida corretamente
    return jsonify({
        "versao_cliente": "1.1",
        "versao_admin": "1.1",
        "apk_cliente_url": f"{base_url}/apk/cliente.apk",
        "apk_admin_url": f"{base_url}/apk/admin.apk"
    })

@app.route('/api/logs', methods=['POST', 'OPTIONS'])
def save_log():
    if request.method == 'OPTIONS':
        return '', 204
    data = request.json
    user_id = data.get('user_id')
    acao = data.get('acao')
    detalhes = data.get('detalhes', '')
    if not user_id or not acao:
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400
    db = get_db()
    db.execute('INSERT INTO logs_atividade (user_id, acao, detalhes) VALUES (?, ?, ?)', (user_id, acao, detalhes))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/admin/logs', methods=['GET', 'OPTIONS'])
def list_logs():
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    logs = db.execute('''
        SELECT l.*, u.nome as user_nome 
        FROM logs_atividade l 
        JOIN users u ON l.user_id = u.id 
        ORDER BY l.criado_em DESC LIMIT 50
    ''').fetchall()
    return jsonify([dict(l) for l in logs])

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND senha = ?', (email, senha)).fetchone()
    if user:
        user_dict = dict(user)
        db.execute('INSERT INTO logs_atividade (user_id, acao) VALUES (?, ?)', (user_dict['id'], 'Acessou o App'))
        db.commit()
        return jsonify({"status": "success", "user": user_dict})
    return jsonify({"status": "error", "message": "E-mail ou senha incorretos."}), 401

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    # Aceita 'usuario'/'senha' (padrão do app) ou 'user'/'pass' (legado)
    user = data.get('usuario') or data.get('user')
    passw = data.get('senha') or data.get('pass')
    if not user or not passw:
        return jsonify({"ok": False, "erro": "Usuário e senha obrigatórios."}), 400
    db = get_db()
    # Verifica na tabela admin_config
    admin = db.execute('SELECT * FROM admin_config WHERE usuario = ? AND senha = ?', (user, passw)).fetchone()
    if not admin:
        # Tenta com username/password (legado)
        admin = db.execute('SELECT * FROM admin_config WHERE username = ? AND password = ?', (user, passw)).fetchone()
    if admin:
        return jsonify({"ok": True, "token": "admin-session-token"})
    return jsonify({"ok": False, "erro": "Usuário ou senha incorretos."}), 401

@app.route('/api/users', methods=['GET'])
def list_users():
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY criado_em DESC').fetchall()
    return jsonify([dict(u) for u in users])

@app.route('/api/users', methods=['POST'])
def save_user():
    data = request.json
    db = get_db()
    fields = [
        'nome', 'email', 'senha', 'bebe', 'semanas', 'dpp', 'parto', 'rg_orgao', 'cpf', 'estado_civil', 
        'endereco_cep', 'nacionalidade', 'pacote_escolhido', 'servicos_extras', 'forma_pagamento', 'melhor_data_pagamento',
        'email_acompanhante', 'ja_iniciou_pre_natal', 'local_pre_natal', 'idade', 'data_nascimento', 
        'acompanhante_parentesco', 'historico_saude', 'sobre_saude', 'alergias', 'sintomas_gravidez', 
        'historico_doencas_familiares', 'doencas_gravidez', 'ja_esteve_gravida_antes', 
        'intercorrencias_gestacoes_anteriores', 'quais_intercorrencias', 'experiencia_partos_anteriores', 
        'relato_experiencia_parto', 'medicacao_suplemento', 'vacinacao_em_dia', 'sentimento_gravidez', 
        'questao_religiosa_cultural', 'expectativas_desejos_parto'
    ]
    
    if 'id' in data and data['id']:
        set_clause = ', '.join([f"{f}=?" for f in fields])
        values = [data.get(f) for f in fields]
        values.append(data['id'])
        db.execute(f'UPDATE users SET {set_clause} WHERE id=?', tuple(values))
    else:
        dup = db.execute('SELECT id FROM users WHERE email = ?', (data['email'],)).fetchone()
        if dup: return jsonify({"status": "error", "message": "E-mail já cadastrado."}), 400
        placeholders = ', '.join(['?' for _ in fields])
        columns = ', '.join(fields)
        values = [data.get(f) for f in fields]
        cursor = db.execute(f'INSERT INTO users ({columns}) VALUES ({placeholders})', tuple(values))
        new_id = cursor.lastrowid
        db.execute('INSERT INTO logs_atividade (user_id, acao) VALUES (?, ?)', (new_id, 'Nova doulanda cadastrada'))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/users/<int:user_id>/toggle', methods=['POST'])
def toggle_user(user_id):
    db = get_db()
    db.execute('UPDATE users SET ativo = NOT ativo WHERE id = ?', (user_id,))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/conteudos', methods=['GET'])
def list_conteudos():
    db = get_db()
    try:
        cont = db.execute('SELECT * FROM conteudos WHERE ativo = 1 ORDER BY secao_id ASC, ordem ASC, criado_em ASC').fetchall()
        return jsonify([dict(c) for c in cont])
    except sqlite3.OperationalError:
        return jsonify([])

@app.route('/api/admin/conteudos', methods=['GET'])
def admin_list_conteudos():
    db = get_db()
    try:
        cont = db.execute('SELECT * FROM conteudos ORDER BY criado_em DESC').fetchall()
        return jsonify([dict(c) for c in cont])
    except sqlite3.OperationalError:
        return jsonify([])

@app.route('/api/conteudos', methods=['POST'])
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
    return jsonify({"status": "success"})

@app.route('/api/conteudos/<int:cont_id>', methods=['DELETE'])
def delete_conteudo(cont_id):
    db = get_db()
    db.execute('DELETE FROM conteudos WHERE id = ?', (cont_id,))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/conteudos/<int:cont_id>/toggle', methods=['POST'])
def toggle_conteudo(cont_id):
    db = get_db()
    db.execute('UPDATE conteudos SET ativo = NOT ativo WHERE id = ?', (cont_id,))
    db.commit()
    return jsonify({"status": "success"})

@app.route("/api/admin/upload_ebook", methods=["POST"])
def upload_ebook():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "Nenhum arquivo enviado."}), 400
    
    file = request.files["file"]
    capa = request.files.get("capa")
    
    if file.filename == "":
        return jsonify({"status": "error", "message": "Nenhum arquivo selecionado."}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        
        url_capa = None
        if capa and allowed_file(capa.filename):
            capa_filename = "capa_" + secure_filename(capa.filename)
            capa_path = os.path.join(app.config["UPLOAD_FOLDER"], capa_filename)
            capa.save(capa_path)
            url_capa = f"/uploads/{capa_filename}"
            
        titulo = request.form.get("titulo")
        descricao = request.form.get("descricao", "")
        if not titulo:
            return jsonify({"status": "error", "message": "Título obrigatório."}), 400
            
        db = get_db()
        db.execute("INSERT INTO ebooks (titulo, descricao, url_pdf, url_capa) VALUES (?, ?, ?, ?)",
                   (titulo, descricao, f"/uploads/{filename}", url_capa))
        db.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Tipo de arquivo não permitido."}), 400

@app.route('/api/ebooks', methods=['GET'])
def list_ebooks():
    db = get_db()
    ebooks = db.execute('SELECT * FROM ebooks ORDER BY criado_em DESC').fetchall()
    return jsonify([dict(e) for e in ebooks])

@app.route('/api/ebooks/<int:ebook_id>', methods=['DELETE'])
def delete_ebook(ebook_id):
    db = get_db()
    db.execute('DELETE FROM ebooks WHERE id = ?', (ebook_id,))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/config', methods=['GET', 'OPTIONS'])
def config():
    """Endpoint público para o app das clientes obter as configurações do sistema (WhatsApp, Instagram, e-mail)."""
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    rows = db.execute('SELECT chave, valor FROM config_global').fetchall()
    config_map = {row['chave']: row['valor'] for row in rows}
    return jsonify({
        'whatsapp_numero':   config_map.get('whatsapp_numero', ''),
        'whatsapp_mensagem': config_map.get('whatsapp_mensagem', 'Olá, preciso de ajuda!'),
        'instagram_url':     config_map.get('instagram_url', ''),
        'email_contato':     config_map.get('email_contato', '')
    })

# ── CONFIGURAÇÕES GLOBAIS DO ADMIN ──────────────────────────────────────────────────────────────────────────────
@app.route('/api/admin/config', methods=['GET', 'POST', 'OPTIONS'])
def admin_config():
    """Endpoint para ler e salvar as configurações globais do sistema (WhatsApp, Instagram, e-mail)."""
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    if request.method == 'GET':
        rows = db.execute('SELECT chave, valor FROM config_global').fetchall()
        return jsonify([dict(r) for r in rows])
    else:
        data = request.json or {}
        campos = ['whatsapp_numero', 'whatsapp_mensagem', 'instagram_url', 'email_contato']
        try:
            for campo in campos:
                if campo in data:
                    db.execute(
                        "INSERT OR REPLACE INTO config_global (chave, valor, atualizado_em) VALUES (?, ?, CURRENT_TIMESTAMP)",
                        (campo, data[campo])
                    )
            db.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/admin/change-password', methods=['POST', 'OPTIONS'])
def admin_change_password():
    """Endpoint para o admin trocar a própria senha."""
    if request.method == 'OPTIONS':
        return '', 204
    data = request.json or {}
    old_pass = data.get('old_password', '')
    new_pass = data.get('new_password', '')
    if not old_pass or not new_pass:
        return jsonify({"status": "error", "message": "Senha atual e nova senha são obrigatórias"}), 400
    db = get_db()
    admin = db.execute('SELECT * FROM admin_config WHERE id = 1').fetchone()
    if not admin or admin['password'] != old_pass:
        return jsonify({"status": "error", "message": "Senha atual incorreta"}), 401
    db.execute('UPDATE admin_config SET password = ? WHERE id = 1', (new_pass,))
    db.commit()
    return jsonify({"status": "success"})

# ── DICAS SEMANAIS ──────────────────────────────────────────────────────────────────────────────
@app.route('/api/dicas', methods=['GET', 'OPTIONS'])
def dicas_publicas():
    """Endpoint público para o app das clientes buscar as dicas (sem autenticação)."""
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    dicas = db.execute('SELECT * FROM dicas_personalizadas ORDER BY semana ASC').fetchall()
    return jsonify([dict(d) for d in dicas])

@app.route('/api/admin/dicas', methods=['GET', 'POST', 'OPTIONS'])
def admin_dicas():
    """Endpoint do admin para listar e criar dicas."""
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    if request.method == 'GET':
        dicas = db.execute('SELECT * FROM dicas_personalizadas ORDER BY semana ASC').fetchall()
        return jsonify([dict(d) for d in dicas])
    else:
        data = request.json or {}
        semana = data.get('semana')
        titulo = data.get('titulo', '')
        dica   = data.get('dica', '')
        emoji  = data.get('emoji', '')
        if not semana or not dica:
            return jsonify({"status": "error", "message": "Semana e dica são obrigatórios"}), 400
        try:
            db.execute(
                'INSERT OR REPLACE INTO dicas_personalizadas (semana, titulo, dica, emoji) VALUES (?, ?, ?, ?)',
                (int(semana), titulo, dica, emoji)
            )
            db.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/admin/dicas/<int:dica_id>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
def admin_dica_detail(dica_id):
    """Endpoint do admin para obter, editar ou excluir uma dica pelo id."""
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    if request.method == 'GET':
        dica = db.execute('SELECT * FROM dicas_personalizadas WHERE id = ?', (dica_id,)).fetchone()
        if not dica:
            return jsonify({"status": "error", "message": "Dica não encontrada"}), 404
        return jsonify(dict(dica))
    elif request.method == 'PUT':
        data = request.json or {}
        semana = data.get('semana')
        titulo = data.get('titulo', '')
        dica   = data.get('dica', '')
        emoji  = data.get('emoji', '')
        if not semana or not dica:
            return jsonify({"status": "error", "message": "Semana e dica são obrigatórios"}), 400
        try:
            db.execute(
                'UPDATE dicas_personalizadas SET semana=?, titulo=?, dica=?, emoji=? WHERE id=?',
                (int(semana), titulo, dica, emoji, dica_id)
            )
            db.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:  # DELETE
        db.execute('DELETE FROM dicas_personalizadas WHERE id = ?', (dica_id,))
        db.commit()
        return jsonify({"status": "success"})

@app.route('/api/maternidade', methods=['GET', 'POST', 'OPTIONS'])
def maternidade():
    if request.method == 'OPTIONS':
        return '', 204
    db = get_db()
    user_id = request.args.get('user_id') or (request.json.get('user_id') if request.json else None)
    if request.method == 'GET':
        try:
            mat = db.execute('SELECT * FROM maternidade WHERE user_id = ?', (user_id,)).fetchone()
            return jsonify(dict(mat) if mat else {})
        except:
            return jsonify({})
    elif request.method == 'POST':
        data = request.json
        try:
            db.execute('INSERT OR REPLACE INTO maternidade (user_id, nome_maternidade, endereco, telefone, medico_nome, medico_telefone, plano_saude, numero_cartao, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (data['user_id'], data.get('nome_maternidade', ''), data.get('endereco', ''), data.get('telefone', ''), data.get('medico_nome', ''), data.get('medico_telefone', ''), data.get('plano_saude', ''), data.get('numero_cartao', ''), data.get('observacoes', '')))
            db.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/plano-parto', methods=['GET', 'POST', 'OPTIONS'])
def plano_parto():
    if request.method == 'OPTIONS':
        return '', 204
    
    db = get_db()
    user_id = request.args.get('user_id') or (request.json.get('user_id') if request.json else None)
    
    if request.method == 'GET':
        try:
            plano = db.execute('SELECT * FROM plano_parto WHERE user_id = ?', (user_id,)).fetchone()
            return jsonify(dict(plano) if plano else {})
        except:
            return jsonify({})
    elif request.method == 'POST':
        data = request.json
        try:
            db.execute('INSERT OR REPLACE INTO plano_parto (user_id, tipo_parto, acompanhante, desejos, medos, posicoes_preferidas, musica_ambiente, iluminacao, outras_observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (data['user_id'], data.get('tipo_parto', ''), data.get('acompanhante', ''), data.get('desejos', ''), data.get('medos', ''), data.get('posicoes_preferidas', ''), data.get('musica_ambiente', ''), data.get('iluminacao', ''), data.get('outras_observacoes', '')))
            db.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500


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

if __name__ == '__main__':
    # Tenta inicializar o banco sempre para garantir as tabelas
    init_db()
    
    # Executa migração de colunas faltantes
    try:
        from migrate_db import migrate
        migrate()
    except Exception as e:
        print(f"Erro ao executar migração automática: {e}")
    
    print(f"\n{'='*60}")
    print(f" 🚀 SERVIDOR API NALIN NAZARETH ATIVO")
    print(f" 📡 IP Local (Wi-Fi): http://{ip_local}:5000")
    print(f" 🌍 Iniciando túnel público (aguarde alguns segundos)...")
    print(f"{'='*60}\n")
    
    # Inicia o tunnel cloudflared em background para não bloquear o servidor
    tunnel_thread = threading.Thread(target=start_cloudflared_tunnel, daemon=True)
    tunnel_thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
