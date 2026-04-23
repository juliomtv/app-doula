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
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de E-books (Uploads de PDF)
CREATE TABLE IF NOT EXISTS ebooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descricao TEXT,
    url_pdf TEXT NOT NULL,
    url_capa TEXT,
    ativo INTEGER DEFAULT 1,
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- Tabela de Dicas Semanais
CREATE TABLE IF NOT EXISTS dicas_semanais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semana INTEGER NOT NULL UNIQUE,
    titulo TEXT NOT NULL,
    dica TEXT NOT NULL,
    emoji TEXT DEFAULT '💡',
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
('email_contato', '', 'E-mail para contato');
