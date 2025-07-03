import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
from mplsoccer import PyPizza, add_image, FontManager
import io
from urllib.request import urlopen

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
opponent = st.sidebar.text_input("Adversaire", "Real Madrid")
uploaded_image = st.sidebar.file_uploader("Téléverser une photo", type=["jpg", "png"])

if uploaded_image:
    player_img = Image.open(uploaded_image)
else:
    URL = "https://raw.githubusercontent.com/andrewRowlinson/mplsoccer-assets/main/fdj_cropped.png"
    player_img = Image.open(urlopen(URL))

# ---- Initialisation des groupes ----
group_titles = ["🎯 Attaque", "⚙️ Distribution", "🛡️ Défense"]
group_keys = ["attaque", "distribution", "defense"]

# Maintenant 6 métriques fixes par groupe (modifiable par utilisateur)
default_metrics = {
    "attaque": [
        "Non-Penalty Goals", "npxG", "xA",
        "Open Play Shot Creating Actions", "Penalty Area Entries", "Goals per 90"
    ],
    "distribution": [
        "Touches per Turnover", "Progressive Passes", "Progressive Carries",
        "Final 1/3 Passes", "Final 1/3 Carries", "Pass Completion %"
    ],
    "defense": [
        "pAdj Pressure Regains", "pAdj Tackles Made", "pAdj Interceptions",
        "Recoveries", "Aerial Win %", "Blocks"
    ]
}

if "grouped_metrics" not in st.session_state:
    st.session_state.grouped_metrics = default_metrics.copy()
else:
    # Si l'utilisateur a modifié la liste, on s'assure qu'il y a bien 6 par groupe, on complète ou coupe
    for key in group_keys:
        current = st.session_state.grouped_metrics.get(key, [])
        if len(current) < 6:
            # Complète avec les métriques par défaut pour atteindre 6
            addition = [m for m in default_metrics[key] if m not in current]
            st.session_state.grouped_metrics[key] = (current + addition)[:6]
        else:
            # Coupe à 6 si plus
            st.session_state.grouped_metrics[key] = current[:6]

# ---- Interface de saisie par groupe ----
st.header("📈 Valeurs des métriques")
values = []
params = []

for title, key in zip(group_titles, group_keys):
    st.subheader(title)

    metrics = st.session_state.grouped_metrics.get(key, [])
    cols = st.columns(6)  # 6 métriques fixes

    for i, metric in enumerate(metrics):
        new_name = cols[i].text_input(f"{title} Métrique {i+1}", value=metric, key=f"edit_{key}_{i}")
        if new_name != metric:
            st.session_state.grouped_metrics[key][i] = new_name
        params.append(st.session_state.grouped_metrics[key][i])

# Maintenant on demande les valeurs, 6 par groupe (ordre des params respecté)
values = []
for key in group_keys:
    metrics = st.session_state.grouped_metrics[key]
    cols_val = st.columns(6)
    for i, metric in enumerate(metrics):
        val = cols_val[i].number_input(
            f"Valeur pour {metric}",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=1.0,
            format="%.1f",
            key=f"{key}_val_{i}"
        )
        values.append(val)

if len(params) == 0:
    st.warning("Ajoute au moins une métrique pour générer le radar.")
    st.stop()

# ---- Couleurs dynamiques par groupe ----
def get_colors(n):
    c1 = ["#009688"] * 6  # 6 verts
    c2 = ["#FF5722"] * 6  # 6 orange
    c3 = ["#3F51B5"] * 6  # 6 bleu
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
    figsize=(8, 10),
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

fig.subplots_adjust(top=0.85)

# Titres et texte en haut
fig.text(0.515, 0.97, f"{player_name} - {team}", size=16,
         ha="center", fontproperties=font_bold.prop, color="#FFFFFF")
fig.text(0.515, 0.940, f"Statistique Générale | Saison {season} | Vs: {opponent}",
         size=13, ha="center", fontproperties=font_bold.prop, color="#AAAAAA")

# Catégories et légendes couleurs plus bas
fig.text(0.320, 0.88, "Attaque", size=12,
         fontproperties=font_bold.prop, color="#009688")
fig.text(0.475, 0.88, "Distribution", size=12,
         fontproperties=font_bold.prop, color="#FF5722")
fig.text(0.64, 0.88, "Défense", size=12,
         fontproperties=font_bold.prop, color="#3F51B5")

x_positions = [0.28, 0.44, 0.60]
colors_for_rect = ["#009688", "#FF5722", "#3F51B5"]
for x, c in zip(x_positions, colors_for_rect):
    fig.patches.append(
        plt.Rectangle((x, 0.88), 0.030, 0.02, fill=True,
                      color=c, transform=fig.transFigure, figure=fig)
    )

# Image joueur plus bas
add_image(player_img, fig, left=0.448, bottom=0.416, width=0.13, height=0.127)

# Affichage Streamlit
st.pyplot(fig)

# Export JPG uniquement
jpg_buf = io.BytesIO()
fig.savefig(jpg_buf, format="jpg", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
jpg_buf.seek(0)
st.download_button(
    "📥 Télécharger le radar (JPG)",
    data=jpg_buf,
    file_name=f"{player_name}_radar.jpg",
    mime="image/jpeg"
)

# Affichage du créateur en bas à gauche
st.markdown(
    """
    <div style='position: fixed; bottom: 10px; left: 10px; color: #AAAAAA; font-size: 12px;'>
        Créé par <strong>Abbes Amine</strong>
    </div>
    """,
    unsafe_allow_html=True
)
