import os
import re
import logging
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!!", intents=intents)


# Funciones auxiliares
def suppress_url_previews(text: str) -> str:
    """Envuelve URLs en <> para evitar que Discord muestre previews."""
    if not text:
        return text
    # Patrón para detectar URLs (http, https)
    url_pattern = r'(https?://[^\s<>]+)'
    # Reemplazar URLs que no estén ya envueltas en <>
    def wrap_url(match):
        url = match.group(1)
        return f"<{url}>"
    return re.sub(url_pattern, wrap_url, text)


def extract_tweet_id(url: str) -> str:
    """Extrae el ID del tweet de una URL de Twitter/X."""
    logger.info(f"Intentando extraer tweet ID de: {url}")
    patterns = [
        r"(?:twitter\.com|x\.com)/(?:\w+)/status/(\d+)",
        r"(?:twitter\.com|x\.com)/i/(?:web/)?status/(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            tweet_id = match.group(1)
            logger.info(f"Tweet ID extraído exitosamente: {tweet_id}")
            return tweet_id
    logger.error(f"No se pudo extraer tweet ID de la URL: {url}")
    return None


async def download_twitter_video(url: str, output_dir: str):
    """
    Descarga un video de Twitter usando yt-dlp y extrae sus metadatos.
    Retorna un diccionario con la información del video o dict con 'error' si falla.
    """
    logger.info(f"=== Iniciando descarga de video ===")
    logger.info(f"URL: {url}")
    logger.info(f"Directorio destino: {output_dir}")

    tweet_id = extract_tweet_id(url)
    if not tweet_id:
        error_msg = "No se pudo extraer el ID del tweet de la URL"
        logger.error(error_msg)
        return {"error": error_msg}

    # Formato preferido (basado en server.js)
    format_pref = "http-2176/http-832/http-288/best[protocol*=https][ext=mp4]/best"
    output_template = str(Path(output_dir) / f"{tweet_id}.%(ext)s")

    # Separador para parsing (mismo que server.js)
    sep = "␟"

    # Construir comando
    # Usamos --print after_video: para asegurar que descarga ANTES de imprimir
    cmd_args = [
        "yt-dlp",
        "-f", format_pref,
        "--no-playlist",
        "--print", f"after_video:%(url)s{sep}%(title)s{sep}%(thumbnail)s{sep}%(uploader)s{sep}%(uploader_id)s{sep}%(description)s{sep}%(upload_date)s",
        "-o", output_template,
        url,
    ]

    logger.info(f"Comando yt-dlp: {' '.join(cmd_args)}")

    try:
        # Ejecutar yt-dlp para obtener metadatos y descargar
        logger.info("Ejecutando yt-dlp...")
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        logger.info("Esperando resultado de yt-dlp (timeout: 60s)...")
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)

        stdout_text = stdout.decode().strip()
        stderr_text = stderr.decode().strip()

        logger.info(f"yt-dlp return code: {process.returncode}")
        logger.info(f"yt-dlp stdout: {stdout_text[:500]}")  # Primeros 500 chars
        if stderr_text:
            logger.warning(f"yt-dlp stderr: {stderr_text[:500]}")

        if process.returncode != 0:
            error_msg = f"yt-dlp falló con código {process.returncode}. Error: {stderr_text}"
            logger.error(error_msg)
            return {"error": error_msg}

        # Parsear salida
        output = stdout_text
        parts = output.split(sep)

        logger.info(f"Partes extraídas de yt-dlp: {len(parts)}")

        if len(parts) < 7:
            error_msg = f"Output de yt-dlp inesperado (esperaba 7 partes, obtuvo {len(parts)}): {output[:200]}"
            logger.error(error_msg)
            return {"error": error_msg}

        video_url, title, thumbnail, uploader, uploader_id, description, upload_date = parts
        logger.info(f"Metadatos extraídos - Autor: {uploader} (@{uploader_id}), Título: {title[:50]}")

        # Buscar archivo descargado
        logger.info(f"Buscando archivos descargados en: {output_dir}")
        video_files = list(Path(output_dir).glob(f"{tweet_id}.*"))
        logger.info(f"Archivos encontrados: {[str(f) for f in video_files]}")

        if not video_files:
            error_msg = f"No se encontró archivo de video descargado en {output_dir}"
            logger.error(error_msg)
            # Listar todos los archivos en el directorio
            all_files = list(Path(output_dir).glob("*"))
            logger.error(f"Archivos en directorio: {[str(f) for f in all_files]}")
            return {"error": error_msg}

        video_path = str(video_files[0])
        file_size = Path(video_path).stat().st_size
        logger.info(f"Video descargado: {video_path} ({file_size / (1024*1024):.2f}MB)")

        return {
            "file_path": video_path,
            "title": title.strip(),
            "thumbnail": thumbnail.strip(),
            "uploader": uploader.strip(),
            "uploader_id": uploader_id.strip(),
            "description": description.strip(),
            "upload_date": upload_date.strip(),
        }

    except asyncio.TimeoutError:
        error_msg = "Timeout (60s) al descargar video de Twitter"
        logger.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Excepción al descargar video: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}


@bot.event
async def on_ready():
    logger.info("El bot está listo")
    logger.info(
        f"Invita al bot con el siguiente enlace: {discord.utils.oauth_url(bot.user.id)}"
    )
    try:
        synced = await bot.tree.sync()
        logger.info(f"Se sincronizaron {len(synced)} comandos")
    except Exception as e:
        logger.error(f"Fallo al sincronizar los comandos: {e}")


@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@bot.tree.command(
    name="vx",
    description="Descarga y envía el video de Twitter/X con información del autor.",
)
@app_commands.describe(url="La URL de Twitter/X del video a descargar")
async def replace_twitter(interaction: discord.Interaction, url: str):
    logger.info(f"=== Comando /vx ejecutado por {interaction.user.name} ===")
    logger.info(f"URL proporcionada: {url}")

    # Validar URL
    if not ("twitter.com" in url or "x.com" in url):
        error_msg = f"URL inválida (no contiene twitter.com o x.com): {url}"
        logger.warning(error_msg)
        await interaction.response.send_message(
            "URL tan invalida como vos.", ephemeral=True
        )
        return

    # Defer response para evitar timeout (la descarga puede tomar tiempo)
    logger.info("Deferiendo respuesta de Discord...")
    await interaction.response.defer()
    logger.info("Respuesta diferida exitosamente")

    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Directorio temporal creado: {temp_dir}")

    try:
        # Descargar video
        logger.info(f"Iniciando descarga de video...")
        video_data = await download_twitter_video(url, temp_dir)

        # Verificar si hubo error
        if "error" in video_data:
            error_msg = video_data["error"]
            logger.error(f"Error en descarga: {error_msg}")
            # Enviar error detallado a Discord
            await interaction.followup.send(
                f"❌ **Error al descargar video:**\n```\n{error_msg[:1800]}\n```",
                ephemeral=True,
            )
            return

        logger.info("Video descargado exitosamente, procesando datos...")

        # Verificar tamaño del archivo
        video_path = Path(video_data["file_path"])
        file_size = video_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        max_size = 50 * 1024 * 1024  # 50MB (para servidores con boost)

        logger.info(f"Tamaño del archivo: {file_size_mb:.2f}MB")

        if file_size > max_size:
            error_msg = f"Video demasiado grande: {file_size_mb:.1f}MB (límite: 50MB)"
            logger.warning(error_msg)
            await interaction.followup.send(
                f"❌ El video es demasiado grande ({file_size_mb:.1f}MB). Discord tiene un límite de 50MB.",
                ephemeral=True,
            )
            return

        # Preparar información del autor
        author_name = video_data.get("uploader", "").strip() or "Desconocido"
        author_handle = video_data.get("uploader_id", "").strip()
        display_handle = f"@{author_handle}" if author_handle else ""
        thumbnail_url = video_data.get("thumbnail", "").strip()

        logger.info(f"Metadatos - Autor: {author_name} ({display_handle})")

        # Formatear descripción
        description = video_data.get("description", "").strip()
        if description and len(description) > 280:
            description = description[:280]

        # Suprimir previews de URLs en la descripción
        if description:
            description = suppress_url_previews(description)

        # Preparar nombre de archivo para attachment
        video_filename = video_path.name

        # Crear embed enriquecido (estilo Twitter)
        embed = discord.Embed(
            description=description or "Video de X",
            color=0x1DA1F2  # Color azul claro de Twitter
        )

        # Agregar autor con handle
        if author_name and author_handle:
            # Usar unavatar.io para el avatar del autor
            avatar_url = f"https://unavatar.io/x/{author_handle}"
            embed.set_author(
                name=f"{author_name} ({display_handle})",
                icon_url=avatar_url
            )
        elif author_name:
            embed.set_author(name=author_name)

        # Agregar información adicional en footer
        embed.set_footer(text=f"Video • {file_size_mb:.1f}MB")

        # Enviar archivo con embed
        logger.info(f"Enviando video a Discord: {video_filename} ({file_size_mb:.2f}MB)")
        try:
            with open(video_path, "rb") as f:
                file = discord.File(f, filename=video_filename)
                await interaction.followup.send(embed=embed, file=file)

            logger.info(f"✅ Video enviado exitosamente de {author_name} ({file_size_mb:.2f}MB)")
        except discord.HTTPException as e:
            error_msg = f"Error HTTP de Discord: {e.status} - {e.text}"
            logger.error(error_msg)
            await interaction.followup.send(
                f"❌ **Error al subir el video a Discord:**\n```\n{error_msg[:1800]}\n```",
                ephemeral=True,
            )

    except Exception as e:
        error_msg = f"Excepción inesperada: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        try:
            await interaction.followup.send(
                f"❌ **Error al procesar el video:**\n```\n{error_msg[:1800]}\n```\nRevisá los logs para más detalles.",
                ephemeral=True,
            )
        except Exception as send_error:
            logger.error(f"No se pudo enviar mensaje de error: {send_error}")

    finally:
        # Limpiar archivos temporales
        logger.info("Limpiando archivos temporales...")
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"✅ Directorio temporal limpiado: {temp_dir}")
        except Exception as e:
            logger.error(f"Error limpiando archivos temporales: {e}")


@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@bot.tree.command(
    name="ig",
    description="Reemplaza la URL de Instagram con la URL de DDInstagram para el embed de Discord.",
)
@app_commands.describe(url="La URL de Instagram que se va a reemplazar")
async def replace_instagram(interaction: discord.Interaction, url: str):
    if "instagram.com" in url:
        new_url = url.replace("instagram.com", "kkinstagram.com")
        await interaction.response.send_message(new_url)
        logger.info(f"URL de Instagram reemplazada: {url} -> {new_url}")
    else:
        await interaction.response.send_message(
            "URL tan invalida como vos.", ephemeral=True
        )
        logger.warning(f"Intento de reemplazo fallido para URL no válida: {url}")


@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@bot.tree.command(
    name="rx",
    description="Reemplaza la URL de Reddit con la URL de RXReddit para el embed de Discord.",
)
@app_commands.describe(url="La URL de Reddit que se va a reemplazar")
async def replace_reddit(interaction: discord.Interaction, url: str):
    if "reddit.com" in url:
        new_url = url.replace("reddit.com", "rxddit.com")
        await interaction.response.send_message(new_url)
        logger.info(f"URL de Reddit reemplazada: {url} -> {new_url}")
    else:
        await interaction.response.send_message(
            "URL tan invalida como vos.", ephemeral=True
        )
        logger.warning(f"Intento de reemplazo fallido para URL no válida: {url}")


@bot.event
async def on_message(message: discord.Message):
    # Verifica si el mensaje menciona al bot
    if bot.user in message.mentions:
        await message.channel.send(f"Warap")
    # Asegúrate de procesar otros comandos
    await bot.process_commands(message)


# Cargar el token y ejecutar el bot
load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    logger.error("No se encontró el token del bot en las variables de entorno.")
else:
    bot.run(token)
