"""
app.py — UI Streamlit layout sesuai wireframe:
  [gambar]          [output kelas]
                    [grad-cam]
  [Pilih Gambar] [Klasifikasi]
  [▸ detail (lipat)]

Confidence angka HANYA ada di dalam blok detail, dan di sana pun
TIDAK ditampilkan nilainya — hanya distribusi bar relatif.
"""
import os
import warnings

import streamlit as st
from PIL import Image

from config import (
    CLASS_NAMES, IMG_SIZE, CONFIDENCE_THRESHOLD,
    MODEL_FOLDER, MODEL_FILENAME, get_hf_config,
)
from hf_hub_utils import hf_download_model
from model_utils import load_model_cached, classify_image, compute_gradcam_overlay
from styles import (
    CSS,
    render_header,
    render_img_placeholder,
    render_placeholder_card,
    render_output_card,
    render_output_not_detected,
    render_img_label,
    render_sonar_no_numbers,
    render_footer,
)

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


# ============================================================
# PAGE CONFIG & CSS
# ============================================================
st.set_page_config(page_title="Habitat Bentik", page_icon="🌊", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(render_header(), unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================
for key, default in {
    "loaded_model": None,
    "model_loaded": False,
    "model_debug": "",
    "pil_image": None,
    "classify_fingerprint": None,
    "classify_result": None,
    "gradcam_class": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ============================================================
# LOAD MODEL
# ============================================================
hf_cfg = get_hf_config()
model_path = os.path.join(MODEL_FOLDER, MODEL_FILENAME)
debug_lines = []

if not st.session_state.model_loaded:
    if hf_cfg and not os.path.exists(model_path):
        debug_lines.append(f"Mengunduh dari HF Hub: {hf_cfg['model_repo']}")
        with st.spinner("Mengunduh model..."):
            downloaded, dl_error = hf_download_model(hf_cfg, local_dir=MODEL_FOLDER)
            if downloaded:
                model_path = os.path.join(MODEL_FOLDER, MODEL_FILENAME)
                debug_lines.append("Download berhasil")
            else:
                debug_lines.append(f"Download gagal: {dl_error}")
    elif not hf_cfg:
        debug_lines.append("HF Hub tidak terkonfigurasi — mencoba path lokal.")

    if os.path.exists(model_path):
        model, status = load_model_cached(model_path)
        debug_lines.append(status)
        if model is not None:
            st.session_state.loaded_model = model
            st.session_state.model_loaded = True
    else:
        debug_lines.append(f"Model tidak ditemukan: {model_path}")

    st.session_state.model_debug = "\n".join(debug_lines)

if not st.session_state.model_loaded:
    st.error("Model belum berhasil dimuat.")
    with st.expander("Detail error"):
        st.code(st.session_state.model_debug or "(tidak ada info)")
    st.stop()


# ============================================================
# LAYOUT UTAMA: gambar (kiri) | hasil (kanan)
# Membaca dari session_state — nilai widget (file_uploader, button)
# belum tersedia di sini, tapi session_state sudah ter-update dari
# run sebelumnya berkat st.rerun() di bawah.
# ============================================================
has_image  = st.session_state.pil_image is not None
has_result = st.session_state.classify_result is not None

col_img, col_res = st.columns([12, 10], gap="medium")

# ── Kolom kiri: preview gambar ──
with col_img:
    if has_image:
        st.markdown(render_img_label("preview"), unsafe_allow_html=True)
        st.image(st.session_state.pil_image, width="stretch")
    else:
        st.markdown(render_img_placeholder(), unsafe_allow_html=True)

# ── Kolom kanan: output kelas + grad-cam ──
with col_res:
    # Output kelas
    if has_result:
        result = st.session_state.classify_result
        pred_class  = result["pred_class"]
        confidence  = result["confidence"]
        below_thr   = confidence < CONFIDENCE_THRESHOLD

        if below_thr:
            st.markdown(render_output_not_detected(), unsafe_allow_html=True)
        else:
            st.markdown(render_output_card(pred_class), unsafe_allow_html=True)
    else:
        st.markdown(render_placeholder_card("output kelas", "100px"), unsafe_allow_html=True)

    # Grad-CAM — label dan konten hanya tampil jika sudah ada hasil
    if has_result and has_image:
        st.markdown(render_img_label("grad-cam"), unsafe_allow_html=True)
        # Selectbox kelas target grad-cam (di sini agar nilainya langsung tersedia)
        default_cls = st.session_state.classify_result["pred_class"]
        default_idx = CLASS_NAMES.index(default_cls)
        gradcam_class = st.selectbox(
            "Kelas target:",
            CLASS_NAMES,
            index=default_idx,
            key="gradcam_select",
            label_visibility="collapsed",
        )

        with st.spinner("Menghitung aktivasi..."):
            overlay = compute_gradcam_overlay(
                st.session_state.loaded_model,
                st.session_state.pil_image,
                pred_index=CLASS_NAMES.index(gradcam_class),
            )

        if overlay is not None:
            st.image(overlay, width="stretch")
            st.caption(f"Fokus model → {gradcam_class}")
        else:
            st.caption("Grad-CAM tidak tersedia untuk arsitektur ini.")
    else:
        st.markdown(render_placeholder_card("grad-cam", "120px"), unsafe_allow_html=True)


# ============================================================
# TOMBOL AKSI
# ============================================================
st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

btn_col1, btn_col2, _ = st.columns([1.3, 1.3, 3])

with btn_col1:
    # File uploader: label kosong + label_visibility collapsed
    # CSS menjadikan area dropzone terlihat sebagai tombol "Pilih Gambar"
    uploaded_file = st.file_uploader(
        "Pilih gambar habitat bentik",
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
        label_visibility="collapsed",
        key="file_uploader",
    )

with btn_col2:
    classify_btn = st.button(
        "Klasifikasi →",
        type="primary",
        width="stretch",
        disabled=not has_image,
    )


# ============================================================
# PROSES WIDGET VALUES
# Dilakukan SETELAH layout agar layout tidak menunggu widget,
# dan st.rerun() menyebabkan layout di-refresh dengan state baru.
# ============================================================

# Gambar baru dipilih
if uploaded_file is not None:
    fingerprint = (uploaded_file.name, uploaded_file.size)
    if st.session_state.classify_fingerprint != fingerprint:
        # Gambar baru → reset hasil lama
        st.session_state.pil_image = Image.open(uploaded_file)
        st.session_state.classify_fingerprint = fingerprint
        st.session_state.classify_result = None
        st.rerun()
    elif st.session_state.pil_image is None:
        st.session_state.pil_image = Image.open(uploaded_file)
        st.rerun()

elif uploaded_file is None and st.session_state.pil_image is not None:
    # File dihapus dari uploader → reset state
    st.session_state.pil_image = None
    st.session_state.classify_result = None
    st.session_state.classify_fingerprint = None
    st.rerun()

# Klasifikasi dijalankan
if classify_btn and st.session_state.pil_image is not None:
    with st.spinner("Memproses..."):
        result = classify_image(
            st.session_state.loaded_model,
            st.session_state.pil_image,
        )
    st.session_state.classify_result = result
    st.rerun()


# ============================================================
# BLOK DETAIL — hanya muncul setelah ada hasil klasifikasi
# Berisi distribusi bar antar kelas TANPA angka persentase
# ============================================================
if has_result:
    probs = st.session_state.classify_result["probs"]
    with st.expander("▸  detail"):
        st.markdown(render_sonar_no_numbers(probs), unsafe_allow_html=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown(render_footer(), unsafe_allow_html=True)
