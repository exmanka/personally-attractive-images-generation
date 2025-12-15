import logging
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from src.services import api


logger = logging.getLogger(__name__)


async def get_generated_image(model: str,
                              seed: np.ndarray,
                              resize_ratio: int = 2) -> Image.Image:
    """Get generated image by API according to model by specified seed.

    :param model: 'stylegan' | 'dcgan'
    :param seed: seed to be passed to generator using API
    :param resize_ration: div resize ration, defaults to 2
    """
    seed_bytes = seed.tobytes()
    seed_file = {'seed': seed_bytes}

    match model:
        case 'dcgan':
            pass
        case 'stylegan3':
            status_code, data = await api.post('http://stylegan-generator:8000/generate/', seed_file, __name__)
    
    if status_code == 200:
        image = Image.open(BytesIO(data))
        image = image.resize((image.width // resize_ratio, image.height // resize_ratio))
    else:
        image = Image.new('RGB', (512, 512), 'white')
    
    return image


async def draw_image_number(image: Image.Image,
                            number: int,
                            text_pad: int = 16,
                            font_size: int = 48,
                            text_fill: tuple = (255, 255, 255)) -> Image.Image:
    """Draw number on picture.

    :param image: image where draw
    :param number: number to draw
    :param text_pad: pad of the text, defaults to 16
    :param font_size: size of the font, defaults to 48
    :param text_fill: color of the text, defaults to (255, 255, 255)
    """
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(font_size)
    bbox = font.getbbox(str(number))
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.rectangle([text_pad, text_pad, text_pad + text_width, text_pad * 3 + text_height], fill='black')
    draw.text((text_pad, text_pad), str(number), fill=text_fill, font=font)

    return image


async def create_general_image(images_list: list[Image.Image],
                               image_rows: int = 4,
                               image_cols: int = 3,
                               spacing_size: int = 10,
                               border_size: int = 2) -> BytesIO:
    """Create general image from specified list of images."""    
    image_width_max = max(img.width for img in images_list)
    image_height_max = max(img.height for img in images_list)
    final_image_width = (image_width_max + spacing_size) * image_cols
    final_image_height = (image_height_max + spacing_size) * image_rows
    final_image = Image.new('RGB', (final_image_width, final_image_height), 'white')

    x_offset = border_size
    y_offset = border_size
    counter = 0
    for img in images_list:
        final_image.paste(img, (x_offset, y_offset))
        x_offset += img.width + spacing_size
        counter += 1
        if counter % image_cols == 0:
            x_offset = border_size
            y_offset += img.height + spacing_size

    final_image_bytes = BytesIO()
    final_image.save(final_image_bytes, format='PNG')
    final_image_bytes.seek(0)

    return final_image_bytes
