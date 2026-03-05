import sys 
import json
from loguru import logger
from core.reader import leer_codigo_fuente
from core.parser import analizar_codigo

def main():
    with logger.catch():
        # 1. Leemos el archivo Rag.py 
        codigo = leer_codigo_fuente(r"C:\Users\EM2026008876\OneDrive - Nfoque nworld6.onmicrosoft.com\Escritorio\Arquitectura_Rag_con_LLM\Rag.py")

        # 2.Proceso de "chunking"
        mi_analisis = analizar_codigo(codigo)

        # 3. Imprimimos el resultado
        print(json.dumps(mi_analisis, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()