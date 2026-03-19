# parser.py — Preprocesamiento y chunking AST del código fuente
import ast
from loguru import logger
import json
from llama_index.core.node_parser import TokenTextSplitter, CodeNodeParser, SemanticSplitterNodeParser
from llama_index.core import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

"""No estamos creando el Chunking todavía, estamos separando el código en funciones/ clases y poniendolo en un diccionario"""

@logger.catch
def analizar_codigo_ast(codigo: str)-> dict: # Me lo convierte en un diccionario
    logger.info("Iniciando análisis del código")
    estructura = {
        "imports": [],
        "funciones": [],
        "clases": [],
        "variables": [],
        "comentarios": [],
        "codigo_completo": codigo
    }
    try:
        arbol = ast.parse(codigo) # Convierte el código fuente en un Árbol Abstracto de Sintaxis (AST)
        """Este árbol es una estructura de datos jerárquicos que representa la estructura gramatical del código sin ejecutarlo"""
        logger.info("Código analizado correctamente")
    except Exception as e:
        logger.exception(f"Fallo crítico al analizar el código: {e}")
        return None
    for nodo in arbol.body: # Aqui se ignora todo lo que sea ruid, como variables sueltas o imports
        if isinstance(nodo,ast.FunctionDef): #isinstance nos permite verificar si un objeto es una instancia de una clase
            estructura["funciones"].append({
                "nombre": nodo.name,
                "argumentos": [arg.arg for arg in nodo.args.args],
                "docstring": ast.get_docstring(nodo),
                "codigo": ast.unparse(nodo)
            })
        elif isinstance(nodo, ast.ClassDef):
            metodos = []
            # Entramos a mirar qué hay DENTRO de la clase
            for sub_nodo in nodo.body:
                if isinstance(sub_nodo, ast.FunctionDef):
                    metodos.append(sub_nodo.name)
            
            estructura["clases"].append({
                "nombre": nodo.name,
                "metodos": metodos, # ¡Ahora sabemos qué hace la clase por dentro!
                "codigo": ast.unparse(nodo) # El código completo para la IA
            })
        elif isinstance(nodo,ast.Import): # ast.Import es un nodo que representa un import
            estructura["imports"].append({
                "modulo": nodo.name,
                "alias": nodo.names[0].asname
            })
        elif isinstance(nodo,ast.Expr): # ast.Expr es un nodo que representa una expresión
            estructura["comentarios"].append({
                "comentario": ast.get_docstring(nodo)
            })
        elif isinstance(nodo,ast.Assign): # ast.Assign es un nodo que representa una asignación
            estructura["variables"].append({
                "nombre": nodo.targets[0].id,
                "valor": ast.unparse(nodo.value)
            })
    logger.success("Análisis completado")
    return estructura



def splitting_and_processing_with_langchain(contenido:str, ruta_archivo:str, chunk_size: int, chunk_overlap: int):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, language=Language.PYTHON)
    return splitter

"""
# 'texto_extraido' viene de tu función leer_codigo_fuente

Esto nos permite guardar cada uno de los chunks en un objeto o variable. Después havemos un for loop para enumerar cada uno de los chunks y mostrar su contenido.
docs = splitter.create_documents([texto_extraido])

for i, doc in enumerate(docs):
    print(f"Fragmento {i}: {len(doc.page_content)} caracteres")

MAPPING_LENGUAJES = {
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".java": Language.JAVA
}
# Así, según el sufijo del archivo en reader.py, eliges el Language correcto.
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from pathlib import Path
# Importamos los lenguajes que soporta LangChain

def procesar_y_dividir_codigo(contenido: str, ruta_archivo: str, chunk_size: int = 2000):
 
    Toma el contenido de un archivo, detecta su lenguaje y lo divide en chunks lógicos.
  
    # 1. Mapeo de extensiones a lenguajes de LangChain
    extension = Path(ruta_archivo).suffix.lower()
    mapping = {
        ".py": Language.PYTHON,
        ".js": Language.JS,
        ".java": Language.JAVA,
        ".cpp": Language.CPP,
        ".md": Language.MARKDOWN
    }
    
    # Seleccionamos el lenguaje o usamos texto plano por defecto
    lenguaje_seleccionado = mapping.get(extension, None)
    
    # 2. Configuración del Splitter
    if lenguaje_seleccionado:
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=lenguaje_seleccionado,
            chunk_size=chunk_size,
            chunk_overlap=int(chunk_size * 0.1) # 10% de solapamiento
        )
    else:
        # Si no reconoce el lenguaje, usa un splitter de texto genérico
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=200
        )
    
    # 3. Ejecución del corte
    chunks = splitter.split_text(contenido)
    return chunks
"""


# 1. Definimos el mapeo global de extensiones soportadas
MAPPING_LENGUAJES = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".html": "html",
    ".md": "markdown",
    ".json": "json",
    ".vb": "visualbasic",
    ".vba": "visualbasic",
    ".vbs": "visualbasic",
    ".bas": "visualbasic"
}
@logger.catch
def procesar_archivo_multilenguaje(contenido: str, ruta_archivo: str, chunk_size: int, chunk_overlap: int):
    """
    Detecta el lenguaje automáticamente y divide el código en nodos.
    """
    # Extraer extensión del archivo
    extension = os.path.splitext(ruta_archivo)[1].lower()
    
    # Buscar el lenguaje en el mapeo
    lenguaje_ia = MAPPING_LENGUAJES.get(extension)

    if not lenguaje_ia:
        # Si la extensión es válida en reader.py pero no tiene parser específico
        logger.warning(f"⚠️ Lenguaje no soportado para {extension}. Usando 'python' como fallback.")
        lenguaje_ia = "python"

    try:
        # Crear el Documento con metadatos para el informe final
        doc = Document(
            text=contenido,
            metadata={
                "file_name": os.path.basename(ruta_archivo),
                "language": lenguaje_ia,
                "path": ruta_archivo,
                "chunk_size": chunk_size,
            }
        )

        # Configurar el parser con el lenguaje detectado
        parser = CodeNodeParser(
            language=lenguaje_ia,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        nodos = parser.get_nodes_from_documents([doc])
        logger.info(f"✅ {os.path.basename(ruta_archivo)} ({lenguaje_ia}) dividido en {len(nodos)} nodos.")
        
        return nodos

    except Exception as e:
        logger.error(f"❌ Error procesando {ruta_archivo}: {e}")
        return []