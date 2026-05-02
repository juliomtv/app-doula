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
            categoria TEXT DEFAULT 'Geral',
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
                categoria TEXT DEFAULT 'Geral',
                url_pdf TEXT NOT NULL,
                url_capa TEXT,
                ativo INTEGER DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            cursor.execute("""
            INSERT INTO ebooks (id, titulo, descricao, categoria, url_pdf, url_capa, ativo, criado_em)
            SELECT id, titulo, descricao, 'Geral', url_pdf, url_capa, ativo, data_upload FROM ebooks_old
            """)
            cursor.execute("DROP TABLE ebooks_old")
            print("[migrate] Tabela ebooks corrigida com sucesso.")
        else:
            cursor.execute("PRAGMA table_info(ebooks)")
            ebook_cols = [row[1] for row in cursor.fetchall()]
            if 'categoria' not in ebook_cols:
                print("[migrate] Adicionando coluna categoria em ebooks...")
                cursor.execute("ALTER TABLE ebooks ADD COLUMN categoria TEXT DEFAULT 'Geral'")
            print("[migrate] Tabela ebooks OK.")

    # ── 3. Tabelas novas (se não existirem) ───────────────────────────────────
    # ── Tabela dicas_personalizadas: migrar para nova estrutura com id, titulo, emoji ──
    if 'dicas_personalizadas' not in all_tables:
        print("[migrate] Criando tabela dicas_personalizadas com nova estrutura...")
        cursor.execute("""
        CREATE TABLE dicas_personalizadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semana INTEGER NOT NULL UNIQUE,
            titulo TEXT,
            dica TEXT NOT NULL,
            emoji TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    else:
        cursor.execute("PRAGMA table_info(dicas_personalizadas)")
        dica_cols = [row[1] for row in cursor.fetchall()]
        if 'id' not in dica_cols:
            print("[migrate] Migrando dicas_personalizadas para nova estrutura (adicionando id, titulo, emoji)...")
            cursor.execute("ALTER TABLE dicas_personalizadas RENAME TO dicas_personalizadas_old")
            cursor.execute("""
            CREATE TABLE dicas_personalizadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                semana INTEGER NOT NULL UNIQUE,
                titulo TEXT,
                dica TEXT NOT NULL,
                emoji TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            cursor.execute("""
            INSERT INTO dicas_personalizadas (semana, dica, criado_em)
            SELECT semana, dica, criado_em FROM dicas_personalizadas_old
            """)
            cursor.execute("DROP TABLE dicas_personalizadas_old")
            print("[migrate] Tabela dicas_personalizadas migrada com sucesso.")
        else:
            print("[migrate] Tabela dicas_personalizadas OK.")
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

    # ── 4. Tabelas do Mini Curso ──────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS curso_secoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descricao TEXT,
        ordem INTEGER DEFAULT 0,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS video_progresso (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        conteudo_id INTEGER NOT NULL,
        assistido INTEGER DEFAULT 0,
        percentual INTEGER DEFAULT 0,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, conteudo_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (conteudo_id) REFERENCES conteudos(id)
    )
    """)
    # Adicionar colunas secao_id e ordem em conteudos (se não existirem)
    cursor.execute("PRAGMA table_info(conteudos)")
    current_cont_cols = [row[1] for row in cursor.fetchall()]
    if 'secao_id' not in current_cont_cols:
        print("[migrate] Adicionando coluna secao_id em conteudos")
        cursor.execute("ALTER TABLE conteudos ADD COLUMN secao_id INTEGER DEFAULT NULL")
    if 'ordem' not in current_cont_cols:
        print("[migrate] Adicionando coluna ordem em conteudos")
        cursor.execute("ALTER TABLE conteudos ADD COLUMN ordem INTEGER DEFAULT 0")

    # ── 5. Configurações padrão no config_global ──────────────────────────────
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

    # ── 6. Garantir admin com credenciais corretas da Nalin ──────────────────
    cursor.execute("SELECT COUNT(*) FROM admin_config WHERE username = 'nalinnazareth'")
    if cursor.fetchone()[0] == 0:
        # Não existe admin 'nalinnazareth' — verifica se tem algum admin
        cursor.execute("SELECT COUNT(*) FROM admin_config")
        if cursor.fetchone()[0] == 0:
            # Banco vazio — insere
            cursor.execute("INSERT INTO admin_config (username, password) VALUES ('nalinnazareth', 'apolo1895')")
            print("[migrate] Admin nalinnazareth criado.")
        else:
            # Existe admin antigo (ex: admin@nalinnazareth.com) — atualiza o id=1
            cursor.execute("UPDATE admin_config SET username='nalinnazareth', password='apolo1895' WHERE id=1")
            print("[migrate] Credenciais do admin atualizadas para nalinnazareth.")
    else:
        print("[migrate] Admin nalinnazareth já existe.")

    conn.commit()
    conn.close()
    print("[migrate] Migração concluída com sucesso.")

if __name__ == "__main__":
    migrate()
