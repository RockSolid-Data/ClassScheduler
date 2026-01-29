'''
These functions and variables are made available by LibrePy
Check out the help manual for a full list

createUnoService()      # Implementation of the Basic CreateUnoService command
getUserPath()           # Get the user path of the currently running instance
thisComponent           # Current component instance
getDefaultContext()     # Get the default context
MsgBox()                # Simple msgbox that takes the same arguments as the Basic MsgBox
mri(obj)                # Mri the object. MRI must be installed for this to work
doc_object              # A generic object with a dict_values and list_values that are persistent

To import files inside this project, use the 'librepy' keyword
For example, to import a file named config, use the following:
from librepy import config
'''
import traceback
from librepy.utils.window_geometry_config_manager import WindowGeometryConfigManager

from librepy.pybrex.values import pybrex_logger
logger = pybrex_logger(__name__)

class App(object):
    """App application"""
    
    def __init__(self, ctx, smgr):
        self.logger = logger
        self.logger.info("APP: Initializing App application")
        
        self.ctx = ctx
        self.smgr = smgr
        
        self._is_disposing = False
        self._initialization_complete = False
        
        self.ps = (0, 0, 1800, 1000)
        self.menubar_height = 25
        self.toolbar_height = 55
        
        self.component_manager = None
        self.ui_initialized = False

        # Load theme configuration early
        from librepy.app.utils.theme_config import get_theme_config
        self.theme_config = get_theme_config(self.logger)
        self.logger.info("Theme configuration loaded")

        self._load_saved_geometry()

        from librepy.app.core import frame_manager
        self.frame_manager = frame_manager.FrameManager(
            self,
            ctx, 
            smgr, 
            ps=self.ps,
            menubar_height=self.menubar_height
        )
        self.logger.info("Frame manager initialized")

        # Instantiate sidebar manager (not hidden)
        self.create_sidebar_manager(hidden=False)
        
        try:
            from librepy.app.core.component_manager import ComponentManager
            self.component_manager = ComponentManager(
                self,
                self.ctx,
                self.smgr,
                self.frame_manager,
                self.ps
            )
            
            self.active_screen = 'training_session_list'
            self.component_manager.switch_component(self.active_screen)
        except Exception:
            self.logger.error("Error creating component manager:")
            self.logger.error(traceback.format_exc())
            self.active_screen = None

        self.sidebar_width = self.sidebar_manager.get_width() if hasattr(self, 'sidebar_manager') and self.sidebar_manager is not None else 0
        self.create_menubar_manager()
        try:
            actual_ps = self.frame_manager.window.getPosSize()
            self.ps = (self.ps[0], self.ps[1], actual_ps.Width, actual_ps.Height)
            if hasattr(self, 'sidebar_manager') and self.sidebar_manager is not None:
                self.sidebar_manager.resize(self.ps[2], self.ps[3])
        except Exception:
            self.logger.error("Error syncing actual window size:")
            self.logger.error(traceback.format_exc())

        self._initialization_complete = True
        self.logger.info("APP: Initialization complete")
        
        if self.component_manager is not None:
            self.logger.info("APP: Forcing component resize after initialization")
            self.component_manager.resize_active_component(self.ps[2], self.ps[3])
            self.logger.info(f"APP: Components resized to {self.ps[2]}x{self.ps[3]}")

    def _load_saved_geometry(self):
        """Load saved window geometry and apply it to self.ps if valid"""
        try:
            geometry_manager = WindowGeometryConfigManager()
            saved_geometry = geometry_manager.get_geometry()
            
            if saved_geometry and geometry_manager.is_geometry_valid_for_screen(saved_geometry):
                x, y, width, height = saved_geometry
                self.ps = (x, y, width, height)
                self.logger.info(f"Loaded saved window geometry: ({x}, {y}, {width}, {height})")
            else:
                self.logger.debug("No valid saved geometry found, using defaults")
                
        except Exception as e:
            self.logger.error(f"Error loading saved geometry: {e}")
            self.logger.error(traceback.format_exc())

    def show_screen(self, screen_name, **kwargs):
        """
        Central method to handle screen transitions
        Uses the component manager to switch between components
        
        Args:
            screen_name (str): Name of the screen to show ('log_in', 'home', 'job_list', 'calendar', etc.)
            **kwargs: Additional parameters to pass to the component (e.g., org_id, estimate_id)
        """
        if self.component_manager is None:
            self.logger.error("Cannot show screen: component manager not initialized")
            return
            
        if self.active_screen == screen_name and not kwargs:
            return
        self.sidebar_manager.show()
        
        # Pass additional parameters to component manager
        component = self.component_manager.switch_component(screen_name, **kwargs)
        self.active_screen = component
        self.ui_initialized = True

    def window_resizing(self, width, height):
        """Handle window resize events"""
        if self.component_manager is None:
            return
            
        self.ps = (self.ps[0], self.ps[1], width, height)
        self.logger.info(f"Window resized to {width}x{height}")
        
        if hasattr(self, 'sidebar_manager') and self.sidebar_manager is not None:
            self.sidebar_manager.resize(width, height)
            
        if hasattr(self, '_initialization_complete') and self._initialization_complete:
            self.component_manager.resize_active_component(width, height)
            self.logger.info(f"Components resized to {width}x{height}")

    def dispose(self):
        """Dispose of the application"""
        if hasattr(self, '_is_disposing') and self._is_disposing:
            return
            
        self._is_disposing = True
        self.logger.info("Disposing application...")
        
        try:
            if hasattr(self, 'component_manager') and self.component_manager is not None:
                self.component_manager.dispose()
                self.logger.info("Component manager disposed")
        except Exception:
            self.logger.error("Error disposing component manager:")
            self.logger.error(traceback.format_exc())
        
        try:
            if hasattr(self, 'menubar_manager') and self.menubar_manager is not None:
                self.menubar_manager.dispose()
                self.logger.info("Menubar manager disposed")
        except Exception:
            self.logger.error("Error disposing menubar manager:")
            self.logger.error(traceback.format_exc())
        
        try:
            if hasattr(self, 'frame_manager'):
                self.frame_manager.dispose()
                self.logger.info("Frame manager disposed")
        except Exception:
            self.logger.error("Error disposing frame manager:")
            self.logger.error(traceback.format_exc())
            
        self._is_disposing = False

    def create_sidebar_manager(self, hidden=False):
        try:
            from librepy.app.core import sidebar_manager
            self.sidebar_manager = sidebar_manager.SidebarManager(self, self.ctx, self.smgr, self.frame_manager, self.ps)
            if hidden and hasattr(self.sidebar_manager, 'hide'):
                self.sidebar_manager.hide()
            self.logger.info("Sidebar manager initialized")
        except Exception:
            self.logger.error("Error creating sidebar manager:")
            self.logger.error(traceback.format_exc())
            self.sidebar_manager = None

    def create_menubar_manager(self):
        try:
            self.logger.info("MAIN: Creating menubar manager")
            from librepy.app.core import menubar_manager as _mm
            self.menubar_manager = _mm.MenubarManager(self, self.ctx, self.smgr, self.frame_manager)
            self.logger.info("MAIN: Menubar manager created successfully")
        except Exception as e:
            self.logger.error(f"MAIN: Error creating menubar manager: {str(e)}")
            self.logger.error(traceback.format_exc())
            # Don't let menubar failure crash the entire application
            self.menubar_manager = None

def main(*args):
    """Main function for the application"""
    logger.info("MAIN: application starting")
    logger.info(f"MAIN: Arguments received: {args}")
    ctx = getDefaultContext()
    smgr = ctx.ServiceManager
    app = App(ctx, smgr)
    
    if not hasattr(app, '_initialization_complete') or not app._initialization_complete:
        logger.warning("MAIN: Application initialization was not completed, exiting...")
        return None
    
    logger.info("MAIN: application initialized successfully")
    return app
