#!/usr/bin/env python3
"""
bump_version.py — Incrementa a versão do app e atualiza version.json
Uso: python3 bump_version.py [patch|minor|major] ["Descrição da atualização"]

Exemplos:
  python3 bump_version.py patch "Correção de bugs nas dicas"
  python3 bump_version.py minor "Nova funcionalidade de agenda"
  python3 bump_version.py major "Redesign completo do app"
"""
import json
import sys
import os
from datetime import date

VERSION_FILE = os.path.join(os.path.dirname(__file__), 'www', 'version.json')

def bump(tipo='patch', notas='Atualização do app', obrigatoria=False):
    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    partes = data['versao'].split('.')
    major, minor, patch = int(partes[0]), int(partes[1]), int(partes[2])
    
    if tipo == 'major':
        major += 1; minor = 0; patch = 0
    elif tipo == 'minor':
        minor += 1; patch = 0
    else:
        patch += 1
    
    nova_versao = f"{major}.{minor}.{patch}"
    data['versao'] = nova_versao
    data['data'] = str(date.today())
    data['notas'] = notas
    data['obrigatoria'] = obrigatoria
    
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Versão atualizada: {nova_versao}")
    print(f"📝 Notas: {notas}")
    print(f"📅 Data: {data['data']}")
    print(f"⚠️  Obrigatória: {'Sim' if obrigatoria else 'Não'}")
    return nova_versao

if __name__ == '__main__':
    tipo = sys.argv[1] if len(sys.argv) > 1 else 'patch'
    notas = sys.argv[2] if len(sys.argv) > 2 else 'Atualização do app'
    obrigatoria = '--obrigatoria' in sys.argv
    bump(tipo, notas, obrigatoria)
