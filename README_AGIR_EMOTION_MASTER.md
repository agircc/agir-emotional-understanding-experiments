# Agir Emotion Master API Testing

This script is used to test the local agir emotion master API performance on the emotional understanding dataset.

## API Interface

- **URL**: `http://localhost:8000/api/chat/completions`
- **Model**: `agir-learner`
- **User ID**: `e030d930-913d-4525-8478-1cf77b698364`

## Usage

### 1. Ensure Environment is Set Up

```bash
# If environment hasn't been installed yet
make env
conda activate agir-eu

# If environment needs updating (added requests library)
make update-env
```

### 2. Test API Connection

Before running the full test, test the API connection first:

```bash
make test-agir-connection
```

### 3. Run Full Test

```bash
# Test all data
make run-agir

# Limit test quantity
make run-agir-limit limit=10

# Resume test from interruption
make resume-agir
```

### 4. View Results

Test results will be saved in the `results/emotion-master/` directory (or `emotion-master-v2/`, `emotion-master-v3/`, etc. if previous results exist):

- `results.jsonl`: Detailed test results
- `progress.json`: Progress information (supports test resumption)

**Note**: The script automatically creates versioned directories to preserve previous test results. If `emotion-master/` already exists, it will create `emotion-master-v2/`, and so on.

### 5. Analyze Results

Use existing analysis tools to analyze emotion-master results:

```bash
# Analyze emotion-master model results (base directory)
make analyze-model model=emotion-master

# Analyze specific version results
make analyze-model model=emotion-master-v2

# Compare all model results (including all emotion-master versions)
make compare-models
```

## Script Features

- **Auto Retry**: API requests will automatically retry on failure (up to 3 times)
- **Progress Saving**: Supports resuming tests after interruption
- **Response Parsing**: Intelligent parsing of JSON responses returned by API
- **Error Handling**: Comprehensive error handling and logging
- **Connection Testing**: Verify API connection before starting tests
- **Version Management**: Automatically creates versioned directories to preserve previous results

## Version Management

The script automatically manages result directories to prevent overwriting previous test results:

- **First run**: Creates `results/emotion-master/`
- **Second run**: Creates `results/emotion-master-v2/` (preserving the original)
- **Third run**: Creates `results/emotion-master-v3/` (preserving v1 and v2)
- And so on...

This allows you to:
- Compare results across different test runs
- Keep historical performance data
- Experiment with different API parameters without losing previous results

Each versioned directory contains its own `results.jsonl` and `progress.json` files.

## Notes

1. Ensure agir emotion master service is running at `http://localhost:8000`
2. Test script uses English prompts, suitable for English emotional understanding tasks
3. Result format is compatible with existing OpenAI API tests, can use the same analysis tools

## Troubleshooting

If encountering connection issues:

1. Check if agir emotion master service is running
2. Confirm service is listening on the correct port (8000)
3. Check firewall settings

If encountering parsing issues:

1. Script will try multiple ways to parse API responses
2. Check logs to understand specific parsing errors
3. Confirm API returns expected format 