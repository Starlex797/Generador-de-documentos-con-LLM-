import os
from loguru import logger
from core.tree_generator import generar_arbol_contexto  # Fase 1
from core.reader import compilar_contexto_repositorio    # Fase 2
from core.ai_engine import preparar_prompt_final, SECCIONES # Fase 3
from dotenv import load_dotenv
import sys
import requests



# --- CONFIGURACIÓN ---
RUTA_PROYECTO = r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\Arquitectura_Rag_con_LLM"
ARCHIVO_SALIDA = "INFORME_TECNICO_RAG.md"

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
    
    # 1. GENERAR EL ÁRBOL (Fase 1)
    arbol = generar_arbol_contexto(RUTA_PROYECTO)
    if not arbol:
        logger.error("No se pudo generar el árbol. Abortando.")
        return

    # 2. COMPILAR CÓDIGO Y TOKENS (Fase 2)
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
        
        # --- 5. GUARDAR RESULTADO REAL ---
        with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
            f.write(informe_generado)
        
        logger.success(f"¡Proceso finalizado! Revisa el archivo: {ARCHIVO_SALIDA}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red o de la API al conectar con {config['backend']}: {e}")
        if response is not None and response.text:
            logger.error(f"Detalle del servidor: {response.text}")
    except Exception as e:
        logger.exception(f"Error inesperado procesando la respuesta: {e}")

if __name__ == "__main__":
    ejecutar_generador()