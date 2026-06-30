"""
styles.py — Tema visual Deep Ocean.
Membuang semua chrome default Streamlit, mengganti seluruh tampilan
dengan desain kustom bertema laut dalam: glassmorphism, sonar readout,
tipografi DM Serif + DM Sans + Space Mono.
"""
from config import CLASS_NAMES, CLASS_COLORS, CLASS_ICONS

# ============================================================
# CSS UTAMA
# ============================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=Space+Mono:wght@400;700&display=swap');

/* ── Sembunyikan semua chrome bawaan Streamlit ── */
/* Gunakan banyak selector sekaligus untuk memastikan terkena */
[data-testid="stHeader"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
.stApp > header { display: none !important; height: 0 !important; }

/* Hapus padding atas yang tersisa setelah header disembunyikan */
[data-testid="stAppViewContainer"] { padding-top: 0 !important; margin-top: 0 !important; }
.stApp { padding-top: 0 !important; }
section.main { padding-top: 0 !important; }

/* ── Background halaman ── */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main,
.stApp {
    background: #05111A !important;
}

/* ── Layout ── */
.block-container {
    padding: 2.4rem 1.2rem 5rem !important;
    max-width: 800px !important;
}

/* ── Tipografi: HINDARI selector * yang terlalu luas
       karena akan merusak font ikon Material Symbols Streamlit
       (ikon 'upload' → tampil sebagai teks "uploadupload")
       Targetkan elemen spesifik saja ── */
body, html {
    font-family: 'DM Sans', sans-serif;
    color: #C7F2E8;
    background: #05111A;
}
p, label, li, td, th, small, div.stMarkdown,
.streamlit-expanderHeader, .streamlit-expanderContent,
[data-testid="stText"], [data-testid="stCaptionContainer"],
[data-testid="stMarkdownContainer"],
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label {
    font-family: 'DM Sans', sans-serif !important;
    color: #C7F2E8 !important;
}

/* ── Divider ── */
hr {
    border-color: rgba(14, 139, 112, 0.18) !important;
    margin: 1.8rem 0 !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(14,139,112,0.07) !important;
    border: 1px solid rgba(14,139,112,0.18) !important;
    border-radius: 10px !important;
    font-size: 0.88rem !important;
}
.streamlit-expanderContent {
    background: rgba(12,42,61,0.6) !important;
    border: 1px solid rgba(14,139,112,0.12) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] {
    background: rgba(14,139,112,0.04) !important;
    border: 2px dashed rgba(14,139,112,0.35) !important;
    border-radius: 18px !important;
    transition: border-color 0.2s, background 0.2s;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: rgba(24,201,154,0.6) !important;
    background: rgba(14,139,112,0.08) !important;
}
/* Tombol browse di dalam dropzone */
[data-testid="stFileUploaderDropzone"] button {
    background: rgba(14,139,112,0.15) !important;
    border: 1px solid rgba(14,139,112,0.35) !important;
    border-radius: 8px !important;
    color: #18C99A !important;
}
/* Teks & ikon di dalam button — JANGAN override font-family ikon Material */
[data-testid="stFileUploaderDropzone"] button p,
[data-testid="stFileUploaderDropzone"] button span:not([data-testid]):not([class*="material"]) {
    color: #18C99A !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small,
[data-testid="stFileUploaderDropzoneInstructions"] p {
    color: #7AB8A8 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Tombol utama ── */
button[kind="primary"] {
    background: linear-gradient(135deg, #0E8B70 0%, #18C99A 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: #05111A !important;
    padding: 0.65rem 1.4rem !important;
    box-shadow: 0 4px 20px rgba(14,139,112,0.3) !important;
}
button[kind="primary"]:hover {
    opacity: 0.88 !important;
    box-shadow: 0 6px 28px rgba(24,201,154,0.4) !important;
}
button[kind="primary"] p {
    color: #05111A !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #18C99A !important; }

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: rgba(12,42,61,0.8) !important;
    border: 1px solid rgba(14,139,112,0.25) !important;
    border-radius: 10px !important;
    color: #C7F2E8 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Alert box ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-left-width: 3px !important;
    background: rgba(12,42,61,0.7) !important;
}

/* ── Gambar ── */
[data-testid="stImage"] img {
    border-radius: 14px !important;
    box-shadow: 0 8px 30px rgba(0,0,0,0.4) !important;
}

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {
    color: #7AB8A8 !important;
    font-size: 0.82rem !important;
    font-family: 'DM Sans', sans-serif !important;
}
</style>
"""


def _c(html: str) -> str:
    """Strip leading whitespace dari tiap baris HTML (cegah Markdown code-block)."""
    return "\n".join(line.strip() for line in html.strip().splitlines())


# ============================================================
# HEADER
# ============================================================
def render_header() -> str:
    """Header halaman: kalimat pembuka + kelas-kelas sebagai tag."""
    tags = "".join(
        f'<span class="bk-tag">{CLASS_ICONS.get(cn,"•")} {cn}</span>'
        for cn in CLASS_NAMES
    )
    return _c(f"""
    <div class="bk-header">
        <div class="bk-eyebrow">Sistem Identifikasi</div>
        <h1 class="bk-title">Habitat Bentik</h1>
        <p class="bk-sub">Identifikasi tutupan dasar laut dari foto bawah air
        menggunakan model MobileNetV2 yang telah dilatih khusus.</p>
        <div class="bk-tags">{tags}</div>
        <div class="bk-header-glow"></div>
    </div>
    <style>
    .bk-header {{
        position: relative;
        padding: 2.8rem 0 2.2rem;
        margin-bottom: 0.4rem;
        overflow: hidden;
    }}
    .bk-header-glow {{
        position: absolute;
        top: -60px; left: -80px;
        width: 420px; height: 300px;
        background: radial-gradient(ellipse at center, rgba(14,139,112,0.18) 0%, transparent 70%);
        pointer-events: none;
    }}
    .bk-eyebrow {{
        font-family: 'Space Mono', monospace !important;
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #0E8B70 !important;
        margin-bottom: 0.5rem;
    }}
    .bk-title {{
        font-family: 'DM Serif Display', serif !important;
        font-style: italic;
        font-size: 3rem;
        font-weight: 400;
        line-height: 1.1;
        color: #C7F2E8 !important;
        margin: 0 0 0.75rem 0;
        letter-spacing: -0.01em;
    }}
    .bk-sub {{
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 300;
        font-size: 1rem;
        color: #7AB8A8 !important;
        max-width: 480px;
        line-height: 1.65;
        margin: 0 0 1.2rem 0;
    }}
    .bk-tags {{ display: flex; flex-wrap: wrap; gap: 0.5rem; }}
    .bk-tag {{
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.8rem;
        font-weight: 500;
        color: #7AB8A8 !important;
        background: rgba(14,139,112,0.1);
        border: 1px solid rgba(14,139,112,0.22);
        border-radius: 999px;
        padding: 0.25rem 0.7rem;
    }}
    </style>
    """)


# ============================================================
# SECTION LABEL
# ============================================================
def render_section(label: str) -> str:
    """Label section bergaya monospace dengan garis pembatas."""
    return _c(f"""
    <div class="bk-section">
        <span class="bk-section-label">{label}</span>
    </div>
    <style>
    .bk-section {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 1.6rem 0 0.9rem;
    }}
    .bk-section-label {{
        font-family: 'Space Mono', monospace !important;
        font-size: 0.68rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #0E8B70 !important;
        white-space: nowrap;
    }}
    .bk-section::after {{
        content: '';
        flex: 1;
        height: 1px;
        background: rgba(14,139,112,0.2);
    }}
    </style>
    """)


# ============================================================
# KARTU HASIL KLASIFIKASI
# ============================================================
def render_result_card(pred_class: str, confidence: float) -> str:
    """Kartu glassmorphism dengan nama kelas & bar confidence utama."""
    colors = CLASS_COLORS.get(pred_class, {"bg": "#0C2A3D", "accent": "#888", "text": "#C7F2E8"})
    icon = CLASS_ICONS.get(pred_class, "•")
    pct = max(0.0, min(1.0, confidence)) * 100

    return _c(f"""
    <div class="bk-result" style="--accent:{colors['accent']};">
        <div class="bk-result-glow"></div>
        <div class="bk-result-inner">
            <div class="bk-result-left">
                <div class="bk-result-icon">{icon}</div>
                <div>
                    <div class="bk-result-eyebrow">Teridentifikasi sebagai</div>
                    <div class="bk-result-class">{pred_class}</div>
                </div>
            </div>
            <div class="bk-result-conf">
                <div class="bk-conf-val">{pct:.1f}<span class="bk-conf-pct">%</span></div>
                <div class="bk-conf-lbl">confidence</div>
            </div>
        </div>
        <div class="bk-conf-bar-wrap">
            <div class="bk-conf-bar" style="width:{pct:.2f}%;"></div>
        </div>
    </div>
    <style>
    .bk-result {{
        position: relative;
        background: rgba(12,42,61,0.7);
        border: 1px solid rgba(14,139,112,0.22);
        border-left: 3px solid var(--accent);
        border-radius: 18px;
        padding: 1.6rem 1.6rem 1.1rem;
        margin: 0.6rem 0 1.4rem;
        backdrop-filter: blur(12px);
        overflow: hidden;
    }}
    .bk-result-glow {{
        position: absolute;
        top: -40px; right: -40px;
        width: 200px; height: 200px;
        background: radial-gradient(ellipse, color-mix(in srgb, var(--accent) 22%, transparent) 0%, transparent 70%);
        pointer-events: none;
    }}
    .bk-result-inner {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.1rem;
    }}
    .bk-result-left {{ display: flex; align-items: center; gap: 1rem; }}
    .bk-result-icon {{ font-size: 2.2rem; line-height: 1; }}
    .bk-result-eyebrow {{
        font-family: 'Space Mono', monospace !important;
        font-size: 0.65rem;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        color: #7AB8A8 !important;
        margin-bottom: 0.2rem;
    }}
    .bk-result-class {{
        font-family: 'DM Serif Display', serif !important;
        font-style: italic;
        font-size: 1.9rem;
        font-weight: 400;
        color: #C7F2E8 !important;
        line-height: 1.1;
    }}
    .bk-result-conf {{ text-align: right; }}
    .bk-conf-val {{
        font-family: 'Space Mono', monospace !important;
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent) !important;
        line-height: 1;
    }}
    .bk-conf-pct {{ font-size: 1rem; }}
    .bk-conf-lbl {{
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.72rem;
        color: #7AB8A8 !important;
        text-align: right;
        margin-top: 0.15rem;
    }}
    .bk-conf-bar-wrap {{
        width: 100%;
        height: 5px;
        background: rgba(255,255,255,0.07);
        border-radius: 999px;
        overflow: hidden;
    }}
    .bk-conf-bar {{
        height: 100%;
        background: linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--accent) 60%, #18C99A));
        border-radius: 999px;
        transition: width 0.6s cubic-bezier(.4,0,.2,1);
    }}
    </style>
    """)


def render_not_detected_card(confidence: float) -> str:
    """Kartu untuk kasus confidence di bawah threshold."""
    pct = max(0.0, min(1.0, confidence)) * 100
    return _c(f"""
    <div class="bk-result bk-result-unknown" style="--accent:#4A6470;">
        <div class="bk-result-inner">
            <div class="bk-result-left">
                <div class="bk-result-icon">❓</div>
                <div>
                    <div class="bk-result-eyebrow">Tidak teridentifikasi</div>
                    <div class="bk-result-class" style="color:#7AB8A8!important;">Tidak terdeteksi</div>
                </div>
            </div>
            <div class="bk-result-conf">
                <div class="bk-conf-val" style="color:#4A6470!important;">{pct:.1f}<span class="bk-conf-pct">%</span></div>
                <div class="bk-conf-lbl">confidence</div>
            </div>
        </div>
        <div class="bk-conf-bar-wrap">
            <div class="bk-conf-bar" style="width:{pct:.2f}%;"></div>
        </div>
        <p style="font-size:0.82rem;color:#7AB8A8!important;margin:0.75rem 0 0;line-height:1.55;">
            Confidence tertinggi {pct:.1f}% berada di bawah ambang batas.
            Coba foto ulang dengan pencahayaan lebih baik atau dari sudut berbeda.
        </p>
    </div>
    """)


# ============================================================
# SONAR READOUT — signature element
# confidence semua kelas ditampilkan sebagai layar echosounder
# ============================================================
def render_sonar_readout(probs: dict) -> str:
    """
    Confidence breakdown semua kelas bergaya readout sonar/echosounder.
    Ini signature element desain: font monospace, bar dengan ping dot
    di ujungnya, label dan angka seperti instrumen ilmiah.
    """
    sorted_items = sorted(probs.items(), key=lambda x: x[1], reverse=True)

    rows = ""
    for rank, (cn, val) in enumerate(sorted_items):
        colors = CLASS_COLORS.get(cn, {"accent": "#888"})
        icon = CLASS_ICONS.get(cn, "•")
        pct = max(0.0, min(100.0, val))
        rows += f"""
<div class="sonar-row" style="--bar-color:{colors['accent']}; --bar-w:{pct:.2f}%;">
    <div class="sonar-label">
        <span class="sonar-icon">{icon}</span>
        <span class="sonar-name">{cn}</span>
    </div>
    <div class="sonar-track">
        <div class="sonar-fill"></div>
        <div class="sonar-ping"></div>
    </div>
    <div class="sonar-val">{pct:05.2f}%</div>
</div>"""

    return _c(f"""
    <div class="sonar-wrap">
        <div class="sonar-top">
            <span class="sonar-eyebrow">▸ depth.scan // confidence_matrix</span>
        </div>
        {rows}
    </div>
    <style>
    .sonar-wrap {{
        background: rgba(5,17,26,0.85);
        border: 1px solid rgba(14,139,112,0.2);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        margin: 0.2rem 0 1.2rem;
        font-family: 'Space Mono', monospace !important;
    }}
    .sonar-top {{ margin-bottom: 1rem; }}
    .sonar-eyebrow {{
        font-family: 'Space Mono', monospace !important;
        font-size: 0.64rem;
        letter-spacing: 0.08em;
        color: #0E8B70 !important;
    }}
    .sonar-row {{
        display: grid;
        grid-template-columns: 110px 1fr 72px;
        align-items: center;
        gap: 0.75rem;
        padding: 0.45rem 0;
        border-top: 1px solid rgba(255,255,255,0.04);
    }}
    .sonar-label {{
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }}
    .sonar-icon {{ font-size: 0.85rem; }}
    .sonar-name {{
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.82rem;
        font-weight: 500;
        color: #C7F2E8 !important;
        white-space: nowrap;
    }}
    .sonar-track {{
        position: relative;
        height: 8px;
        background: rgba(255,255,255,0.05);
        border-radius: 999px;
        overflow: visible;
    }}
    .sonar-fill {{
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: var(--bar-w);
        background: linear-gradient(90deg, rgba(var(--bar-color-rgb,14,139,112),0.4), var(--bar-color));
        border-radius: 999px;
        background: var(--bar-color);
        opacity: 0.85;
    }}
    .sonar-ping {{
        position: absolute;
        top: 50%;
        left: var(--bar-w);
        transform: translate(-50%, -50%);
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--bar-color);
        box-shadow: 0 0 8px 3px var(--bar-color);
    }}
    .sonar-val {{
        font-family: 'Space Mono', monospace !important;
        font-size: 0.76rem;
        font-weight: 700;
        color: var(--bar-color) !important;
        text-align: right;
    }}
    </style>
    """)


# ============================================================
# LABEL GAMBAR
# ============================================================
def render_img_label(text: str) -> str:
    return _c(f"""
    <p style="font-family:'Space Mono',monospace!important;font-size:0.65rem;
    letter-spacing:0.13em;text-transform:uppercase;color:#0E8B70!important;margin:0 0 0.4rem;">
    {text}</p>
    """)


# ============================================================
# GRAD-CAM LABEL
# ============================================================
def render_gradcam_header() -> str:
    return _c("""
    <div style="margin-bottom:0.6rem;">
        <p style="font-family:'Space Mono',monospace!important;font-size:0.64rem;
        letter-spacing:0.13em;text-transform:uppercase;color:#0E8B70!important;margin:0 0 0.2rem;">
        ▸ grad-cam // gradient_weighted_class_activation</p>
        <p style="font-family:'DM Sans',sans-serif!important;font-size:0.84rem;
        color:#7AB8A8!important;margin:0;line-height:1.55;">
        Merah/kuning = area yang paling memengaruhi prediksi model.
        Biru/hijau = area kurang berpengaruh.</p>
    </div>
    """)


# ============================================================
# FOOTER
# ============================================================
def render_footer() -> str:
    return _c("""
    <div style="text-align:center;padding:2.5rem 0 1rem;
    border-top:1px solid rgba(14,139,112,0.12);margin-top:2rem;">
        <p style="font-family:'Space Mono',monospace!important;font-size:0.65rem;
        letter-spacing:0.1em;color:#2D5E52!important;margin:0;">
        HABITAT BENTIK · MobileNetV2 · Streamlit + TensorFlow + HF Hub</p>
    </div>
    """)
