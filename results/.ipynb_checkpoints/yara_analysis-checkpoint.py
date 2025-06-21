#!/usr/bin/env python3
"""
YaraBench Model Performance Analysis
Analyzes YARA rule generation performance across different AI models
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from collections import defaultdict
import warnings
import sys
import os
warnings.filterwarnings('ignore')

# Set style for better-looking plots
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except:
    plt.style.use('ggplot')

def load_data(filename='commercial_model_comparison_fused.json'):
    """Load the JSON data"""
    with open(filename, 'r') as f:
        return json.load(f)

def extract_model_info(model_name):
    """Extract provider and model from model name"""
    if '/' in model_name:
        provider, model = model_name.split('/', 1)
        return provider.capitalize(), model
    return 'Unknown', model_name

def analyze_challenge_performance(data):
    """Analyze performance by challenge type"""
    challenge_stats = defaultdict(lambda: {'total': 0, 'successful': 0, 'scores': []})
    
    for model_data in data:
        for result in model_data['results']:
            challenge_id = result['challenge_id']
            challenge_stats[challenge_id]['total'] += 1
            if result['score'] > 0.5:  # Consider score > 0.5 as successful
                challenge_stats[challenge_id]['successful'] += 1
            challenge_stats[challenge_id]['scores'].append(result['score'])
    
    # Calculate average score and success rate for each challenge
    for challenge_id, stats in challenge_stats.items():
        stats['avg_score'] = np.mean(stats['scores'])
        stats['success_rate'] = stats['successful'] / stats['total']
        stats['std_dev'] = np.std(stats['scores'])
    
    return challenge_stats

def create_performance_dataframe(data):
    """Create a comprehensive performance dataframe"""
    rows = []
    
    for model_data in data:
        provider, model_name = extract_model_info(model_data['model'])
        
        # Calculate additional metrics
        total_score = sum(r['score'] for r in model_data['results'])
        syntax_errors = sum(1 for r in model_data['results'] if not r.get('valid_syntax', True))
        perfect_scores = sum(1 for r in model_data['results'] if r['score'] == 1.0)
        
        # Calculate average latency
        latencies = [r.get('latency_ms', 0) for r in model_data['results'] if r.get('latency_ms')]
        avg_latency = np.mean(latencies) if latencies else 0
        
        row = {
            'Provider': provider,
            'Model': model_name,
            'Full Name': model_data['model'],
            'Total Challenges': model_data['total_challenges'],
            'Successful': model_data['successful_challenges'],
            'Success Rate': model_data['successful_challenges'] / model_data['total_challenges'],
            'Average Score': model_data['average_score'],
            'Total Score': total_score,
            'Perfect Scores': perfect_scores,
            'Syntax Errors': syntax_errors,
            'Avg Latency (ms)': avg_latency,
            'Total Time (s)': model_data['total_time_ms'] / 1000
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df = df.sort_values('Average Score', ascending=False)
    return df

def create_visualization(df, challenge_stats):
    """Create a comprehensive visualization"""
    fig = plt.figure(figsize=(20, 12))
    
    # Create a 2x2 grid with equal spacing
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # 1. Model Performance Bar Chart (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    # Reverse the order so best models appear on top
    models = df['Model'].values[::-1]
    scores = df['Average Score'].values[::-1]
    colors = plt.cm.viridis(scores / scores.max())
    
    bars = ax1.barh(models, scores, color=colors, edgecolor='black', linewidth=1)
    ax1.set_xlabel('Average Score', fontsize=12, fontweight='bold')
    ax1.set_title('YARA Rule Generation Performance by Model', fontsize=16, fontweight='bold', pad=20)
    
    # Dynamic x-axis range based on actual scores
    min_score = scores.min()
    max_score = scores.max()
    padding = (max_score - min_score) * 0.1
    ax1.set_xlim(max(0, min_score - padding), min(1.0, max_score + padding))
    
    # Add value labels
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax1.text(score + 0.002, bar.get_y() + bar.get_height()/2, 
                f'{score:.3f}', va='center', fontsize=10)
    
    # 2. Success Rate vs Latency Scatter (top right)
    ax2 = fig.add_subplot(gs[0, 1])
    scatter = ax2.scatter(df['Avg Latency (ms)'] / 1000, df['Success Rate'] * 100, 
                         s=df['Total Score'] * 5, alpha=0.7, 
                         c=range(len(df)), cmap='tab10')
    ax2.set_xlabel('Average Latency (seconds)', fontsize=12)
    ax2.set_ylabel('Success Rate (%)', fontsize=12)
    ax2.set_title('Performance vs Speed Trade-off', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Add model labels
    for idx, row in df.iterrows():
        ax2.annotate(row['Model'].split('-')[0], 
                    (row['Avg Latency (ms)']/1000, row['Success Rate']*100),
                    fontsize=8, alpha=0.7)
    
    # 3. Provider Comparison (bottom left)
    ax3 = fig.add_subplot(gs[1, 0])
    provider_stats = df.groupby('Provider').agg({
        'Average Score': 'mean',
        'Success Rate': 'mean',
        'Avg Latency (ms)': 'mean'
    }).sort_values('Average Score', ascending=False)
    
    provider_stats['Average Score'].plot(kind='bar', ax=ax3, color='skyblue', 
                                        edgecolor='black', linewidth=1)
    ax3.set_title('Average Performance by Provider', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Average Score', fontsize=12)
    ax3.set_xticklabels(ax3.get_xticklabels(), rotation=45, ha='right')
    
    # Dynamic y-axis range for provider comparison
    provider_min = provider_stats['Average Score'].min()
    provider_max = provider_stats['Average Score'].max()
    provider_padding = (provider_max - provider_min) * 0.1
    ax3.set_ylim(max(0, provider_min - provider_padding), min(1.0, provider_max + provider_padding))
    
    # Add value labels
    for i, v in enumerate(provider_stats['Average Score']):
        ax3.text(i, v + 0.001, f'{v:.3f}', ha='center', fontsize=10)
    
    # 4. Challenge Difficulty Analysis (bottom right)
    ax4 = fig.add_subplot(gs[1, 1])
    challenge_df = pd.DataFrame([
        {
            'Challenge': k.replace('l1_', '').replace('_', ' ').title(),
            'Success Rate': v['success_rate'],
            'Avg Score': v['avg_score'],
            'Std Dev': v['std_dev']
        }
        for k, v in challenge_stats.items()
    ]).sort_values('Success Rate')
    
    # Show top 10 hardest and easiest challenges
    hardest = challenge_df.head(10)
    easiest = challenge_df.tail(10)
    combined = pd.concat([hardest, easiest])
    
    y_pos = np.arange(len(combined))
    colors = ['red' if x < 0.9 else 'green' for x in combined['Success Rate']]
    
    bars = ax4.barh(y_pos, combined['Success Rate'], color=colors, alpha=0.7, 
                    edgecolor='black', linewidth=1)
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(combined['Challenge'], fontsize=9)
    ax4.set_xlabel('Success Rate', fontsize=12)
    ax4.set_title('Hardest and Easiest Challenges', fontsize=14, fontweight='bold')
    ax4.axvline(x=0.9, color='black', linestyle='--', alpha=0.5, label='90% threshold')
    
    # Add value labels
    for i, (bar, rate) in enumerate(zip(bars, combined['Success Rate'])):
        ax4.text(rate + 0.01, bar.get_y() + bar.get_height()/2, 
                f'{rate:.2f}', va='center', fontsize=9)
    
    # Overall title
    fig.suptitle('YaraBench: Comprehensive YARA Rule Generation Analysis', 
                 fontsize=20, fontweight='bold', y=0.98)
    
    # Add timestamp
    plt.figtext(0.99, 0.01, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 
                ha='right', fontsize=10, alpha=0.7)
    
    plt.tight_layout()

def generate_markdown_report(df, challenge_stats, data):
    """Generate a comprehensive Markdown report"""
    
    # Calculate additional statistics
    total_challenges_run = sum(df['Total Challenges'])
    total_successful = sum(df['Successful'])
    overall_success_rate = total_successful / total_challenges_run
    
    report = f"""# YaraBench Model Performance Analysis Report

*Generated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}*

## Executive Summary

This report analyzes the performance of **{len(df)} AI models** in generating YARA rules across **{df['Total Challenges'].iloc[0]} different security challenges**. The evaluation covers various aspects of YARA rule generation including syntax validity, detection accuracy, and generation speed.

### Key Findings

- **Best Performing Model**: {df.iloc[0]['Full Name']} with an average score of **{df.iloc[0]['Average Score']:.3f}**
- **Overall Success Rate**: {overall_success_rate:.1%} across all models
- **Fastest Model**: {df.loc[df['Avg Latency (ms)'].idxmin(), 'Full Name']} with {df['Avg Latency (ms)'].min():.0f}ms average latency
- **Most Consistent**: {df.loc[df['Total Score'].idxmax(), 'Full Name']} with {df.loc[df['Total Score'].idxmax(), 'Perfect Scores']} perfect scores

## Model Performance Leaderboard

| Rank | Model | Provider | Avg Score | Success Rate | Perfect Scores | Syntax Errors | Avg Latency |
|------|-------|----------|-----------|--------------|----------------|---------------|-------------|
"""
    
    for i, row in df.iterrows():
        report += f"| {i+1} | **{row['Model']}** | {row['Provider']} | {row['Average Score']:.3f} | {row['Success Rate']:.1%} | {row['Perfect Scores']} | {row['Syntax Errors']} | {row['Avg Latency (ms)']:.0f}ms |\n"
    
    report += f"""
## Performance by Provider

| Provider | Models | Avg Score | Avg Success Rate | Avg Latency |
|----------|--------|-----------|------------------|-------------|
"""
    
    provider_summary = df.groupby('Provider').agg({
        'Model': 'count',
        'Average Score': 'mean',
        'Success Rate': 'mean',
        'Avg Latency (ms)': 'mean'
    }).sort_values('Average Score', ascending=False)
    
    for provider, stats in provider_summary.iterrows():
        report += f"| {provider} | {int(stats['Model'])} | {stats['Average Score']:.3f} | {stats['Success Rate']:.1%} | {stats['Avg Latency (ms)']:.0f}ms |\n"
    
    # Challenge Analysis
    sorted_challenges = sorted(challenge_stats.items(), key=lambda x: x[1]['success_rate'])
    
    report += f"""
## Challenge Analysis

### Most Difficult Challenges
| Challenge | Success Rate | Avg Score | Std Dev |
|-----------|--------------|-----------|---------|
"""
    
    for challenge_id, stats in sorted_challenges[:5]:
        challenge_name = challenge_id.replace('l1_', '').replace('_', ' ').title()
        report += f"| {challenge_name} | {stats['success_rate']:.1%} | {stats['avg_score']:.3f} | {stats['std_dev']:.3f} |\n"
    
    report += f"""
### Easiest Challenges
| Challenge | Success Rate | Avg Score | Std Dev |
|-----------|--------------|-----------|---------|
"""
    
    for challenge_id, stats in sorted_challenges[-5:]:
        challenge_name = challenge_id.replace('l1_', '').replace('_', ' ').title()
        report += f"| {challenge_name} | {stats['success_rate']:.1%} | {stats['avg_score']:.3f} | {stats['std_dev']:.3f} |\n"
    
    # Model-specific insights
    report += """
## Model-Specific Insights

### Top Performers Analysis
"""
    
    for i in range(min(3, len(df))):
        row = df.iloc[i]
        model_data = next(m for m in data if m['model'] == row['Full Name'])
        
        # Analyze strengths
        challenge_scores = [(r['challenge_id'], r['score']) for r in model_data['results']]
        perfect_challenges = [c[0] for c in challenge_scores if c[1] == 1.0]
        
        report += f"""
#### {i+1}. {row['Full Name']}
- **Average Score**: {row['Average Score']:.3f}
- **Strengths**: Perfect scores in {len(perfect_challenges)} challenges
- **Processing Speed**: {row['Avg Latency (ms)']:.0f}ms average latency
- **Reliability**: {row['Syntax Errors']} syntax errors out of {row['Total Challenges']} challenges
"""
    
    report += """
## Methodology

The evaluation tested each model's ability to generate YARA rules for various security scenarios including:
- Ransomware detection
- Anti-VM/sandbox evasion techniques
- Information stealers
- Backdoor detection
- Cryptominers
- Various obfuscation techniques

Each rule was evaluated on:
1. **Syntax Validity**: Whether the generated YARA rule compiles successfully
2. **Detection Accuracy**: Whether the rule correctly identifies malicious samples while avoiding false positives
3. **Expected Elements**: Presence of required strings and keywords
4. **Generation Speed**: Time taken to generate the rule

## Recommendations

Based on this analysis:

1. **For Production Use**: Consider {df.iloc[0]['Full Name']} for highest accuracy
2. **For Speed-Critical Applications**: Use {df.loc[df['Avg Latency (ms)'].idxmin(), 'Full Name']}
3. **For Balanced Performance**: {df.iloc[1]['Full Name']} offers good accuracy with reasonable speed

## Visualization

![YaraBench Analysis](yara_analysis_plot.png)

---

*This report was automatically generated from YaraBench evaluation data.*
"""
    
    return report

def main():
    """Main analysis function"""
    # Get input file from command line or use default
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'commercial_model_comparison_fused.json'
    
    # Extract base name for output files
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    if '_model_comparison' in base_name:
        prefix = base_name.split('_model_comparison')[0]
    else:
        prefix = base_name
    
    # Define output filenames
    output_plot = f'{prefix}_analysis_plot.png'
    output_report = f'{prefix}_analysis_report.md'
    output_csv = f'{prefix}_analysis_results.csv'
    
    print(f"Loading data from {input_file}...")
    data = load_data(input_file)
    
    print("Analyzing challenge performance...")
    challenge_stats = analyze_challenge_performance(data)
    
    print("Creating performance dataframe...")
    df = create_performance_dataframe(data)
    
    print("\nModel Performance Summary:")
    print(df[['Model', 'Provider', 'Average Score', 'Success Rate', 'Avg Latency (ms)']].to_string())
    
    print("\nGenerating visualization...")
    create_visualization(df, challenge_stats)
    plt.savefig(output_plot, dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Generating Markdown report...")
    report = generate_markdown_report(df, challenge_stats, data)
    
    with open(output_report, 'w') as f:
        f.write(report)
    
    # Save detailed results table
    df.to_csv(output_csv, index=False)
    
    print("\n✅ Analysis complete!")
    print("📊 Generated files:")
    print(f"  - {output_plot} (visualization)")
    print(f"  - {output_report} (detailed report)")
    print(f"  - {output_csv} (full results table)")

if __name__ == "__main__":
    main()