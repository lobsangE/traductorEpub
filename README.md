Traductor Avanzado de ePub con IA (OpenAI)

Este proyecto contiene un script de Python de alto rendimiento para traducir archivos .epub de forma rápida, robusta y automática, utilizando la potente API de OpenAI (GPT-4o).

El script ha sido optimizado para manejar libros largos y complejos, asegurando una traducción fluida, preservación del formato original y resiliencia frente a errores de red o interrupciones.

✨ Características Principales

    🤖 Traducción con OpenAI: Utiliza los modelos más avanzados de OpenAI (gpt-4o) para obtener traducciones de alta calidad.

    ⚡ Alta Velocidad (Procesamiento Asíncrono): Envía cientos de fragmentos de texto a la API de forma concurrente, reduciendo drásticamente el tiempo total de traducción en comparación con métodos secuenciales.

    🎨 Preservación de Formato HTML: Mantiene intacta toda la maquetación del libro, incluyendo negritas, cursivas, enlaces, listas y otras etiquetas HTML.

    📦 Procesamiento por Lotes (Batches): Agrupa las solicitudes a la API en lotes para evitar exceder los límites de tasa (rate limits), garantizando un proceso estable y sin errores de cuota.

    🔄 Reintentos Automáticos: Si una solicitud a la API falla por un problema de red, el script la reintentará automáticamente varias veces antes de marcarla como error.

    💾 Persistencia y Reanudación de Progreso: El script guarda el progreso después de traducir cada capítulo. Si el proceso se interrumpe, puedes volver a ejecutar el mismo comando y continuará exactamente donde se quedó, sin perder trabajo ni gastar créditos de API innecesariamente.

    🔑 Manejo Seguro de API Keys: Utiliza un archivo .env para gestionar tu clave de API de OpenAI de forma segura, evitando exponerla en el código fuente.

✅ Requisitos

    Python 3.8 o superior.

    Una API Key de OpenAI. Puedes obtenerla en platform.openai.com/api-keys.

    Las librerías de Python listadas en el archivo requirements.txt.

⚙️ Instalación y Configuración

    Clonar el repositorio (o descargar los archivos):
    Bash

git clone https://github.com/lobsangE/traductorEpub.git
cd traductorEpub

Instalar las dependencias:
Se recomienda crear un entorno virtual primero. Luego, instala las librerías necesarias:
Bash

pip install -r requirements.txt

Configurar la API Key:
Crea un archivo llamado .env en la raíz del proyecto. Este archivo no debe ser subido al repositorio (.gitignore ya está configurado para ignorarlo). Añade tu clave de API de OpenAI dentro de él de la siguiente forma:
Fragmento de código

    OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    Reemplaza sk-xxxxxxxx... con tu clave real.

🚀 Modo de Uso

Una vez configurado, puedes ejecutar el script desde tu terminal. La sintaxis es la siguiente:
Bash

python traductor.py <ruta_del_archivo_de_entrada.epub> <ruta_para_el_archivo_de_salida.epub>

Ejemplo:

Bash

python traductor.py "Alices Adventures in Wonderland.epub" "Alicia en el País de las Maravillas [ES].epub"

El script mostrará el progreso en la consola, informando qué capítulo está procesando, el estado de los lotes de traducción y cuándo guarda el progreso en el disco. Si lo detienes y lo vuelves a ejecutar, verás un mensaje indicando que está reanudando una sesión anterior.