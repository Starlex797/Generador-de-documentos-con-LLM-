# ai_engine.py — Comunicación con el LLM y construcción de prompts

import os
from loguru import logger



# ─────────────────────────────────────────────
# Secciones del informe: (título, instrucción al LLM)
# Puedes añadir, quitar o reordenar secciones aquí
# ─────────────────────────────────────────────
SECCIONES = {
    "## 1. Abstract": (
        "Analiza el código y escribe una descripción general clara en 3-5 frases. "
        "Explica de qué trata el repositorio, cuál es su propósito principal y en qué contexto se usaría."
    ),
    "## 2. Herramientas utilizadas": (
        "Lista las herramientas más importantes que han sido utilizadas en el repositorio. "
        
    ),
    "## 3. Funciones documentadas": (
        "Documenta cada función del código. Para cada una incluye: "
        "nombre, parámetros (nombre y tipo si se puede inferir), qué hace, qué retorna, "
        "y explica el proceso que sigue la función y para qué sirve."
    ),
    "## 4. Ejemplos de uso": (
        "Proporciona ejemplos claros y concisos de cómo utilizar el código. "
        "Incluye ejemplos de uso de cada función y de cómo utilizar el repositorio en general."
    ),
    "## 5. Posibles mejoras": (
        "Sugiere exactamente 3 mejoras concretas y aplicables al código analizado. "
        "Para cada mejora explica el problema actual y cómo solucionarlo."
    ),
}



def preparar_prompt_final(arbol: str, codigo: str, diccionario_secciones: dict) -> list[dict]:
    # 1. Convertimos el diccionario en un bloque de texto estructurado
    instrucciones_secciones = ""
    for titulo, instruccion in diccionario_secciones.items():
        instrucciones_secciones += f"{titulo}\n{instruccion}\n\n"

    # 2. ROL SYSTEM (Las reglas de comportamiento)
    system_content = f"""Genera un único informe global que cubra todo el proyecto, pero entra en detalle en los archivos 
    más importantes (como Rag.py o app.py) dentro de las secciones de funciones y clases.

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



