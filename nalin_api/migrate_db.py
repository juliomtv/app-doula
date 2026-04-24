import sqlite3
import os

# Caminho para o banco de dados (ajustado para rodar na pasta nalin_api)
# O banco 'dados.db' está na raiz do projeto, um nível acima de 'nalin_api'
DATABASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dados.db'))

def migrate():
    if not os.path.exists(DATABASE):
        print(f"Banco de dados não encontrado em: {DATABASE}")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Lista de colunas que devem existir na tabela users (baseado no schema.sql atual)
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

    # Obter colunas atuais
    cursor.execute("PRAGMA table_info(users)")
    current_columns = [row[1] for row in cursor.fetchall()]

    added_count = 0
    for col_name, col_type in required_columns:
        if col_name not in current_columns:
            print(f"Adicionando coluna faltante: {col_name}")
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                added_count += 1
            except Exception as e:
                print(f"Erro ao adicionar {col_name}: {e}")

    # Criar tabela de logs se não existir
    print("Verificando tabela de logs...")
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
    
    if added_count > 0:
        print(f"Migração concluída! {added_count} colunas adicionadas.")
    else:
        print("O banco de dados já está atualizado.")

if __name__ == "__main__":
    migrate()
