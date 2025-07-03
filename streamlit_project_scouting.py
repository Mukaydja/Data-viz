import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from mplsoccer import PyPizza, add_image, FontManager
from urllib.request import urlopen
import io

# Fonts
font_normal = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf')
font_bold = FontManager('https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf')

st.set_page_config(layout="wide")

# --- Fonction pour préparer image circulaire ---
def prepare_circular_image(img, size_px=200):
    img = img.convert("RGBA")
    img.thumbnail((size_px, size_px), Image.LANCZOS)

    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([(0, 0), img.size], fill=255)

    output = Image.new("RGBA", img.size)
    output.paste(img, (0, 0), mask=mask)
    return output

# --- Fonction pour faire un saut de ligne intelligent sur les noms de métriques ---
def split_label(label, max_len=12):
    if len(label) <= max_len:
        return label
    
    # Cherche un espace avant max_len (de droite à gauche)
    for i in range(max_len, 0, -1):
        if label[i] == " ":
            return label[:i] + "\n" + label[i+1:]
    # Sinon cherche un espace après max_len (de gauche à droite)
    for i in range(max_len, len(label)):
        if label[i] == " ":
            return label[:i] + "\n" + label[i+1:]
    
    # Pas d'espace proche, on ne coupe pas au milieu
    return label

# --- TITRE PERSONNALISÉ ---
st.sidebar.markdown("🌓 **Apparence**")
theme_mode = st.sidebar.radio("Mode d'affichage", ["Clair", "Sombre"], index=1)

# Thème
if theme_mode == "Clair":
    bg_color = "#FFFFFF"
    line_color = "#000000"
    text_default = "#000000"
else:
    bg_color = "#1E1E1E"
    line_color = "#FFFFFF"
    text_default = "#F2F2F2"

# Couleurs personnalisables
st.sidebar.markdown("🎨 **Couleurs radar**")
group_titles = ["🎯 Attaque", "⚙️ Distribution", "🛡️ Défense"]
group_keys = ["attaque", "distribution", "defense"]
default_colors = {"attaque": "#009688", "distribution": "#FF5722", "defense": "#3F51B5"}
group_colors = {k: st.sidebar.color_picker(f"{t} - Couleur", default_colors[k]) for k, t in zip(group_keys, group_titles)}
text_color = st.sidebar.color_picker("📝 Couleur du texte radar", value=text_default)
bg_color = st.sidebar.color_picker("🎆 Couleur de fond du radar", value=bg_color)

# --- INFOS JOUEUR ---
st.title("📊 Football Player Radar Generator")
st.sidebar.header("🎯 Infos joueur")
player_name = st.sidebar.text_input("Nom du joueur", "Frenkie de Jong")
team = st.sidebar.text_input("Club", "FC Barcelona")
season = st.sidebar.text_input("Saison", "2020-21")
opponent = st.sidebar.text_input("Adversaire", "Real Madrid")
uploaded_image = st.sidebar.file_uploader("📷 Photo du joueur", type=["jpg", "png"])

if uploaded_image:
    player_img = Image.open(uploaded_image)
else:
    URL = "https://raw.githubusercontent.com/andrewRowlinson/mplsoccer-assets/main/fdj_cropped.png"
    player_img = Image.open(urlopen(URL))

# Préparation image circulaire adaptée
player_img_circular = prepare_circular_image(player_img, size_px=200)

# --- MÉTRIQUES FIXES PAR GROUPE ---
grouped_metrics = {
    "attaque": [
        "Non-Penalty Goals", "npxG", "xA", "Shot Creating Actions", "Touches in Box", "Penalty Area Entries"
    ],
    "distribution": [
        "Touches per Turnover", "Progressive Passes", "Progressive Carries", "Final 1/3 Passes", "Final 1/3 Carries", "Pass Completion %"
    ],
    "defense": [
        "Pressure Regains", "Tackles Made", "Interceptions", "Recoveries", "Aerial Win %", "Blocks"
    ]
}

# --- SAISIE DES VALEURS ---
params = []
values = []

st.header("📈 Valeurs des métriques")
for title, key in zip(group_titles, group_keys):
    st.subheader(title)
    cols = st.columns(3)
    for i, metric in enumerate(grouped_metrics[key]):
        metric_name = cols[i % 3].text_input(f"{metric}", value=metric, key=f"{key}_metric_{i}")
        val = cols[i % 3].slider(f"Valeur {i+1}", 0.0, 100.0, 50.0, 1.0, key=f"{key}_val_{i}")
        # Appliquer saut de ligne intelligent sur le nom pour l'affichage
        params.append(split_label(metric_name))
        values.append(val)

# --- COULEURS SLICE ---
slice_colors = (
    [group_colors["attaque"]] * 6 +
    [group_colors["distribution"]] * 6 +
    [group_colors["defense"]] * 6
)
text_colors = [text_color] * len(params)

# --- GÉNÉRATION RADAR ---
baker = PyPizza(
    params=params,
    background_color=bg_color,
    straight_line_color=line_color,
    straight_line_lw=1,
    last_circle_color=line_color,
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
    kwargs_params=dict(color=text_color, fontsize=11, fontproperties=font_normal.prop, va="center"),
    kwargs_values=dict(
        color="#000000", fontsize=11, fontproperties=font_normal.prop, zorder=3,
        bbox=dict(edgecolor="#000000", facecolor="#FFFFFF", boxstyle="round,pad=0.2", lw=1)
    )
)

fig.subplots_adjust(top=0.85)
fig.text(0.515, 0.97, f"{player_name} - {team}", size=16, ha="center", fontproperties=font_bold.prop, color=text_color)
fig.text(0.515, 0.94, f"Statistiques Radar | Saison {season} | Vs: {opponent}", size=13, ha="center", fontproperties=font_bold.prop, color="#888888")

# Légendes de groupes
group_names = ["Attaque", "Distribution", "Défense"]
positions = [0.30, 0.475, 0.64]
for gname, pos, gkey in zip(group_names, positions, group_keys):
    fig.text(pos, 0.88, gname, size=12, fontproperties=font_bold.prop, color=group_colors[gkey])
    fig.patches.append(
        plt.Rectangle((pos - 0.03, 0.88), 0.025, 0.02, fill=True,
                      color=group_colors[gkey], transform=fig.transFigure, figure=fig)
    )

# Ajout de l'image circulaire du joueur dans le radar
add_image(player_img_circular, fig, left=0.448, bottom=0.416, width=0.13, height=0.127)

# --- AFFICHAGE ---
st.pyplot(fig)

# --- TÉLÉCHARGEMENT PNG ---
png_buf = io.BytesIO()
fig.savefig(png_buf, format="png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
png_buf.seek(0)
st.download_button("📥 Télécharger le radar (PNG)", data=png_buf, file_name=f"{player_name}_radar.png", mime="image/png")

# --- CRÉDIT ---
st.markdown(
    """
    <div style='text-align: center; margin-top: 30px; font-size: 13px; color: gray;'>
        👨‍💻 Créé par <strong>Abbes Amine</strong>
    </div>
    """,
    unsafe_allow_html=True
)
