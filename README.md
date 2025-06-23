# Traductor Automático de ePub con IA (Gemini)

Este proyecto contiene un script de Python para traducir archivos de formato `.epub` de un idioma a otro de forma completamente automática, utilizando la API de Google Gemini. El script está diseñado para ser flexible, robusto y fácil de usar desde la línea de comandos.

## Características

- **Traducción Automática**: Procesa un ePub capítulo por capítulo, enviando el texto a la API de Gemini para su traducción.
- **Interfaz de Línea de Comandos**: Permite especificar los archivos de entrada y salida como argumentos, haciéndolo fácil de integrar en flujos de trabajo.
- **Preservación de Estructura**: Mantiene la estructura básica del ePub (capítulos, orden, metadatos) en el archivo traducido.
- **Prompt de Traducción Personalizable**: Las reglas de traducción se definen en un _prompt_ claro dentro del script, permitiendo ajustar el estilo y las directrices (por ejemplo, traducción literal, manejo de alternativas, etc.).
- **Manejo Seguro de API Keys**: Utiliza un archivo `.env` para gestionar la API key de forma segura, evitando exponerla en el código fuente.

## Requisitos

- Python 3.8 o superior.
- Una API Key de Google AI (Gemini). Puedes obtenerla en [Google AI Studio](https://aistudio.google.com/app/apikey).
- Las librerías de Python listadas en el archivo `requirements.txt`.

## Instalación y Configuración

1.  **Clonar el repositorio (o descargar los archivos):**
    ```bash
    git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
    cd tu-repositorio
    ```

2.  **Instalar las dependencias:**
    Se recomienda crear un entorno virtual primero. Luego, instala las librerías necesarias:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar la API Key:**
    Crea un archivo llamado `.env` en la raíz del proyecto. Este archivo **no** debe ser subido al repositorio. Añade tu API key dentro de él de la siguiente forma:
    ```
    GEMINI_API_KEY=TU_API_KEY_AQUI
    ```

## Modo de Uso

Una vez configurado, puedes ejecutar el script desde tu terminal. La sintaxis es la siguiente:

```bash
python traductor.py <ruta_del_archivo_de_entrada.epub> <ruta_para_el_archivo_de_salida.epub>
