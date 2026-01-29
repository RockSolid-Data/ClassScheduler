#coding:utf-8
# Author:  Joshua Aguilar
# Purpose: Menubar manager for the contact list application
# Created: 01.07.2025

import traceback
from librepy.pybrex import menubar


class MenubarManager(object):
    def __init__(self, parent, ctx, smgr, frame):
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.logger = parent.logger
        self.logger.info("MenubarManager: Starting initialization")
        try:
            self.menubar = self.create_menubar()
            self.logger.info("MenubarManager: Initialization complete")
        except Exception as e:
            self.logger.error(f"MenubarManager: Error during initialization: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def create_menubar(self):
        """Menubar for the contact list application"""
        self.logger.info("MenubarManager: Creating menubar")
        
        try:
            #Menu bar items
            m = menubar.Menu
            sm = menubar.SubMenu
            menulist = [
                m(0, '~Settings', None, (
                    # Set app specific settings here
                    sm(None, 'Divider'),
                    sm(2, '~Appearance', 'p_appearance', graphic='background.png'),
                    sm(3, '~Log Settings', 'p_log_settings', graphic='log-settings.png'),
                    sm(4, '~Database Settings', 'p_settings', graphic='database-settings2.png'),
                    sm(5, '~Staff', 'p_staff', graphic='business-info.png'),
                )),
                m(1, '~About', None, (
                    sm(0, '~About', 'h_about', graphic='help-about.png'),
                )),
            ]
            
            self.logger.info("MenubarManager: Menu structure created")
            
            #Menu bar functions
            fn = {}
            # Set app specific functions here
            fn['p_appearance'] = self.appearance_settings
            fn['p_log_settings'] = self.log_settings
            fn['p_settings'] = self.settings
            fn['p_staff'] = self.staff
            fn['h_about'] = self.show_about
            
            self.logger.info("MenubarManager: Function mappings created")
            
            menubar_instance = menubar.Menubar(self.parent, self.ctx, self.smgr, self.frame, menulist, fn)
            self.logger.info("MenubarManager: Menubar instance created successfully")
            return menubar_instance
            
        except Exception as e:
            self.logger.error(f"MenubarManager: Error creating menubar: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
    
    def dispose(self):
        """Dispose of the menubar manager"""
        try:
            self.menubar.dispose()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            self.logger.error(traceback.format_exc())

    # Menubar actions...
    
    def appearance_settings(self, *args):
        """Show appearance settings dialog"""
        from librepy.app.components.settings.app_settings_dlg import AppSettingsDialog
        dlg = AppSettingsDialog(self.ctx, self.parent, self.logger)
        dlg.execute()
        
    def log_settings(self, *args):
        """Show log settings dialog"""
        from librepy.app.components.settings.log_settings_dlg import LogSettingsDialog
        dlg = LogSettingsDialog(self.ctx, self.parent, self.logger)
        dlg.execute()

    def settings(self, *args):
        """Show settings dialog"""
        from librepy.peewee.connection import db_dialog
        
        from librepy.boot.bootstrap import ensure_database_ready
        
        dialog = db_dialog.DBDialog(self.ctx, self.parent, self.logger)
        if dialog.execute():
            # Re-run bootstrap to ensure connection is refreshed and migrations are applied
            ensure_database_ready(self.logger)

    def staff(self, *args):
        """Show staff dialog"""
        from librepy.app.components.settings.staff_dlg import StaffDialog
        dlg = StaffDialog(self.ctx, self.parent, self.logger)
        dlg.execute()

    def show_about(self, *args):
        """Show about dialog"""
        from librepy.app.components.settings.about_dlg import AboutDialog
        dlg = AboutDialog(self.ctx, self.smgr, self.parent)
        dlg.execute()