import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import time
import argparse
import uuid  # <--- CAMBIO: Se importa la librería correcta para IDs únicos
import google.generativeai as genai
from dotenv import load_dotenv

# --- Cargar la API Key de forma segura desde el archivo .env ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No se encontró la API Key. Asegúrate de crear un archivo .env con 'GEMINI_API_KEY=SU_CLAVE'")

genai.configure(api_key=api_key)

# --- Configuración del Modelo de IA (Gemini) ---
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- Plantilla de Instrucciones para la IA (sin cambios) ---
PROMPT_DE_TRADUCCION = """
Eres un asistente de traducción literal y programático. Tu única función es traducir el texto que te proporciono.
Sigue estas reglas ESTRICTAMENTE:

1.  Traduce del inglés al español.
2.  NO interpretes nada, NO opines y NO añadas aclaraciones.
3.  Cuando una palabra o frase pueda tener varias traducciones válidas, ponlas separadas por una barra inclinada (`/`). Por ejemplo: `/traducción1/traducción2/traducción3/`.
4.  Tu respuesta debe ser ÚNICAMENTE el texto traducido. NO incluyas frases como "Aquí está la traducción:", ni saludos, ni ningún texto adicional. Solo la traducción directa del texto proporcionado.

Aquí está el texto a traducir:
---
{TEXTO_A_TRADUCIR}
"""

def extraer_texto_limpio(contenido_html):
    """Extrae solo el texto visible del HTML de un capítulo."""
    soup = BeautifulSoup(contenido_html, 'html.parser')
    return soup.get_text(separator='\n', strip=True)

def texto_a_html(texto_traducido):
    """Convierte el texto plano traducido de vuelta a un formato HTML simple."""
    parrafos = texto_traducido.strip().split('\n')
    contenido_html = "<html><head><meta charset='UTF-8'/></head><body>"
    for p in parrafos:
        if p.strip():
            contenido_html += f"<p>{p.strip()}</p>"
    contenido_html += "</body></html>"
    return contenido_html.encode('utf-8')

def traducir_texto_con_api(texto):
    """Envía el texto a la API de Gemini y devuelve la traducción."""
    if not texto.strip():
        return ""

    prompt_completo = PROMPT_DE_TRADUCCION.format(TEXTO_A_TRADUCIR=texto)
    
    try:
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        response = model.generate_content(prompt_completo, safety_settings=safety_settings)
        return response.text.strip()
    except Exception as e:
        print(f"  !! Error en la API: {e}")
        print("  !! Se devolverá el texto original para este capítulo.")
        return f"--- ERROR DE TRADUCCIÓN ---\n{texto}"

def traducir_epub_automatico(nombre_original, nombre_traducido):
    """Proceso AUTOMÁTICO para traducir un ePub, recibiendo nombres por parámetros."""
    if not os.path.exists(nombre_original):
        print(f"Error: El archivo de entrada '{nombre_original}' no se encontró.")
        return

    print(f"Leyendo ePub original: {nombre_original}")
    libro_original = epub.read_epub(nombre_original)
    libro_traducido = epub.EpubBook()

    # Copiar metadatos
    # CAMBIO: Se utiliza uuid.uuid4() para generar un identificador único y válido.
    libro_traducido.set_identifier(f"urn:uuid:{uuid.uuid4()}")
    
    try:
        original_title = libro_original.get_metadata('DC', 'title')[0][0]
    except IndexError:
        original_title = os.path.basename(nombre_original)
    libro_traducido.set_title(f"[ES] {original_title}")
    libro_traducido.set_language('es')
    try:
        for autor in libro_original.get_metadata('DC', 'creator'):
            libro_traducido.add_author(autor[0])
    except IndexError:
        pass

    # Bucle principal de traducción
    items_procesados = []

    print("--- INICIO DE LA TRADUCCiÓN AUTOMÁTICA ---")
    
    items_del_libro = list(libro_original.get_items())
    total_items = len(items_del_libro)

    for i, item in enumerate(items_del_libro):
        print(f"Procesando item {i + 1}/{total_items}: {item.get_name()}", end="")
        
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            print(" (Capítulo)")
            contenido_original = item.get_content()
            texto_para_traducir = extraer_texto_limpio(contenido_original)
            
            if texto_para_traducir.strip():
                print("  -> Enviando a la API para traducción...")
                texto_traducido = traducir_texto_con_api(texto_para_traducir)
                print("  -> Traducción recibida.")
                nuevo_contenido_html = texto_a_html(texto_traducido)
                item.content = nuevo_contenido_html # Asignar contenido modificado
                time.sleep(1.5)
            else:
                print("  -> Capítulo vacío o de formato. Se copia directamente.")
        else:
            print(f" ({item.get_type()}) - Copiando directamente.")

        items_procesados.append(item)
    
    # Ensamblar el nuevo libro
    for item in items_procesados:
        libro_traducido.add_item(item)

    libro_traducido.spine = libro_original.spine
    libro_traducido.toc = libro_original.toc
    libro_traducido.add_item(epub.EpubNcx())
    libro_traducido.add_item(epub.EpubNav())

    # Guardar el archivo final
    epub.write_epub(nombre_traducido, libro_traducido, {})
    print("\n=======================================================")
    print("¡TRADUCCIÓN AUTOMÁTICA COMPLETADA!")
    print(f"Libro guardado como: '{nombre_traducido}'")
    print("=======================================================")

def main():
    """Función principal para parsear argumentos y lanzar la traducción."""
    parser = argparse.ArgumentParser(
        description="Traduce un archivo ePub de forma automática usando la API de Gemini.",
        epilog="Ejemplo: python traductor_v3.py 'libro.epub' 'libro_traducido.epub'"
    )
    parser.add_argument("input_file", help="Ruta al archivo ePub original que se va a traducir.")
    parser.add_argument("output_file", help="Ruta donde se guardará el nuevo archivo ePub traducido.")
    
    args = parser.parse_args()
    
    traducir_epub_automatico(args.input_file, args.output_file)

if __name__ == "__main__":
    main()
