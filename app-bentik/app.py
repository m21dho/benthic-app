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
from hf_hub_utils import hf_download_model  # noqa: F401 (kept for potential future use)
from model_utils import classify_image, compute_gradcam_overlay, classify_patches, draw_patch_grid
from styles import (
    CSS,
    render_header,
    render_img_placeholder,
    render_placeholder_card,
    render_output_card,
    render_output_not_detected,
    render_img_label,
    render_sonar_no_numbers,
    render_detected_summary,
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
@st.cache_resource(show_spinner=False)
def get_model(token: str, model_repo: str, model_folder: str, model_filename: str):
    """
    Load model. Urutan prioritas:
    1. Cek path lokal di sebelah app.py (model ada di repo GitHub)
    2. Cek MODEL_FOLDER (sudah pernah didownload sebelumnya)
    3. Download dari HF Hub sebagai fallback terakhir
    Di-cache — hanya jalan sekali per sesi app.
    """
    import os

    # Matikan XetHub — protocol baru HF yang sering hang di Streamlit Cloud
    os.environ["HF_HUB_DISABLE_XET"] = "1"

    # Path 1: model di sebelah app.py (sudah ada di repo GitHub)
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    path_in_repo = os.path.join(script_dir, "models", model_filename)

    # Path 2: model di MODEL_FOLDER (hasil download sebelumnya)
    path_in_folder = os.path.join(model_folder, model_filename)

    # Tentukan path yang akan dipakai
    if os.path.exists(path_in_repo):
        local_path = path_in_repo
    elif os.path.exists(path_in_folder):
        local_path = path_in_folder
    else:
        # Download dari HF Hub via HTTPS langsung (bukan hf_hub_download)
        # hf_hub_download sering hang di Streamlit Cloud karena hf-xet protocol
        if not token or not model_repo:
            return None, "STEP_DOWNLOAD", \
                "Model tidak ditemukan lokal dan HF Hub tidak terkonfigurasi."
        try:
            import requests
            os.makedirs(model_folder, exist_ok=True)
            url = (f"https://huggingface.co/{model_repo}"
                   f"/resolve/main/{model_filename}?download=true")
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(url, headers=headers, stream=True, timeout=300)
            resp.raise_for_status()
            with open(path_in_folder, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
            local_path = path_in_folder
        except Exception as e:
            return None, "STEP_DOWNLOAD", f"Download gagal: {e}"

    # Load model — coba keras 3 dulu, lalu tf.keras sebagai fallback
    loaders = []
    try:
        import keras
        loaders.append(("keras 3", lambda: keras.models.load_model(local_path, compile=False)))
    except ImportError:
        pass
    try:
        from tensorflow.keras.models import load_model as tf_load
        loaders.append(("tf.keras compile=False", lambda: tf_load(local_path, compile=False)))
        loaders.append(("tf.keras default",        lambda: tf_load(local_path)))
    except ImportError:
        pass

    errors = []
    for label, fn in loaders:
        try:
            model = fn()
            return model, "STEP_LOAD", f"OK via {label} — {local_path}"
        except Exception as e:
            errors.append(f"{label}: {e}")

    return None, "STEP_LOAD", "Semua metode load gagal:\n" + "\n".join(errors)


hf_cfg    = get_hf_config()
token_val = hf_cfg["token"]      if hf_cfg else ""
repo_val  = hf_cfg["model_repo"] if hf_cfg else ""

if not st.session_state.model_loaded:
    with st.status("Menyiapkan model klasifikasi...", expanded=True) as load_status:
        st.write("🔍 **Step 1/2** — Mencari & mengunduh model...")
        st.write("_(Download langsung via HTTPS — estimasi 1–3 menit tergantung ukuran model)_")

        model, step, status_msg = get_model(
            token_val, repo_val, MODEL_FOLDER, MODEL_FILENAME
        )

        if model is not None:
            st.write("✅ File model ditemukan & berhasil dimuat")
            st.write("🧠 **Step 2/2** — Model siap digunakan")
            load_status.update(label="✅ Model siap!", state="complete", expanded=False)
            st.session_state.loaded_model = model
            st.session_state.model_loaded = True
            st.session_state.model_debug  = status_msg
        else:
            fail_step = "download" if step == "STEP_DOWNLOAD" else "load model"
            load_status.update(
                label=f"❌ Gagal saat {fail_step}",
                state="error", expanded=True,
            )
            st.error(f"**Detail error:** {status_msg}")
            st.session_state.model_debug = status_msg

if not st.session_state.model_loaded:
    st.error("Model belum berhasil dimuat.")
    with st.expander("Detail error (untuk debugging)"):
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

col_img, col_res = st.columns([12, 10], gap="small")

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
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

btn_col1, btn_col2 = st.columns(2)

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
if st.session_state.classify_fingerprint is not None:
    fname, fsize_bytes = st.session_state.classify_fingerprint
    fsize_str = f"{fsize_bytes/1024:.1f} KB"
    st.markdown(
        f'<p style="font-family:\'Space Mono\',monospace!important;'
        f'font-size:0.65rem;color:#2D5E52!important;margin:0.35rem 0 0;'
        f'letter-spacing:0.04em;">✓ {fname} &nbsp;·&nbsp; {fsize_str}</p>',
        unsafe_allow_html=True,
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
# MULTI-OBJECT DETECTION — patch-based
# Hanya tampil jika sudah ada gambar & hasil klasifikasi
# ============================================================
if has_image and has_result:
    st.markdown("---")
    st.markdown(
        '<p style="font-family:\'Space Mono\',monospace!important;font-size:0.7rem;'
        'letter-spacing:0.12em;text-transform:uppercase;color:#0E8B70!important;'
        'margin:0 0 0.7rem;">▸ multi-objek // patch_analysis</p>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Model yang sama dijalankan pada setiap area foto secara terpisah "
        "untuk mendeteksi beberapa jenis habitat dalam satu gambar."
    )

    grid_choice = st.radio(
        "Jumlah patch:",
        ["2×2  (4 area)", "3×3  (9 area)"],
        horizontal=True,
        label_visibility="visible",
    )
    grid = (2, 2) if grid_choice.startswith("2") else (3, 3)

    if st.button("🔍 Jalankan Deteksi Multi-Objek", type="primary", width="stretch"):
        with st.spinner("Menganalisis setiap area gambar..."):
            patch_result = classify_patches(
                st.session_state.loaded_model,
                st.session_state.pil_image,
                grid=grid,
                threshold=CONFIDENCE_THRESHOLD,
            )
            annotated = draw_patch_grid(
                st.session_state.pil_image,
                patch_result["patches"],
                grid,
            )
        st.session_state["patch_result"]  = patch_result
        st.session_state["patch_annotated"] = annotated
        st.session_state["patch_grid"] = grid

    if "patch_result" in st.session_state:
        pr  = st.session_state["patch_result"]
        ann = st.session_state["patch_annotated"]
        pg  = st.session_state.get("patch_grid", (2, 2))

        # Gambar anotasi
        ma1, ma2 = st.columns([1, 1])
        with ma1:
            st.markdown(render_img_label("original"), unsafe_allow_html=True)
            st.image(st.session_state.pil_image, width="stretch")
        with ma2:
            st.markdown(render_img_label(f"patch {pg[0]}×{pg[1]}"), unsafe_allow_html=True)
            st.image(ann, width="stretch")

        # Ringkasan kelas yang terdeteksi
        st.markdown(
            render_detected_summary(
                pr["detected_classes"],
                pr["total_ms"],
                pr["grid"],
            ),
            unsafe_allow_html=True,
        )

        # Detail tiap patch
        with st.expander("▸  detail tiap patch"):
            rows, cols = pr["grid"]
            for r in range(rows):
                patch_cols = st.columns(cols)
                for c in range(cols):
                    idx = r * cols + c
                    p   = pr["patches"][idx]
                    with patch_cols[c]:
                        st.image(p["patch_img"], width="stretch")
                        cls   = p["pred_class"]
                        conf  = p["confidence"]
                        hit   = p["detected"]
                        color = "#18C99A" if hit else "#4A6470"
                        st.markdown(
                            f'<p style="font-family:\'Space Mono\',monospace!important;'
                            f'font-size:0.62rem;color:{color}!important;'
                            f'margin:0.2rem 0 0;text-align:center;">'
                            f'{"✓" if hit else "○"} {cls}<br>{conf*100:.0f}%</p>',
                            unsafe_allow_html=True,
                        )


# ============================================================
# FOOTER
# ============================================================
st.markdown(render_footer(), unsafe_allow_html=True)
