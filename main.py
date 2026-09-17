

import streamlit as st
import requests

# 1. Look du site style ChatGPT / Gemini
st.set_page_config(page_title="Yagami AI", page_icon="🚀", layout="centered")
st.title("🚀 Yagami AI")
st.write("Mon clone de ChatGPT rapide et gratuit !")

# Initialiser l'historique de discussion dans le navigateur
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher les anciens messages à l'écran
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 2. La barre de saisie en bas de l'écran
if prompt := st.chat_input("Posez votre question ici..."):
    # Afficher le message que tu viens de taper
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 3. Demander la réponse à l'IA en arrière-plan
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("*En train de réfléchir...*")
        
        try:
            # Connexion directe à l'IA gratuite de Qwen
            api_url = "https://huggingface.co"
            payload = {"inputs": prompt, "parameters": {"max_new_tokens": 500}}
            
            response = requests.post(api_url, json=payload).json()
            
            # Extraire la réponse proprement
            if isinstance(response, list) and "generated_text" in response[0]:
                reponse_ia = response[0]["generated_text"]
            else:
                reponse_ia = "Désolé, le serveur est un peu chargé. Réessaye !"
                
        except:
            reponse_ia = "Erreur de connexion avec l'IA."
            
        # Afficher la réponse finale de l'IA
        placeholder.markdown(reponse_ia)
        st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
