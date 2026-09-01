import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("download")

def download_sample_real_video():
    os.makedirs("data/videos", exist_ok=True)
    target_path = "data/videos/real_cctv_traffic.mp4"
    
    # Intel IoT DevKit CC0 Open Sample Traffic Video
    url = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/car-detection.mp4"
    
    logger.info(f"Downloading independently sourced open CCTV traffic video from {url}...")
    try:
        urllib.request.urlretrieve(url, target_path)
        size = os.path.getsize(target_path)
        logger.info(f"Successfully downloaded {target_path} ({size} bytes)")
        return target_path
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None

if __name__ == "__main__":
    download_sample_real_video()
