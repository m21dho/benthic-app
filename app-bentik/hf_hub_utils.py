"""
hf_hub_utils.py — Fungsi yang berbicara ke Hugging Face Hub.
Hanya berisi pengambilan (download) model — website ini murni untuk
klasifikasi, tidak ada fitur upload dataset/training dari sisi web.
"""
import os

from config import MODEL_FILENAME


def hf_download_model(hf_cfg, local_dir="models"):
    """Download model .keras dari HF Hub ke folder lokal. Return (path, error_msg)."""
    from huggingface_hub import hf_hub_download
    os.makedirs(local_dir, exist_ok=True)
    try:
        path = hf_hub_download(
            repo_id=hf_cfg["model_repo"],
            filename=MODEL_FILENAME,
            token=hf_cfg["token"],
            local_dir=local_dir,
        )
        return path, None
    except Exception as e:
        return None, str(e)
