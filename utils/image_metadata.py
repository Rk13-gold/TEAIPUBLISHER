from PIL import Image
from PIL.ExifTags import TAGS
import os
import json

def extract_metadata(image_path):
    """
    Extracts metadata from an image file.

    Args:
        image_path (str): The path to the image file.

    Returns:
        dict: A dictionary containing the extracted metadata.
    """
    metadata = {}
    try:
        with Image.open(image_path) as img:
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['size'] = img.size
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    metadata[tag] = value
    except Exception as e:
        metadata['error'] = str(e)
    return metadata

def save_metadata_to_file(metadata, output_path):
    try:
        with open(output_path, 'w') as json_file:
            json.dump(metadata, json_file, indent=4)
    except Exception as e:
        print(f"Error saving metadata to file: {e}")

def get_image_keywords(image_path):
    metadata = extract_metadata(image_path)
    keywords = []
    if 'UserComment' in metadata:
        keywords.extend(metadata['UserComment'].split(','))
    return keywords

def get_image_tone(image_path):
    # Placeholder for tone determination logic
    return "Neutral"