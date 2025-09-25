"""
Configuration management for the monitoring application
"""

import os
from typing import Dict, Any

import yaml


class MonitoringConfig:
    """Configuration manager for the monitoring application"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or "monitoring_config.yaml"
        self.config = self._load_default_config()

        if os.path.exists(self.config_file):
            self._load_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            "api": {
                "base_url": "http://localhost:8000",
                "timeout": 10,
                "endpoints": [
                    "/",
                    "/health",
                    "/regions",
                    "/wines",
                    "/search/wines"
                ]
            },
            "monitoring": {
                "check_interval": 30,
                "metrics_retention": 1000,
                "alert_retention_days": 7
            },
            "monitoring_agent": {
                "response_time_threshold": 2.0,
                "error_rate_threshold": 0.05,
                "anomaly_sensitivity": 2.0,
                "baseline_window": 50
            },
            "dashboard": {
                "refresh_interval": 1,
                "max_alerts_display": 10,
                "max_insights_display": 5
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "monitoring.log"
            }
        }

    def _load_config(self) -> None:
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                self._merge_config(self.config, file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")

    def _merge_config(self, base: Dict, override: Dict) -> None:
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'api.base_url')"""
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")

    def create_sample_config(self) -> None:
        """Create a sample configuration file"""
        sample_config = {
            "api": {
                "base_url": "http://localhost:8000",
                "timeout": 10,
                "endpoints": [
                    "/",
                    "/health",
                    "/regions",
                    "/wines",
                    "/search/wines"
                ]
            },
            "monitoring": {
                "check_interval": 30,
                "metrics_retention": 1000,
                "alert_retention_days": 7
            },
            "monitoring_agent": {
                "response_time_threshold": 2.0,
                "error_rate_threshold": 0.05,
                "anomaly_sensitivity": 2.0,
                "baseline_window": 50
            },
            "dashboard": {
                "refresh_interval": 1,
                "max_alerts_display": 10,
                "max_insights_display": 5
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "monitoring.log"
            }
        }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)

        print(f"Sample configuration created: {self.config_file}")


# Global config instance
config = MonitoringConfig()
