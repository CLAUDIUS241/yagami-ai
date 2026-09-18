import streamlit as st
import io
import base64
import time
import uuid
from huggingface_hub import InferenceClient

# 1. Configuration de la page et du look ChatGPT/Gemini
st.set_page_config(
    page_title="Yagami AI",
    page_icon="🚀",
    layout="centered"
)

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .block-container {padding-top: 2rem; padding-bottom: 7rem;}
        div[data-testid="stVerticalBlock"] > div:has(div.stChatInput) {
            position: fixed; bottom: 0; left: 0; right: 0;
            background-color: #131314; padding: 1.5rem 0; z-index: 99;
        }
        .stChatInput {max-width: 730px; margin: 0 auto;}

        /* --- Animation d'apparition fluide des messages --- */
        @keyframes fadeSlideIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        div[data-testid="stChatMessage"] {
            animation: fadeSlideIn 0.3s ease-out;
        }

        /* --- IA à gauche --- */
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
            flex-direction: row;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stChatMessageContent"] {
            text-align: left;
            background-color: #1e1f20;
            border-radius: 18px 18px 18px 4px;
            padding: 12px 16px;
            max-width: 80%;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }

        /* --- Utilisateur à droite --- */
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
            flex-direction: row-reverse;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) div[data-testid="stChatMessageContent"] {
            text-align: right;
            background-color: #2b3a55;
            border-radius: 18px 18px 4px 18px;
            padding: 12px 16px;
            max-width: 80%;
            margin-left: auto;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }

        /* --- Indicateur "en train d'écrire" façon Gemini --- */
        .typing-indicator {
            display: flex;
            gap: 5px;
            padding: 4px 0;
        }
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background-color: #8e9196;
            border-radius: 50%;
            animation: bounce 1.3s infinite ease-in-out both;
        }
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
            40% { transform: scale(1); opacity: 1; }
        }

        img { border-radius: 14px; }

        /* --- Bouton toggle tableau de bord --- */
        .toggle-dashboard-btn button {
            border-radius: 50%;
            width: 42px;
            height: 42px;
        }

        /* --- Historique dans le tableau de bord --- */
        .conv-item-active {
            background-color: #2b3a55 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONNEXION GOOGLE ---
# Nécessite : Authlib dans requirements.txt + un bloc [auth] et [auth.google]
# dans tes secrets Streamlit.
if not st.user.is_logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh; font-size: 3rem;'>🚀 Yagami AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8e9196;'>Connecte-toi avec Google pour commencer à discuter.</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔐 Se connecter avec Google", use_container_width=True):
            st.login("google")
    st.stop()

# --- INITIALISATION DES CONVERSATIONS ---
if "conversations" not in st.session_state:
    premier_id = str(uuid.uuid4())
    st.session_state.conversations = {
        premier_id: {"titre": "Nouvelle conversation", "messages": []}
    }
    st.session_state.current_conv_id = premier_id

if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = True

# Cache le tableau de bord si désactivé
if not st.session_state.show_dashboard:
    st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

# --- BOUTON POUR AFFICHER/MASQUER LE TABLEAU DE BORD ---
col_toggle, col_espace = st.columns([1, 9])
with col_toggle:
    st.markdown('<div class="toggle-dashboard-btn">', unsafe_allow_html=True)
    if st.button("☰"):
        st.session_state.show_dashboard = not st.session_state.show_dashboard
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- TABLEAU DE BORD (BARRE LATÉRALE) ---
if st.session_state.show_dashboard:
    with st.sidebar:
        if st.user.get("picture"):
            st.image(st.user.picture, width=60)
        st.markdown(f"**{st.user.get('name', 'Utilisateur')}**")
        st.caption(st.user.get("email", ""))
        st.divider()

        if st.button("🆕 Nouvelle conversation", use_container_width=True):
            nouvel_id = str(uuid.uuid4())
            st.session_state.conversations[nouvel_id] = {"titre": "Nouvelle conversation", "messages": []}
            st.session_state.current_conv_id = nouvel_id
            st.rerun()

        st.divider()
        st.markdown("**Historique**")

        # Affiche les conversations, la plus récente en premier
        for conv_id in reversed(list(st.session_state.conversations.keys())):
            conv = st.session_state.conversations[conv_id]
            est_active = (conv_id == st.session_state.current_conv_id)
            label = ("🟢 " if est_active else "") + conv["titre"]
            if st.button(label, key=f"conv_{conv_id}", use_container_width=True):
                st.session_state.current_conv_id = conv_id
                st.rerun()

        st.divider()
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.logout()

# --- RÉCUPÈRE LA CONVERSATION ACTIVE ---
conv_active = st.session_state.conversations[st.session_state.current_conv_id]
messages = conv_active["messages"]

if len(messages) == 0:
    st.markdown("<h1 style='text-align: center; margin-top: 5vh; font-size: 3rem; color: #f0f4f9;'>🚀 Yagami AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #8e9196;'>Pose-moi tes questions, ou demande-moi de générer une image !</p>", unsafe_allow_html=True)

# --- Affichage de l'historique de la conversation active ---
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

# --- Détection d'une demande de génération d'image ---
MOTS_CLES_IMAGE = [
    "génère une image", "genere une image", "génère-moi une image", "genere moi une image",
    "dessine", "crée une image", "cree une image", "créer une image", "creer une image",
    "fais une image", "fait moi une image", "fais moi une image", "image de",
    "photo de", "génère la photo", "peux tu dessiner", "peux-tu dessiner", "illustre"
]

def est_demande_image(texte):
    texte_lower = texte.lower()
    return any(mot in texte_lower for mot in MOTS_CLES_IMAGE)

# --- Zone de saisie en bas ---
if prompt := st.chat_input("Écris un message ou décris une image à générer..."):
    # Met à jour le titre de la conversation si c'est le premier message
    if len(messages) == 0:
        conv_active["titre"] = prompt[:30] + ("..." if len(prompt) > 30 else "")

    messages.append({"role": "user", "content": prompt, "type": "text"})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(
            "<div class='typing-indicator'><span></span><span></span><span></span></div>",
            unsafe_allow_html=True
        )

        if est_demande_image(prompt):
            # --- GÉNÉRATION D'IMAGE ---
            try:
                client_img = InferenceClient(token=st.secrets["HF_TOKEN"], provider="auto")
                image = client_img.text_to_image(
                    prompt,
                    model="black-forest-labs/FLUX.1-schnell"
                )
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                img_b64 = base64.b64encode(buffer.getvalue()).decode()

                placeholder.empty()
                st.image(buffer.getvalue(), use_container_width=True)
                st.caption(f"🎨 {prompt}")
                st.download_button(
                    "📥 Télécharger l'image",
                    data=buffer.getvalue(),
                    file_name="yagami_ai_image.png",
                    mime="image/png",
                    key=f"dl_new_{len(messages)}"
                )

                messages.append({
                    "role": "assistant",
                    "content": img_b64,
                    "type": "image",
                    "caption": prompt
                })
            except Exception as e:
                erreur_msg = f"Désolé, je n'ai pas pu générer l'image. Erreur réelle : {e}"
                placeholder.markdown(erreur_msg)
                messages.append({"role": "assistant", "content": erreur_msg, "type": "text"})

        else:
            # --- RÉPONSE TEXTE ---
            try:
                client = InferenceClient(
                    model="meta-llama/Llama-3.1-8B-Instruct",
                    token=st.secrets["HF_TOKEN"],
                    provider="auto"
                )

                reponse_complete = client.chat_completion(
                    messages=[
                        {"role": "system", "content": "Tu es Yagami AI, un assistant virtuel rapide de type ChatGPT ou Gemini. Tu réponds aux questions courantes de la vie de tous les jours de manière claire et concise en français. Si on te demande qui t'a créé, qui est ton créateur, ou à qui tu appartiens, réponds toujours que tu as été créé par Yagami AI Corp, sans mentionner Hugging Face, Meta, Llama ni aucun autre modèle ou entreprise sous-jacente."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=600
                )

                reponse_ia = reponse_complete.choices[0].message.content

            except Exception as e:
                reponse_ia = f"Erreur réelle : {e}"

            # Effet d'écriture progressive façon Gemini
            affichage = ""
            mots = reponse_ia.split(" ")
            for i, mot in enumerate(mots):
                affichage += mot + " "
                if i % 2 == 0:
                    placeholder.markdown(affichage + "▌")
                    time.sleep(0.02)
            placeholder.markdown(reponse_ia)

            messages.append({"role": "assistant", "content": reponse_ia, "type": "text"})
