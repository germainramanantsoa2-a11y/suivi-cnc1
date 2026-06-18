import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Tâches du jour", layout="centered")

# --- CSS simple ---
st.markdown("""
<style>
  .stButton > button {border-radius: 8px; width: 100%;}
    h1 {text-align: center; color: #2c3e50;}
</style>
""", unsafe_allow_html=True)

# --- Init ---
if 'taches' not in st.session_state:
    st.session_state.taches = []
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'role' not in st.session_state:
    st.session_state.role = None

# --- Login ---
def login():
    st.title("Connexion")
    user = st.text_input("Nom")
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Entrer"):
        if user == "patron" and pwd == "admin":
            st.session_state.logged_in = True
            st.session_state.role = "patron"
            st.rerun()
        elif user == "moi" and pwd == "1234":
            st.session_state.logged_in = True
            st.session_state.role = "moi"
            st.rerun()
        else:
            st.error("Mauvais identifiants")

# --- App ---
def app():
    st.title("📋 Tâches quotidiennes")

    with st.sidebar:
        st.write(f"Connecté : **{st.session_state.role}**")
        if st.button("Déconnexion"):
            st.session_state.logged_in = False
            st.rerun()

    # PATRON : ajoute des tâches
    if st.session_state.role == "patron":
        st.subheader("Ajouter une tâche")
        nouvelle_tache = st.text_input("Que faut-il faire aujourd'hui?")
        if st.button("Ajouter"):
            if nouvelle_tache:
                st.session_state.taches.append({
                    "tache": nouvelle_tache,
                    "fini_par_moi": False,
                    "valide_patron": False,
                    "date": datetime.now().strftime("%d/%m %H:%M")
                })
                st.rerun()

    # LISTE DES TÂCHES
    st.subheader("Liste du jour")

    if not st.session_state.taches:
        st.info("Aucune tâche pour l'instant")
    else:
        for i, t in enumerate(st.session_state.taches):
            col1, col2, col3 = st.columns([3,1,1])

            with col1:
                if t['valide_patron']:
                    st.success(f"✅ {t['tache']} - Validé")
                elif t['fini_par_moi']:
                    st.warning(f"⏳ {t['tache']} - En attente validation")
                else:
                    st.write(f"🔲 {t['tache']} - À faire")
                st.caption(f"Ajouté le {t['date']}")

            with col2:
                # TOI : tu coches quand t'as fini
                if st.session_state.role == "moi" and not t['fini_par_moi']:
                    if st.button("J'ai fini", key=f"fini_{i}"):
                        st.session_state.taches[i]['fini_par_moi'] = True
                        st.rerun()

            with col3:
                # PATRON : il valide
                if st.session_state.role == "patron" and t['fini_par_moi'] and not t['valide_patron']:
                    if st.button("Valider", key=f"val_{i}"):
                        st.session_state.taches[i]['valide_patron'] = True
                        st.rerun()

                # PATRON : il peut supprimer
                if st.session_state.role == "patron":
                    if st.button("🗑️", key=f"del_{i}"):
                        st.session_state.taches.pop(i)
                        st.rerun()
            st.divider()

# --- Run ---
if not st.session_state.logged_in:
    login()
else:
    app()
