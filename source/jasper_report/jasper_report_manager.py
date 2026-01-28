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
import os
from librepy.utils.log_config_manager import LoggingConfigManager
from librepy.utils.db_config_manager import DatabaseConfigManager
from datetime import datetime, date
from librepy.pybrex.values import pybrex_logger
from librepy.pybrex.values import JASPER_REPORTS_DIR
import uno
import shutil
import pkgutil
import zipfile
from librepy.pybrex.values import USER_DIR

logger = pybrex_logger(__name__)

_TEMPLATE_MAP = {}


def _ensure_template_path(src_path):
    """Return a file system path to the template that the Java manager can read."""
    try:
        dest_dir = os.path.join(USER_DIR, 'jasper_templates')
        os.makedirs(dest_dir, exist_ok=True)
        fname = os.path.basename(src_path)
        dest_path = os.path.join(dest_dir, fname)
        if os.path.exists(dest_path):
            _TEMPLATE_MAP[fname] = dest_path
            return dest_path

        # First try normal filesystem copy if source exists
        if os.path.exists(src_path):
            shutil.copy(src_path, dest_path)
            _TEMPLATE_MAP[fname] = dest_path
            return dest_path

        # Fallback: load template bytes from the package resources (works when
        # running from an embedded document where the source path is a UNO URL).
        try:
            data = pkgutil.get_data('librepy.jasper_report.templates', fname)
            if data:
                with open(dest_path, 'wb') as fh:
                    fh.write(data)
                _TEMPLATE_MAP[fname] = dest_path
                return dest_path
            else:
                logger.error(f"Unable to load template bytes for {fname}")
        except Exception as pkg_err:
            logger.error(f"pkgutil failed for {fname}: {pkg_err}")
        _TEMPLATE_MAP[os.path.basename(src_path)] = dest_path
        return dest_path
    except Exception:
        logger.error('Failed to copy template; using source path')
        return src_path

def precopy_all_templates():
    """Copy every embedded .jrxml template to external folder once at startup."""
    try:
        copied = 0
        # Try filesystem directory first (works when not embedded)
        if os.path.isdir(JASPER_REPORTS_DIR):
            for fname in os.listdir(JASPER_REPORTS_DIR):
                if fname.lower().endswith('.jrxml'):
                    _ensure_template_path(os.path.join(JASPER_REPORTS_DIR, fname))
                    copied += 1
        # If nothing copied yet, fall back to zip extraction from the embedded document
        logger.info(f"Pre-copy complete. Total templates copied: {copied}")
        if copied == 0:
            try:
                doc_url = thisComponent.URL if 'thisComponent' in globals() else None
                if doc_url:
                    doc_path = uno.fileUrlToSystemPath(doc_url)
                    if os.path.exists(doc_path):
                        with zipfile.ZipFile(doc_path) as zpf:
                            for zinfo in zpf.infolist():
                                if zinfo.filename.lower().endswith('.jrxml') and 'Scripts/python/jasper_report/templates' in zinfo.filename:
                                    fname = os.path.basename(zinfo.filename)
                                    dest_dir = os.path.join(USER_DIR, 'jasper_templates')
                                    os.makedirs(dest_dir, exist_ok=True)
                                    dest_path = os.path.join(dest_dir, fname)
                                    with open(dest_path, 'wb') as fh:
                                        fh.write(zpf.read(zinfo))
                                    _TEMPLATE_MAP[fname] = dest_path
                                    copied += 1
                        logger.info(f"Zip extraction copied: {copied}")
            except Exception as zip_err:
                logger.error(f"Zip extraction failed: {zip_err}")
    except Exception as e:
        logger.error(f'Failed precopy templates: {e}')

def set_report_parameter(report, param_name, param_value, param_type):
    """
    Set a parameter on the report based on its type.
    
    Args:
        report: JasperReport instance
        param_name (str): Name of the parameter
        param_value: Value of the parameter
        param_type (str): Type of parameter. One of:
            - 'string': String value
            - 'int': Integer value
            - 'long': Long value
            - 'double': Double value
            - 'float': Float value
            - 'boolean': Boolean value
            - 'date': Date value (datetime.date or datetime.datetime)
            - 'uno_date': com.sun.star.util.Date value
            - 'image_bytes': Image as bytes array
            - 'image_path': Image as file path
    """
    try:
        logger.info(f"Setting parameter {param_name} with value {param_value} of type {param_type}")
        
        if param_value is None:
            logger.info(f"Parameter {param_name} has None value, skipping")
            return
            
        if param_type == 'string':
            report.setStringParam(param_name, str(param_value))
        elif param_type == 'int' or param_type == 'integer':
            report.setIntParam(param_name, int(param_value))
        elif param_type == 'long':
            report.setLongParam(param_name, int(param_value))  # Python int maps to Java long
        elif param_type == 'double':
            report.setDoubleParam(param_name, float(param_value))
        elif param_type == 'float':
            report.setFloatParam(param_name, float(param_value))
        elif param_type == 'boolean':
            report.setBooleanParam(param_name, bool(param_value))
        elif param_type == 'date':
            logger.info(f"Processing date parameter {param_name}")
            logger.info(f"Value type: {type(param_value)}")
            logger.info(f"Value: {param_value}")
            
            # Handle both datetime and date objects
            if isinstance(param_value, (datetime, date)):
                logger.info(f"Creating UNO date for {param_value}")
                # Create a new UNO date object
                uno_date = uno.createUnoStruct("com.sun.star.util.Date")
                logger.info(f"Created UNO date object: {uno_date}")
                uno_date.Year = param_value.year
                uno_date.Month = param_value.month
                uno_date.Day = param_value.day
                logger.info(f"Setting date parameter with UNO date: Year={uno_date.Year}, Month={uno_date.Month}, Day={uno_date.Day}")
                report.setDateParam(param_name, uno_date)
            else:
                raise ValueError(f"Expected datetime.date or datetime.datetime, got {type(param_value)}")
        elif param_type == 'uno_date':
            # Directly use the UNO date object
            report.setDateParam(param_name, param_value)
        elif param_type == 'image_bytes':
            report.setImageFromBytesParam(param_name, param_value)
        elif param_type == 'image_path':
            report.setImageFromPathParam(param_name, str(param_value))
        else:
            raise ValueError(f"Unsupported parameter type: {param_type}")
            
    except Exception as e:
        logger.error(f"Error in set_report_parameter: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Error setting parameter {param_name}: {str(e)}")

def main(report_path, report_params=None, *args):
    try:
        logger.info(f"Starting report generation with params: {report_params}")
        
        manager = createUnoService("org.libretools.JasperReportManager")
        
        log_config_manager = LoggingConfigManager()
        log_dir = os.path.dirname(log_config_manager.get_log_path())
        jasper_log_file = os.path.join(log_dir, "jasper_reports.log")
        manager.setLogFile(jasper_log_file)
        
        # Get database configuration from DatabaseConfigManager
        db_config_manager = DatabaseConfigManager()
        db_config = db_config_manager.get_connection_params()
        
        if not db_config:
            raise Exception("Database configuration not found or invalid")
        
        # Build JDBC URL with credentials embedded
        url = f"jdbc:postgresql://{db_config['host']}:{db_config['port']}/{db_config['database']}?user={db_config['user']}&password={db_config['password']}"
        
        # Add connection using the URL directly
        manager.addConnection(url)
        
        report_path = _ensure_template_path(report_path)
        report = manager.addReport(report_path)
         
        # Set report parameters if provided
        if report_params:
            logger.info("Processing report parameters")
            for param_name, param_info in report_params.items():
                try:
                    logger.info(f"Processing parameter: {param_name}")
                    logger.info(f"Parameter info: {param_info}")
                    param_value = param_info.get('value')
                    param_type = param_info.get('type', 'string')  # Default to string if type not specified
                    logger.info(f"Extracted value: {param_value}, type: {param_type}")
                    set_report_parameter(report, param_name, param_value, param_type)
                except Exception as e:
                    logger.error(f"Error processing parameter {param_name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise Exception(f"Failed to set parameter {param_name}: {str(e)}")
                
        report.setPromptForParameters(False)
        
        report.execute()
        
    except Exception as e:
        logger.error(f"Error encountered: {str(e)}")
        logger.error(traceback.format_exc())
        MsgBox("Error encountered!\n%s" % e)