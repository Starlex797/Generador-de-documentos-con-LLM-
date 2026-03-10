import os
from loguru import logger
from core.tree_generator import generar_arbol_contexto  # Fase 1
from core.reader import compilar_contexto_repositorio    # Fase 2
from core.reader import leer_codigo_fuente
from core.ai_engine import preparar_prompt_final, SECCIONES # Fase 3
from dotenv import load_dotenv
import sys
import requests
import json
from datetime import datetime 




# --- CONFIGURACIÓN ---
RUTA_PROYECTO = r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\Arquitectura_Rag_con_LLM"
ARCHIVO_SOLO = r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\Arquitectura_Rag_con_LLM\Rag.py"
CARPETA_BASE= "salida_de_informes"
#------------------------
# Subcarpetas 
#------------------------
SUB_SINGLE= "archivos_individuales"
SUB_REPO= "archivos_repo"

def obtener_indice_archivo(ruta_carpeta:str)->int:
    if not os.path.exists(ruta_carpeta):
        return 1
    archivos = [f for f in os.listdir(ruta_carpeta) if f.endswith(".md")]
    return len(archivos) + 1


def load_config():
    """Carga y valida la configuración desde variables de entorno."""
    load_dotenv()

    config = {
        "backend": os.getenv("BACKEND", "ollama").lower(),
        "temperature": float(os.getenv("TEMPERATURE", "0.2")), # Recomiendo 0.2 para código, 0.0 a veces es muy rígido
        "ollama_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1/chat/completions"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "tinyllama"),
        "groq_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions"),
        "groq_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "groq_api_key": os.getenv("GROQ_API_KEY"),
    }

    if config["backend"] not in ["ollama", "groq"]:
        logger.error(f"Error: BACKEND inválido '{config['backend']}'.")
        sys.exit(1)

    if config["backend"] == "groq" and not config["groq_api_key"]:
        logger.error("Error: BACKEND=groq requiere GROQ_API_KEY.") 
        sys.exit(1)

    return config

@logger.catch
def ejecutar_generador():
    logger.info("🚀 Iniciando el proceso de documentación automática...")
    config = load_config()
    ahora = datetime.now().strftime("%Y%m%d_%H%M%S") # Para conseguir el tiempo y el dia
    # 1. GENERAR EL ÁRBOL (Fase 1)
    arbol = generar_arbol_contexto(RUTA_PROYECTO)
    if not arbol:
        logger.error("No se pudo generar el árbol. Abortando.")
        return

    # 2. COMPILAR CÓDIGO Y TOKENS (Fase 2)
    if ARCHIVO_SOLO and os.path.exists(ARCHIVO_SOLO):
        logger.info(f"Procesando 1 archivo {os.path.basename(ARCHIVO_SOLO)}")
        sub_destino= SUB_SINGLE 
        prefijo ="FILE"
        codigo, total_tokens= leer_codigo_fuente(ARCHIVO_SOLO)
        logger.info(f"Contexto listo. Tamaño: {total_tokens} tokens.")
        
    else:
      logger.info("Modo: Repositorio")
      sub_destino= SUB_REPO 
      codigo, total_tokens = compilar_contexto_repositorio(RUTA_PROYECTO)
      logger.info(f"Contexto listo. Tamaño total: {total_tokens} tokens.")
   

    # 3. PREPARAR EL PROMPT (Fase 3)
    mensajes_llm = preparar_prompt_final(arbol, codigo, SECCIONES)
    
    # --- 4. LLAMADA A LA IA (INFERENCIA REAL) ---
    logger.info("\n--- 🤖 ENVIANDO DATOS AL LLM ---")
    
    # Preparamos el "paquete" (Payload) estándar para APIs compatibles con OpenAI
    payload = {
        "messages": mensajes_llm,
        "temperature": config["temperature"]
    }
    
    headers = {"Content-Type": "application/json"}

    # Configuramos los datos según el backend elegido
    if config["backend"] == "groq":
        logger.info(f"Usando Groq | Modelo: {config['groq_model']}")
        url = config["groq_url"]
        payload["model"] = config["groq_model"]
        headers["Authorization"] = f"Bearer {config['groq_api_key']}"
    else:
        logger.info(f"Usando Ollama | Modelo: {config['ollama_model']}")
        url = config["ollama_url"]
        payload["model"] = config["ollama_model"]
        # Ollama local normalmente no requiere Authorization

    try:
        logger.info("Esperando respuesta de la IA (esto puede tardar unos segundos/minutos)...")
        # Hacemos la petición POST al servidor
        response = requests.post(url, headers=headers, json=payload)
        
        # Lanza un error si la respuesta del servidor no es 200 OK
        response.raise_for_status() 
        
        # Extraemos el texto del JSON que nos devuelve la API
        respuesta_json = response.json()

        informe_generado = respuesta_json["choices"][0]["message"]["content"]
         
       # Gestión de carpetas 
        ruta_subcarpeta= os.path.join(CARPETA_BASE,sub_destino)
        os.makedirs(ruta_subcarpeta,exist_ok=True)

        indice= obtener_indice_archivo(ruta_subcarpeta)
        nombre_final=f"{indice}_INFORME_{prefijo}_{ahora}"
        ruta_completa_salida = os.path.join(ruta_subcarpeta, nombre_final)
        # --- 5. GUARDAR RESULTADO REAL ---
        with open(ruta_completa_salida, "w", encoding="utf-8") as f:
            f.write(informe_generado)
        logger.success(f"✅ Informe #{indice} guardado en: {ruta_completa_salida}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red o de la API al conectar con {config['backend']}: {e}")
        if response is not None and response.text:
            logger.error(f"Detalle del servidor: {response.text}")
    except Exception as e:
        logger.exception(f"Error inesperado procesando la respuesta: {e}")

if __name__ == "__main__":
    ejecutar_generador()


"""# ... (carga de config y generación de árbol)

# 1. Obtener la lista de archivos individuales
lista_archivos = obtener_lista_archivos(RUTA_PROYECTO)
logger.info(f"Se procesarán {len(lista_archivos)} archivos individualmente.")

resumenes_mapeados = []

# 2. Bucle MAP: Procesar cada archivo
for archivo in lista_archivos:
    logger.info(f"📝 Generando resumen para: {archivo['nombre']}")
    
    # Preparamos el prompt específico para este archivo
    mensajes_map = preparar_prompt_map(archivo['nombre'], archivo['contenido'])
    
    # Realizamos la petición (reutilizando tu lógica de requests)
    payload = {
        "messages": mensajes_map,
        "temperature": 0.1, # Menor temperatura para mayor precisión técnica
        "model": config["ollama_model"] if config["backend"] == "ollama" else config["groq_model"]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        resumen = response.json()["choices"][0]["message"]["content"]
        
        # Guardamos el resultado del MAP
        resumenes_mapeados.append(f"## Análisis de {archivo['nombre']}\n{resumen}")
        
    except Exception as e:
        logger.error(f"Error procesando {archivo['nombre']}: {e}")

# 3. Guardar el resultado de la fase MAP
with open("RESUMENES_MAP.md", "w", encoding="utf-8") as f:
    f.write("# FASE 1: RESÚMENES INDIVIDUALES (MAP)\n\n")
    f.write("\n\n---\n\n".join(resumenes_mapeados))

logger.success("Fase de MAP completada. Revisa RESUMENES_MAP.md")"""