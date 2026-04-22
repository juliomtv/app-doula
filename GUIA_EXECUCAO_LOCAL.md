# Guia: Rodando a API no seu Notebook

Como você vai rodar tudo no seu notebook, o processo é muito simples. Siga os passos abaixo:

## 1. Preparar o Ambiente (No Notebook)
Certifique-se de ter o **Python** instalado.
Abra o terminal na pasta `nalin_api` e instale as dependências:
```bash
pip install flask flask-cors
```

## 2. Iniciar a API
Ainda no terminal, execute:
```bash
python app.py
```
O terminal mostrará uma mensagem como esta:
`Endereço para os APKS: http://192.168.1.15:5000`

**Importante:** Anote esse número de IP (ex: `192.168.1.15`).

---

## 3. Conectar os Apps (APK) à API
Para que os APKs no celular achem o seu notebook, você deve atualizar a URL nos arquivos HTML **antes** de gerar o APK.

### No `app.html` e `admin.html`:
No topo do `<script>`, coloque o IP que apareceu no seu terminal:
```javascript
const API_URL = "http://SEU_IP_AQUI:5000"; // Ex: http://192.168.1.15:5000
```

---

## 4. Dicas de Ouro para Rede Local
1. **Mesmo Wi-Fi**: O seu notebook e o seu celular Android **devem** estar conectados na mesma rede Wi-Fi.
2. **Firewall**: Se o app não conectar, pode ser que o Firewall do Windows esteja bloqueando a porta 5000. Tente desativar temporariamente ou permitir a porta 5000.
3. **IP Dinâmico**: O IP do seu notebook pode mudar se você reiniciar o roteador. Se o app parar de funcionar, verifique se o IP no terminal do Python ainda é o mesmo.

---

## 5. Vantagem do Banco de Dados Local
- O arquivo `dados.db` será criado automaticamente na pasta raiz do projeto.
- Todas as clientes que você cadastrar no Admin ficarão salvas nesse arquivo no seu notebook.
- Se você quiser fazer um backup, basta copiar o arquivo `dados.db`.
