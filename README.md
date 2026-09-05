# Ailment Discoverer 2.0: Machine Learning Diagnostic Engine

**Developer:** Muhammed Rehan C.K  
**Core Architecture:** Random Forest Classifier  
**Primary Libraries:** Python, Pandas, NumPy, Scikit-Learn  

## Project Overview
Ailment Discoverer 2.0 is a machine learning-based clinical diagnostic engine. Designed to move beyond basic conditional logic, this engine utilizes a Random Forest Classifier to analyze patient symptoms and output a probabilistic differential diagnosis for various infectious diseases (including Malaria, Dengue, and Typhoid). 

This repository currently houses the Minimum Viable Product (CLI version), which demonstrates the core machine learning architecture, data pipelines, and probability generation before the planned frontend web deployment.

## Technical Architecture
* **Algorithm:** Random Forest Classifier (Scikit-Learn).
* **Ensemble Learning:** The model is initialized with 100 decision trees (`n_estimators=100`) to mitigate overfitting and improve the generalization of the symptom data.
* **Probability Mapping:** Instead of returning a single binary prediction, the engine utilizes the `predict_proba` function to generate a multi-class probability matrix. This mimics real-world clinical differential diagnosis reporting by outputting confidence percentages.
* **Data Handling:** Pandas DataFrames are utilized to structure simulated clinical patient records, mapped against seven binary symptom features.

## Local Installation and Execution

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/ailment-discoverer.git](https://github.com/yourusername/ailment-discoverer.git)
   cd ailment-discoverer
