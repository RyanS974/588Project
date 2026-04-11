import matplotlib.pyplot as plt
import numpy as np
import os

def create_qualitative_viz():
    # --- Data (Adjust these percentages based on your manual analysis) ---
    labels = [
        'Lacks meaningful\nfailure messages', 
        'Shallow assertions\n(e.g., isNotNull vs. state check)', 
        'Hallucinated\nmock objects'
    ]
    ai_freq = [75, 60, 25]     # Example % of AI tests exhibiting this issue
    human_freq = [15, 20, 0]   # Example % of Human tests exhibiting this issue

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    # --- Setup Plot ---
    fig, ax = plt.subplots(figsize=(10, 5.5))
    
    # Define colors (matching standard presentation palettes)
    ai_color = '#E66C37'      # Vibrant Orange/Red for AI issues
    human_color = '#118DFF'   # Professional Blue for Human baseline

    # Create horizontal bars
    rects1 = ax.barh(x + width/2, ai_freq, width, label='AI-Generated Tests', color=ai_color, alpha=0.85)
    rects2 = ax.barh(x - width/2, human_freq, width, label='Human-Written Tests', color=human_color, alpha=0.85)

    # --- Formatting ---
    ax.set_xlabel('Observed Frequency in PRs (%)', fontsize=12, fontweight='bold', color='#333333')
    ax.set_title('Qualitative Issues in Test Generation: AI vs. Human', fontsize=14, fontweight='bold', pad=20)
    
    ax.set_yticks(x)
    ax.set_yticklabels(labels, fontsize=11, fontweight='bold', color='#444444')
    ax.invert_yaxis()  # Labels read top-to-bottom
    
    ax.set_xlim(0, 100)
    ax.grid(axis='x', linestyle='--', alpha=0.4)
    
    # Remove top and right spines for a cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add legend
    ax.legend(loc='lower right', fontsize=11, framealpha=0.9)

    # Add percentage labels to the ends of the bars
    ax.bar_label(rects1, padding=5, fmt='%.0f%%', color=ai_color, fontweight='bold')
    ax.bar_label(rects2, padding=5, fmt='%.0f%%', color=human_color, fontweight='bold')

    fig.tight_layout()

    # --- Save Figure ---
    output_dir = "paper/figures"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "qualitative_insights.png")
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', transparent=True)
    print(f"Visualization successfully saved to: {output_path}")

if __name__ == "__main__":
    create_qualitative_viz()
