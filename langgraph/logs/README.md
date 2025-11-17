# Logfire Integration

This folder contains the centralized Logfire configuration for the langgraph system.

## Setup

1. **Get your Logfire token:**
   - Sign up at https://logfire.pydantic.dev/
   - Create a project
   - Copy your project token

2. **Add token to .env file:**
   ```bash
   LOGFIRE_TOKEN=your_token_here
   ```

3. **Install Logfire:**
   ```bash
   pip install logfire
   ```

## How It Works

- `logfire_config.py` sets up Logfire and integrates it with Python's logging module
- All existing `logger.info()`, `logger.error()`, etc. calls are automatically captured by Logfire
- No code changes needed in individual files - just import `get_logger` instead of using `logging.getLogger`

## Usage

The setup happens automatically when you run `build_supervisor_graph.py`. All logs will appear in:
- Your terminal (as before)
- Logfire UI (with nice visualization, traces, and search)

## Features

- All existing log messages are captured
- Console output remains unchanged
- Logfire UI provides:
  - Search and filtering
  - Log aggregation
  - Performance metrics
  - Error tracking
