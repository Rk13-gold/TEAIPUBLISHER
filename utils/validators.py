def validate_title(title):
    if not title or len(title) < 3:
        raise ValueError("El título debe tener al menos 3 caracteres.")
    return True

def validate_image_path(image_path):
    if not image_path or not image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        raise ValueError("La ruta de la imagen debe ser válida y tener una extensión de imagen soportada.")
    return True

def validate_keywords(keywords):
    if not isinstance(keywords, list) or not all(isinstance(keyword, str) for keyword in keywords):
        raise ValueError("Las palabras clave deben ser una lista de cadenas.")
    return True

def validate_tone(tone):
    valid_tones = ['informativo', 'persuasivo', 'divertido', 'serio']
    if tone not in valid_tones:
        raise ValueError(f"El tono debe ser uno de los siguientes: {', '.join(valid_tones)}.")
    return True

def validate_post_content(content):
    if not content or len(content) < 10:
        raise ValueError("El contenido de la publicación debe tener al menos 10 caracteres.")
    return True