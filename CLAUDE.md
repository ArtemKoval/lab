# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal experimentation lab containing independent projects for exploring ML, AI, and data science concepts. Projects are standalone - no shared build system or test suite.

## Environment Setup

Base conda environment (for time series work):
```bash
conda env create -f environment.yml  # Creates 'timecast' env with Python 3.10
conda activate timecast
```

Individual projects may have their own `requirements.txt` files - install dependencies per-project as needed.

## Project Categories

- **anomaly_detection/**: Time series anomaly detection (Prophet, KNN, Z-score, Isolation Forest, sktime)
- **advanced_rag/**: RAG experiments with cross-encoders, DPR, query expansion
- **rag/**, **lang_chain/**: RAG and LangChain experiments (Jupyter notebooks)
- **llm_local_ai_apps/**: Local LLM applications (DeepSeek, Gemma3, QwQ)
- **small_language_models/**: LLM fine-tuning and domain adaptation notebooks
- **ai_products/**: AI product strategy and opportunity analysis notebooks
- **time_series/**: Time series forecasting (includes Transformer models)
- **mermaid_js/**: Mermaid diagram documentation files
- **rad-master/**, **high_perf_node_redis-master/**, **file_app-master/**: Node.js projects (have their own package.json)

## Running Code

Python scripts: `python <script.py>` (ensure correct environment is activated)
Jupyter notebooks: `jupyter lab` then open the notebook
Node.js projects: Check individual project README and use `npm install` / `npm start`
