import re

with open('nalin_api/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Adicionar import hashlib e json no topo
if 'import hashlib' not in content:
    content = content.replace('import re\n', 'import re\nimport hashlib\nimport json\n')
    print('Imports adicionados: OK')
else:
    print('Imports já existem: OK')

# 2. Adicionar rotas OTA no CORS
old_cors_end = '    r"/api/url-servidor": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}\n})'
new_cors_end = '''    r"/api/url-servidor": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]},
    r"/ota/*": {"origins": "*", "methods": ["GET", "OPTIONS"], "allow_headers": ["Content-Type"]}
})'''
if old_cors_end in content:
    content = content.replace(old_cors_end, new_cors_end)
    print('CORS atualizado: OK')
else:
    print('WARN: CORS nao encontrado para atualizar')

# 3. Adicionar os endpoints OTA antes do endpoint /versao_app
ota_endpoints = '''
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

'''

# Inserir antes do endpoint /versao_app
if '# ════ OTA UPDATE ════' not in content:
    content = content.replace(
        "@app.route('/versao_app', methods=['GET', 'OPTIONS'])",
        ota_endpoints + "@app.route('/versao_app', methods=['GET', 'OPTIONS'])"
    )
    print('Endpoints OTA adicionados: OK')
else:
    print('Endpoints OTA já existem: OK')

with open('nalin_api/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('app.py salvo.')
