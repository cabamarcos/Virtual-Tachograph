# Utiliza la imagen base de Python
FROM python:3.12.1-alpine

# Crea y define el directorio de trabajo
WORKDIR /etc/usr/src/app

# Copia el contenido del directorio local `./code` al contenedor
COPY ./code /etc/usr/src/app

# Instala las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt
RUN apk add --no-cache bash



# Ejecuta el componente correspondiente
CMD ["python", "ControlUnitSimulator.py"]
