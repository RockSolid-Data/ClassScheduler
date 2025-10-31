import traceback
from librepy.pybrex import ctr_container
from com.sun.star.awt.PosSize import POSSIZE

class TrainingSessionList(ctr_container.Container):
    component_name = 'training_session_list'

    def __init__(self, parent, ctx, smgr, frame, ps):
        self.logger = parent.logger
        self.parent = parent  
        self.ctx = ctx            
        self.smgr = smgr         
        self.frame = frame        
        self.ps = ps 

        # Add toolbar offset
        self.toolbar_offset = 0
        
        # Settings configuration
        self.container_config = {
            'button_width': int(ps[2] * 0.20),  # 20% of window width
            'button_height': int(ps[3] * 0.15),  # 15% of window height
            'padding_x': int(ps[2] * 0.02),      # 2% horizontal padding
            'padding_y': int(ps[3] * 0.05),      # 5% vertical padding
            'top_offset': self.toolbar_offset,
            'colors': {
                'border': 0x000000,      # Black border
                'button_normal': 0xFFFFFF,   # White
                'button_hover': 0xF0F0F0,    # Light white
                'button_pressed': 0xE0E0E0,  # Slightly darker white
            }
        }
        
        # Initialize the parent Container class properly
        super().__init__(
            ctx, 
            smgr, 
            frame.window,
            ps,
            background_color=0xF2F2F2
        )
        # Store initial container size from available area
        self.window_width = ps[2]
        self.window_height = ps[3]

        self._create()
        self.logger.info(f"Home View initialized")
        self.show()

    def _create(self):
        # Calculate initial positions
        pos = self._calculate_positions()
        
        # Home title
        self.lbl_home_title = self.add_label(
            "lbl_home_title", 
            pos['title_x'], 
            pos['title_y'], 
            pos['title_width'], 
            pos['title_height'], 
            Label="Home", 
            FontHeight=24, 
            FontWeight=150, 
            FontName='Sans-serif'
        )

    def load_data(self):
        pass
    
    def show(self):
        super().show()
        self.load_data()
        self.resize(self.window_width, self.window_height)

    def hide(self):
        super().hide()

    def resize(self, width, height):
        """Handle window resize events"""
        try:
            # Update stored dimensions
            self.window_width = width
            self.window_height = height - self.toolbar_offset
            
            # Update container configuration
            self.container_config.update({
                'button_width': int(width * 0.20),
                'button_height': int((height - self.toolbar_offset) * 0.15),
                'padding_x': int(width * 0.02),
                'padding_y': int((height - self.toolbar_offset) * 0.05),
            })
            
            # Get current sidebar width to maintain proper positioning
            sidebar_width = getattr(self.parent, 'sidebar_width', 0)
            
            # Resize the main container (preserve sidebar offset for X position)
            self.container.setPosSize(
                sidebar_width,  # Start after sidebar, not at 0
                self.toolbar_offset,
                width, 
                height - self.toolbar_offset,
                POSSIZE
            )
            
            # Calculate positions for all components
            pos = self._calculate_positions()
            
            # Update home title label
            if hasattr(self, 'lbl_home_title'):
                self.lbl_home_title.setPosSize(
                    pos['title_x'],
                    pos['title_y'], 
                    pos['title_width'], 
                    pos['title_height'], 
                    POSSIZE
                )
            
            # Force redraw
            if hasattr(self, 'container') and self.container.getPeer():
                peer = self.container.getPeer()
                peer.invalidate(0)
                
        except Exception as e:
            self.logger.error(f"Error during resize: {e}")
            self.logger.error(traceback.format_exc())
    def _calculate_positions(self):
        """Calculate positions for UI components based on current window size"""
        # Use padding from configuration
        padding_x = self.container_config['padding_x']
        padding_y = self.container_config['padding_y']
        
        # Home title positioning - centered horizontally, near the top
        title_width = min(400, self.window_width - (padding_x * 2))  # Responsive width with max
        title_height = 60  # Sufficient height for large title
        title_x = (self.window_width - title_width) // 2  # Center horizontally
        title_y = padding_y + 20  # Some space from top
        
        return {
            'title_x': title_x,
            'title_y': title_y,
            'title_width': title_width,
            'title_height': title_height
        }

    def dispose(self):
        """Dispose of all controls and grids"""
        try:
            self.logger.info("Disposing of Home page")
            
            # Dispose of main container
            if hasattr(self, 'container') and self.container is not None:
                try:
                    # Make sure the container window is hidden
                    try:
                        self.container.getPeer().setVisible(False)
                    except:
                        pass
                    
                    # Then dispose the container
                    self.container.dispose()
                except Exception as container_error:
                    self.logger.error(f"Error disposing container: {str(container_error)}")
                finally:
                    self.container = None
            
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc())
        