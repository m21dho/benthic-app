import streamlit as st
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import numpy as np
from PIL import Image
import os
import io
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# ============================================================
# KONFIGURASI UTAMA
# ============================================================
NUM_CLASSES = 5
CLASS_NAMES = ["Alga", "Karang", "Lainnya", "Lamun", "Pasir"]
# Urutan HARUS sama dengan sorted(os.listdir(TRAIN_DIR)) saat training:
#   alga, karang, lainnya, lamun, pasir (alfabetis)

IMG_SIZE = 224
CONFIDENCE_THRESHOLD = 0.7
MIN_IMAGES_PER_CLASS = 25  # Batas minimum citra per kelas untuk retrain

# Path lokal (fallback jika HF Hub tidak dikonfigurasi)
MODEL_FOLDER = os.environ.get("MODEL_FOLDER", "models")
MODEL_FILENAME = "mobilenetv2_bentik_streamlit_fixed.keras"

# Hugging Face Hub — baca dari st.secrets atau environment variable
# Cara set di Streamlit Cloud: Settings → Secrets →
#   HF_TOKEN = "hf_xxxxx"
#   HF_MODEL_REPO = "username/bentik-model"
#   HF_DATASET_REPO = "username/bentik-dataset"
def get_hf_config():
    """Ambil konfigurasi HF Hub dari secrets/env, return dict atau None."""
    token = st.secrets.get("HF_TOKEN", os.environ.get("HF_TOKEN", ""))
    model_repo = st.secrets.get("HF_MODEL_REPO", os.environ.get("HF_MODEL_REPO", ""))
    dataset_repo = st.secrets.get("HF_DATASET_REPO", os.environ.get("HF_DATASET_REPO", ""))
    if token and model_repo and dataset_repo:
        return {"token": token, "model_repo": model_repo, "dataset_repo": dataset_repo}
    return None


# ============================================================
# HUGGING FACE HUB HELPERS
# ============================================================
def hf_ensure_repos(hf_cfg):
    """Pastikan repo model & dataset sudah ada di HF Hub; buat jika belum."""
    from huggingface_hub import HfApi
    api = HfApi(token=hf_cfg["token"])
    for repo_id, repo_type in [(hf_cfg["model_repo"], "model"),
                                (hf_cfg["dataset_repo"], "dataset")]:
        try:
            api.repo_info(repo_id=repo_id, repo_type=repo_type)
        except Exception:
            api.create_repo(repo_id=repo_id, repo_type=repo_type, private=True)


def hf_download_model(hf_cfg, local_dir="models"):
    """Download model .keras dari HF Hub ke folder lokal."""
    from huggingface_hub import hf_hub_download
    os.makedirs(local_dir, exist_ok=True)
    try:
        path = hf_hub_download(
            repo_id=hf_cfg["model_repo"],
            filename=MODEL_FILENAME,
            token=hf_cfg["token"],
            local_dir=local_dir,
        )
        return path
    except Exception:
        return None


def hf_upload_model(hf_cfg, local_path):
    """Upload model .keras ke HF Hub."""
    from huggingface_hub import HfApi
    api = HfApi(token=hf_cfg["token"])
    # Backup: simpan dengan timestamp
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    api.upload_file(
        path_or_fileobj=local_path,
        path_in_repo=f"backups/{ts}_{MODEL_FILENAME}",
        repo_id=hf_cfg["model_repo"],
        repo_type="model",
    )
    # Upload sebagai model utama
    api.upload_file(
        path_or_fileobj=local_path,
        path_in_repo=MODEL_FILENAME,
        repo_id=hf_cfg["model_repo"],
        repo_type="model",
    )


def hf_upload_images(hf_cfg, class_name, image_bytes_list):
    """Upload list of (filename, bytes) ke HF dataset repo di folder class_name/."""
    from huggingface_hub import HfApi
    api = HfApi(token=hf_cfg["token"])
    class_folder = class_name.lower()
    uploaded = 0
    for fname, fbytes in image_bytes_list:
        try:
            api.upload_file(
                path_or_fileobj=fbytes,
                path_in_repo=f"{class_folder}/{fname}",
                repo_id=hf_cfg["dataset_repo"],
                repo_type="dataset",
            )
            uploaded += 1
        except Exception:
            pass
    return uploaded


def hf_get_image_counts(hf_cfg):
    """Hitung jumlah citra per kelas di HF dataset repo."""
    from huggingface_hub import HfApi
    api = HfApi(token=hf_cfg["token"])
    counts = {name: 0 for name in CLASS_NAMES}
    try:
        files = api.list_repo_files(
            repo_id=hf_cfg["dataset_repo"], repo_type="dataset"
        )
        img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
        for f in files:
            parts = f.split("/")
            if len(parts) >= 2:
                folder = parts[0]
                ext = os.path.splitext(parts[-1])[1].lower()
                if ext in img_exts:
                    # Cocokkan folder name ke CLASS_NAMES (case-insensitive)
                    for cn in CLASS_NAMES:
                        if folder.lower() == cn.lower():
                            counts[cn] += 1
                            break
    except Exception:
        pass
    return counts


def hf_download_dataset(hf_cfg, local_dir):
    """Download seluruh dataset repo ke folder lokal."""
    from huggingface_hub import snapshot_download
    path = snapshot_download(
        repo_id=hf_cfg["dataset_repo"],
        repo_type="dataset",
        token=hf_cfg["token"],
        local_dir=local_dir,
    )
    return path


# ============================================================
# MODEL LOADING
# ============================================================
def load_model_custom_loader(model_path):
    """Load model dengan berbagai metode untuk handle kompatibilitas."""
    from tensorflow.keras.models import load_model as tf_load_model
    methods = [
        {"label": "Direct load", "kwargs": {}},
        {"label": "safe_mode=False", "kwargs": {"safe_mode": False}},
        {"label": "compile=False", "kwargs": {"compile": False}},
        {"label": "safe_mode=False + compile=False",
         "kwargs": {"safe_mode": False, "compile": False}},
    ]
    for m in methods:
        try:
            return tf_load_model(model_path, **m["kwargs"])
        except Exception:
            continue
    return None


@st.cache_resource
def load_model_cached(model_path):
    """Load & cache model. Return (model, status_msg)."""
    if not os.path.exists(model_path):
        return None, f"File model tidak ditemukan: {model_path}"
    model = load_model_custom_loader(model_path)
    if model is not None:
        return model, "Model berhasil dimuat"
    return None, "Semua metode load gagal — model mungkin tidak compatible"


# ============================================================
# FINE-TUNING (dijalankan di CPU Streamlit Cloud)
# ============================================================
def prepare_dataset_from_dir(data_dir, validation_split=0.2):
    """
    Baca citra dari data_dir/<kelas>/*.jpg dan buat tf.data.Dataset
    untuk train & validation.
    """
    images, labels = [], []
    img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

    for idx, class_name in enumerate(CLASS_NAMES):
        class_dir = os.path.join(data_dir, class_name.lower())
        if not os.path.isdir(class_dir):
            continue
        for fname in os.listdir(class_dir):
            if os.path.splitext(fname)[1].lower() not in img_exts:
                continue
            fpath = os.path.join(class_dir, fname)
            try:
                img = Image.open(fpath).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
                arr = np.array(img, dtype=np.float32)
                arr = preprocess_input(arr)
                images.append(arr)
                labels.append(idx)
            except Exception:
                continue

    if len(images) == 0:
        return None, None, 0

    images = np.array(images, dtype=np.float32)
    labels = np.array(labels, dtype=np.int32)
    total = len(images)

    # Shuffle
    idx_perm = np.random.permutation(total)
    images, labels = images[idx_perm], labels[idx_perm]

    # Split
    val_count = max(1, int(total * validation_split))
    train_imgs, val_imgs = images[val_count:], images[:val_count]
    train_lbls, val_lbls = labels[val_count:], labels[:val_count]

    batch_size = min(16, len(train_imgs))

    train_ds = tf.data.Dataset.from_tensor_slices((train_imgs, train_lbls))
    train_ds = train_ds.shuffle(512).batch(batch_size).prefetch(tf.data.AUTOTUNE)

    val_ds = tf.data.Dataset.from_tensor_slices((val_imgs, val_lbls))
    val_ds = val_ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)

    return train_ds, val_ds, total


def finetune_model(base_model, train_ds, val_ds, epochs=5, lr=1e-5):
    """
    Fine-tune: freeze backbone, hanya latih classification head.
    Return (finetuned_model, history_dict).
    """
    import copy

    # Clone model weights ke model baru agar tidak merusak model produksi
    model = tf.keras.models.clone_model(base_model)
    model.set_weights(base_model.get_weights())

    # Freeze semua layer kecuali classification head (Dense, Dropout, BatchNorm terakhir)
    # Strategi: freeze semua layer yang namanya mengandung 'mobilenetv2' atau 'Conv'
    trainable_count = 0
    for layer in model.layers:
        if any(kw in layer.name.lower() for kw in ["mobilenetv2", "conv", "bn", "block"]):
            layer.trainable = False
        else:
            layer.trainable = True
            trainable_count += 1

    # Jika tidak ada layer yang trainable (misal nama layer berbeda), unfreeze 10 layer terakhir
    if trainable_count == 0:
        for layer in model.layers[-10:]:
            layer.trainable = True

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=lr, clipnorm=1.0),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        verbose=0,
    )

    return model, history.history


# ============================================================
# PAGE CONFIG & CSS
# ============================================================
st.set_page_config(
    page_title="Klasifikasi Habitat Bentik",
    page_icon="🌊",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main { padding-top: 0rem; }
h1 { color: #1f77b4; text-align: center; }
.status-good { color: #28a745; font-weight: bold; }
.status-bad  { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🌊 Klasifikasi Habitat Bentik")
st.markdown("---")

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.header("⚙️ Konfigurasi")

hf_cfg = get_hf_config()
hf_available = hf_cfg is not None

# Info HF Hub
st.sidebar.subheader("☁️ Hugging Face Hub")
if hf_available:
    st.sidebar.success("✅ HF Hub terkonfigurasi")
else:
    st.sidebar.warning(
        "⚠️ HF Hub belum dikonfigurasi.\n\n"
        "Tambahkan di **Settings → Secrets**:\n"
        "```\n"
        'HF_TOKEN = "hf_xxxxx"\n'
        'HF_MODEL_REPO = "user/bentik-model"\n'
        'HF_DATASET_REPO = "user/bentik-dataset"\n'
        "```"
    )

# Info kelas
st.sidebar.subheader("📋 Kelas Model")
class_list = "\n".join([f"{i+1}. {c}" for i, c in enumerate(CLASS_NAMES)])
st.sidebar.info(
    f"**Jumlah Kelas:** {NUM_CLASSES}\n\n"
    f"**Nama Kelas:**\n{class_list}\n\n"
    f"**Ukuran Input:** {IMG_SIZE}×{IMG_SIZE}px\n"
    f"**Confidence Threshold:** {CONFIDENCE_THRESHOLD*100:.0f}%"
)

st.sidebar.markdown("---")
st.sidebar.info(
    "📝 **Petunjuk:**\n\n"
    "**Tab Klasifikasi** — upload gambar, lihat prediksi.\n\n"
    "**Tab Kelola Dataset** — upload citra training per kelas "
    f"(min. {MIN_IMAGES_PER_CLASS}/kelas), lalu latih ulang model."
)

# ============================================================
# LOAD MODEL (dari HF Hub atau lokal)
# ============================================================
if 'loaded_model' not in st.session_state:
    st.session_state.loaded_model = None
    st.session_state.model_loaded = False
    st.session_state.model_path = None

# Coba load model
model_path = os.path.join(MODEL_FOLDER, MODEL_FILENAME)

# Prioritas: HF Hub → lokal
if not st.session_state.model_loaded:
    # 1) Coba dari HF Hub
    if hf_available and not os.path.exists(model_path):
        with st.spinner("⏳ Mengunduh model dari Hugging Face Hub..."):
            downloaded = hf_download_model(hf_cfg, local_dir=MODEL_FOLDER)
            if downloaded:
                model_path = os.path.join(MODEL_FOLDER, MODEL_FILENAME)

    # 2) Load model
    if os.path.exists(model_path):
        model, status = load_model_cached(model_path)
        if model is not None:
            st.session_state.loaded_model = model
            st.session_state.model_loaded = True
            st.session_state.model_path = model_path

# Sidebar model status
st.sidebar.subheader("📊 Status Model")
if st.session_state.model_loaded:
    st.sidebar.success(f"✅ Model aktif\n📁 {MODEL_FILENAME}")
else:
    st.sidebar.error("❌ Model belum dimuat")


# ============================================================
# MAIN CONTENT — TABS
# ============================================================
tab_klasifikasi, tab_dataset = st.tabs(["🔬 Klasifikasi", "📂 Kelola Dataset & Training"])

# ────────────────────────────────────────────────────────────
# TAB 1: KLASIFIKASI (fungsi asli, sudah diupdate ke 5 kelas)
# ────────────────────────────────────────────────────────────
with tab_klasifikasi:
    st.markdown("### 📤 Upload Gambar Habitat Bentik")

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
            st.subheader("📸 Gambar Input")
            st.image(pil_image, use_container_width=True)

        with col2:
            st.subheader("🔍 Informasi Gambar")
            st.info(
                f"**Dimensi Asli:** {pil_image.width} × {pil_image.height} px\n\n"
                f"**Ukuran File:** {uploaded_image.size / 1024:.2f} KB"
            )

        if st.button("🚀 Jalankan Klasifikasi", use_container_width=True):
            try:
                with st.spinner("⏳ Memproses gambar..."):
                    img_rgb = pil_image.convert("RGB").resize((IMG_SIZE, IMG_SIZE))
                    img_array = preprocess_input(np.array(img_rgb, dtype=np.float32))
                    img_input = np.expand_dims(img_array, axis=0)

                    predictions = st.session_state.loaded_model.predict(img_input, verbose=0)
                    pred_confidence = float(np.max(predictions))
                    pred_class_idx = int(np.argmax(predictions))
                    pred_class = CLASS_NAMES[pred_class_idx]

                st.markdown("---")
                st.subheader("📊 Hasil Klasifikasi")

                c1, c2 = st.columns(2)
                with c1:
                    st.metric("🎯 Prediksi", pred_class, delta="Habitat Bentik")
                with c2:
                    st.metric("📈 Confidence", f"{pred_confidence:.2%}")

                if pred_confidence < CONFIDENCE_THRESHOLD:
                    st.warning(
                        f"⚠️ Confidence ({pred_confidence:.2%}) di bawah threshold "
                        f"({CONFIDENCE_THRESHOLD:.2%}). Hasil mungkin kurang akurat."
                    )

                st.subheader("📋 Persentase Semua Kelas")
                import pandas as pd

                pred_dict = {
                    CLASS_NAMES[i]: float(predictions[0][i]) * 100
                    for i in range(NUM_CLASSES)
                }
                sorted_pred = dict(sorted(pred_dict.items(), key=lambda x: x[1], reverse=True))
                st.bar_chart(sorted_pred)

                df = pd.DataFrame(
                    [(k, f"{v:.2f}%") for k, v in sorted_pred.items()],
                    columns=["Kelas", "Confidence (%)"],
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.success("✅ Klasifikasi selesai!")

            except Exception as e:
                st.error(f"❌ Error: {e}")

    elif uploaded_image is not None and not st.session_state.model_loaded:
        st.warning("⚠️ Model belum dimuat. Periksa konfigurasi model / HF Hub.")
    else:
        if st.session_state.model_loaded:
            st.info("📤 Silakan upload gambar untuk diklasifikasi...")
        else:
            st.error("❌ Model gagal dimuat. Periksa konfigurasi.")


# ────────────────────────────────────────────────────────────
# TAB 2: KELOLA DATASET & TRAINING
# ────────────────────────────────────────────────────────────
with tab_dataset:
    st.markdown("### 📂 Kelola Dataset & Latih Ulang Model")

    if not hf_available:
        st.error(
            "☁️ **Hugging Face Hub belum dikonfigurasi.**\n\n"
            "Fitur upload dataset & retrain memerlukan HF Hub untuk menyimpan "
            "citra dan model secara permanen (Streamlit Cloud storage bersifat sementara).\n\n"
            "**Langkah setup:**\n"
            "1. Buat akun gratis di [huggingface.co](https://huggingface.co)\n"
            "2. Buat **Access Token** (write) di Settings → Access Tokens\n"
            "3. Buat 2 repo: satu bertipe **Model**, satu bertipe **Dataset**\n"
            "4. Di Streamlit Cloud → Settings → Secrets, tambahkan:\n"
            "```toml\n"
            'HF_TOKEN = "hf_xxxxx"\n'
            'HF_MODEL_REPO = "username/bentik-model"\n'
            'HF_DATASET_REPO = "username/bentik-dataset"\n'
            "```\n"
            "5. Restart app — fitur ini akan aktif."
        )
    else:
        # Pastikan repo ada
        try:
            hf_ensure_repos(hf_cfg)
        except Exception as e:
            st.error(f"Gagal menyiapkan repo HF Hub: {e}")

        # ── Status dataset saat ini ──
        st.subheader("📊 Status Dataset di Hugging Face Hub")

        if st.button("🔄 Refresh Hitungan", key="refresh_counts"):
            st.cache_data.clear()

        @st.cache_data(ttl=60, show_spinner=False)
        def cached_counts(_token, _repo):
            return hf_get_image_counts(hf_cfg)

        with st.spinner("Menghitung citra di HF Hub..."):
            counts = cached_counts(hf_cfg["token"], hf_cfg["dataset_repo"])

        # Tampilkan tabel status
        import pandas as pd
        status_rows = []
        all_ready = True
        for cn in CLASS_NAMES:
            n = counts.get(cn, 0)
            ok = n >= MIN_IMAGES_PER_CLASS
            if not ok:
                all_ready = False
            status_rows.append({
                "Kelas": cn,
                "Jumlah Citra": n,
                "Minimum": MIN_IMAGES_PER_CLASS,
                "Status": "✅ Siap" if ok else f"❌ Kurang {MIN_IMAGES_PER_CLASS - n}",
            })

        df_status = pd.DataFrame(status_rows)
        st.dataframe(df_status, use_container_width=True, hide_index=True)

        if all_ready:
            st.success(
                f"✅ Semua kelas memenuhi minimum {MIN_IMAGES_PER_CLASS} citra. "
                "Anda bisa melatih ulang model."
            )
        else:
            st.warning(
                f"⚠️ Beberapa kelas belum memenuhi minimum {MIN_IMAGES_PER_CLASS} citra. "
                "Upload citra lagi sebelum melatih ulang."
            )

        st.markdown("---")

        # ── Upload Citra ──
        st.subheader("📤 Upload Citra Baru ke Dataset")

        selected_class = st.selectbox(
            "Pilih kelas tujuan:",
            CLASS_NAMES,
            help="Citra yang di-upload akan masuk ke kelas ini.",
        )

        uploaded_files = st.file_uploader(
            f"Upload citra untuk kelas **{selected_class}**",
            type=["jpg", "jpeg", "png", "bmp", "tiff"],
            accept_multiple_files=True,
            help=f"Upload minimal {MIN_IMAGES_PER_CLASS} citra per kelas. "
                 "Anda bisa upload berkali-kali — citra akan terakumulasi di HF Hub.",
            key="dataset_uploader",
        )

        if uploaded_files:
            st.info(f"📎 {len(uploaded_files)} file dipilih untuk kelas **{selected_class}**")

            # Preview (maks 8 gambar)
            preview_count = min(8, len(uploaded_files))
            cols = st.columns(min(4, preview_count))
            for i in range(preview_count):
                with cols[i % len(cols)]:
                    img = Image.open(uploaded_files[i])
                    st.image(img, caption=uploaded_files[i].name, use_container_width=True)

            if len(uploaded_files) > preview_count:
                st.caption(f"... dan {len(uploaded_files) - preview_count} citra lainnya")

            if st.button("⬆️ Upload ke Hugging Face Hub", use_container_width=True, type="primary"):
                image_data = []
                skipped = 0
                for f in uploaded_files:
                    try:
                        # Validasi: bisa dibuka sebagai gambar?
                        img = Image.open(f)
                        img.verify()
                        f.seek(0)
                        image_data.append((f.name, f.read()))
                        f.seek(0)
                    except Exception:
                        skipped += 1

                if image_data:
                    with st.spinner(f"⬆️ Mengupload {len(image_data)} citra ke HF Hub..."):
                        uploaded_count = hf_upload_images(hf_cfg, selected_class, image_data)

                    st.success(f"✅ Berhasil upload {uploaded_count} citra ke kelas **{selected_class}**")
                    if skipped > 0:
                        st.warning(f"⚠️ {skipped} file dilewati (bukan gambar valid)")

                    # Clear cache agar hitungan ter-update
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Tidak ada file gambar valid yang bisa di-upload.")

        st.markdown("---")

        # ── Latih Ulang Model ──
        st.subheader("🧠 Latih Ulang Model (Fine-Tuning)")

        st.info(
            "**Cara kerja:**\n"
            "1. Semua citra di HF Dataset di-download ke memori sementara\n"
            "2. Model saat ini di-fine-tune (backbone dibekukan, hanya head dilatih)\n"
            "3. Akurasi validasi dicek — model baru **hanya menggantikan model lama "
            "jika akurasinya tidak lebih buruk**\n"
            "4. Model lama otomatis di-backup di HF Hub (bisa rollback)\n"
            "5. Learning rate kecil (1e-5), 5 epoch — cocok untuk CPU"
        )

        # Hyperparameters (opsional, expandable)
        with st.expander("⚙️ Pengaturan Fine-Tuning (opsional)"):
            ft_epochs = st.slider("Jumlah epoch", 2, 15, 5)
            ft_lr = st.select_slider(
                "Learning rate",
                options=[1e-6, 5e-6, 1e-5, 5e-5, 1e-4],
                value=1e-5,
                format_func=lambda x: f"{x:.0e}",
            )
            ft_val_split = st.slider("Validasi split (%)", 10, 30, 20) / 100

        # Tombol latih ulang
        can_train = all_ready and st.session_state.model_loaded
        train_disabled = not can_train
        if not st.session_state.model_loaded:
            st.warning("⚠️ Model belum dimuat — tidak bisa fine-tune.")
        if not all_ready:
            st.warning(
                f"⚠️ Belum semua kelas memenuhi minimum {MIN_IMAGES_PER_CLASS} citra."
            )

        if st.button(
            "🚀 Mulai Latih Ulang Model",
            use_container_width=True,
            type="primary",
            disabled=train_disabled,
        ):
            status_container = st.status("🔄 Proses fine-tuning...", expanded=True)

            with status_container:
                try:
                    # Step 1: Download dataset
                    st.write("📥 Mengunduh dataset dari HF Hub...")
                    tmp_dir = tempfile.mkdtemp(prefix="bentik_ds_")
                    hf_download_dataset(hf_cfg, tmp_dir)
                    st.write("✅ Dataset berhasil di-download")

                    # Step 2: Persiapan data
                    st.write("🔄 Mempersiapkan data training & validasi...")
                    train_ds, val_ds, total_imgs = prepare_dataset_from_dir(
                        tmp_dir, validation_split=ft_val_split
                    )
                    if train_ds is None:
                        st.error("❌ Tidak ada citra valid ditemukan di dataset.")
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                        st.stop()

                    st.write(f"✅ Total {total_imgs} citra — "
                             f"train: {int(total_imgs*(1-ft_val_split))}, "
                             f"val: {int(total_imgs*ft_val_split)}")

                    # Step 3: Evaluasi model lama pada val set
                    st.write("📊 Mengevaluasi model lama pada data validasi...")
                    old_model = st.session_state.loaded_model
                    old_loss, old_acc = old_model.evaluate(val_ds, verbose=0)
                    st.write(f"   Model lama — Val Accuracy: **{old_acc*100:.2f}%**")

                    # Step 4: Fine-tuning
                    st.write(f"🧠 Melatih model baru ({ft_epochs} epoch, lr={ft_lr:.0e})...")
                    new_model, history = finetune_model(
                        old_model, train_ds, val_ds,
                        epochs=ft_epochs, lr=ft_lr,
                    )

                    new_acc = history["val_accuracy"][-1]
                    st.write(f"   Model baru — Val Accuracy: **{new_acc*100:.2f}%**")

                    # Step 5: Bandingkan & keputusan
                    st.write("⚖️ Membandingkan model lama vs baru...")
                    improvement = new_acc - old_acc

                    if new_acc >= old_acc - 0.02:
                        # Model baru diterima (tidak boleh turun lebih dari 2%)
                        st.write(f"✅ Model baru diterima (Δ = {improvement*100:+.2f}%)")

                        # Simpan model baru
                        st.write("💾 Menyimpan model baru...")
                        os.makedirs(MODEL_FOLDER, exist_ok=True)
                        new_model_path = os.path.join(MODEL_FOLDER, MODEL_FILENAME)
                        new_model.save(new_model_path)

                        # Upload ke HF Hub
                        st.write("☁️ Mengupload model baru ke HF Hub (+ backup model lama)...")
                        hf_upload_model(hf_cfg, new_model_path)
                        st.write("✅ Upload selesai!")

                        # Update session state
                        st.cache_resource.clear()
                        st.session_state.loaded_model = new_model
                        st.session_state.model_loaded = True
                        st.session_state.model_path = new_model_path

                        status_container.update(
                            label="✅ Fine-tuning selesai — model baru aktif!",
                            state="complete",
                        )
                    else:
                        st.write(
                            f"❌ Model baru DITOLAK — akurasi turun {abs(improvement)*100:.2f}% "
                            f"(melebihi toleransi 2%). Model lama tetap dipakai."
                        )
                        status_container.update(
                            label="⚠️ Model baru ditolak — model lama tetap aktif",
                            state="error",
                        )

                    # Training history
                    st.markdown("**📈 Training History:**")
                    import pandas as pd
                    hist_df = pd.DataFrame({
                        "Epoch": list(range(1, len(history["accuracy"]) + 1)),
                        "Train Acc": [f"{a*100:.2f}%" for a in history["accuracy"]],
                        "Val Acc": [f"{a*100:.2f}%" for a in history["val_accuracy"]],
                        "Train Loss": [f"{l:.4f}" for l in history["loss"]],
                        "Val Loss": [f"{l:.4f}" for l in history["val_loss"]],
                    })
                    st.dataframe(hist_df, use_container_width=True, hide_index=True)

                except Exception as e:
                    status_container.update(label="❌ Error saat training", state="error")
                    st.error(f"Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                finally:
                    # Cleanup temp dir
                    if 'tmp_dir' in locals():
                        shutil.rmtree(tmp_dir, ignore_errors=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#666;'>"
    "<small>🌊 Klasifikasi Habitat Bentik | Powered by Streamlit, TensorFlow & Hugging Face Hub</small>"
    "</div>",
    unsafe_allow_html=True,
)