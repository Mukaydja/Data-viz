import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
from mplsoccer import PyPizza, add_image, FontManager
import io
from fpdf import FPDF
from urllib.request import urlopen
import os

# Fonts
font_normal = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf')
font_italic = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Italic.ttf')
font_bold = FontManager('https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf')

st.set_page_config(layout="wide")
st.title("📊 Football Player Radar Generator")

# ---- Sidebar : infos joueur ----
st.sidebar.header("🎯 Infos joueur")
player_name = st.sidebar.text_input("Nom du joueur", "Frenkie de Jong")
team = st.sidebar.text_input("Club", "FC Barcelona")
season = st.sidebar.text_input("Saison", "2020-21")
uploaded_image = st.sidebar.file_uploader("Téléverser une photo", type=["jpg", "png"])

if uploaded_image:
    player_img = Image.open(uploaded_image)
else:
    URL = "https://raw.githubusercontent.com/andrewRowlinson/mplsoccer-assets/main/fdj_cropped.png"
    player_img = Image.open(urlopen(URL))

# ---- Initialisation des groupes ----
group_titles = ["🎯 Attaque", "⚙️ Distribution", "🛡️ Défense"]
group_keys = ["attacking", "possession", "defending"]

default_metrics = {
    "attacking": ["Non-Penalty Goals", "npxG", "xA", "Open Play Shot Creating Actions", "Penalty Area Entries"],
    "possession": ["Touches per Turnover", "Progressive Passes", "Progressive Carries", "Final 1/3 Passes", "Final 1/3 Carries"],
    "defending": ["pAdj Pressure Regains", "pAdj Tackles Made", "pAdj Interceptions", "Recoveries", "Aerial Win %"]
}

if "grouped_metrics" not in st.session_state:
    st.session_state.grouped_metrics = default_metrics.copy()

# ---- Interface de saisie par groupe ----
st.header("📈 Valeurs des métriques")
values = []
params = []

for title, key in zip(group_titles, group_keys):
    st.subheader(title)

    # Affichage + suppression possible des métriques dans ce groupe
    metrics_to_remove = None
    metrics_copy = st.session_state.grouped_metrics[key].copy()
    cols_del = st.columns(len(metrics_copy)*2 if metrics_copy else 1)

    for i, metric in enumerate(metrics_copy):
        # Affiche la métrique avec un champ éditable
        new_name = cols_del[2*i].text_input(f"{title} Métrique {i+1}", value=metric, key=f"edit_{key}_{i}")
        if new_name != metric:
            st.session_state.grouped_metrics[key][i] = new_name
        
        # Bouton suppression (unique, on mémorise l'indice)
        if cols_del[2*i+1].button("❌", key=f"del_{key}_{i}"):
            metrics_to_remove = i

    if metrics_to_remove is not None:
        st.session_state.grouped_metrics[key].pop(metrics_to_remove)
        st.experimental_rerun()

    # Inputs valeurs métriques
    cols_val = st.columns(3)
    for i, metric in enumerate(st.session_state.grouped_metrics[key]):
        val = cols_val[i % 3].number_input(
            metric,
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=1.0,
            format="%.1f",
            key=f"{key}_val_{i}"
        )
        values.append(val)
        params.append(metric)

    # Ajouter une nouvelle métrique à ce groupe
    new_metric = st.text_input(f"Ajouter une métrique à {title}", key=f"add_{key}")
    if st.button(f"➕ Ajouter à {title}", key=f"btn_add_{key}"):
        nm = new_metric.strip()
        all_metrics = sum(st.session_state.grouped_metrics.values(), [])
        if nm and nm not in all_metrics:
            st.session_state.grouped_metrics[key].append(nm)
            st.experimental_rerun()

if len(params) == 0:
    st.warning("Ajoute au moins une métrique pour générer le radar.")
    st.stop()

# ---- Couleurs dynamiques par groupe ----
def get_colors(n):
    c1 = ["#009688"] * min(5, n)
    c2 = ["#FF5722"] * min(5, max(0, n-5))
    c3 = ["#3F51B5"] * max(0, n-10)
    return (c1 + c2 + c3)[:n]

slice_colors = get_colors(len(params))
text_colors = ["#FFFFFF"] * len(params)

# ---- Génération radar ----
baker = PyPizza(
    params=params,
    background_color="#1E1E1E",
    straight_line_color="#FFFFFF",
    straight_line_lw=1,
    last_circle_color="#FFFFFF",
    last_circle_lw=1,
    other_circle_lw=0,
    inner_circle_size=20
)

fig, ax = baker.make_pizza(
    values,
    figsize=(8, 8.5),
    color_blank_space="same",
    slice_colors=slice_colors,
    value_colors=text_colors,
    value_bck_colors=slice_colors,
    blank_alpha=0.4,
    kwargs_slices=dict(edgecolor="#000000", zorder=2, linewidth=1),
    kwargs_params=dict(color="#F2F2F2", fontsize=11, fontproperties=font_normal.prop, va="center"),
    kwargs_values=dict(
        color="#000000", fontsize=11, fontproperties=font_normal.prop, zorder=3,
        bbox=dict(edgecolor="#000000", facecolor="#FFFFFF", boxstyle="round,pad=0.2", lw=1)
    )
)

# Titres et texte
fig.text(0.515, 0.975, f"{player_name} - {team}", size=16,
         ha="center", fontproperties=font_bold.prop, color="#FFFFFF")
fig.text(0.515, 0.955, f"Statistique Générale | Saison {season}",
         size=13, ha="center", fontproperties=font_bold.prop, color="#AAAAAA")
fig.text(0.99, 0.02, "Amine Abbes",
         size=9, fontproperties=font_italic.prop, color="#AAAAAA", ha="right")
fig.text(0.34, 0.93, "Attacking        Possession       Defending", size=14,
         fontproperties=font_bold.prop, color="#F2F2F2")

# Légendes couleurs
x_positions = [0.31, 0.462, 0.632]
colors_for_rect = ["#009688", "#FF5722", "#3F51B5"]
for x, c in zip(x_positions, colors_for_rect):
    fig.patches.append(plt.Rectangle((x, 0.9225), 0.025, 0.021, fill=True, color=c, transform=fig.transFigure, figure=fig))

# Ajouter image joueur
add_image(player_img, fig, left=0.4478, bottom=0.4315, width=0.13, height=0.127)

# Affichage Streamlit
st.pyplot(fig)

# --- Export PNG ---
png_buf = io.BytesIO()
fig.savefig(png_buf, format="png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
png_buf.seek(0)
st.download_button("📥 Télécharger le radar (PNG)", data=png_buf, file_name=f"{player_name}_radar.png", mime="image/png")

# --- Export PDF ---
fig.savefig("temp_radar.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", "B", 16)
pdf.cell(0, 10, f"{player_name} - {team}", ln=True, align="C")
pdf.image("temp_radar.png", x=10, y=30, w=190)

pdf_buf = io.BytesIO()
pdf.output("temp_radar.pdf")

with open("temp_radar.pdf", "rb") as f:
    pdf_buf.write(f.read())
pdf_buf.seek(0)

st.download_button("📄 Télécharger le radar (PDF)", data=pdf_buf, file_name=f"{player_name}_radar.pdf", mime="application/pdf")

# Nettoyage fichiers temporaires
if os.path.exists("temp_radar.png"):
    os.remove("temp_radar.png")
if os.path.exists("temp_radar.pdf"):
    os.remove("temp_radar.pdf")
