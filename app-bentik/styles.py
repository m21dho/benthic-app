"""
styles.py — Tema visual (CSS) + komponen HTML yang bisa dipakai ulang.
Tidak ada logika model/HF Hub di sini — murni presentasi.
"""
from config import CLASS_NAMES, CLASS_COLORS, CLASS_ICONS

# ============================================================
# CSS TEMA — terinspirasi gradasi permukaan laut menuju dasar laut
# ============================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

:root {
    --ocean-deep: #07212F;
    --ocean-mid: #0F3D52;
    --ocean-teal: #167F6B;
    --ocean-teal-light: #1D9E75;
    --coral: #D85A30;
    --sand: #E8C77A;
    --ink: #0B1E2D;
    --ink-soft: #51666C;
    --border-soft: rgba(11, 30, 45, 0.10);
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main .block-container { padding-top: 1.2rem; max-width: 880px; }

h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; color: var(--ink); }
h2 { font-size: 1.3rem !important; }
h3 { font-size: 1.08rem !important; }

/* ---------- Hero banner ---------- */
.bentik-hero {
    position: relative;
    border-radius: 18px;
    padding: 2.1rem 2rem 2.6rem;
    margin-bottom: 1.6rem;
    background: linear-gradient(165deg, #BFE6DD 0%, #2E8C82 38%, var(--ocean-mid) 72%, var(--ocean-deep) 100%);
    overflow: hidden;
    box-shadow: 0 10px 28px rgba(7, 33, 47, 0.18);
}
.bentik-hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.9rem;
    color: #FFFFFF;
    margin: 0 0 0.35rem 0;
    letter-spacing: -0.01em;
}
.bentik-hero-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    color: rgba(255,255,255,0.88);
    margin: 0 0 1.1rem 0;
    max-width: 520px;
    line-height: 1.55;
}
.bentik-badge-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.bentik-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(255,255,255,0.16);
    border: 1px solid rgba(255,255,255,0.28);
    border-radius: 999px;
    padding: 0.32rem 0.8rem;
    font-size: 0.82rem; font-weight: 500; color: #FFFFFF;
    backdrop-filter: blur(2px);
}

/* ---------- Generic card ---------- */
.bentik-card {
    border: 1px solid var(--border-soft);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    background: #FFFFFF;
}

/* ---------- Prediction result card ---------- */
.bentik-result {
    border-radius: 16px;
    padding: 1.5rem 1.6rem;
    margin: 0.6rem 0 1rem 0;
    display: flex; align-items: center; gap: 1.1rem;
    border: 1px solid var(--border-soft);
}
.bentik-result-icon { font-size: 2.1rem; line-height: 1; }
.bentik-result-label { font-size: 0.78rem; color: var(--ink-soft); font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; margin: 0; }
.bentik-result-class { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; margin: 0.1rem 0 0.5rem 0; }
.bentik-conf-text { font-size: 0.8rem; color: var(--ink-soft); margin-top: 0.3rem; font-weight: 500; }

/* ---------- Dataset status cards ---------- */
.bentik-status-grid { display: flex; gap: 0.75rem; flex-wrap: wrap; margin: 0.6rem 0 1rem 0; }
.bentik-status-card {
    flex: 1 1 150px; min-width: 140px;
    border-radius: 14px; padding: 0.95rem 1.05rem;
    border: 1px solid var(--border-soft);
}
.bentik-status-top { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem; }
.bentik-status-name { font-weight: 600; font-size: 0.88rem; color: var(--ink); }
.bentik-status-count { font-family: 'Space Grotesk', sans-serif; font-size: 1.55rem; font-weight: 700; margin: 0.1rem 0 0.45rem 0; color: var(--ink); }
.bentik-status-track { width: 100%; height: 7px; border-radius: 999px; background: rgba(11,30,45,0.08); overflow: hidden; margin-bottom: 0.4rem; }
.bentik-status-fill { height: 100%; border-radius: 999px; }
.bentik-status-label { font-size: 0.74rem; font-weight: 600; }

/* ---------- Footer ---------- */
.bentik-footer {
    text-align: center; color: var(--ink-soft); font-size: 0.82rem;
    padding: 1.2rem 0 0.4rem 0; border-top: 1px solid var(--border-soft); margin-top: 1.6rem;
}

/* ---------- Native widget tweaks ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 1.6rem; }
.stTabs [data-baseweb="tab"] { font-weight: 600; color: var(--ink-soft); }
.stTabs [aria-selected="true"] { color: var(--ocean-teal) !important; }
.stButton > button[kind="primary"] {
    background: var(--ocean-teal); border-color: var(--ocean-teal);
    border-radius: 10px; font-weight: 600;
}
.stButton > button[kind="primary"]:hover { background: var(--ocean-teal-light); border-color: var(--ocean-teal-light); }
[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid var(--border-soft);
    border-radius: 12px; padding: 0.7rem 0.9rem;
}
section[data-testid="stSidebar"] { background: #F4F8F7; }
</style>
"""


def _clean_html(html: str) -> str:
    """
    Hilangkan spasi di awal setiap baris.
    Penting: Markdown menganggap baris berawalan 4+ spasi sebagai code block
    (ditampilkan sebagai teks mentah, bukan dirender sebagai HTML). Semua
    fungsi render_* di bawah harus membungkus hasilnya dengan ini.
    """
    return "\n".join(line.strip() for line in html.strip().splitlines())


def render_hero(title: str, subtitle: str) -> str:
    """Hero banner dengan judul, subjudul, dan badge semua kelas."""
    badges = ""
    for cn in CLASS_NAMES:
        icon = CLASS_ICONS.get(cn, "•")
        badges += f'<span class="bentik-badge">{icon} {cn}</span>'

    return _clean_html(f"""
    <div class="bentik-hero">
        <p class="bentik-hero-title">{title}</p>
        <p class="bentik-hero-sub">{subtitle}</p>
        <div class="bentik-badge-row">{badges}</div>
    </div>
    """)


def render_prediction_card(pred_class: str) -> str:
    """Kartu hasil prediksi: ikon + nama kelas, tanpa skor confidence."""
    colors = CLASS_COLORS.get(pred_class, {"bg": "#F0F0F0", "accent": "#888", "text": "#333"})
    icon = CLASS_ICONS.get(pred_class, "•")

    return _clean_html(f"""
    <div class="bentik-result" style="background:{colors['bg']};">
        <div class="bentik-result-icon">{icon}</div>
        <div style="flex:1;">
            <p class="bentik-result-label">Hasil klasifikasi</p>
            <p class="bentik-result-class" style="color:{colors['text']};">{pred_class}</p>
        </div>
    </div>
    """)


def render_not_detected_card() -> str:
    """Kartu netral untuk kasus confidence di bawah threshold."""
    return _clean_html("""
    <div class="bentik-result" style="background:#EFEFEC;">
        <div class="bentik-result-icon">❓</div>
        <div style="flex:1;">
            <p class="bentik-result-label">Hasil klasifikasi</p>
            <p class="bentik-result-class" style="color:#3F3F3B;">Tidak terdeteksi</p>
            <div class="bentik-conf-text" style="color:#6B6B66;">
                Model tidak cukup yakin gambar ini termasuk salah satu kelas yang dikenali.
            </div>
        </div>
    </div>
    """)



def render_class_status_cards(counts: dict, minimum: int) -> str:
    """Grid kartu status jumlah citra per kelas vs minimum yang dibutuhkan."""
    cards = ""
    for cn in CLASS_NAMES:
        n = counts.get(cn, 0)
        colors = CLASS_COLORS.get(cn, {"bg": "#F0F0F0", "accent": "#888", "text": "#333"})
        icon = CLASS_ICONS.get(cn, "•")
        pct = max(0.0, min(1.0, n / minimum if minimum else 0)) * 100
        ok = n >= minimum
        status_text = "✅ Siap" if ok else f"Butuh {minimum - n} lagi"
        status_color = colors["accent"] if ok else "#A3431F"

        cards += f"""
        <div class="bentik-status-card" style="background:{colors['bg']};">
            <div class="bentik-status-top">
                <span>{icon}</span>
                <span class="bentik-status-name" style="color:{colors['text']};">{cn}</span>
            </div>
            <p class="bentik-status-count" style="color:{colors['text']};">{n}</p>
            <div class="bentik-status-track">
                <div class="bentik-status-fill" style="width:{pct:.1f}%; background:{colors['accent']};"></div>
            </div>
            <div class="bentik-status-label" style="color:{status_color};">{status_text}</div>
        </div>
        """
    return _clean_html(f'<div class="bentik-status-grid">{cards}</div>')


def render_footer(text: str) -> str:
    return f'<div class="bentik-footer">{text}</div>'
