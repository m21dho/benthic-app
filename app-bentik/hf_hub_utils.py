"""
hf_hub_utils.py — Semua fungsi yang berbicara ke Hugging Face Hub.
Murni fungsi I/O, tidak ada st.* (kode UI) di sini.
"""
import os
from datetime import datetime

from config import CLASS_NAMES, MODEL_FILENAME

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


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


def hf_upload_model(hf_cfg, local_path):
    """Upload model .keras ke HF Hub (+ simpan backup bertimestamp) DALAM SATU COMMIT."""
    from huggingface_hub import HfApi, CommitOperationAdd
    api = HfApi(token=hf_cfg["token"])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    operations = [
        CommitOperationAdd(path_in_repo=MODEL_FILENAME, path_or_fileobj=local_path),
        CommitOperationAdd(path_in_repo=f"backups/{ts}_{MODEL_FILENAME}", path_or_fileobj=local_path),
    ]
    api.create_commit(
        repo_id=hf_cfg["model_repo"],
        repo_type="model",
        operations=operations,
        commit_message=f"Update model + backup {ts}",
    )


def hf_upload_images(hf_cfg, class_name, image_bytes_list, batch_size=75):
    """
    Upload list of (filename, bytes) ke HF dataset repo di folder class_name/.

    PENTING: digabung jadi commit BATCH (maks `batch_size` file per commit),
    bukan 1 commit per file — Hugging Face membatasi 128 commit/jam untuk
    akun gratis, jadi upload satu-per-satu akan cepat kena rate limit.
    Dengan batching, 1000 citra cukup ~14 commit, bukan 1000 commit.
    """
    from huggingface_hub import HfApi, CommitOperationAdd
    api = HfApi(token=hf_cfg["token"])
    class_folder = class_name.lower()
    items = list(image_bytes_list)
    uploaded = 0

    for i in range(0, len(items), batch_size):
        chunk = items[i:i + batch_size]
        operations = [
            CommitOperationAdd(
                path_in_repo=f"{class_folder}/{fname}",
                path_or_fileobj=fbytes,
            )
            for fname, fbytes in chunk
        ]
        try:
            api.create_commit(
                repo_id=hf_cfg["dataset_repo"],
                repo_type="dataset",
                operations=operations,
                commit_message=f"Tambah {len(operations)} citra ke kelas {class_name}",
            )
            uploaded += len(operations)
        except Exception:
            # Lewati batch yang gagal, lanjut ke batch berikutnya
            continue

    return uploaded


def hf_get_image_counts(hf_cfg):
    """Hitung jumlah citra per kelas di HF dataset repo."""
    from huggingface_hub import HfApi
    api = HfApi(token=hf_cfg["token"])
    counts = {name: 0 for name in CLASS_NAMES}
    try:
        files = api.list_repo_files(repo_id=hf_cfg["dataset_repo"], repo_type="dataset")
        for f in files:
            parts = f.split("/")
            if len(parts) >= 2:
                folder = parts[0]
                ext = os.path.splitext(parts[-1])[1].lower()
                if ext in IMAGE_EXTS:
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
    return snapshot_download(
        repo_id=hf_cfg["dataset_repo"],
        repo_type="dataset",
        token=hf_cfg["token"],
        local_dir=local_dir,
    )


def detect_class_from_path(rel_path, class_names):
    """
    Cari nama kelas dari path relatif sebuah file hasil upload folder
    (mis. 'dataset_baru/karang/foto1.jpg' -> 'Karang').
    Mencocokkan SETIAP segmen folder (case-insensitive) terhadap class_names.
    Return nama kelas (sesuai class_names) atau None jika tidak ketemu.
    """
    parts = rel_path.replace("\\", "/").split("/")[:-1]  # buang nama file
    for part in parts:
        for cn in class_names:
            if part.strip().lower() == cn.lower():
                return cn
    return None
