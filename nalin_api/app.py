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
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps

app = Flask(__name__)

# ── SEGURANÇA ────────────────────────────────────────────────────────────────
JWT_SECRET = os.environ.get('JWT_SECRET', 'doula-nalin-jwt-secret-mude-em-producao')
JWT_EXPIRATION_HOURS = 8

def hash_password(plain):
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(plain, hashed):
    try:
        # Fallback para senhas em texto puro (como a inserida pelo migrate_db.py)
        if plain == hashed:
            return True
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def generate_token(admin_id, username):
    payload = {'sub': str(admin_id), 'username': username,
                'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)}
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"ok": False, "erro": "Token de autenticação ausente."}), 401
        token = auth_header.split(' ', 1)[1]
        try:
            jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({"ok": False, "erro": "Sessão expirada. Faça login novamente."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"ok": False, "erro": "Token inválido."}), 401
        return f(*args, **kwargs)
    return decorated

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(os.path.dirname(BASE_DIR), 'dados.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')
UPLOAD_FOLDER = os.path.join(os.path.dirname(BASE_DIR), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
WWW_DIR = os.path.join(os.path.dirname(BASE_DIR), 'www')
VERSION_FILE = os.path.join(WWW_DIR, 'version.json')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close(); return ip
    except: return "127.0.0.1"

ip_local = get_local_ip()
base_url = f"http://{ip_local}:5000"
tunnel_url = None

def start_cloudflared_tunnel():
    global tunnel_url
    try:
        check = subprocess.run(['cloudflared', '--version'], capture_output=True, text=True)
        if check.returncode != 0: return
        proc = subprocess.Popen(['cloudflared', 'tunnel', '--url', 'http://localhost:5000'],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
            if match:
                tunnel_url = match.group(0)
                print(f"\n{'='*60}\n 🌍 URL PÚBLICA: {tunnel_url}\n{'='*60}\n")
                break
    except Exception as e:
        print(f"[TUNNEL] Erro: {e}")

CORS(app, resources={
    r"/api/*": {"origins": "*", "methods": ["GET","POST","PUT","DELETE","OPTIONS"], "allow_headers": ["Content-Type","Authorization"]},
    r"/versao_app": {"origins": "*"}, r"/server-info": {"origins": "*"},
    r"/ota/*": {"origins": "*"}, r"/uploads/*": {"origins": "*"}
})

app.add_url_rule("/uploads/<path:filename>", endpoint="uploads",
                 view_func=lambda filename: send_from_directory(app.config["UPLOAD_FOLDER"], filename))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        r = app.make_default_options_response()
        r.headers['Access-Control-Allow-Origin'] = '*'
        r.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return r

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()

def init_db():
    with app.app_context():
        db = get_db()
        if os.path.exists(SCHEMA_PATH):
            with open(SCHEMA_PATH, mode='r', encoding='utf-8') as f:
                db.cursor().executescript(f.read())
            db.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_activity(user_id, acao, detalhes=''):
    try:
        db = get_db()
        db.execute('INSERT INTO logs_atividade (user_id, acao, detalhes) VALUES (?, ?, ?)', (user_id, acao, detalhes))
        db.commit()
    except Exception: pass

def get_app_version():
    try:
        with open(VERSION_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"versao": "1.0.0", "data": "", "notas": "", "obrigatoria": False}

def get_index_hash():
    try:
        with open(os.path.join(WWW_DIR, 'index.html'), 'rb') as f: return hashlib.md5(f.read()).hexdigest()
    except: return ""

# ── ROTAS ────────────────────────────────────────────────────────────────────
@app.route('/api/status', methods=['GET','OPTIONS'])
def status():
    if request.method == 'OPTIONS': return '', 204
    return jsonify({"status": "online"})

@app.route('/server-info', methods=['GET','OPTIONS'])
def server_info():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    try:
        row = db.execute("SELECT valor FROM config_global WHERE chave = 'url_base_servidor'").fetchone()
        url_base_salva = row['valor'] if row and row['valor'] else None
    except: url_base_salva = None
    return jsonify({"status":"online","ip_local":ip_local,"url_local":f"http://{ip_local}:5000",
                    "url_publica":tunnel_url,"url_base_servidor":url_base_salva})

@app.route('/api/url-servidor', methods=['GET','POST','OPTIONS'])
def url_servidor():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        try:
            row = db.execute("SELECT valor FROM config_global WHERE chave = 'url_base_servidor'").fetchone()
            url_base = row['valor'] if row and row['valor'] else None
        except: url_base = None
        return jsonify({"status":"ok","url_base_servidor":url_base,"url_publica":tunnel_url,"ip_local":ip_local})
    data = request.json or {}
    nova_url = data.get('url_base_servidor','').strip()
    if not nova_url: return jsonify({"status":"error","message":"url_base_servidor é obrigatória"}), 400
    db.execute("INSERT OR REPLACE INTO config_global (chave,valor,descricao,atualizado_em) VALUES ('url_base_servidor',?,'URL base do servidor',CURRENT_TIMESTAMP)",(nova_url,))
    db.commit()
    return jsonify({"status":"success","url_base_servidor":nova_url})

@app.route('/ota/versao', methods=['GET','OPTIONS'])
def ota_versao():
    if request.method == 'OPTIONS': return '', 204
    ver = get_app_version(); ver['hash'] = get_index_hash(); return jsonify(ver)

@app.route('/ota/bundle.zip', methods=['GET','OPTIONS'])
def ota_bundle_zip():
    """
    Empacota a pasta www/ em um zip on-the-fly e devolve.
    O @capgo/capacitor-updater baixa esse zip, extrai e troca o WebView.
    Estrutura: o zip deve ter os arquivos do bundle direto na raiz
    (index.html no topo) — é exatamente o que esta função produz.
    """
    if request.method == 'OPTIONS': return '', 204
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(WWW_DIR):
            # ignora diretórios ocultos e admin (não faz parte do app cliente)
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for fname in files:
                if fname.startswith('.'): continue
                # admin.html não vai pro app cliente
                if fname == 'admin.html': continue
                full = os.path.join(root, fname)
                # Caminho relativo dentro do zip (a partir de www/)
                rel = os.path.relpath(full, WWW_DIR).replace('\\', '/')
                zf.write(full, rel)
    buf.seek(0)
    from flask import send_file
    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name='bundle.zip'
    )

@app.route('/ota/index.html', methods=['GET','OPTIONS'])
def ota_index():
    if request.method == 'OPTIONS': return '', 204
    return send_from_directory(WWW_DIR, 'index.html')

@app.route('/admin', methods=['GET','OPTIONS'])
@app.route('/admin.html', methods=['GET','OPTIONS'])
@app.route('/ota/admin.html', methods=['GET','OPTIONS'])
def ota_admin():
    if request.method == 'OPTIONS': return '', 204
    resp = send_from_directory(WWW_DIR, 'admin.html')
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    return resp

@app.route('/ota/version.json', methods=['GET','OPTIONS'])
def ota_version_json():
    if request.method == 'OPTIONS': return '', 204
    return send_from_directory(WWW_DIR, 'version.json')

@app.route('/versao_app', methods=['GET','OPTIONS'])
def versao_app():
    if request.method == 'OPTIONS': return '', 204
    return jsonify({"versao_cliente":"1.1","versao_admin":"1.1"})

@app.route('/api/pdf/temp', methods=['POST','OPTIONS'])
def pdf_temp_upload():
    """Recebe PDF em base64, salva temporariamente e retorna URL para download no Android."""
    if request.method == 'OPTIONS': return '', 204
    import base64, uuid, time
    data = request.json or {}
    pdf_b64 = data.get('pdf_base64',''); filename = data.get('filename','documento.pdf')
    if not pdf_b64: return jsonify({"ok":False,"erro":"PDF não enviado."}), 400
    try:
        pdf_bytes = base64.b64decode(pdf_b64)
        tmp_dir = os.path.join(UPLOAD_FOLDER, 'tmp'); os.makedirs(tmp_dir, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}_{secure_filename(filename)}"
        with open(os.path.join(tmp_dir, safe_name), 'wb') as f: f.write(pdf_bytes)
        now = time.time()
        for old in os.listdir(tmp_dir):
            try:
                if now - os.path.getmtime(os.path.join(tmp_dir, old)) > 600: os.remove(os.path.join(tmp_dir, old))
            except: pass
        return jsonify({"ok":True,"url":f"/uploads/tmp/{safe_name}"})
    except Exception as e: return jsonify({"ok":False,"erro":str(e)}), 500

@app.route('/api/logs', methods=['POST','OPTIONS'])
def save_log():
    if request.method == 'OPTIONS': return '', 204
    data = request.json
    user_id = data.get('user_id'); acao = data.get('acao'); detalhes = data.get('detalhes','')
    if not user_id or not acao: return jsonify({"status":"error","message":"Dados incompletos"}), 400
    db = get_db()
    db.execute('INSERT INTO logs_atividade (user_id,acao,detalhes) VALUES (?,?,?)',(user_id,acao,detalhes))
    db.commit(); return jsonify({"status":"success"})

@app.route('/api/admin/logs', methods=['GET','OPTIONS'])
@require_admin
def list_logs():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    logs = db.execute('SELECT l.*,u.nome as user_nome FROM logs_atividade l JOIN users u ON l.user_id=u.id ORDER BY l.criado_em DESC LIMIT 50').fetchall()
    return jsonify([dict(l) for l in logs])

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json; email = data.get('email'); senha = data.get('senha')
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if user and check_password(senha, user['senha']):
        user_dict = dict(user)
        db.execute('INSERT INTO logs_atividade (user_id,acao) VALUES (?,?)',(user_dict['id'],'Acessou o App'))
        db.commit(); return jsonify({"status":"success","user":user_dict})
    return jsonify({"status":"error","message":"E-mail ou senha incorretos."}), 401

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    user = data.get('usuario') or data.get('user'); passw = data.get('senha') or data.get('pass')
    if not user or not passw: return jsonify({"ok":False,"erro":"Usuário e senha obrigatórios."}), 400
    db = get_db()
    admin = db.execute('SELECT * FROM admin_config WHERE username = ?',(user,)).fetchone()
    if admin and check_password(passw, admin['password']):
        return jsonify({"ok":True,"token":generate_token(admin['id'],admin['username'])})
    return jsonify({"ok":False,"erro":"Usuário ou senha incorretos."}), 401

@app.route('/api/users', methods=['GET'])
@require_admin
def list_users():
    db = get_db()
    return jsonify([dict(u) for u in db.execute('SELECT * FROM users ORDER BY criado_em DESC').fetchall()])

@app.route('/api/users', methods=['POST'])
def save_user():
    data = request.json; db = get_db()
    fields = ['nome','email','senha','bebe','semanas','dpp','parto','rg_orgao','cpf','estado_civil',
              'endereco_cep','nacionalidade','pacote_escolhido','servicos_extras','forma_pagamento','melhor_data_pagamento',
              'email_acompanhante','ja_iniciou_pre_natal','local_pre_natal','idade','data_nascimento',
              'acompanhante_parentesco','historico_saude','sobre_saude','alergias','sintomas_gravidez',
              'historico_doencas_familiares','doencas_gravidez','ja_esteve_gravida_antes',
              'intercorrencias_gestacoes_anteriores','quais_intercorrencias','experiencia_partos_anteriores',
              'relato_experiencia_parto','medicacao_suplemento','vacinacao_em_dia','sentimento_gravidez',
              'questao_religiosa_cultural','expectativas_desejos_parto']
    if 'id' in data and data['id']:
        if data.get('senha') and not str(data['senha']).startswith('$2b$'):
            data['senha'] = hash_password(data['senha'])
        values = [data.get(f) for f in fields]; values.append(data['id'])
        db.execute(f"UPDATE users SET {', '.join([f'{f}=?' for f in fields])} WHERE id=?", tuple(values))
    else:
        if db.execute('SELECT id FROM users WHERE email = ?',(data['email'],)).fetchone():
            return jsonify({"status":"error","message":"E-mail já cadastrado."}), 400
        if data.get('senha'): data['senha'] = hash_password(data['senha'])
        values = [data.get(f) for f in fields]
        cursor = db.execute(f"INSERT INTO users ({','.join(fields)}) VALUES ({','.join(['?']*len(fields))})", tuple(values))
        db.execute('INSERT INTO logs_atividade (user_id,acao) VALUES (?,?)',(cursor.lastrowid,'Nova doulanda cadastrada'))
    db.commit(); return jsonify({"status":"success"})

@app.route('/api/users/<int:user_id>/toggle', methods=['POST'])
@require_admin
def toggle_user(user_id):
    db = get_db(); db.execute('UPDATE users SET ativo = NOT ativo WHERE id = ?',(user_id,)); db.commit()
    return jsonify({"status":"success"})

@app.route('/api/conteudos', methods=['GET'])
def list_conteudos():
    db = get_db()
    try: return jsonify([dict(c) for c in db.execute('SELECT * FROM conteudos WHERE ativo=1 ORDER BY secao_id ASC,ordem ASC,criado_em ASC').fetchall()])
    except sqlite3.OperationalError: return jsonify([])

@app.route('/api/admin/conteudos', methods=['GET'])
@require_admin
def admin_list_conteudos():
    db = get_db()
    try: return jsonify([dict(c) for c in db.execute('SELECT * FROM conteudos ORDER BY criado_em DESC').fetchall()])
    except sqlite3.OperationalError: return jsonify([])

@app.route('/api/conteudos', methods=['POST'])
@require_admin
def save_conteudo():
    data = request.json; db = get_db(); secao_id = data.get('secao_id') or None; ordem = data.get('ordem',0)
    if 'id' in data and data['id']:
        db.execute('UPDATE conteudos SET titulo=?,categoria=?,subcategoria=?,emoji=?,descricao=?,duracao=?,paginas=?,url=?,cor=?,secao_id=?,ordem=? WHERE id=?',
                   (data['titulo'],data['categoria'],data['subcategoria'],data['emoji'],data['descricao'],data['duracao'],data['paginas'],data['url'],data['cor'],secao_id,ordem,data['id']))
        db.commit(); return jsonify({"status":"success","id":int(data['id'])})
    else:
        db.execute('INSERT INTO conteudos (titulo,categoria,subcategoria,emoji,descricao,duracao,paginas,url,cor,secao_id,ordem) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                   (data['titulo'],data['categoria'],data['subcategoria'],data['emoji'],data['descricao'],data['duracao'],data['paginas'],data['url'],data['cor'],secao_id,ordem))
        db.commit()
        new_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        return jsonify({"status":"success","id":new_id})

@app.route('/api/admin/conteudo/<int:cont_id>/capa', methods=['POST','OPTIONS'])
@require_admin
def upload_capa_conteudo(cont_id):
    if request.method == 'OPTIONS': return '', 204
    if 'capa' not in request.files: return jsonify({"status":"error","message":"Nenhuma imagem enviada."}), 400
    capa = request.files['capa']
    if not capa.filename: return jsonify({"status":"error","message":"Nenhum arquivo selecionado."}), 400
    if not allowed_file(capa.filename): return jsonify({"status":"error","message":"Tipo não permitido. Use JPG, PNG ou WebP."}), 400
    filename = f"capa_video_{cont_id}_" + secure_filename(capa.filename)
    capa.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    url_capa = f"/uploads/{filename}"
    db = get_db()
    db.execute('UPDATE conteudos SET capa=? WHERE id=?', (url_capa, cont_id))
    db.commit()
    return jsonify({"status":"success","url_capa":url_capa})

@app.route('/api/conteudos/<int:cont_id>', methods=['DELETE'])
@require_admin
def delete_conteudo(cont_id):
    db = get_db(); db.execute('DELETE FROM conteudos WHERE id=?',(cont_id,)); db.commit()
    return jsonify({"status":"success"})

@app.route('/api/conteudos/<int:cont_id>/toggle', methods=['POST'])
@require_admin
def toggle_conteudo(cont_id):
    db = get_db(); db.execute('UPDATE conteudos SET ativo=NOT ativo WHERE id=?',(cont_id,)); db.commit()
    return jsonify({"status":"success"})

@app.route("/api/admin/upload_ebook", methods=["POST"])
@require_admin
def upload_ebook():
    if "file" not in request.files: return jsonify({"status":"error","message":"Nenhum arquivo enviado."}), 400
    file = request.files["file"]; capa = request.files.get("capa")
    if file.filename == "": return jsonify({"status":"error","message":"Nenhum arquivo selecionado."}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        url_capa = None
        if capa and allowed_file(capa.filename):
            capa_filename = "capa_" + secure_filename(capa.filename)
            capa.save(os.path.join(app.config["UPLOAD_FOLDER"], capa_filename))
            url_capa = f"/uploads/{capa_filename}"
        titulo = request.form.get("titulo")
        if not titulo: return jsonify({"status":"error","message":"Título obrigatório."}), 400
        db = get_db()
        db.execute("INSERT INTO ebooks (titulo,descricao,categoria,url_pdf,url_capa) VALUES (?,?,?,?,?)",
                   (titulo, request.form.get("descricao",""), request.form.get("categoria","Geral") or "Geral", f"/uploads/{filename}", url_capa))
        db.commit(); return jsonify({"status":"success"})
    return jsonify({"status":"error","message":"Tipo de arquivo não permitido."}), 400

@app.route('/api/ebooks', methods=['GET'])
def list_ebooks():
    db = get_db()
    return jsonify([dict(e) for e in db.execute('SELECT * FROM ebooks ORDER BY criado_em DESC').fetchall()])

@app.route('/api/ebooks/<int:ebook_id>', methods=['PUT','DELETE','OPTIONS'])
@require_admin
def manage_ebook(ebook_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'DELETE':
        db.execute('DELETE FROM ebooks WHERE id=?', (ebook_id,)); db.commit()
        return jsonify({"status":"success"})
    # PUT — atualiza metadados e opcionalmente a capa
    if request.content_type and 'multipart' in request.content_type:
        titulo = request.form.get('titulo','')
        descricao = request.form.get('descricao','')
        categoria = request.form.get('categoria','Geral') or 'Geral'
        capa = request.files.get('capa')
        url_capa = None
        if capa and allowed_file(capa.filename):
            capa_filename = 'capa_eb_' + secure_filename(capa.filename)
            capa.save(os.path.join(app.config['UPLOAD_FOLDER'], capa_filename))
            url_capa = f'/uploads/{capa_filename}'
        if url_capa:
            db.execute('UPDATE ebooks SET titulo=?,descricao=?,categoria=?,url_capa=? WHERE id=?',
                       (titulo, descricao, categoria, url_capa, ebook_id))
        else:
            db.execute('UPDATE ebooks SET titulo=?,descricao=?,categoria=? WHERE id=?',
                       (titulo, descricao, categoria, ebook_id))
    else:
        data = request.json or {}
        db.execute('UPDATE ebooks SET titulo=?,descricao=?,categoria=? WHERE id=?',
                   (data.get('titulo',''), data.get('descricao',''), data.get('categoria','Geral') or 'Geral', ebook_id))
    db.commit()
    return jsonify({'status':'success'})

@app.route('/api/admin/ebooks/update', methods=['POST','OPTIONS'])
@require_admin
def admin_update_ebook():
    if request.method == 'OPTIONS': return '', 204
    try:
        db = get_db()
        if request.content_type and 'multipart' in request.content_type:
            ebook_id = request.form.get('id', type=int)
            if not ebook_id: return jsonify({'status':'error','message':'ID ausente'}), 400
            titulo = request.form.get('titulo','')
            descricao = request.form.get('descricao','')
            categoria = request.form.get('categoria','Geral')
            capa = request.files.get('capa')
            url_capa = None
            if capa and allowed_file(capa.filename):
                capa_filename = 'capa_eb_' + secure_filename(capa.filename)
                capa.save(os.path.join(app.config['UPLOAD_FOLDER'], capa_filename))
                url_capa = f'/uploads/{capa_filename}'
            if url_capa:
                db.execute('UPDATE ebooks SET titulo=?,descricao=?,categoria=?,url_capa=? WHERE id=?',
                           (titulo, descricao, categoria, url_capa, ebook_id))
            else:
                db.execute('UPDATE ebooks SET titulo=?,descricao=?,categoria=? WHERE id=?',
                           (titulo, descricao, categoria, ebook_id))
        else:
            data = request.json or {}
            ebook_id = data.get('id')
            if not ebook_id: return jsonify({'status':'error','message':'ID ausente'}), 400
            db.execute('UPDATE ebooks SET titulo=?,descricao=?,categoria=? WHERE id=?',
                       (data.get('titulo',''), data.get('descricao',''), data.get('categoria',''), ebook_id))
        db.commit()
        return jsonify({'status':'success'})
    except Exception as e:
        print(f'[EBOOK UPDATE ERROR] {e}')
        return jsonify({'status':'error','message':str(e)}), 500

@app.route('/api/config', methods=['GET','OPTIONS'])
def config():
    if request.method == 'OPTIONS': return '', 204
    db = get_db(); rows = db.execute('SELECT chave,valor FROM config_global').fetchall()
    m = {r['chave']:r['valor'] for r in rows}
    return jsonify({'whatsapp_numero':m.get('whatsapp_numero',''),'whatsapp_mensagem':m.get('whatsapp_mensagem','Olá!'),'instagram_url':m.get('instagram_url',''),'email_contato':m.get('email_contato','')})

@app.route('/api/admin/config', methods=['GET','POST','OPTIONS'])
@require_admin
def admin_config():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        return jsonify([dict(r) for r in db.execute('SELECT chave,valor FROM config_global').fetchall()])
    data = request.json or {}
    for campo in ['whatsapp_numero','whatsapp_mensagem','instagram_url','email_contato']:
        if campo in data:
            db.execute("INSERT OR REPLACE INTO config_global (chave,valor,atualizado_em) VALUES (?,?,CURRENT_TIMESTAMP)",(campo,data[campo]))
    db.commit(); return jsonify({"status":"success"})

@app.route('/api/admin/change-password', methods=['POST','OPTIONS'])
@require_admin
def admin_change_password():
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}; old_pass = data.get('old_password',''); new_pass = data.get('new_password','')
    if not old_pass or not new_pass: return jsonify({"status":"error","message":"Senha atual e nova senha são obrigatórias"}), 400
    db = get_db(); admin = db.execute('SELECT * FROM admin_config WHERE id=1').fetchone()
    if not admin or not check_password(old_pass, admin['password']):
        return jsonify({"status":"error","message":"Senha atual incorreta"}), 401
    db.execute('UPDATE admin_config SET password=? WHERE id=1',(hash_password(new_pass),)); db.commit()
    return jsonify({"status":"success"})

@app.route('/api/dicas', methods=['GET','OPTIONS'])
def dicas_publicas():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    return jsonify([dict(d) for d in db.execute('SELECT * FROM dicas_personalizadas ORDER BY semana ASC').fetchall()])

@app.route('/api/admin/dicas', methods=['GET','POST','OPTIONS'])
@require_admin
def admin_dicas():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        return jsonify([dict(d) for d in db.execute('SELECT * FROM dicas_personalizadas ORDER BY semana ASC').fetchall()])
    data = request.json or {}; semana = data.get('semana'); dica = data.get('dica','')
    if not semana or not dica: return jsonify({"status":"error","message":"Semana e dica são obrigatórios"}), 400
    db.execute('INSERT OR REPLACE INTO dicas_personalizadas (semana,titulo,dica,emoji) VALUES (?,?,?,?)',
               (int(semana),data.get('titulo',''),dica,data.get('emoji','')))
    db.commit(); return jsonify({"status":"success"})

@app.route('/api/admin/dicas/<int:dica_id>', methods=['GET','PUT','DELETE','OPTIONS'])
@require_admin
def admin_dica_detail(dica_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        dica = db.execute('SELECT * FROM dicas_personalizadas WHERE id=?',(dica_id,)).fetchone()
        return jsonify(dict(dica)) if dica else jsonify({"status":"error"}), 404
    if request.method == 'PUT':
        data = request.json or {}; semana = data.get('semana'); dica = data.get('dica','')
        if not semana or not dica: return jsonify({"status":"error","message":"Semana e dica são obrigatórios"}), 400
        db.execute('UPDATE dicas_personalizadas SET semana=?,titulo=?,dica=?,emoji=? WHERE id=?',
                   (int(semana),data.get('titulo',''),dica,data.get('emoji',''),dica_id))
        db.commit(); return jsonify({"status":"success"})
    db.execute('DELETE FROM dicas_personalizadas WHERE id=?',(dica_id,)); db.commit()
    return jsonify({"status":"success"})

@app.route('/api/maternidade', methods=['GET','POST','OPTIONS'])
def maternidade():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id: return jsonify({})
        row = db.execute('SELECT dados_json FROM maternidade WHERE user_id=?',(int(user_id),)).fetchone()
        if not row or not row['dados_json']: return jsonify({})
        try: return jsonify(json.loads(row['dados_json']))
        except: return jsonify({})
    data = request.json or {}
    try: user_id = int(data.get('user_id', 0))
    except: return jsonify({'status':'error'}), 400
    if not user_id: return jsonify({'status':'error','message':'user_id obrigatório'}), 400
    dados_str = json.dumps(data)
    if db.execute('SELECT id FROM maternidade WHERE user_id=?',(user_id,)).fetchone():
        db.execute('UPDATE maternidade SET dados_json=? WHERE user_id=?',(dados_str, user_id))
    else:
        db.execute('INSERT INTO maternidade (user_id,nome_maternidade,dados_json) VALUES (?,?,?)',
                   (user_id, data.get('nome',''), dados_str))
    db.commit(); return jsonify({'status':'success'})

@app.route('/api/agenda', methods=['GET','POST','OPTIONS'])
def agenda():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id: return jsonify([])
        rows = db.execute('SELECT * FROM agenda WHERE user_id=? ORDER BY data_evento ASC, hora_evento ASC',(int(user_id),)).fetchall()
        return jsonify([{'id':r['id'],'tipo':r['tipo'] or r['titulo'],'data':r['data_evento'],'hora':r['hora_evento'],'descricao':r['descricao']} for r in rows])
    data = request.json or {}
    try: user_id = int(data.get('user_id',0))
    except: return jsonify({'status':'error'}), 400
    tipo = data.get('tipo','')
    db.execute('INSERT INTO agenda (user_id,titulo,descricao,data_evento,hora_evento,tipo) VALUES (?,?,?,?,?,?)',
               (user_id, tipo, data.get('descricao',''), data.get('data',''), data.get('hora',''), tipo))
    db.commit()
    return jsonify({'status':'success','id': db.execute('SELECT last_insert_rowid()').fetchone()[0]})

@app.route('/api/agenda/<int:item_id>', methods=['PUT','DELETE','OPTIONS'])
def agenda_item(item_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'DELETE':
        try: user_id = int(request.args.get('user_id',0))
        except: return jsonify({'status':'error'}), 400
        db.execute('DELETE FROM agenda WHERE id=? AND user_id=?',(item_id, user_id))
        db.commit(); return jsonify({'status':'success'})
    data = request.json or {}
    try: user_id = int(data.get('user_id',0))
    except: return jsonify({'status':'error'}), 400
    tipo = data.get('tipo','')
    db.execute('UPDATE agenda SET titulo=?,descricao=?,data_evento=?,hora_evento=?,tipo=? WHERE id=? AND user_id=?',
               (tipo, data.get('descricao',''), data.get('data',''), data.get('hora',''), tipo, item_id, user_id))
    db.commit(); return jsonify({'status':'success'})

@app.route('/api/enxoval', methods=['GET','POST','OPTIONS'])
def enxoval():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id: return jsonify([])
        rows = db.execute('SELECT * FROM enxoval WHERE user_id=? ORDER BY criado_em ASC',(int(user_id),)).fetchall()
        return jsonify([{'id':r['id'],'item':r['item'],'comprado':bool(r['comprado'])} for r in rows])
    data = request.json or {}
    try: user_id = int(data.get('user_id',0))
    except: return jsonify({'status':'error'}), 400
    db.execute('INSERT INTO enxoval (user_id,item,comprado) VALUES (?,?,0)',(user_id, data.get('item', data.get('nome',''))))
    db.commit()
    return jsonify({'status':'success','id': db.execute('SELECT last_insert_rowid()').fetchone()[0]})

@app.route('/api/enxoval/<int:item_id>', methods=['PUT','DELETE','OPTIONS'])
def enxoval_item(item_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'DELETE':
        try: user_id = int(request.args.get('user_id',0))
        except: return jsonify({'status':'error'}), 400
        db.execute('DELETE FROM enxoval WHERE id=? AND user_id=?',(item_id, user_id))
        db.commit(); return jsonify({'status':'success'})
    data = request.json or {}
    try: user_id = int(data.get('user_id',0))
    except: return jsonify({'status':'error'}), 400
    db.execute('UPDATE enxoval SET comprado=? WHERE id=? AND user_id=?',
               (1 if data.get('comprado') else 0, item_id, user_id))
    db.commit(); return jsonify({'status':'success'})

@app.route('/api/contracoes', methods=['GET','POST','DELETE','OPTIONS'])
def contracoes():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    uid_raw = request.args.get('user_id') or (request.json.get('user_id') if request.json else None)
    try: user_id = int(uid_raw or 0)
    except: return jsonify({'status':'error'}), 400
    if not user_id: return jsonify({'status':'error','message':'user_id obrigatório'}), 400
    if request.method == 'GET':
        rows = db.execute('SELECT * FROM contracoes WHERE user_id=? ORDER BY start_time DESC',(user_id,)).fetchall()
        return jsonify([dict(r) for r in rows])
    if request.method == 'DELETE':
        db.execute('DELETE FROM contracoes WHERE user_id=?',(user_id,))
        db.commit(); return jsonify({'status':'success'})
    data = request.json or {}
    db.execute('INSERT INTO contracoes (user_id,start_time,end_time,duration_sec,interval_min) VALUES (?,?,?,?,?)',
               (user_id, data.get('start_time', data.get('start','')), data.get('end_time', data.get('end','')),
                int(data.get('duration_sec', data.get('duration',0))), float(data.get('interval_min', data.get('interval',0)))))
    db.commit()
    return jsonify({'status':'success','id': db.execute('SELECT last_insert_rowid()').fetchone()[0]})

@app.route('/api/contracoes/<int:cnt_id>', methods=['DELETE','OPTIONS'])
def contracao_item(cnt_id):
    if request.method == 'OPTIONS': return '', 204
    try: user_id = int(request.args.get('user_id',0))
    except: return jsonify({'status':'error'}), 400
    db = get_db()
    db.execute('DELETE FROM contracoes WHERE id=? AND user_id=?',(cnt_id, user_id))
    db.commit(); return jsonify({'status':'success'})

@app.route('/api/diario', methods=['GET','POST','OPTIONS'])
def diario():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    raw_id = request.args.get('user_id') or (request.json.get('user_id') if request.json else None)
    if not raw_id: return jsonify({'status':'error','message':'user_id obrigatório'}), 400
    try: user_id = int(raw_id)
    except (ValueError, TypeError): return jsonify({'status':'error','message':'user_id inválido'}), 400
    if request.method == 'GET':
        rows = db.execute('SELECT * FROM diario WHERE user_id=? ORDER BY criado_em DESC', (user_id,)).fetchall()
        return jsonify([dict(r) for r in rows])
    data = request.json
    db.execute('INSERT INTO diario (user_id,txt,mood,semanas,data,dia) VALUES (?,?,?,?,?,?)',
               (user_id, data.get('txt',''), data.get('mood',''), int(data.get('semanas',0)), data.get('data',''), data.get('dia','')))
    db.commit()
    entry_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    return jsonify({'status':'success', 'id': entry_id})

@app.route('/api/diario/<int:entry_id>', methods=['DELETE','PUT','OPTIONS'])
def diario_entry(entry_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'DELETE':
        raw_id = request.args.get('user_id')
        if not raw_id: return jsonify({'status':'error','message':'user_id obrigatório'}), 400
        try: user_id = int(raw_id)
        except (ValueError, TypeError): return jsonify({'status':'error','message':'user_id inválido'}), 400
        db.execute('DELETE FROM diario WHERE id=? AND user_id=?', (entry_id, user_id))
        db.commit()
        return jsonify({'status':'success'})
    # PUT — editar texto da entrada
    data = request.json or {}
    try: user_id = int(data.get('user_id', 0))
    except (ValueError, TypeError): return jsonify({'status':'error','message':'user_id inválido'}), 400
    if not user_id: return jsonify({'status':'error','message':'user_id obrigatório'}), 400
    db.execute('UPDATE diario SET txt=? WHERE id=? AND user_id=?', (data.get('txt',''), entry_id, user_id))
    db.commit()
    return jsonify({'status':'success'})

@app.route('/api/plano-parto', methods=['GET','POST','OPTIONS'])
def plano_parto():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id: return jsonify({})
        row = db.execute('SELECT dados_json FROM plano_parto WHERE user_id=?',(int(user_id),)).fetchone()
        if not row or not row['dados_json']: return jsonify({})
        try: return jsonify(json.loads(row['dados_json']))
        except: return jsonify({})
    data = request.json or {}
    try: user_id = int(data.get('user_id',0))
    except: return jsonify({'status':'error'}), 400
    if not user_id: return jsonify({'status':'error','message':'user_id obrigatório'}), 400
    dados_str = json.dumps(data)
    if db.execute('SELECT id FROM plano_parto WHERE user_id=?',(user_id,)).fetchone():
        db.execute('UPDATE plano_parto SET dados_json=? WHERE user_id=?',(dados_str, user_id))
    else:
        db.execute('INSERT INTO plano_parto (user_id,dados_json,acompanhante) VALUES (?,?,?)',
                   (user_id, dados_str, data.get('acomp','')))
    db.commit(); return jsonify({'status':'success'})

@app.route('/api/admin/secoes', methods=['GET','POST','OPTIONS'])
@require_admin
def admin_secoes():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        secoes = db.execute('SELECT * FROM curso_secoes ORDER BY ordem ASC,id ASC').fetchall()
        result = []
        for s in secoes:
            s_dict = dict(s)
            s_dict['videos'] = [dict(v) for v in db.execute('SELECT * FROM conteudos WHERE secao_id=? AND ativo=1 ORDER BY ordem ASC,criado_em ASC',(s['id'],)).fetchall()]
            result.append(s_dict)
        return jsonify(result)
    data = request.json or {}; titulo = data.get('titulo','').strip()
    if not titulo: return jsonify({'status':'error','message':'Título obrigatório'}), 400
    if data.get('id'):
        db.execute('UPDATE curso_secoes SET titulo=?,descricao=?,ordem=?,ativo=? WHERE id=?',
                   (titulo,data.get('descricao',''),data.get('ordem',0),data.get('ativo',1),data['id']))
    else:
        max_ordem = db.execute('SELECT COALESCE(MAX(ordem),0) FROM curso_secoes').fetchone()[0]
        db.execute('INSERT INTO curso_secoes (titulo,descricao,ordem) VALUES (?,?,?)',(titulo,data.get('descricao',''),max_ordem+1))
    db.commit(); return jsonify({'status':'success'})

@app.route('/api/admin/secoes/<int:secao_id>', methods=['DELETE','OPTIONS'])
@require_admin
def admin_delete_secao(secao_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    db.execute('UPDATE conteudos SET secao_id=NULL WHERE secao_id=?',(secao_id,))
    db.execute('DELETE FROM curso_secoes WHERE id=?',(secao_id,)); db.commit()
    return jsonify({'status':'success'})

@app.route('/api/secoes', methods=['GET','OPTIONS'])
def secoes_publicas():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    try:
        secoes = db.execute('SELECT * FROM curso_secoes WHERE ativo=1 ORDER BY ordem ASC,id ASC').fetchall()
        result = []
        for s in secoes:
            s_dict = dict(s)
            s_dict['videos'] = [dict(v) for v in db.execute('SELECT * FROM conteudos WHERE secao_id=? AND ativo=1 AND categoria="video" ORDER BY ordem ASC,criado_em ASC',(s['id'],)).fetchall()]
            result.append(s_dict)
        return jsonify(result)
    except: return jsonify([])

@app.route('/api/comentarios', methods=['GET','POST','OPTIONS'])
def video_comentarios():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        conteudo_id = request.args.get('conteudo_id')
        if not user_id: return jsonify([])
        if conteudo_id:
            row = db.execute('SELECT * FROM video_comentarios WHERE user_id=? AND conteudo_id=?',
                             (int(user_id), int(conteudo_id))).fetchone()
            return jsonify(dict(row) if row else {})
        rows = db.execute('SELECT * FROM video_comentarios WHERE user_id=?', (int(user_id),)).fetchall()
        return jsonify([dict(r) for r in rows])
    data = request.json or {}
    user_id = data.get('user_id'); conteudo_id = data.get('conteudo_id'); comentario = data.get('comentario','').strip()
    if not user_id or not conteudo_id: return jsonify({'status':'error','message':'user_id e conteudo_id obrigatórios'}), 400
    db.execute('INSERT OR REPLACE INTO video_comentarios (user_id,conteudo_id,comentario,atualizado_em) VALUES (?,?,?,CURRENT_TIMESTAMP)',
               (int(user_id), int(conteudo_id), comentario))
    db.commit()
    return jsonify({'status':'success'})

@app.route('/api/progresso', methods=['GET','POST','OPTIONS'])
def video_progresso_endpoint():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id: return jsonify([])
        return jsonify([dict(r) for r in db.execute('SELECT * FROM video_progresso WHERE user_id=?',(user_id,)).fetchall()])
    data = request.json or {}; user_id = data.get('user_id'); conteudo_id = data.get('conteudo_id')
    if not user_id or not conteudo_id: return jsonify({'status':'error','message':'user_id e conteudo_id obrigatórios'}), 400
    db.execute('INSERT OR REPLACE INTO video_progresso (user_id,conteudo_id,assistido,percentual,atualizado_em) VALUES (?,?,?,?,CURRENT_TIMESTAMP)',
               (user_id,conteudo_id,data.get('assistido',1),data.get('percentual',100)))
    db.commit()
    cont = db.execute('SELECT titulo FROM conteudos WHERE id=?',(conteudo_id,)).fetchone()
    log_activity(user_id,'Assistiu ao vídeo',cont['titulo'] if cont else f'Vídeo #{conteudo_id}')
    return jsonify({'status':'success'})

@app.route('/api/admin/progresso', methods=['GET','OPTIONS'])
@require_admin
def admin_progresso():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    try:
        rows = db.execute('SELECT vp.user_id,u.nome as user_nome,vp.conteudo_id,c.titulo as video_titulo,vp.assistido,vp.percentual,vp.atualizado_em FROM video_progresso vp JOIN users u ON u.id=vp.user_id JOIN conteudos c ON c.id=vp.conteudo_id ORDER BY vp.atualizado_em DESC').fetchall()
        return jsonify([dict(r) for r in rows])
    except: return jsonify([])

@app.route('/api/admin/progresso/<int:user_id>', methods=['GET','OPTIONS'])
@require_admin
def admin_progresso_usuario(user_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    try:
        total = db.execute("SELECT COUNT(*) FROM conteudos WHERE categoria='video' AND ativo=1").fetchone()[0]
        assistidos = db.execute('SELECT COUNT(*) FROM video_progresso WHERE user_id=? AND assistido=1',(user_id,)).fetchone()[0]
        rows = db.execute('SELECT vp.conteudo_id,c.titulo,c.secao_id,vp.assistido,vp.percentual,vp.atualizado_em FROM video_progresso vp JOIN conteudos c ON c.id=vp.conteudo_id WHERE vp.user_id=? ORDER BY vp.atualizado_em DESC',(user_id,)).fetchall()
        return jsonify({'total_videos':total,'assistidos':assistidos,'percentual_geral':round((assistidos/total*100) if total>0 else 0),'detalhes':[dict(r) for r in rows]})
    except: return jsonify({'total_videos':0,'assistidos':0,'percentual_geral':0,'detalhes':[]})

if __name__ == '__main__':
    init_db()
    try:
        from migrate_db import migrate
        migrate()
    except Exception as e:
        print(f"Erro na migração: {e}")
    print(f"\n{'='*60}\n 🚀 SERVIDOR API NALIN NAZARETH ATIVO\n 📡 IP Local: http://{ip_local}:5000\n{'='*60}\n")
    tunnel_thread = threading.Thread(target=start_cloudflared_tunnel, daemon=True)
    tunnel_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
