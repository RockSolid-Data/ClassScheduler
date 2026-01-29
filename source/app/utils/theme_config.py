"""
Theme configuration manager for the application.
Loads and provides access to user-customized theme settings.
"""
from librepy.app.data.dao.settings_dao import SettingsDAO


class ThemeConfig:
    """
    Centralized theme configuration that loads user preferences
    from SettingsDAO and provides default values.
    """
    
    # Default color values
    DEFAULT_MAIN_BG_COLOR = "#F2F2F2"
    DEFAULT_SIDEBAR_BG_COLOR = "#357399"
    
    _instance = None
    _initialized = False
    
    def __new__(cls, logger=None):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(ThemeConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, logger=None):
        """Initialize theme config (only once due to singleton)"""
        if not ThemeConfig._initialized:
            self.logger = logger
            self.settings_dao = SettingsDAO(logger)
            self._load_colors()
            ThemeConfig._initialized = True
    
    def _load_colors(self):
        """Load color preferences from settings"""
        try:
            # Load main background color
            main_bg = self.settings_dao.get_setting('main_bg_color')
            self.main_bg_color = main_bg if main_bg else self.DEFAULT_MAIN_BG_COLOR
            
            # Load sidebar background color
            sidebar_bg = self.settings_dao.get_setting('sidebar_bg_color')
            self.sidebar_bg_color = sidebar_bg if sidebar_bg else self.DEFAULT_SIDEBAR_BG_COLOR
            
            if self.logger:
                self.logger.info(f"Theme loaded - Main BG: {self.main_bg_color}, Sidebar BG: {self.sidebar_bg_color}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading theme colors, using defaults: {e}")
            self.main_bg_color = self.DEFAULT_MAIN_BG_COLOR
            self.sidebar_bg_color = self.DEFAULT_SIDEBAR_BG_COLOR
    
    def reload(self):
        """Reload colors from settings (useful after settings change)"""
        self._load_colors()
    
    def get_main_bg_color_int(self):
        """Get main background color as integer (for UNO controls)"""
        try:
            hex_color = self.main_bg_color.replace('#', '')
            return int(hex_color, 16)
        except:
            return 0xF2F2F2  # Default fallback
    
    def get_sidebar_bg_color_int(self):
        """Get sidebar background color as integer (for UNO controls)"""
        try:
            hex_color = self.sidebar_bg_color.replace('#', '')
            return int(hex_color, 16)
        except:
            return 0x357399  # Default fallback
    
    def get_calendar_grid_bg_color_int(self):
        """Get calendar grid background color as integer (for UNO controls)
        
        Note: Calendar grid uses the same color as main background for consistency
        """
        return self.get_main_bg_color_int()
    
    def get_sidebar_colors_dict(self):
        """
        Get a complete color dictionary for sidebar configuration.
        Calculates derived colors (selected, hover) from the base sidebar color.
        """
        base_color = self.get_sidebar_bg_color_int()
        
        # Calculate darker shade for selected state (reduce brightness by ~15%)
        selected_color = self._adjust_brightness(base_color, 0.85)
        
        # Calculate lighter shade for hover state (increase brightness by ~10%)
        hover_color = self._adjust_brightness(base_color, 1.10)
        
        return {
            'background': base_color,
            'selected': selected_color,
            'hover': hover_color,
            'text': 0xFFFFFF,
            'text_selected': 0xFFFFFF,
            'text_hover': 0xFFFFFF,
            'title_text': 0xFFFFFF
        }
    
    def _adjust_brightness(self, color_int, factor):
        """
        Adjust the brightness of a color by a factor.
        
        Args:
            color_int: Integer color value (0xRRGGBB)
            factor: Brightness factor (< 1.0 = darker, > 1.0 = lighter)
        
        Returns:
            Adjusted color as integer
        """
        # Extract RGB components
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        
        # Adjust each component
        r = min(255, max(0, int(r * factor)))
        g = min(255, max(0, int(g * factor)))
        b = min(255, max(0, int(b * factor)))
        
        # Recombine
        return (r << 16) | (g << 8) | b


# Convenience function to get the singleton instance
def get_theme_config(logger=None):
    """Get the theme configuration singleton instance"""
    return ThemeConfig(logger)
