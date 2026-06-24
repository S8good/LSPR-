import json
import os


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".nanosense")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def get_default_settings():
    default_db_path = os.path.join(CONFIG_DIR, "nanosense_data.db")
    return {
        "default_save_path": "",
        "default_load_path": "",
        "analysis_wl_start": 450.0,
        "analysis_wl_end": 750.0,
        "theme": "dark",
        "database_path": default_db_path,
        "lspr_master_root": "",
        "lspr_default_model_mode": "auto",
        "lspr_default_artifact_dir": "",
        "lspr_enable_digital_twin_overlay": True,
        "lspr_batch_export_dir": "",
        "onboarding_welcome_done": False,
        "onboarding_main_window_done": False,
        "mock_api_config": {
            "mode": "dynamic",
            "static_peak_pos": 650.0,
            "static_peak_amp": 15000.0,
            "static_peak_width": 10.0,
            "noise_level": 50.0,
            "dynamic_initial_pos": 650.0,
            "dynamic_shift_total": 10.0,
            "dynamic_baseline_duration": 5,
            "dynamic_assoc_duration": 20,
            "dynamic_dissoc_duration": 30,
        },
    }


def load_settings():
    defaults = get_default_settings()
    if not os.path.exists(CONFIG_FILE):
        return defaults

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
            settings = json.load(handle)
        for key, value in defaults.items():
            settings.setdefault(key, value)
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    settings[key].setdefault(sub_key, sub_value)
        return settings
    except (json.JSONDecodeError, IOError) as exc:
        print(f"Failed to load config: {exc}")
        return defaults


def save_settings(settings):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=4)
    except IOError as exc:
        print(f"Failed to save config: {exc}")
