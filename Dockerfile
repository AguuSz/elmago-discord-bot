# Dockerfile

# 1. Usa una imagen base oficial de Python.
# 'slim' es una versión ligera, ideal para producción.
FROM python:3.10-slim

# 2. Establece el directorio de trabajo dentro del contenedor.
# Todas las acciones posteriores se realizarán aquí.
WORKDIR /app

# 3. Copia solo el archivo de dependencias primero.
# Esto aprovecha el caché de Docker. Si no cambias las dependencias,
# este paso no se volverá a ejecutar en futuras construcciones.
COPY requirements.txt .

# 4. Instala las dependencias.
# '--no-cache-dir' reduce el tamaño final de la imagen.
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia el resto del código de tu aplicación al contenedor.
COPY . .

# 6. Comando que se ejecutará cuando el contenedor inicie.
# Esto arranca tu bot.
CMD ["python", "bot.py"]