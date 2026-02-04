import streamlit as st
import pandas as pd
from collections import defaultdict
import base64

# =========================
# CONFIG & STYLING
# =========================
st.set_page_config(
    page_title="Sistem Pakar VARK",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS untuk styling modern seperti di gambar
st.markdown("""
<style>
    /* Background gelap */
    .stApp {
        background-color: #0b1220;
    }
    
    /* Header styling */
    h1 {
        color: white !important;
        font-size: 3rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        color: #b6c2ff !important;
        font-size: 1.2rem !important;
        font-weight: 400 !important;
        margin-top: 0 !important;
    }
    
    h3 {
        color: white !important;
        font-size: 1.8rem !important;
    }
    
    /* Card styling */
    .stButton > button {
        width: 100%;
        background-color: #6366f1;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #4f46e5;
        transform: translateY(-2px);
    }
    
    /* Text styling */
    p, li {
        color: #cbd5e1 !important;
        font-size: 1.05rem !important;
    }
    
    /* Info box */
    .stAlert {
        background-color: #111a2e;
        border: 1px solid #1e293b;
        border-radius: 12px;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #6366f1;
    }
    
    /* Radio buttons */
    .stRadio > label {
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: #22c55e !important;
        font-size: 2rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #b6c2ff !important;
    }
    
    /* Success box */
    .success-box {
        background: linear-gradient(135deg, #111a2e 0%, #1e293b 100%);
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #334155;
        margin: 1rem 0;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: #111a2e;
        border: 2px dashed #334155;
        border-radius: 12px;
        padding: 2rem;
    }
    
    /* Divider */
    hr {
        border-color: #1e293b;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# DATA LOADER
# =========================
@st.cache_data
def load_dataset(csv_path):
    """Load dan parse dataset VARK"""
    df = pd.read_csv(csv_path)
    
    # Pisahkan data berdasarkan tipe
    gejala_df = df[df["tipe"] == "GEJALA"].copy()
    rules_df = df[df["tipe"] == "RULE"].copy()
    strategi_df = df[df["tipe"] == "STRATEGI"].copy()
    
    # Bersihkan NaN
    gejala_df = gejala_df.fillna("")
    rules_df = rules_df.fillna("")
    strategi_df = strategi_df.fillna("")
    
    # Parse gejala
    gejala_list = []
    for _, row in gejala_df.iterrows():
        gejala_list.append({
            "kode": str(row["kode_gejala"]).strip(),
            "pertanyaan": str(row["pertanyaan"]).strip(),
            "gaya": str(row["gaya_vark"]).strip(),
            "bobot": int(float(row["bobot"])) if str(row["bobot"]).strip() != "" else 1
        })
    
    # Parse rules
    rules_list = []
    for _, row in rules_df.iterrows():
        rules_list.append({
            "id": str(row["id"]).strip(),
            "gaya": str(row["gaya_vark"]).strip(),
            "conds": [
                str(row["rule_gejala_1"]).strip(),
                str(row["rule_gejala_2"]).strip(),
                str(row["rule_gejala_3"]).strip()
            ]
        })
    
    # Parse strategi
    strategi_map = {}
    for _, row in strategi_df.iterrows():
        gaya = str(row["gaya_vark"]).strip()
        strategi = str(row["strategi"]).strip()
        strategi_map[gaya] = strategi
    
    return gejala_list, rules_list, strategi_map

# =========================
# EXPERT SYSTEM LOGIC
# =========================
def evaluate_rules(rules_list, answered_yes):
    """Evaluasi rule yang terpenuhi"""
    matched = defaultdict(list)
    for r in rules_list:
        conds = [c for c in r["conds"] if c != ""]
        if conds and all(c in answered_yes for c in conds):
            matched[r["gaya"]].append(r["id"])
    return matched

# =========================
# CONSTANTS
# =========================
VARK_NAMES = {
    "V": "Visual",
    "A": "Auditory", 
    "R": "Read/Write",
    "K": "Kinesthetic"
}

VARK_ICONS = {
    "V": "👁️",
    "A": "👂",
    "R": "📖",
    "K": "🤸"
}

VARK_COLORS = {
    "V": "#f59e0b",
    "A": "#8b5cf6",
    "R": "#3b82f6",
    "K": "#10b981"
}

# =========================
# SESSION STATE INIT
# =========================
if "page" not in st.session_state:
    st.session_state.page = "upload"
if "dataset_loaded" not in st.session_state:
    st.session_state.dataset_loaded = False
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "scores" not in st.session_state:
    st.session_state.scores = {"V": 0, "A": 0, "R": 0, "K": 0}

# =========================
# PAGES
# =========================

def page_upload():
    """Halaman upload dataset"""
    # Header dengan icon
    col1, col2 = st.columns([1, 12])
    with col1:
        st.markdown("# 🌾")
    with col2:
        st.markdown("# Sistem Pakar Identifikasi Gaya Belajar VARK")
        st.markdown("## Menggunakan Metode Forward Chaining berbasis Kuesioner")
    
    st.markdown("---")
    
    # Info box
    st.info("""
    📋 **Tentang Aplikasi Ini:**
    
    Sistem pakar ini membantu mahasiswa mengetahui gaya belajar dominan mereka berdasarkan model VARK:
    - 👁️ **Visual**: Belajar dengan melihat (gambar, diagram, video)
    - 👂 **Auditory**: Belajar dengan mendengar (diskusi, audio, penjelasan lisan)
    - 📖 **Read/Write**: Belajar dengan membaca dan menulis
    - 🤸 **Kinesthetic**: Belajar dengan praktik langsung
    """)
    
    st.markdown("### 📁 Upload Dataset")
    st.markdown("Silakan upload file CSV dataset VARK atau gunakan dataset default")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Pilih file CSV dataset",
        type=["csv"],
        help="Upload file dataset_sistem_pakar_vark.csv"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Gunakan Dataset yang Diupload", disabled=(uploaded_file is None)):
            if uploaded_file:
                try:
                    # Simpan file
                    with open("dataset_temp.csv", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Load dataset
                    gejala, rules, strategi = load_dataset("dataset_temp.csv")
                    
                    st.session_state.gejala_list = gejala
                    st.session_state.rules_list = rules
                    st.session_state.strategi_map = strategi
                    st.session_state.dataset_loaded = True
                    st.session_state.page = "quiz"
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error loading dataset: {e}")
    
    with col2:
        if st.button("🎯 Mulai dengan Dataset Default"):
            st.session_state.use_default = True
            st.session_state.page = "quiz"
            st.rerun()

def page_quiz():
    """Halaman kuesioner"""
    # Load dataset (default atau uploaded)
    if not st.session_state.dataset_loaded:
        if hasattr(st.session_state, 'use_default') and st.session_state.use_default:
            # Gunakan dataset default dari uploads
            try:
                gejala, rules, strategi = load_dataset("/mnt/user-data/uploads/dataset_sistem_pakar_vark.csv")
                st.session_state.gejala_list = gejala
                st.session_state.rules_list = rules
                st.session_state.strategi_map = strategi
                st.session_state.dataset_loaded = True
            except:
                st.error("❌ Dataset default tidak ditemukan!")
                return
    
    gejala_list = st.session_state.gejala_list
    total_questions = len(gejala_list)
    current_idx = st.session_state.current_question
    
    # Header
    st.markdown("# 📝 Kuesioner Gaya Belajar VARK")
    st.markdown("## Jawab setiap pertanyaan sesuai dengan kebiasaan belajar Anda")
    
    # Progress
    progress = (current_idx) / total_questions
    st.progress(progress)
    st.markdown(f"**Pertanyaan {current_idx + 1} dari {total_questions}**")
    
    st.markdown("---")
    
    # Layout 2 kolom
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if current_idx < total_questions:
            current_item = gejala_list[current_idx]
            
            # Tampilkan pertanyaan
            st.markdown(f"### Pertanyaan {current_idx + 1}")
            st.markdown(f"**Kode:** `{current_item['kode']}`")
            st.markdown(f"**Gaya:** {VARK_ICONS.get(current_item['gaya'], '')} {VARK_NAMES.get(current_item['gaya'], '')}")
            
            st.markdown(f"## {current_item['pertanyaan']}")
            
            # Pilihan jawaban
            answer = st.radio(
                "Pilih jawaban Anda:",
                ["YA", "TIDAK"],
                key=f"q_{current_idx}",
                horizontal=True
            )
            
            st.markdown("---")
            
            col_back, col_next = st.columns(2)
            
            with col_back:
                if st.button("⬅️ Sebelumnya", disabled=(current_idx == 0)):
                    st.session_state.current_question -= 1
                    st.rerun()
            
            with col_next:
                if st.button("Selanjutnya ➡️"):
                    # Simpan jawaban
                    kode = current_item["kode"]
                    gaya = current_item["gaya"]
                    bobot = current_item["bobot"]
                    
                    is_yes = (answer == "YA")
                    st.session_state.answers[kode] = is_yes
                    
                    # Update skor
                    if is_yes:
                        st.session_state.scores[gaya] += bobot
                    
                    # Next question
                    if current_idx < total_questions - 1:
                        st.session_state.current_question += 1
                        st.rerun()
                    else:
                        # Selesai
                        st.session_state.page = "result"
                        st.rerun()
    
    with col2:
        # Skor sementara
        st.markdown("### 📊 Skor Sementara")
        
        for gaya in ["V", "A", "R", "K"]:
            score = st.session_state.scores[gaya]
            st.metric(
                label=f"{VARK_ICONS[gaya]} {VARK_NAMES[gaya]}",
                value=score
            )
        
        st.markdown("---")
        
        st.markdown("### ℹ️ Petunjuk")
        st.markdown("""
        - Jawab sesuai kebiasaan belajar Anda
        - Tidak ada jawaban benar/salah
        - Jawab sejujur-jujurnya
        - Sistem akan menghitung skor otomatis
        """)
        
        if st.button("🔄 Mulai Ulang", type="secondary"):
            st.session_state.current_question = 0
            st.session_state.answers = {}
            st.session_state.scores = {"V": 0, "A": 0, "R": 0, "K": 0}
            st.rerun()

def page_result():
    """Halaman hasil diagnosis"""
    # Evaluasi hasil
    answered_yes = {k for k, v in st.session_state.answers.items() if v}
    matched_rules = evaluate_rules(st.session_state.rules_list, answered_yes)
    
    # Tentukan gaya dominan
    max_score = max(st.session_state.scores.values()) if st.session_state.scores else 0
    dominant = [g for g, s in st.session_state.scores.items() if s == max_score and s > 0]
    
    if not dominant:
        dominant = ["V", "A", "R", "K"]
    
    # Header
    st.markdown("# 🎉 Hasil Diagnosis Gaya Belajar VARK")
    st.markdown("## Berikut adalah analisis gaya belajar Anda")
    
    st.markdown("---")
    
    # Skor final
    st.markdown("### 📊 Skor Akhir")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label=f"{VARK_ICONS['V']} Visual",
            value=st.session_state.scores['V']
        )
    
    with col2:
        st.metric(
            label=f"{VARK_ICONS['A']} Auditory",
            value=st.session_state.scores['A']
        )
    
    with col3:
        st.metric(
            label=f"{VARK_ICONS['R']} Read/Write",
            value=st.session_state.scores['R']
        )
    
    with col4:
        st.metric(
            label=f"{VARK_ICONS['K']} Kinesthetic",
            value=st.session_state.scores['K']
        )
    
    st.markdown("---")
    
    # Gaya dominan
    st.markdown("### 🏆 Gaya Belajar Dominan Anda")
    
    if len(dominant) == 1:
        gaya_utama = dominant[0]
        st.success(f"""
        **{VARK_ICONS[gaya_utama]} {VARK_NAMES[gaya_utama]}**
        
        Anda memiliki kecenderungan kuat pada gaya belajar **{VARK_NAMES[gaya_utama]}**.
        """)
    else:
        st.info(f"""
        **Kombinasi: {', '.join([VARK_ICONS[g] + ' ' + VARK_NAMES[g] for g in dominant])}**
        
        Anda memiliki gaya belajar yang seimbang dan bisa beradaptasi dengan berbagai metode pembelajaran.
        """)
    
    # Validasi rules
    st.markdown("### ✅ Validasi Rule (IF-THEN)")
    
    any_rule = False
    for g in ["V", "A", "R", "K"]:
        ids = matched_rules.get(g, [])
        if ids:
            any_rule = True
            st.markdown(f"**{VARK_ICONS[g]} {VARK_NAMES[g]}:** {', '.join(ids)}")
    
    if not any_rule:
        st.markdown("*(Tidak ada rule yang terpenuhi penuh. Hasil berdasarkan skor bobot)*")
    
    st.markdown("---")
    
    # Rekomendasi strategi
    st.markdown("### 💡 Rekomendasi Strategi Belajar")
    
    for i, gaya in enumerate(dominant):
        strategi = st.session_state.strategi_map.get(gaya, "-")
        
        with st.expander(f"{VARK_ICONS[gaya]} **{VARK_NAMES[gaya]}** - Klik untuk melihat strategi", expanded=(i==0)):
            st.markdown(strategi)
    
    st.markdown("---")
    
    # Tombol aksi
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Mulai Diagnosis Baru", type="primary"):
            # Reset semua
            st.session_state.current_question = 0
            st.session_state.answers = {}
            st.session_state.scores = {"V": 0, "A": 0, "R": 0, "K": 0}
            st.session_state.page = "quiz"
            st.rerun()
    
    with col2:
        if st.button("🏠 Kembali ke Halaman Utama"):
            st.session_state.page = "upload"
            st.session_state.dataset_loaded = False
            st.rerun()

# =========================
# MAIN APP ROUTER
# =========================
def main():
    """Main app router"""
    if st.session_state.page == "upload":
        page_upload()
    elif st.session_state.page == "quiz":
        page_quiz()
    elif st.session_state.page == "result":
        page_result()

if __name__ == "__main__":
    main()
