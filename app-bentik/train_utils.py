"""
train_utils.py — Fungsi penyiapan dataset & fine-tuning model.
Tidak ada elemen UI di sini.
"""
import os
import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

from config import CLASS_NAMES, IMG_SIZE

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def prepare_dataset_from_dir(data_dir, validation_split=0.2):
    """
    Baca citra dari data_dir/<kelas>/*.jpg dan buat tf.data.Dataset
    untuk train & validation.
    Return (train_ds, val_ds, total_images) — train_ds/val_ds bisa None jika kosong.
    """
    images, labels = [], []

    for idx, class_name in enumerate(CLASS_NAMES):
        class_dir = os.path.join(data_dir, class_name.lower())
        if not os.path.isdir(class_dir):
            continue
        for fname in os.listdir(class_dir):
            if os.path.splitext(fname)[1].lower() not in IMAGE_EXTS:
                continue
            fpath = os.path.join(class_dir, fname)
            try:
                img = Image.open(fpath).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
                arr = preprocess_input(np.array(img, dtype=np.float32))
                images.append(arr)
                labels.append(idx)
            except Exception:
                continue

    if len(images) == 0:
        return None, None, 0

    images = np.array(images, dtype=np.float32)
    labels = np.array(labels, dtype=np.int32)
    total = len(images)

    idx_perm = np.random.permutation(total)
    images, labels = images[idx_perm], labels[idx_perm]

    val_count = max(1, int(total * validation_split))
    train_imgs, val_imgs = images[val_count:], images[:val_count]
    train_lbls, val_lbls = labels[val_count:], labels[:val_count]

    batch_size = min(16, len(train_imgs))

    train_ds = tf.data.Dataset.from_tensor_slices((train_imgs, train_lbls))
    train_ds = train_ds.shuffle(512).batch(batch_size).prefetch(tf.data.AUTOTUNE)

    val_ds = tf.data.Dataset.from_tensor_slices((val_imgs, val_lbls))
    val_ds = val_ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)

    return train_ds, val_ds, total


def evaluate_model(model, val_ds):
    """
    Evaluasi model pada val_ds (label berupa integer, bukan one-hot).

    Model yang di-load dari file .keras bisa saja punya konfigurasi loss lama
    dari training awal (mis. categorical_crossentropy + label one-hot, kalau
    training aslinya pakai Label Smoothing). Itu tidak cocok dengan val_ds
    kita yang labelnya integer biasa -> akan error rank mismatch saat evaluate.

    Compile ulang dengan SparseCategoricalCrossentropy supaya cocok dengan
    format label kita. Ini AMAN: compile cuma mengganti konfigurasi
    loss/optimizer/metric, tidak mengubah bobot/weight model sama sekali.

    Return (loss, accuracy).
    """
    model.compile(
        optimizer=tf.keras.optimizers.Adam(),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )
    loss, acc = model.evaluate(val_ds, verbose=0)
    return loss, acc


def finetune_model(base_model, train_ds, val_ds, epochs=5, lr=1e-5):
    """
    Fine-tune: backbone dibekukan, hanya classification head yang dilatih.
    Return (finetuned_model, history_dict).
    """
    model = tf.keras.models.clone_model(base_model)
    model.set_weights(base_model.get_weights())

    # Freeze layer backbone (nama mengandung 'mobilenetv2'/'conv'/'bn'/'block'),
    # sisanya (classification head) tetap trainable.
    trainable_count = 0
    for layer in model.layers:
        if any(kw in layer.name.lower() for kw in ["mobilenetv2", "conv", "bn", "block"]):
            layer.trainable = False
        else:
            layer.trainable = True
            trainable_count += 1

    if trainable_count == 0:
        for layer in model.layers[-10:]:
            layer.trainable = True

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=lr, clipnorm=1.0),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )

    history = model.fit(train_ds, validation_data=val_ds, epochs=epochs, verbose=0)
    return model, history.history
