Here's a detailed README file for your GitHub repository:

# Compare Models: GPT-4-turbo and Claude 3 Opus

This project compares the performance of GPT-4-turbo and Claude 3 Opus by sending questions to both APIs and then analyzing the quality of their responses without disclosing which model provided which answer. It's a simple way to assess and compare the capabilities of these models.

## Project Structure

The project consists of three main Python scripts:

1. `run_model_comparaison_analysis.py`: The main script that orchestrates the comparison process.
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
   python run_model_comparaison_analysis.py
   ```

2. Follow the prompts to enter the dataset name, question field name, and the number of questions to process.

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