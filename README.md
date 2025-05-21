# EU (Emotional Understanding) Testing with GPT-4.1-nano

This project uses Python code to test the EU.jsonl dataset with the GPT-4.1-nano model.

Results are recorded in a file, capturing both the GPT model's responses and the correct answers.

Key features:
- Supports resuming testing from the point of interruption
- Allows specifying the number of records to test
- Uses conda and makefile for environment management

## Environment Setup

1. Clone this repository
2. Create and activate the conda environment:

```
make env
conda activate agir-eu
```

3. Configure API Key:

```
cp .env-example .env
```

Then edit the `.env` file to add your OpenAI API key:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Run Complete Test

```
make run
```

### Limit Number of Test Records

```
make run-limit limit=10
```

This will test only the first 10 records.

### Resume Testing from Previous Interruption

```
make resume limit=20
```

This will resume testing from where it left off, processing 20 records at a time.

### Recreate Environment

If you need to recreate the conda environment:

```
make recreate-env
conda activate agir-eu
```

## Results

Test results are saved in the `results/results.jsonl` file. Each line contains a JSON object with:

- Original scenario
- Correct emotion and reason
- GPT's predicted emotion and reason
- Accuracy metrics

Progress information is saved in `results/progress.json` to support resuming from interruptions.

After completion, the program displays statistics including:
- Emotion prediction accuracy
- Reason prediction accuracy
- Combined accuracy (both correct)