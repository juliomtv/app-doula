CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    bebe TEXT,
    semanas INTEGER DEFAULT 0,
    dpp TEXT,
    parto TEXT DEFAULT 'normal',
    ativo BOOLEAN DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conteudos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    categoria TEXT NOT NULL, -- video, ebook, meditacao
    subcategoria TEXT,
    emoji TEXT DEFAULT '📄',
    descricao TEXT,
    duracao TEXT,
    paginas TEXT,
    url TEXT,
    cor TEXT DEFAULT '#e8b4a0,#c9907a',
    ativo BOOLEAN DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- Inserir admin padrão se não existir
INSERT OR IGNORE INTO admin_config (id, username, password) VALUES (1, 'admin@nalinnazareth.com', 'admin123');

CREATE TABLE IF NOT EXISTS ebooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descricao TEXT,
    url_pdf TEXT NOT NULL,
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT 1
);
