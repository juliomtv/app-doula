import sqlite3
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
import os
import socket
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type"]}})

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

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

@app.route('/api/status', methods=['GET', 'OPTIONS'])
def status():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({"status": "online", "message": "API Nalin Nazareth rodando localmente"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND senha = ?', (email, senha)).fetchone()
    if user:
        return jsonify({"status": "success", "user": dict(user)})
    return jsonify({"status": "error", "message": "E-mail ou senha incorretos."}), 401

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    user = data.get('user')
    passw = data.get('pass')
    db = get_db()
    admin = db.execute('SELECT * FROM admin_config WHERE username = ? AND password = ?', (user, passw)).fetchone()
    if admin:
        return jsonify({"status": "success", "token": "admin-session-token"})
    return jsonify({"status": "error", "message": "Acesso negado."}), 401

@app.route('/api/users', methods=['GET'])
def list_users():
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY criado_em DESC').fetchall()
    return jsonify([dict(u) for u in users])

@app.route('/api/users', methods=['POST'])
def save_user():
    data = request.json
    db = get_db()
    if 'id' in data and data['id']:
        db.execute('UPDATE users SET nome=?, email=?, senha=?, bebe=?, semanas=?, dpp=?, parto=?, rg_orgao=?, cpf=?, estado_civil=?, endereco_cep=?, nacionalidade=?, pacote_escolhido=?, servicos_extras=?, forma_pagamento=?, melhor_data_pagamento=? WHERE id=?', 
                   (data['nome'], data['email'], data['senha'], data['bebe'], data['semanas'], data['dpp'], data['parto'], 
                    data.get('rg_orgao'), data.get('cpf'), data.get('estado_civil'), data.get('endereco_cep'), data.get('nacionalidade'), 
                    data.get('pacote_escolhido'), data.get('servicos_extras'), data.get('forma_pagamento'), data.get('melhor_data_pagamento'), data['id']))
    else:
        dup = db.execute('SELECT id FROM users WHERE email = ?', (data['email'],)).fetchone()
        if dup: return jsonify({"status": "error", "message": "E-mail já cadastrado."}), 400
        db.execute('INSERT INTO users (nome, email, senha, bebe, semanas, dpp, parto, rg_orgao, cpf, estado_civil, endereco_cep, nacionalidade, pacote_escolhido, servicos_extras, forma_pagamento, melhor_data_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (data['nome'], data['email'], data['senha'], data['bebe'], data['semanas'], data['dpp'], data['parto'],
                    data.get('rg_orgao'), data.get('cpf'), data.get('estado_civil'), data.get('endereco_cep'), data.get('nacionalidade'), 
                    data.get('pacote_escolhido'), data.get('servicos_extras'), data.get('forma_pagamento'), data.get('melhor_data_pagamento')))
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
        cont = db.execute('SELECT * FROM conteudos WHERE ativo = 1 ORDER BY criado_em DESC').fetchall()
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
    if 'id' in data and data['id']:
        db.execute('UPDATE conteudos SET titulo=?, categoria=?, subcategoria=?, emoji=?, descricao=?, duracao=?, paginas=?, url=?, cor=? WHERE id=?',
                   (data['titulo'], data['categoria'], data['subcategoria'], data['emoji'], data['descricao'], data['duracao'], data['paginas'], data['url'], data['cor'], data['id']))
    else:
        db.execute('INSERT INTO conteudos (titulo, categoria, subcategoria, emoji, descricao, duracao, paginas, url, cor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (data['titulo'], data['categoria'], data['subcategoria'], data['emoji'], data['descricao'], data['duracao'], data['paginas'], data['url'], data['cor']))
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
            os.remove(filepath)
            return jsonify({"status": "error", "message": "Título do eBook é obrigatório."}), 400
            
        db = get_db()
        try:
            db.execute(
                "INSERT INTO ebooks (titulo, descricao, url_pdf, url_capa) VALUES (?, ?, ?, ?)",
                (titulo, descricao, f"/uploads/{filename}", url_capa),
            )
            db.commit()
            return jsonify({"status": "success", "message": "eBook enviado com sucesso!"}), 201
        except Exception as e:
            if os.path.exists(filepath): os.remove(filepath)
            return jsonify({"status": "error", "message": f"Erro ao salvar eBook: {str(e)}"}), 500
    else:
        return jsonify({"status": "error", "message": "Tipo de arquivo não permitido."}), 400

@app.route("/api/ebooks", methods=["GET"])
def list_ebooks():
    db = get_db()
    try:
        # Tenta adicionar a coluna url_capa se ela não existir (migração rápida)
        try:
            db.execute("ALTER TABLE ebooks ADD COLUMN url_capa TEXT")
            db.commit()
        except:
            pass
            
        ebooks = db.execute("SELECT id, titulo, descricao, url_pdf, url_capa, data_upload FROM ebooks ORDER BY data_upload DESC").fetchall()
        return jsonify([dict(e) for e in ebooks])
    except sqlite3.OperationalError:
        return jsonify([])

@app.route("/api/ebook/<int:ebook_id>", methods=["GET"])
def get_ebook(ebook_id):
    db = get_db()
    try:
        ebook = db.execute("SELECT id, titulo, descricao, url_pdf, data_upload FROM ebooks WHERE id = ? AND ativo = 1", (ebook_id,)).fetchone()
        if ebook: return jsonify(dict(ebook))
        return jsonify({"status": "error", "message": "eBook não encontrado."}), 404
    except sqlite3.OperationalError:
        return jsonify({"status": "error", "message": "Tabela de eBooks não encontrada."}), 500

@app.route("/api/ebook/<int:ebook_id>", methods=["DELETE"])
def delete_ebook(ebook_id):
    db = get_db()
    db.execute("DELETE FROM ebooks WHERE id = ?", (ebook_id,))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/config', methods=['GET'])
def get_config():
    db = get_db()
    try:
        configs = db.execute('SELECT chave, valor FROM config_global').fetchall()
        return jsonify({config['chave']: config['valor'] for config in configs})
    except:
        return jsonify({})

@app.route('/api/admin/config', methods=['GET', 'POST', 'OPTIONS'])
def admin_config():
    if request.method == 'OPTIONS':
        return '', 204
    
    db = get_db()
    if request.method == 'GET':
        try:
            configs = db.execute('SELECT chave, valor, descricao FROM config_global').fetchall()
            return jsonify([dict(c) for c in configs])
        except:
            return jsonify([])
    elif request.method == 'POST':
        data = request.json
        try:
            for chave, valor in data.items():
                db.execute('INSERT OR REPLACE INTO config_global (chave, valor) VALUES (?, ?)', (chave, valor))
            db.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/dicas', methods=['GET'])
def get_dicas():
    db = get_db()
    try:
        dicas = db.execute('SELECT * FROM dicas_semanais ORDER BY semana').fetchall()
        return jsonify([dict(d) for d in dicas])
    except:
        return jsonify([])

@app.route('/api/admin/dicas', methods=['GET', 'POST', 'OPTIONS'])
def admin_dicas():
    if request.method == 'OPTIONS':
        return '', 204
    
    db = get_db()
    if request.method == 'GET':
        try:
            dicas = db.execute('SELECT * FROM dicas_semanais ORDER BY semana').fetchall()
            return jsonify([dict(d) for d in dicas])
        except:
            return jsonify([])
    elif request.method == 'POST':
        data = request.json
        try:
            db.execute('INSERT OR REPLACE INTO dicas_semanais (semana, titulo, dica, emoji) VALUES (?, ?, ?, ?)',
                      (data['semana'], data['titulo'], data['dica'], data.get('emoji', '')))
            db.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/agenda', methods=['GET', 'POST', 'OPTIONS'])
def agenda():
    if request.method == 'OPTIONS':
        return '', 204
    
    db = get_db()
    user_id = request.args.get('user_id') or (request.json.get('user_id') if request.json else None)
    
    if request.method == 'GET':
        try:
            eventos = db.execute('SELECT * FROM agenda WHERE user_id = ? ORDER BY data_evento ASC', (user_id,)).fetchall()
            return jsonify([dict(e) for e in eventos])
        except:
            return jsonify([])
    elif request.method == 'POST':
        data = request.json
        try:
            db.execute('INSERT INTO agenda (user_id, titulo, descricao, data_evento, hora_evento, tipo) VALUES (?, ?, ?, ?, ?, ?)',
                      (data['user_id'], data['titulo'], data.get('descricao', ''), data['data_evento'], data.get('hora_evento', ''), data.get('tipo', 'outro')))
            db.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/agenda/<int:evento_id>', methods=['DELETE', 'OPTIONS'])
def delete_agenda(evento_id):
    if request.method == 'OPTIONS':
        return '', 204
    
    db = get_db()
    db.execute('DELETE FROM agenda WHERE id = ?', (evento_id,))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/enxoval', methods=['GET', 'POST', 'OPTIONS'])
def enxoval():
    if request.method == 'OPTIONS':
        return '', 204
    
    db = get_db()
    user_id = request.args.get('user_id') or (request.json.get('user_id') if request.json else None)
    
    if request.method == 'GET':
        try:
            itens = db.execute('SELECT * FROM enxoval WHERE user_id = ? ORDER BY prioridade DESC, criado_em DESC', (user_id,)).fetchall()
            return jsonify([dict(i) for i in itens])
        except:
            return jsonify([])
    elif request.method == 'POST':
        data = request.json
        try:
            db.execute('INSERT INTO enxoval (user_id, item, quantidade, prioridade) VALUES (?, ?, ?, ?)',
                      (data['user_id'], data['item'], data.get('quantidade', 1), data.get('prioridade', 'normal')))
            db.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/enxoval/<int:item_id>', methods=['DELETE', 'POST', 'OPTIONS'])
def update_enxoval(item_id):
    if request.method == 'OPTIONS':
        return '', 204
    
    db = get_db()
    if request.method == 'DELETE':
        db.execute('DELETE FROM enxoval WHERE id = ?', (item_id,))
    elif request.method == 'POST':
        data = request.json
        db.execute('UPDATE enxoval SET comprado = ? WHERE id = ?', (data.get('comprado', 0), item_id))
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

if __name__ == '__main__':
    # Tenta inicializar o banco sempre para garantir as tabelas
    init_db()
    
    ip = get_local_ip()
    print(f"\n{'='*50}")
    print(f" API RODANDO LOCALMENTE")
    print(f" Endereço para os APKS: http://{ip}:5000")
    print(f"{'='*50}\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
