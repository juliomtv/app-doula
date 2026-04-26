-- Tabela de Usuários (Doulandas)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    bebe TEXT,
    semanas INTEGER DEFAULT 0,
    dpp TEXT,
    parto TEXT DEFAULT 'normal',
    rg_orgao TEXT,
    cpf TEXT,
    estado_civil TEXT,
    endereco_cep TEXT,
    nacionalidade TEXT,
    pacote_escolhido TEXT,
    servicos_extras TEXT,
    forma_pagamento TEXT,
    melhor_data_pagamento TEXT,
    email_acompanhante TEXT,
    ja_iniciou_pre_natal TEXT,
    local_pre_natal TEXT,
    idade INTEGER,
    data_nascimento TEXT,
    acompanhante_parentesco TEXT,
    historico_saude TEXT,
    sobre_saude TEXT,
    alergias TEXT,
    sintomas_gravidez TEXT,
    historico_doencas_familiares TEXT,
    doencas_gravidez TEXT,
    ja_esteve_gravida_antes TEXT,
    intercorrencias_gestacoes_anteriores TEXT,
    quais_intercorrencias TEXT,
    experiencia_partos_anteriores TEXT,
    relato_experiencia_parto TEXT,
    medicacao_suplemento TEXT,
    vacinacao_em_dia TEXT,
    sentimento_gravidez TEXT,
    questao_religiosa_cultural TEXT,
    expectativas_desejos_parto TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Seções do Mini Curso
CREATE TABLE IF NOT EXISTS curso_secoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descricao TEXT,
    ordem INTEGER DEFAULT 0,
    ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Conteúdos (Vídeos, Meditações, etc)
CREATE TABLE IF NOT EXISTS conteudos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    categoria TEXT NOT NULL, -- 'video', 'meditacao', 'ebook'
    subcategoria TEXT,
    emoji TEXT DEFAULT '📄',
    descricao TEXT,
    duracao TEXT,
    paginas TEXT,
    url TEXT NOT NULL,
    cor TEXT DEFAULT '#e8b4a0,#c9907a',
    ativo INTEGER DEFAULT 1,
    secao_id INTEGER DEFAULT NULL,  -- NULL = sem seção (meditações, ebooks)
    ordem INTEGER DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (secao_id) REFERENCES curso_secoes(id)
);

-- Tabela de E-books (Uploads de PDF)
CREATE TABLE IF NOT EXISTS ebooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descricao TEXT,
    url_pdf TEXT NOT NULL,
    url_capa TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Configuração do Admin
CREATE TABLE IF NOT EXISTS admin_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- Tabela de Configurações Globais
CREATE TABLE IF NOT EXISTS config_global (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chave TEXT UNIQUE NOT NULL,
    valor TEXT,
    descricao TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserir admin padrão se não existir
INSERT OR IGNORE INTO admin_config (id, username, password) VALUES (1, 'admin@nalinnazareth.com', 'admin123');

-- Tabela de Dicas Personalizadas
CREATE TABLE IF NOT EXISTS dicas_personalizadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semana INTEGER NOT NULL UNIQUE,
    titulo TEXT,
    dica TEXT NOT NULL,
    emoji TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Agenda do Bebê
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
);

-- Tabela de Lista de Enxoval
CREATE TABLE IF NOT EXISTS enxoval (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item TEXT NOT NULL,
    quantidade INTEGER DEFAULT 1,
    comprado INTEGER DEFAULT 0,
    prioridade TEXT DEFAULT 'normal',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Tabela de Informacoes da Maternidade
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
);

-- Tabela de Plano de Parto
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
);

-- Inserir configuracoes padrao
INSERT OR IGNORE INTO config_global (chave, valor, descricao) VALUES 
('whatsapp_numero', '5500000000000', 'Numero de WhatsApp da Doula'),
('whatsapp_mensagem', 'Ola! Tudo bem? Sou a Nalin, sua doula. Como posso ajuda-la?', 'Mensagem padrao do WhatsApp'),
('instagram_url', '', 'URL do Instagram'),
('email_contato', '', 'E-mail para contato'),
('url_base_servidor', '', 'URL base do servidor (IP local). Configurada pelo admin. O app usa para descobrir a URL publica do tunnel automaticamente.');

-- Tabela de Progresso de Vídeos por Usuária
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
);

-- Tabela de Logs de Atividade
CREATE TABLE IF NOT EXISTS logs_atividade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    acao TEXT NOT NULL, -- Ex: 'Viu o vídeo: Titulo', 'Escreveu no diário', 'Acessou o app'
    detalhes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
