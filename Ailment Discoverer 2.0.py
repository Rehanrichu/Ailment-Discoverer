"""
AILMENT DISCOVERER 2.0: MACHINE LEARNING DIAGNOSTIC ENGINE
Developer: Muhammed Rehan C.K
Architecture: Random Forest Classifier using Scikit-Learn
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import warnings

warnings.filterwarnings('ignore')

print("---  INITIALIZING ML CLINICAL ENGINE  ---")

# 1. BUILD THE CLINICAL DATASET (Simulated Patient Records)
# Features: [high_fever, stomach_pain, headache, cough, chills, joint_pain, skin_rash]
# 1 = Symptom Present, 0 = Symptom Absent
data = {
    'high_fever':   [1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1],
    'stomach_pain': [1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
    'headache':     [1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1],
    'cough':        [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0],
    'chills':       [0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1],
    'joint_pain':   [0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],
    'skin_rash':    [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1],
    # Targets based on PCMB Biological definitions
    'disease': [
        'Typhoid', 'Typhoid', 'Common Cold', 'Malaria', 'Amoebiasis', 
        'Pneumonia', 'Dengue', 'Ringworms', 'Chikungunya', 'Typhoid',
        'Common Cold', 'Ringworms', 'Pneumonia', 'Typhoid', 'Dengue'
    ]
}

df = pd.DataFrame(data)

# 2. SPLIT DATA & TRAIN THE MODEL
X = df.drop('disease', axis=1) # Features (Symptoms)
y = df['disease']              # Target (Diagnosis)

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train Random Forest (Ensemble Learning)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate Baseline Accuracy
predictions = model.predict(X_test)
acc = accuracy_score(y_test, predictions)
print(f"✔️ Model Trained Successfully. Base Accuracy: {acc*100:.1f}%\n")

# 3. INTERACTIVE PATIENT INTERFACE
print("---  PATIENT SYMPTOM INTAKE  ---")
print("Answer 1 for YES, 0 for NO.\n")

symptoms = []
symptoms.append(int(input("Do you have a high fever (1/0)? ")))
symptoms.append(int(input("Do you have stomach pain (1/0)? ")))
symptoms.append(int(input("Do you have a headache (1/0)? ")))
symptoms.append(int(input("Do you have a cough (1/0)? ")))
symptoms.append(int(input("Do you feel chills (1/0)? ")))
symptoms.append(int(input("Do you have joint pain (1/0)? ")))
symptoms.append(int(input("Do you have a skin rash (1/0)? ")))

# Convert patient input to DataFrame for prediction
patient_data = pd.DataFrame([symptoms], columns=X.columns)

# 4. STATISTICAL DIAGNOSIS (Probability Output)
probabilities = model.predict_proba(patient_data)[0]
classes = model.classes_

print("\n---  DIFFERENTIAL DIAGNOSIS REPORT ---")
# Pair diseases with their calculated probabilities and sort them
results = sorted(zip(classes, probabilities), key=lambda x: x[1], reverse=True)

for disease, prob in results:
    if prob > 0:
        print(f" {disease}: {prob*100:.1f}% confidence")

print("\n MEDICAL DISCLAIMER: AI Diagnostic Probability Engine. Consult a certified GP.")