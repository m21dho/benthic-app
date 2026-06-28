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


# ============================================================
# GRAD-CAM — melihat area gambar yang menjadi fokus model
# ============================================================
def _find_gradcam_target_layer(model, layer_name=None):
    """
    Cari layer feature-map (4D output) terakhir untuk dijadikan basis Grad-CAM.
    Coba nama layer spesifik dulu, lalu 'out_relu' (umum di MobileNetV2),
    baru fallback ke layer 4D terakhir di model.
    """
    if layer_name:
        try:
            return model.get_layer(layer_name)
        except ValueError:
            pass

    try:
        return model.get_layer("out_relu")
    except ValueError:
        pass

    for layer in reversed(model.layers):
        try:
            shape = layer.output.shape
        except Exception:
            continue
        if shape is not None and len(shape) == 4:
            return layer

    return None


def make_gradcam_heatmap(model, img_input, pred_index=None, layer_name=None):
    """
    Hitung heatmap Grad-CAM mentah (2D, ternormalisasi 0..1).
    img_input: array sudah di-preprocess, shape (1, H, W, 3).
    Return (heatmap_2d_atau_None, pred_index_yang_dipakai).
    """
    import tensorflow as tf

    target_layer = _find_gradcam_target_layer(model, layer_name)
    if target_layer is None:
        return None, pred_index

    grad_model = tf.keras.models.Model(
        inputs=model.inputs, outputs=[target_layer.output, model.output]
    )

    with tf.GradientTape() as tape:
        conv_output, predictions = grad_model(img_input)
        if pred_index is None:
            pred_index = int(tf.argmax(predictions[0]))
        class_channel = predictions[:, pred_index]

    grads = tape.gradient(class_channel, conv_output)
    if grads is None:
        return None, pred_index

    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_output = conv_output[0]
    heatmap = conv_output @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0)
    max_val = tf.math.reduce_max(heatmap)
    heatmap = heatmap / (max_val + 1e-8)
    return heatmap.numpy(), pred_index


def overlay_gradcam(pil_image, heatmap, alpha=0.45, img_size=IMG_SIZE):
    """
    Tempelkan heatmap (colormap jet) di atas gambar asli.
    Return PIL.Image hasil overlay.
    """
    import cv2
    from PIL import Image as PILImage

    base_img = np.array(pil_image.convert("RGB").resize((img_size, img_size)))

    heatmap_uint8 = np.uint8(255 * heatmap)
    heatmap_resized = cv2.resize(heatmap_uint8, (img_size, img_size))
    heatmap_color = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)
    heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

    overlay = heatmap_color.astype(np.float32) * alpha + base_img.astype(np.float32) * (1 - alpha)
    overlay = np.clip(overlay, 0, 255).astype(np.uint8)
    return PILImage.fromarray(overlay)


def compute_gradcam_overlay(model, pil_image, pred_index=None, alpha=0.45):
    """
    Fungsi siap-pakai: hitung Grad-CAM utk pil_image & kembalikan PIL.Image
    hasil overlay, atau None jika gagal (mis. tidak ada conv layer ditemukan).
    """
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    img_rgb = pil_image.convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    img_array = preprocess_input(np.array(img_rgb, dtype=np.float32))
    img_input = np.expand_dims(img_array, axis=0)

    try:
        heatmap, used_index = make_gradcam_heatmap(model, img_input, pred_index=pred_index)
    except Exception:
        return None

    if heatmap is None:
        return None

    return overlay_gradcam(pil_image, heatmap, alpha=alpha)
