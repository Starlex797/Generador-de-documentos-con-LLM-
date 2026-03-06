from directory_tree import DisplayTree
import os # Para verificar que el directorio existe en mi pc
from loguru import logger
""" Genera un árbol de directorioos y archivos que explique la estructura del proyecto en formato texto,
    podemos ver qué archivos podemos ignorar para que no malgastar tokens en el LLM """
@logger.catch
def generar_arbol_contexto(ruta_repo: str):
    if not os.path.exists(ruta_repo):
        raise ValueError(f"El directorio {ruta_repo} no existe")
    """ Lista negra para negra de archivos que deben ser ignorados """
    archivos_ignorados = [ #este es un caso en el que conozco el repositoria. Pero el directorio que trataremos de analizar no tendrá tantos archivos repetidos. 
        ".git", ".venv", "__pycache__", "venv", ".env", ".gitignore",
        "README.md",
        "RAG1.PY",
        "Rag - copia.py",    # Corregido: R mayúscula
        "app - copia.py",
        "app1.py",
        "ML.py",
        "Formación_Estructural.pdf",
        "dataset_info.txt",
        "chroma_db",         # Para carpetas, asegúrate que no tenga '/' al final
        "CE_4.pdf"
    ]
    archivos_ignorados = list(set(archivos_ignorados))
    
    logger.info(f"Generando árbol de directorios para el proyecto {ruta_repo}")

    arbol_texto = DisplayTree(
        dirPath=ruta_repo,
        stringRep=True,        # FUNDAMENTAL: Queremos el texto de vuelta, no un print()
        showHidden=False,      # Evita que se cuele .git, .env, .github, etc.
        ignoreList=archivos_ignorados, # Aplicamos nuestro filtro
        header=False           # No necesitamos encabezados estéticos para el LLM
    )
    if arbol_texto:
        logger.info(f"Árbol de directorios generado correctamente para el proyecto {ruta_repo}")
    else:
        logger.error(f"No se pudo generar el árbol de directorios para el proyecto {ruta_repo}")
    return arbol_texto


# --- Ejemplo de uso ---
if __name__ == "__main__":
    ruta_al_repo = r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\Arquitectura_Rag_con_LLM" 
    
    print("Generando árbol de directorios...")
    arbol = generar_arbol_contexto(ruta_al_repo)
    
    print("\n--- Resultado listo para inyectar en el Prompt ---")
    print(arbol)