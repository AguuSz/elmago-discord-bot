# 🤖 Discord Bot para Reemplazo de URLs

Este proyecto es un bot de Discord que permite reemplazar URLs de Twitter, Instagram y Reddit con sus respectivas versiones optimizadas para una mejor visualización en Discord (embeddings). El bot responde a comandos específicos y también puede interactuar cuando se le menciona.

## ✨ Funcionalidades

- 🐦 Reemplazo de URLs de Twitter/X con `vxtwitter.com`.
- 📸 Reemplazo de URLs de Instagram con `kkinstagram.com`.
- 👽 Reemplazo de URLs de Reddit con `rxddit.com`.

## 💻 Requisitos

- Python 3.8 o superior
- Biblioteca `discord.py` (instalación mediante `pip install discord.py`)

## ⚙️ Configuración

Para ejecutar el bot, necesitarás un archivo `.env` que contenga el token de tu bot de Discord.

### 🗃️ Creación del archivo `.env`

1. Crea un archivo llamado `.env` en la raíz de tu proyecto.
2. Agrega la siguiente línea, reemplazando `YOUR_DISCORD_BOT_TOKEN` con el token de tu bot:

   ```plaintext
   DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
   ```

## 🚀 Ejecución

Una vez que hayas configurado el archivo `.env`, puedes ejecutar el bot con el siguiente comando:

```bash
python app.py
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si deseas mejorar el bot, siéntete libre de abrir un issue o un pull request.
