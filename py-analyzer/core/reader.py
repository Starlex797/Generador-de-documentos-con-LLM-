# reader.py — Lectura y carga de archivos .py
from pathlib import Path
from loguru import logger

# Creamos una carpeta para guadar todos los logs. 
logger.add("debug_proyecto.log", rotation="1 MB",retention="1 week") # Guada todos los logs en el archivo debug_proye

def leer_codigo_fuente(nombre_archivo: str):
    ruta = Path(nombre_archivo) # Path() es una clase que nos permite manejar rutas de archivos de manera más sencilla.
    
    # Log de inicio de proceso
    logger.info(f"Intentando leer el archivo: {nombre_archivo}")

    if not ruta.exists():
        # Log de error si no existe
        logger.error(f"Archivo no encontrado en la ruta: {ruta.absolute()}")
        return None
    
    try: # try-except nos permite manejar errores de manera más sencilla.
        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()
        # With nos permite abrir y cerrar archivos de manera más sencilla.
        # Log de éxito si todo salió bien
        logger.success(f"Archivo '{nombre_archivo}' leído correctamente ({len(contenido)} caracteres)")
        return contenido
            
    except Exception as e:
        # Log de excepción crítica con todos los detalles del error
        logger.exception(f"Fallo crítico al leer {nombre_archivo}: {e}")
        return None


