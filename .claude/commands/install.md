# Install & Prime

## Read
config.yaml (never read .env)

## Read and Execute
./.claude/commands/prime.md

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

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "Environment variables loaded from .env"
else
    echo "Warning: .env file not found - you may need to set OPENAI_API_KEY manually"
fi

# Initialize the framework
python cli.py init

# Run database migrations
alembic upgrade head
```

## Validate
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

## Report
- Output the work you've just done in a concise bullet point list.