# Universal Video Downloader

[🇧🇷 Leia em Português](#-português) | [🇺🇸 Read in English](#-english)

---

## 🇧🇷 Português

Um aplicativo simples para desktop (feito com Tkinter) que baixa vídeos do **YouTube, Reddit, X (Twitter), Instagram, TikTok** e cerca de 1000 outros sites. Nunca mais precise procurar um site para baixar vídeos!

### Pré-requisitos (Obrigatórios)

Para rodar este aplicativo, é **necessário** ter os seguintes itens na sua máquina:
1. **Python** instalado (lembre-se de marcar a opção "Add to PATH" na instalação).
2. A biblioteca **`yt-dlp`**.
3. A ferramenta **FFmpeg** (necessária para juntar vídeos em HD e converter MP3).

*(Nota: Na primeira vez que você rodar o aplicativo no Windows, o próprio código tentará baixar automaticamente a biblioteca `yt-dlp` via pip e o `ffmpeg` via comando winget!)*

### Como rodar o app

Para iniciar o aplicativo, basta dar um duplo clique no arquivo **`iniciar_app.bat`**. Ele detecta a pasta atual e abre o app de forma automática.

Se preferir rodar manualmente pelo terminal, use:
```bash
python video_downloader.py
```

### Uso de Cookies (Para vídeos restritos)

Para baixar vídeos de plataformas que exigem login, possuem restrição de idade ou são marcados como conteúdo sensível (como muitos posts do Reddit), o aplicativo precisa se autenticar no site. Para isso, ele utiliza um arquivo de cookies.

**Como coletar e configurar os cookies:**
1. Instale uma extensão no seu navegador chamada **"Get cookies.txt LOCALLY"** (ou similar, disponível para Chrome, Edge e Firefox).
2. Acesse o site do Reddit pelo navegador e certifique-se de estar logado na sua conta.
3. Clique na extensão para exportar os cookies daquela página e salve o arquivo gerado.
4. **IMPORTANTE:** Renomeie o arquivo salvo **exatamente** para `reddit_cookies.txt`.
5. Mova esse arquivo `reddit_cookies.txt` para dentro da mesma pasta onde está o aplicativo.

Com o arquivo posicionado corretamente, o aplicativo usará a sua sessão e conseguirá fazer o download de conteúdos restritos sem problemas.

### Como usar o aplicativo

1. Copie o link do vídeo (ou clique em **Paste** para pegar da área de transferência).
2. Escolha a **Qualidade** (o padrão é 720p). Escolha **Audio only (MP3)** para baixar apenas o áudio.
3. Clique em **Add to Queue**. Você pode adicionar quantos vídeos quiser, eles baixarão um após o outro.
4. Acompanhe o progresso pela barra. Clique em **Open download folder** quando terminar.

Os vídeos são salvos por padrão na pasta `downloads/` dentro do diretório do aplicativo. Você também pode clicar em **Browse** para escolher outra pasta. Seu histórico é salvo no arquivo `download_history.json`.

### 🤝 Sobre o Projeto e Contribuições

Este aplicativo foi desenvolvido com o auxílio de **Inteligência Artificial**. Sendo assim, o código e a estrutura podem sempre melhorar e evoluir. Sugestões, correções de bugs e novas implementações (Pull Requests) são sempre muito bem-vindas! Sinta-se à vontade para contribuir.

---

## 🇺🇸 English

A simple desktop application (built with Tkinter) that downloads videos from **YouTube, Reddit, X (Twitter), Instagram, TikTok**, and around 1000 other sites. Never search for a video downloader site again!

### Requirements (Mandatory)

To run this application, it is **required** to have the following installed on your machine:
1. **Python** (remember to check the "Add to PATH" option during installation).
2. The **`yt-dlp`** library.
3. The **FFmpeg** tool (required to merge HD videos and convert to MP3).

*(Note: The first time you run the application on Windows, the code itself will try to automatically download the `yt-dlp` library via pip and `ffmpeg` via the winget command!)*

### How to run the app

To start the application, just double-click the **`iniciar_app.bat`** file. It detects the current folder and automatically opens the app.

If you prefer to run it manually via the terminal, use:
```bash
python video_downloader.py
```

### Use of Cookies (For restricted videos)

To download videos from platforms that require a login, are age-restricted, or are marked as sensitive content (like many Reddit posts), the application needs to authenticate itself on the site. To do this, it uses a cookies file.

**How to collect and configure cookies:**
1. Install a browser extension called **"Get cookies.txt LOCALLY"** (or similar, available for Chrome, Edge, and Firefox).
2. Access the Reddit website through your browser and make sure you are logged into your account.
3. Click the extension to export the cookies from that page and save the generated file.
4. **IMPORTANT:** Rename the saved file **exactly** to `reddit_cookies.txt`.
5. Move this `reddit_cookies.txt` file into the same folder where the application is located.

With the file correctly placed, the application will use your session and will be able to download restricted content without issues.

### How to use the app

1. Copy the video link (or click **Paste** to grab it from your clipboard).
2. Choose the **Quality** (default is 720p). Choose **Audio only (MP3)** to download only the audio.
3. Click **Add to Queue**. You can add as many videos as you want, they will download one after another.
4. Track the progress via the progress bar. Click **Open download folder** when finished.

Videos are saved by default in the `downloads/` folder inside the application's directory. You can also click **Browse** to choose a different folder. Your history is saved in the `download_history.json` file.

### 🤝 About the Project & Contributions

This application was developed with the assistance of **Artificial Intelligence**. Because of this, the code and structure can always improve and evolve. Suggestions, bug fixes, and new features (Pull Requests) are always very welcome! Feel free to contribute.
