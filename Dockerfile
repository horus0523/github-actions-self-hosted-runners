FROM python:3.13-slim

WORKDIR /app

# Crear requirements.txt si no existe o copiarlo si existe
COPY requirements.txt* ./

# Instalar dependencias (si requirements.txt existe)
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copiar el código fuente
COPY src/ ./

# Exponer puerto (ajusta según tu aplicación)
EXPOSE 8000

# Comando por defecto
CMD ["python", "main.py"]