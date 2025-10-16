# Backend

```bash
# From agenticAI root directory
mkdir backend
cd backend
pyenv install 3.11.9  # install
pyenv local 3.11.9    # make it local
python --version  # check version
pyenv install --list | grep 3.11  # check available python versions

# setup virtual enviroment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]" 
```