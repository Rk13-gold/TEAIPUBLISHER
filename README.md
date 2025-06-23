# Telegram AI Publisher

## Descripción del Proyecto
Telegram AI Publisher es una aplicación diseñada para automatizar la publicación de contenido en canales de Telegram utilizando inteligencia artificial. La aplicación permite gestionar títulos y asociar imágenes, generar contenido a través de un modelo de lenguaje, y programar publicaciones automáticas en Telegram.

## Estructura del Proyecto
El proyecto está organizado en varios módulos, cada uno con responsabilidades específicas:

- **core**: Maneja la configuración, la base de datos y el registro de eventos.
- **data**: Define los modelos de datos y las operaciones de acceso a la base de datos.
- **ai_integration**: Se encarga de la integración con el modelo de lenguaje LM Studio.
- **services**: Contiene la lógica para interactuar con la API de Telegram y la programación de publicaciones.
- **gui**: Implementa la interfaz gráfica de usuario utilizando PySide6.
- **utils**: Proporciona funciones auxiliares, como validaciones y gestión de metadatos de imágenes.
- **tests**: Contiene pruebas unitarias para asegurar la calidad del código.

## Requisitos
- Python 3.7 o superior
- PySide6
- SQLite
- Requests (para la API de Telegram)

## Instalación
1. Clona el repositorio:
   ```
   git clone <URL_DEL_REPOSITORIO>
   cd telegram-ai-publisher
   ```

2. Instala las dependencias necesarias:
   ```
   pip install -r requirements.txt
   ```

3. Configura el archivo `core/config.py` con tus credenciales de la API de Telegram y otros parámetros necesarios.

## Uso
1. Ejecuta la aplicación:
   ```
   python main.py
   ```

2. Utiliza la interfaz gráfica para:
   - Gestionar títulos y asociar imágenes.
   - Generar contenido utilizando inteligencia artificial.
   - Programar y publicar automáticamente en Telegram.
   - Visualizar métricas y estadísticas de publicaciones.

## Contribuciones
Las contribuciones son bienvenidas. Si deseas contribuir, por favor abre un issue o envía un pull request.

## Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.