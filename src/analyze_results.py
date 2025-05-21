#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from pathlib import Path
import logging
from dotenv import load_dotenv
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure matplotlib font for CJK characters
def configure_fonts():
    """Configure matplotlib to use appropriate fonts for CJK characters."""
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        mpl.rc('font', family='Arial Unicode MS')
    elif system == 'Windows':
        mpl.rc('font', family='Microsoft YaHei')
    elif system == 'Linux':
        # Try common CJK fonts available on Linux
        for font in ['Noto Sans CJK JP', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei']:
            try:
                mpl.rc('font', family=font)
                logger.info(f"Using font: {font}")
                break
            except:
                continue
    
    # Fallback to non-CJK handling if we can't find a good font
    mpl.rcParams['axes.unicode_minus'] = False  # Fix minus sign display issue

def load_results(results_file):
    """Load results from JSONL file."""
    data = []
    with open(results_file, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def calculate_metrics(results):
    """Calculate metrics from the results."""
    total = len(results)
    emotion_correct = sum(1 for r in results if r["emotion_correct"])
    cause_correct = sum(1 for r in results if r["cause_correct"])
    both_correct = sum(1 for r in results if r["both_correct"])
    
    metrics = {
        "total_items": total,
        "emotion_accuracy": emotion_correct / total if total > 0 else 0,
        "cause_accuracy": cause_correct / total if total > 0 else 0,
        "both_correct_accuracy": both_correct / total if total > 0 else 0
    }
    
    return metrics

def create_confusion_matrix(results):
    """Create a confusion matrix for emotion prediction."""
    # Extract unique emotions
    all_emotions = set()
    for r in results:
        true_emotion = r["true_emotion"].split(" & ")[0]  # Just use first emotion for simplicity
        pred_emotion = r["predicted_emotion"].split(" & ")[0]  # Just use first emotion for simplicity
        all_emotions.add(true_emotion)
        all_emotions.add(pred_emotion)
    
    all_emotions = sorted(list(all_emotions))
    
    # Create the confusion matrix
    confusion = pd.DataFrame(0, index=all_emotions, columns=all_emotions)
    
    for r in results:
        true_emotion = r["true_emotion"].split(" & ")[0]
        pred_emotion = r["predicted_emotion"].split(" & ")[0]
        confusion.loc[true_emotion, pred_emotion] += 1
    
    return confusion

def analyze_model_results(model_dir):
    """Analyze results for a specific model."""
    results_file = os.path.join("results", model_dir, "results.jsonl")
    
    if not os.path.exists(results_file):
        logger.error(f"Results file not found: {results_file}")
        return None
    
    results = load_results(results_file)
    logger.info(f"Loaded {len(results)} results from {results_file}")
    
    # Calculate basic metrics
    metrics = calculate_metrics(results)
    
    # Create a DataFrame for easier analysis
    df = pd.DataFrame(results)
    
    return {
        "model_name": model_dir,
        "metrics": metrics,
        "dataframe": df,
        "confusion_matrix": create_confusion_matrix(results)
    }

def plot_confusion_matrix(confusion_matrix, model_name, output_dir):
    """Plot and save confusion matrix heatmap."""
    plt.figure(figsize=(12, 10))
    sns.heatmap(confusion_matrix, annot=True, fmt='d', cmap='Blues')
    plt.title(f'Emotion Confusion Matrix - {model_name}')
    plt.ylabel('True Emotion')
    plt.xlabel('Predicted Emotion')
    plt.tight_layout()
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{model_name}_confusion_matrix.png")
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved confusion matrix to {output_path}")

def plot_accuracy_metrics(metrics, model_name, output_dir):
    """Plot and save accuracy metrics."""
    metrics_to_plot = {k: v for k, v in metrics.items() if k != 'total_items'}
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(metrics_to_plot.keys(), metrics_to_plot.values(), color=['blue', 'green', 'red'])
    
    # Add percentage labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                 f'{height:.1%}', ha='center', va='bottom')
    
    plt.title(f'Accuracy Metrics - {model_name}')
    plt.ylim(0, 1)
    plt.ylabel('Accuracy')
    plt.tight_layout()
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{model_name}_accuracy_metrics.png")
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved accuracy metrics to {output_path}")

def compare_models(models_results, output_dir):
    """Compare multiple models and create comparison visualizations."""
    if not models_results:
        logger.error("No model results to compare")
        return
    
    # Extract metrics for comparison
    model_names = []
    emotion_accuracy = []
    cause_accuracy = []
    both_accuracy = []
    
    for result in models_results:
        model_names.append(result["model_name"])
        emotion_accuracy.append(result["metrics"]["emotion_accuracy"])
        cause_accuracy.append(result["metrics"]["cause_accuracy"])
        both_accuracy.append(result["metrics"]["both_correct_accuracy"])
    
    # Create a DataFrame for comparison
    comparison_df = pd.DataFrame({
        'Model': model_names,
        'Emotion Accuracy': emotion_accuracy,
        'Cause Accuracy': cause_accuracy,
        'Both Correct': both_accuracy
    })
    
    # Plot comparison
    plt.figure(figsize=(12, 8))
    
    bar_width = 0.25
    index = range(len(model_names))
    
    plt.bar([i - bar_width for i in index], emotion_accuracy, bar_width, label='Emotion Accuracy', color='blue')
    plt.bar(index, cause_accuracy, bar_width, label='Cause Accuracy', color='green')
    plt.bar([i + bar_width for i in index], both_accuracy, bar_width, label='Both Correct', color='red')
    
    plt.xlabel('Model')
    plt.ylabel('Accuracy')
    plt.title('Model Comparison')
    plt.xticks(index, model_names, rotation=45)
    plt.legend()
    plt.tight_layout()
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "model_comparison.png")
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved model comparison to {output_path}")
    
    # Save the comparison data
    comparison_csv = os.path.join(output_dir, "model_comparison.csv")
    comparison_df.to_csv(comparison_csv, index=False)
    logger.info(f"Saved model comparison data to {comparison_csv}")
    
    return comparison_df

def analyze_misclassifications(results):
    """Analyze common misclassifications of emotions."""
    misclassifications = []
    
    for result in results:
        if not result["emotion_correct"]:
            true_emotion = result["true_emotion"].split(" & ")[0]  # Use first emotion for simplicity
            pred_emotion = result["predicted_emotion"].split(" & ")[0]
            
            misclassifications.append({
                "true_emotion": true_emotion,
                "predicted_emotion": pred_emotion,
                "scenario": result["scenario"],
                "subject": result["subject"],
                "qid": result["qid"]
            })
    
    return misclassifications

def plot_top_misclassifications(results, model_name, output_dir, top_n=10):
    """Plot the top N most common emotion misclassifications."""
    misclass = analyze_misclassifications(results)
    
    if not misclass:
        logger.info("No misclassifications found.")
        return
    
    # Count misclassification pairs
    misclass_counts = {}
    for item in misclass:
        key = f"{item['true_emotion']} → {item['predicted_emotion']}"
        if key in misclass_counts:
            misclass_counts[key] += 1
        else:
            misclass_counts[key] = 1
    
    # Sort by count (descending)
    sorted_misclass = sorted(misclass_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Take top N
    top_misclass = sorted_misclass[:top_n]
    
    # Prepare data for plotting
    labels = [item[0] for item in top_misclass]
    counts = [item[1] for item in top_misclass]
    
    # Plot horizontal bar chart
    plt.figure(figsize=(12, 8))
    y_pos = range(len(labels))
    plt.barh(y_pos, counts, align='center')
    plt.yticks(y_pos, labels)
    plt.xlabel('Count')
    plt.title(f'Top {top_n} Emotion Misclassifications - {model_name}')
    plt.tight_layout()
    
    # Save figure
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{model_name}_top_misclassifications.png")
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved top misclassifications to {output_path}")
    
    # Save misclassification details to CSV for further analysis
    misclass_df = pd.DataFrame(misclass)
    csv_path = os.path.join(output_dir, f"{model_name}_misclassifications.csv")
    misclass_df.to_csv(csv_path, index=False)
    logger.info(f"Saved misclassification details to {csv_path}")

def main():
    parser = argparse.ArgumentParser(description="Analyze and visualize emotional understanding results")
    parser.add_argument("--model", help="Specific model directory to analyze (e.g., gpt-4-1-nano)")
    parser.add_argument("--compare", action="store_true", help="Compare all available models")
    parser.add_argument("--output_dir", default="results/analysis", help="Directory to save analysis results")
    args = parser.parse_args()
    
    # Configure fonts for CJK characters
    configure_fonts()
    
    # Load environment variables to get access to GPT_MODEL 
    load_dotenv()
    
    # Determine directories to process
    results_dir = "results"
    if args.model:
        model_dirs = [args.model]
    else:
        # Get all model directories
        model_dirs = [d for d in os.listdir(results_dir) 
                      if os.path.isdir(os.path.join(results_dir, d)) 
                      and os.path.exists(os.path.join(results_dir, d, "results.jsonl"))]
    
    logger.info(f"Analyzing models: {', '.join(model_dirs)}")
    
    # Process each model
    all_results = []
    for model_dir in model_dirs:
        result = analyze_model_results(model_dir)
        if result:
            all_results.append(result)
            
            # Create individual model visualizations
            output_dir = os.path.join(args.output_dir, model_dir)
            os.makedirs(output_dir, exist_ok=True)
            
            # Plot confusion matrix
            plot_confusion_matrix(result["confusion_matrix"], model_dir, output_dir)
            
            # Plot accuracy metrics
            plot_accuracy_metrics(result["metrics"], model_dir, output_dir)
            
            # Save metrics as JSON
            metrics_json_path = os.path.join(output_dir, "metrics.json")
            with open(metrics_json_path, 'w') as f:
                json.dump(result["metrics"], f, indent=2)
            logger.info(f"Saved metrics to {metrics_json_path}")
            
            # Plot top misclassifications
            plot_top_misclassifications(result["dataframe"].to_dict('records'), model_dir, output_dir)
    
    # Compare models if requested or if multiple models are being analyzed
    if args.compare or len(all_results) > 1:
        comparison = compare_models(all_results, args.output_dir)
        if comparison is not None:
            logger.info("\nModel Comparison Summary:")
            print(comparison.to_string(index=False))

if __name__ == "__main__":
    main() 