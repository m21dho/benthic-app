"""
app.py — Lapisan UI Streamlit.
Aplikasi ini KHUSUS untuk klasifikasi (tidak ada fitur upload dataset/training
dari web). Logika model ada di model_utils.py & hf_hub_utils.py.
"""
import os
import warnings

import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image

from config import (
    CLASS_NAMES, CLASS_COLORS, IMG_SIZE, CONFIDENCE_THRESHOLD,
    MODEL_FOLDER, MODEL_FILENAME, get_hf_config,
)
from hf_hub_utils import hf_download_model
from model_utils import load_model_cached, classify_image, compute_gradcam_overlay
from styles import CSS, render_hero, render_prediction_card, render_not_detected_card, render_footer

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


# ============================================================
# PAGE CONFIG & TEMA
# ============================================================
st.set_page_config(
    page_title="Klasifikasi Habitat Bentik",
    page_icon="🌊",
    layout="centered",
)
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    render_hero(
        "🌊 Klasifikasi Habitat Bentik",
        "Identifikasi tutupan dasar laut dari foto bawah air — alga, karang, "
        "lamun, pasir, atau lainnya.",
    ),
    unsafe_allow_html=True,
)

with st.expander("ℹ️ Cara pakai"):
    st.markdown(
        "Upload gambar habitat bentik, lalu klik **Jalankan klasifikasi**. "
        "Hasil prediksi, confidence semua kelas, dan area fokus model (Grad-CAM) "
        "akan ditampilkan.\n\n"
        f"Model menerima gambar {IMG_SIZE}×{IMG_SIZE}px, dengan confidence threshold "
        f"{CONFIDENCE_THRESHOLD*100:.0f}%."
    )


# ============================================================
# LOAD MODEL (dari HF Hub atau lokal)
# ============================================================
hf_cfg = get_hf_config()
hf_available = hf_cfg is not None

if "loaded_model" not in st.session_state:
    st.session_state.loaded_model = None
    st.session_state.model_loaded = False
    st.session_state.model_debug = ""

model_path = os.path.join(MODEL_FOLDER, MODEL_FILENAME)
debug_lines = []

if not st.session_state.model_loaded:
    if hf_available and not os.path.exists(model_path):
        debug_lines.append(f"Mencari di HF Hub repo: {hf_cfg['model_repo']}, file: {MODEL_FILENAME}")
        with st.spinner("⏳ Mengunduh model dari Hugging Face Hub..."):
            downloaded, dl_error = hf_download_model(hf_cfg, local_dir=MODEL_FOLDER)
            if downloaded:
                model_path = os.path.join(MODEL_FOLDER, MODEL_FILENAME)
                debug_lines.append(f"✅ Download dari HF Hub berhasil: {downloaded}")
            else:
                debug_lines.append(f"❌ Download dari HF Hub gagal: {dl_error}")
    elif not hf_available:
        debug_lines.append("HF Hub tidak terkonfigurasi (cek Secrets) — mencoba path lokal saja.")

    if os.path.exists(model_path):
        model, status = load_model_cached(model_path)
        debug_lines.append(status)
        if model is not None:
            st.session_state.loaded_model = model
            st.session_state.model_loaded = True
    else:
        debug_lines.append(f"File model tidak ditemukan di: {model_path}")

    st.session_state.model_debug = "\n".join(debug_lines)

if not st.session_state.model_loaded:
    st.error("❌ Model belum berhasil dimuat.")
    with st.expander("🔍 Detail error (untuk debugging)"):
        st.code(st.session_state.model_debug or "(tidak ada info)")


# ============================================================
# KLASIFIKASI
# ============================================================
st.markdown("#### Upload gambar habitat bentik")

uploaded_image = st.file_uploader(
    "Upload gambar untuk diklasifikasi",
    type=["jpg", "jpeg", "png", "bmp", "tiff"],
    help="Format: JPG, PNG, BMP, TIFF",
    key="classify_uploader",
)

if uploaded_image is not None and st.session_state.model_loaded:
    col1, col2 = st.columns(2)
    pil_image = Image.open(uploaded_image)

    with col1:
        st.markdown("**📸 Gambar input**")
        st.image(pil_image, width="stretch")

    with col2:
        st.markdown("**🔍 Informasi gambar**")
        st.info(
            f"**Dimensi:** {pil_image.width} × {pil_image.height} px\n\n"
            f"**Ukuran file:** {uploaded_image.size / 1024:.2f} KB"
        )

    # Reset hasil lama kalau gambar yang di-upload berganti
    fingerprint = (uploaded_image.name, uploaded_image.size)
    if st.session_state.get("classify_fingerprint") != fingerprint:
        st.session_state.pop("classify_result", None)
        st.session_state["classify_fingerprint"] = fingerprint
        st.session_state["classify_image"] = pil_image

    if st.button("🚀 Jalankan klasifikasi", width="stretch", type="primary"):
        try:
            with st.spinner("⏳ Memproses gambar..."):
                result = classify_image(st.session_state.loaded_model, pil_image)
            st.session_state["classify_result"] = result
            st.session_state["classify_image"] = pil_image
        except Exception as e:
            st.error(f"❌ Error: {e}")

    if "classify_result" in st.session_state:
        result = st.session_state["classify_result"]
        pred_class = result["pred_class"]
        confidence = result["confidence"]
        probs = result["probs"]
        below_threshold = confidence < CONFIDENCE_THRESHOLD

        if below_threshold:
            st.markdown(render_not_detected_card(confidence), unsafe_allow_html=True)
        else:
            st.markdown(render_prediction_card(pred_class, confidence), unsafe_allow_html=True)

        st.markdown("**📋 Confidence semua kelas**")

        sorted_items = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        chart_df = pd.DataFrame(sorted_items, columns=["Kelas", "Confidence"])

        color_scale = alt.Scale(
            domain=[k for k, _ in sorted_items],
            range=[CLASS_COLORS.get(k, {"accent": "#888"})["accent"] for k, _ in sorted_items],
        )
        chart = (
            alt.Chart(chart_df)
            .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6, size=22)
            .encode(
                x=alt.X("Confidence:Q", title="Confidence (%)", scale=alt.Scale(domain=[0, 100])),
                y=alt.Y("Kelas:N", sort="-x", title=None),
                color=alt.Color("Kelas:N", scale=color_scale, legend=None),
                tooltip=["Kelas", alt.Tooltip("Confidence:Q", format=".2f")],
            )
            .properties(height=180)
        )
        st.altair_chart(chart, width="stretch")

        df = pd.DataFrame(
            [(k, f"{v:.2f}%") for k, v in sorted_items],
            columns=["Kelas", "Confidence (%)"],
        )
        st.dataframe(df, width="stretch", hide_index=True)

        # ── Grad-CAM ──
        st.markdown("---")
        st.markdown("**🔥 Grad-CAM — area fokus model**")
        st.caption(
            "Warna merah/kuning menandai bagian gambar yang paling memengaruhi "
            "prediksi model. Biru/hijau berarti area itu kurang berpengaruh."
        )

        gradcam_class = st.selectbox(
            "Lihat fokus model untuk kelas:",
            CLASS_NAMES,
            index=CLASS_NAMES.index(pred_class),
            key="gradcam_class_select",
        )
        target_idx = CLASS_NAMES.index(gradcam_class)
        cam_image = st.session_state.get("classify_image", pil_image)

        with st.spinner("🔥 Menghitung Grad-CAM..."):
            overlay_img = compute_gradcam_overlay(
                st.session_state.loaded_model, cam_image, pred_index=target_idx
            )

        if overlay_img is not None:
            gc1, gc2 = st.columns(2)
            with gc1:
                st.markdown("Gambar asli")
                st.image(cam_image.convert("RGB").resize((IMG_SIZE, IMG_SIZE)), width="stretch")
            with gc2:
                st.markdown(f"Fokus model: {gradcam_class}")
                st.image(overlay_img, width="stretch")
        else:
            st.info(
                "Grad-CAM tidak tersedia untuk arsitektur model ini "
                "(tidak ditemukan layer feature-map yang cocok)."
            )

elif uploaded_image is not None and not st.session_state.model_loaded:
    st.warning("⚠️ Model belum dimuat. Lihat detail error di atas.")
else:
    if st.session_state.model_loaded:
        st.info("📤 Silakan upload gambar untuk diklasifikasi.")
    else:
        st.error("❌ Model belum aktif. Lihat detail error di atas.")


# ============================================================
# FOOTER
# ============================================================
st.markdown(
    render_footer("🌊 Klasifikasi Habitat Bentik · Streamlit + TensorFlow + Hugging Face Hub"),
    unsafe_allow_html=True,
)
