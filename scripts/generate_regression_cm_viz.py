import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

def create_regression_confusion_matrix_viz():
    # Confusion Matrix Data from validation
    # Actual: Regression (TP, FN), Actual: Normal (FP, TN)
    cm = np.array([[17, 6],   # Actual: Regression
                  [16, 11]]) # Actual: Normal
    
    labels = ['Regression', 'Normal']
    
    plt.figure(figsize=(8, 6))
    
    # Define custom annotations with labels (TP, FP, etc.)
    annot = [
        [f'TP: {cm[0,0]}', f'FN: {cm[0,1]}'],
        [f'FP: {cm[1,0]}', f'TN: {cm[1,1]}']
    ]
    
    # Use a nice color map
    sns.heatmap(cm, annot=annot, fmt='', cmap='Blues', 
                xticklabels=['Predicted: Regression', 'Predicted: Normal'],
                yticklabels=['Actual: Regression', 'Actual: Normal'],
                cbar=False, annot_kws={"size": 16, "weight": "bold"})
    
    plt.title('Confusion Matrix: Regression Test Detection Heuristic', fontsize=14, fontweight='bold', pad=20)
    plt.ylabel('Ground Truth', fontsize=12, fontweight='bold')
    plt.xlabel('Heuristic Prediction', fontsize=12, fontweight='bold')
    
    # --- Save Figure ---
    output_dir = "paper/figures"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "regression_confusion_matrix.png")
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', transparent=True)
    print(f"Visualization successfully saved to: {output_path}")

if __name__ == "__main__":
    create_regression_confusion_matrix_viz()
