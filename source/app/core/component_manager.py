import traceback
import os
import tempfile
import shutil
import uno
from librepy.pybrex.values import pybrex_logger, GRAPHICS_DIR

logger = pybrex_logger(__name__)

class ComponentManager:
    """
    Manages the loading, disposal and lifecycle of UI components
    """
    
    def __init__(self, app, ctx, smgr, frame_manager, ps):
        """
        Initialize the component manager
        
        Args:
            app: The main application instance
            ctx: The UNO context
            smgr: The UNO service manager
            frame_manager: The frame manager instance 
            ps: Position and size tuple (x, y, width, height)
        """
        self.logger = logger
        self.logger.info("ComponentManager initialized")
        self.app = app
        self.ctx = ctx
        self.smgr = smgr
        self.frame_manager = frame_manager
        self.ps = ps
        
        self.active_component = None
        
        # Initialize icon cache on startup
        self.icon_cache = {}
        self._initialize_icon_cache()
        
        self._component_loaders = {
            'training_session_list': self._load_home_component,
            'calendar': self._load_calendar_component,
            'appointment_calendar': self._load_appointment_calendar_component,
            'employee_calendar': self._load_employee_calendar_component,
            # Add the rest of the components here
        }
        
        # Components that should use available area (accounting for sidebar)
        # Other components will use full area
        self._sidebar_aware_components = {'training_session_list', 'calendar', 'appointment_calendar', 'employee_calendar'}
    
    def get_available_area(self):
        """
        Calculate the available area for components, accounting for sidebar width
        
        Returns:
            tuple: (x, y, width, height) representing the available area for components
        """
        x, y, total_width, total_height = self.ps
        
        # Get current sidebar width from the app
        sidebar_width = 0
        if hasattr(self.app, 'sidebar_width') and self.app.sidebar_width is not None:
            sidebar_width = self.app.sidebar_width
        elif hasattr(self.app, 'sidebar_manager') and self.app.sidebar_manager is not None:
            sidebar_width = self.app.sidebar_manager.get_width()
        
        # Calculate available area (sidebar is on the left, so offset x and reduce width)
        available_x = x + sidebar_width
        available_y = y
        available_width = total_width - sidebar_width
        available_height = total_height
        
        self.logger.debug(f"Available area: x={available_x}, y={available_y}, width={available_width}, height={available_height} (sidebar_width={sidebar_width})")
        
        return (available_x, available_y, available_width, available_height)
    
    def _initialize_icon_cache(self):
        """Initialize icon cache by copying commonly used icons to permanent storage"""
        try:
            # List of icons that need to be cached
            icons_to_cache = [
                'copy_arrow_right.png'
            ]
            
            # Create permanent directory in temp folder
            temp_dir = os.path.join(tempfile.gettempdir(), '.librepy_component_icons')
            os.makedirs(temp_dir, exist_ok=True)
            
            for icon_filename in icons_to_cache:
                try:
                    # Get source path (from document)
                    source_path = os.path.join(GRAPHICS_DIR, icon_filename)
                    
                    # Destination path
                    dest_path = os.path.join(temp_dir, icon_filename)
                    
                    # Copy file if source exists and destination doesn't exist or is older
                    if os.path.exists(source_path):
                        if not os.path.exists(dest_path) or os.path.getmtime(source_path) > os.path.getmtime(dest_path):
                            shutil.copy2(source_path, dest_path)
                            self.logger.debug(f"Cached icon {icon_filename} to {dest_path}")
                        
                        # Store file:// URL in cache
                        self.icon_cache[icon_filename] = uno.systemPathToFileUrl(dest_path)
                    else:
                        self.logger.warning(f"Source icon not found: {source_path}")
                        
                except Exception as e:
                    self.logger.error(f"Error caching icon {icon_filename}: {str(e)}")
            
            self.logger.info(f"Icon cache initialized with {len(self.icon_cache)} icons")
            
        except Exception as e:
            self.logger.error(f"Error initializing icon cache: {str(e)}")
    
    def get_cached_icon_url(self, icon_filename):
        """Get a cached icon URL
        
        Args:
            icon_filename (str): Name of the icon file
            
        Returns:
            str: file:// URL of the cached icon or empty string if not found
        """
        return self.icon_cache.get(icon_filename, "")
        
    def _load_home_component(self):
        self.logger.info("Loading Home component")
        from librepy.app.components.home import home_view
        # Use available area (accounting for sidebar width)
        available_area = self.get_available_area()
        component = home_view.Home(
            self.app,
            self.ctx,
            self.smgr,
            self.frame_manager,
            available_area
        )
        component.show()
        return component

    def _load_calendar_component(self):
        self.logger.info("Loading Calendar component")
        from librepy.app.components.calendar.training_sessions_calendar import TrainingSessionsCalendar
        # Use available area (accounting for sidebar width)
        available_area = self.get_available_area()
        component = TrainingSessionsCalendar(
            self.app,
            self.ctx,
            self.smgr,
            self.frame_manager,
            available_area
        )
        component.show()
        return component

    def _load_appointment_calendar_component(self):
        self.logger.info("Loading Appointment Calendar component")
        from librepy.app.components.calendar.appointment_calendar import AppointmentCalendar
        available_area = self.get_available_area()
        component = AppointmentCalendar(
            self.app,
            self.ctx,
            self.smgr,
            self.frame_manager,
            available_area
        )
        component.show()
        return component

    def _load_employee_calendar_component(self):
        self.logger.info("Loading Employee Calendar component")
        from librepy.app.components.calendar.employee_calendar import EmployeeCalendar
        available_area = self.get_available_area()
        component = EmployeeCalendar(
            self.app,
            self.ctx,
            self.smgr,
            self.frame_manager,
            available_area
        )
        component.show()
        return component

    def load_component(self, component_name):
        """
        Load a component by name
        
        Args:
            component_name (str): Name of the component to load
            
        Returns:
            The loaded component or None if the component could not be loaded
        """
        if component_name not in self._component_loaders:
            self.logger.error(f"Unknown component name: {component_name}")
            return None
            
        try:
            loader_func = self._component_loaders[component_name]
            component = loader_func()
            if component is not None:
                if hasattr(component, 'resize'):
                    # Use appropriate area based on component type
                    if component_name in self._sidebar_aware_components:
                        # Use available area for sidebar-aware components
                        available_area = self.get_available_area()
                        component.resize(available_area[2], available_area[3])
                    else:
                        # Use full area for other components (like login)
                        component.resize(self.app.ps[2], self.app.ps[3])
            return component
        except Exception:
            self.logger.error(f"Error loading component {component_name}:")
            self.logger.error(traceback.format_exc())
            return None
    
    def dispose_component(self, component):
        """
        Dispose of a component properly
        
        Args:
            component: The component to dispose
        """
        if component is None:
            return
            
        try:
            self.logger.info(f"Disposing component: {component.__class__.__name__}")
            if hasattr(component, 'dispose'):
                component.dispose()
        except Exception:
            self.logger.error(f"Error disposing component {component.__class__.__name__}:")
            self.logger.error(traceback.format_exc())
    
    def switch_component(self, component_name):
        """
        Switch to a different component
        
        Args:
            component_name (str): Name of the component to switch to
            
        Returns:
            The newly loaded component or None if switch failed
        """
        if self.active_component is not None and component_name == getattr(self.active_component, '_view', None):
            return self.active_component
            
        if self.active_component is not None:
            self.dispose_component(self.active_component)
        
        self.active_component = self.load_component(component_name)
        return self.active_component
    
    def resize_active_component(self, width, height):
        """
        Resize the active component
        
        Args:
            width (int): The new width
            height (int): The new height
        """
        if self.active_component is None:
            return
            
        try:
            if hasattr(self.active_component, 'resize'):
                # Update stored dimensions first
                self.ps = (self.ps[0], self.ps[1], width, height)
                
                # Calculate available area for sidebar-aware components
                component_name = getattr(self.active_component, 'component_name', None)
                if component_name in self._sidebar_aware_components:
                    # Use available area for sidebar-aware components
                    available_area = self.get_available_area()
                    self.active_component.resize(available_area[2], available_area[3])
                else:
                    # Use full area for other components (like login)
                    self.active_component.resize(width, height)
        except Exception:
            self.logger.error(f"Error resizing component {self.active_component.__class__.__name__}:")
            self.logger.error(traceback.format_exc())
    
    def dispose(self):
        """Dispose of all components and clean up resources"""
        self.logger.info("Disposing ComponentManager")
        
        if self.active_component is not None:
            self.dispose_component(self.active_component)
                
        self.active_component = None 