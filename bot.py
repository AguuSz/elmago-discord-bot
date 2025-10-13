import os
import re
import logging
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
    description="Reemplaza la URL de Twitter/X con la URL de VXTwitter para mejor visualización.",
)
@app_commands.describe(url="La URL de Twitter/X que se va a reemplazar")
async def replace_twitter(interaction: discord.Interaction, url: str):
    if "twitter.com" in url or "x.com" in url:
        new_url = url.replace("twitter.com", "vxtwitter.com").replace(
            "x.com", "vxtwitter.com"
        )
        await interaction.response.send_message(new_url)
        logger.info(f"URL de Twitter/X reemplazada: {url} -> {new_url}")
    else:
        await interaction.response.send_message(
            "URL tan invalida como vos.", ephemeral=True
        )
        logger.warning(f"Intento de reemplazo fallido para URL no válida: {url}")


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
