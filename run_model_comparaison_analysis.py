import os
import sqlite3
import json 
import re
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
from datasets import load_dataset


# Initialize environment variables
load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

# Check if API keys are set
if not openai_api_key or not anthropic_api_key:
    raise ValueError("API keys for OpenAI and Anthropic are not set. Please provide them in the .env file.")


# Initialize API clients
clientOpenAI = OpenAI(api_key=openai_api_key)
clientAnthropic = Anthropic(api_key=anthropic_api_key)

system_message_comparison = """
Please respond exclusively in JSON format, adhering to the following structure:
{
  "explanation": "A detailed narrative explaining the reasoning behind the comparison, 
                  including a chain of thought process that leads to the final assessment.",
  "score_a": "A numerical score between 0 and 100 representing the quality of answer A.",
  "score_b": "A numerical score between 0 and 100 representing the quality of answer B.",
  "better_answer": "Indicates which answer is superior, 'A' or 'B'. The choice should be 
                    supported by the scores and the detailed explanation provided. Only reply A or B in better_answer."
}
All the fields are mandatory!
"""

def get_questions(dataset_name="microsoft/orca-math-word-problems-200k", question_field="question", n=20):
    # Load the dataset
    dataset = load_dataset(dataset_name)
    # Access the training split
    train_data = dataset["train"]
    # Yield the first n questions from the specified field
    for i in range(n):
        yield train_data[i][question_field]

# Database initialization
def initialize_db(db_name="db_compare_models.db"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY, question TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS answers (id INTEGER PRIMARY KEY, question_id INTEGER, model TEXT, answer TEXT, FOREIGN KEY(question_id) REFERENCES questions(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS comparisons (id INTEGER PRIMARY KEY, question_id INTEGER, model_evaluating TEXT, preferred_answer TEXT, model_bot_a TEXT, model_bot_b TEXT, score_a INTEGER, score_b INTEGER, explanation TEXT, FOREIGN KEY(question_id) REFERENCES questions(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS comparison_gpt4_claude3 (id INTEGER PRIMARY KEY, question_id INTEGER, model_evaluating TEXT, preferred_answer TEXT, model_bot_a TEXT, model_bot_b TEXT, score_GPT4 INTEGER, score_Claude3 INTEGER, explanation TEXT, FOREIGN KEY(question_id) REFERENCES questions(id))''')
    conn.commit()
    conn.close()

# Insert question and answers into database
def insert_question_and_answers(question, answer_gpt4, answer_claude3):
    conn = sqlite3.connect("db_compare_models.db")
    c = conn.cursor()
    # Insert question
    c.execute("INSERT INTO questions (question) VALUES (?)", (question,))
    question_id = c.lastrowid
    # Insert answers
    c.execute("INSERT INTO answers (question_id, model, answer) VALUES (?, ?, ?)", (question_id, "GPT-4", json.dumps(answer_gpt4)))
    c.execute("INSERT INTO answers (question_id, model, answer) VALUES (?, ?, ?)", (question_id, "Claude3", json.dumps(answer_claude3)))
    conn.commit()
    conn.close()
    return question_id

# Insert comparison results into database
def insert_comparisons(question_id, model_evaluating, preferred_answer, model_bot_a, model_bot_b, score_a, score_b, explanation):
    # Determine scores for GPT-4 and Claude3
    if model_bot_a == "GPT-4" and model_bot_b == "Claude3":
        score_GPT4 = score_a
        score_Claude3 = score_b
    elif model_bot_a == "Claude3" and model_bot_b == "GPT-4":
        score_GPT4 = score_b
        score_Claude3 = score_a
    else:
        # This case should not occur, but it's handled for completeness
        print("Error: Model names do not match expected 'GPT-4' or 'Claude3'.")
        return
    
    conn = sqlite3.connect("db_compare_models.db")
    c = conn.cursor()
    c.execute("INSERT INTO comparisons (question_id, model_evaluating, preferred_answer, model_bot_a, model_bot_b, score_a, score_b, explanation) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (question_id, model_evaluating, preferred_answer, model_bot_a, model_bot_b, score_a, score_b, explanation))
    c.execute("INSERT INTO comparison_gpt4_claude3 (question_id, model_evaluating, preferred_answer, model_bot_a, model_bot_b, score_GPT4, score_Claude3, explanation) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (question_id, model_evaluating, preferred_answer, model_bot_a, model_bot_b, score_GPT4, score_Claude3, explanation))
    conn.commit()
    conn.close()

# Function to get answer from GPT-4-turbo-preview with explanation and scores
def get_gpt4_answer(prompt, system_prompt=None, reply_with_JSON=False):
    try:
        messages = [{"role": "user", "content": prompt}]
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        ## CALL API
        completion = clientOpenAI.chat.completions.create(
            model="gpt-4-turbo-preview", 
            messages=messages
        )
        response = completion.choices[0].message.content.strip()
        
        # Attempt to decode JSON
        if reply_with_JSON:
            # Find the first { and the last } in the response using regex
            matches = re.search(r'{.*}', response, re.DOTALL)
            if matches:
                json_str = matches.group(0)  # Extract the matched JSON string
                # Remove newline and carriage return characters
                json_str = json_str.replace('\n', '').replace('\r', '')
                # Escape backslashes before decoding
                json_str = json_str.replace('\\', '\\\\')
                try:
                    response_json = json.loads(json_str)
                    return response_json
                except json.JSONDecodeError as e:
                    print("Failed to decode JSON response in get_gpt4_answer.")
                    print(e)
                    print(f"get_gpt4_answer {repr(response)}")
                    return None
            else:
                print("No JSON found in the response.")
                return None
        else:
            return response
    except Exception as e:
        print("Error:", e)
        return None


# Function to get answer from Claude3 Opus with explanation and scores
def get_claude3_answer(prompt, system_prompt=None, reply_with_JSON=False):
    try:
        message_data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt is not None:
            message_data["system"] = system_prompt
        ## CALL API
        completion = clientAnthropic.messages.create(**message_data)
        response = completion.content[0].text
        if reply_with_JSON:
            try:
                # Remove newline and carriage return characters
                response = response.replace('\n', '').replace('\r', '')
                # Escape backslashes before decoding
                response = response.replace('\\', '\\\\')
                response_json = json.loads(response)
                return response_json
            except json.JSONDecodeError as e:
                print("Failed to decode JSON response in get_claude3_answer.")
                print(e) 
                print(f"get_claude3_answer {repr(response)}")
                return None
        else:
            return response
    except Exception as e:
        print("Error:", e)
        return None

def fetch_answers(question):
    # This function will be executed in a parallel manner for fetching answers
    if question['type'] == 'GPT-4':
        return get_gpt4_answer(question['prompt'])
    elif question['type'] == 'Claude3':
        return get_claude3_answer(question['prompt'])
    else:
        raise ValueError("Unsupported model type")
    
def fetch_comparisons(data):
    # This function will be executed in a parallel manner for fetching comparisons
    if data['type'] == 'GPT-4':
        return get_gpt4_answer(data['prompt'], system_prompt=system_message_comparison, reply_with_JSON=True)
    elif data['type'] == 'Claude3':
        return get_claude3_answer(data['prompt'], system_prompt=system_message_comparison, reply_with_JSON=True)
    else:
        raise ValueError("Unsupported model type")    
    
# Initialize database
initialize_db()

# Main script
if __name__ == "__main__":
    # Prompt user for dataset name, question field name, and number of questions to process
    dataset_name = input("Enter the dataset name (default: microsoft/orca-math-word-problems-200k): ").strip()
    if not dataset_name:
        dataset_name = "microsoft/orca-math-word-problems-200k"

    question_field = input("Enter the name of the question field (default: question): ").strip()
    if not question_field:
        question_field = "question"

    num_questions = input("Enter the number of questions to process (default: 20): ").strip()
    try:
        num_questions = int(num_questions) if num_questions else 20
    except ValueError:
        print("Invalid input for the number of questions. Using default value of 20.")
        num_questions = 20
        
    for user_question in get_questions(dataset_name, question_field, num_questions):
        # Process each question as before
        question_prompts = [
            {"type": "GPT-4", "prompt": user_question},
            {"type": "Claude3", "prompt": user_question}
        ]

        # Parallel fetching of answers
        with ThreadPoolExecutor() as executor:
            answers = list(executor.map(fetch_answers, question_prompts))

        answer_gpt4 = answers[0]
        answer_claude3 = answers[1]
        print(f"#####")
        print(f"""Answer by GPT-4: 
                {answer_gpt4}""")
        print(f"#####")
        print(f"""Answer by Claude3: 
                {answer_claude3}""")

        # Insert question and answers into database
        question_id = insert_question_and_answers(user_question, answer_gpt4, answer_claude3)

        # Prepare and evaluate comparison prompts
        comparison_prompt_first_gpt4 = f"Question: {user_question}\n\nAnswer A: {answer_gpt4}\n\nAnswer B: {answer_claude3}\n\nProvide a detailed comparison including an explanation, scores for each answer, and select the better answer."
        comparison_prompt_first_claude3 = f"Question: {user_question}\n\nAnswer A: {answer_claude3}\n\nAnswer B: {answer_gpt4}\n\nProvide a detailed comparison including an explanation, scores for each answer, and select the better answer."
        
        comparison_prompts = [
            {"type": "GPT-4", "prompt": comparison_prompt_first_gpt4, "question_id": question_id, "model_bot_a": "GPT-4", "model_bot_b": "Claude3"},
            {"type": "GPT-4", "prompt": comparison_prompt_first_claude3, "question_id": question_id, "model_bot_a": "Claude3", "model_bot_b": "GPT-4"},
            {"type": "Claude3", "prompt": comparison_prompt_first_gpt4, "question_id": question_id, "model_bot_a": "GPT-4", "model_bot_b": "Claude3"},
            {"type": "Claude3", "prompt": comparison_prompt_first_claude3, "question_id": question_id, "model_bot_a": "Claude3", "model_bot_b": "GPT-4"},
        ]
        
        # Parallel fetching of comparisons
        with ThreadPoolExecutor() as executor:
            comparison_results = list(executor.map(fetch_comparisons, comparison_prompts))

        # Initialize score accumulators and counts
        total_score_gpt4 = 0
        total_score_claude3 = 0
        count_gpt4 = 0
        count_claude3 = 0
        print("###")
        print(f"comparison_result={comparison_results}")
        print(" ")
        for i, comparison_result in enumerate(comparison_results):
            model_evaluating = comparison_prompts[i]['type']
            model_bot_a = comparison_prompts[i]['model_bot_a']
            model_bot_b = comparison_prompts[i]['model_bot_b']
            # Determine the preferred answer based on the comparison result
            if comparison_result is not None and 'better_answer' in comparison_result:
                if comparison_result['better_answer'][0] == 'A':
                    preferred_answer = model_bot_a
                elif comparison_result['better_answer'][0] == 'B':
                    preferred_answer = model_bot_b
                else:
                    print(f"Unknown? {comparison_result['better_answer']}")
                    preferred_answer = "Unknown"  # Fallback case, should ideally not happen
            else:
                print("####")
                print("Comparison result is None or 'better_answer' key is missing.")   
                print(f"comparison_prompts[i]={comparison_prompts[i]}")
                print(f"comparison_result={comparison_result}")
                print(f"comparison_results i={i}")
                print("Comparison result is None or 'better_answer' key is missing.")        
                print(" ")
                

            explanation = comparison_result['explanation']
            score_a = int(comparison_result['score_a'])  # Convert score to integer
            score_b = int(comparison_result['score_b'])  # Convert score to integer
            
            # Insert comparison results into the database
            insert_comparisons(question_id, model_evaluating, preferred_answer, model_bot_a, model_bot_b, score_a, score_b, explanation)

            # Print comparison results with explanations and scores
            print(f"#####")
            print(f"""Comparison result by {model_evaluating}: 
    Bot A {model_bot_a} (score {score_a}) vs Bot B {model_bot_b} (score {score_b})
    Preferred answer: {preferred_answer} with explanation: 
            {explanation}""")
            # Update score totals and counts based on the model being evaluated
            if model_bot_a == "GPT-4":
                total_score_gpt4 += score_a
                count_gpt4 += 1
            if model_bot_b == "GPT-4":
                total_score_gpt4 += score_b
                count_gpt4 += 1
            if model_bot_a == "Claude3":
                total_score_claude3 += score_a
                count_claude3 += 1
            if model_bot_b == "Claude3":
                total_score_claude3 += score_b
                count_claude3 += 1

# After all comparisons are processed, calculate the average scores
average_score_gpt4 = total_score_gpt4 / count_gpt4 if count_gpt4 else 0
average_score_claude3 = total_score_claude3 / count_claude3 if count_claude3 else 0

# Display the average scores
print("Average Scores:")
print(f"GPT-4: {average_score_gpt4}")
print(f"Claude3: {average_score_claude3}")