import streamlit as st
import requests

# 1. Configuration de la page (Design Sombre & Minimaliste style Gemini)
st.set_page_config(
    page_title="Yagami AI", 
    page_icon="🚀", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Style CSS personnalisé pour masquer les menus Streamlit et rendre la barre fixe en bas
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 2rem; padding-bottom: 7rem;}
        div[data-testid="stVerticalBlock"] > div:has(div.stChatInput) {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #131314;
            padding: 1.5rem 0;
            z-index: 99;
        }
        .stChatInput {max-width: 730px; margin: 0 auto;}
    </style>
""", unsafe_allow_html=True)

# 2. Écran d'accueil si aucune discussion n'a commencé
if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    st.markdown("<h1 style='text-align: center; margin-top: 5vh; font-size: 3rem; color: #f0f4f9;'>🚀 Yagami AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #8e9196; margin-bottom: 5vh;'>Comment puis-je t'aider aujourd'hui ?</p>", unsafe_allow_html=True)
else:
    st.markdown("<h3 style='color: #8e9196;'>🚀 Yagami AI</h3>", unsafe_allow_html=True)

# 3. Affichage de l'historique des messages à l'écran
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Zone de saisie utilisateur fixe en bas
if prompt := st.chat_input("Saisissez une invite ici..."):
    # Afficher le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Réponse de l'assistant Yagami AI
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("*Yagami AI réfléchit...*")
        
        try:
            # Reconnexion via l'API publique recommandée de Hugging Face (Modèle Qwen 2.5 robuste)
            API_URL = "https://huggingface.co"
            
            # Formatage strict pour éviter les bugs textuels ou balises brutes
            payload = {
                "inputs": f"<|im_start|>system\nTu es Yagami AI, un assistant virtuel de type ChatGPT ou Gemini. Tu réponds aux questions du quotidien avec précision, clarté et bienveillance. Écris en français courant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n",
                "parameters": {"max_new_tokens": 700, "return_full_text": False}
            }
            
            response = requests.post(API_URL, json=payload)
            data = response.json()
            
            # Extraction et nettoyage de la réponse textuelle
            if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
                reponse_ia = data[0]["generated_text"].strip()
            elif isinstance(data, dict) and "generated_text" in data:
                reponse_ia = data["generated_text"].strip()
            else:
                reponse_ia = "Désolé, mon système rencontre une forte affluence. Peux-tu réécrire ton message ?"
            
            # Nettoyage final des tags internes s'il y en a
            reponse_ia = reponse_ia.replace("<|im_end|>", "").replace("<|im_start|>", "")
            
        except Exception as e:
            reponse_ia = "Erreur technique temporaire. Vérifie la syntaxe de ton invite ou réessaie."

        # Affichage définitif de la réponse
        placeholder.markdown(reponse_ia)
        st.session_state.messages.append({"role": "assistant", "content": reponse_ia})

