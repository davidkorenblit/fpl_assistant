"""
System Import Validation for FPL Assistant
Validates that all required modules can be imported successfully
"""

import os
import sys
import logging
from typing import Dict, List, Tuple


class ImportValidator:
    """Validates system imports and dependencies"""

    def __init__(self):
        """Initialize the import validator"""
        self.logger = logging.getLogger(__name__)

        self.required_files = [
            'data_fetcher.py',
            'DataManager.py',
            'MomentumAnalyzer.py',
            'FixtureAnalyzer.py',
            'MomentumVisualizer.py',
            'MomentumIntegration.py'
        ]

        self.core_modules = [
            ('data_fetcher', 'EnhancedFPLDataFetcher'),
            ('DataManager', 'EnhancedFPLDataManager'),
            ('MomentumAnalyzer', 'MomentumAnalyzer'),
            ('FixtureAnalyzer', 'FixtureAnalyzer'),
            ('MomentumVisualizer', 'MomentumVisualizer'),
            ('MomentumIntegration', 'MomentumIntegration')
        ]

        self.required_packages = ['pandas', 'numpy', 'requests', 'datetime']
        self.optional_packages = ['matplotlib', 'seaborn']

    def check_file_exists(self, filename: str) -> bool:
        """Check if a file exists"""
        exists = os.path.exists(filename)
        if exists:
            self.logger.info(f"File found: {filename}")
        else:
            self.logger.error(f"Missing file: {filename}")
        return exists

    def check_module_import(self, module_name: str, class_name: str = None) -> bool:
        """Check if a module can be imported"""
        try:
            if class_name:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                self.logger.info(f"Successfully imported {module_name}.{class_name}")
            else:
                __import__(module_name)
                self.logger.info(f"Successfully imported {module_name}")
            return True
        except ImportError as e:
            self.logger.error(f"Failed to import {module_name}.{class_name if class_name else ''}: {e}")
            return False
        except AttributeError:
            self.logger.error(f"Class {class_name} not found in {module_name}")
            return False

    def validate_system(self) -> Dict[str, bool]:
        """Validate entire system"""
        results = {
            'files_ok': True,
            'core_modules_ok': True,
            'required_packages_ok': True,
            'system_ready': False
        }

        # Check files
        self.logger.info("Checking required files...")
        for filename in self.required_files:
            if not self.check_file_exists(filename):
                results['files_ok'] = False

        # Check required packages
        self.logger.info("Checking required packages...")
        for package in self.required_packages:
            if not self.check_module_import(package):
                results['required_packages_ok'] = False

        # Check optional packages
        self.logger.info("Checking optional packages...")
        for package in self.optional_packages:
            self.check_module_import(package)  # Don't affect system status

        # Check core modules
        self.logger.info("Checking core FPL modules...")
        for module_name, class_name in self.core_modules:
            if not self.check_module_import(module_name, class_name):
                results['core_modules_ok'] = False

        # Determine system readiness
        results['system_ready'] = all([
            results['files_ok'],
            results['core_modules_ok'],
            results['required_packages_ok']
        ])

        return results

    def get_setup_instructions(self) -> List[str]:
        """Get setup instructions for missing dependencies"""
        instructions = []

        # Check for missing packages
        missing_packages = []
        for package in self.required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            instructions.append(f"Install missing packages: pip install {' '.join(missing_packages)}")

        # Check for missing optional packages
        missing_optional = []
        for package in self.optional_packages:
            try:
                __import__(package)
            except ImportError:
                missing_optional.append(package)

        if missing_optional:
            instructions.append(f"Install optional packages: pip install {' '.join(missing_optional)}")

        return instructions


def validate_fpl_system() -> bool:
    """Main validation function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    validator = ImportValidator()
    results = validator.validate_system()

    if results['system_ready']:
        logging.info("FPL Assistant system is ready!")
        return True
    else:
        logging.error("System validation failed")
        instructions = validator.get_setup_instructions()
        for instruction in instructions:
            logging.info(f"Setup: {instruction}")
        return False


if __name__ == "__main__":
    success = validate_fpl_system()
    sys.exit(0 if success else 1)