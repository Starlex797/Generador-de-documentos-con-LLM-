# ai_engine.py — Comunicación con el LLM y construcción de prompts

import os
from loguru import logger



# ─────────────────────────────────────────────
# Secciones del informe: (título, instrucción al LLM)
# Puedes añadir, quitar o reordenar secciones aquí
# ─────────────────────────────────────────────
SECCIONES = {
    "## 1. Abstract ": (
        "Haz un resumen de lo que trata el archivo, su funcionalidad y su propósito."
        "Este abstract debe debe tener al menos 200 palabras"
    ),
    "## 2. Diagrama Lógico": (
        "Explica el proceso que sigue el archivo. "
        "Utiliza formato Mermaid para crear un diagrama de flujo profesional."
    ),
    "## 3. Explicación el proceso": (
        "Explica en detalle cada uno de los pasos del procedimiento que se sigue en el archivo. Desde el inicio hasta el final. Debe tener al menos 100 palabras en cada paso "
        "Dividelo en pasos y añade un ejemplo de código en cada uno de los pasos."
    ),
    "## 4. Librerias utilizadas": (
        "Enumera en una lista las librerias utilizadas"
    ),
    "## 5. Puntos Críticos y Vulnerabilidades": (
        "Identifica 3 posibles fallos (seguridad, manejo de excepciones o límites de tokens) "
        "y sugiere cómo solucionarlos siguiendo buenas prácticas de Clean Code."
    ),
}

def preparar_prompt_map(nombre_archivo: str, codigo: str) -> list[dict]:
    system_content = """ROL: Ingeniero de IA y tutor de unos becarios
OBJETIVO: Realizar un resumen técnico y conciso de un archivo específico.
REGLAS:
- Describe la responsabilidad principal del archivo.
- ¿De qué trata el archivo de la primera llamada?
- Sigue  los pasos que se indican en el apartado de Secciones.
- Utiliza un tono formal.
- Usa un formato Markdown limpio."""

    user_content = f"ARCHIVO: {nombre_archivo}\n\nCONTENIDO:\n{codigo}."

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]

def preparar_prompt_final(arbol: str, codigo: str, diccionario_secciones: dict) -> list[dict]: # str y dict es el tipo de dato que se espera. Lo del final es lo que nos va a devolver la máquina. 
    # 1. Convertimos el diccionario en un bloque de texto estructurado
    instrucciones_secciones = ""
    for titulo, instruccion in diccionario_secciones.items(): # items() es un método que devuelve una lista de tuplas (clave, valor)
        instrucciones_secciones += f"{titulo}\n{instruccion}\n\n" # Concatenamos el título y la instrucción

    # 2. ROL SYSTEM (Las reglas de comportamiento)
    system_content = f"""ROL: Eres un Arquitecto de Soluciones Senior y experto en IA. Además eres tutor de unos becarios que tienes que enseñarlos.
OBJETIVO: Tu misión es generar una documentación técnica de nivel profesional para un repositorio de código.
TONO: Técnico, preciso y basado únicamente en los hechos del código proporcionado. Evita adjetivos subjetivos.

{instrucciones_secciones} 

REGLAS ADICIONALES:
- Usa un tono profesional y técnico.
- Si una sección no aplica a los archivos proporcionados, indícalo brevemente.
- Genera esquemas o diagramas si ayudan a la comprensión."""

    # 3. ROL USER (Los datos del proyecto)
    user_content = f"""Aquí tienes el contexto del proyecto para analizar:

### ESTRUCTURA DEL DIRECTORIO ###
{arbol}

### CÓDIGO FUENTE COMPLETO ###
{codigo}

Por favor, genera el informe siguiendo las secciones indicadas en el rol de sistema."""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]



