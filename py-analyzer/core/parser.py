# parser.py — Preprocesamiento y chunking AST del código fuente
import ast
from loguru import logger
import json

"""No estamos creando el Chunking todavía, estamos separando el código en funciones/ clases y poniendolo en un diccionario"""

@logger.catch
def analizar_codigo(codigo: str)-> dict: # Me lo convierte en un diccionario
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

