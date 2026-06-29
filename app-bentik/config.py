"""
config.py — Konfigurasi & konstanta bersama.
Tidak ada logika UI atau logika klasifikasi di sini, hanya data konfigurasi.
"""
import os
import streamlit as st

# ============================================================
# KELAS MODEL
# ============================================================
NUM_CLASSES = 5
CLASS_NAMES = ["Alga", "Karang", "Lainnya", "Lamun", "Pasir"]
# Urutan HARUS sama dengan sorted(os.listdir(TRAIN_DIR)) saat training:
#   alga, karang, lainnya, lamun, pasir (alfabetis)

# Ikon kecil per kelas (warna konsisten dipakai di badge & bar chart prediksi)
CLASS_ICONS = {
    "Alga": "🟢",
    "Karang": "🟠",
    "Lainnya": "⚪",
    "Lamun": "🟩",
    "Pasir": "🟡",
}

# Palet warna per kelas — dipetakan ke materi fisik aslinya
# (hijau utk alga, coral utk karang, abu utk lainnya, teal utk lamun, amber utk pasir)
CLASS_COLORS = {
    "Alga":    {"bg": "#E3F3E8", "accent": "#2E8B57", "text": "#1F5C3B"},
    "Karang":  {"bg": "#FCE9E1", "accent": "#D85A30", "text": "#8C3A1E"},
    "Lainnya": {"bg": "#EFEFEC", "accent": "#6B6B66", "text": "#3F3F3B"},
    "Lamun":   {"bg": "#E0F2EE", "accent": "#167F6B", "text": "#0E5447"},
    "Pasir":   {"bg": "#FBF1DD", "accent": "#B9802E", "text": "#7A551D"},
}

IMG_SIZE = 224
CONFIDENCE_THRESHOLD = 0.70

# ============================================================
# PATH MODEL
# ============================================================
MODEL_FOLDER = os.environ.get("MODEL_FOLDER", "models")
MODEL_FILENAME = "mobilenetv2_bentik_streamlit_fixed.keras"


# ============================================================
# KONFIGURASI HUGGING FACE HUB
# ============================================================
def get_hf_config():
    """
    Ambil konfigurasi HF Hub dari st.secrets atau environment variable.
    Return dict {"token", "model_repo"} atau None jika belum lengkap.

    Cara set di Streamlit Cloud: Settings → Secrets →
        HF_TOKEN = "hf_xxxxx"
        HF_MODEL_REPO = "username/bentik-model"
    """
    token = st.secrets.get("HF_TOKEN", os.environ.get("HF_TOKEN", ""))
    model_repo = st.secrets.get("HF_MODEL_REPO", os.environ.get("HF_MODEL_REPO", ""))
    if token and model_repo:
        return {"token": token, "model_repo": model_repo}
    return None
