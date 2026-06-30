"""
app.py — Lapisan UI Streamlit.
Murni klasifikasi. Semua hasil ditampilkan via HTML kustom (styles.py),
tidak ada chart Altair atau dataframe generik untuk confidence.
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
    render_section,
    render_result_card,
    render_not_detected_card,
    render_sonar_readout,
    render_img_label,
    render_gradcam_header,
    render_footer,
)

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


# ============================================================
# PAGE CONFIG & CSS
# ============================================================
st.set_page_config(
    page_title="Habitat Bentik",
    page_icon="🌊",
    layout="centered",
)
st.markdown(CSS, unsafe_allow_html=True)

# Header
st.markdown(render_header(), unsafe_allow_html=True)


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
        debug_lines.append(f"Mencari di HF Hub repo: {hf_cfg['model_repo']}")
        with st.spinner("Mengunduh model dari Hugging Face Hub..."):
            downloaded, dl_error = hf_download_model(hf_cfg, local_dir=MODEL_FOLDER)
            if downloaded:
                model_path = os.path.join(MODEL_FOLDER, MODEL_FILENAME)
                debug_lines.append("Download berhasil")
            else:
                debug_lines.append(f"Download gagal: {dl_error}")
    elif not hf_available:
        debug_lines.append("HF Hub tidak terkonfigurasi — mencoba path lokal.")

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
    st.error("Model belum berhasil dimuat.")
    with st.expander("Detail error"):
        st.code(st.session_state.model_debug or "(tidak ada info)")
    st.stop()


# ============================================================
# UPLOAD GAMBAR
# ============================================================
st.markdown(render_section("▸ input // upload_citra"), unsafe_allow_html=True)

uploaded_image = st.file_uploader(
    "Seret foto bawah air ke sini, atau klik untuk memilih",
    type=["jpg", "jpeg", "png", "bmp", "tiff"],
    label_visibility="visible",
    key="classify_uploader",
)

if uploaded_image is None:
    st.markdown(
        '<p style="font-family:\'Space Mono\',monospace!important;font-size:0.72rem;'
        'color:#2D5E52!important;text-align:center;padding:0.5rem 0;">'
        'JPG · PNG · BMP · TIFF</p>',
        unsafe_allow_html=True,
    )
    st.markdown(render_footer(), unsafe_allow_html=True)
    st.stop()


# ============================================================
# GAMBAR TERUPLOAD
# ============================================================
pil_image = Image.open(uploaded_image)

col1, col2 = st.columns([3, 2])

with col1:
    st.markdown(render_img_label("preview"), unsafe_allow_html=True)
    st.image(pil_image, width="stretch")

with col2:
    st.markdown(render_img_label("metadata"), unsafe_allow_html=True)
    st.markdown(
        f'<div class="bk-meta">'
        f'<div class="bk-meta-row"><span>Lebar</span><span>{pil_image.width} px</span></div>'
        f'<div class="bk-meta-row"><span>Tinggi</span><span>{pil_image.height} px</span></div>'
        f'<div class="bk-meta-row"><span>Ukuran</span><span>{uploaded_image.size/1024:.1f} KB</span></div>'
        f'<div class="bk-meta-row"><span>Format</span><span>{pil_image.format or "—"}</span></div>'
        f'<div class="bk-meta-row"><span>Mode</span><span>{pil_image.mode}</span></div>'
        f'</div>'
        f'<style>'
        f'.bk-meta{{background:rgba(5,17,26,0.85);border:1px solid rgba(14,139,112,0.18);'
        f'border-radius:12px;padding:0.9rem 1rem;font-family:"Space Mono",monospace!important;}}'
        f'.bk-meta-row{{display:flex;justify-content:space-between;align-items:center;'
        f'padding:0.35rem 0;border-top:1px solid rgba(255,255,255,0.04);font-size:0.72rem;}}'
        f'.bk-meta-row:first-child{{border-top:none;}}'
        f'.bk-meta-row span:first-child{{color:#7AB8A8!important;}}'
        f'.bk-meta-row span:last-child{{color:#C7F2E8!important;font-weight:700;}}'
        f'</style>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

# Reset hasil lama kalau gambar berganti
fingerprint = (uploaded_image.name, uploaded_image.size)
if st.session_state.get("classify_fingerprint") != fingerprint:
    st.session_state.pop("classify_result", None)
    st.session_state["classify_fingerprint"] = fingerprint
    st.session_state["classify_image"] = pil_image

if st.button("Jalankan klasifikasi →", width="stretch", type="primary"):
    try:
        with st.spinner("Memproses..."):
            result = classify_image(st.session_state.loaded_model, pil_image)
        st.session_state["classify_result"] = result
        st.session_state["classify_image"] = pil_image
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# HASIL KLASIFIKASI
# ============================================================
if "classify_result" not in st.session_state:
    st.markdown(render_footer(), unsafe_allow_html=True)
    st.stop()

result = st.session_state["classify_result"]
pred_class = result["pred_class"]
confidence = result["confidence"]
probs = result["probs"]
below_threshold = confidence < CONFIDENCE_THRESHOLD

st.markdown(render_section("▸ output // hasil_klasifikasi"), unsafe_allow_html=True)

if below_threshold:
    st.markdown(render_not_detected_card(confidence), unsafe_allow_html=True)
else:
    st.markdown(render_result_card(pred_class, confidence), unsafe_allow_html=True)

# Sonar readout — semua kelas
st.markdown(render_section("▸ scan // confidence_matrix"), unsafe_allow_html=True)
st.markdown(render_sonar_readout(probs), unsafe_allow_html=True)


# ============================================================
# GRAD-CAM
# ============================================================
st.markdown(render_section("▸ visual // grad_cam"), unsafe_allow_html=True)
st.markdown(render_gradcam_header(), unsafe_allow_html=True)

gradcam_class = st.selectbox(
    "Kelas target:",
    CLASS_NAMES,
    index=CLASS_NAMES.index(pred_class),
    key="gradcam_class_select",
)
target_idx = CLASS_NAMES.index(gradcam_class)
cam_image = st.session_state.get("classify_image", pil_image)

with st.spinner("Menghitung aktivasi..."):
    overlay_img = compute_gradcam_overlay(
        st.session_state.loaded_model, cam_image, pred_index=target_idx
    )

if overlay_img is not None:
    gc1, gc2 = st.columns(2)
    with gc1:
        st.markdown(render_img_label("original"), unsafe_allow_html=True)
        st.image(cam_image.convert("RGB").resize((IMG_SIZE, IMG_SIZE)), width="stretch")
    with gc2:
        st.markdown(render_img_label(f"fokus → {gradcam_class}"), unsafe_allow_html=True)
        st.image(overlay_img, width="stretch")
else:
    st.caption("Grad-CAM tidak tersedia untuk arsitektur model ini.")

st.markdown(render_footer(), unsafe_allow_html=True)
