# Guia: Rodando o Servidor no seu Computador

O servidor roda no seu computador e o app no celular pode se conectar a ele de **qualquer rede** (Wi-Fi, 5G) usando o **Cloudflare Tunnel** — uma ferramenta gratuita que cria uma URL pública temporária para o seu servidor local.

---

## 1. Preparar o Ambiente (No Computador)

Certifique-se de ter o **Python** instalado.

Abra o terminal na pasta `nalin_api` e instale as dependências:

```bash
pip install flask flask-cors
```

---

## 2. Instalar o Cloudflare Tunnel (cloudflared)

O `cloudflared` cria um túnel seguro HTTPS entre a internet e o seu servidor local. É **gratuito** e não precisa de conta.

**Windows:**
```powershell
winget install Cloudflare.cloudflared
```
Ou baixe o instalador em: https://github.com/cloudflare/cloudflared/releases

**Mac:**
```bash
brew install cloudflared
```

**Linux/Ubuntu:**
```bash
sudo apt install cloudflared
```

---

## 3. Iniciar o Servidor

Na pasta `nalin_api`, execute:

```bash
python app.py
```

O terminal mostrará algo como:

```
============================================================
 🚀 SERVIDOR API NALIN NAZARETH ATIVO
 📡 IP Local (Wi-Fi): http://192.168.1.15:5000
 🌍 Iniciando túnel público (aguarde alguns segundos)...
============================================================

============================================================
 🌍 URL PÚBLICA GERADA COM SUCESSO!
 🔗 https://exemplo-aleatorio.trycloudflare.com
 📱 Cole essa URL no app para acessar de qualquer rede
============================================================
```

**Anote a URL pública** (ex: `https://exemplo-aleatorio.trycloudflare.com`).

---

## 4. Conectar o App ao Servidor

Na tela de login do app, cole a **URL pública** no campo **"URL do Servidor"**:

```
https://exemplo-aleatorio.trycloudflare.com
```

A URL fica salva automaticamente — você só precisa informar uma vez. Nas próximas vezes que abrir o app, ela já estará preenchida.

> **Importante:** A URL pública muda toda vez que você reinicia o servidor. Se o app parar de conectar, verifique a nova URL no terminal e atualize no campo de login.

---

## 5. Funcionamento em Diferentes Redes

| Situação | Como conectar |
|---|---|
| Celular no mesmo Wi-Fi do computador | Use a URL pública **ou** o IP local (`http://192.168.1.15:5000`) |
| Celular em outra rede (5G, Wi-Fi externo) | Use **somente** a URL pública (`https://xxxx.trycloudflare.com`) |

---

## 6. Dicas Importantes

1. **Servidor deve estar ligado:** O computador precisa estar ligado e com o servidor rodando para o app funcionar.
2. **Firewall:** Se o cloudflared não iniciar, verifique se o Firewall está bloqueando. Permita o `cloudflared` nas configurações de segurança.
3. **URL muda ao reiniciar:** A URL pública é temporária. Ao reiniciar o servidor, uma nova URL é gerada — atualize no app.
4. **Backup do banco:** O arquivo `dados.db` fica na pasta raiz do projeto. Copie-o para fazer backup de todas as clientes cadastradas.

---

## 7. Sem o cloudflared (somente Wi-Fi local)

Se preferir não usar o cloudflared, o app ainda funciona normalmente **na mesma rede Wi-Fi** do computador. Use o IP local exibido no terminal:

```
http://192.168.1.15:5000
```

Nesse caso, o celular e o computador precisam estar na mesma rede Wi-Fi.
