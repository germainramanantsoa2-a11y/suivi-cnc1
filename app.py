import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import io

st.set_page_config(page_title="Suivi CNC", layout="wide", page_icon="🔧")

# --- CSS Custom ---
st.markdown("""
<style>
   .stButton > button {
        border-radius: 8px;
        background-color: #c70000;
        color: white;
        border: none;
    }
   .stButton > button:hover {
        background-color: #a00000;
        color: white;
    }
    h1 { color: #c70000; text-align: center; }
   .stExpander { border: 1px solid #ddd; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- Init session ---
if 'taches' not in st.session_state:
    st.session_state.taches = []
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'users' not in st.session_state:
    st.session_state.users = {"patron": "admin", "personnel": "1234"}

# --- Fonctions ---
def login():
    st.title("🔧 Connexion Suivi CNC")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        user = st.text_input("Utilisateur")
        pwd = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter", use_container_width=True):
            if user in st.session_state.users and st.session_state.users[user] == pwd:
                st.session_state.logged_in = True
                st.session_state.role = user
                st.rerun()
            else:
                st.error("Identifiants incorrects")

def export_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def filtrer_taches(df, periode):
    if df.empty: return df
    df['cree_le'] = pd.to_datetime(df['cree_le'])
    today = datetime.now().date()
    if periode == "Jour":
        return df[df['cree_le'].dt.date == today]
    elif periode == "Semaine":
        debut_semaine = today - timedelta(days=today.weekday())
        return df[df['cree_le'].dt.date >= debut_semaine]
    elif periode == "Mois":
        return df[df['cree_le'].dt.month == today.month]
    return df

# --- App principale ---
def main_app():
    st.title("Suivi des Tâches CNC")

    # Sidebar
    with st.sidebar:
        st.subheader(f"Connecté : {st.session_state.role}")

        st.divider()
        st.subheader("🌤️ Météo Antananarivo")
        try:
            data = requests.get("https://wttr.in/Antananarivo?format=j1", timeout=3).json()
            current = data['current_condition'][0]
            st.metric("Température", f"{current['temp_C']}°C")
            st.caption(current['weatherDesc'][0]['value'])
        except:
            st.info("Météo indisponible")

        st.divider()
        if st.session_state.role == "patron":
            with st.expander("⚙️ Changer mot de passe"):
                new_pwd = st.text_input("Nouveau mdp", type="password", key="newpwd")
                if st.button("Valider"):
                    st.session_state.users['patron'] = new_pwd
                    st.success("Mot de passe changé")

        if st.button("Déconnexion", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Patron : ajout tâches
    if st.session_state.role == "patron":
        with st.expander("➕ Ajouter une tâche", expanded=True):
            titre = st.text_input("Intitulé de la tâche")
            if st.button("Ajouter la tâche", use_container_width=True):
                if titre:
                    st.session_state.taches.append({
                        "titre": titre,
                        "cree_le": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "valide": False,
                        "valide_le": None
                    })
                    st.success(f"Tâche '{titre}' ajoutée")
                    st.rerun()

    # Filtres + Export
    st.subheader("Liste des tâches")
    col1, col2, col3 = st.columns([2,2,2])
    with col1:
        filtre_periode = st.selectbox("Période", ["Tout", "Jour", "Semaine", "Mois"])
    with col2:
        filtre_statut = st.selectbox("Statut", ["Toutes", "À faire", "Validées"])

    df = pd.DataFrame(st.session_state.taches)
    if not df.empty:
        df_filtre = filtrer_taches(df, filtre_periode)
        if filtre_statut == "À faire":
            df_filtre = df_filtre[df_filtre['valide'] == False]
        elif filtre_statut == "Validées":
            df_filtre = df_filtre[df_filtre['valide'] == True]
    else:
        df_filtre = df

    with col3:
        st.download_button(
            "📥 Export CSV",
            export_csv(df_filtre),
            f"taches_cnc_{datetime.now().date()}.csv",
            "text/csv",
            use_container_width=True
        )

    # Affichage tâches
    if not df_filtre.empty:
        for i, tache in df_filtre.iterrows():
            col1, col2 = st.columns([5,1])
            with col1:
                if tache['valide']:
                    st.success(f"✅ **{tache['titre']}** \nValidé le {tache['valide_le']} | Créé le {tache['cree_le']}")
                else:
                    st.warning(f"⏳ **{tache['titre']}** \nCréé le {tache['cree_le']}")
            with col2:
                if st.session_state.role == "personnel" and not tache['valide']:
                    if st.button("Valider", key=f"val_{i}", use_container_width=True):
                        idx_original = df[df['titre'] == tache['titre']].index[0]
                        st.session_state.taches[idx_original]['valide'] = True
                        st.session_state.taches[idx_original]['valide_le'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.rerun()
                if st.session_state.role == "patron":
                    if st.button("🗑️", key=f"del_{i}"):
                        idx_original = df[df['titre'] == tache['titre']].index[0]
                        st.session_state.taches.pop(idx_original)
                        st.rerun()
            st.divider()
    else:
        st.info("Aucune tâche pour les filtres sélectionnés")

# --- Run ---
if not st.session_state.logged_in:
    login()
else:
    main_app()
