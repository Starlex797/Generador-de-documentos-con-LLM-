# ai_engine.py — Comunicación con el LLM y construcción de prompts

import os
from loguru import logger
from core.reader import contar_tokens




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

def preparar_prompt_archivo_unico(codigo: str, diccionario_secciones: dict) -> list[dict]: # str y dict es el tipo de dato que se espera. Lo del final es lo que nos va a devolver la máquina. 
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


### CÓDIGO FUENTE COMPLETO ###
{codigo}

Por favor, genera el informe siguiendo las secciones indicadas en el rol de sistema."""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]

def preparar_prompt_repo(arbol: str, codigo: str, SECCIONES: dict) -> list[dict]: # str y dict es el tipo de dato que se espera. Lo del final es lo que nos va a devolver la máquina. 
    # 1. Convertimos el diccionario en un bloque de texto estructurado
    instrucciones_secciones = ""
    for titulo, instruccion in SECCIONES.items(): # items() es un método que devuelve una lista de tuplas (clave, valor)
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


def preparar_prompt_chunking(nombre_archivo: str, lista_chunks: list, informe_previo: str = "", limite_tokens: int = 6000) -> tuple[list[dict], int]: # Limite_tokens: es el limite de mi ventana de contexto 
    
    reserva_output= 2000
    presupuesto_maximo = limite_tokens - reserva_output
    messages=[]

    if not informe_previo:
        system_content = f""" Eres ingeniero de IA y tutor de unos becarios
OBJETIVO:Tu objetivo es generar un INFORME TÉCNICO profesional en Markdown para el archivo {nombre_archivo}.
REGLAS:
1. Usa un lenguaje técnico  pero directo 
2. Formato: Markdown limpio (encabezados, listas, bloques de código, etc)
3. Contenido: explica la Responsabilidad de cada componente, no solo lo que hace. 
4. Sé ultra conciso y ve al grano: evita instrucciones como  " En este código podemos ver ..." o "Ahora vamos a ver ..." 

ESTRUCTURA DEL INFORME:
# Informe Técnico: {nombre_archivo}
## Resumen General
(Breve explicación del propósito del archivo)
## Arquitectura y Estructura
(Clases, Funciones globales y su lógica)
## Detalle de Componentes
(Análisis técnico de los métodos)
"""
    else: 
        system_content =f"""ROL: Arquitecto de IA.
TE PASO EL ESTADO ACTUAL DEL REPORTE:
{informe_previo}

INSTRUCCIONES:
1. Actualiza o expande las secciones correspondientes (Resumen, Arquitectura, Componentes).
2. Si el nuevo código revela una lógica compleja, añádela de forma sucinta.
3. MANTÉN el formato Markdown original.
4. NO REPITAS información que ya esté en el informe.
5. Devuelve SIEMPRE el informe completo y actualizado.

"""
    messages.append({"role": "system", "content": system_content})
    
    tokens_instrucciones = contar_tokens(system_content)
    chunks_incluidos = 0

    # 2. El bucle "x6 veces" (o X veces) de la pizarra
    for chunk in lista_chunks:
        tokens_chunk = contar_tokens(chunk)
        if tokens_chunk > presupuesto_maximo:
            logger.warning(f"⚠️ Chunk {chunks_incluidos + 1} es muy grande ({tokens_chunk} tokens). Presupuesto: {presupuesto_maximo}")
        # Si el chunk cabe en el presupuesto, lo añadimos como un mensaje de usuario nuevo
        if (tokens_instrucciones + tokens_chunk) < presupuesto_maximo:
            messages.append({"role": "user", "content": f"CHUNK {chunks_incluidos + 1}:\n{chunk}"})
            tokens_instrucciones += tokens_chunk
            chunks_incluidos += 1
        else:
            logger.info(f"Ventana de contexto llena. Se han metido {chunks_incluidos} fragmentos.")
            logger.info(
                f"📊 [TELEMETRÍA] Archivo: {nombre_archivo} | "
                f"Chunks: {chunks_incluidos}/{len(lista_chunks)} | "
                f"Tokens Input: {tokens_instrucciones} | "
                f"Espacio libre para respuesta: {limite_tokens - tokens_instrucciones}"
            )
            # Si no cabe más, paramos de añadir a este paquete
            break
   
    return messages, chunks_incluidos
   
def preparar_prompt_repo_iterativo(arbol: str, lote_resumenes: str, informe_previo: str = "") -> list[dict]:
    """Genera o actualiza el informe global del repositorio por lotes."""
    
    if not informe_previo:
        system_content = f"""ROL: Arquitecto de Software Senior.
OBJETIVO: Estás creando la Documentación Global (README Técnico) de un repositorio paso a paso.
ESTRUCTURA DEL PROYECTO:
{arbol}

INSTRUCCIONES:
1. Analiza los resúmenes de los archivos proporcionados.
2. Inicia un documento Markdown profesional que explique la ARQUITECTURA GLOBAL.
3. Agrupa por módulos lógicos (ej. Frontend, Backend, Core, Utilidades), no hagas una simple lista de archivos.
4. Mantén un tono técnico y de alto nivel."""

    else:
        system_content = f"""ROL: Arquitecto de Software Senior.
ESTRUCTURA DEL PROYECTO:
{arbol}

DOCUMENTACIÓN GLOBAL ACTUAL (En progreso):
{informe_previo}

INSTRUCCIONES:
1. Lee los nuevos resúmenes de archivos que se han analizado.
2. INTEGRA esta nueva información en la Documentación Global Actual.
3. Expande las secciones existentes o crea nuevas si descubres nuevos módulos (ej. si aparece la base de datos).
4. Devuelve SIEMPRE el documento global completo y actualizado en Markdown. No repitas, sintetiza."""

    user_content = f"NUEVOS ARCHIVOS ANALIZADOS:\n{lote_resumenes}"

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]
"""
# ai_engine.py

def preparar_paquete_dinamico(nombre_archivo: str, lista_chunks: list, informe_previo: str = "", limite_tokens: int = 120000) -> tuple[list[dict], int]:
  
    Construye la lista de mensajes (el paquete) metiendo tantos chunks como quepan.
    Devuelve (lista_de_mensajes, num_chunks_procesados)
   "
    mensajes = []
    
    # 1. El System Prompt (La primera llave de la pizarra)
    instruccion_sistema = "Eres un Arquitecto Senior. Actualiza el informe técnico con el código proporcionado."
    if informe_previo:
        instruccion_sistema += f"\n\nESTADO ACTUAL DEL INFORME:\n{informe_previo}"
    
    mensajes.append({"role": "system", "content": instruccion_sistema})
    
    tokens_consumidos = len(instruccion_sistema) // 4 # Estimación simple o usa tiktoken
    chunks_incluidos = 0

    # 2. El bucle "x6 veces" (o X veces) de la pizarra
    for chunk in lista_chunks:
        tokens_este_chunk = len(chunk) // 4
        
        # Si el chunk cabe en el presupuesto, lo añadimos como un mensaje de usuario nuevo
        if tokens_consumidos + tokens_este_chunk < limite_tokens:
            mensajes.append({"role": "user", "content": f"CHUNK {chunks_incluidos + 1}:\n{chunk}"})
            tokens_consumidos += tokens_este_chunk
            chunks_incluidos += 1
        else:
            # Si no cabe más, paramos de añadir a este paquete
            break
            
    return mensajes, chunks_incluidos


    

"""