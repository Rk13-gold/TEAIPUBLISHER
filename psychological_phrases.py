#!/usr/bin/env python3
"""
Generador de frases psicológicas para reemplazar en el código
"""

# Arsenal de 50+ frases psicológicas poderosas
psychological_phrases = [
    # Curiosidad y decisión poderosa
    "🤔 El momento de la verdad ha llegado... ¿Cuál de estas opciones cambiará tu destino para siempre?",
    "🎯 Tres caminos se abren ante ti, solo uno te llevará al éxito que tanto deseas alcanzar hoy",
    "🔍 La respuesta que has estado buscando durante tanto tiempo está escondida detrás de uno de estos botones",
    "⚡ Tu futuro se decide ahora mismo con un simple clic... ¿Estás preparado para esta transformación total?",
    "🧠 Miles de personas ya eligieron su destino aquí, ahora es tu turno de unirte a los ganadores",
    
    # Escasez y urgencia extrema
    "⏰ Solo quedan pocas horas para acceder a esta información que podría cambiar tu vida completamente",
    "🔥 Esta oportunidad única desaparecerá pronto, no dejes que otros tomen tu lugar en el éxito",
    "💎 El acceso exclusivo que todos quieren obtener está aquí, pero no estará disponible para siempre",
    "🚨 Último momento para descubrir el secreto que los más exitosos han estado guardando celosamente",
    "⚡ La ventana de oportunidad se cierra en cualquier momento, no pierdas tu única chance real",
    
    # Autoridad y prueba social masiva
    "👑 Únete a los miles de personas exitosas que ya descubrieron el poder de estas estrategias comprobadas",
    "🏆 Los líderes más influyentes del mundo utilizan exactamente estos métodos que encontrarás aquí dentro",
    "💼 Profesionales de élite pagan miles por acceder a esta información que tienes al alcance hoy",
    "🎖️ Expertos reconocidos mundialmente recomiendan estas técnicas que han transformado millones de vidas",
    "👥 Más de cien mil personas han cambiado su realidad usando exactamente lo que encontrarás aquí",
    
    # Transformación radical garantizada
    "🚀 Tu versión más poderosa y exitosa está esperando ser liberada con la información de estos enlaces",
    "💫 Imagina despertar mañana siendo una persona completamente diferente, más fuerte, más segura, más exitosa",
    "🌟 El cambio radical que necesitas para alcanzar tus sueños más ambiciosos comienza con esta decisión",
    "🎭 Deja atrás la versión antigua de ti mismo y abraza el poder ilimitado que llevas dentro",
    "🔑 La llave maestra que abrirá todas las puertas de tu éxito está esperando tu decisión",
    
    # Pérdida y arrepentimiento intenso
    "😱 No cometas el mismo error que miles de personas que dejaron pasar esta oportunidad única",
    "💔 El arrepentimiento de no actuar hoy será mucho más doloroso que cualquier acción que tomes",
    "🔒 Mientras dudas, otros están tomando la decisión que los llevará al siguiente nivel de éxito",
    "⚠️ La diferencia entre los que triunfan y los que se quedan atrás está en estas decisiones",
    "😔 No seas parte de las estadísticas de personas que siempre dicen 'debería haber actuado antes'",
    
    # Exclusividad y estatus VIP
    "👑 Acceso VIP reservado solo para las mentes más brillantes y ambiciosas como la tuya",
    "💎 Contenido exclusivo que la mayoría nunca tendrá la oportunidad de ver en toda su vida",
    "🏰 Bienvenido al círculo interno de personas que realmente entienden cómo funciona el éxito verdadero",
    "🔐 Información clasificada que solo los más determinados tienen el privilegio de conocer y aplicar",
    "✨ Únete a la élite de personas que no se conforman con la mediocridad y buscan la excelencia",
    
    # Curiosidad intensa y misterio
    "🕵️ El secreto mejor guardado de los millonarios está a punto de ser revelado en estos enlaces",
    "🎪 Lo que descubrirás aquí dentro desafiará todo lo que creías saber sobre el éxito y poder",
    "🔍 La verdad oculta que las grandes corporaciones no quieren que sepas está aquí esperándote",
    "🎭 Prepárate para que tu realidad sea completamente sacudida por lo que vas a descubrir ahora",
    "🌪️ Tu perspectiva del mundo cambiará para siempre después de conocer esta información revolucionaria",
    
    # Poder y control absoluto
    "⚡ Toma el control total de tu destino con las herramientas más poderosas que existen actualmente",
    "🔥 Libera el poder ilimitado que llevas dentro usando estas técnicas de transformación personal radical",
    "💪 Conviértete en la versión imparable de ti mismo que siempre supiste que podías llegar a ser",
    "🦁 Despierta al león que duerme dentro de ti y domina cada aspecto de tu vida personal",
    "⚔️ Forja tu carácter con las mismas técnicas que usan los guerreros mentales más exitosos",
    
    # Destino y propósito superior
    "🌟 Tu verdadero propósito en la vida está esperando ser descubierto en estos recursos transformadores",
    "🎯 El camino hacia tu destino más grandioso comienza exactamente aquí, en este momento crucial",
    "🚪 Las puertas hacia tu futuro más brillante están abiertas, solo necesitas dar el primer paso",
    "🗺️ El mapa del tesoro hacia tu éxito personal está escondido en alguno de estos enlaces",
    "🎖️ Tu misión más importante en la vida te está llamando, responde a ese llamado ahora",
    
    # Inteligencia y sabiduría ancestral
    "🧠 Las mentes más brillantes de la historia compartieron estos secretos que cambiarán tu perspectiva",
    "📚 La sabiduría acumulada de generaciones de genios está condensada en estos recursos únicos",
    "🎓 Obtén el conocimiento que las universidades más prestigiosas no enseñan en sus programas tradicionales",
    "💡 Ideas revolucionarias que han transformado civilizaciones enteras están esperando tu descubrimiento aquí",
    "🔬 La ciencia del éxito decodificada al más alto nivel está disponible en estos enlaces",
    
    # Acción inmediata y momentum
    "🏃 El momento perfecto para actuar es AHORA, no mañana, no después, sino en este instante",
    "⚡ La energía del cambio está fluyendo en este momento, úsala antes de que se desvanezca",
    "🔥 Tu momento de gloria comienza con la decisión que tomes en los próximos segundos",
    "💥 La explosión de transformación que necesitas está a un clic de distancia de tu realidad",
    "🌊 Surfea la ola del cambio ahora mismo antes de que pase y tengas que esperar",
    
    # Libertad y independencia
    "🕊️ Libérate para siempre de las cadenas mentales que te han mantenido atrapado durante años",
    "🌈 Descubre la libertad total que solo experimentan aquellos que se atreven a dar el salto",
    "🏖️ La vida de libertad financiera y emocional que sueñas está más cerca de lo que imaginas"
]

# Mostrar estadísticas
print(f"📊 Total de frases generadas: {len(psychological_phrases)}")
print(f"📝 Promedio de palabras por frase: {sum(len(phrase.split()) for phrase in psychological_phrases) / len(psychological_phrases):.1f}")

# Verificar que todas tengan más de 10 palabras
short_phrases = [phrase for phrase in psychological_phrases if len(phrase.split()) < 10]
if short_phrases:
    print(f"⚠️ Frases con menos de 10 palabras: {len(short_phrases)}")
else:
    print("✅ Todas las frases tienen 10+ palabras")

print(f"\n🎯 Frases listas para usar en el código")
