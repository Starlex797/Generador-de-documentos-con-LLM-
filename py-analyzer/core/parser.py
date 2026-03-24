# parser.py — Preprocesamiento y chunking AST del código fuente
# parser.py
import ast
from loguru import logger
import os 
import json
# Cambiamos CodeNodeParser por CodeSplitter
from llama_index.core.node_parser import TokenTextSplitter, CodeSplitter
from llama_index.core import Document

# Modifica la línea 6 de parser.py


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

    for nodo in arbol.body: # Aqui se ignora todo lo que sea ruido, como variables sueltas o imports. Con este loop estamos recorriendo todo lso nodos del árbol
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
                    metodos.append({
                        "nombre": sub_nodo.name,
                        "codigo": ast.unparse(sub_nodo)
                    })
            
            estructura["clases"].append({
                "nombre": nodo.name,
                "metodos": metodos, # ¡Ahora sabemos qué hace la clase por dentro
                # En lugar de guardar toda la clase, guardamos solo su cabecera
                "codigo_firma": f"class {nodo.name}:\n    pass # (Métodos procesados por separado)"
            })
        elif isinstance(nodo, ast.Import): # Corrección del error 'AttributeError'
            for alias in nodo.names:
                estructura["imports"].append({
                    "modulo": alias.name, # Correcto: accedemos al nombre del alias
                    "alias": alias.asname
                })
        # 4. Procesamiento de Comentarios/Strings sueltos
        elif isinstance(nodo, ast.Expr):
            # Comprobamos si la expresión es una constante de texto (comentarios de triple comilla)
            if isinstance(nodo.value, ast.Constant) and isinstance(nodo.value.value, str):
                estructura["comentarios"].append({
                    "comentario": nodo.value.value
                })
        elif isinstance(nodo,ast.Assign): # ast.Assign es un nodo que representa una asignación
            estructura["variables"].append({
                "nombre": nodo.targets[0].id,
                "valor": ast.unparse(nodo.value)
            })
    logger.success("Análisis completado")
    return estructura



# 1. Definimos el mapeo global de extensiones soportadas
MAPPING_LENGUAJES = {
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
        doc = Document(
            text=contenido,
            metadata={
                "file_name": os.path.basename(ruta_archivo),
                "language": lenguaje_ia,
                "path": ruta_archivo
            }
        )

        # 2. ESTRATEGIA DE CHUNKING SEGÚN EXTENSIÓN
        if extension in [".json", ".md", ".txt"]:
            # Para JSON/MD no necesitamos gramática, solo trozos de texto válidos
            logger.info(f"Usando TokenTextSplitter para {os.path.basename(ruta_archivo)}")
            parser = TokenTextSplitter(
                chunk_size=chunk_size, 
                chunk_overlap=chunk_overlap
            )
        else:
            # Para código real (.py, .js, .java, etc.) usamos CodeSplitter
            logger.info(f"Usando CodeSplitter para {os.path.basename(ruta_archivo)} ({lenguaje_ia})")
            parser = CodeSplitter(
                language=lenguaje_ia,
                chunk_lines=40,
                chunk_lines_overlap=5,
                max_chars=chunk_size
            )

        nodos = parser.get_nodes_from_documents([doc])
        logger.info(f"✅ {os.path.basename(ruta_archivo)} dividido en {len(nodos)} nodos.")
        
        return nodos

    except Exception as e:
        logger.error(f"❌ Error procesando {ruta_archivo}: {e}")
        return []