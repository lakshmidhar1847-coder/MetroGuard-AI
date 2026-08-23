"""
MetroGuard AI - Dataset Downloader
Downloads the official MetroPT-3 dataset from the UCI Machine Learning Repository
and extracts it to data/raw/ while keeping the raw archive and files intact.
"""

import os
import zipfile
import requests
from tqdm import tqdm

UCI_METROPT3_URL = "https://archive.ics.uci.edu/static/public/791/metropt+3+dataset.zip"
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
ZIP_DEST = os.path.join(RAW_DATA_DIR, "metropt_3_dataset.zip")

def download_file(url, destination):
    print(f"Downloading from {url}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, stream=True, headers=headers, timeout=60)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    chunk_size = 1024 * 1024  # 1 MB chunk
    
    with open(destination, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="MetroPT-3 Download", unit_divisor=1024) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    print(f"Download completed: {destination} ({os.path.getsize(destination) / (1024*1024):.2f} MB)")

def extract_zip(zip_path, extract_dir):
    print(f"Extracting {zip_path} into {extract_dir}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print("Extraction completed.")

def main():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    
    # Check if already downloaded
    csv_candidates = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".csv")]
    if csv_candidates:
        print(f"Dataset already exists in {RAW_DATA_DIR}: {csv_candidates}")
    else:
        if not os.path.exists(ZIP_DEST):
            download_file(UCI_METROPT3_URL, ZIP_DEST)
        extract_zip(ZIP_DEST, RAW_DATA_DIR)
        
    print("\nContents of data/raw/:")
    for fname in os.listdir(RAW_DATA_DIR):
        fpath = os.path.join(RAW_DATA_DIR, fname)
        fsize = os.path.getsize(fpath) / (1024*1024)
        print(f" - {fname} ({fsize:.2f} MB)")

if __name__ == "__main__":
    main()
