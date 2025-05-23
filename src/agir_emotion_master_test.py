#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import argparse
import time
import sys
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

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

# Constants
API_BASE_URL = "http://localhost:8000/api"
MODEL_NAME = "agir-learner"
USER_ID = "e030d930-913d-4525-8478-1cf77b698364"  # From agir_emotion_master.py
INPUT_FILE = "EU.jsonl"
RESULTS_DIR = "results"
BASE_MODEL_DIR = "emotion-master"

# These will be set dynamically in setup_directories()
MODEL_RESULTS_DIR = ""
PROGRESS_FILE = ""
RESULTS_FILE = ""

def setup_directories() -> None:
    """Create necessary directories if they don't exist, with versioning support."""
    global MODEL_RESULTS_DIR, PROGRESS_FILE, RESULTS_FILE
    
    Path(RESULTS_DIR).mkdir(exist_ok=True)
    
    # Find the next available directory name
    model_dir = BASE_MODEL_DIR
    version = 1
    
    while True:
        candidate_dir = f"{RESULTS_DIR}/{model_dir}"
        if not Path(candidate_dir).exists():
            # Found an available directory name
            MODEL_RESULTS_DIR = candidate_dir
            break
        else:
            # Directory exists, try next version
            version += 1
            model_dir = f"{BASE_MODEL_DIR}-v{version}"
            logger.info(f"Directory {candidate_dir} already exists, trying {model_dir}")
    
    # Update file paths based on the chosen directory
    PROGRESS_FILE = f"{MODEL_RESULTS_DIR}/progress.json"
    RESULTS_FILE = f"{MODEL_RESULTS_DIR}/results.jsonl"
    
    # Create the chosen directory
    Path(MODEL_RESULTS_DIR).mkdir(exist_ok=True)
    
    if version > 1:
        logger.info(f"Created new version directory: {MODEL_RESULTS_DIR}")
        logger.info(f"Previous results preserved in emotion-master through emotion-master-v{version-1}")
    else:
        logger.info(f"Results will be stored in: {MODEL_RESULTS_DIR}")
    
    logger.info(f"Progress file: {PROGRESS_FILE}")
    logger.info(f"Results file: {RESULTS_FILE}")

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
    """Create a prompt for agir-learner based on the item."""
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

def query_agir_api(prompt: str, retries: int = 3, retry_delay: int = 5) -> Optional[Dict[str, Any]]:
    """Query the agir emotion master API with retry logic."""
    url = f"{API_BASE_URL}/completions"
    
    payload = {
        "prompt": prompt,
        "model": MODEL_NAME,
        "max_tokens": 500,
        "temperature": 0,
        "user_id": USER_ID
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    for attempt in range(retries):
        try:
            logger.info(f"=== API Request Attempt {attempt + 1}/{retries} ===")
            logger.info(f"URL: {url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            import time
            start_time = time.time()
            logger.info(f"Making API request at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Request completed in {duration:.2f} seconds")
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(f"Response JSON: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse response as JSON: {je}")
                    logger.error(f"Raw response text: {repr(response.text)}")
                    response_data = {"error": "Invalid JSON response", "raw_text": response.text}
                
                # Extract the text from choices
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    text_content = response_data["choices"][0].get("text", "")
                    logger.info(f"Extracted text content: {repr(text_content)}")
                    
                    if not text_content.strip():
                        logger.error("Received empty text content from API")
                        if attempt < retries - 1:
                            logger.info(f"Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.error("Empty response after all retries. Exiting.")
                            sys.exit(1)
                    
                    # Try to parse JSON from the text content
                    try:
                        # The text might contain extra content, try to find JSON
                        text_content = text_content.strip()
                        logger.info(f"Attempting to parse JSON from: {repr(text_content)}")
                        
                        # Look for JSON-like content
                        if text_content.startswith('{') and text_content.endswith('}'):
                            parsed_result = json.loads(text_content)
                            logger.info(f"Successfully parsed JSON: {parsed_result}")
                            return parsed_result
                        else:
                            # Try to extract JSON from the text
                            import re
                            json_match = re.search(r'\{[^}]*"emotion"[^}]*"cause"[^}]*\}', text_content)
                            if json_match:
                                json_str = json_match.group()
                                logger.info(f"Found JSON pattern: {json_str}")
                                parsed_result = json.loads(json_str)
                                logger.info(f"Successfully parsed extracted JSON: {parsed_result}")
                                return parsed_result
                            else:
                                # If no proper JSON found, try to extract emotion and cause manually
                                emotion_match = re.search(r'"emotion"\s*:\s*"([^"]*)"', text_content)
                                cause_match = re.search(r'"cause"\s*:\s*"([^"]*)"', text_content)
                                
                                if emotion_match and cause_match:
                                    extracted_result = {
                                        "emotion": emotion_match.group(1),
                                        "cause": cause_match.group(1)
                                    }
                                    logger.info(f"Manually extracted emotion and cause: {extracted_result}")
                                    return extracted_result
                                else:
                                    logger.error(f"Could not extract emotion and cause from: {text_content}")
                                    logger.error(f"Emotion match: {emotion_match}")
                                    logger.error(f"Cause match: {cause_match}")
                                    raise json.JSONDecodeError("Could not extract structured data", text_content, 0)
                        
                    except json.JSONDecodeError as je:
                        logger.error(f"JSON decode error: {je}")
                        logger.error(f"Content that failed to parse: {repr(text_content)}")
                        if attempt < retries - 1:
                            logger.info(f"Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.error("Non-JSON response received after all retries. Exiting.")
                            sys.exit(1)
                else:
                    logger.error("No choices in API response")
                    logger.error(f"Full response structure: {response_data}")
                    if attempt < retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error("No choices after all retries. Exiting.")
                        sys.exit(1)
            else:
                logger.error(f"API request failed with status {response.status_code}")
                logger.error(f"Response headers: {dict(response.headers)}")
                logger.error(f"Response text: {response.text}")
                if attempt < retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Exiting.")
                    sys.exit(1)
                    
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout after 120 seconds (attempt {attempt+1}/{retries}): {str(e)}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached due to timeout. Exiting.")
                sys.exit(1)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error (attempt {attempt+1}/{retries}): {str(e)}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached due to connection error. Exiting.")
                sys.exit(1)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error (attempt {attempt+1}/{retries}): {str(e)}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Exiting.")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error (attempt {attempt+1}/{retries}): {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Exiting.")
                sys.exit(1)

def evaluate_responses(api_response: Dict[str, str], item: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate API's responses against the ground truth."""
    true_emotion = item["emotion_label"]
    true_cause = item["cause_label"]
    
    predicted_emotion = api_response.get("emotion", "")
    predicted_cause = api_response.get("cause", "")
    
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
    
    for item in tqdm(data_to_process, desc="Testing agir emotion master"):
        prompt = create_prompt(item)
        api_response = query_agir_api(prompt)
        
        if api_response:
            result = evaluate_responses(api_response, item)
            save_result(result)
            processed_ids.append(item["qid"])
            save_progress(processed_ids)
        else:
            logger.warning(f"Skipping item {item['qid']} due to failed API query.")
    
    logger.info(f"Testing complete. Processed {len(processed_ids)} items in total.")

def calculate_statistics() -> Dict[str, Any]:
    """Calculate statistics from the results file."""
    if not RESULTS_FILE or not Path(RESULTS_FILE).exists():
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

def test_api_connection() -> bool:
    """Test if the API is accessible."""
    try:
        logger.info("=== API Connection Test ===")
        test_prompt = "What book have you read recently?"
        test_payload = {
            "prompt": test_prompt,
            "model": MODEL_NAME,
            "max_tokens": 100,
            "temperature": 0.7,
            "user_id": USER_ID
        }
        
        url = f"{API_BASE_URL}/completions"
        
        logger.info(f"Test URL: {url}")
        logger.info(f"Test Payload: {json.dumps(test_payload, indent=2, ensure_ascii=False)}")
        
        import time
        start_time = time.time()
        logger.info(f"Starting connection test at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(url, json=test_payload, timeout=120)
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Connection test completed in {duration:.2f} seconds")
        logger.info(f"Test response status code: {response.status_code}")
        logger.info(f"Test response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            logger.info("API connection successful")
            try:
                response_data = response.json()
                logger.info(f"Test response data: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError as je:
                logger.warning(f"Could not parse test response as JSON: {je}")
                logger.warning(f"Raw test response: {repr(response.text)}")
            return True
        else:
            logger.error(f"API connection failed with status {response.status_code}")
            logger.error(f"Test response text: {response.text}")
            return False
            
    except requests.exceptions.Timeout as e:
        logger.error(f"API connection test timeout after 120 seconds: {str(e)}")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"API connection test failed - connection error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"API connection test failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(description="Test agir emotion master API on EU.jsonl")
    parser.add_argument("--limit", type=int, help="Limit the number of records to test")
    parser.add_argument("--resume", action="store_true", help="Resume from previous run")
    parser.add_argument("--test-connection", action="store_true", help="Only test API connection")
    args = parser.parse_args()
    
    setup_directories()
    
    # Test API connection first
    if args.test_connection:
        if test_api_connection():
            logger.info("API connection test passed")
        else:
            logger.error("API connection test failed")
        return
    
    # if not test_api_connection():
    #     logger.error("Cannot connect to agir emotion master API. Please ensure the service is running at http://localhost:8000")
    #     return
    
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
    logger.info(f"Results summary for agir emotion master:")
    for key, value in stats.items():
        if isinstance(value, float):
            logger.info(f"{key}: {value:.2%}")
        else:
            logger.info(f"{key}: {value}")

if __name__ == "__main__":
    main() 