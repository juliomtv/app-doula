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

    # ── 1. Colunas faltantes na tabela users ──────────────────────────────────
    required_user_columns = [
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
        ('expectativas_desejos_parto', 'TEXT'),
    ]
    cursor.execute("PRAGMA table_info(users)")
    current_user_cols = [row[1] for row in cursor.fetchall()]
    for col_name, col_type in required_user_columns:
        if col_name not in current_user_cols:
            print(f"[migrate] Adicionando coluna em users: {col_name}")
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"[migrate] Erro ao adicionar {col_name}: {e}")

    # ── 2. Tabela ebooks: corrigir data_upload → criado_em ────────────────────
    all_tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    if 'ebooks' not in all_tables:
        print("[migrate] Criando tabela ebooks com criado_em...")
        cursor.execute("""
        CREATE TABLE ebooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            url_pdf TEXT NOT NULL,
            url_capa TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    else:
        cursor.execute("PRAGMA table_info(ebooks)")
        ebook_cols = [row[1] for row in cursor.fetchall()]
        if 'data_upload' in ebook_cols and 'criado_em' not in ebook_cols:
            print("[migrate] Corrigindo tabela ebooks: data_upload → criado_em...")
            cursor.execute("ALTER TABLE ebooks RENAME TO ebooks_old")
            cursor.execute("""
            CREATE TABLE ebooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT,
                url_pdf TEXT NOT NULL,
                url_capa TEXT,
                ativo INTEGER DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            cursor.execute("""
            INSERT INTO ebooks (id, titulo, descricao, url_pdf, url_capa, ativo, criado_em)
            SELECT id, titulo, descricao, url_pdf, url_capa, ativo, data_upload FROM ebooks_old
            """)
            cursor.execute("DROP TABLE ebooks_old")
            print("[migrate] Tabela ebooks corrigida com sucesso.")
        else:
            print("[migrate] Tabela ebooks OK.")

    # ── 3. Tabelas novas (se não existirem) ───────────────────────────────────
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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config_global (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave TEXT UNIQUE NOT NULL,
        valor TEXT,
        descricao TEXT,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agenda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        titulo TEXT NOT NULL,
        descricao TEXT,
        data_evento DATE NOT NULL,
        hora_evento TIME,
        tipo TEXT DEFAULT 'outro',
        concluido INTEGER DEFAULT 0,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enxoval (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item TEXT NOT NULL,
        quantidade INTEGER DEFAULT 1,
        comprado INTEGER DEFAULT 0,
        prioridade TEXT DEFAULT 'normal',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maternidade (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        nome_maternidade TEXT,
        endereco TEXT,
        telefone TEXT,
        medico_nome TEXT,
        medico_telefone TEXT,
        plano_saude TEXT,
        numero_cartao TEXT,
        observacoes TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plano_parto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        tipo_parto TEXT,
        acompanhante TEXT,
        desejos TEXT,
        medos TEXT,
        posicoes_preferidas TEXT,
        musica_ambiente TEXT,
        iluminacao TEXT,
        outras_observacoes TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # ── 4. Configurações padrão no config_global ──────────────────────────────
    defaults = [
        ('whatsapp_numero', '5500000000000', 'Numero de WhatsApp da Doula'),
        ('whatsapp_mensagem', 'Ola! Tudo bem? Sou a Nalin, sua doula. Como posso ajuda-la?', 'Mensagem padrao do WhatsApp'),
        ('instagram_url', '', 'URL do Instagram'),
        ('email_contato', '', 'E-mail para contato'),
        ('url_base_servidor', '', 'URL base do servidor (IP local). Configurada pelo admin. O app usa para descobrir a URL publica do tunnel automaticamente.'),
    ]
    for chave, valor, descricao in defaults:
        cursor.execute(
            "INSERT OR IGNORE INTO config_global (chave, valor, descricao) VALUES (?, ?, ?)",
            (chave, valor, descricao)
        )

    conn.commit()
    conn.close()
    print("[migrate] Migração concluída com sucesso.")

if __name__ == "__main__":
    migrate()
