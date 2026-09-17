import streamlit as st
from huggingface_hub import InferenceClient

# 1. Configuration de la page et du look ChatGPT/Gemini
st.set_page_config(
    page_title="Yagami AI", 
    page_icon="🚀", 
    layout="centered"
)

# Ton mot de passe secret pour bloquer l'accès
MOT_DE_PASSE_SECRET = "Yagami241"

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
            st.error("Code d'accès incorrect. Contactez le propriétaire pour obtenir votre code.")
            
    st.markdown("""
        <div style='text-align: center; margin-top: 5vh; padding: 15px; background-color: #1e1f20; border-radius: 8px;'>
            <p style='margin: 0; color: #f0f4f9;'><b>Comment obtenir un code ?</b></p>
            <p style='margin: 5px 0 0 0; color: #8e9196; font-size: 0.9rem;'>Envoyez votre paiement par Mobile Money (Airtel/Moov) puis contactez le support.</p>
        </div>
    """, unsafe_allow_html=True)

# --- INTERFACE DE CHAT (SI DÉBLOQUÉ) ---
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

            /* --- Animation d'apparition fluide des messages --- */
            @keyframes fadeSlideIn {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }
            div[data-testid="stChatMessage"] {
                animation: fadeSlideIn 0.25s ease-out;
            }

            /* --- IA à gauche (par défaut) --- */
            div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
                flex-direction: row;
            }
            div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stChatMessageContent"] {
                text-align: left;
                background-color: #1e1f20;
                border-radius: 18px 18px 18px 4px;
                padding: 10px 15px;
                max-width: 80%;
            }

            /* --- Utilisateur à droite --- */
            div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
                flex-direction: row-reverse;
            }
            div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) div[data-testid="stChatMessageContent"] {
                text-align: right;
                background-color: #2b3a55;
                border-radius: 18px 18px 4px 18px;
                padding: 10px 15px;
                max-width: 80%;
                margin-left: auto;
            }
        </style>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if len(st.session_state.messages) == 0:
        st.markdown("<h1 style='text-align: center; margin-top: 5vh; font-size: 3rem; color: #f0f4f9;'>🚀 Yagami AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #8e9196;'>Pose-moi tes questions du quotidien ! Je suis opérationnel.</p>", unsafe_allow_html=True)

    # Affichage de l'historique
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Zone de saisie en bas
    if prompt := st.chat_input("Saisissez un message ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("*Yagami AI réfléchit...*")
            
            try:
                # Utilisation du client officiel Hugging Face (Ultra stable)
                client = InferenceClient(
                    model="Qwen/Qwen2.5-7B-Instruct",
                    token=st.secrets["HF_TOKEN"]
                )
                
                # Création de la réponse structurée en mode conversation
                reponse_complete = client.chat_completion(
                    messages=[
                        {"role": "system", "content": "Tu es Yagami AI, un assistant virtuel rapide de type ChatGPT ou Gemini. Tu réponds aux questions courantes de la vie de tous les jours de manière claire et concise en français."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=600
                )
                
                reponse_ia = reponse_complete.choices[0].message.content
                
            except Exception as e:
                reponse_ia = f"Erreur réelle : {e}"

            # Affichage de la réponse finale
            placeholder.markdown(reponse_ia)
            st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
