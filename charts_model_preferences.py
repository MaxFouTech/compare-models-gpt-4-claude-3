import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sqlite3

# Connect to the database
conn = sqlite3.connect('db_compare_models.db')
# Fetch all rows from the new comparisons table
query = "SELECT * FROM comparison_gpt4_claude3"
comparisons_df = pd.read_sql_query(query, conn)
conn.close()

# Define a function to count preferences based on evaluation setup
def count_preferences(df, evaluator, bot_a, bot_b):
    # Filter based on evaluator and bot positions
    filtered_df = df[(df['model_evaluating'] == evaluator) & 
                     (df['model_bot_a'] == bot_a) & 
                     (df['model_bot_b'] == bot_b)]
    # Count the number of times each model is preferred
    preferences_count = filtered_df['preferred_answer'].value_counts()
    return [preferences_count.get('GPT-4', 0), preferences_count.get('Claude3', 0)]

# Prepare data for the pie charts based on specific conditions
conditions = [
    ('GPT-4', 'GPT-4', 'Claude3'),
    ('GPT-4', 'Claude3', 'GPT-4'),
    ('Claude3', 'GPT-4', 'Claude3'),
    ('Claude3', 'Claude3', 'GPT-4')
]

# Generate pie chart data based on conditions
pie_data = [count_preferences(comparisons_df, *cond) for cond in conditions]

# Titles for the pie charts
titles = [
    "GPT-4 Evaluation:\nComparing GPT-4 vs. Claude3\nNumbers indicate GPT-4's preference\nbetween its own and Claude3's answers.",
    "GPT-4 Evaluation:\nComparing Claude3 vs. GPT-4\nNumbers indicate GPT-4's preference\nbetween its own and Claude3's answers.",
    "Claude3 Evaluation:\nComparing GPT-4 vs. Claude3\nNumbers indicate Claude3's preference\nbetween its own and GPT-4's answers.",
    "Claude3 Evaluation:\nComparing Claude3 vs. GPT-4\nNumbers indicate Claude3's preference\nbetween its own and GPT-4's answers."
]

# Visualization with pie charts
fig, axs = plt.subplots(1, 4, figsize=(24, 6))  # Adjust the subplot layout

# Loop through each condition to create pie charts
for ax, data, title in zip(axs, pie_data, titles):
    ax.pie(data, labels=['GPT-4', 'Claude3'], autopct=lambda p: '{:.0f}\n({:.1f}%)'.format(p * sum(data) / 100, p) if p > 0 else '', startangle=90, colors=['#a8c2ba', '#c2896f'])
    ax.set_title(title)

# Calculate the total number of questions
total_questions = comparisons_df['question_id'].nunique()

# Add a boxed title within the plot area
fig.text(0.5, 0.90, f"Preference Evaluation between GPT-4 and Claude3: Each model blindly assesses answers from both, across a total of {total_questions} questions.",
         ha='center', va='top', fontsize=14, bbox=dict(facecolor='none', edgecolor='black', boxstyle='round,pad=1'))

plt.tight_layout()
plt.show()
