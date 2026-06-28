"""
model_utils.py — Fungsi inti: memuat model & menjalankan klasifikasi.
Tidak ada layout/komponen UI di sini — hanya logika model.
"""
import os
import numpy as np
import streamlit as st

from config import CLASS_NAMES, NUM_CLASSES, IMG_SIZE


def load_model_custom_loader(model_path):
    """
    Coba load model dengan beberapa metode untuk handle masalah kompatibilitas
    antar versi Keras/TensorFlow.
    Return (model_or_None, list_of_error_strings).
    """
    from tensorflow.keras.models import load_model as tf_load_model
    methods = [
        {"label": "Direct load", "kwargs": {}},
        {"label": "safe_mode=False", "kwargs": {"safe_mode": False}},
        {"label": "compile=False", "kwargs": {"compile": False}},
        {"label": "safe_mode=False + compile=False",
         "kwargs": {"safe_mode": False, "compile": False}},
    ]
    errors = []
    for m in methods:
        try:
            return tf_load_model(model_path, **m["kwargs"]), errors
        except Exception as e:
            errors.append(f"{m['label']}: {e}")
    return None, errors


@st.cache_resource
def load_model_cached(model_path):
    """Load & cache model di memori. Return (model_or_None, status_msg)."""
    if not os.path.exists(model_path):
        return None, f"File model tidak ditemukan di path lokal: {model_path}"
    model, errors = load_model_custom_loader(model_path)
    if model is not None:
        return model, "Model berhasil dimuat"
    detail = "\n".join(f"- {e}" for e in errors)
    return None, f"Semua metode load gagal:\n{detail}"


def classify_image(model, pil_image):
    """
    Fungsi inti klasifikasi — murni logika, tanpa elemen Streamlit.
    Input : model Keras + gambar PIL
    Output: dict {
        "pred_class": str,
        "confidence": float (0..1),
        "probs": {nama_kelas: persentase_float, ...}
    }
    """
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    img_rgb = pil_image.convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    img_array = preprocess_input(np.array(img_rgb, dtype=np.float32))
    img_input = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_input, verbose=0)
    pred_confidence = float(np.max(predictions))
    pred_class_idx = int(np.argmax(predictions))
    pred_class = CLASS_NAMES[pred_class_idx]

    probs = {
        CLASS_NAMES[i]: float(predictions[0][i]) * 100
        for i in range(NUM_CLASSES)
    }

    return {
        "pred_class": pred_class,
        "confidence": pred_confidence,
        "probs": probs,
    }
