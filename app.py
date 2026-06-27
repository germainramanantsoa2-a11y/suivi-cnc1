import streamlit as st
import json
import os
import hashlib
import pandas as pd
from datetime import datetime, timedelta
import uuid

TASKS_FILE = "tasks.json"
USERS_FILE = "users.json"

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def load_users():
    # Utilise st.secrets si dispo, sinon valeurs par défaut
    try:
        DEFAULT_USERS = {
            "Germain": {"password": hash_password(st.secrets.passwords.germain), "role": "personnel", "name": "Germain"},
            "patron": {"password": hash_password(st.secrets.passwords.patron), "role": "patron", "name": "Patron"}
        }
    except:
        DEFAULT_USERS = {
            "Germain": {"password": hash_password("1234"), "role": "personnel", "name": "Germain"},
            "patron": {"password": hash_password("admin"), "role": "patron", "name": "Patron"}
        }

    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_USERS, f, indent=2, ensure_ascii=False)
        return DEFAULT_USERS
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else DEFAULT_USERS
    except:
        return DEFAULT_USERS

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except:
        return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

def login_page(users):
    st.title("🔐 Connexion Suivi Tâches Germain")
    username = st.text_input("Utilisateur")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter", type="primary"):
        if username in users and users[username]["password"] == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.session_state.name = users[username]["name"]
            st.rerun()
        else:
            st.error("Utilisateur ou mot de passe incorrect")

def get_status(v_me, v_boss):
    if v_me and v_boss: return "Validé ✅", "#28a745"
    elif v_me: return "En attente patron", "#fd7e14"
    elif v_boss: return "En attente personnel", "#fd7e14"
    return "À faire", "#dc3545"

def get_next_due_period(frequency):
    now = datetime.now()
    if frequency == "Jour":
        return (now + timedelta(days=1)).strftime("%d/%m/%Y")
    elif frequency == "Semaine":
        return (now + timedelta(weeks=1)).strftime("Semaine %W - %Y")
    elif frequency == "Mois":
        month = now.month + 1
        year = now.year
        if month > 12: month, year = 1, year + 1
        return datetime(year, month, 1).strftime("%B %Y")
    elif frequency == "Trimestre":
        quarter = (now.month - 1) // 3 + 1
        next_q = quarter % 4 + 1
        year = now.year if next_q > quarter else now.year + 1
        return f"T{next_q} {year}"
    return ""

st.set_page_config(page_title="Suivi Tâches Germain", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

users = load_users()

if not st.session_state.logged_in:
    login_page(users)
    st.stop()

# Sidebar
st.sidebar.write(f"Connecté : **{st.session_state.name}** | Rôle : **{st.session_state.role}**")
if st.sidebar.button("Déconnexion"):
    st.session_state.logged_in = False
    st.rerun()

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

st.title(f"📋 Suivi Tâches Germain")

# Ajout tâche = patron uniquement
if st.session_state.role == "patron":
    with st.expander("➕ Ajouter une nouvelle tâche", expanded=False):
        with st.form("add_task", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nom de la tâche *")
                batch = st.text_input("Lot / Machine", placeholder="Haas VF2, Imprimante Prusa...")
                frequency = st.selectbox("Fréquence", ["Unique", "Jour", "Semaine", "Mois", "Trimestre"])
            with col2:
                period = st.text_input("Période actuelle", placeholder="ex: 22/06, Semaine 25, Juin, T2")
                description = st.text_area("Description", height=80)
            if st.form_submit_button("Ajouter la tâche", type="primary") and name:
                new_task = {
                    "id": str(uuid.uuid4()), # ID unique pour chaque tâche
                    "name": name,
                    "batch": batch,
                    "frequency": frequency,
                    "period": period,
                    "description": description,
                    "validated_by_me": False,
                    "validated_by_boss": False,
                    "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "cache_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.tasks.append(new_task)
                save_tasks(st.session_state.tasks)
                st.success("Tâche ajoutée!")
                st.rerun()

st.divider()

# Filtres
col1, col2, col3 = st.columns([2,2,1])
with col1:
    filtre_freq = st.multiselect("Filtrer par fréquence", ["Unique", "Jour", "Semaine", "Mois", "Trimestre"],
                                 default=["Unique", "Jour", "Semaine", "Mois", "Trimestre"])
with col2:
    filtre_statut = st.multiselect("Filtrer par statut", ["À faire", "En attente patron", "En attente personnel", "Validé ✅"],
                                   default=["À faire", "En attente patron", "En attente personnel", "Validé ✅"])
with col3:
    if st.button("Exporter CSV") and st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger", csv, "suivi_taches.csv", "text/csv")

# Stats
if st.session_state.tasks:
    # Tri par date de création, plus récent en premier
    st.session_state.tasks.sort(key=lambda x: x['created_date'], reverse=True)

    tasks_filtrees = []
    for t in st.session_state.tasks:
        status, _ = get_status(t["validated_by_me"], t["validated_by_boss"])
        if t["frequency"] in filtre_freq and status in filtre_statut:
            tasks_filtrees.append(t)

    overdue = sum(1 for t in tasks_filtrees if not (t["validated_by_me"] and t["validated_by_boss"]))
    c1, c2, c3 = st.columns(3)
    c1.metric("Total tâches", len(tasks_filtrees))
    c2.metric("En attente", overdue)
    c3.metric("Validées", len(tasks_filtrees) - overdue)
else:
    tasks_filtrees = []

# Affichage tâches
for i, t in enumerate(tasks_filtrees):
    status, color = get_status(t["validated_by_me"], t["validated_by_boss"])

    # Container avec bordure colorée
    st.markdown(f"""<div style='border: 1px solid #ddd; border-left: 5px solid {color}; border-radius: 5px; padding: 10px; margin-bottom: 10px;'>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.markdown(f"### {t['name']}")
        batch_info = f" | **Lot:** {t['batch']}" if t.get('batch') else ""
        st.write(f"**{t['frequency']}** - {t['period']}{batch_info}")
        if t.get('description'):
            st.caption(t['description'])
        if t['frequency']!= "Unique":
            st.write(f"**Prochaine échéance:** {get_next_due_period(t['frequency'])}")
        st.caption(f"Créée le: {t['created_date']} | MAJ: {t['cache_date']}")

    with col2:
        # ID unique basé sur l'UUID de la tâche = bug fixé
        task_id = t.get('id', t['created_date'])

        if st.session_state.role == "personnel":
            me = st.checkbox("Je valide", value=t["validated_by_me"], key=f"me_{task_id}")
            st.checkbox("Validé par patron", value=t["validated_by_boss"], key=f"boss_{task_id}", disabled=True)
            if me!= t["validated_by_me"]:
                # Trouve la vraie tâche dans st.session_state.tasks via l'id
                for idx, task in enumerate(st.session_state.tasks):
                    if task.get('id') == t.get('id'):
                        st.session_state.tasks[idx]["validated_by_me"] = me
                        st.session_state.tasks[idx]["cache_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        break
                save_tasks(st.session_state.tasks)
                st.rerun()
        else: # patron
               st.checkbox("Validé par personnel", value=t["validated_by_me"], key=f"me_{task_id}", disabled=True)
    boss = st.checkbox("Je valide", value=t["validated_by_boss"], key=f"boss_{task_id}", disabled=not t["validated_by_me"])
    if boss!= t["validated_by_boss"]:
        for idx, task in enumerate(st.session_state.tasks):
            if task.get('id') == t.get('id'):
                if boss and t["frequency"]!= "Unique":
                    st.session_state.tasks[idx]["period"] = get_next_due_period(t["frequency"])
                    st.session_state.tasks[idx]["validated_by_me"] = False
                    st.session_state.tasks[idx]["validated_by_boss"] = False
                    new_period = st.session_state.tasks[idx]["period"]
                else:
                    st.session_state.tasks[idx]["validated_by_boss"] = boss
                st.session_state.tasks[idx]["cache_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        save_tasks(st.session_state.tasks)
        if boss and t["frequency"]!= "Unique":
            st.success(f"Tâche validée et reprogrammée pour {new_period}")
        else:
            st.success("Validation enregistrée")

                st.rerun()

        st.markdown(f"<span style='color:{color}; font-weight:bold;'>● {status}</span>", unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)                        

    with col3:
        if st.session_state.role == "patron":
            if st.button("🗑️ Supprimer", key=f"del_{task_id}", type="secondary"):
                st.session_state.tasks = [task for task in st.session_state.tasks if task.get('id')!= t.get('id')]
                save_tasks(st.session_state.tasks)
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
