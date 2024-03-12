# Blind Self-Evaluation: GPT-4-turbo vs. Claude 3 Opus

This project compares the performance of GPT-4-turbo and Claude 3 Opus by sending questions to both APIs and then asking them to evaluate the quality of both answers without knowing the origin of the answers.

This blind assessment approach provides a simple and "unbiased" way to assess and compare the quality of these models.

During my limited testing, both GPT-4-turbo and Claude 3 Opus showed a preference for the answers generated by Claude 3 Opus for the question coming from dataset microsoft/orca-math-word-problems-200k.
However, Claude 3 Opus and GPT-4-turbo seems to both prefer the haikus generated by GPT-4-turbo :)

## Context

This is a side project that was made possible with the help of ChatGPT! 🙌

While it may not be fully optimized, the idea is to test the concept of models self-evaluating.

A potential next step could be to compare the models' answers with the dataset's correct answer to evalute the accuracy. Additionally, creating a third answer during the comparison of the two answers previously generated by GPT-4-turbo and Claude 3 Opus could be interesting to evaluate if it generates better outcomes.


## Methodology

1. When the question is sent to get the original model's answer, there is no system message.
2. However, when we ask the model to compare both answers, we are sending the following system message:

```json
Please respond exclusively in JSON format, adhering to the following structure:
{
 "explanation": "A detailed narrative explaining the reasoning behind the comparison, including a chain of thought process that leads to the final assessment.",
 "score_a": "A numerical score between 0 and 100 representing the quality of answer A.",
 "score_b": "A numerical score between 0 and 100 representing the quality of answer B.",
 "better_answer": "Indicates which answer is superior, 'A' or 'B'. The choice should be supported by the scores and the detailed explanation provided. Only reply with 'A' or 'B' in better_answer."
}
All fields are mandatory!
```

The different steps of the comparison process are as follows:

1. Send the user question to API A (e.g., GPT-4-turbo) and receive its answer.
2. Send the user question to API B (e.g., Claude 3 Opus) and receive its answer.
3. Send the user question along with the answers from API A and API B to API A (e.g., GPT-4-turbo) and ask it to evaluate which answer is the best, without disclosing which model provided each answer.
4. Send the user question along with the answers from API A and API B to API B (e.g., Claude 3 Opus) and ask it to evaluate which answer is the best, without disclosing which model provided each answer.
5. Repeat steps 3 and 4, but switch the sequence of the API answers (API B first, then API A) to ensure a balanced evaluation.

By having each model evaluate the answers without knowing their origins and by switching the order of the answers, the project aims to obtain a comparison of the models' performance and capabilities that is as objective as possible within the constraints of using the models themselves for evaluation.

## Results overview about twenty questions (source microsoft/orca-math-word-problems-200k)

![Alt Text](/charts_images/model_scores.png)
![Alt Text](/charts_images/model_preferences.png)

## Project Structure

The project consists of three main Python scripts:

1. `run_model_comparison_analysis.py`: The main script that orchestrates the comparison process.
2. `charts_model_scores.py`: Generates visualizations for the average scores of the models.
3. `charts_model_preferences.py`: Generates visualizations for the preference evaluation between the models.

## Prerequisites

Before running the project, ensure you have the following:

- Python 3.x installed
- Required Python packages: `openai`, `anthropic`, `python-dotenv`, `datasets`, `matplotlib`, `pandas`, `numpy`, `sqlite3`
- API keys for OpenAI and Anthropic

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/MaxFouTech/compare-models-gpt-4-claude-3.git
   ```

2. Install the required Python packages:
   ```
   pip install openai anthropic python-dotenv datasets matplotlib pandas numpy sqlite3
   ```

3. Create a `.env` file in the project root directory and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

## Usage

1. Run the main script:
   ```
   python run_model_comparison_analysis.py
   ```

2. Follow the prompts to enter your own question or the dataset name, question field name, and the number of questions to process.

3. The script will fetch questions from the specified dataset, send them to both GPT-4-turbo and Claude 3 Opus APIs, and store the responses in a SQLite database.

4. The script will then generate comparison prompts, asking each model to evaluate the responses from both models without disclosing which model provided which answer.

5. The comparison results, including explanations and scores, will be stored in the database and displayed in the console.

6. To generate visualizations for the average scores, run:
   ```
   python charts_model_scores.py
   ```

7. To generate visualizations for the preference evaluation, run:
   ```
   python charts_model_preferences.py
   ```

## API Calls and Parameters

### GPT-4-turbo API

The `get_gpt4_answer` function calls the OpenAI API to get responses from GPT-4-turbo. It uses the following parameters:

- `model`: Set to "gpt-4-turbo-preview"
- `messages`: A list of messages, including the user's prompt and an optional system prompt
- `max_tokens`: Not explicitly set, using the default value

### Claude 3 Opus API

The `get_claude3_answer` function calls the Anthropic API to get responses from Claude 3 Opus. It uses the following parameters:

- `model`: Set to "claude-3-opus-20240229"
- `max_tokens`: Set to 1000
- `messages`: A list of messages, including the user's prompt and an optional system prompt

## Database Schema

The project uses a SQLite database (`db_compare_models.db`) to store questions, answers, and comparison results. The database schema consists of the following tables:

- `questions`: Stores the question ID and text
- `answers`: Stores the answer ID, question ID (foreign key), model name, and answer text
- `comparisons`: Stores the comparison ID, question ID (foreign key), evaluating model, preferred answer, model names for bot A and bot B, scores for bot A and bot B, and explanation
- `comparison_gpt4_claude3`: Similar to `comparisons`, but with separate columns for GPT-4 and Claude3 scores

## Visualizations

The project generates two types of visualizations:

1. Average Scores: Bar charts showing the average scores for GPT-4 and Claude3 under different evaluation conditions and overall.

2. Preference Evaluation: Pie charts illustrating each model's preference between its own answers and the other model's answers, based on blind assessments.

## Limitations and Considerations

- The comparison results may be influenced by the specific dataset and questions used. It's recommended to test with different datasets and a larger number of questions for more comprehensive insights.

- The API parameters used for GPT-4-turbo and Claude 3 Opus can impact the quality and style of the generated responses. Adjusting these parameters may lead to different results.

- The project relies on the availability and stability of the OpenAI and Anthropic APIs. Any changes or limitations in these APIs may affect the functionality of the project.

## License

This project is open-source and available under the [MIT License](LICENSE).