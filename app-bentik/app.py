"""
app.py — Lapisan UI Streamlit.
Semua logika model, HF Hub, dan training ada di modul lain (model_utils,
hf_hub_utils, train_utils). File ini hanya mengatur tampilan & alur halaman.
"""
import os
import tempfile
import shutil
import warnings

import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image

from config import (
    NUM_CLASSES, CLASS_NAMES, CLASS_COLORS, CLASS_ICONS,
    IMG_SIZE, CONFIDENCE_THRESHOLD, MIN_IMAGES_PER_CLASS,
    MODEL_FOLDER, MODEL_FILENAME, get_hf_config,
)
from hf_hub_utils import (
    hf_ensure_repos, hf_download_model, hf_upload_model,
    hf_upload_images, hf_get_image_counts, hf_download_dataset,
)
from model_utils import load_model_cached, classify_image, compute_gradcam_overlay
from train_utils import prepare_dataset_from_dir, finetune_model
from styles import CSS, render_hero, render_prediction_card, render_class_status_cards, render_footer

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
        "lamun, pasir, atau lainnya — lalu bantu model belajar dari citra baru Anda.",
    ),
    unsafe_allow_html=True,
)

hf_cfg = get_hf_config()
hf_available = hf_cfg is not None

with st.expander("ℹ️ Cara pakai"):
    st.markdown(
        "**Tab Klasifikasi** — upload gambar, lihat prediksi & area fokus model (Grad-CAM).\n\n"
        "**Tab Kelola Dataset** — upload citra training per kelas "
        f"(min. {MIN_IMAGES_PER_CLASS}/kelas), lalu latih ulang model.\n\n"
        f"Model menerima gambar {IMG_SIZE}×{IMG_SIZE}px, dengan confidence threshold "
        f"{CONFIDENCE_THRESHOLD*100:.0f}%."
    )


# ============================================================
# LOAD MODEL (dari HF Hub atau lokal)
# ============================================================
if "loaded_model" not in st.session_state:
    st.session_state.loaded_model = None
    st.session_state.model_loaded = False
    st.session_state.model_path = None
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
        debug_lines.append("HF Hub tidak terkonfigurasi (cek Secrets).")

    if os.path.exists(model_path):
        model, status = load_model_cached(model_path)
        debug_lines.append(status)
        if model is not None:
            st.session_state.loaded_model = model
            st.session_state.model_loaded = True
            st.session_state.model_path = model_path
    else:
        debug_lines.append(f"File model tidak ditemukan di: {model_path}")

    st.session_state.model_debug = "\n".join(debug_lines)

if not st.session_state.model_loaded:
    st.error("❌ Model belum berhasil dimuat.")
    with st.expander("🔍 Detail error (untuk debugging)"):
        st.code(st.session_state.model_debug or "(tidak ada info)")



# ============================================================
# MAIN — TABS
# ============================================================
tab_klasifikasi, tab_dataset = st.tabs(["🔬 Klasifikasi", "📂 Kelola Dataset & Training"])

# ────────────────────────────────────────────────────────────
# TAB 1: KLASIFIKASI
# ────────────────────────────────────────────────────────────
with tab_klasifikasi:
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

            st.markdown(
                render_prediction_card(pred_class, confidence, below_threshold),
                unsafe_allow_html=True,
            )

            st.markdown("**📋 Persentase semua kelas**")

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


# ────────────────────────────────────────────────────────────
# TAB 2: KELOLA DATASET & TRAINING
# ────────────────────────────────────────────────────────────
with tab_dataset:
    st.markdown("#### Kelola dataset & latih ulang model")

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
        try:
            hf_ensure_repos(hf_cfg)
        except Exception as e:
            st.error(f"Gagal menyiapkan repo HF Hub: {e}")

        # ── Status dataset ──
        st.markdown("**📊 Status dataset di Hugging Face Hub**")

        if st.button("🔄 Refresh hitungan", key="refresh_counts"):
            st.cache_data.clear()

        @st.cache_data(ttl=60, show_spinner=False)
        def cached_counts(_token, _repo):
            return hf_get_image_counts(hf_cfg)

        with st.spinner("Menghitung citra di HF Hub..."):
            counts = cached_counts(hf_cfg["token"], hf_cfg["dataset_repo"])

        st.markdown(render_class_status_cards(counts, MIN_IMAGES_PER_CLASS), unsafe_allow_html=True)

        all_ready = all(counts.get(cn, 0) >= MIN_IMAGES_PER_CLASS for cn in CLASS_NAMES)
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

        # ── Upload citra ──
        st.markdown("**📤 Upload citra baru ke dataset**")

        selected_class = st.selectbox(
            "Pilih kelas tujuan:",
            CLASS_NAMES,
            help="Citra yang di-upload akan masuk ke kelas ini.",
        )

        uploaded_files = st.file_uploader(
            f"Upload citra untuk kelas {selected_class}",
            type=["jpg", "jpeg", "png", "bmp", "tiff"],
            accept_multiple_files=True,
            help=f"Upload minimal {MIN_IMAGES_PER_CLASS} citra per kelas. "
                 "Anda bisa upload berkali-kali — citra akan terakumulasi di HF Hub.",
            key="dataset_uploader",
        )

        if uploaded_files:
            st.caption(f"📎 {len(uploaded_files)} file dipilih untuk kelas **{selected_class}**")

            preview_count = min(8, len(uploaded_files))
            cols = st.columns(min(4, preview_count))
            for i in range(preview_count):
                with cols[i % len(cols)]:
                    img = Image.open(uploaded_files[i])
                    st.image(img, caption=uploaded_files[i].name, width="stretch")

            if len(uploaded_files) > preview_count:
                st.caption(f"... dan {len(uploaded_files) - preview_count} citra lainnya")

            if st.button("⬆️ Upload ke Hugging Face Hub", width="stretch", type="primary"):
                image_data, skipped = [], 0
                for f in uploaded_files:
                    try:
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

                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Tidak ada file gambar valid yang bisa di-upload.")

        st.markdown("---")

        # ── Latih ulang model ──
        st.markdown("**🧠 Latih ulang model (fine-tuning)**")

        st.info(
            "**Cara kerja:**\n"
            "1. Semua citra di HF Dataset di-download ke memori sementara\n"
            "2. Model saat ini di-fine-tune (backbone dibekukan, hanya head dilatih)\n"
            "3. Akurasi validasi dicek — model baru **hanya menggantikan model lama "
            "jika akurasinya tidak lebih buruk**\n"
            "4. Model lama otomatis di-backup di HF Hub (bisa rollback)\n"
            "5. Learning rate kecil (1e-5), 5 epoch — cocok untuk CPU"
        )

        with st.expander("⚙️ Pengaturan fine-tuning (opsional)"):
            ft_epochs = st.slider("Jumlah epoch", 2, 15, 5)
            ft_lr = st.select_slider(
                "Learning rate",
                options=[1e-6, 5e-6, 1e-5, 5e-5, 1e-4],
                value=1e-5,
                format_func=lambda x: f"{x:.0e}",
            )
            ft_val_split = st.slider("Validasi split (%)", 10, 30, 20) / 100

        can_train = all_ready and st.session_state.model_loaded
        if not st.session_state.model_loaded:
            st.warning("⚠️ Model belum dimuat — tidak bisa fine-tune.")
        if not all_ready:
            st.warning(f"⚠️ Belum semua kelas memenuhi minimum {MIN_IMAGES_PER_CLASS} citra.")

        if st.button(
            "🚀 Mulai latih ulang model",
            width="stretch",
            type="primary",
            disabled=not can_train,
        ):
            status_container = st.status("🔄 Proses fine-tuning...", expanded=True)
            tmp_dir = None

            with status_container:
                try:
                    st.write("📥 Mengunduh dataset dari HF Hub...")
                    tmp_dir = tempfile.mkdtemp(prefix="bentik_ds_")
                    hf_download_dataset(hf_cfg, tmp_dir)
                    st.write("✅ Dataset berhasil di-download")

                    st.write("🔄 Mempersiapkan data training & validasi...")
                    train_ds, val_ds, total_imgs = prepare_dataset_from_dir(
                        tmp_dir, validation_split=ft_val_split
                    )
                    if train_ds is None:
                        st.error("❌ Tidak ada citra valid ditemukan di dataset.")
                        st.stop()

                    st.write(
                        f"✅ Total {total_imgs} citra — "
                        f"train: {int(total_imgs*(1-ft_val_split))}, "
                        f"val: {int(total_imgs*ft_val_split)}"
                    )

                    st.write("📊 Mengevaluasi model lama pada data validasi...")
                    old_model = st.session_state.loaded_model
                    old_loss, old_acc = old_model.evaluate(val_ds, verbose=0)
                    st.write(f"   Model lama — Val Accuracy: **{old_acc*100:.2f}%**")

                    st.write(f"🧠 Melatih model baru ({ft_epochs} epoch, lr={ft_lr:.0e})...")
                    new_model, history = finetune_model(
                        old_model, train_ds, val_ds, epochs=ft_epochs, lr=ft_lr,
                    )
                    new_acc = history["val_accuracy"][-1]
                    st.write(f"   Model baru — Val Accuracy: **{new_acc*100:.2f}%**")

                    st.write("⚖️ Membandingkan model lama vs baru...")
                    improvement = new_acc - old_acc

                    if new_acc >= old_acc - 0.02:
                        st.write(f"✅ Model baru diterima (Δ = {improvement*100:+.2f}%)")

                        st.write("💾 Menyimpan model baru...")
                        os.makedirs(MODEL_FOLDER, exist_ok=True)
                        new_model_path = os.path.join(MODEL_FOLDER, MODEL_FILENAME)
                        new_model.save(new_model_path)

                        st.write("☁️ Mengupload model baru ke HF Hub (+ backup model lama)...")
                        hf_upload_model(hf_cfg, new_model_path)
                        st.write("✅ Upload selesai!")

                        st.cache_resource.clear()
                        st.session_state.loaded_model = new_model
                        st.session_state.model_loaded = True
                        st.session_state.model_path = new_model_path

                        status_container.update(
                            label="✅ Fine-tuning selesai — model baru aktif!", state="complete"
                        )
                    else:
                        st.write(
                            f"❌ Model baru DITOLAK — akurasi turun {abs(improvement)*100:.2f}% "
                            f"(melebihi toleransi 2%). Model lama tetap dipakai."
                        )
                        status_container.update(
                            label="⚠️ Model baru ditolak — model lama tetap aktif", state="error"
                        )

                    st.markdown("**📈 Training history**")
                    hist_df = pd.DataFrame({
                        "Epoch": list(range(1, len(history["accuracy"]) + 1)),
                        "Train Acc": [f"{a*100:.2f}%" for a in history["accuracy"]],
                        "Val Acc": [f"{a*100:.2f}%" for a in history["val_accuracy"]],
                        "Train Loss": [f"{l:.4f}" for l in history["loss"]],
                        "Val Loss": [f"{l:.4f}" for l in history["val_loss"]],
                    })
                    st.dataframe(hist_df, width="stretch", hide_index=True)

                except Exception as e:
                    status_container.update(label="❌ Error saat training", state="error")
                    st.error(f"Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                finally:
                    if tmp_dir:
                        shutil.rmtree(tmp_dir, ignore_errors=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown(
    render_footer("🌊 Klasifikasi Habitat Bentik · Streamlit + TensorFlow + Hugging Face Hub"),
    unsafe_allow_html=True,
)
