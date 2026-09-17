import streamlit as st
import requests

# 1. Configuration de la page
st.set_page_config(
    page_title="Yagami AI", 
    page_icon="🚀", 
    layout="centered"
)

# Ton mot de passe secret pour les clients
MOT_DE_PASSE_SECRET = "Yagami241"

# Vérification de la session
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False

# --- ÉCRAN D'ACCUEIL VERROUILLÉ ---
if not st.session_state.authentifie:
    st.markdown("<h1 style='text-align: center; margin-top: 10vh;'>🔒 Yagami AI Premium</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8e9196;'>Entrez votre code d'accès pour débloquer l'IA.</p>", unsafe_allow_html=True)
    
    code_entre = st.text_input("Code d'accès :", type="password")
    
    if st.button("Débloquer l'accès ➔"):
        if code_entre == MOT_DE_PASSE_SECRET:
            st.session_state.authentifie = True
            st.rerun()
        else:
            st.error("Code d'accès incorrect. Contactez le propriétaire pour acheter un accès.")
            
    st.markdown("""
        <div style='text-align: center; margin-top: 5vh; padding: 15px; background-color: #1e1f20; border-radius: 8px;'>
            <p style='margin: 0; color: #f0f4f9;'><b>Comment obtenir un code ?</b></p>
            <p style='margin: 5px 0 0 0; color: #8e9196; font-size: 0.9rem;'>Envoyez votre paiement par Mobile Money puis contactez le support WhatsApp.</p>
        </div>
    """, unsafe_allow_html=True)

# --- INTERFACE DE CHAT DU QUOTIDIEN (SI AUTHENTIFIÉ) ---
else:
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
            .block-container {padding-top: 2rem; padding-bottom: 7rem;}
            div[data-testid="stVerticalBlock"] > div:has(div.stChatInput) {
                position: fixed; bottom: 0; left: 0; right: 0;
                background-color: #131314; padding: 1.5rem 0; z-index: 99;
            }
            .stChatInput {max-width: 730px; margin: 0 auto;}
        </style>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if len(st.session_state.messages) == 0:
        st.markdown("<h1 style='text-align: center; margin-top: 5vh; font-size: 3rem; color: #f0f4f9;'>🚀 Yagami AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #8e9196;'>Pose-moi tes questions du quotidien ! Je suis prêt.</p>", unsafe_allow_html=True)

    # Affichage de la discussion
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Zone de saisie
    if prompt := st.chat_input("Saisissez un message ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("*Yagami AI réfléchit...*")
            
            try:
                # Utilisation d'un format de requête simplifié et universel
                API_URL = "https://huggingface.co"
                headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
                
                # Envoi simple du texte sans balises complexes
                payload = {
                    "inputs": prompt,
                    "parameters": {"max_new_tokens": 500}
                }
                
                response = requests.post(API_URL, headers=headers, json=payload)
                data = response.json()
                
                # Extraction sécurisée du texte retourné
                if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
                    reponse_ia = data[0]["generated_text"].strip()
                elif isinstance(data, dict) and "generated_text" in data:
                    reponse_ia = data["generated_text"].strip()
                else:
                    reponse_ia = "Mon système est surchargé. Réessaie ton message dans un instant !"
                
                # Éviter que l'IA ne répète la question de l'utilisateur
                if reponse_ia.startswith(prompt):
                    reponse_ia = reponse_ia[len(prompt):].strip()
                    
            except Exception as e:
                reponse_ia = "Erreur de connexion avec le serveur d'IA. Réessaye."

            # Affichage de la réponse à l'écran
            placeholder.markdown(reponse_ia)
            st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
