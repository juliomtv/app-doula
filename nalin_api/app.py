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

# ── WEB PUSH (VAPID) ──────────────────────────────────────────────────────────
_VAPID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vapid_keys.json')
_VAPID_KEYS = {}
try:
    with open(_VAPID_FILE) as _f:
        _VAPID_KEYS = json.load(_f)
    print('[VAPID] Chaves carregadas.')
except Exception as _e:
    print(f'[VAPID] Chaves não encontradas: {_e}')

def web_push_send(subscriptions, titulo, mensagem):
    if not _VAPID_KEYS or not subscriptions: return
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        print('[WEBPUSH] pywebpush não instalado'); return
    payload = json.dumps({'title': titulo, 'body': mensagem, 'icon': '/icons/icon-192.png'})
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={'endpoint': sub['endpoint'], 'keys': {'p256dh': sub['p256dh'], 'auth': sub['auth']}},
                data=payload,
                vapid_private_key=_VAPID_KEYS['private'],
                vapid_claims={'sub': 'mailto:contato@appdoula.com'}
            )
        except Exception as _e:
            print(f'[WEBPUSH] Erro: {_e}')

# ── FIREBASE ADMIN ────────────────────────────────────────────────────────────
try:
    import firebase_admin
    from firebase_admin import credentials as fb_credentials, messaging as fb_messaging
    _SA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'firebase-service-account.json')
    if os.path.exists(_SA_PATH):
        firebase_admin.initialize_app(fb_credentials.Certificate(_SA_PATH))
        FCM_OK = True
        print('[FCM] Firebase inicializado com sucesso.')
    else:
        FCM_OK = False
        print('[FCM] firebase-service-account.json não encontrado.')
except Exception as _e:
    FCM_OK = False
    print(f'[FCM] Erro ao inicializar Firebase: {_e}')

def fcm_send(tokens, titulo, mensagem):
    if not FCM_OK or not tokens: return
    tokens = [t for t in tokens if t]
    if not tokens: return
    try:
        if len(tokens) == 1:
            fb_messaging.send(fb_messaging.Message(
                notification=fb_messaging.Notification(title=titulo, body=mensagem),
                token=tokens[0],
                android=fb_messaging.AndroidConfig(priority='high',
                    notification=fb_messaging.AndroidNotification(channel_id='doula_notif', sound='default'))
            ))
        else:
            fb_messaging.send_each_for_multicast(fb_messaging.MulticastMessage(
                notification=fb_messaging.Notification(title=titulo, body=mensagem),
                tokens=tokens,
                android=fb_messaging.AndroidConfig(priority='high',
                    notification=fb_messaging.AndroidNotification(channel_id='doula_notif', sound='default'))
            ))
        print(f'[FCM] Enviado para {len(tokens)} dispositivo(s).')
    except Exception as e:
        print(f'[FCM] Erro ao enviar: {e}')

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
APK_DIR = os.path.join(os.path.dirname(BASE_DIR), 'downloads')
APK_CONFIG_PATH = os.path.join(os.path.dirname(BASE_DIR), 'apk_config.json')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB para APKs
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
os.makedirs(APK_DIR, exist_ok=True)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close(); return ip
    except: return "127.0.0.1"

ip_local = get_local_ip()
base_url = f"http://{ip_local}:5000"
TUNNEL_FIXO = 'https://doulanalinnazareth.com'
tunnel_url = TUNNEL_FIXO

def start_cloudflared_tunnel():
    try:
        check = subprocess.run(['cloudflared', '--version'], capture_output=True, text=True)
        if check.returncode != 0:
            print('[TUNNEL] cloudflared não encontrado.')
            return
        print(f"\n{'='*60}\n 🌍 URL PÚBLICA: {TUNNEL_FIXO}\n{'='*60}\n")
        subprocess.Popen(
            ['cloudflared', 'tunnel', '--config',
             os.path.expanduser('~/.cloudflared/config.yml'), 'run', 'nalin-doula'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"[TUNNEL] Erro: {e}")

CORS(app, resources={
    r"/api/*": {"origins": "*", "methods": ["GET","POST","PUT","DELETE","OPTIONS"], "allow_headers": ["Content-Type","Authorization"]},
    r"/versao_app": {"origins": "*"}, r"/server-info": {"origins": "*"},
    r"/ota/*": {"origins": "*"}, r"/uploads/*": {"origins": "*"}, r"/downloads/*": {"origins": "*"}
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
    if request.method != 'OPTIONS':
        import sys
        print(f">> REQUEST: {request.method} {request.path}", flush=True, file=sys.stderr)
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
        # Migration: tabelas de comunidade
        db.executescript("""
            CREATE TABLE IF NOT EXISTS comunidade_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                texto TEXT NOT NULL,
                categoria TEXT DEFAULT 'geral',
                ativo INTEGER DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS comunidade_comentarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                texto TEXT NOT NULL,
                ativo INTEGER DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES comunidade_posts(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS comunidade_curtidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(post_id, user_id),
                FOREIGN KEY (post_id) REFERENCES comunidade_posts(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS comunidade_comentarios_curtidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comentario_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(comentario_id, user_id),
                FOREIGN KEY (comentario_id) REFERENCES comunidade_comentarios(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                endpoint TEXT NOT NULL,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, endpoint),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
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

def _get_apk_config():
    try:
        with open(APK_CONFIG_PATH, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def _save_apk_config(data):
    with open(APK_CONFIG_PATH, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

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
    ver = get_app_version(); ver['hash'] = get_index_hash()
    apk = _get_apk_config()
    if apk:
        ver['apk_versionCode'] = apk.get('versionCode', 0)
        ver['apk_versionName'] = apk.get('versionName', '')
        ver['apk_url'] = apk.get('url', '')
        ver['apk_notas'] = apk.get('notas', '')
    return jsonify(ver)

@app.route('/downloads/<filename>', methods=['GET','OPTIONS'])
def serve_apk(filename):
    if request.method == 'OPTIONS': return '', 204
    if not filename.endswith('.apk'):
        return jsonify({'error': 'Not found'}), 404
    return send_from_directory(APK_DIR, filename, as_attachment=True,
                               mimetype='application/vnd.android.package-archive')

@app.route('/api/admin/apk/info', methods=['GET','OPTIONS'])
@require_admin
def apk_info():
    if request.method == 'OPTIONS': return '', 204
    return jsonify(_get_apk_config() or {})

@app.route('/api/admin/apk/upload', methods=['POST','OPTIONS'])
@require_admin
def upload_apk():
    if request.method == 'OPTIONS': return '', 204
    if 'arquivo' not in request.files:
        return jsonify({'error': 'Arquivo não enviado'}), 400
    f = request.files['arquivo']
    if not f.filename.endswith('.apk'):
        return jsonify({'error': 'Apenas arquivos .apk são aceitos'}), 400
    try:
        version_code = int(request.form.get('versionCode', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'versionCode inválido'}), 400
    version_name = request.form.get('versionName', '').strip()
    notas = request.form.get('notas', '').strip()
    if not version_code or not version_name:
        return jsonify({'error': 'versionCode e versionName são obrigatórios'}), 400
    filename = 'doula-nalin-nazareth-latest.apk'
    f.save(os.path.join(APK_DIR, filename))
    host = request.host_url.rstrip('/')
    apk_url = f'{host}/downloads/{filename}'
    _save_apk_config({
        'versionCode': version_code,
        'versionName': version_name,
        'notas': notas,
        'url': apk_url,
        'atualizado_em': datetime.now(timezone.utc).isoformat()
    })
    return jsonify({'status': 'success', 'url': apk_url})

@app.route('/api/admin/apk/notificar', methods=['POST','OPTIONS'])
@require_admin
def apk_notificar():
    if request.method == 'OPTIONS': return '', 204
    cfg = _get_apk_config()
    if not cfg:
        return jsonify({'error': 'Nenhum APK cadastrado ainda'}), 400
    db = get_db()
    tokens = [r['fcm_token'] for r in db.execute(
        "SELECT fcm_token FROM users WHERE plataforma='android' AND ativo=1 AND fcm_token IS NOT NULL AND fcm_token != ''"
    ).fetchall()]
    if not tokens:
        return jsonify({'status': 'ok', 'enviado_para': 0, 'aviso': 'Nenhum token Android encontrado'})
    if not FCM_OK:
        return jsonify({'error': 'Firebase não configurado no servidor'}), 500
    titulo = f"Nova versão {cfg.get('versionName','')} disponível"
    mensagem = cfg.get('notas') or 'Toque para baixar e instalar a atualização.'
    apk_data = {
        'type': 'apk_update',
        'apk_url': cfg.get('url', ''),
        'apk_version_name': cfg.get('versionName', ''),
        'apk_version_code': str(cfg.get('versionCode', ''))
    }
    try:
        msg = fb_messaging.MulticastMessage(
            notification=fb_messaging.Notification(title=titulo, body=mensagem),
            data=apk_data,
            tokens=tokens,
            android=fb_messaging.AndroidConfig(priority='high',
                notification=fb_messaging.AndroidNotification(channel_id='doula_notif', sound='default'))
        )
        fb_messaging.send_each_for_multicast(msg)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'success', 'enviado_para': len(tokens)})

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

@app.route('/', methods=['GET'])
@app.route('/index.html', methods=['GET'])
def serve_index():
    return send_from_directory(WWW_DIR, 'index.html')

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

# ── PWA ──────────────────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
@app.route('/app', methods=['GET'])
@app.route('/app.html', methods=['GET'])
def pwa_index():
    resp = send_from_directory(WWW_DIR, 'index.html')
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.route('/manifest.json', methods=['GET'])
def pwa_manifest():
    return send_from_directory(WWW_DIR, 'manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js', methods=['GET'])
def pwa_sw():
    resp = send_from_directory(WWW_DIR, 'sw.js', mimetype='application/javascript')
    resp.headers['Service-Worker-Allowed'] = '/'
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.route('/icons/<path:filename>', methods=['GET'])
def pwa_icons(filename):
    icons_dir = os.path.join(WWW_DIR, 'icons')
    return send_from_directory(icons_dir, filename)

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

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    nome  = data.get('nome', '').strip()
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '').strip()
    bebe  = data.get('bebe', '').strip()
    dpp   = data.get('dpp', '').strip()
    if not nome or not email or not senha or not dpp:
        return jsonify({"status":"error","message":"Nome, e-mail, senha e DPP são obrigatórios."}), 400
    if len(senha) < 6:
        return jsonify({"status":"error","message":"Senha deve ter pelo menos 6 caracteres."}), 400
    db = get_db()
    if db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone():
        return jsonify({"status":"error","message":"E-mail já cadastrado."}), 400
    db.execute(
        'INSERT INTO users (nome,email,senha,bebe,dpp,tipo,acesso_videos,acesso_ebooks,senha_provisoria,ativo) VALUES (?,?,?,?,?,?,?,?,?,?)',
        (nome, email, hash_password(senha), bebe, dpp, 'publico', 0, 0, 0, 1)
    )
    db.commit()
    user = dict(db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone())
    return jsonify({"status":"success","user":user})

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
        # Marca senha como provisória para forçar troca no primeiro login
        db.execute('UPDATE users SET senha_provisoria=1 WHERE id=?', (cursor.lastrowid,))
        db.execute('INSERT INTO logs_atividade (user_id,acao) VALUES (?,?)',(cursor.lastrowid,'Nova doulanda cadastrada'))
    db.commit(); return jsonify({"status":"success"})

@app.route('/api/users/change-password', methods=['POST', 'OPTIONS'])
def user_change_password():
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id')
    nova_senha = data.get('nova_senha', '').strip()
    if not user_id or not nova_senha:
        return jsonify({"status":"error","message":"Dados incompletos."}), 400
    if len(nova_senha) < 6:
        return jsonify({"status":"error","message":"A senha deve ter pelo menos 6 caracteres."}), 400
    db = get_db()
    db.execute('UPDATE users SET senha=?, senha_provisoria=0 WHERE id=?', (hash_password(nova_senha), user_id))
    db.commit()
    return jsonify({"status":"success"})

@app.route('/api/admin/users/<int:user_id>/reset-senha', methods=['POST', 'OPTIONS'])
@require_admin
def admin_reset_senha(user_id):
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    nova_senha = data.get('nova_senha', '').strip()
    if not nova_senha:
        return jsonify({"status":"error","message":"Informe a nova senha."}), 400
    db = get_db()
    db.execute('UPDATE users SET senha=?, senha_provisoria=1 WHERE id=?', (hash_password(nova_senha), user_id))
    db.commit()
    return jsonify({"status":"success"})

@app.route('/api/users/<int:user_id>', methods=['DELETE', 'OPTIONS'])
@require_admin
def delete_user(user_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    db.execute('DELETE FROM users WHERE id=?', (user_id,))
    db.commit()
    return jsonify({"status":"success"})

@app.route('/api/users/<int:user_id>/toggle', methods=['POST'])
@require_admin
def toggle_user(user_id):
    db = get_db(); db.execute('UPDATE users SET ativo = NOT ativo WHERE id = ?',(user_id,)); db.commit()
    return jsonify({"status":"success"})

@app.route('/api/admin/users/<int:user_id>/tornar-doulanda', methods=['POST', 'OPTIONS'])
@require_admin
def tornar_doulanda(user_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    db.execute("UPDATE users SET tipo='doulanda', acesso_videos=1, acesso_ebooks=1 WHERE id=?", (user_id,))
    db.commit()
    return jsonify({"status":"success"})

@app.route('/api/admin/users/<int:user_id>/acesso', methods=['POST', 'OPTIONS'])
@require_admin
def toggle_acesso(user_id):
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    campo = data.get('campo')
    if campo not in ('acesso_videos', 'acesso_ebooks'):
        return jsonify({'status': 'error', 'message': 'Campo inválido'}), 400
    valor = 1 if data.get('valor') else 0
    db = get_db()
    db.execute(f'UPDATE users SET {campo}=? WHERE id=?', (valor, user_id))
    db.commit()
    return jsonify({'status': 'success'})

# ── WEB PUSH ENDPOINTS ───────────────────────────────────────────────────────
@app.route('/api/vapid-public-key', methods=['GET', 'OPTIONS'])
def vapid_public_key():
    if request.method == 'OPTIONS': return '', 204
    return jsonify({'publicKey': _VAPID_KEYS.get('public', '')})

@app.route('/api/users/web_push_subscription', methods=['POST', 'OPTIONS'])
def save_web_push_subscription():
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id')
    endpoint = (data.get('endpoint') or '').strip()
    p256dh = (data.get('p256dh') or '').strip()
    auth = (data.get('auth') or '').strip()
    if not user_id or not endpoint or not p256dh or not auth:
        return jsonify({'error': 'Dados incompletos'}), 400
    db = get_db()
    db.execute("""
        INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
        VALUES (?,?,?,?)
        ON CONFLICT(user_id, endpoint) DO UPDATE SET p256dh=excluded.p256dh, auth=excluded.auth
    """, (user_id, endpoint, p256dh, auth))
    db.commit()
    return jsonify({'status': 'success'})

# ── FCM TOKEN ────────────────────────────────────────────────────────────────
@app.route('/api/users/fcm_token', methods=['POST', 'OPTIONS'])
def save_fcm_token():
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id')
    token = (data.get('token') or '').strip()
    if not user_id or not token: return jsonify({'status': 'error'}), 400
    db = get_db()
    db.execute('UPDATE users SET fcm_token=?, plataforma=? WHERE id=?', (token, 'android', user_id))
    db.commit()
    return jsonify({'status': 'success'})

@app.route('/api/users/plataforma', methods=['POST', 'OPTIONS'])
def save_plataforma():
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id')
    plataforma = data.get('plataforma', 'pwa')
    if not user_id or plataforma not in ('android', 'pwa'): return jsonify({'status': 'error'}), 400
    db = get_db()
    # Só atualiza para pwa se ainda não for android (não sobrescreve token FCM registrado)
    db.execute("UPDATE users SET plataforma=? WHERE id=? AND (plataforma IS NULL OR plataforma='pwa')", (plataforma, user_id))
    db.commit()
    return jsonify({'status': 'success'})

# ── NOTIFICAÇÕES ──────────────────────────────────────────────────────────────
@app.route('/api/notificacoes', methods=['GET', 'OPTIONS'])
def get_notificacoes():
    if request.method == 'OPTIONS': return '', 204
    user_id = request.args.get('user_id', type=int)
    if not user_id: return jsonify([])
    db = get_db()
    rows = db.execute(
        'SELECT * FROM notificacoes WHERE user_id=? ORDER BY criado_em DESC LIMIT 50', (user_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/notificacoes/lidas', methods=['POST', 'OPTIONS'])
def marcar_lidas():
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id')
    if not user_id: return jsonify({'status': 'error'}), 400
    get_db().execute('UPDATE notificacoes SET lida=1 WHERE user_id=?', (user_id,))
    get_db().commit()
    return jsonify({'status': 'success'})

@app.route('/api/admin/notificacoes', methods=['POST', 'OPTIONS'])
@require_admin
def admin_send_notificacao():
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    titulo  = (data.get('titulo') or '').strip()
    mensagem = (data.get('mensagem') or '').strip()
    user_id  = data.get('user_id')  # None = todas
    if not titulo or not mensagem:
        return jsonify({'status': 'error', 'message': 'Título e mensagem obrigatórios'}), 400
    db = get_db()
    if user_id:
        user = db.execute('SELECT id, fcm_token FROM users WHERE id=? AND ativo=1', (user_id,)).fetchone()
        if not user: return jsonify({'status': 'error', 'message': 'Usuária não encontrada'}), 404
        db.execute('INSERT INTO notificacoes (user_id,titulo,mensagem) VALUES (?,?,?)', (user_id, titulo, mensagem))
        db.commit()
        fcm_send([user['fcm_token']], titulo, mensagem)
    else:
        users = db.execute('SELECT id, fcm_token FROM users WHERE ativo=1').fetchall()
        for u in users:
            db.execute('INSERT INTO notificacoes (user_id,titulo,mensagem) VALUES (?,?,?)', (u['id'], titulo, mensagem))
        db.commit()
        fcm_send([u['fcm_token'] for u in users], titulo, mensagem)
    return jsonify({'status': 'success', 'enviado_para': user_id or 'todas'})

@app.route('/api/admin/notificacoes', methods=['GET', 'OPTIONS'])
@require_admin
def admin_list_notificacoes():
    if request.method == 'OPTIONS': return '', 204
    rows = get_db().execute(
        '''SELECT n.*, u.nome as user_nome FROM notificacoes n
           LEFT JOIN users u ON n.user_id = u.id
           ORDER BY n.criado_em DESC LIMIT 100'''
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/users/me', methods=['GET', 'OPTIONS'])
def users_me():
    if request.method == 'OPTIONS': return '', 204
    user_id = request.args.get('id', type=int)
    if not user_id: return jsonify({'status': 'error', 'message': 'ID ausente'}), 400
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id=? AND ativo=1', (user_id,)).fetchone()
    if not user: return jsonify({'status': 'error', 'message': 'Não encontrado'}), 404
    return jsonify({'status': 'success', 'user': dict(user)})

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
    import sys
    print(f"\n[EBOOK] form_keys={list(request.form.keys())}", flush=True, file=sys.stderr)
    print(f"[EBOOK] form_data={dict(request.form)}", flush=True, file=sys.stderr)
    print(f"[EBOOK] files={list(request.files.keys())}", flush=True, file=sys.stderr)

    titulo = (request.form.get("titulo") or "").strip()
    if not titulo: return jsonify({"status":"error","message":"Título obrigatório."}), 400
    descricao = request.form.get("descricao","")
    categoria = (request.form.get("categoria") or "").strip() or "Geral"
    capa = request.files.get("capa")
    db = get_db()

    url_capa = None
    if capa and capa.filename and allowed_file(capa.filename):
        capa_filename = "capa_" + secure_filename(capa.filename)
        capa.save(os.path.join(app.config["UPLOAD_FOLDER"], capa_filename))
        url_capa = f"/uploads/{capa_filename}"

    # Se vier ebook_id no form → é EDIÇÃO
    ebook_id_raw = request.form.get("ebook_id", "")
    import sys
    print(f"[EBOOK] ebook_id_raw={repr(ebook_id_raw)}", flush=True, file=sys.stderr)
    try:
        ebook_id = int(ebook_id_raw) if ebook_id_raw.strip() else None
    except (ValueError, TypeError):
        ebook_id = None
    print(f"[EBOOK] ebook_id={ebook_id}, titulo={repr(titulo)}, categoria={repr(categoria)}", flush=True, file=sys.stderr)
    if ebook_id:
        if url_capa:
            db.execute("UPDATE ebooks SET titulo=?,descricao=?,categoria=?,url_capa=? WHERE id=?",
                       (titulo, descricao, categoria, url_capa, ebook_id))
        else:
            db.execute("UPDATE ebooks SET titulo=?,descricao=?,categoria=? WHERE id=?",
                       (titulo, descricao, categoria, ebook_id))
        db.commit()
        return jsonify({"status":"success"})

    # Sem ebook_id → é CRIAÇÃO
    file = request.files.get("file")
    if not file or not file.filename: return jsonify({"status":"error","message":"Nenhum arquivo enviado."}), 400
    if not allowed_file(file.filename): return jsonify({"status":"error","message":"Tipo de arquivo não permitido."}), 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    db.execute("INSERT INTO ebooks (titulo,descricao,categoria,url_pdf,url_capa) VALUES (?,?,?,?,?)",
               (titulo, descricao, categoria, f"/uploads/{filename}", url_capa))
    db.commit()
    return jsonify({"status":"success"})

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
    try:
        plano_valor = float(m['plano_valor']) if 'plano_valor' in m else _PLANO_VALOR_FALLBACK
    except (ValueError, TypeError):
        plano_valor = _PLANO_VALOR_FALLBACK
    return jsonify({
        'whatsapp_numero': m.get('whatsapp_numero', ''),
        'whatsapp_mensagem': m.get('whatsapp_mensagem', 'Olá!'),
        'instagram_url': m.get('instagram_url', ''),
        'email_contato': m.get('email_contato', ''),
        'plano_valor': plano_valor,
        'plano_nome': m.get('plano_nome') or _PLANO_NOME_FALLBACK,
    })

@app.route('/api/admin/config', methods=['GET','POST','OPTIONS'])
@require_admin
def admin_config():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    if request.method == 'GET':
        return jsonify([dict(r) for r in db.execute('SELECT chave,valor FROM config_global').fetchall()])
    data = request.json or {}
    for campo in ['whatsapp_numero','whatsapp_mensagem','instagram_url','email_contato','plano_nome']:
        if campo in data:
            db.execute("INSERT OR REPLACE INTO config_global (chave,valor,atualizado_em) VALUES (?,?,CURRENT_TIMESTAMP)",(campo,data[campo]))
    if 'plano_valor' in data:
        try:
            val = float(str(data['plano_valor']).replace(',','.'))
            if val > 0:
                db.execute("INSERT OR REPLACE INTO config_global (chave,valor,atualizado_em) VALUES (?,?,CURRENT_TIMESTAMP)",('plano_valor', str(round(val, 2))))
        except (ValueError, TypeError):
            pass
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
        uid = int(user_id)
        today = datetime.now().strftime('%Y-%m-%d')
        db.execute('DELETE FROM agenda WHERE user_id=? AND data_evento < ?', (uid, today))
        db.commit()
        rows = db.execute('SELECT * FROM agenda WHERE user_id=? ORDER BY data_evento ASC, hora_evento ASC', (uid,)).fetchall()
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

@app.route('/api/admin/contracoes/monitoramento', methods=['GET', 'OPTIONS'])
@require_admin
def admin_monitoramento_contracoes():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    users = db.execute("SELECT id, nome FROM users WHERE ativo=1").fetchall()
    resultado = []
    agora = datetime.now(timezone.utc)
    for u in users:
        rows = db.execute(
            "SELECT start_time, end_time, duration_sec, interval_min FROM contracoes WHERE user_id=? ORDER BY start_time DESC LIMIT 20",
            (u['id'],)
        ).fetchall()
        if not rows: continue
        total = len(rows)
        duracoes = [r['duration_sec'] for r in rows if r['duration_sec'] and r['duration_sec'] > 0]
        intervalos = [r['interval_min'] for r in rows if r['interval_min'] and r['interval_min'] > 0]
        if not duracoes: continue
        avg_dur = round(sum(duracoes) / len(duracoes))
        avg_int = round(sum(intervalos) / len(intervalos), 1) if intervalos else None
        ultima = rows[0]['start_time'] or rows[0]['end_time'] or ''
        # Verifica se padrão se mantém por 60 min (para "trabalho de parto provável")
        padrao_60min = False
        if len(rows) >= 3 and ultima:
            try:
                dt_ultima = datetime.fromisoformat(ultima.replace('Z','').rstrip('+00:00'))
                dt_primeira = datetime.fromisoformat((rows[min(len(rows)-1,9)]['start_time'] or '').replace('Z','').rstrip('+00:00'))
                padrao_60min = (dt_ultima - dt_primeira).total_seconds() >= 3600
            except: pass
        # Determina status
        status = 'normal'
        if avg_int is not None:
            if avg_int < 3 and total > 10:
                status = 'prioridade_alta'
            elif avg_int < 5 and avg_dur >= 60 and padrao_60min:
                status = 'trabalho_parto'
            elif total >= 5 and avg_int < 7 and avg_dur >= 40:
                status = 'atencao'
            elif total >= 3 and avg_int < 10:
                status = 'observacao'
        if status == 'normal': continue
        resultado.append({
            'user_id': u['id'],
            'nome': _nome_curto(u['nome']),
            'status': status,
            'avg_dur_sec': avg_dur,
            'avg_int_min': avg_int,
            'total': total,
            'ultima': ultima
        })
    ordem = {'prioridade_alta': 0, 'trabalho_parto': 1, 'atencao': 2, 'observacao': 3}
    resultado.sort(key=lambda x: ordem.get(x['status'], 9))
    return jsonify({'monitoramento': resultado})

@app.route('/api/admin/contracoes/<int:user_id>', methods=['DELETE','OPTIONS'])
@require_admin
def admin_limpar_contracoes(user_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    db.execute("DELETE FROM contracoes WHERE user_id=?", (user_id,))
    db.commit()
    return jsonify({'ok': True})

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

def _gerar_icones_pwa():
    """Gera ícones PNG simples para o PWA usando apenas stdlib."""
    import struct, zlib, math
    def _png(path, size):
        if os.path.exists(path): return
        cx = cy = (size - 1) / 2
        r_circ = size * 0.40
        rows = bytearray()
        for y in range(size):
            rows.append(0)  # filtro PNG
            for x in range(size):
                if math.hypot(x - cx, y - cy) < r_circ:
                    rows += b'\xfb\xf7\xf4'  # cream #FBF7F4
                else:
                    rows += b'\xc9\x90\x7a'  # rose  #C9907A
        def chunk(t, d):
            c = t + d
            return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        png = (b'\x89PNG\r\n\x1a\n'
               + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
               + chunk(b'IDAT', zlib.compress(bytes(rows), 6))
               + chunk(b'IEND', b''))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f: f.write(png)
        print(f'[PWA] Ícone gerado: {path}')
    icons = os.path.join(WWW_DIR, 'icons')
    _png(os.path.join(icons, 'icon-192.png'), 192)
    _png(os.path.join(icons, 'icon-512.png'), 512)
    _png(os.path.join(icons, 'icon-180.png'), 180)

# ══════════════════════════════════════════════════════════════════
# PAGAMENTO — ASAAS
# ══════════════════════════════════════════════════════════════════
try:
    from nalin_api.config_pagamento import PLANO_VALOR, PLANO_NOME, ASAAS_WEBHOOK_TOKEN
    from nalin_api import asaas as _asaas
    _ASAAS_OK = True
except ImportError:
    try:
        from config_pagamento import PLANO_VALOR, PLANO_NOME, ASAAS_WEBHOOK_TOKEN
        import asaas as _asaas
        _ASAAS_OK = True
    except ImportError:
        _ASAAS_OK = False
        ASAAS_WEBHOOK_TOKEN = ''

_PLANO_VALOR_FALLBACK = PLANO_VALOR if _ASAAS_OK else 19.90
_PLANO_NOME_FALLBACK  = PLANO_NOME  if _ASAAS_OK else 'Acesso Premium - App Doula Nalin'

def get_plano_config():
    """Lê valor e nome do plano do banco (config_global), com fallback para config_pagamento.py."""
    db = get_db()
    rows = {r['chave']: r['valor'] for r in db.execute(
        "SELECT chave,valor FROM config_global WHERE chave IN ('plano_valor','plano_nome')"
    ).fetchall()}
    try:
        valor = float(rows['plano_valor']) if 'plano_valor' in rows else _PLANO_VALOR_FALLBACK
    except (ValueError, TypeError):
        valor = _PLANO_VALOR_FALLBACK
    nome = rows.get('plano_nome') or _PLANO_NOME_FALLBACK
    return valor, nome

@app.route('/api/pagamento/iniciar', methods=['POST', 'OPTIONS'])
def iniciar_pagamento():
    """Cria cliente + assinatura no ASAAS e retorna o link de pagamento."""
    if request.method == 'OPTIONS': return '', 204
    if not _ASAAS_OK:
        return jsonify({"status":"error","message":"Módulo de pagamento não configurado."}), 503
    data = request.json or {}
    user_id = data.get('user_id')
    billing_type = data.get('billing_type', 'PIX').upper()
    if billing_type not in ('BOLETO', 'CREDIT_CARD', 'PIX'):
        billing_type = 'PIX'
    cpf_fornecido = data.get('cpf', '').replace('.','').replace('-','').replace(' ','')
    if billing_type == 'BOLETO' and len(cpf_fornecido) < 11:
        return jsonify({"status":"error","message":"CPF obrigatório para pagamento via Boleto."}), 400
    if not user_id:
        return jsonify({"status":"error","message":"user_id obrigatório."}), 400
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    if not user:
        return jsonify({"status":"error","message":"Usuária não encontrada."}), 404
    user = dict(user)
    try:
        customer_id = user.get('asaas_customer_id')
        # Verifica se o cliente ainda existe e não foi removido no ASAAS
        if customer_id:
            try:
                cliente_existente = _asaas.buscar_cliente_por_id(customer_id)
                if not cliente_existente:
                    customer_id = None  # Removido ou inválido
            except Exception:
                customer_id = None
        if not customer_id:
            cliente = _asaas.buscar_cliente_por_email(user['email'])
            if not cliente:
                cliente = _asaas.criar_cliente(user['nome'], user['email'], cpf_fornecido or user.get('cpf'))
            customer_id = cliente['id']
            db.execute('UPDATE users SET asaas_customer_id=? WHERE id=?', (customer_id, user_id))
            db.commit()
        # Atualiza CPF no ASAAS e no banco se foi fornecido
        if cpf_fornecido:
            try:
                _asaas.atualizar_cpf_cliente(customer_id, cpf_fornecido)
            except Exception:
                pass
            db.execute('UPDATE users SET cpf=? WHERE id=?', (cpf_fornecido, user_id))
            db.commit()
        plano_valor, plano_nome = get_plano_config()
        cobranca = _asaas.criar_cobranca(customer_id, plano_valor, plano_nome, billing_type)
        payment_id = cobranca.get('id')
        invoice_url = cobranca.get('invoiceUrl')
        db.execute('UPDATE users SET asaas_subscription_id=?, assinatura_status=? WHERE id=?',
                   (payment_id, 'pendente', user_id))
        db.commit()
        resp = {"status":"success","payment_id":payment_id,"invoice_url":invoice_url,"billing_type":billing_type}
        if billing_type == 'PIX' and payment_id:
            try:
                pix = _asaas.buscar_pix_qrcode(payment_id)
                if pix:
                    resp['pix_qrcode'] = pix.get('encodedImage')
                    resp['pix_payload'] = pix.get('payload')
            except Exception:
                pass
        return jsonify(resp)
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500

@app.route('/api/pagamento/webhook', methods=['POST'])
def pagamento_webhook():
    """Recebe notificações do ASAAS e atualiza acesso da usuária."""
    token_recebido = request.headers.get('asaas-access-token', '')
    if ASAAS_WEBHOOK_TOKEN and token_recebido != ASAAS_WEBHOOK_TOKEN:
        return '', 401
    data = request.json or {}
    evento = data.get('event', '')
    payment = data.get('payment', {})
    subscription_id = payment.get('subscription') or data.get('subscription', {}).get('id')
    payment_id = payment.get('id')
    db = get_db()
    # Busca por subscription_id (assinatura) ou payment_id (cobrança única)
    user = None
    if subscription_id:
        user = db.execute('SELECT * FROM users WHERE asaas_subscription_id=?', (subscription_id,)).fetchone()
    if not user and payment_id:
        user = db.execute('SELECT * FROM users WHERE asaas_subscription_id=?', (payment_id,)).fetchone()
    if not user:
        return '', 200
    if evento in ('PAYMENT_CONFIRMED', 'PAYMENT_RECEIVED'):
        db.execute("UPDATE users SET assinatura_status='ativa', acesso_videos=1, acesso_ebooks=1 WHERE id=?", (user['id'],))
    elif evento in ('PAYMENT_OVERDUE', 'PAYMENT_REFUNDED', 'PAYMENT_CHARGEBACK', 'SUBSCRIPTION_INACTIVATED'):
        db.execute("UPDATE users SET assinatura_status='vencida', acesso_videos=0, acesso_ebooks=0 WHERE id=?", (user['id'],))
    db.commit()
    return '', 200

def _nome_curto(nome):
    p = (nome or '').strip().split()
    return (p[0] + ' ' + p[-1]) if len(p) > 1 else (nome or '').strip()

def _eh_nalin(user_id):
    try:
        db = get_db()
        u = db.execute("SELECT tipo FROM users WHERE id=?", (user_id,)).fetchone()
        return u and u['tipo'] in ('doula', 'admin', 'nalin')
    except: return False

def _get_nalin_user(db):
    return db.execute("SELECT id, fcm_token FROM users WHERE tipo IN ('doula','admin','nalin') AND ativo=1 LIMIT 1").fetchone()

def _notif_user(db, user_id, titulo, mensagem):
    try:
        db.execute("INSERT INTO notificacoes (user_id,titulo,mensagem) VALUES (?,?,?)", (user_id, titulo, mensagem))
        u = db.execute("SELECT fcm_token FROM users WHERE id=? AND fcm_token IS NOT NULL AND fcm_token!=''", (user_id,)).fetchone()
        if u: fcm_send([u['fcm_token']], titulo, mensagem)
        subs = db.execute("SELECT endpoint,p256dh,auth FROM push_subscriptions WHERE user_id=?", (user_id,)).fetchall()
        if subs: web_push_send([dict(s) for s in subs], titulo, mensagem)
    except Exception as e:
        print(f'[NOTIF] Erro: {e}')

def _notif_todos(db, titulo, mensagem, excluir_ids=None):
    try:
        excluir_ids = excluir_ids or []
        users = db.execute("SELECT id, fcm_token FROM users WHERE ativo=1").fetchall()
        tokens = []
        all_subs = []
        for u in users:
            if u['id'] in excluir_ids: continue
            db.execute("INSERT INTO notificacoes (user_id,titulo,mensagem) VALUES (?,?,?)", (u['id'], titulo, mensagem))
            if u['fcm_token']: tokens.append(u['fcm_token'])
            subs = db.execute("SELECT endpoint,p256dh,auth FROM push_subscriptions WHERE user_id=?", (u['id'],)).fetchall()
            all_subs.extend([dict(s) for s in subs])
        if tokens: fcm_send(tokens, titulo, mensagem)
        if all_subs: web_push_send(all_subs, titulo, mensagem)
    except Exception as e:
        print(f'[NOTIF] Erro broadcast: {e}')

# ── COMUNIDADE — POSTS ───────────────────────────────────────────────────────

@app.route('/api/comunidade/posts', methods=['GET', 'OPTIONS'])
def listar_posts():
    if request.method == 'OPTIONS': return '', 204
    categoria = request.args.get('categoria', '')
    page = max(1, int(request.args.get('page', 1)))
    user_id = request.args.get('user_id', 0, type=int)
    limit = 20; offset = (page - 1) * limit
    db = get_db()
    where = "WHERE p.ativo=1"
    params = []
    if categoria and categoria != 'todos':
        where += " AND p.categoria=?"; params.append(categoria)
    rows = db.execute(f"""
        SELECT p.id, p.user_id, p.texto, p.categoria, p.criado_em,
               u.nome AS autor_nome, u.tipo AS autor_tipo,
               (SELECT COUNT(*) FROM comunidade_comentarios c WHERE c.post_id=p.id AND c.ativo=1) AS total_comentarios,
               (SELECT COUNT(*) FROM comunidade_curtidas ct WHERE ct.post_id=p.id) AS curtidas,
               CASE WHEN (SELECT COUNT(*) FROM comunidade_curtidas ct WHERE ct.post_id=p.id AND ct.user_id=?) > 0 THEN 1 ELSE 0 END AS curtiu
        FROM comunidade_posts p
        JOIN users u ON u.id=p.user_id
        {where}
        ORDER BY p.criado_em DESC
        LIMIT ? OFFSET ?
    """, [user_id] + params + [limit, offset]).fetchall()
    posts = [dict(r) for r in rows]
    for p in posts:
        p['autor_nome'] = _nome_curto(p['autor_nome'])
    return jsonify({'posts': posts})

@app.route('/api/comunidade/posts', methods=['POST', 'OPTIONS'])
def criar_post():
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id'); texto = (data.get('texto') or '').strip()
    categoria = data.get('categoria', 'geral')
    if categoria not in ('geral', 'doacao', 'duvida', 'experiencia'): categoria = 'geral'
    if not user_id or not texto: return jsonify({'error': 'Dados incompletos'}), 400
    if len(texto) > 1000: return jsonify({'error': 'Texto muito longo (máx. 1000 caracteres)'}), 400
    db = get_db()
    if not db.execute("SELECT id FROM users WHERE id=? AND ativo=1", (user_id,)).fetchone():
        return jsonify({'error': 'Usuário não encontrado'}), 404
    cur = db.execute("INSERT INTO comunidade_posts (user_id,texto,categoria) VALUES (?,?,?)", (user_id, texto, categoria))
    db.commit()
    autor = db.execute("SELECT nome, tipo FROM users WHERE id=?", (user_id,)).fetchone()
    nome_curto = _nome_curto(autor['nome']) if autor else 'Alguém'
    is_nalin = autor and autor['tipo'] in ('doula', 'admin', 'nalin')
    if is_nalin:
        _notif_todos(db, '🌸 Nova mensagem da Nalin', texto[:80] + ('...' if len(texto) > 80 else ''), excluir_ids=[user_id])
    else:
        nalin = _get_nalin_user(db)
        if nalin:
            _notif_user(db, nalin['id'], f'💬 {nome_curto} postou na comunidade', texto[:80] + ('...' if len(texto) > 80 else ''))
    db.commit()
    return jsonify({'status': 'success', 'id': cur.lastrowid})

@app.route('/api/comunidade/posts/<int:post_id>', methods=['DELETE', 'OPTIONS'])
def deletar_post(post_id):
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id')
    db = get_db()
    post = db.execute("SELECT user_id FROM comunidade_posts WHERE id=?", (post_id,)).fetchone()
    if not post: return jsonify({'error': 'Post não encontrado'}), 404
    # Permite deletar se for o próprio autor ou admin
    auth = request.headers.get('Authorization', '')
    is_admin = False
    if auth.startswith('Bearer '):
        try:
            jwt.decode(auth.split(' ', 1)[1], JWT_SECRET, algorithms=['HS256'])
            is_admin = True
        except: pass
    if not is_admin and (not user_id or int(user_id) != post['user_id']):
        return jsonify({'error': 'Sem permissão'}), 403
    db.execute("UPDATE comunidade_posts SET ativo=0 WHERE id=?", (post_id,))
    db.execute("UPDATE comunidade_comentarios SET ativo=0 WHERE post_id=?", (post_id,))
    db.commit()
    return jsonify({'status': 'success'})

# ── COMUNIDADE — COMENTÁRIOS ─────────────────────────────────────────────────

@app.route('/api/comunidade/posts/<int:post_id>/comentarios', methods=['GET', 'OPTIONS'])
def listar_comentarios(post_id):
    if request.method == 'OPTIONS': return '', 204
    user_id = request.args.get('user_id', 0, type=int)
    db = get_db()
    rows = db.execute("""
        SELECT c.id, c.user_id, c.texto, c.criado_em,
               u.nome AS autor_nome, u.tipo AS autor_tipo,
               (SELECT COUNT(*) FROM comunidade_comentarios_curtidas cc WHERE cc.comentario_id=c.id) AS curtidas,
               CASE WHEN (SELECT COUNT(*) FROM comunidade_comentarios_curtidas cc WHERE cc.comentario_id=c.id AND cc.user_id=?) > 0 THEN 1 ELSE 0 END AS curtiu
        FROM comunidade_comentarios c
        JOIN users u ON u.id=c.user_id
        WHERE c.post_id=? AND c.ativo=1
        ORDER BY c.criado_em ASC
    """, (user_id, post_id)).fetchall()
    comentarios = [dict(r) for r in rows]
    for c in comentarios:
        c['autor_nome'] = _nome_curto(c['autor_nome'])
    return jsonify({'comentarios': comentarios})

@app.route('/api/comunidade/comentarios/<int:coment_id>/curtir', methods=['POST', 'OPTIONS'])
def curtir_comentario(coment_id):
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id')
    if not user_id: return jsonify({'error': 'user_id obrigatório'}), 400
    db = get_db()
    existe = db.execute("SELECT id FROM comunidade_comentarios_curtidas WHERE comentario_id=? AND user_id=?", (coment_id, user_id)).fetchone()
    if existe:
        db.execute("DELETE FROM comunidade_comentarios_curtidas WHERE comentario_id=? AND user_id=?", (coment_id, user_id))
    else:
        db.execute("INSERT INTO comunidade_comentarios_curtidas (comentario_id,user_id) VALUES (?,?)", (coment_id, user_id))
    db.commit()
    curtiu = not existe
    total = db.execute("SELECT COUNT(*) FROM comunidade_comentarios_curtidas WHERE comentario_id=?", (coment_id,)).fetchone()[0]
    return jsonify({'curtiu': curtiu, 'curtidas': total})

@app.route('/api/comunidade/posts/<int:post_id>/comentarios', methods=['POST', 'OPTIONS'])
def criar_comentario(post_id):
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id'); texto = (data.get('texto') or '').strip()
    if not user_id or not texto: return jsonify({'error': 'Dados incompletos'}), 400
    if len(texto) > 500: return jsonify({'error': 'Comentário muito longo (máx. 500 caracteres)'}), 400
    db = get_db()
    if not db.execute("SELECT id FROM comunidade_posts WHERE id=? AND ativo=1", (post_id,)).fetchone():
        return jsonify({'error': 'Post não encontrado'}), 404
    cur = db.execute("INSERT INTO comunidade_comentarios (post_id,user_id,texto) VALUES (?,?,?)", (post_id, user_id, texto))
    db.commit()
    post = db.execute("SELECT user_id FROM comunidade_posts WHERE id=?", (post_id,)).fetchone()
    autor = db.execute("SELECT nome FROM users WHERE id=?", (user_id,)).fetchone()
    nome_curto = _nome_curto(autor['nome']) if autor else 'Alguém'
    if post and post['user_id'] != user_id:
        _notif_user(db, post['user_id'], f'💬 {nome_curto} comentou no seu post', texto[:80] + ('...' if len(texto) > 80 else ''))
    nalin = _get_nalin_user(db)
    if nalin and nalin['id'] != user_id and (not post or post['user_id'] != nalin['id']):
        _notif_user(db, nalin['id'], f'💬 {nome_curto} comentou na comunidade', texto[:80] + ('...' if len(texto) > 80 else ''))
    db.commit()
    return jsonify({'status': 'success', 'id': cur.lastrowid})

@app.route('/api/comunidade/comentarios/<int:coment_id>', methods=['DELETE', 'OPTIONS'])
def deletar_comentario(coment_id):
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id')
    db = get_db()
    c = db.execute("SELECT user_id FROM comunidade_comentarios WHERE id=?", (coment_id,)).fetchone()
    if not c: return jsonify({'error': 'Comentário não encontrado'}), 404
    auth = request.headers.get('Authorization', '')
    is_admin = False
    if auth.startswith('Bearer '):
        try:
            jwt.decode(auth.split(' ', 1)[1], JWT_SECRET, algorithms=['HS256'])
            is_admin = True
        except: pass
    if not is_admin and (not user_id or int(user_id) != c['user_id']):
        return jsonify({'error': 'Sem permissão'}), 403
    db.execute("UPDATE comunidade_comentarios SET ativo=0 WHERE id=?", (coment_id,))
    db.commit()
    return jsonify({'status': 'success'})

# ── COMUNIDADE — CURTIDAS ─────────────────────────────────────────────────────

@app.route('/api/comunidade/posts/<int:post_id>/curtir', methods=['POST', 'OPTIONS'])
def curtir_post(post_id):
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    user_id = data.get('user_id')
    if not user_id: return jsonify({'error': 'user_id obrigatório'}), 400
    db = get_db()
    existe = db.execute("SELECT id FROM comunidade_curtidas WHERE post_id=? AND user_id=?", (post_id, user_id)).fetchone()
    if existe:
        db.execute("DELETE FROM comunidade_curtidas WHERE post_id=? AND user_id=?", (post_id, user_id))
    else:
        db.execute("INSERT INTO comunidade_curtidas (post_id,user_id) VALUES (?,?)", (post_id, user_id))
    db.commit()
    curtiu = not existe
    total = db.execute("SELECT COUNT(*) FROM comunidade_curtidas WHERE post_id=?", (post_id,)).fetchone()[0]
    if curtiu:
        post = db.execute("SELECT user_id FROM comunidade_posts WHERE id=?", (post_id,)).fetchone()
        if post and post['user_id'] != user_id:
            quem = db.execute("SELECT nome FROM users WHERE id=?", (user_id,)).fetchone()
            nome_curto = _nome_curto(quem['nome']) if quem else 'Alguém'
            _notif_user(db, post['user_id'], f'❤️ {nome_curto} curtiu seu post', '')
            db.commit()
    return jsonify({'curtiu': curtiu, 'curtidas': total})

# ── COMUNIDADE — ADMIN ────────────────────────────────────────────────────────

@app.route('/api/admin/comunidade/posts', methods=['GET', 'OPTIONS'])
@require_admin
def admin_listar_posts():
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    rows = db.execute("""
        SELECT p.id, p.user_id, p.texto, p.categoria, p.ativo, p.criado_em,
               u.nome AS autor_nome,
               (SELECT COUNT(*) FROM comunidade_comentarios c WHERE c.post_id=p.id AND c.ativo=1) AS total_comentarios,
               (SELECT COUNT(*) FROM comunidade_curtidas cu WHERE cu.post_id=p.id) AS curtidas
        FROM comunidade_posts p JOIN users u ON u.id=p.user_id
        WHERE p.ativo=1
        ORDER BY p.criado_em DESC LIMIT 200
    """).fetchall()
    posts = [dict(r) for r in rows]
    for p in posts:
        p['autor_nome'] = _nome_curto(p['autor_nome'])
    return jsonify({'posts': posts})

@app.route('/api/admin/comunidade/posts/<int:post_id>', methods=['DELETE', 'OPTIONS'])
@require_admin
def admin_deletar_post(post_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    db.execute("UPDATE comunidade_posts SET ativo=0 WHERE id=?", (post_id,))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/admin/comunidade/postar', methods=['POST', 'OPTIONS'])
@require_admin
def admin_nalin_postar():
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    texto = (data.get('texto') or '').strip()
    categoria = data.get('categoria', 'geral')
    if categoria not in ('geral', 'doacao', 'duvida', 'experiencia'): categoria = 'geral'
    if not texto: return jsonify({'error': 'Texto vazio'}), 400
    db = get_db()
    nalin = _get_nalin_user(db)
    if not nalin: return jsonify({'error': 'Usuária Nalin não encontrada no banco'}), 404
    cur = db.execute("INSERT INTO comunidade_posts (user_id,texto,categoria) VALUES (?,?,?)", (nalin['id'], texto, categoria))
    db.commit()
    _notif_todos(db, '🌸 Nova mensagem da Nalin', texto[:80] + ('...' if len(texto) > 80 else ''), excluir_ids=[nalin['id']])
    db.commit()
    return jsonify({'ok': True, 'id': cur.lastrowid})

@app.route('/api/admin/comunidade/posts/<int:post_id>/comentar', methods=['POST', 'OPTIONS'])
@require_admin
def admin_nalin_comentar(post_id):
    if request.method == 'OPTIONS': return '', 204
    data = request.json or {}
    texto = (data.get('texto') or '').strip()
    if not texto: return jsonify({'error': 'Texto vazio'}), 400
    db = get_db()
    nalin = _get_nalin_user(db)
    if not nalin: return jsonify({'error': 'Usuária Nalin não encontrada'}), 404
    post = db.execute("SELECT user_id FROM comunidade_posts WHERE id=? AND ativo=1", (post_id,)).fetchone()
    if not post: return jsonify({'error': 'Post não encontrado'}), 404
    cur = db.execute("INSERT INTO comunidade_comentarios (post_id,user_id,texto) VALUES (?,?,?)", (post_id, nalin['id'], texto))
    db.commit()
    if post['user_id'] != nalin['id']:
        _notif_user(db, post['user_id'], '🌸 Nalin comentou no seu post', texto[:80] + ('...' if len(texto) > 80 else ''))
        db.commit()
    return jsonify({'ok': True, 'id': cur.lastrowid})

@app.route('/api/admin/comunidade/posts/<int:post_id>/curtir', methods=['POST', 'OPTIONS'])
@require_admin
def admin_nalin_curtir(post_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    nalin = _get_nalin_user(db)
    if not nalin: return jsonify({'error': 'Usuária Nalin não encontrada'}), 404
    existe = db.execute("SELECT id FROM comunidade_curtidas WHERE post_id=? AND user_id=?", (post_id, nalin['id'])).fetchone()
    if existe:
        db.execute("DELETE FROM comunidade_curtidas WHERE post_id=? AND user_id=?", (post_id, nalin['id']))
    else:
        db.execute("INSERT INTO comunidade_curtidas (post_id,user_id) VALUES (?,?)", (post_id, nalin['id']))
    db.commit()
    curtiu = not existe
    total = db.execute("SELECT COUNT(*) FROM comunidade_curtidas WHERE post_id=?", (post_id,)).fetchone()[0]
    if curtiu:
        post = db.execute("SELECT user_id FROM comunidade_posts WHERE id=?", (post_id,)).fetchone()
        if post and post['user_id'] != nalin['id']:
            _notif_user(db, post['user_id'], '🌸 Nalin curtiu seu post', '')
            db.commit()
    return jsonify({'curtiu': curtiu, 'curtidas': total})

@app.route('/api/admin/comunidade/comentarios/<int:coment_id>/curtir', methods=['POST', 'OPTIONS'])
@require_admin
def admin_nalin_curtir_comentario(coment_id):
    if request.method == 'OPTIONS': return '', 204
    db = get_db()
    nalin = _get_nalin_user(db)
    if not nalin: return jsonify({'error': 'Usuária Nalin não encontrada'}), 404
    existe = db.execute("SELECT id FROM comunidade_comentarios_curtidas WHERE comentario_id=? AND user_id=?", (coment_id, nalin['id'])).fetchone()
    if existe:
        db.execute("DELETE FROM comunidade_comentarios_curtidas WHERE comentario_id=? AND user_id=?", (coment_id, nalin['id']))
    else:
        db.execute("INSERT INTO comunidade_comentarios_curtidas (comentario_id,user_id) VALUES (?,?)", (coment_id, nalin['id']))
    db.commit()
    curtiu = not existe
    total = db.execute("SELECT COUNT(*) FROM comunidade_comentarios_curtidas WHERE comentario_id=?", (coment_id,)).fetchone()[0]
    return jsonify({'curtiu': curtiu, 'curtidas': total})

@app.route('/api/comunidade/ranking', methods=['GET'])
def ranking_comunidade():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM conteudos WHERE categoria='video' AND ativo=1").fetchone()[0]
    rows = db.execute("""
        SELECT u.id, u.nome,
               COALESCE(SUM(CASE WHEN vp.assistido=1 THEN 1 ELSE 0 END),0) AS assistidos
        FROM users u
        LEFT JOIN video_progresso vp ON vp.user_id=u.id
        WHERE u.ativo=1
        GROUP BY u.id
        ORDER BY assistidos DESC, u.nome ASC
    """).fetchall()

    def _nivel(pct):
        if pct >= 67: return 'Doulanda Experiente'
        if pct >= 34: return 'Doulanda Iniciante'
        return 'Doulanda em Formação'

    def _nome_curto(nome):
        p = (nome or '').strip().split()
        return (p[0] + ' ' + p[-1]) if len(p) > 1 else (nome or '').strip()

    ranking = []
    for i, u in enumerate(rows, 1):
        ass = u['assistidos']
        pct = round(ass / total * 100) if total > 0 else 0
        ranking.append({'posicao':i,'user_id':u['id'],'nome':_nome_curto(u['nome']),
                        'assistidos':ass,'total':total,'percentual':pct,'nivel':_nivel(pct)})
    return jsonify({'ranking':ranking,'total_videos':total})

@app.route('/api/pagamento/status', methods=['GET'])
def status_pagamento():
    user_id = request.args.get('user_id')
    if not user_id: return jsonify({"status":"error"}), 400
    db = get_db()
    user = db.execute('SELECT assinatura_status, acesso_videos, acesso_ebooks FROM users WHERE id=?', (user_id,)).fetchone()
    if not user: return jsonify({"status":"error"}), 404
    return jsonify(dict(user))

@app.route('/api/admin/users/<int:user_id>/sincronizar-assinatura', methods=['POST', 'OPTIONS'])
@require_admin
def sincronizar_assinatura(user_id):
    """Consulta o ASAAS e atualiza o status de acesso da usuária."""
    if request.method == 'OPTIONS': return '', 204
    if not _ASAAS_OK:
        return jsonify({"status":"error","message":"Módulo de pagamento não configurado."}), 503
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    if not user: return jsonify({"status":"error","message":"Usuária não encontrada."}), 404
    user = dict(user)
    sub_id = user.get('asaas_subscription_id')
    if not sub_id:
        return jsonify({"status":"error","message":"Usuária não possui pagamento cadastrado."}), 400
    try:
        # pay_* = cobrança única;  sub_* = assinatura recorrente (legado)
        if sub_id.startswith('pay_'):
            cobranca = _asaas.buscar_cobranca(sub_id)
            if not cobranca:
                return jsonify({"status":"error","message":"Cobrança não encontrada no ASAAS."}), 404
            status_asaas = cobranca.get('status', '')
            if status_asaas in ('CONFIRMED', 'RECEIVED'):
                db.execute("UPDATE users SET assinatura_status='ativa', acesso_videos=1, acesso_ebooks=1 WHERE id=?", (user_id,))
                novo_status = 'ativa'
            elif status_asaas in ('OVERDUE', 'REFUNDED', 'CHARGEBACK'):
                db.execute("UPDATE users SET assinatura_status='vencida', acesso_videos=0, acesso_ebooks=0 WHERE id=?", (user_id,))
                novo_status = 'vencida'
            else:
                novo_status = status_asaas
        else:
            assinatura = _asaas.buscar_assinatura(sub_id)
            status_asaas = assinatura.get('status', '')
            if status_asaas == 'ACTIVE':
                db.execute("UPDATE users SET assinatura_status='ativa', acesso_videos=1, acesso_ebooks=1 WHERE id=?", (user_id,))
                novo_status = 'ativa'
            elif status_asaas in ('INACTIVE', 'OVERDUE', 'EXPIRED'):
                db.execute("UPDATE users SET assinatura_status='vencida', acesso_videos=0, acesso_ebooks=0 WHERE id=?", (user_id,))
                novo_status = 'vencida'
            else:
                novo_status = status_asaas
        db.commit()
        return jsonify({"status":"success","asaas_status":status_asaas,"assinatura_status":novo_status})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500

init_db()

if __name__ == '__main__':
    _gerar_icones_pwa()
    try:
        from migrate_db import migrate
        migrate()
    except Exception as e:
        print(f"Erro na migração: {e}")
    print(f"\n{'='*60}\n 🚀 SERVIDOR API NALIN NAZARETH ATIVO\n 📡 IP Local: http://{ip_local}:5000\n{'='*60}\n")
    tunnel_thread = threading.Thread(target=start_cloudflared_tunnel, daemon=True)
    tunnel_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
