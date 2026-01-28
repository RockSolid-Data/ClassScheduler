import traceback
from librepy.pybrex.sidebar import Sidebar
from librepy.utils.window_geometry_config_manager import WindowGeometryConfigManager

class SidebarManager(Sidebar):
    """Manages the sidebar and main containers for the application"""
    
    def __init__(self, parent, ctx, smgr, frame_manager, ps):
        """Initialize the sidebar manager
        
        Args:
            parent: The main application instance
            ctx: UNO context
            smgr: Service manager
            frame_manager: Frame manager instance
            ps: Position and size tuple (x, y, width, height)
        """
        self.frame_manager = frame_manager
        self.ps = ps
        self.logger = parent.logger

        # Determine default sidebar state based on saved preference
        try:
            _geom_mgr = WindowGeometryConfigManager()
            _expanded_pref = _geom_mgr.get_sidebar_expanded()
        except Exception:
            _expanded_pref = False

        default_state_pref = 'expanded' if _expanded_pref else 'closed'

        # Define sidebar items
        sidebar_items = [
            ('Button', 'Classes List', 'list.png', lambda: parent.show_screen('training_session_list'), 'Home'),
            ('Separator',),
            ('Button', 'Classes', 'classes.png', lambda: parent.show_screen('calendar'), 'Calendar of events'),
            ('Separator',),
            ('Button', 'Appointments', 'appointments.png', lambda: parent.show_screen('appointment_calendar'), 'Appointment calendar'),
            ('Separator',),
            ('Button', 'Employees', 'employees2.png', lambda: parent.show_screen('employee_calendar'), 'Employee calendar')
            # Add the rest of the sidebar items here
        ]
        
        # Initialize the parent Sidebar class
        super().__init__(
            parent=parent,
            ctx=ctx,
            smgr=smgr,
            frame=frame_manager,
            sidebar_items=sidebar_items,
            width=64,
            expanded_width=160,
            default_state=default_state_pref,
            title=' CC',
            expanded_title='Control Center',
            position='left'
        )
        
        self.logger.info("SidebarManager initialized")
    
    def resize(self, width, height):
        """Handle resize events
        
        Args:
            width: New width
            height: New height
        """
        try:
            # Update stored dimensions
            self.ps = (self.ps[0], self.ps[1], width, height)
            
            # Resize sidebar using inherited method
            super().resize(width, height)
                        
        except Exception as e:
            self.logger.error(f"Error during resize: {str(e)}")
            self.logger.error(traceback.format_exc())
    
    def toggle_sidebar(self):
        """Toggle sidebar open/closed"""
        try:
            old_width = self.get_width()
            self.toggle()
            new_width = self.get_width()
            
            if old_width != new_width:
                # Update parent's sidebar_width tracking
                if hasattr(self.parent, 'sidebar_width'):
                    self.parent.sidebar_width = new_width
                # Trigger resize to adjust main containers
                self.resize(self.ps[2], self.ps[3])
                # Persist sidebar expanded state
                try:
                    _geom_mgr = WindowGeometryConfigManager()
                    _geom_mgr.save_sidebar_expanded(self.is_expanded)
                except Exception:
                    pass
                
                if hasattr(self.parent, 'component_manager'):
                    self.parent.component_manager.resize_active_component(self.ps[2], self.ps[3])
                
        except Exception as e:
            self.logger.error(f"Error toggling sidebar: {str(e)}")
            self.logger.error(traceback.format_exc())
    
    def dispose(self):
        """Clean up resources"""
        try:
            # Dispose using inherited method
            super().dispose() 
            self.logger.info("SidebarManager disposed")
            
        except Exception as e:
            self.logger.error(f"Error during SidebarManager disposal: {str(e)}")
            self.logger.error(traceback.format_exc())


    # Visibility helpers
    def hide(self):
        """Hide the entire sidebar container"""
        try:
            if hasattr(self, 'sidebar_container'):
                self.sidebar_container.setVisible(False)
        except Exception:
            pass

    def show(self):
        """Show the sidebar container"""
        try:
            if hasattr(self, 'sidebar_container'):
                self.sidebar_container.setVisible(True)
        except Exception:
            pass