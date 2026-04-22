# Guia: Transformando o App em APK (Android)

Este projeto agora está configurado com o **Capacitor**, o que permite transformar seus arquivos HTML em um aplicativo Android real.

## 1. Pré-requisitos no seu PC
Para gerar o APK, você precisará ter instalado:
1.  **Node.js** (que você já deve ter para rodar o npm).
2.  **Android Studio**.
3.  **Java (JDK 17 ou superior)**.

## 2. Preparando os arquivos
Sempre que você alterar o `app.html` ou `admin.html`, siga estes passos:

1.  Copie os arquivos para a pasta `www`:
    ```bash
    # No terminal, na raiz do projeto:
    cp app.html www/index.html
    cp admin.html www/admin.html
    cp api_integration.js www/
    ```
    *Nota: O `app.html` é renomeado para `index.html` porque é a tela inicial do aplicativo.*

2.  Sincronize com o projeto Android:
    ```bash
    npx cap copy android
    ```

## 3. Gerando o APK no Android Studio
1.  Abra o **Android Studio**.
2.  Vá em `File > Open` e selecione a pasta **`android`** que está dentro do seu repositório `app-doula`.
3.  Espere o Gradle carregar tudo (pode demorar na primeira vez).
4.  No menu superior, vá em: **`Build > Build Bundle(s) / APK(s) > Build APK(s)`**.
5.  Quando terminar, uma notificação aparecerá no canto inferior direito. Clique em **`locate`** para encontrar o arquivo `app-debug.apk`.

## 4. Conectando ao seu PC (Servidor)
Para que o APK funcione, ele precisa saber o IP do seu computador:
1.  Abra o `app.html` (ou `index.html` na pasta www).
2.  Procure pela linha `const API_URL = "http://..."`.
3.  Coloque o IP que aparece quando você roda a API (ex: `http://192.168.1.15:5000`).
4.  **Importante**: O celular e o PC devem estar no **mesmo Wi-Fi**.

## 5. Dica para o App de Administração
Como o APK inicia pelo `index.html` (Cliente), você pode gerar um segundo APK para Administração alterando o passo 2.1:
*   Para o APK de Cliente: `cp app.html www/index.html`
*   Para o APK de Admin: `cp admin.html www/index.html`
*   Depois siga os passos de sincronização e build normalmente.
