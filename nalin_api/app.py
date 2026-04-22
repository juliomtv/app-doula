import sqlite3
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os
import socket

app = Flask(__name__)
CORS(app)

DATABASE = '../dados.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

@app.route('/api/status', methods=['GET'])
def status():
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
        db.execute('UPDATE users SET nome=?, email=?, senha=?, bebe=?, semanas=?, dpp=?, parto=? WHERE id=?', 
                   (data['nome'], data['email'], data['senha'], data['bebe'], data['semanas'], data['dpp'], data['parto'], data['id']))
    else:
        dup = db.execute('SELECT id FROM users WHERE email = ?', (data['email'],)).fetchone()
        if dup: return jsonify({"status": "error", "message": "E-mail já cadastrado."}), 400
        db.execute('INSERT INTO users (nome, email, senha, bebe, semanas, dpp, parto) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (data['nome'], data['email'], data['senha'], data['bebe'], data['semanas'], data['dpp'], data['parto']))
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
    cont = db.execute('SELECT * FROM conteudos WHERE ativo = 1 ORDER BY criado_em DESC').fetchall()
    return jsonify([dict(c) for c in cont])

@app.route('/api/admin/conteudos', methods=['GET'])
def admin_list_conteudos():
    db = get_db()
    cont = db.execute('SELECT * FROM conteudos ORDER BY criado_em DESC').fetchall()
    return jsonify([dict(c) for c in cont])

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

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    
    ip = get_local_ip()
    print(f"\n{'='*50}")
    print(f" API RODANDO LOCALMENTE")
    print(f" Endereço para os APKS: http://{ip}:5000")
    print(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
