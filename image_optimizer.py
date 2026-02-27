from PIL import Image
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def optimize_image(image_path, max_width=1200, quality=80):
    """
    Сжимает изображение, конвертирует в WebP и удаляет оригинал.
    Возвращает путь к новому файлу.
    """
    try:
        base_path = os.path.splitext(image_path)[0]
        webp_path = f"{base_path}.webp"

        with Image.open(image_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            if img.size[0] > max_width:
                w_percent = (max_width / float(img.size[0]))
                h_size = int((float(img.size[1]) * float(w_percent)))
                img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
            
            img.save(webp_path, "WEBP", quality=quality)

        if os.path.exists(image_path) and image_path != webp_path:
            os.remove(image_path)

        logger.info("✨ WebP создан: %s", webp_path)
        return webp_path

    except Exception as e:
        logger.warning("Image optimization error: %s; %s", image_path, e)
        return image_path