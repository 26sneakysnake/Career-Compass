import pandas as pd
import numpy as np

class CareerCompassEngine:
    def __init__(self, employee_data_file, career_paths_file, trainings_file):
        """
        Initialise le moteur de recommandation avec les fichiers de données
        """
        self.employees = pd.read_csv(employee_data_file)
        self.career_paths = pd.read_csv(career_paths_file)
        self.trainings = pd.read_csv(trainings_file)
        
    def get_employee_data(self, employee_id):
        """
        Récupère les données d'un employé spécifique
        """
        return self.employees[self.employees['employee_id'] == employee_id].iloc[0]
    
    def calculate_skill_match(self, employee_skills, required_skills):
        """
        Calcule le pourcentage de compétences requises que l'employé possède déjà
        """
        employee_skills_list = set(employee_skills.split(';'))
        required_skills_list = set(required_skills.split(';'))
        
        if not required_skills_list:
            return 0
        
        matching_skills = employee_skills_list.intersection(required_skills_list)
        return len(matching_skills) / len(required_skills_list) * 100
    
    def get_missing_skills(self, employee_skills, required_skills):
        """
        Identifie les compétences manquantes
        """
        employee_skills_list = set(employee_skills.split(';'))
        required_skills_list = set(required_skills.split(';'))
        
        return list(required_skills_list - employee_skills_list)
    
    def recommend_trainings(self, missing_skills):
        """
        Recommande des formations pour acquérir les compétences manquantes
        """
        recommended_trainings = []
        
        for skill in missing_skills:
            # Recherche des formations qui fournissent cette compétence
            for _, training in self.trainings.iterrows():
                if skill in training['skills_provided']:
                    recommended_trainings.append({
                        'training_id': training['training_id'],
                        'training_name': training['training_name'],
                        'duration_days': training['duration_days'],
                        'level': training['level'],
                        'for_skill': skill
                    })
        
        return recommended_trainings
    
    def get_career_recommendations(self, employee_id):
        """
        Génère des recommandations de carrière pour un employé spécifique
        """
        employee = self.get_employee_data(employee_id)
        
        # Filtrer les chemins de carrière possibles pour cet employé
        potential_paths = self.career_paths[self.career_paths['from_position'] == employee['current_position']]
        
        if potential_paths.empty:
            return {
                'employee': employee,
                'career_paths': [],
                'message': "Aucun chemin de carrière défini pour ce poste."
            }
        
        recommendations = []
        
        for _, path in potential_paths.iterrows():
            # Calculer le pourcentage de correspondance de compétences
            skill_match = self.calculate_skill_match(employee['skills'], path['required_skills'])
            
            # Vérifier les années d'expérience et la performance
            meets_experience = employee['years_in_position'] >= path['min_years_experience']
            meets_performance = employee['performance_score'] >= path['min_performance']
            
            # Calculer un score global de compatibilité
            compatibility_score = (
                skill_match * 0.5 +
                (100 if meets_experience else 50) * 0.3 +
                (100 if meets_performance else 50) * 0.2
            )
            
            # Identifier les compétences manquantes
            missing_skills = self.get_missing_skills(employee['skills'], path['required_skills'])
            
            # Recommander des formations pour les compétences manquantes
            training_recommendations = self.recommend_trainings(missing_skills)
            
            recommendations.append({
                'target_position': path['to_position'],
                'compatibility_score': compatibility_score,
                'skill_match': skill_match,
                'meets_experience': meets_experience,
                'meets_performance': meets_performance,
                'missing_skills': missing_skills,
                'recommended_trainings': training_recommendations,
                'requirements': {
                    'min_years_experience': path['min_years_experience'],
                    'min_performance': path['min_performance'],
                    'required_skills': path['required_skills'].split(';')
                }
            })
        
        # Trier par score de compatibilité
        recommendations.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        return {
            'employee': employee,
            'career_paths': recommendations
        }

# Exemple d'utilisation
if __name__ == "__main__":
    engine = CareerCompassEngine(
        employee_data_file='employee_data.csv',
        career_paths_file='career_paths.csv',
        trainings_file='trainings.csv'
    )
    
    # Obtenir des recommandations pour un employé
    recommendations = engine.get_career_recommendations('EMP001')
    
    # Afficher les résultats
    employee = recommendations['employee']
    print(f"Recommandations pour {employee['employee_id']} - {employee['current_position']}")
    print(f"Compétences actuelles: {employee['skills']}")
    print(f"Performance: {employee['performance_score']}")
    print(f"Années d'expérience: {employee['years_in_position']}")
    print("\nChemins de carrière recommandés:")
    
    for i, path in enumerate(recommendations['career_paths']):
        print(f"\n{i+1}. {path['target_position']} - Score de compatibilité: {path['compatibility_score']:.1f}%")
        print(f"   Match de compétences: {path['skill_match']:.1f}%")
        print(f"   Expérience requise: {path['meets_experience']} ({path['requirements']['min_years_experience']} ans minimum)")
        print(f"   Performance requise: {path['meets_performance']} ({path['requirements']['min_performance']} minimum)")
        
        if path['missing_skills']:
            print(f"   Compétences manquantes: {', '.join(path['missing_skills'])}")
            
            if path['recommended_trainings']:
                print("   Formations recommandées:")
                for training in path['recommended_trainings']:
                    print(f"      - {training['training_name']} ({training['duration_days']} jours) - pour acquérir {training['for_skill']}")