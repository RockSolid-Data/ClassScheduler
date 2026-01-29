import json
import os


class SettingsDAO:
    """
    Data Access Object for application settings.
    
    Stores settings in a JSON file in the user's home directory.
    This approach avoids modifying the database model while providing
    persistent storage for user preferences like UI colors.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the SettingsDAO.
        
        Args:
            logger: Optional logger instance for error tracking
        """
        self.logger = logger
        # Store settings in user's home directory
        self.config_file = os.path.join(
            os.path.expanduser('~'), 
            '.classscheduler_settings.json'
        )
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """
        Create the settings file if it doesn't exist.
        
        This ensures the file is ready for read/write operations
        without causing errors on first run.
        """
        if not os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'w') as f:
                    json.dump({}, f)
                if self.logger:
                    self.logger.info(f"Created settings file: {self.config_file}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error creating settings file: {e}")
    
    def get_setting(self, key):
        """
        Retrieve a setting value by key.
        
        Args:
            key: The setting key to retrieve (e.g., 'main_bg_color')
            
        Returns:
            The setting value if found, None otherwise
        """
        try:
            with open(self.config_file, 'r') as f:
                settings = json.load(f)
                return settings.get(key)
        except FileNotFoundError:
            # File doesn't exist yet, recreate it
            self._ensure_config_exists()
            return None
        except json.JSONDecodeError:
            if self.logger:
                self.logger.error(f"Invalid JSON in settings file, resetting")
            # Corrupted file, reset it
            self._ensure_config_exists()
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error reading setting '{key}': {e}")
            return None
    
    def set_setting(self, key, value):
        """
        Save a setting value.
        
        Args:
            key: The setting key (e.g., 'main_bg_color')
            value: The value to store (will be JSON serialized)
            
        Raises:
            Exception: If unable to save the setting
        """
        try:
            # Read existing settings
            try:
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                # File doesn't exist or is corrupted, start fresh
                settings = {}
            
            # Update the setting
            settings[key] = value
            
            # Write back to file
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            if self.logger:
                self.logger.info(f"Saved setting '{key}' = '{value}'")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving setting '{key}': {e}")
            raise
    
    def get_all_settings(self):
        """
        Retrieve all settings as a dictionary.
        
        Returns:
            Dictionary of all settings, or empty dict if none exist
        """
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error reading all settings: {e}")
            return {}
    
    def delete_setting(self, key):
        """
        Delete a specific setting.
        
        Args:
            key: The setting key to delete
            
        Returns:
            True if deleted, False if key didn't exist
        """
        try:
            with open(self.config_file, 'r') as f:
                settings = json.load(f)
            
            if key in settings:
                del settings[key]
                
                with open(self.config_file, 'w') as f:
                    json.dump(settings, f, indent=2)
                
                if self.logger:
                    self.logger.info(f"Deleted setting '{key}'")
                return True
            return False
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error deleting setting '{key}': {e}")
            return False
