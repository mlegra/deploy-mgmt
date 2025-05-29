# Deployment Management App

A Flask-based web application for tracking and managing software deployments across different environments (PreDEV, DEV, UAT, PPD, PRD).

## Features

- 📦 Track feature deployments across multiple environments
- 🔍 Filter and search deployment records
- 📊 Generate deployment reports and KPIs
- ✅ Visual status indicators for deployment states
- 📤 Export filtered data to CSV
- 🎯 Interactive deployment matrix view

## Requirements

- **Python 3.13+** (This project uses Python 3.13)
- Flask 3.0.3

## Setup Instructions

### 1. Clone the Repository

```bash
git clone git@github.com:mlegra/deployment-app.git
cd deployment-app
```

### 2. Install Python 3.13 using pyenv (Recommended)

If you don't have Python 3.13 installed, we recommend using pyenv to manage Python versions:

```bash
# Install pyenv (macOS with Homebrew)
brew install pyenv

# Or install pyenv (Linux/macOS with curl)
curl https://pyenv.run | bash

# Add pyenv to your shell profile (add to ~/.bashrc, ~/.zshrc, etc.)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Restart your shell or source your profile
source ~/.zshrc
or 
source ~/.bashrc

# Install Python 3.13.3
pyenv install 3.13.3

# Set Python 3.13.3 as the local version for this project
pyenv local 3.13.3

# Verify installation
python --version  # Should show Python 3.13.3
```

### 3. Create a Virtual Environment

It's recommended to use a virtual environment to isolate project dependencies:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000` by default.

## Project Structure

```
deployment-app/
├── app.py              # Main Flask application
├── model.py            # Database models and operations
├── utils.py            # Utility functions for KPI calculations
├── requirements.txt    # Python dependencies
├── deployments.db      # SQLite database (auto-created)
├── templates/          # HTML templates
│   ├── index.html      # Main dashboard
│   ├── reports.html    # Reports page
│   └── indexOld.html   # Legacy template
└── __pycache__/        # Python bytecode cache
```

## Usage

1. **Dashboard** (`/`): Main interface for registering new deployments and viewing the deployment matrix
2. **Reports** (`/reports`): Advanced filtering and reporting with date range support

### Adding a New Deployment

1. Fill out the deployment form with:
   - Feature name
   - Repository
   - Type (PersDB, App, MDSGen, MDSHealth)
   - Environment (PreDEV, DEV, UAT, PPD, PRD)
   - Date
   - Release Manager
   - Status (Valid, Invalid, Failed, Archived, In-PRD)

2. Click "💾 Guardar" to save

### Viewing Deployments

- Use the deployment matrix to see all features and their status across environments
- Click ✎ or ➕ buttons to edit existing deployments or add new ones
- Use filters to search by text, status, or environment

## Database

The application uses SQLite with two main tables:
- `features`: Stores feature information (name, repo, type, etc.)
- `deployments`: Stores deployment records linked to features

The database is automatically created when you first run the application.

## Development

To run in development mode:

```bash
export FLASK_ENV=development
python app.py
```

## Deactivating Virtual Environment

When you're done working with the project:

```bash
deactivate
```
