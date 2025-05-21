#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import argparse
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Clear environment variables that may affect OpenAI client initialization
proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 
              'OPENAI_PROXY', 'openai_proxy']
for var in proxy_vars:
    if var in os.environ:
        logger.info(f"Clearing environment variable {var} to avoid OpenAI client initialization errors")
        os.environ.pop(var)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Constants
MODEL_NAME = os.getenv("GPT_MODEL", "gpt-4.1-nano")
INPUT_FILE = "EU.jsonl"
RESULTS_DIR = "results"
# Create model-specific directory name by replacing dots with hyphens
MODEL_DIR = MODEL_NAME.replace(".", "-")
MODEL_RESULTS_DIR = f"{RESULTS_DIR}/{MODEL_DIR}"
PROGRESS_FILE = f"{MODEL_RESULTS_DIR}/progress.json"
RESULTS_FILE = f"{MODEL_RESULTS_DIR}/results.jsonl"

def setup_directories() -> None:
    """Create necessary directories if they don't exist."""
    Path(RESULTS_DIR).mkdir(exist_ok=True)
    Path(MODEL_RESULTS_DIR).mkdir(exist_ok=True)
    logger.info(f"Results will be stored in: {MODEL_RESULTS_DIR}")

def load_data(file_path: str) -> List[Dict[str, Any]]:
    """Load data from JSONL file."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def save_progress(processed_ids: List[str]) -> None:
    """Save progress information."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"processed_ids": processed_ids, "updated_at": datetime.now().isoformat()}, f)

def load_progress() -> List[str]:
    """Load progress information if it exists."""
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get("processed_ids", [])
    return []

def save_result(result: Dict[str, Any]) -> None:
    """Save a single result to the results file."""
    with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False) + '\n')

def create_prompt(item: Dict[str, Any]) -> str:
    """Create a prompt for GPT based on the item."""
    scenario = item["scenario"]
    subject = item["subject"]
    emotion_choices = item["emotion_choices"]
    cause_choices = item["cause_choices"]
    
    prompt = f"""Given the following scenario, identify the emotion of the subject and the cause of that emotion.

Scenario: {scenario}

Subject: {subject}

Emotion choices: {", ".join(emotion_choices)}

Cause choices: {", ".join(cause_choices)}

Provide your answer in JSON format with two fields: "emotion" and "cause".
"""
    return prompt

def query_gpt(prompt: str, retries: int = 3, retry_delay: int = 5) -> Optional[Dict[str, Any]]:
    """Query the GPT model with retry logic."""
    for attempt in range(retries):
        try:
            # Set parameters based on model type
            params = {
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Different models use different parameter names for token limits and formats
            if MODEL_NAME.startswith("o4"):
                # For o4 models:
                # 1. Use higher token limit
                # 2. For o4-mini, response_format can sometimes cause issues
                params["max_completion_tokens"] = 2000
                
                # o4-mini doesn't support custom temperature, only default (1)
                # Don't set temperature at all for o4-mini
                
                # Only use response_format if not o4-mini specifically
                if MODEL_NAME != "o4-mini":
                    params["response_format"] = {"type": "json_object"}
                    # Only set temperature for non-o4-mini models
                    params["temperature"] = 0
                else:
                    # For o4-mini, add explicit instruction for JSON format
                    params["messages"][0]["content"] += "\n\nIMPORTANT: Your response MUST be in valid JSON format with the fields 'emotion' and 'cause' only."
            else:
                params["max_tokens"] = 500
                params["temperature"] = 0
                params["response_format"] = {"type": "json_object"}
            
            # Log the parameters we're using
            logger.info(f"Querying model with parameters: {params}")
                
            response = client.chat.completions.create(**params)
            
            # Debug logging
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response choices: {response.choices}")
            
            if len(response.choices) > 0:
                logger.info(f"Message content type: {type(response.choices[0].message.content)}")
                logger.info(f"Raw message content: {repr(response.choices[0].message.content)}")
                
                # Check for empty content
                if not response.choices[0].message.content.strip():
                    logger.error("Received empty response from model")
                    if attempt < retries - 1:
                        logger.info(f"Retrying with simpler prompt...")
                        # Try a simpler prompt if this was an empty response
                        if MODEL_NAME == "o4-mini":
                            # Simplify prompt for retry
                            simple_scenario = prompt.split('Scenario: ')[1].split('\n\nSubject:')[0]
                            simple_subject = prompt.split('Subject: ')[1].split('\n\nEmotion choices:')[0]
                            simple_prompt = f'From this scenario: "{simple_scenario}", the subject is "{simple_subject}". '
                            simple_prompt += 'What is their emotion and its cause? Reply only with JSON: {"emotion": "chosen_emotion", "cause": "chosen_cause"}'
                            
                            params["messages"][0]["content"] = simple_prompt
                            continue
                    else:
                        logger.error("Empty response after all retries. Exiting.")
                        sys.exit(1)
            else:
                logger.error("No choices in response")
                sys.exit(1)
            
            # Parse JSON or exit
            try:
                # Try direct JSON parsing
                if response.choices[0].message.content:
                    try:
                        return json.loads(response.choices[0].message.content)
                    except json.JSONDecodeError as je:
                        logger.error(f"JSON decode error: {je}")
                        logger.error(f"Content that failed to parse: {repr(response.choices[0].message.content)}")
                        logger.error("Non-JSON response received. Exiting.")
                        sys.exit(1)
                else:
                    logger.error("Empty response content. Exiting.")
                    sys.exit(1)
                    
            except Exception as je:
                logger.error(f"Error parsing response: {je}")
                logger.error("Exiting due to invalid response format.")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error querying GPT (attempt {attempt+1}/{retries}): {str(e)}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Exiting.")
                sys.exit(1)

def evaluate_responses(gpt_response: Dict[str, str], item: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate GPT's responses against the ground truth."""
    true_emotion = item["emotion_label"]
    true_cause = item["cause_label"]
    
    predicted_emotion = gpt_response.get("emotion", "")
    predicted_cause = gpt_response.get("cause", "")
    
    emotion_correct = predicted_emotion == true_emotion
    cause_correct = predicted_cause == true_cause
    
    return {
        "qid": item["qid"],
        "scenario": item["scenario"],
        "subject": item["subject"],
        "true_emotion": true_emotion,
        "predicted_emotion": predicted_emotion,
        "emotion_correct": emotion_correct,
        "true_cause": true_cause,
        "predicted_cause": predicted_cause,
        "cause_correct": cause_correct,
        "both_correct": emotion_correct and cause_correct
    }

def run_test(data: List[Dict[str, Any]], limit: Optional[int] = None, resume: bool = False) -> None:
    """Run the test on the provided data."""
    processed_ids = load_progress() if resume else []
    
    # Filter out already processed items if resuming
    if resume and processed_ids:
        logger.info(f"Resuming from previous run. {len(processed_ids)} items already processed.")
        data_to_process = [item for item in data if item["qid"] not in processed_ids]
    else:
        data_to_process = data
    
    # Apply limit if specified
    if limit is not None:
        data_to_process = data_to_process[:limit]
    
    logger.info(f"Processing {len(data_to_process)} items...")
    
    for item in tqdm(data_to_process, desc="Testing"):
        prompt = create_prompt(item)
        gpt_response = query_gpt(prompt)
        
        if gpt_response:
            result = evaluate_responses(gpt_response, item)
            save_result(result)
            processed_ids.append(item["qid"])
            save_progress(processed_ids)
        else:
            logger.warning(f"Skipping item {item['qid']} due to failed GPT query.")
    
    logger.info(f"Testing complete. Processed {len(processed_ids)} items in total.")

def calculate_statistics() -> Dict[str, Any]:
    """Calculate statistics from the results file."""
    if not Path(RESULTS_FILE).exists():
        return {"error": "No results file found"}
    
    results = []
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            results.append(json.loads(line))
    
    total = len(results)
    emotion_correct = sum(1 for r in results if r["emotion_correct"])
    cause_correct = sum(1 for r in results if r["cause_correct"])
    both_correct = sum(1 for r in results if r["both_correct"])
    
    return {
        "total_items": total,
        "emotion_accuracy": emotion_correct / total if total > 0 else 0,
        "cause_accuracy": cause_correct / total if total > 0 else 0,
        "both_correct_accuracy": both_correct / total if total > 0 else 0
    }

def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(description="Test GPT-4.1-nano on EU.jsonl")
    parser.add_argument("--limit", type=int, help="Limit the number of records to test")
    parser.add_argument("--resume", action="store_true", help="Resume from previous run")
    args = parser.parse_args()
    
    setup_directories()
    
    # Check if API key is set
    if not api_key:
        logger.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return
    
    # Load data
    try:
        data = load_data(INPUT_FILE)
        logger.info(f"Loaded {len(data)} records from {INPUT_FILE}")
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return
    
    # Run test
    run_test(data, limit=args.limit, resume=args.resume)
    
    # Calculate and display statistics
    stats = calculate_statistics()
    logger.info(f"Results summary:")
    for key, value in stats.items():
        if isinstance(value, float):
            logger.info(f"{key}: {value:.2%}")
        else:
            logger.info(f"{key}: {value}")

if __name__ == "__main__":
    main() 