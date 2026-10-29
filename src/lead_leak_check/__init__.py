"""lead-leak-check: find where inbound leads are silently dropped."""
from .rules import analyze_history, check_config, check_description, config_from_text

__all__ = ["analyze_history", "check_config", "check_description", "config_from_text"]
__version__ = "0.1.0"
