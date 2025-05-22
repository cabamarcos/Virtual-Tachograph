FROM python:3.11.1

# Directorio de trabajo dentro del contenedor
WORKDIR /etc/usr/src/app

# Copiar el código fuente
COPY ./code /etc/usr/src/app

# Instalar dependencias
COPY ./code/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Ejecutar microservicio
CMD ["python", "sessions_manager_api.py"]