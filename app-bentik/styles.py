"""
styles.py — Tema visual Deep Ocean.
Komponen HTML kustom + CSS yang membuang chrome default Streamlit.
"""
from config import CLASS_NAMES, CLASS_COLORS, CLASS_ICONS

# ============================================================
# CSS UTAMA
# ============================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=Space+Mono:wght@400;700&display=swap');

/* ── Sembunyikan chrome Streamlit ── */
[data-testid="stHeader"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
.stApp > header { display: none !important; height: 0 !important; }
[data-testid="stAppViewContainer"] { padding-top: 0 !important; margin-top: 0 !important; }
.stApp { padding-top: 0 !important; }
section.main { padding-top: 0 !important; }

/* ── Background ── */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, .stApp { background: #05111A !important; }

/* ── Layout ── */
.block-container {
    padding: 2.4rem 1.2rem 5rem !important;
    max-width: 800px !important;
}

/* ── Tipografi — JANGAN gunakan * selector (merusak ikon Material) ── */
body, html { font-family: 'DM Sans', sans-serif; color: #C7F2E8; background: #05111A; }
p, label, li, td, th,
.streamlit-expanderHeader, .streamlit-expanderContent,
[data-testid="stText"],
[data-testid="stCaptionContainer"],
[data-testid="stMarkdownContainer"],
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label {
    font-family: 'DM Sans', sans-serif !important;
    color: #C7F2E8 !important;
}

/* ── Divider ── */
hr { border-color: rgba(14,139,112,0.18) !important; margin: 1.6rem 0 !important; }

/* ── Expander (blok detail) ── */
.streamlit-expanderHeader {
    background: rgba(14,139,112,0.07) !important;
    border: 1px solid rgba(14,139,112,0.22) !important;
    border-radius: 10px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    color: #18C99A !important;
}
.streamlit-expanderContent {
    background: rgba(5,17,26,0.85) !important;
    border: 1px solid rgba(14,139,112,0.16) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    padding: 1rem 1.2rem !important;
}

/* ── File uploader: tampil sebagai tombol "Pilih Gambar" ──
   PENDEKATAN: ::after pada DROPZONE (bukan span),
   button transparan mengisi seluruh area → klik tetap bekerja
   Menghindari manipulasi span yang menyebabkan duplikasi teks ── */

/* Sembunyikan SELURUH label dan instruksi */
[data-testid="stFileUploader"] > div > label,
[data-testid="stFileUploader"] > label,
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderFile"],
[data-testid="stFileUploaderDeleteBtn"] {
    display: none !important;
}

/* FIX BUG: File info (nama file, ukuran, tombol hapus) muncul sebagai
   SIBLING di luar dropzone setelah file dipilih — harus disembunyikan
   dengan cara menarget elemen sibling dropzone dan semua list file */
[data-testid="stFileUploaderDropzone"] ~ *,
[data-testid="stFileUploader"] ul,
[data-testid="stFileUploader"] li,
[data-testid="stFileUploader"] small {
    display: none !important;
}

/* FIX DEFINITIF: Clip seluruh container file uploader ke tinggi tombol.
   Apapun posisi DOM file info (sibling, child, nested) — tidak akan
   terlihat karena overflow tersembunyi di batas 42px. */
[data-testid="stFileUploader"],
[data-testid="stFileUploader"] > div {
    max-height: 42px !important;
    overflow: hidden !important;
}

/* Dropzone: tampil sebagai area tombol persegi */
[data-testid="stFileUploaderDropzone"] {
    position: relative !important;
    height: 42px !important;
    overflow: hidden !important;
    background: rgba(14,139,112,0.10) !important;
    border: 1px solid rgba(14,139,112,0.40) !important;
    border-radius: 10px !important;
    cursor: pointer !important;
    padding: 0 !important;
    min-height: 0 !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    background: rgba(14,139,112,0.16) !important;
    border-color: rgba(24,201,154,0.6) !important;
}
/* Label "Pilih Gambar" sebagai overlay — background OPAQUE agar file info tertutup total */
[data-testid="stFileUploaderDropzone"]::after {
    content: "Pilih Gambar" !important;
    position: absolute !important;
    top: 0; left: 0; right: 0; bottom: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #061D23 !important;   /* opaque — blending #05111A + rgba(14,139,112,0.10) */
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #18C99A !important;
    pointer-events: none !important;
    letter-spacing: 0.01em;
    z-index: 99 !important;
}
/* Button transparan mengisi seluruh dropzone → masih bisa diklik */
[data-testid="stFileUploaderDropzone"] button {
    position: absolute !important;
    top: 0; left: 0; right: 0; bottom: 0 !important;
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    cursor: pointer !important;
    border: none !important;
    background: transparent !important;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 1 !important;
}

/* ── Tinggi kolom sama (kiri stretch menyesuaikan kanan) ── */
[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
}
[data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
}
/* Placeholder gambar mengisi sisa tinggi kolom */
[data-testid="column"]:first-child [data-testid="stMarkdownContainer"]:first-child {
    flex: 1 !important;
    display: flex !important;
}

/* ── Tombol Klasifikasi ──
   Gunakan BANYAK selector karena di Streamlit 1.58 'kind' attribute
   bisa bervariasi cara rendernya */
button[kind="primary"],
[data-testid="stBaseButton-primary"],
[data-testid="baseButton-primary"],
.stButton > button {
    background: linear-gradient(135deg, #0E8B70 0%, #18C99A 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    color: #05111A !important;
    box-shadow: 0 4px 18px rgba(14,139,112,0.28) !important;
}
button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover,
.stButton > button:hover {
    opacity: 0.88 !important;
    box-shadow: 0 6px 24px rgba(24,201,154,0.38) !important;
}
button[kind="primary"] p,
[data-testid="stBaseButton-primary"] p,
.stButton > button p {
    color: #05111A !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
}
button[kind="primary"]:disabled,
[data-testid="stBaseButton-primary"]:disabled,
.stButton > button:disabled {
    opacity: 0.35 !important;
    background: rgba(14,139,112,0.25) !important;
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
    font-size: 0.84rem !important;
}

/* ── Alert ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    background: rgba(12,42,61,0.7) !important;
    border-left-width: 3px !important;
}

/* ── Gambar ── */
[data-testid="stImage"] img {
    border-radius: 14px !important;
    box-shadow: 0 8px 28px rgba(0,0,0,0.38) !important;
}

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {
    color: #7AB8A8 !important;
    font-size: 0.8rem !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Column gap ── */
[data-testid="column"] { gap: 0 !important; }
</style>
"""


def _c(html: str) -> str:
    """Strip leading whitespace agar tidak jadi Markdown code-block."""
    return "\n".join(line.strip() for line in html.strip().splitlines())


# ============================================================
# HEADER
# ============================================================
def render_header() -> str:
    tags = "".join(
        f'<span class="bk-tag">{CLASS_ICONS.get(cn,"•")} {cn}</span>'
        for cn in CLASS_NAMES
    )
    return _c(f"""
<div class="bk-header">
<div class="bk-header-glow"></div>
<div class="bk-eyebrow">Sistem Klasifikasi</div>
<h1 class="bk-title">Habitat Bentik</h1>
<p class="bk-sub">Identifikasi tutupan dasar laut dari foto bawah air
menggunakan model MobileNetV2 yang telah dilatih khusus.</p>
<div class="bk-tags">{tags}</div>
</div>
<style>
.bk-header {{
position: relative; padding: 2.6rem 0 1.8rem;
}}
.bk-header-glow {{
position: absolute; top: -60px; left: -80px;
width: 420px; height: 300px;
background: radial-gradient(ellipse, rgba(14,139,112,0.16) 0%, transparent 70%);
pointer-events: none;
}}
.bk-eyebrow {{
font-family: 'Space Mono', monospace !important;
font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase;
color: #0E8B70 !important; margin-bottom: 0.45rem;
}}
.bk-title {{
font-family: 'DM Serif Display', serif !important;
font-style: italic; font-size: 2.8rem; font-weight: 400;
line-height: 1.1; color: #C7F2E8 !important;
margin: 0 0 0.65rem; letter-spacing: -0.01em;
}}
.bk-sub {{
font-family: 'DM Sans', sans-serif !important;
font-weight: 300; font-size: 0.95rem;
color: #7AB8A8 !important; max-width: 460px;
line-height: 1.6; margin: 0 0 1rem;
}}
.bk-tags {{ display: flex; flex-wrap: wrap; gap: 0.45rem; }}
.bk-tag {{
font-family: 'DM Sans', sans-serif !important;
font-size: 0.78rem; font-weight: 500; color: #7AB8A8 !important;
background: rgba(14,139,112,0.1);
border: 1px solid rgba(14,139,112,0.22);
border-radius: 999px; padding: 0.22rem 0.65rem;
}}
</style>
""")


# ============================================================
# IMAGE PLACEHOLDER — sebelum gambar dipilih
# ============================================================
def render_img_placeholder() -> str:
    return _c("""
<div style="display:flex;flex-direction:column;flex:1;height:100%;min-height:240px;">
<div class="bk-img-ph">
<svg xmlns="http://www.w3.org/2000/svg" width="52" height="60" viewBox="0 0 52 60" fill="none">
<rect x="2" y="2" width="38" height="48" rx="5" fill="rgba(12,42,61,0.5)"
stroke="rgba(14,139,112,0.28)" stroke-width="2"/>
<rect x="10" y="2" width="38" height="48" rx="5" fill="rgba(12,42,61,0.7)"
stroke="rgba(14,139,112,0.35)" stroke-width="2"/>
<line x1="18" y1="18" x2="36" y2="18" stroke="rgba(14,139,112,0.3)"
stroke-width="1.5" stroke-linecap="round"/>
<line x1="18" y1="24" x2="33" y2="24" stroke="rgba(14,139,112,0.2)"
stroke-width="1" stroke-linecap="round"/>
<line x1="18" y1="29" x2="30" y2="29" stroke="rgba(14,139,112,0.15)"
stroke-width="1" stroke-linecap="round"/>
<rect x="16" y="35" width="16" height="9" rx="2" fill="rgba(14,139,112,0.15)"
stroke="rgba(14,139,112,0.3)" stroke-width="1"/>
<text x="24" y="42" text-anchor="middle" font-family="Space Mono,monospace"
font-size="5.5" font-weight="700" fill="rgba(14,139,112,0.65)">IMG</text>
</svg>
<p class="bk-ph-hint">Pilih gambar di bawah</p>
</div>
</div>
<style>
.bk-img-ph {
flex: 1;
background: rgba(12,42,61,0.3);
border: 2px dashed rgba(14,139,112,0.2);
border-radius: 16px;
display: flex; flex-direction: column;
align-items: center; justify-content: center;
width: 100%; gap: 0.75rem;
}
.bk-ph-hint {
font-family: 'Space Mono', monospace !important;
font-size: 0.6rem !important; letter-spacing: 0.12em;
text-transform: uppercase; color: #2D5E52 !important; margin: 0 !important;
}
</style>
""")


# ============================================================
# PLACEHOLDER KARTU — sebelum ada hasil
# ============================================================
def render_placeholder_card(label: str, min_height: str = "100px") -> str:
    return _c(f"""
<div class="bk-ph-card" style="min-height:{min_height};">
<span class="bk-ph-card-lbl">{label}</span>
</div>
<style>
.bk-ph-card {{
background: rgba(12,42,61,0.3);
border: 1px dashed rgba(14,139,112,0.18);
border-radius: 14px;
display: flex; align-items: center; justify-content: center;
width: 100%; margin-bottom: 0.75rem;
}}
.bk-ph-card-lbl {{
font-family: 'Space Mono', monospace !important;
font-size: 0.6rem; letter-spacing: 0.14em;
text-transform: uppercase; color: #2D5E52 !important;
}}
</style>
""")


# ============================================================
# OUTPUT KELAS — hasil klasifikasi TANPA angka confidence
# ============================================================
def render_output_card(pred_class: str) -> str:
    """Kartu hasil klasifikasi di tampilan utama — tidak menampilkan angka."""
    colors = CLASS_COLORS.get(pred_class, {
        "bg": "rgba(12,42,61,0.7)", "accent": "#888", "text": "#C7F2E8"
    })
    icon = CLASS_ICONS.get(pred_class, "•")
    return _c(f"""
<div class="bk-out" style="--acc:{colors['accent']};background:{colors['bg']};">
<div class="bk-out-glow"></div>
<div class="bk-out-ey">Output kelas</div>
<div class="bk-out-main">
<span class="bk-out-ico">{icon}</span>
<span class="bk-out-name" style="color:{colors['text']};">{pred_class}</span>
</div>
<div class="bk-out-line"><div class="bk-out-fill"></div></div>
</div>
<style>
.bk-out {{
position: relative;
border: 1px solid rgba(14,139,112,0.22);
border-left: 3px solid var(--acc);
border-radius: 14px;
padding: 1rem 1.1rem 0.85rem;
margin-bottom: 0.75rem; overflow: hidden;
}}
.bk-out-glow {{
position: absolute; top: -30px; right: -30px;
width: 130px; height: 130px;
background: radial-gradient(ellipse,
color-mix(in srgb, var(--acc) 18%, transparent) 0%, transparent 70%);
pointer-events: none;
}}
.bk-out-ey {{
font-family: 'Space Mono', monospace !important;
font-size: 0.58rem; letter-spacing: 0.14em;
text-transform: uppercase; color: #7AB8A8 !important;
margin-bottom: 0.45rem;
}}
.bk-out-main {{ display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.7rem; }}
.bk-out-ico {{ font-size: 1.6rem; line-height: 1; }}
.bk-out-name {{
font-family: 'DM Serif Display', serif !important;
font-style: italic; font-size: 1.55rem; font-weight: 400; line-height: 1.1;
}}
.bk-out-line {{
width: 100%; height: 3px;
background: rgba(255,255,255,0.05); border-radius: 999px; overflow: hidden;
}}
.bk-out-fill {{
height: 100%; width: 100%;
background: linear-gradient(90deg, transparent, var(--acc));
opacity: 0.45;
}}
</style>
""")


def render_output_not_detected() -> str:
    return _c("""
<div class="bk-out" style="--acc:#4A6470;background:rgba(12,42,61,0.45);">
<div class="bk-out-ey">Output kelas</div>
<div class="bk-out-main">
<span class="bk-out-ico">
<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="15" cy="15" r="13" stroke="#4A6470" stroke-width="1.8"/>
<text x="15" y="20.5" text-anchor="middle"
font-family="Georgia,serif" font-size="16" font-weight="700"
fill="#4A6470">?</text>
</svg>
</span>
<span class="bk-out-name" style="color:#7AB8A8!important;">Tidak terdeteksi</span>
</div>
<p style="font-family:'DM Sans',sans-serif!important;font-size:0.78rem;
color:#7AB8A8!important;margin:0.4rem 0 0;line-height:1.5;">
Confidence terlalu rendah. Coba foto ulang dengan pencahayaan lebih baik.</p>
</div>
""")


# ============================================================
# LABEL KECIL (monospace)
# ============================================================
def render_img_label(text: str) -> str:
    return _c(f"""
<p style="font-family:'Space Mono',monospace!important;font-size:0.6rem;
letter-spacing:0.13em;text-transform:uppercase;
color:#0E8B70!important;margin:0 0 0.35rem;">{text}</p>
""")


# ============================================================
# SONAR TANPA ANGKA — untuk blok detail
# ============================================================
def render_sonar_no_numbers(probs: dict) -> str:
    """
    Bar distribusi kelas TANPA angka persentase.
    Hanya tampilkan lebar relatif bar agar pengguna tahu
    kelas mana yang lebih 'meyakinkan' tanpa nilai eksak.
    """
    sorted_items = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    rows = ""
    for cn, val in sorted_items:
        colors = CLASS_COLORS.get(cn, {"accent": "#888"})
        icon = CLASS_ICONS.get(cn, "•")
        pct = max(0.0, min(100.0, val))
        rows += f"""
<div class="sn-row" style="--bc:{colors['accent']};--bw:{pct:.2f}%;">
<div class="sn-lbl"><span>{icon}</span><span class="sn-nm">{cn}</span></div>
<div class="sn-track"><div class="sn-fill"></div><div class="sn-ping"></div></div>
</div>"""
    return _c(f"""
<div class="sn-wrap">
<p class="sn-hint">Lebar bar menunjukkan keyakinan relatif model terhadap setiap kelas.</p>
{rows}
</div>
<style>
.sn-wrap {{ padding: 0.1rem 0; }}
.sn-hint {{
font-family: 'DM Sans', sans-serif !important;
font-size: 0.78rem !important; color: #7AB8A8 !important;
margin: 0 0 0.8rem !important; line-height: 1.5;
}}
.sn-row {{
display: grid; grid-template-columns: 90px 1fr;
align-items: center; gap: 0.7rem;
padding: 0.38rem 0; border-top: 1px solid rgba(255,255,255,0.04);
}}
.sn-row:first-of-type {{ border-top: none; }}
.sn-lbl {{
display: flex; align-items: center; gap: 0.38rem;
font-family: 'DM Sans', sans-serif !important;
font-size: 0.82rem; font-weight: 500; color: #C7F2E8 !important;
}}
.sn-nm {{ color: #C7F2E8 !important; }}
.sn-track {{
position: relative; height: 8px;
background: rgba(255,255,255,0.05); border-radius: 999px;
}}
.sn-fill {{
position: absolute; left: 0; top: 0; bottom: 0;
width: var(--bw); background: var(--bc);
border-radius: 999px; opacity: 0.82;
}}
.sn-ping {{
position: absolute; top: 50%; left: var(--bw);
transform: translate(-50%,-50%);
width: 9px; height: 9px; border-radius: 50%;
background: var(--bc); box-shadow: 0 0 7px 2px var(--bc);
}}
</style>
""")


# ============================================================
# FOOTER
# ============================================================
def render_footer() -> str:
    return _c("""
<div style="text-align:center;padding:2.2rem 0 1rem;
border-top:1px solid rgba(14,139,112,0.1);margin-top:2rem;">
<p style="font-family:'Space Mono',monospace!important;font-size:0.62rem;
letter-spacing:0.1em;color:#2D5E52!important;margin:0;">
HABITAT BENTIK · MobileNetV2 · Streamlit + TF + HF Hub</p>
</div>
""")
