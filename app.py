import json
import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Ma Banque", page_icon="💳", layout="centered")


# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def charger_donnees():
    try:
        with open("identifiant.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def enregistrer_sous_json(compte_data):
    with open("identifiant.json", "w") as file:
        json.dump(compte_data, file, indent=4)


# Initialisation de l'état de session
if "compte" not in st.session_state:
    st.session_state.compte = charger_donnees()
if "utilisateur" not in st.session_state:
    st.session_state.utilisateur = None
if "mode" not in st.session_state:
    st.session_state.mode = "connexion"

compte = st.session_state.compte

# --- ÉCRAN DE CONNEXION / INSCRIPTION ---
if st.session_state.utilisateur is None:
    st.title("🏦 Ma Banque en Ligne")

    if st.session_state.mode == "connexion":
        st.subheader("Connexion à votre compte")
        identifiant = st.text_input("Identifiant")
        mot_de_passe = st.text_input("Mot de passe", type="password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Se connecter", use_container_width=True):
                if identifiant in compte:
                    # Vérifier si le compte est bloqué par l'admin
                    if compte[identifiant].get("bloque", False):
                        st.error("Ce compte a été bloqué par l'administrateur.")
                    elif mot_de_passe == compte[identifiant]["motdepasse"]:
                        st.session_state.utilisateur = identifiant
                        st.rerun()
                    else:
                        st.error("Identifiant ou mot de passe incorrect.")
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
        with col2:
            if st.button("Créer un compte", use_container_width=True):
                st.session_state.mode = "creation"
                st.rerun()

    else:
        st.subheader("Création d'un nouveau compte")
        n_identifiant = st.text_input("Nouvel Identifiant")
        n_mdp = st.text_input("Nouveau mot de passe", type="password")
        n_argent = st.number_input("Argent initial (€)", min_value=0, value=100)
        n_plafond = st.number_input("Plafond autorisé (€)", value=-500)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Valider la création", use_container_width=True):
                if n_identifiant and n_identifiant not in compte:
                    compte[n_identifiant] = {
                        "motdepasse": n_mdp,
                        "argent": int(n_argent),
                        "plafon": int(n_plafond),
                        "historique": ["Compte créé avec succès."],
                        "livret": 0,
                        "bloque": False  # Statut du blocage
                    }
                    enregistrer_sous_json(compte)
                    st.success("Compte créé avec succès ! Connectez-vous.")
                    st.session_state.mode = "connexion"
                    st.rerun()
                else:
                    st.error("Identifiant invalide ou déjà pris.")
        with col2:
            if st.button("Retour", use_container_width=True):
                st.session_state.mode = "connexion"
                st.rerun()

# --- ESPACE CLIENT (UNE FOIS CONNECTÉ) ---
else:
    user = st.session_state.utilisateur
    user_data = compte[user]

    st.sidebar.title(f"Bonjour, {user} 👋")

    options_menu = ["Accueil / Paiement", "Virements", "Historique", "Livret A", "Paramètres"]

    if user.lower() == "mathis":
        options_menu.append("Administration")

    menu = st.sidebar.radio("Navigation", options_menu)

    if st.sidebar.button("Se déconnecter"):
        st.session_state.utilisateur = None
        st.rerun()

    # 1. ACCUEIL
    if menu == "Accueil / Paiement":
        st.title("Tableau de bord")
        st.metric(label="Solde de votre compte", value=f"{user_data['argent']} €")

        st.divider()
        st.subheader("Effectuer un paiement")
        montant_paiement = st.number_input("Montant du paiement (€)", min_value=1, step=1)
        carte_bloquee = st.checkbox("Bloquer la carte bancaire")

        if st.button("Payer"):
            if carte_bloquee:
                st.error("Impossible d'effectuer le paiement : votre carte est bloquée !")
            elif montant_paiement > user_data["argent"]:
                st.error("Solde insuffisant.")
            elif (user_data["argent"] - montant_paiement) < user_data["plafon"]:
                st.error("Plafond de découvert atteint !")
            else:
                user_data["argent"] -= montant_paiement
                user_data["historique"].append(f"-{montant_paiement}€ (Paiement)")
                enregistrer_sous_json(compte)
                st.success(f"Paiement de {montant_paiement}€ effectué avec succès !")
                st.rerun()

    # 2. VIREMENTS
    elif menu == "Virements":
        st.title("💸 Faire un virement")
        destinataire = st.selectbox("Nom du destinataire", [u for u in compte.keys() if u != user])
        montant_virement = st.number_input("Montant du virement (€)", min_value=1, step=1)

        if st.button("Envoyer le virement"):
            if not destinataire:
                st.warning("Veuillez sélectionner un destinataire.")
            elif montant_virement > user_data["argent"]:
                st.error("Solde insuffisant.")
            else:
                user_data["argent"] -= montant_virement
                user_data["historique"].append(f"-{montant_virement}€ (Virement vers {destinataire})")

                compte[destinataire]["argent"] += montant_virement
                compte[destinataire]["historique"].append(f"+{montant_virement}€ (Virement de {user})")

                enregistrer_sous_json(compte)
                st.success(f"Virement de {montant_virement}€ vers {destinataire} réussi !")
                st.rerun()

    # 3. HISTORIQUE
    elif menu == "Historique":
        st.title("📜 Historique des transactions")
        for h in reversed(user_data["historique"]):
            st.write(f"- {h}")

    # 4. LIVRET A
    elif menu == "Livret A":
        st.title("💰 Livret A")
        st.metric(label="Épargne actuelle", value=f"{user_data['livret']} €")
        st.progress(min(user_data['livret'] / 24000, 1.0))

        somme_slider = st.slider("Montant à ajouter/enlever", 0, 1000, 100)

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Ajouter {somme_slider}€ au Livret"):
                if user_data["argent"] >= somme_slider:
                    user_data["argent"] -= somme_slider
                    user_data["livret"] += somme_slider
                    enregistrer_sous_json(compte)
                    st.success("Opération réussie !")
                    st.rerun()
                else:
                    st.error("Fonds insuffisants sur le compte courant.")
        with col2:
            if st.button(f"Retirer {somme_slider}€ du Livret"):
                if user_data["livret"] >= somme_slider:
                    user_data["livret"] -= somme_slider
                    user_data["argent"] += somme_slider
                    enregistrer_sous_json(compte)
                    st.success("Opération réussie !")
                    st.rerun()
                else:
                    st.error("Fonds insuffisants sur le livret A.")

    # 5. PARAMÈTRES
    elif menu == "Paramètres":
        st.title("⚙️ Paramètres")
        nouveau_mdp = st.text_input("Nouveau mot de passe", type="password")
        if st.button("Modifier le mot de passe"):
            if nouveau_mdp:
                user_data["motdepasse"] = nouveau_mdp
                enregistrer_sous_json(compte)
                st.success("Mot de passe mis à jour !")

    # 6. 👑 PANEL ADMINISTRATEUR (Réservé à Mathis)
    elif menu == "Administration":
        st.title("🛠️ Espace Administrateur")
        st.warning("Vous êtes connecté en tant qu'administrateur (Mathis).")

        st.subheader("Gestion des comptes utilisateurs")

        for pseudo, infos in list(compte.items()):
            with st.expander(f"Compte : {pseudo} {'🔒 [BLOQUÉ]' if infos.get('bloque', False) else ''}"):
                st.write(f"**Argent :** {infos['argent']} € | **Livret A :** {infos['livret']} €")
                st.write(f"**Mot de passe actuel :** {infos['motdepasse']}")

                # 1. Modifier le mot de passe d'un utilisateur
                nouveau_mdp_admin = st.text_input(f"Changer le mot de passe de {pseudo}", type="password",
                                                  key=f"pwd_{pseudo}")
                if st.button(f"Valider le nouveau mot de passe pour {pseudo}", key=f"btn_pwd_{pseudo}"):
                    if nouveau_mdp_admin:
                        compte[pseudo]["motdepasse"] = nouveau_mdp_admin
                        enregistrer_sous_json(compte)
                        st.success(f"Le mot de passe de {pseudo} a été modifié !")
                        st.rerun()

                st.divider()

                # 2. Bloquer ou Débloquer le compte
                est_bloque = infos.get("bloque", False)
                if est_bloque:
                    if st.button(f"🔓 Débloquer le compte de {pseudo}", key=f"unblock_{pseudo}"):
                        compte[pseudo]["bloque"] = False
                        enregistrer_sous_json(compte)
                        st.success(f"Le compte de {pseudo} a été débloqué.")
                        st.rerun()
                else:
                    if st.button(f"🔒 Bloquer le compte de {pseudo}", key=f"block_{pseudo}"):
                        compte[pseudo]["bloque"] = True
                        enregistrer_sous_json(compte)
                        st.warning(f"Le compte de {pseudo} a été bloqué.")
                        st.rerun()

                st.divider()

                # 3. Supprimer le compte (interdit de supprimer son propre compte admin)
                if pseudo.lower() == "mathis":
                    st.info("Vous ne pouvez pas supprimer votre propre compte administrateur.")
                else:
                    if st.button(f"❌ Supprimer définitivement le compte de {pseudo}", key=f"del_{pseudo}"):
                        del compte[pseudo]
                        enregistrer_sous_json(compte)
                        st.error(f"Le compte de {pseudo} a été supprimé.")
                        st.rerun()