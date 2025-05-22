FROM python:3.11.1

# Crear directorio de trabajo
WORKDIR /etc/usr/src/app

# Copiar los archivos desde ./code
COPY ./code /etc/usr/src/app

# Instalar dependencias
COPY ./code/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Ejecutar el microservicio
CMD ["python", "devices_manager_api.py"]