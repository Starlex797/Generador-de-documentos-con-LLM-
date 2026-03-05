import json
from parser import analizar_codigo

def construir_prompt(estructura: dict) -> list[dict]:
    estructura_texto = json.dumps(estructura, indent=2, ensure_ascii=False)
    
    system_prompt = """Eres un experto en documentación de software.
    Recibirás la estructura analizada de un archivo Python en formato JSON.
    Tu tarea es generar documentación clara en Markdown donde se explique el proceso que se ha seguido incluyendo
    ejemplos de uso y esquemas para poder entender el código de manera mas sencilla."""
    
    user_prompt = f"""Aquí tienes la estructura del código analizado:{estructura_texto}
Genera una documentación completa en Markdown que incluya:
- Descripción general del archivo
- Documentación de cada función (parámetros, qué hace, qué retorna)
- Documentación 
"""
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
