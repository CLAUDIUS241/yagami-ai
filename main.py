import streamlit as st
import io
import base64
import time
import uuid
from huggingface_hub import InferenceClient

# 1. Configuration de la page
st.set_page_config(
    page_title="Yagami AI",
    page_icon="🚀",
    layout="centered"
)

# ============================================================
#  STYLES — interface façon "produit pro" (Gemini / ChatGPT)
# ============================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .block-container {padding-top: 1.2rem; padding-bottom: 7rem; max-width: 780px;}

        .stApp {
            background: radial-gradient(circle at 15% 10%, #1b1f3b 0%, #0d0e1a 55%, #050509 100%);
        }

        /* Zone de saisie fixée en bas */
        div[data-testid="stVerticalBlock"] > div:has(div.stChatInput) {
            position: fixed; bottom: 0; left: 0; right: 0;
            background: linear-gradient(180deg, rgba(5,5,9,0) 0%, #0a0a12 35%);
            padding: 1.5rem 0 1.2rem 0; z-index: 99;
        }
        .stChatInput {max-width: 730px; margin: 0 auto;}
        .stChatInput textarea, .stChatInput input {
            border-radius: 22px !important;
        }

        /* Boutons — look premium homogène */
        div[data-testid="stButton"] button {
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.09);
            background-color: rgba(255,255,255,0.04);
            color: #e6e6f0;
            transition: all 0.2s ease;
        }
        div[data-testid="stButton"] button:hover {
            background-color: rgba(127,90,240,0.22);
            border-color: #7f5af0;
            transform: translateY(-1px);
        }

        /* Bouton toggle tableau de bord — rond, discret */
        .toggle-dashboard-btn button {
            border-radius: 50% !important;
            width: 44px; height: 44px;
            font-size: 1.1rem;
            padding: 0 !important;
        }

        /* On désactive la flèche native de Streamlit pour éviter les conflits
           avec notre propre bouton d'affichage/masquage */
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }

        section[data-testid="stSidebar"] {
            background-color: #0d0e1a;
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        /* Écran d'accueil */
        .hero-title {
            background: linear-gradient(90deg, #7f5af0, #2cb67d, #7f5af0);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmer 5s linear infinite;
            text-align: center;
            font-weight: 700;
            font-size: 3rem;
            margin-top: 6vh;
            margin-bottom: 0.3rem;
        }
        @keyframes shimmer { to { background-position: 200% center; } }

        .hero-subtitle {
            text-align: center;
            color: #a0a3bd;
            font-size: 1.05rem;
            margin-bottom: 2.2rem;
        }

        /* Animation d'apparition des messages */
        @keyframes fadeSlideIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        div[data-testid="stChatMessage"] { animation: fadeSlideIn 0.3s ease-out; }

        /* IA à gauche */
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) { flex-direction: row; }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stChatMessageContent"] {
            text-align: left;
            background-color: #16172a;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 18px 18px 18px 4px;
            padding: 12px 16px;
            max-width: 80%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.35);
        }

        /* Utilisateur à droite */
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) { flex-direction: row-reverse; }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) div[data-testid="stChatMessageContent"] {
            text-align: right;
            background: linear-gradient(135deg, #4b3f8f, #2b3a75);
            border-radius: 18px 18px 4px 18px;
            padding: 12px 16px;
            max-width: 80%;
            margin-left: auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.35);
        }

        /* Indicateur "en train d'écrire" */
        .typing-indicator { display: flex; gap: 5px; padding: 4px 0; }
        .typing-indicator span {
            width: 8px; height: 8px; background-color: #8e9196; border-radius: 50%;
            animation: bounce 1.3s infinite ease-in-out both;
        }
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
            40% { transform: scale(1); opacity: 1; }
        }

        img { border-radius: 14px; }
    </style>
""", unsafe_allow_html=True)

# ============================================================
#  CONNEXION GOOGLE
# ============================================================
if not st.user.is_logged_in:
    st.markdown("<div class='hero-title'>🚀 Yagami AI</div>", unsafe_allow_html=True)
    st.markdown("<p class='hero-subtitle'>Connecte-toi avec Google pour commencer à discuter.</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if st.button("🔐 Se connecter avec Google", use_container_width=True):
            st.login("google")
    st.stop()

# ============================================================
#  ÉTAT DE L'APPLICATION
# ============================================================
if "conversations" not in st.session_state:
    premier_id = str(uuid.uuid4())
    st.session_state.conversations = {premier_id: {"titre": "Nouvelle conversation", "messages": []}}
    st.session_state.current_conv_id = premier_id

if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = True

if "image_a_modifier" not in st.session_state:
    st.session_state.image_a_modifier = None

if not st.session_state.show_dashboard:
    st.markdown("<style>section[data-testid='stSidebar']{display:none;}</style>", unsafe_allow_html=True)

# ============================================================
#  BOUTON D'AFFICHAGE / MASQUAGE DU TABLEAU DE BORD
# ============================================================
col_toggle, col_espace = st.columns([1, 9])
with col_toggle:
    st.markdown('<div class="toggle-dashboard-btn">', unsafe_allow_html=True)
    if st.button("☰", key="toggle_dashboard_btn"):
        st.session_state.show_dashboard = not st.session_state.show_dashboard
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
#  TABLEAU DE BORD (BARRE LATÉRALE)
# ============================================================
if st.session_state.show_dashboard:
    with st.sidebar:
        if st.user.get("picture"):
            st.image(st.user.picture, width=60)
        st.markdown(f"**{st.user.get('name', 'Utilisateur')}**")
        st.caption(st.user.get("email", ""))
        st.divider()

        if st.button("🆕 Nouvelle conversation", use_container_width=True, key="btn_nouvelle_conv"):
            nouvel_id = str(uuid.uuid4())
            st.session_state.conversations[nouvel_id] = {"titre": "Nouvelle conversation", "messages": []}
            st.session_state.current_conv_id = nouvel_id
            st.rerun()

        st.divider()
        st.markdown("**Historique**")

        for conv_id in reversed(list(st.session_state.conversations.keys())):
            conv = st.session_state.conversations[conv_id]
            est_active = (conv_id == st.session_state.current_conv_id)
            label = ("🟢 " if est_active else "💬 ") + conv["titre"]
            if st.button(label, key=f"conv_{conv_id}", use_container_width=True):
                st.session_state.current_conv_id = conv_id
                st.rerun()

        st.divider()
        if st.button("🚪 Se déconnecter", use_container_width=True, key="btn_logout"):
            st.logout()

# ============================================================
#  CONVERSATION ACTIVE
# ============================================================
conv_active = st.session_state.conversations[st.session_state.current_conv_id]
messages = conv_active["messages"]

# ============================================================
#  FONCTIONS UTILITAIRES
# ============================================================
MOTS_CLES_IMAGE = [
    "génère une image", "genere une image", "génère-moi une image", "genere moi une image",
    "dessine", "crée une image", "cree une image", "créer une image", "creer une image",
    "fais une image", "fait moi une image", "fais moi une image", "image de",
    "photo de", "génère la photo", "peux tu dessiner", "peux-tu dessiner", "illustre",
    "miniature", "thumbnail"
]

def est_demande_image(texte):
    texte_lower = texte.lower()
    return any(mot in texte_lower for mot in MOTS_CLES_IMAGE)

def ameliore_prompt_blox_fruits(prompt):
    """Enrichit automatiquement le prompt si la demande concerne Blox Fruits,
    pour obtenir un rendu façon miniature de jeu, cartoon 2D/3D dynamique."""
    texte_lower = prompt.lower()
    if "blox fruit" in texte_lower or "blox fruits" in texte_lower or "bloxfruit" in texte_lower:
        return (
            prompt +
            ", style miniature YouTube/Roblox Blox Fruits, rendu cartoon 3D dynamique et énergique, "
            "couleurs très vives et saturées, pose d'action épique, contours nets façon bande dessinée, "
            "éclairage dramatique et contrasté, composition centrée façon miniature de jeu, "
            "détails hybrides 2D/3D, ambiance électrisante, haute qualité"
        )
    return prompt

def traiter_message(prompt, image_jointe=None):
    """Gère l'envoi d'un message : texte, génération d'image, ou modification d'image."""
    if len(messages) == 0:
        conv_active["titre"] = prompt[:30] + ("..." if len(prompt) > 30 else "")

    messages.append({"role": "user", "content": prompt, "type": "text"})
    with st.chat_message("user"):
        st.markdown(prompt)
        if image_jointe:
            st.image(image_jointe, width=220)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(
            "<div class='typing-indicator'><span></span><span></span><span></span></div>",
            unsafe_allow_html=True
        )

        # --- MODIFICATION D'UNE IMAGE TÉLÉVERSÉE ---
        if image_jointe:
            try:
                client_img = InferenceClient(token=st.secrets["HF_TOKEN"], provider="auto")
                image_resultat = client_img.image_to_image(
                    image=image_jointe,
                    prompt=prompt,
                    model="black-forest-labs/FLUX.1-Kontext-dev"
                )
                buffer = io.BytesIO()
                image_resultat.save(buffer, format="PNG")
                img_b64 = base64.b64encode(buffer.getvalue()).decode()

                placeholder.empty()
                st.image(buffer.getvalue(), use_container_width=True)
                st.caption(f"🖌️ Modifiée : {prompt}")
                st.download_button(
                    "📥 Télécharger l'image", data=buffer.getvalue(),
                    file_name="yagami_ai_modifiee.png", mime="image/png",
                    key=f"dl_edit_{len(messages)}"
                )
                messages.append({
                    "role": "assistant", "content": img_b64, "type": "image",
                    "caption": f"Modifiée : {prompt}"
                })
            except Exception as e:
                erreur_msg = f"Désolé, je n'ai pas pu modifier l'image. Erreur réelle : {e}"
                placeholder.markdown(erreur_msg)
                messages.append({"role": "assistant", "content": erreur_msg, "type": "text"})

        # --- GÉNÉRATION D'UNE NOUVELLE IMAGE ---
        elif est_demande_image(prompt):
            try:
                prompt_final = ameliore_prompt_blox_fruits(prompt)
                client_img = InferenceClient(token=st.secrets["HF_TOKEN"], provider="auto")
                image = client_img.text_to_image(prompt_final, model="black-forest-labs/FLUX.1-schnell")
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                img_b64 = base64.b64encode(buffer.getvalue()).decode()

                placeholder.empty()
                st.image(buffer.getvalue(), use_container_width=True)
                st.caption(f"🎨 {prompt}")
                st.download_button(
                    "📥 Télécharger l'image", data=buffer.getvalue(),
                    file_name="yagami_ai_image.png", mime="image/png",
                    key=f"dl_new_{len(messages)}"
                )
                messages.append({
                    "role": "assistant", "content": img_b64, "type": "image", "caption": prompt
                })
            except Exception as e:
                erreur_msg = f"Désolé, je n'ai pas pu générer l'image. Erreur réelle : {e}"
                placeholder.markdown(erreur_msg)
                messages.append({"role": "assistant", "content": erreur_msg, "type": "text"})

        # --- RÉPONSE TEXTE ---
        else:
            try:
                client = InferenceClient(
                    model="meta-llama/Llama-3.1-8B-Instruct",
                    token=st.secrets["HF_TOKEN"],
                    provider="auto"
                )
                reponse_complete = client.chat_completion(
                    messages=[
                        {"role": "system", "content": (
                            "Tu es Yagami AI, un assistant virtuel rapide de type ChatGPT ou Gemini. "
                            "Tu réponds aux questions courantes de la vie de tous les jours de manière "
                            "claire et concise en français. Si on te demande qui t'a créé, qui est ton "
                            "créateur, ou à qui tu appartiens, réponds toujours que tu as été créé par "
                            "Yagami AI Corp, sans mentionner Hugging Face, Meta, Llama ni aucun autre "
                            "modèle ou entreprise sous-jacente."
                        )},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=600
                )
                reponse_ia = reponse_complete.choices[0].message.content
            except Exception as e:
                reponse_ia = f"Erreur réelle : {e}"

            affichage = ""
            mots = reponse_ia.split(" ")
            for i, mot in enumerate(mots):
                affichage += mot + " "
                if i % 2 == 0:
                    placeholder.markdown(affichage + "▌")
                    time.sleep(0.02)
            placeholder.markdown(reponse_ia)
            messages.append({"role": "assistant", "content": reponse_ia, "type": "text"})

# ============================================================
#  ÉCRAN D'ACCUEIL (si conversation vide)
# ============================================================
if len(messages) == 0:
    st.markdown("<div class='hero-title'>🚀 Yagami AI</div>", unsafe_allow_html=True)
    st.markdown(
        "<p class='hero-subtitle'>Discute, génère des images, ou modifie une photo que tu téléverses.</p>",
        unsafe_allow_html=True
    )

    suggestions = [
        "🎨 Dessine un chat astronaute",
        "🏝️ Miniature Blox Fruits épique",
        "❓ Explique-moi un sujet au choix"
    ]
    chip_cols = st.columns(3)
    for i, chip in enumerate(suggestions):
        with chip_cols[i]:
            if st.button(chip, use_container_width=True, key=f"chip_{i}"):
                traiter_message(chip.split(" ", 1)[1])

# ============================================================
#  AFFICHAGE DE L'HISTORIQUE DE LA CONVERSATION ACTIVE
# ============================================================
for idx, message in enumerate(messages):
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            image_bytes = base64.b64decode(message["content"])
            st.image(image_bytes, use_container_width=True)
            if message.get("caption"):
                st.caption(message["caption"])
            st.download_button(
                "📥 Télécharger l'image",
                data=image_bytes,
                file_name=f"yagami_ai_{idx}.png",
                mime="image/png",
                key=f"dl_hist_{st.session_state.current_conv_id}_{idx}"
            )
        else:
            st.markdown(message["content"])

# ============================================================
#  TÉLÉVERSEMENT D'IMAGE (+) — pour la modifier
# ============================================================
with st.popover("➕ Téléverser une image"):
    fichier = st.file_uploader(
        "Choisis une image à modifier", type=["png", "jpg", "jpeg"], key="uploader_image"
    )
    if fichier is not None:
        st.session_state.image_a_modifier = fichier.getvalue()
        st.success("Image prête ! Décris la modification à apporter dans le champ de discussion ci-dessous.")

if st.session_state.image_a_modifier:
    col_apercu, col_retirer = st.columns([1, 4])
    with col_apercu:
        st.image(st.session_state.image_a_modifier, width=90)
    with col_retirer:
        st.caption("Image en attente de modification")
        if st.button("✖ Retirer l'image", key="btn_retirer_image"):
            st.session_state.image_a_modifier = None
            st.rerun()

# ============================================================
#  ZONE DE SAISIE
# ============================================================
if prompt := st.chat_input("Écris un message, décris une image, ou une modification à apporter..."):
    image_en_attente = st.session_state.image_a_modifier
    st.session_state.image_a_modifier = None
    traiter_message(prompt, image_en_attente)
