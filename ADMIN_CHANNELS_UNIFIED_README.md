# 🔧 Admin Channels Manager - Sistema Unificado

Este sistema modular te permite extraer y gestionar los IDs de canales y grupos de Telegram donde tu bot es administrador o miembro, tanto públicos como privados.

## 🎯 Características Principales

### ✅ **Extracción Completa**
- **Canales públicos y privados** donde el bot es administrador
- **Grupos y supergrupos** con permisos de administración
- **Canales donde es solo miembro** (opcional)
- **Verificación de permisos específicos** del bot

### ✅ **Métodos de Extracción**
- **Rápido**: Basado en updates recientes (más rápido)
- **Completo**: Escaneo exhaustivo (más lento pero más completo)
- **Búsqueda específica**: Por ID o username de canal

### ✅ **Interfaces Múltiples**
- **GUI integrada**: Pestaña unificada en la aplicación
- **CLI avanzado**: Script de línea de comandos con múltiples opciones
- **Biblioteca modular**: Para integración en otros proyectos

---

## 🚀 Uso Rápido

### 1. **Interfaz Gráfica (GUI)**
Abre la aplicación Telegram AI Publisher y ve a la pestaña **"🔧 Admin Channels Manager"**:

1. Ingresa tu **Bot Token**
2. Selecciona opciones:
   - ☑️ **Comprehensive Scan**: Escaneo más completo
   - ☑️ **Include Member Channels**: Incluir canales donde solo es miembro
3. Haz clic en **"🔍 Extract Admin Channels"**
4. Los resultados aparecerán en la tabla
5. Usa **"📋 Copy IDs"** o **"💾 Save to File"** para exportar

### 2. **Línea de Comandos (CLI)**

#### Extracción básica (solo IDs):
```bash
python extract_admin_channels_enhanced.py --token YOUR_BOT_TOKEN
```

#### Extracción detallada:
```bash
python extract_admin_channels_enhanced.py --token YOUR_BOT_TOKEN --detailed
```

#### Escaneo completo:
```bash
python extract_admin_channels_enhanced.py --token YOUR_BOT_TOKEN --comprehensive --detailed
```

#### Incluir canales donde es miembro:
```bash
python extract_admin_channels_enhanced.py --token YOUR_BOT_TOKEN --members --detailed
```

#### Guardar en archivo:
```bash
python extract_admin_channels_enhanced.py --token YOUR_BOT_TOKEN --save channels.txt
```

#### Buscar canal específico:
```bash
python extract_admin_channels_enhanced.py --token YOUR_BOT_TOKEN --search @channel_username
python extract_admin_channels_enhanced.py --token YOUR_BOT_TOKEN --search -1001234567890
```

---

## 📊 Tipos de Información Extraída

### **Información Básica**
- **ID del canal/grupo**: Número único de identificación
- **Título**: Nombre del canal o grupo
- **Username**: @username (si es público)
- **Tipo**: Canal, Supergrupo, o Grupo
- **Privacidad**: Si es público o privado

### **Estado del Bot**
- **🔧 Administrador**: Bot tiene permisos de administración
- **👥 Miembro**: Bot es solo miembro (sin permisos admin)
- **Rol específico**: Creator, Administrator, Member

### **Permisos Específicos** (para administradores)
- Gestionar chat
- Publicar mensajes
- Editar mensajes
- Eliminar mensajes
- Invitar usuarios
- Restringir miembros
- Fijar mensajes
- Promover miembros

---

## 🔧 Arquitectura Modular

### **Componentes Principales**

#### 1. `BotChannelIDExtractor` (Núcleo)
Clase principal ubicada en `utils/bot_channel_extractor.py`:

```python
from utils.bot_channel_extractor import BotChannelIDExtractor

extractor = BotChannelIDExtractor("YOUR_BOT_TOKEN")

# Métodos principales:
admin_channels = extractor.get_admin_channel_ids_only()           # Solo IDs
detailed_info = extractor.get_admin_channels_detailed()           # Info completa
comprehensive = extractor.get_comprehensive_admin_channels()      # Escaneo completo
channel_info = extractor.get_channel_info_by_id("@username")      # Búsqueda específica
```

#### 2. `UnifiedAdminChannelsTab` (GUI)
Interfaz gráfica en `gui/unified_admin_channels_tab.py`:
- Búsqueda en tiempo real
- Tabla de resultados interactiva
- Opciones de exportación
- Logs de progreso

#### 3. CLI Mejorado
Script completo en `extract_admin_channels_enhanced.py`:
- Múltiples modos de operación
- Opciones avanzadas
- Exportación a archivos
- Modo silencioso

---

## 📝 Ejemplos de Uso Programático

### **Extracción Simple**
```python
from utils.bot_channel_extractor import extract_admin_channel_ids_only

success, channel_ids, message = extract_admin_channel_ids_only(
    bot_token="YOUR_BOT_TOKEN",
    verbose=True,
    comprehensive=False
)

if success:
    print(f"Found {len(channel_ids)} admin channels:")
    for channel_id in channel_ids:
        print(f"  {channel_id}")
```

### **Extracción Detallada**
```python
from utils.bot_channel_extractor import BotChannelIDExtractor

extractor = BotChannelIDExtractor("YOUR_BOT_TOKEN")

# Test del bot
bot_info = extractor.test_bot_token()
if bot_info['success']:
    print(f"Bot conectado: {bot_info['message']}")
    
    # Obtener canales admin con detalles
    channels = extractor.get_comprehensive_admin_channels(
        include_member_channels=False  # Solo canales donde es admin
    )
    
    for channel in channels:
        print(f"Canal: {channel['title']}")
        print(f"  ID: {channel['id']}")
        print(f"  Tipo: {channel['type']}")
        print(f"  Admin: {'Sí' if channel['is_admin'] else 'No'}")
        print(f"  Privado: {'Sí' if channel['is_private'] else 'No'}")
```

### **Búsqueda Específica**
```python
extractor = BotChannelIDExtractor("YOUR_BOT_TOKEN")

# Buscar por username
channel_info = extractor.get_channel_info_by_id("@mi_canal")

# Buscar por ID numérica
channel_info = extractor.get_channel_info_by_id("-1001234567890")

if channel_info:
    print(f"Canal encontrado: {channel_info['title']}")
    print(f"Miembros: {channel_info['member_count']}")
    
    # Verificar permisos del bot
    admin_info = extractor.check_admin_permissions(channel_info['id'])
    if admin_info['is_admin']:
        print("🔧 Bot es administrador")
        print(f"Rol: {admin_info['status']}")
    else:
        print("👥 Bot no es administrador")
```

---

## 🔍 Casos de Uso

### **1. Configuración Inicial**
- Descubrir todos los canales donde el bot puede publicar
- Identificar permisos específicos en cada canal
- Configurar canales para publicación automática

### **2. Monitoreo y Mantenimiento**
- Verificar regularmente el acceso del bot
- Detectar cambios en permisos
- Identificar nuevos canales añadidos

### **3. Gestión de Contenido**
- Seleccionar canales específicos para tipos de contenido
- Verificar capacidades antes de publicar
- Gestionar múltiples canales simultáneamente

### **4. Debugging y Troubleshooting**
- Verificar por qué no se puede publicar en un canal
- Confirmar que el bot tiene los permisos necesarios
- Identificar problemas de configuración

---

## ⚙️ Configuración y Requisitos

### **Dependencias**
```bash
pip install requests PySide6
```

### **Variables de Entorno (Opcional)**
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

### **Archivos de Configuración**
- Los IDs extraídos se guardan en `admin_channel_ids.txt`
- Los logs se almacenan en el módulo de logging de la aplicación
- La configuración de la GUI se integra con `core/config.py`

---

## 🛡️ Consideraciones de Seguridad

### **Token del Bot**
- ⚠️ **Nunca hardcodees el token** en el código
- ✅ Usa variables de entorno o archivos de configuración seguros
- ✅ El token se oculta por defecto en la GUI

### **Permisos Mínimos**
El bot necesita únicamente:
- Acceso básico a la API de Telegram
- Capacidad de obtener información de chats
- No requiere permisos especiales de administración

### **Limitaciones de Rate**
- La API de Telegram tiene límites de velocidad
- El escaneo completo es más lento para evitar limitaciones
- Se implementan delays automáticos entre solicitudes

---

## 🐛 Solución de Problemas

### **Error: "Bot token test failed"**
- Verifica que el token sea correcto
- Asegúrate de que el bot esté activo
- Revisa la conectividad a internet

### **No se encuentran canales**
- El bot debe haber recibido mensajes en los canales recientemente
- Usa el modo "Comprehensive Scan" para búsqueda más amplia
- Verifica que el bot esté realmente añadido a los canales

### **Permisos insuficientes**
- El bot debe ser administrador para aparecer como admin
- Algunos canales pueden tener restricciones especiales
- Verifica los permisos específicos del bot en Telegram

### **Error en la GUI**
- Asegúrate de tener PySide6 instalado correctamente
- Verifica que todos los archivos estén en su lugar
- Revisa los logs de la aplicación

---

## 📚 API Reference

### **Métodos Principales**

#### `BotChannelIDExtractor(bot_token: str)`
Constructor principal de la clase extractora.

#### `test_bot_token() -> Dict[str, any]`
Verifica la validez del token del bot.

#### `get_admin_channel_ids_only() -> List[int]`
Obtiene solo las IDs de canales donde el bot es admin (método rápido).

#### `get_admin_channels_detailed() -> List[Dict]`
Obtiene información detallada de canales admin (método rápido).

#### `get_comprehensive_admin_channels(include_member_channels: bool = False) -> List[Dict]`
Escaneo completo de todos los canales accesibles.

#### `get_channel_info_by_id(channel_id: str) -> Optional[Dict]`
Obtiene información de un canal específico por ID o username.

#### `check_admin_permissions(chat_id: int) -> Dict[str, any]`
Verifica permisos específicos del bot en un chat.

---

## 🔄 Integración con la Aplicación

### **Flujo de Trabajo Típico**
1. **Extracción**: Usar la pestaña unificada para obtener IDs
2. **Configuración**: Configurar canales en Channel Manager
3. **Publicación**: Usar los canales configurados para publicar contenido
4. **Monitoreo**: Verificar métricas y rendimiento

### **Conexión con Otros Módulos**
- **Content Tab**: Seleccionar canales para contenido específico
- **Publish Tab**: Usar IDs extraídas para publicación
- **Metrics Tab**: Monitorear rendimiento por canal
- **AI Tab**: Generar contenido específico por audiencia de canal

---

## 📈 Mejoras Futuras

### **Características Planeadas**
- 🔄 Sincronización automática de canales
- 📊 Análisis de audiencia por canal
- 🤖 Sugerencias de contenido por canal
- 📅 Programación avanzada por canal
- 🔔 Notificaciones de cambios en permisos

### **Optimizaciones Técnicas**
- ⚡ Cache de información de canales
- 🔄 Actualización incremental
- 📊 Métricas de rendimiento
- 🛡️ Mejores validaciones de seguridad

---

¡Con este sistema unificado y modular, puedes gestionar fácilmente todos los canales donde tu bot de Telegram tiene acceso! 🚀
