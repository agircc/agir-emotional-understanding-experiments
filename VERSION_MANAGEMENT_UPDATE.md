# Version Management Feature Update

## Overview

Added automatic directory versioning to the agir emotion master test script to prevent overwriting previous test results.

## Implementation Details

### Key Changes

1. **Dynamic Path Management**
   - Changed from static paths to dynamic global variables
   - `MODEL_RESULTS_DIR`, `PROGRESS_FILE`, and `RESULTS_FILE` are now set dynamically

2. **Version Detection Logic**
   - Checks if `results/emotion-master/` exists
   - If exists, tries `emotion-master-v2`, `emotion-master-v3`, etc.
   - Continues until it finds an available directory name

3. **Enhanced Logging**
   - Reports which version directory is being created
   - Shows information about preserved previous results
   - Displays full paths for progress and results files

### Code Structure

```python
# Constants (updated)
BASE_MODEL_DIR = "emotion-master"
MODEL_RESULTS_DIR = ""  # Set dynamically
PROGRESS_FILE = ""      # Set dynamically  
RESULTS_FILE = ""       # Set dynamically

# New versioning logic in setup_directories()
def setup_directories():
    global MODEL_RESULTS_DIR, PROGRESS_FILE, RESULTS_FILE
    
    model_dir = BASE_MODEL_DIR
    version = 1
    
    while True:
        candidate_dir = f"{RESULTS_DIR}/{model_dir}"
        if not Path(candidate_dir).exists():
            MODEL_RESULTS_DIR = candidate_dir
            break
        else:
            version += 1
            model_dir = f"{BASE_MODEL_DIR}-v{version}"
    
    # Update file paths and create directory
    PROGRESS_FILE = f"{MODEL_RESULTS_DIR}/progress.json"
    RESULTS_FILE = f"{MODEL_RESULTS_DIR}/results.jsonl"
    Path(MODEL_RESULTS_DIR).mkdir(exist_ok=True)
```

## Benefits

### 1. **Data Preservation**
- Previous test results are never overwritten
- Historical performance data is maintained
- Easy comparison between different test runs

### 2. **Experimentation Support**
- Test different API parameters without losing results
- Compare performance across multiple configurations
- Track improvements over time

### 3. **Analysis Flexibility**
- Each version can be analyzed independently
- Use existing tools with versioned directory names
- Support for batch comparison across versions

## Usage Examples

### Running Tests
```bash
# First run creates: results/emotion-master/
make run-agir-limit limit=10

# Second run creates: results/emotion-master-v2/
make run-agir-limit limit=10

# Third run creates: results/emotion-master-v3/
make run-agir-limit limit=10
```

### Analyzing Results
```bash
# Analyze original results
make analyze-model model=emotion-master

# Analyze second version
make analyze-model model=emotion-master-v2

# Analyze third version
make analyze-model model=emotion-master-v3

# Compare all versions
make compare-models
```

## Directory Structure Example

After multiple test runs:
```
results/
├── emotion-master/          # First test run
│   ├── progress.json
│   └── results.jsonl
├── emotion-master-v2/       # Second test run  
│   ├── progress.json
│   └── results.jsonl
├── emotion-master-v3/       # Third test run
│   ├── progress.json
│   └── results.jsonl
└── analysis/                # Analysis outputs
    ├── emotion-master/
    ├── emotion-master-v2/
    └── emotion-master-v3/
```

## Testing

The versioning functionality has been tested and works correctly:

1. **First run**: Creates `emotion-master/`
2. **Second run**: Detects existing directory, creates `emotion-master-v2/`
3. **Third run**: Detects v1 and v2, creates `emotion-master-v3/`

Log output shows proper detection and creation of versioned directories.

## Compatibility

- ✅ Fully backward compatible with existing analysis tools
- ✅ Works with all existing Makefile commands
- ✅ Maintains same file structure within each directory
- ✅ No changes required to existing workflows

## Updated Documentation

- Updated `README_AGIR_EMOTION_MASTER.md` with version management section
- Updated `SUMMARY.md` with new feature details
- Added usage examples for versioned directories
- Documented analysis commands for different versions 