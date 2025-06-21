# YaraBench Model Performance Analysis Report

*Generated: 2025-06-21 19:10 UTC*

## Executive Summary

This report analyzes the performance of **15 AI models** in generating YARA rules across **32 different security challenges**. The evaluation covers various aspects of YARA rule generation including syntax validity, detection accuracy, and generation speed.

### Key Findings

- **Best Performing Model**: deepseek/deepseek-chat-v3-0324 with an average score of **0.924**
- **Overall Success Rate**: 76.5% across all models
- **Fastest Model**: meta-llama/llama-4-maverick with 1836ms average latency
- **Most Consistent**: deepseek/deepseek-chat-v3-0324 with 23 perfect scores

## Model Performance Leaderboard

| Rank | Model | Provider | Avg Score | Success Rate | Perfect Scores | Syntax Errors | Avg Latency |
|------|-------|----------|-----------|--------------|----------------|---------------|-------------|
| 6 | **deepseek-chat-v3-0324** | Deepseek | 0.924 | 96.9% | 23 | 1 | 11671ms |
| 7 | **deepseek-r1** | Deepseek | 0.901 | 96.9% | 20 | 1 | 22676ms |
| 1 | **llama-4-maverick** | Meta-llama | 0.896 | 96.9% | 19 | 1 | 1836ms |
| 9 | **mistral-small-3.2-24b-instruct:free** | Mistralai | 0.885 | 90.6% | 25 | 3 | 2866ms |
| 13 | **phi-4** | Microsoft | 0.833 | 87.5% | 20 | 4 | 2665ms |
| 12 | **gemma-3-12b-it** | Google | 0.823 | 87.5% | 21 | 4 | 7737ms |
| 5 | **qwen3-14b** | Qwen | 0.791 | 81.2% | 21 | 6 | 9178ms |
| 11 | **gemma-3-27b-it** | Google | 0.789 | 81.2% | 21 | 6 | 5977ms |
| 4 | **qwen3-30b-a3b** | Qwen | 0.777 | 81.2% | 19 | 6 | 13519ms |
| 15 | **llama-3.3-70b-instruct** | Meta-llama | 0.763 | 78.1% | 18 | 7 | 3484ms |
| 14 | **wizardlm-2-8x22b** | Microsoft | 0.726 | 84.4% | 11 | 5 | 11342ms |
| 3 | **qwen3-32b** | Qwen | 0.678 | 71.9% | 13 | 9 | 22756ms |
| 2 | **llama-3.1-8b-instruct** | Meta-llama | 0.613 | 68.8% | 11 | 10 | 2077ms |
| 10 | **magistral-medium-2506** | Mistralai | 0.263 | 28.1% | 7 | 23 | 22514ms |
| 8 | **mistral-nemo** | Mistralai | 0.203 | 15.6% | 4 | 27 | 4451ms |

## Performance by Provider

| Provider | Models | Avg Score | Avg Success Rate | Avg Latency |
|----------|--------|-----------|------------------|-------------|
| Deepseek | 2 | 0.913 | 96.9% | 17173ms |
| Google | 2 | 0.806 | 84.4% | 6857ms |
| Microsoft | 2 | 0.779 | 85.9% | 7003ms |
| Meta-llama | 3 | 0.757 | 81.2% | 2465ms |
| Qwen | 3 | 0.749 | 78.1% | 15151ms |
| Mistralai | 3 | 0.450 | 44.8% | 9944ms |

## Challenge Analysis

### Most Difficult Challenges
| Challenge | Success Rate | Avg Score | Std Dev |
|-----------|--------------|-----------|---------|
| Position At 001 | 20.0% | 0.173 | 0.347 |
| String Hex Pattern 001 | 33.3% | 0.364 | 0.419 |
| Ransomware 001 | 53.3% | 0.553 | 0.454 |
| Filesize Exact 001 | 60.0% | 0.520 | 0.425 |
| Filesize Range 001 | 60.0% | 0.520 | 0.425 |

### Easiest Challenges
| Challenge | Success Rate | Avg Score | Std Dev |
|-----------|--------------|-----------|---------|
| Advanced Ransomware 001 | 93.3% | 0.876 | 0.248 |
| False Positive Risk 001 | 93.3% | 0.580 | 0.075 |
| Insufficient Info 001 | 93.3% | 0.847 | 0.228 |
| Not Actionable 001 | 93.3% | 0.873 | 0.221 |
| Packer Multiple 001 | 93.3% | 0.893 | 0.259 |

## Model-Specific Insights

### Top Performers Analysis

#### 1. deepseek/deepseek-chat-v3-0324
- **Average Score**: 0.924
- **Strengths**: Perfect scores in 23 challenges
- **Processing Speed**: 11671ms average latency
- **Reliability**: 1 syntax errors out of 32 challenges

#### 2. deepseek/deepseek-r1
- **Average Score**: 0.901
- **Strengths**: Perfect scores in 20 challenges
- **Processing Speed**: 22676ms average latency
- **Reliability**: 1 syntax errors out of 32 challenges

#### 3. meta-llama/llama-4-maverick
- **Average Score**: 0.896
- **Strengths**: Perfect scores in 19 challenges
- **Processing Speed**: 1836ms average latency
- **Reliability**: 1 syntax errors out of 32 challenges

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
