import os
from loguru import logger
from core.tree_generator import generar_arbol_contexto  # Fase 1
from core.reader import compilar_contexto_repositorio
from core.ai_engine import preparar_prompt_repo, SECCIONES, preparar_prompt_map
from core.ai_engine import preparar_prompt_chunking, preparar_prompt_repo_iterativo #Fase 3 
from core.parser import analizar_codigo_ast, procesar_archivo_multilenguaje
from dotenv import load_dotenv
import sys
import requests
import json
from datetime import datetime 
from core.reader import leer_codigo_fuente
import time
from core.ai_engine import preparar_prompt_archivo_unico
from core.reader import contar_tokens

# --- CONFIGURACIÓN ---
RUTA_PROYECTO = r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\VB.NET-PROJECTS-master"
#r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\Arquitectura_Rag_con_LLM"
ARCHIVO_SOLO = r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\Generador-de-documentos-con-LLM-\venv\Lib\site-packages\marshmallow\fields.py"
 #r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\Arquitectura_Rag_con_LLM\Rag.py"
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
        "groq_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions"),
        "groq_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "groq_api_key": os.getenv("GROQ_API_KEY")
    }

    if config["backend"] not in ["groq"]:
        logger.error(f"Error: BACKEND inválido '{config['backend']}'.")
        sys.exit(1)

    if not config["groq_api_key"]:
        logger.error("Error: BACKEND=groq requiere GROQ_API_KEY.") 
        sys.exit(1)

    return config


def realizar_peticion_llm(mensajes, config):
    """Encapsula la lógica de comunicación con el backend (Groq/Ollama)."""
    is_groq = config["backend"] == "groq"
    url = config["groq_url"] if is_groq else config["ollama_url"]
    
    headers = {"Content-Type": "application/json"}
    if is_groq:
        headers["Authorization"] = f"Bearer {config['groq_api_key']}"

    payload = {
        "messages": mensajes,
        "temperature": config["temperature"],
        "model": config["groq_model"] if is_groq else config["ollama_model"]
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def guardar_resultado(contenido, sub_destino, prefijo, ahora):
    """Gestiona la persistencia de los informes en disco."""
    ruta_subcarpeta = os.path.join(CARPETA_BASE, sub_destino)
    os.makedirs(ruta_subcarpeta, exist_ok=True)
    
    indice = obtener_indice_archivo(ruta_subcarpeta)
    nombre_final = f"{indice}_INFORME_{prefijo}_{ahora}.md"
    ruta_completa = os.path.join(ruta_subcarpeta, nombre_final)
    
    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido)
    return ruta_completa

@logger.catch
def procesar_archivo_individual(archivo:dict, config:dict, es_modo_repo:bool=False)-> str:
    """ Decide la estrategia de procesamiento para un solo archivo y devuelve su Markdown
    Si es modo repo=True, genera resumenes. Si es Falase, genera informes definitivos para un archivo"""
    nombre= str(archivo['nombre'])
    contenido= archivo['contenido']
    tokens_totales= archivo['tokens'] # Tokens totales del archivo or archivo.get("tokens", 0)
    extension = os.path.splitext(nombre)[1].lower()
    limite_tokens = 10000

    logger.info(f"Analizando archivo: {nombre} ({tokens_totales} tokens)")
    
    # Caso 1: Archivo pequeño 
    if tokens_totales < 1000:
        if es_modo_repo:
            logger.info(f"Archivo {nombre} manejable → se genera resumen.")
            mensajes= preparar_prompt_map(nombre, contenido)
        else:
            logger.info(f"Archivo {nombre} manejable → se genera informe completo.")
            mensajes= preparar_prompt_archivo_unico(nombre, contenido, SECCIONES)

        informe= realizar_peticion_llm(mensajes, config)
        #Respetamos el Rate limit de Groq 
        logger.info("Esperando 10 segundos tras procesar archivo pequeño.")
        time.sleep(10)
        return informe 
    
    #Caso 2: Archivo grande 
    # Lógica del Chunking 
    
    logger.info(f"📦 Fragmentación requerida para {nombre} ({tokens_totales} tokens)")
    if extension == ".py":
        logger.info("Fragmentando archivo .py con AST...")
        #Usamos extracción por funciones y clases
        chunk_dict = analizar_codigo_ast(contenido)
        if chunk_dict:
            fragmentos_finales = [f["codigo"] for f in chunk_dict.get("funciones", [])]
            for c in chunk_dict.get("clases", []):
                fragmentos_finales.append(c.get("codigo_firma", ""))
                for m in c.get("metodos", []):
                        fragmentos_finales.append(f"Clase {c['nombre']} -> Método: {m['nombre']}\n{m.get('codigo', '')}")
            logger.info(f"Diccionario AST normalizado a {len(fragmentos_finales)} fragmentos.")
        else:
            logger.warning(f"Fallo en AST para {archivo['nombre']}. Usando modo backup.")
            fragmentos_finales = [archivo["contenido"]]
    
                
    else:
        # LlamaIndex para otros lenguajes (Markdown, JS, etc.)
        nodos = procesar_archivo_multilenguaje(
            archivo["contenido"], str(archivo["nombre"]),
            chunk_size=100, chunk_overlap=20 
            )
        fragmentos_finales = [n.get_content() for n in nodos]
        logger.info(f"LlamaIndex → {len(fragmentos_finales)} fragmentos.")     

    # --- BUCLE DE REFINAMIENTO ---
    informe_acumulado = ""
    chunks_pendientes = fragmentos_finales
    
    while chunks_pendientes:
        mensajes, num_procesados = preparar_prompt_chunking(
            nombre, chunks_pendientes, informe_previo=informe_acumulado, limite_tokens=limite_tokens
        )
        #ESCUDO ANTI-BUCLES INFINITOS
        if num_procesados == 0:
            logger.error(f"¡Atasco detectado! Un fragmento es más grande que el límite de tokens {limite_tokens}.")
            logger.warning("Descartando fragmento gigante para poder continuar...") #Deberíamos poner el número de tokens de ese chunk 
            chunks_pendientes = chunks_pendientes[1:] # Lo eliminamos a la fuerza para avanzar 
            continue # Saltamos a la siguiente iteración sin llamar al LLM (NO SE SI ESTO ESTÁ BIEN)

        
        logger.info(f"Enviando {num_procesados} fragmentos al LLM...")
        informe_acumulado = realizar_peticion_llm(mensajes, config)
        
        chunks_pendientes = chunks_pendientes[num_procesados:]
        progreso = ((len(fragmentos_finales) - len(chunks_pendientes)) / len(fragmentos_finales)) * 100
        logger.info(f"Progreso {nombre}: {progreso:.0f}%")
        
        if chunks_pendientes:
            logger.info("⏳ Esperando 30s para liberar cuota de tokens (TPM)...")
            time.sleep(40)
            
    return informe_acumulado

def procesar_repositorio_completo(archivos: list, arbol: str, config: dict, ahora: str):
    """Procesa todos los archivos y genera un informe maestro usando lotes (Batches)."""
    
    informe_global_acumulado = ""
    lote_actual = ""
    tokens_lote = 0
    LIMITE_TOKENS_LOTE = 4000 # Enviamos al LLM cada vez que juntemos ~4k tokens de resúmenes
    
    for archivo in archivos:
        try:
            # 1. MAP: Generamos el informe de este archivo individual
            informe_archivo = procesar_archivo_individual(archivo, config, es_modo_repo=True)
            
            # Guardamos el backup individual
            guardar_resultado(informe_archivo, SUB_REPO, f"DOC_{os.path.basename(str(archivo['nombre']))}", ahora)
            
            # 2. Preparamos el texto a añadir al lote
            texto_añadir = f"\n\n### Archivo: {archivo['nombre']}\n{informe_archivo}"
            tokens_añadir = contar_tokens(texto_añadir)
            
            # 3. CONTROL DE LOTES (El secreto del escalado)
            if (tokens_lote + tokens_añadir) > LIMITE_TOKENS_LOTE:
                logger.info("📦 Lote de resúmenes lleno. Actualizando Informe Global Maestro...")
                mensajes = preparar_prompt_repo_iterativo(arbol, lote_actual, informe_global_acumulado)
                informe_global_acumulado = realizar_peticion_llm(mensajes, config)
                
                # Vaciamos el lote y metemos el archivo actual como el primero del nuevo lote
                lote_actual = texto_añadir
                tokens_lote = tokens_añadir
                
                logger.info("⏳ Esperando 25s tras actualizar el global (Rate Limit)...")
                time.sleep(25)
            else:
                # Si hay espacio, seguimos llenando el lote
                lote_actual += texto_añadir
                tokens_lote += tokens_añadir
                
        except Exception as e:
            logger.error(f"Fallo al procesar {archivo['nombre']}: {e}")

    # 4. REDUCE FINAL: Si quedó algo en el lote tras terminar el bucle, hacemos la última llamada
    if lote_actual.strip():
        logger.info("🏁 Procesando el último lote para cerrar el Informe Global...")
        mensajes = preparar_prompt_repo_iterativo(arbol, lote_actual, informe_global_acumulado)
        informe_global_acumulado = realizar_peticion_llm(mensajes, config)

    # 5. Guardamos el resultado definitivo
    ruta = guardar_resultado(informe_global_acumulado, SUB_REPO, "INFORME_MAESTRO_FINAL", ahora)
    logger.success(f"🏆 Documentación completa del repositorio guardada en: {ruta}")
        
"""
def procesar_repositorio_completo(archivos: list, arbol: str, config: dict, ahora: str):
  
    resumenes_individuales = ""
    
    # 1. FASE MAP (Procesar cada archivo)
    for archivo in archivos:
        try:
            informe_archivo = procesar_archivo_individual(archivo, config, es_modo_repo=True)
            
            # Guardamos el backup individual
            guardar_resultado(informe_archivo, SUB_REPO, f"DOC_{os.path.basename(str(archivo['nombre']))}", ahora)
            
            # Acumulamos para el informe final
            resumenes_individuales += f"\n\n### Archivo: {archivo['nombre']}\n{informe_archivo}"
            
        except Exception as e:
            logger.error(f"Fallo al procesar {archivo['nombre']}: {e}")

    # 2. FASE REDUCE (Generar el Informe Maestro)
    logger.info("🧠 Generando Informe Global del Repositorio...")
    
   # 
    mensajes_finales = preparar_prompt_repo(arbol, resumenes_individuales, SECCIONES)
    
    informe_global = realizar_peticion_llm(mensajes_finales, config)
    ruta = guardar_resultado(informe_global, SUB_REPO, "INFORME_MAESTRO", ahora)
    logger.success(f"🏆 Documentación completa del repositorio guardada en: {ruta}")

"""

@logger.catch
def ejecutar_generador():
    logger.info("🚀 Iniciando proceso RAG Documentador...")
    config = load_config()
    ahora = datetime.now().strftime("%Y%m%d_%H%M%S")

    # FASE 1: Obtener Árbol
    arbol = generar_arbol_contexto(RUTA_PROYECTO)
    if not arbol: 
        logger.error("No se pudo generar el árbol. Abortando.")
        return

    # FASE 2: Enrutamiento (Router)
    if ARCHIVO_SOLO and os.path.exists(ARCHIVO_SOLO):
        logger.info("⚙️ MODO: Archivo Individual")
        contenido, num_tokens = leer_codigo_fuente(ARCHIVO_SOLO)
        archivo_dict = {"nombre": os.path.basename(ARCHIVO_SOLO), "contenido": contenido, "tokens": num_tokens}
        
        # Llamamos a la lógica individual
        informe_final = procesar_archivo_individual(archivo_dict, config)
        # Si no se nombre la variable es_modo_repo, se asume False, establecido por defecto

        if informe_final:
            ruta = guardar_resultado(informe_final, SUB_SINGLE, "FILE", ahora)
            logger.success(f"✅ Informe guardado en: {ruta}")
        else:
            logger.error("❌ El proceso terminó pero el informe está vacío. No se guardará nada.")

    else:
        logger.info("⚙️ MODO: Repositorio Completo")
        archivos_a_procesar = compilar_contexto_repositorio(RUTA_PROYECTO)
        
        if not archivos_a_procesar:
            logger.warning("No se encontraron archivos válidos para procesar.")
            return
            
        # Llamamos a la lógica de repositorio
        procesar_repositorio_completo(archivos_a_procesar, arbol, config, ahora)

if __name__ == "__main__":
    ejecutar_generador()


"""
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


    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red o de la API al conectar con {config['backend']}: {e}")
        if response is not None and response.text:
            logger.error(f"Detalle del servidor: {response.text}")
    except Exception as e:
        logger.exception(f"Error inesperado procesando la respuesta: {e}")
"""


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