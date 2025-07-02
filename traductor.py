import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString
import os
import time
import argparse
import uuid
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

# --- Cargar API Key y configurar cliente (sin cambios) ---
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("No se encontró la OPENAI_API_KEY.")
client = AsyncOpenAI(api_key=api_key)

# --- Prompts y funciones de traducción (sin cambios) ---
PROMPT_DEL_SISTEMA = """
Eres un asistente de traducción literal y programático. Tu única función es traducir el texto que el usuario te proporcionará.
Sigue estas reglas ESTRICTAMENTE:
1.  Traduce del inglés al español.
2.  Mantén la traducción lo más literal y fiel posible al original.
3.  NO interpretes el texto, NO opines y NO añadas aclaraciones, notas o texto introductorio.
4.  Si una palabra o frase tiene múltiples traducciones comunes y válidas, puedes incluirlas separadas por una barra inclinada (`/`).
5.  Tu respuesta debe ser ÚNICAMENTE el texto traducido. NO incluyas frases como "Aquí está la traducción:", ni saludos, ni nada fuera de la traducción directa.
"""

async def traducir_texto_con_api(texto, indice, max_reintentos=3):
    if not texto.strip(): return texto
    for intento in range(max_reintentos):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": PROMPT_DEL_SISTEMA}, {"role": "user", "content": texto}],
                temperature=0.1, timeout=120
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  !! Error en API (fragmento {indice}, intento {intento + 1}): {e}")
            if intento == max_reintentos - 1: break
            await asyncio.sleep(5)
    return f"--- TRADUCCION_FALLIDA: {texto} ---"

async def traducir_contenido_html_asincrono(contenido_html):
    soup = BeautifulSoup(contenido_html, 'html.parser')
    
    nodos_a_procesar = []
    for tag in soup.find_all(string=True):
        # La condición de filtro sigue siendo la misma
        if tag.parent.name in ['script', 'style', '[document]', 'head', 'title'] or not tag.string.strip():
            continue

        original_string = tag.string
        
        # --- NUEVA LÓGICA PARA MANEJAR ESPACIOS ---
        # 1. Detectar y separar los espacios del texto principal
        texto_nucleo = original_string.strip()
        espacio_inicial = original_string[:original_string.find(texto_nucleo[0])]
        espacio_final = original_string[original_string.rfind(texto_nucleo[-1])+1:]
        
        # Añadimos la información a una lista de diccionarios para mayor claridad
        nodos_a_procesar.append({
            "nodo": tag,
            "texto_a_traducir": texto_nucleo,
            "espacio_inicial": espacio_inicial,
            "espacio_final": espacio_final
        })
        
    if not nodos_a_procesar:
        print("  -> No se encontró texto traducible.", end="")
        return str(soup).encode('utf-8')
    
    total_fragmentos = len(nodos_a_procesar)
    TAMANO_LOTE = 50
    traducciones_totales = []
    total_lotes = (total_fragmentos + TAMANO_LOTE - 1) // TAMANO_LOTE

    print(f"  -> Traduciendo {total_fragmentos} fragmentos en {total_lotes} lotes...", end="")
    
    # Extraemos solo el texto a traducir para la API
    textos_para_api = [info["texto_a_traducir"] for info in nodos_a_procesar]

    for i in range(0, total_fragmentos, TAMANO_LOTE):
        lote_textos = textos_para_api[i:i + TAMANO_LOTE]
        tasks = [traducir_texto_con_api(texto, i + j) for j, texto in enumerate(lote_textos)]
        resultados_lote = await asyncio.gather(*tasks, return_exceptions=True)
        traducciones_totales.extend(resultados_lote)
        if total_lotes > 1: await asyncio.sleep(1)

    # --- LÓGICA DE REEMPLAZO MEJORADA ---
    for i, info_nodo in enumerate(nodos_a_procesar):
        texto_traducido = traducciones_totales[i]
        
        if not isinstance(texto_traducido, Exception):
            # 3. Reconstruir el string con el texto traducido y los espacios originales
            string_reconstruido = f"{info_nodo['espacio_inicial']}{texto_traducido}{info_nodo['espacio_final']}"
            info_nodo["nodo"].replace_with(NavigableString(string_reconstruido))
            
    return str(soup).encode('utf-8')

# --- [CAMBIO RADICAL] Lógica principal de ePub con persistencia ---
def traducir_epub_automatico(nombre_original, nombre_traducido):
    print(f"Libro original: {nombre_original}")
    print(f"Archivo de salida: {nombre_traducido}")

    libro_original = epub.read_epub(nombre_original)
    libro_traducido = None
    items_traducidos = {}

    # 1. Comprobar si existe un progreso guardado
    if os.path.exists(nombre_traducido):
        print("\n✅ Archivo de salida encontrado. Intentando reanudar la traducción...")
        libro_traducido = epub.read_epub(nombre_traducido)
        # Crear un diccionario de los items ya presentes en el archivo de salida
        for item in libro_traducido.get_items():
            items_traducidos[item.get_name()] = item
    else:
        print("\n🚀 No se encontró progreso. Iniciando una nueva traducción...")
        libro_traducido = epub.EpubBook()
        # Configurar metadatos para el nuevo libro
        libro_traducido.set_identifier(f"urn:uuid:{uuid.uuid4()}")
        try:
            titulo_original = libro_original.get_metadata('DC', 'title')[0][0]
        except IndexError:
            titulo_original = os.path.basename(nombre_original)
        libro_traducido.set_title(f"[ES] {titulo_original}")
        libro_traducido.set_language('es')
        try:
            for autor in libro_original.get_metadata('DC', 'creator'):
                libro_traducido.add_author(autor[0])
        except IndexError:
            pass

    # 2. Iterar sobre los items del libro original y decidir si traducir o copiar
    items_originales = list(libro_original.get_items())
    total_items = len(items_originales)
    
    print("\n--- INICIO/REANUDACIÓN DEL PROCESAMIENTO ---")

    for i, item_original in enumerate(items_originales):
        nombre_item = item_original.get_name()
        print(f"\nProcesando item {i + 1}/{total_items}: {nombre_item}", end="")

        item_existente = items_traducidos.get(nombre_item)
        
        # Condición para volver a traducir: si el item tiene una marca de error
        debe_retraducir = item_existente and b"TRADUCCION_FALLIDA" in item_existente.get_content()

        if item_existente and not debe_retraducir:
            print(" (Capítulo ya traducido) -> Omitiendo.")
            continue # Saltar al siguiente item

        if debe_retraducir:
            print(" (Reintentando capítulo con error)")
        
        # 3. Lógica de traducción o copia
        if item_original.get_type() == ebooklib.ITEM_DOCUMENT:
            print(" (Traduciendo capítulo HTML)...")
            contenido_original = item_original.get_content()
            
            if contenido_original and contenido_original.strip():
                contenido_traducido = asyncio.run(traducir_contenido_html_asincrono(contenido_original))
                item_original.set_content(contenido_traducido)
                print("  -> Contenido del capítulo procesado.")
            else:
                print("  -> Capítulo vacío. Se copia directamente.")
        else:
            print(f" (Copiando item tipo: {item_original.get_type()})")

        # 4. Añadir o actualizar el item en el libro traducido
        # Si el ítem ya existía (porque tenía un error), ya está en `libro_traducido`.
        # Si no, lo añadimos. `ebooklib` maneja la adición.
        if not item_existente:
             libro_traducido.add_item(item_original)
        
        # 5. Guardar el progreso en el disco
        print("  -> Guardando progreso en el disco...")
        # Se reconstruyen spine y toc en cada guardado para mantener la integridad del ePub
        libro_traducido.spine = libro_original.spine
        libro_traducido.toc = libro_original.toc
        epub.write_epub(nombre_traducido, libro_traducido, {})
        print("  -> Progreso guardado.")

    # Ensamblado final (aunque ya se guarda en cada paso, asegura la última versión)
    libro_traducido.spine = libro_original.spine
    libro_traducido.toc = libro_original.toc
    libro_traducido.add_item(epub.EpubNcx())
    libro_traducido.add_item(epub.EpubNav())

    print("\n=======================================================")
    print(f"Escribiendo versión final en: {nombre_traducido}")
    epub.write_epub(nombre_traducido, libro_traducido, {})
    print("¡TRADUCCIÓN COMPLETADA!")
    print("=======================================================")

# Función `main` sin cambios
def main():
    parser = argparse.ArgumentParser(
        description="Traduce un archivo ePub de forma robusta, guardando el progreso.",
        epilog="Ejemplo: python tu_script.py 'libro.epub' 'libro_traducido.epub'"
    )
    parser.add_argument("input_file", help="Ruta al ePub original.")
    parser.add_argument("output_file", help="Ruta donde se guardará el ePub traducido.")
    args = parser.parse_args()
    traducir_epub_automatico(args.input_file, args.output_file)

if __name__ == "__main__":
    main()