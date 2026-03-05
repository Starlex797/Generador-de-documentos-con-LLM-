# ai_engine.py — Comunicación con el LLM y construcción de prompts
import json
import os
from pathlib import Path
from groq import Groq
from loguru import logger
from dotenv import load_dotenv

# Carga el .env desde la misma carpeta que este archivo (core/)
load_dotenv(Path(__file__).parent / ".env")

# ─────────────────────────────────────────────
# Secciones del informe: (título, instrucción al LLM)
# Puedes añadir, quitar o reordenar secciones aquí
# ─────────────────────────────────────────────
SECCIONES = {
    "## 1. Descripción general": (
        "Analiza el código y escribe una descripción general clara en 3-5 frases. "
        "Explica qué hace el archivo, cuál es su propósito principal y en qué contexto se usaría."
    ),
    "## 2. Dependencias e imports": (
        "Lista todos los imports del código. Para cada uno explica brevemente para qué se usa "
        "en este archivo concreto. Usa una tabla Markdown con columnas: Módulo | Para qué sirve aquí."
    ),
    "## 3. Funciones documentadas": (
        "Documenta cada función del código. Para cada una incluye: "
        "nombre, parámetros (nombre y tipo si se puede inferir), qué hace, qué retorna, "
        "y un ejemplo de llamada. Usa subsecciones ### para cada función."
    ),
    "## 4. Clases documentadas": (
        "Documenta cada clase del código. Para cada una incluye: "
        "nombre, responsabilidad, lista de métodos con una frase explicando cada uno. "
        "Si no hay clases, escribe 'No se encontraron clases en este archivo.'"
    ),
    "## 5. Flujo de ejecución": (
        "Describe paso a paso el flujo de ejecución del archivo. "
        "Explica el orden en que se ejecuta el código, qué llama a qué, y cuál es el resultado final. "
        "Si es posible, usa una lista numerada."
    ),
    "## 6. Posibles mejoras": (
        "Sugiere exactamente 3 mejoras concretas y aplicables al código analizado. "
        "Para cada mejora explica el problema actual y cómo solucionarlo."
    ),
}


def _llamar_llm(instruccion: str, contexto_json: str) -> str:
    """Realiza una única llamada al LLM con una instrucción y el contexto del código."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    mensajes = [
        {
            "role": "system",
            "content": (
                "Eres un experto en documentación de software Python. "
                "Respondes siempre en Markdown bien formateado y en español. "
                f"Instrucción para esta sección: {instruccion}"
            ),
        },
        {
            "role": "user",
            "content": f"Aquí tienes la estructura del código analizado en JSON:\n\n{contexto_json}",
        },
    ]

    respuesta = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=mensajes,
        temperature=0.2,  # Bajo = más técnico y determinista
    )
    return respuesta.choices[0].message.content


def generar_informe(estructura: dict, nombre_archivo: str = "archivo.py") -> str:
    """
    Genera un informe Markdown completo sección a sección.
    Cada sección hace una llamada independiente al LLM.

    Args:
        estructura: dict devuelto por parser.analizar_codigo()
        nombre_archivo: nombre del archivo original para el título del informe

    Returns:
        str: informe completo en Markdown
    """
    logger.info(f"Iniciando generación de informe para '{nombre_archivo}'")

    contexto_json = json.dumps(estructura, indent=2, ensure_ascii=False)

    # Cabecera del informe
    partes = [
        f"# Informe de código: `{nombre_archivo}`",
        f"> Generado automáticamente por py-analyzer\n",
    ]

    # Llamada al LLM sección por sección
    for titulo, instruccion in SECCIONES.items():
        logger.info(f"Generando sección: {titulo}")
        try:
            contenido = _llamar_llm(instruccion, contexto_json)
            partes.append(f"{titulo}\n\n{contenido}")
            logger.success(f"Sección '{titulo}' completada")
        except Exception as e:
            logger.error(f"Error al generar '{titulo}': {e}")
            partes.append(f"{titulo}\n\n> ⚠️ Error al generar esta sección: {e}")

    informe = "\n\n---\n\n".join(partes)
    logger.success(f"Informe completo generado ({len(informe)} caracteres)")
    return informe
