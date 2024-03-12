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

# Modified helper function to calculate average score for GPT-4 and Claude3 directly
def extract_specific_scores(df, evaluator):
    scores_gpt4 = df[df['model_evaluating'] == evaluator]['score_GPT4']
    scores_claude3 = df[df['model_evaluating'] == evaluator]['score_Claude3']
    return scores_gpt4.mean(), scores_claude3.mean()

# Since we're now directly using model scores, we simplify conditions
conditions = [
    ('GPT-4', 'GPT-4 Evaluation'),
    ('Claude3', 'Claude3 Evaluation'),
]

avg_scores_specific = {}
for evaluator, variable_prefix in conditions:
    score_gpt4_avg, score_claude3_avg = extract_specific_scores(comparisons_df, evaluator)
    avg_scores_specific[f"{variable_prefix}-score for GPT-4"] = score_gpt4_avg
    avg_scores_specific[f"{variable_prefix}-score for Claude3"] = score_claude3_avg

# Calculate the total average scores for GPT-4 and Claude3
total_scores_gpt4 = comparisons_df['score_GPT4'].mean()
total_scores_claude3 = comparisons_df['score_Claude3'].mean()

# Add to the conditions for plotting
conditions.append(('Total', 'Total Evaluation'))

# Add the total averages to the avg_scores_specific dictionary
avg_scores_specific['Total Evaluation-score for GPT-4'] = total_scores_gpt4
avg_scores_specific['Total Evaluation-score for Claude3'] = total_scores_claude3

# Helper function to count preferences for GPT-4 and Claude based on scores
def count_preferences(df):
    gpt4_preferred = (df['score_GPT4'] > df['score_Claude3']).sum()
    claude_preferred = (df['score_GPT4'] < df['score_Claude3']).sum()
    ties = (df['score_GPT4'] == df['score_Claude3']).sum()
    return gpt4_preferred, claude_preferred, ties

gpt4_preferred_count, claude_preferred_count, ties_count = count_preferences(comparisons_df)

# Group by 'question_id' and calculate average scores for GPT-4 and Claude3 for each question
grouped_avg_scores = comparisons_df.groupby('question_id').agg({'score_GPT4':'mean', 'score_Claude3':'mean'})

# Determine preferences based on average scores for each question
grouped_avg_scores['preference'] = np.select(
    [grouped_avg_scores['score_GPT4'] > grouped_avg_scores['score_Claude3'], grouped_avg_scores['score_GPT4'] < grouped_avg_scores['score_Claude3']],
    ['GPT-4', 'Claude3'], 
    default='Ties'
)

# Count preferences based on average scores
question_preferences_avg = grouped_avg_scores['preference'].value_counts().to_dict()
gpt4_question_preferred_avg = question_preferences_avg.get('GPT-4', 0)
claude_question_preferred_avg = question_preferences_avg.get('Claude3', 0)
question_ties_avg = question_preferences_avg.get('Ties', 0)

# Total questions and evaluations
total_questions = len(grouped_avg_scores)
total_evaluations = len(comparisons_df)

# Visualization
fig, ax = plt.subplots(figsize=(12, 8))

# Update title to include total questions and evaluations with preferences
title_message = f"Average Scores by Evaluation Conditions and Overall\n" \
                f"Total Question: {total_questions}, Preferences - GPT-4: {gpt4_question_preferred_avg}, " \
                f"Claude3: {claude_question_preferred_avg}, Ties: {question_ties_avg}\n" \
                f"Total Evaluation: {total_evaluations}, Preferences - GPT-4: {gpt4_preferred_count}, " \
                f"Claude3: {claude_preferred_count}, Ties: {ties_count}"
ax.set_title(title_message)

# Data for plotting
model_labels = [condition[1] for condition in conditions]
gpt4_scores = [avg_scores_specific[f"{label}-score for GPT-4"] for label in model_labels]
claude3_scores = [avg_scores_specific[f"{label}-score for Claude3"] for label in model_labels]
x = np.arange(len(model_labels))  # the label locations
width = 0.35  # the width of the bars

# Plot bars
bars1 = ax.bar(x - width/2, gpt4_scores, width, label='GPT-4', color='#a8c2ba')
bars2 = ax.bar(x + width/2, claude3_scores, width, label='Claude3', color='#c2896f')

# Add some text for labels, title, and custom x-axis tick labels
ax.set_ylabel('Average Scores')
ax.set_xticks(x)
ax.set_xticklabels(model_labels, rotation=45, ha='right')
ax.legend()

# Function to add labels on top of the bars
def add_labels(bars):
    for bar in bars:
        height = bar.get_height()
        ax.annotate('{}'.format(round(height, 2)),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

add_labels(bars1)
add_labels(bars2)

plt.tight_layout()
plt.show()