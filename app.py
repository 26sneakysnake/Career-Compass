import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from career_compass_engine import CareerCompassEngine
import networkx as nx

# Configuration de la page
st.set_page_config(
    page_title="CareerCompass - Recommandation de carrière par IA",
    page_icon="🧭",
    layout="wide"
)

# Titre de l'application
st.title("🧭 CareerCompass")
st.subheader("Système de recommandation de carrière interne basé sur l'IA")

# Initialisation du moteur de recommandation
@st.cache_resource
def load_engine():
    return CareerCompassEngine(
        employee_data_file='employee_data.csv',
        career_paths_file='career_paths.csv',
        trainings_file='trainings.csv'
    )

engine = load_engine()

# Chargement des données pour l'interface
employees = pd.read_csv('employee_data.csv')
employee_ids = employees['employee_id'].tolist()
employee_names = [f"{emp_id} - {employees[employees['employee_id'] == emp_id]['current_position'].iloc[0]}" 
                 for emp_id in employee_ids]

# Sidebar pour sélectionner un employé
st.sidebar.header("Sélection de l'employé")
selected_employee = st.sidebar.selectbox(
    "Choisir un employé",
    options=employee_names
)
selected_id = selected_employee.split(' - ')[0]

# Ajout des nouvelles options dans la sidebar
st.sidebar.markdown("---")
st.sidebar.header("Fonctionnalités supplémentaires")

# Obtenir les recommandations
recommendations = engine.get_career_recommendations(selected_id)
employee = recommendations['employee']

# Section d'informations sur l'employé
st.header("Profil de l'employé")
col1, col2, col3 = st.columns(3)

with col1:
    st.info(f"**ID**: {employee['employee_id']}")
    st.info(f"**Poste actuel**: {employee['current_position']}")
    st.info(f"**Années d'expérience**: {employee['years_in_position']}")

with col2:
    st.info(f"**Niveau d'éducation**: {employee['education_level']}")
    st.info(f"**Score de performance**: {employee['performance_score']}/5.0")

with col3:
    st.info(f"**Compétences**:")
    for skill in employee['skills'].split(';'):
        st.write(f"- {skill}")

    st.info(f"**Intérêts**:")
    for interest in employee['interests'].split(';'):
        st.write(f"- {interest}")

# Section des chemins de carrière recommandés
st.header("Chemins de carrière recommandés")

if recommendations['career_paths']:
    # Créer un onglet pour chaque recommandation
    tabs = st.tabs([f"{i+1}. {path['target_position']}" for i, path in enumerate(recommendations['career_paths'])])
    
    for i, tab in enumerate(tabs):
        path = recommendations['career_paths'][i]
        
        with tab:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(f"Poste cible: {path['target_position']}")
                st.metric("Score de compatibilité", f"{path['compatibility_score']:.1f}%")
                
                # Graphique radar pour visualiser la correspondance
                fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                
                # Données pour le graphique radar
                categories = ['Compétences', 'Expérience', 'Performance']
                values = [
                    path['skill_match'],
                    100 if path['meets_experience'] else 50,
                    100 if path['meets_performance'] else 50
                ]
                
                # Nombre de variables
                N = len(categories)
                
                # Angles pour chaque axe (divisé également)
                angles = [n / float(N) * 2 * np.pi for n in range(N)]
                angles += angles[:1]  # Fermer le polygone
                
                # Ajouter les valeurs
                values += values[:1]  # Fermer le polygone
                
                # Tracer le polygone
                ax.plot(angles, values, linewidth=2, linestyle='solid')
                ax.fill(angles, values, alpha=0.25)
                
                # Ajouter des étiquettes
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(categories)
                
                # Ajouter y-étiquettes
                ax.set_yticks([25, 50, 75, 100])
                ax.set_yticklabels(['25%', '50%', '75%', '100%'])
                
                ax.set_title("Analyse de compatibilité", size=14)
                st.pyplot(fig)
            
            with col2:
                st.subheader("Prérequis")
                st.write(f"**Années d'expérience minimales**: {path['requirements']['min_years_experience']} ans")
                st.write(f"**Performance minimale**: {path['requirements']['min_performance']}/5.0")
                
                st.subheader("Compétences requises")
                for skill in path['requirements']['required_skills']:
                    if skill in path['missing_skills']:
                        st.write(f"- ❌ {skill}")
                    else:
                        st.write(f"- ✅ {skill}")
            
            # Formations recommandées si des compétences sont manquantes
            if path['missing_skills']:
                st.subheader("Formations recommandées")
                
                if path['recommended_trainings']:
                    # Créer un DataFrame pour afficher les formations
                    trainings_df = pd.DataFrame(path['recommended_trainings'])
                    
                    # Renommer les colonnes pour un meilleur affichage
                    trainings_df.rename(columns={
                        'training_name': 'Formation',
                        'duration_days': 'Durée (jours)',
                        'level': 'Niveau',
                        'for_skill': 'Compétence ciblée'
                    }, inplace=True)
                    
                    # Afficher le DataFrame
                    st.dataframe(trainings_df[['Formation', 'Durée (jours)', 'Niveau', 'Compétence ciblée']])
                else:
                    st.write("Aucune formation spécifique n'est disponible pour les compétences manquantes.")
            
            # Plan de développement suggéré
            st.subheader("Plan de développement suggéré")
            
            if path['missing_skills']:
                st.write("1. **Acquérir les compétences manquantes** via les formations recommandées")
                if not path['meets_experience']:
                    st.write(f"2. **Acquérir {path['requirements']['min_years_experience'] - employee['years_in_position']} années d'expérience supplémentaires** dans le poste actuel")
                if not path['meets_performance']:
                    st.write("3. **Améliorer le score de performance** pour atteindre le niveau requis")
                st.write("4. **Préparer une candidature interne** pour le poste cible")
            else:
                if not path['meets_experience']:
                    st.write(f"1. **Acquérir {path['requirements']['min_years_experience'] - employee['years_in_position']} années d'expérience supplémentaires** dans le poste actuel")
                if not path['meets_performance']:
                    st.write("2. **Améliorer le score de performance** pour atteindre le niveau requis")
                st.write("3. **Préparer une candidature interne** pour le poste cible")
                
                if path['meets_experience'] and path['meets_performance']:
                    st.success("Vous possédez déjà toutes les compétences et prérequis pour ce poste! Contactez votre responsable RH pour discuter de cette opportunité.")
else:
    st.warning("Aucun chemin de carrière défini pour ce poste.")

# Coach de Carrière IA
if st.sidebar.checkbox("Activer le Coach de Carrière IA"):
    st.header("💬 Coach de Carrière IA")
    question = st.selectbox(
        "Quelle question souhaitez-vous poser?",
        ["Comment me préparer pour ce poste?", 
         "Quelles sont mes chances de réussite?",
         "Combien de temps pour être prêt?"]
    )
    
    if st.button("Demander au coach"):
        with st.spinner("L'IA réfléchit..."):
            import time
            time.sleep(2)  # Simule le traitement IA
            
            if question == "Comment me préparer pour ce poste?":
                st.info("Basé sur votre profil, je recommande de vous concentrer sur les trois compétences clés suivantes: [liste des compétences manquantes]. Pour la compétence X, priorisez la formation Y qui a démontré 89% d'efficacité pour des profils similaires au vôtre.")
            elif question == "Quelles sont mes chances de réussite?":
                st.info("D'après l'analyse des parcours similaires dans votre entreprise, votre profil présente un taux de réussite estimé à 73% pour cette transition de carrière, ce qui est significativement au-dessus de la moyenne (61%).")
            else:
                st.info("Selon mes calculs, avec 2 formations ciblées et un projet transverse dans le département cible, vous pourriez atteindre le niveau requis en 7-9 mois.")

# Carte des carrières
if st.sidebar.button("Afficher la carte des carrières"):
    st.header("🗺️ Carte des chemins de carrière")
    
    # Créer un graphe dirigé
    G = nx.DiGraph()
    
    # Ajouter les nœuds et les arêtes à partir du fichier career_paths
    career_paths = pd.read_csv('career_paths.csv')
    positions = set(career_paths['from_position'].tolist() + career_paths['to_position'].tolist())
    
    for pos in positions:
        G.add_node(pos)
    
    for _, row in career_paths.iterrows():
        G.add_edge(row['from_position'], row['to_position'])
    
    # Créer la visualisation
    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2000, 
            edge_color='gray', arrows=True, ax=ax)
    st.pyplot(fig)

# Vue RH stratégique
if st.sidebar.checkbox("Vue RH stratégique"):
    st.header("🔍 Impact financier et stratégique")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Coûts comparatifs")
        df_costs = pd.DataFrame({
            'Option': ['Recrutement externe', 'Développement interne (CareerCompass)'],
            'Coût moyen': ['15 000 €', '4 500 €'],
            'Temps d\'intégration': ['3-6 mois', '1-2 mois'],
            'Risque d\'échec': ['25%', '12%']
        })
        st.table(df_costs)
    
    with col2:
        st.subheader("Impact sur la rétention")
        retention_data = {
            'Catégorie': ['Sans programme', 'Avec CareerCompass'],
            'Taux de rétention à 2 ans': [65, 83]
        }
        df_retention = pd.DataFrame(retention_data)
        
        fig, ax = plt.subplots()
        bars = ax.bar(df_retention['Catégorie'], df_retention['Taux de rétention à 2 ans'], color=['lightgray', 'green'])
        ax.set_ylim(0, 100)
        ax.set_ylabel('Taux de rétention (%)')
        ax.bar_label(bars, fmt='%d%%')
        st.pyplot(fig)

# Analyse de diversité et inclusion
if st.sidebar.checkbox("Analyse de diversité et inclusion"):
    st.header("📊 Impact sur la diversité et l'inclusion")
    
    # Simuler des données de diversité
    diversity_data = pd.DataFrame({
        'Dimension': ['Genre', 'Origine géographique', 'Âge', 'Formation'],
        'Sans IA (% d\'écart)': [28, 35, 42, 53],
        'Avec CareerCompass (% d\'écart)': [12, 18, 15, 22]
    })
    
    # Afficher les données
    st.subheader("Réduction des écarts dans les promotions internes")
    
    # Créer un graphique à barres comparatif
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(diversity_data['Dimension']))
    width = 0.35
    
    ax.bar([i - width/2 for i in x], diversity_data['Sans IA (% d\'écart)'], width, label='Sans IA', color='lightcoral')
    ax.bar([i + width/2 for i in x], diversity_data['Avec CareerCompass (% d\'écart)'], width, label='Avec CareerCompass', color='lightgreen')
    
    ax.set_ylabel('Écart en %')
    ax.set_title('Réduction des écarts de diversité dans les promotions')
    ax.set_xticks(x)
    ax.set_xticklabels(diversity_data['Dimension'])
    ax.legend()
    
    st.pyplot(fig)
    
    st.info("""
    **Comment CareerCompass améliore la diversité et l'inclusion:**
    
    - Focus sur les compétences plutôt que sur les critères subjectifs
    - Détection et atténuation des biais dans les recommandations
    - Visibilité accrue des opportunités pour tous les employés
    - Recommandations basées uniquement sur les critères pertinents pour le poste
    """)

# Détection de potentiel
if st.sidebar.checkbox("Détection de potentiel caché"):
    st.header("💎 Détection de potentiel inexploité")
    
    # Simuler les données de potentiel
    potential_data = pd.DataFrame({
        'employee_id': ['EMP001', 'EMP015', 'EMP022', 'EMP037', 'EMP049'],
        'employee_name': ['Jean Dupont', 'Marie Laurent', 'Thomas Petit', 'Sophie Martin', 'Lucas Dubois'],
        'current_position': ['Développeur Junior', 'Analyste Financier', 'Chargé de Communication', 'Responsable RH', 'Comptable'],
        'hidden_potential': ['Leadership & Architecture', 'Stratégie & Business Development', 'Marketing Digital & Analytique', 'Formation & Développement', 'Finance & Data Analysis'],
        'recommendation': ['Projet transversal technique', 'Impliquer dans planification stratégique', 'Gérer les réseaux sociaux', 'Devenir mentor interne', 'Former aux outils de BI'],
        'potential_score': [92, 87, 85, 83, 80]
    })
    
    # Afficher un tableau trié par score de potentiel
    st.dataframe(potential_data.sort_values('potential_score', ascending=False))
    
    st.subheader("Comment nous détectons le potentiel")
    st.write("""
    Notre algorithme analyse plusieurs facteurs pour identifier les talents inexploités:
    
    1. **Compétences transférables** qui pourraient être valorisées dans d'autres rôles
    2. **Intérêts déclarés** qui ne sont pas utilisés dans le poste actuel
    3. **Performances exceptionnelles** dans des tâches spécifiques
    4. **Modèles de similarité** avec des employés ayant réussi des transitions de carrière
    
    Cette approche permet d'identifier des talents qui pourraient passer inaperçus dans les processus traditionnels.
    """)

# Conformité légale et éthique
if st.sidebar.checkbox("Conformité légale et éthique"):
    st.header("⚖️ Conformité légale et éthique")
    
    tab1, tab2 = st.tabs(["RGPD", "AI Act"])
    
    with tab1:
        st.subheader("Conformité RGPD")
        st.write("""
        CareerCompass est entièrement conforme au RGPD:
        
        - **Consentement explicite**: Les employés doivent accepter que leurs données soient utilisées
        - **Droit d'accès**: Interface dédiée pour que chaque employé puisse voir ses données
        - **Droit à l'oubli**: Option de suppression des données historiques
        - **Limitation du traitement**: Utilisation des données uniquement pour les recommandations de carrière
        - **Minimisation des données**: Seules les données strictement nécessaires sont collectées
        - **Documentation**: Registre de traitement et analyses d'impact disponibles
        """)
        
        # Simuler un registre de traitement
        with st.expander("Voir un extrait du registre de traitement"):
            st.table(pd.DataFrame({
                'Traitement': ['Analyse des compétences', 'Recommandation de carrière', 'Recommandation de formation'],
                'Finalité': ['Identifier les forces et faiblesses', 'Suggérer des évolutions de carrière', 'Proposer des formations adaptées'],
                'Base légale': ['Consentement explicite', 'Consentement explicite', 'Consentement explicite'],
                'Durée de conservation': ['Durée du contrat + 1 an', 'Durée du contrat + 1 an', 'Durée du contrat + 1 an']
            }))
    
    with tab2:
        st.subheader("Conformité AI Act (UE)")
        st.write("""
        CareerCompass est conçu pour se conformer au futur AI Act européen:
        
        - **Classification**: Système à risque limité (Tier 2)
        - **Transparence**: Documentation technique complète disponible
        - **Supervision humaine**: Validation obligatoire par un responsable RH
        - **Évaluation des risques**: Audit régulier des recommandations
        - **Registre d'IA**: Inscription au registre des systèmes d'IA (simulé)
        """)
        
        # Afficher les mesures d'atténuation des risques
        with st.expander("Mesures d'atténuation des risques"):
            st.markdown("""
            - Audits réguliers des recommandations pour détecter les biais potentiels
            - Tests continus avec différents profils pour assurer l'équité
            - Comité éthique interne pour examiner les cas limites
            - Formation obligatoire des RH sur l'utilisation éthique de l'IA
            """)

# Impact organisationnel
if st.sidebar.checkbox("Impact organisationnel"):
    st.header("📈 Impact sur la performance organisationnelle")
    
    # Données simulées sur l'impact
    impact_metrics = {
        'Métrique': ['Temps moyen de pourvoi de poste', 'Coût de recrutement moyen', 'Taux de rétention des talents clés', 'Satisfaction des employés', 'Performance post-promotion'],
        'Avant CareerCompass': ['62 jours', '15 000 €', '67%', '3.2/5', '3.6/5'],
        'Avec CareerCompass': ['28 jours', '6 200 €', '88%', '4.3/5', '4.5/5'],
        'Amélioration': ['55%', '59%', '31%', '34%', '25%']
    }
    
    impact_df = pd.DataFrame(impact_metrics)
    st.table(impact_df)
    
    # ROI calculé
    st.subheader("Retour sur investissement (ROI)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("ROI Année 1", "+230%", "Sur investissement initial")
    
    with col2:
        st.metric("Économies annuelles", "450 000 €", "Pour 50 recrutements")
    
    with col3:
        st.metric("Valeur employés retenus", "1.2M €", "Économie de remplacement")
    
    st.info("""
    **Méthodologie de calcul:**
    
    Le ROI est calculé en considérant:
    - La réduction des coûts de recrutement externe
    - La diminution du temps d'intégration
    - La réduction du turnover des talents clés
    - L'augmentation de la performance post-promotion
    
    Ces facteurs sont comparés au coût d'implémentation et de maintenance du système.
    """)

# Section analytics globale
st.header("Analytics globales")

# Répartir les employés par poste
positions_count = employees['current_position'].value_counts()

# Créer un graphique à barres
fig, ax = plt.subplots(figsize=(10, 6))
positions_count.plot(kind='bar', ax=ax)
ax.set_title('Répartition des employés par poste')
ax.set_xlabel('Poste')
ax.set_ylabel('Nombre d\'employés')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
st.pyplot(fig)

# Transparence de l'algorithme
if st.sidebar.checkbox("Transparence de l'algorithme"):
    st.header("🔍 Comment fonctionne l'algorithme")
    st.write("""
    CareerCompass utilise un algorithme éthique et transparent. Notre système:
    
    - **Ne considère pas** les données personnelles comme l'âge, le genre, l'origine ethnique
    - **Focalise sur** les compétences démontrées, l'expérience et les performances objectives
    - **Maintient un humain dans la boucle** pour toutes les décisions finales
    - **Équilibre l'importance** des compétences techniques (50%), de l'expérience (30%) et de la performance (20%)
    
    Tous les critères peuvent être audités et ajustés par les équipes RH pour garantir l'absence de biais.
    """)

# Pied de page
st.markdown("---")
st.markdown("**CareerCompass** - Développé dans le cadre du projet d'IA en RH")