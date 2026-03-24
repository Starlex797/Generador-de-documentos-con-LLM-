# reader.py — Lectura y carga de archivos .py
from pathlib import Path
from loguru import logger
import tiktoken



logger.add("debug_proyecto.log", rotation="1 MB", retention="1 week")

# ### NUEVO: Inicializamos el codificador (usamos cl100k_base que es el de GPT-4/Gemini) ###
encoding = tiktoken.get_encoding("cl100k_base")

def contar_tokens(texto: str) -> int:
    """Cuenta los tokens exactos de un string."""
    return len(encoding.encode(texto))

@logger.catch
def leer_codigo_fuente(ruta_archivo: str):
    ruta = Path(ruta_archivo)
    logger.info(f"Intentando leer el archivo: {ruta_archivo}")

    if not ruta.exists():
        logger.error(f"Archivo no encontrado en la ruta: {ruta.absolute()}")
        return None
    
    try:
        with open(ruta, "r", encoding="utf-8") as archivo: # Lectura del archivo
            contenido = archivo.read()
        
        # ### Calculamos tokens de este archivo específico ###
        num_tokens = len(encoding.encode(contenido))
        if num_tokens>=10000:
             logger.info("⚠️ ALERTA: Es necesario hacer Chunking")
        else: 
            logger.info("🚀 INFO: No es necesario hacer Chunking")
        logger.success(f"Archivo '{ruta.name}' leído: {len(contenido)} chars | {num_tokens} tokens")
        
        return contenido, num_tokens # Nos devuelve el contenido del archivo y el número de tokens
            
    except Exception as e:
        logger.exception(f"Fallo crítico al leer {ruta.name}: {e}")
        return None, 0

@logger.catch
def compilar_contexto_repositorio(ruta_directorio: str) -> list[dict]:
    directorio_raiz = Path(ruta_directorio)
    lista_archivos=[]
    for ruta_archivo in directorio_raiz.rglob("*"):
        if ruta_archivo.is_dir(): continue

        # --- FILTROS (Igual que los tenías) ---
        carpetas_a_ignorar = {".git", "__pycache__", "chroma_db", "venv"}
        if any(carpeta in ruta_archivo.parts for carpeta in carpetas_a_ignorar): continue
            
        extensiones_validas = [".py", ".md", ".json", ".txt"]
        if ruta_archivo.suffix.lower() not in extensiones_validas: continue
        
        archivos_a_ignorar = {".gitignore", "README.md", "RAG1.PY", "Rag - copia.py", "app - copia.py", "app1.py", "ML.py", "Formación_Estructural.pdf", "dataset_info.txt", "CE_4.pdf"}
        if ruta_archivo.name in archivos_a_ignorar: continue
            
        if "- copia" in ruta_archivo.name.lower(): continue

        # --- LECTURA Y CONTEO ---
        texto_extraido, tokens_archivo = leer_codigo_fuente(str(ruta_archivo)) # Se pone así cuando la función devuleve dos resultados, en este caso contenido y num tokens
        
        if texto_extraido: # OJO pongo todo el código de los diferentes archivos en una varoable. Están etiquetadas pero no es la mejor opción por la ventana de contexto. 
            lista_archivos.append({
                "nombre":ruta_archivo,
                "contenido":texto_extraido,
                "tokens":tokens_archivo
            })
            logger.info(f"Archivo '{ruta_archivo.name}' leído correctamente | {tokens_archivo} tokens")

    logger.info(f"Proceso finalizado.")
    return  lista_archivos


if __name__ == "__main__":
    carpeta_repo = r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\Arquitectura_Rag_con_LLM"
    
    # ### MODIFICADO para recibir los dos valores ###
    texto_final = compilar_contexto_repositorio(carpeta_repo)
    
    with open("contexto_para_llm.txt", "r",encoding="utf-8") as f:
        f.write(texto_final)
        
    print(f"\n✅ Proceso completado.")
    print(f"📊 TOTAL DE TOKENS DEL PROYECTO: {total_tokens}")
    
    