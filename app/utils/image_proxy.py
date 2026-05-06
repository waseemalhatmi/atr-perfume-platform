import os
import requests
import uuid
from flask import current_app
from app.utils.logger import get_logger

log = get_logger(__name__)

def proxy_image(url: str) -> str:
    """
    Downloads an external image and saves it locally to avoid hotlinking 
    and dead images from external feeds.
    
    Args:
        url: The remote URL of the image.
        
    Returns:
        The local path relative to static/ (e.g., 'uploads/proxied_images/abc.jpg')
        or the original URL if download fails.
    """
    if not url or not url.startswith('http'):
        return url
        
    # Check if we already proxied this (simple deduplication could be added here)
    
    try:
        # 1. Prepare storage path
        # Assuming we are in app/utils, so go up to root
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'proxied_images')
        os.makedirs(upload_folder, exist_ok=True)
        
        # 2. Extract extension safely
        ext = 'jpg'
        if '.' in url:
            possible_ext = url.split('.')[-1].split('?')[0].lower()
            if possible_ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                ext = possible_ext
        
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_folder, filename)
        
        # 3. Fetch image with timeout and user-agent to avoid blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15, stream=True)
        if response.status_code == 200:
            # Check content size (max 5MB)
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 5 * 1024 * 1024:
                log.warning("image_too_large", url=url, size=content_length)
                return url

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(4096):
                    f.write(chunk)
            
            # Return relative path for database storage (matching how Flask serves static)
            return f"uploads/proxied_images/{filename}"
        
        log.warning("image_proxy_http_error", url=url, status=response.status_code)
        return url
        
    except Exception as e:
        log.error("image_proxy_exception", url=url, error=str(e))
        return url
