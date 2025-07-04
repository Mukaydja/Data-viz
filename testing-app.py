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

def prepare_circular_image(img, size_px=200):
    img = img.convert("RGBA")
    img.thumbnail((size_px, size_px), Image.LANCZOS)
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([(0, 0), img.size], fill=255)
    output = Image.new("RGBA", img.size)
    output.paste(img, (0, 0), mask=mask)
    return output

def smart_wrap_label(label, max_len=15):
    words = label.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + (1 if current_line else 0) <= max_len:
            if current_line != "":
                current_line += " "
            current_line += word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)

# Sidebar & theme
mode_display = st.sidebar.radio("Mode affichage", ["Desktop", "Mobile"], index=0, key="mode_display")
st.sidebar.markdown("🌓 **Apparence**")
theme_mode = st.sidebar.radio("Mode d'affichage", ["Clair", "Sombre"], index=1, key="theme_mode")

if theme_mode == "Clair":
    bg_color = "#FFFFFF"
    line_color = "#000000"
    text_default = "#000000"
else:
    bg_color = "#1E1E1E"
    line_color = "#FFFFFF"
    text_default = "#F2F2F2"

# Couleurs radar personnalisables
st.sidebar.markdown("🎨 **Couleurs radar**")
group_titles = ["🎯 Attaque", "⚙️ Distribution", "🛡️ Défense"]
group_keys = ["attaque", "distribution", "defense"]
default_colors = {"attaque": "#009688", "distribution": "#FF5722", "defense": "#3F51B5"}
group_colors = {k: st.sidebar.color_picker(f"{t} - Couleur", default_colors[k]) for k, t in zip(group_keys, group_titles)}
text_color = st.sidebar.color_picker("📝 Couleur du texte radar", value=text_default)
bg_color = st.sidebar.color_picker("🎆 Couleur de fond du radar", value=bg_color)

# Infos joueur
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

player_img_circular = prepare_circular_image(player_img, size_px=200)

# Métriques initiales
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

# Saisie des noms et notes manuelles (sans barre +/-)
params = []
values = []

st.header("📈 Valeurs des métriques")

if mode_display == "Desktop":
    nb_cols = 3
else:
    nb_cols = 1

for gkey, gtitle in zip(group_keys, group_titles):
    st.subheader(gtitle)
    cols = st.columns(nb_cols)
    metrics_list = grouped_metrics[gkey]
    for i, metric in enumerate(metrics_list):
        col_idx = i % nb_cols
        with cols[col_idx]:
            # Nom du critère modifiable sans affichage de (attaque_0)
            nom_critere = st.text_input(
                label="Nom du critère",
                value=metric,
                key=f"{gkey}_metric_{i}"
            )
            # Notes avec limites différentes selon groupe
            if gkey == "attaque":
                # Plage 0-25 float possible
                note_str = st.text_input(
                    label=f"Note pour « {nom_critere} » (0.0 à 25.0, décimal possible)",
                    value="12.5",
                    key=f"{gkey}_val_{i}"
                )
                try:
                    note_val = float(note_str.replace(",", "."))
                    if note_val < 0:
                        note_val = 0.0
                    elif note_val > 25:
                        note_val = 25.0
                except:
                    note_val = 12.5

            elif gkey == "distribution":
                # Plage 0-100 int uniquement
                note_str = st.text_input(
                    label=f"Note pour « {nom_critere} » (0 à 100, entier)",
                    value="50",
                    key=f"{gkey}_val_{i}"
                )
                try:
                    note_val = int(float(note_str))
                    if note_val < 0:
                        note_val = 0
                    elif note_val > 100:
                        note_val = 100
                except:
                    note_val = 50

            else:  # defense
                # Plage 0-50 int uniquement
                note_str = st.text_input(
                    label=f"Note pour « {nom_critere} » (0 à 50, entier)",
                    value="25",
                    key=f"{gkey}_val_{i}"
                )
                try:
                    note_val = int(float(note_str))
                    if note_val < 0:
                        note_val = 0
                    elif note_val > 50:
                        note_val = 50
                except:
                    note_val = 25

            params.append(nom_critere)
            values.append(note_val)

params_wrapped = [smart_wrap_label(param, max_len=15) for param in params]

slice_colors = (
    [group_colors["attaque"]] * 6 +
    [group_colors["distribution"]] * 6 +
    [group_colors["defense"]] * 6
)
text_colors = [text_color] * len(params_wrapped)

baker = PyPizza(
    params=params_wrapped,
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

group_names = ["Attaque", "Distribution", "Défense"]
positions = [0.30, 0.475, 0.64]
for gname, pos, gkey in zip(group_names, positions, group_keys):
    fig.text(pos, 0.88, gname, size=12, fontproperties=font_bold.prop, color=group_colors[gkey])
    fig.patches.append(
        plt.Rectangle((pos - 0.03, 0.88), 0.025, 0.02, fill=True,
                      color=group_colors[gkey], transform=fig.transFigure, figure=fig)
    )

add_image(player_img_circular, fig, left=0.448, bottom=0.416, width=0.13, height=0.127)

st.pyplot(fig)

# Téléchargement PNG
png_buf = io.BytesIO()
fig.savefig(png_buf, format="png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
png_buf.seek(0)
st.download_button("📥 Télécharger le radar (PNG)", data=png_buf, file_name=f"{player_name}_radar.png", mime="image/png")

# Crédit
st.markdown(
    """
    <div style='text-align: center; margin-top: 30px; font-size: 13px; color: gray;'>
        👨‍💻 Créé par <strong>Abbes Amine</strong>
    </div>
    """,
    unsafe_allow_html=True
)
