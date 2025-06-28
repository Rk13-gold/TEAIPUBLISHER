# Telegram AI Publisher - Enhanced Version

Una aplicación avanzada para gestionar y publicar contenido en Telegram con inteligencia artificial, monitoreo en tiempo real y gestión masiva de canales.

## 🚀 Nuevas Funcionalidades Mejoradas

### ⚡ Sistema de Caché Inteligente
- **Caché en memoria y base de datos** para consultas 10x más rápidas
- **Actualización automática** de información obsoleta
- **Gestión eficiente** de límites de la API de Telegram

### 🔍 Búsqueda Avanzada de Canales
- **Búsqueda por nombre y descripción** en tiempo real
- **Operaciones por lotes** para consultar múltiples canales
- **Historial de búsquedas** persistente
- **Filtrado inteligente** por tipo, suscriptores y actividad

### 📊 Monitoreo en Tiempo Real
- **Seguimiento automático** de nuevos mensajes
- **Alertas personalizables** para cambios importantes
- **Estadísticas de crecimiento** de suscriptores
- **Métricas de engagement** avanzadas

### 🎛️ Gestión Masiva de Canales
- **Configuración multi-canal** con tags y categorías
- **Monitoreo simultáneo** de múltiples canales
- **Exportación/importación** de configuraciones
- **Panel de control unificado**

### 📈 Análisis Mejorado
- **Tracking de rendimiento** por canal
- **Historial de estadísticas** con gráficos
- **Detección de tendencias** automática
- **Alertas de anomalías**

## 📁 Estructura del Proyecto Actualizada

```
telegram-ai-publisher/
├── services/
│   ├── enhanced_telegram_client.py    # Cliente mejorado con caché
│   ├── telegram_monitor.py            # Monitoreo en tiempo real
│   ├── telegram_metrics.py            # Métricas mejoradas
│   └── ...
├── gui/
│   ├── enhanced_channel_tab.py        # Nueva pestaña de gestión
│   ├── dashboard.py                   # Dashboard mejorado
│   └── ...
├── utils/
│   ├── channel_config.py              # Gestor de configuraciones
│   └── ...
├── demo_enhanced_features.py          # Script de demostración
└── requirements.txt                   # Dependencias actualizadas
```

## 🛠️ Instalación y Configuración

### Requisitos Actualizados
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