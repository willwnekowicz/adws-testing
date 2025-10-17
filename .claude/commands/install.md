# Install
> Install the ADWS Testing Framework and initialize the environment

## Create virtual environment
```bash
python3 -m venv venv
```

## Activate virtual environment
```bash
source venv/bin/activate
```

## Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Install package in development mode
```bash
pip install -e .
```

## Initialize database and directories
```bash
python cli.py init
```

## Run Alembic migrations
```bash
alembic upgrade head
```

## Validate configuration
```bash
python cli.py validate
```

## Set environment variables (if needed)
```bash
# Set your OpenAI API key for LLM judge features
export OPENAI_API_KEY="your-api-key-here"

# Optional: Override standard-configuration path
# export STANDARD_CONFIG_PATH="~/ai/standard-configuration"
```

## Verify installation
```bash
python cli.py --help
```