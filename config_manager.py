import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"groq_api_key": ""}

def save_config(config):
    """Save configuration to JSON file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_groq_api_key():
    """Get the Groq API key from config."""
    config = load_config()
    return config.get("groq_api_key", "")

def set_groq_api_key(api_key):
    """Save the Groq API key to config."""
    config = load_config()
    config["groq_api_key"] = api_key
    save_config(config)
