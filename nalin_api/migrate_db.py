import sqlite3
import os

# Caminho para o banco de dados
DATABASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dados.db'))

def migrate():
    if not os.path.exists(DATABASE):
        print(f"Banco de dados não encontrado em: {DATABASE}")
        # Se não existe, o init_db no app.py criará via schema.sql
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 1. Verificar colunas faltantes na tabela users
    required_columns = [
        ('rg_orgao', 'TEXT'),
        ('cpf', 'TEXT'),
        ('estado_civil', 'TEXT'),
        ('endereco_cep', 'TEXT'),
        ('nacionalidade', 'TEXT'),
        ('pacote_escolhido', 'TEXT'),
        ('servicos_extras', 'TEXT'),
        ('forma_pagamento', 'TEXT'),
        ('melhor_data_pagamento', 'TEXT'),
        ('email_acompanhante', 'TEXT'),
        ('ja_iniciou_pre_natal', 'TEXT'),
        ('local_pre_natal', 'TEXT'),
        ('idade', 'INTEGER'),
        ('data_nascimento', 'TEXT'),
        ('acompanhante_parentesco', 'TEXT'),
        ('historico_saude', 'TEXT'),
        ('sobre_saude', 'TEXT'),
        ('alergias', 'TEXT'),
        ('sintomas_gravidez', 'TEXT'),
        ('historico_doencas_familiares', 'TEXT'),
        ('doencas_gravidez', 'TEXT'),
        ('ja_esteve_gravida_antes', 'TEXT'),
        ('intercorrencias_gestacoes_anteriores', 'TEXT'),
        ('quais_intercorrencias', 'TEXT'),
        ('experiencia_partos_anteriores', 'TEXT'),
        ('relato_experiencia_parto', 'TEXT'),
        ('medicacao_suplemento', 'TEXT'),
        ('vacinacao_em_dia', 'TEXT'),
        ('sentimento_gravidez', 'TEXT'),
        ('questao_religiosa_cultural', 'TEXT'),
        ('expectativas_desejos_parto', 'TEXT')
    ]

    cursor.execute("PRAGMA table_info(users)")
    current_columns = [row[1] for row in cursor.fetchall()]

    added_count = 0
    for col_name, col_type in required_columns:
        if col_name not in current_columns:
            print(f"Adicionando coluna faltante em users: {col_name}")
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                added_count += 1
            except Exception as e:
                print(f"Erro ao adicionar {col_name}: {e}")

    # 2. Criar tabelas novas se não existirem
    print("Verificando tabelas novas...")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ebooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descricao TEXT,
        url_pdf TEXT NOT NULL,
        url_capa TEXT,
        ativo INTEGER DEFAULT 1,
        data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dicas_personalizadas (
        semana INTEGER PRIMARY KEY,
        dica TEXT NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs_atividade (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        acao TEXT NOT NULL,
        detalhes TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Migração concluída com sucesso.")

if __name__ == "__main__":
    migrate()
