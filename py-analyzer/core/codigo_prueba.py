RUTA_PROYECTO = r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\Arquitectura_Rag_con_LLM"
ARCHIVO_SALIDA = "INFORME_TECNICO_RAG.md"

def load_config(): # carga la configuración desde variables de entorno
    """Carga y valida la configuración desde variables de entorno."""
    load_dotenv() # carga las variables de entorno

    config = {
        "backend": os.getenv("BACKEND", "ollama").lower(), # os.getenv() es una función que retorna el valor de una variable de entorno.Y
        # si no existe la variable de entorno, retorna el valor por defecto que le pasamos (Que en este caso es "ollama").
        "temperature": float(os.getenv("TEMPERATURE", "0.0")),
        "ollama_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1/chat/completions"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "tinyllama"),
        "groq_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions"),
        "groq_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "groq_api_key": os.getenv("GROQ_API_KEY"),
    }

    if config["backend"] not in ["ollama", "groq"]: # 
        print(f"Error: BACKEND inválido '{config['backend']}'.")
        sys.exit(1)

    if config["backend"] == "groq" and not config["groq_api_key"]: # si el backend es groq y no hay api key
        print("Error: BACKEND=groq requiere GROQ_API_KEY.") 
        sys.exit(1) # sale del programa

    return config # retorna la configuración. Es decir, nos está dando las variables de entorno


@logger.catch
def ejecutar_generador():

    logger.info("🚀 Iniciando el proceso de documentación automática...")
    config = load_config()
    # 1. GENERAR EL ÁRBOL (Fase 1)
    # Obtenemos el esquema visual para que la IA entienda la jerarquía
    arbol = generar_arbol_contexto(RUTA_PROYECTO)
    if not arbol:
        logger.error("No se pudo generar el árbol. Abortando.")
        return

    # 2. COMPILAR CÓDIGO Y TOKENS (Fase 2)
    # Filtramos la 'basura' y unimos el código útil
    codigo, total_tokens = compilar_contexto_repositorio(RUTA_PROYECTO)
    logger.info(f"Contexto listo. Tamaño total: {total_tokens} tokens.")

    # 3. PREPARAR EL PROMPT (Fase 3)
    # Organizamos la información por roles y secciones
    mensajes_llm = preparar_prompt_final(arbol, codigo, SECCIONES)
    
    # 4. LLAMADA A LA IA (Simulación de conexión)
    # Aquí es donde conectarías con 'client.chat.completions.create' o similar
    logger.info("\n--- 🤖 ENVIANDO DATOS AL LLM ---")
    logger.info(f"Enviando {len(mensajes_llm)} mensajes estructurados...")

    if config["backend"] == "ollama":
        logger.info("Usando Ollama")
    else:
        logger.info("Usando Groq")
    # NOTA: En este punto, el LLM procesará la anatomía del prompt maestro
    # y generará el informe basado en las instrucciones de salida.

    # 5. GUARDAR RESULTADO
    # Supongamos que 'respuesta_ia' es lo que devuelve el modelo
    # Con fines de prueba, guardaremos el prompt completo para que lo veas
    with open("PROMPT_GENERADO.txt", "w", encoding="utf-8") as f:
        f.write(str(mensajes_llm))
    
    logger.success(f"¡Proceso finalizado! Revisa {ARCHIVO_SALIDA} (o el prompt generado).")

if __name__ == "__main__":
    ejecutar_generador()