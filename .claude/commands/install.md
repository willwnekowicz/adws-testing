# Install
> Install the ADWS Testing Framework and initialize the environment

## Read
requirements.txt
setup.py
config.yaml

## Run
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Set environment variables (required for OpenAI LLM judge)
export OPENAI_API_KEY="your-api-key-here"

# Initialize the framework
python cli.py init

# Run database migrations
alembic upgrade head
```

## Report
```bash
# Validate configuration
python cli.py validate

# Show CLI help to confirm installation
python cli.py --help

# List Python packages
pip list | grep -E "sqlalchemy|alembic|psutil|click|openai|gitpython"

# Check database initialization
ls -la test_runs.db 2>/dev/null || echo "Database will be created on first run"
```