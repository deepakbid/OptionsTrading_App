"""
File-based strategy loader that loads strategies from the cursorstrategies folder.
"""
import os
import sys
import importlib.util
from typing import Dict, List, Optional, Type
from strategies.base import Strategy
import asyncio

# Use ib_async consistently across the app
from ib_async import (
    IB, Contract, Order, LimitOrder, MarketOrder, ComboLeg, Option
)

class FileStrategyLoader:
    """Loads strategies from Python files in the cursorstrategies folder."""
    
    def __init__(self, strategies_dir: str = "cursorstrategies"):
        self.strategies_dir = strategies_dir
        self.strategies_cache = {}
        self._ensure_strategies_dir()
    
    def _ensure_strategies_dir(self):
        """Ensure the strategies directory exists."""
        if not os.path.exists(self.strategies_dir):
            os.makedirs(self.strategies_dir)
            print(f"Created strategies directory: {self.strategies_dir}")
    
    def get_strategy_files(self) -> List[str]:
        """Get list of all strategy files."""
        if not os.path.exists(self.strategies_dir):
            return []
        
        strategy_files = []
        for file in os.listdir(self.strategies_dir):
            if file.endswith('.py') and not file.startswith('__'):
                strategy_files.append(file)
        
        return sorted(strategy_files)
    
    def load_strategy_from_file(self, filename: str) -> Optional[Type[Strategy]]:
        """Load a strategy class from a Python file."""
        filepath = os.path.join(self.strategies_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"Strategy file not found: {filepath}")
            return None
        
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
            if spec is None or spec.loader is None:
                print(f"Failed to create spec for {filename}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find Strategy subclass
            strategy_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, Strategy) and 
                    attr is not Strategy):
                    strategy_class = attr
                    break
            
            if strategy_class is None:
                print(f"No Strategy subclass found in {filename}")
                return None
            
            return strategy_class
            
        except Exception as e:
            print(f"Error loading strategy from {filename}: {e}")
            return None
    
    def get_all_strategies(self) -> Dict[str, Type[Strategy]]:
        """Get all available strategies from files."""
        strategies = {}
        
        for filename in self.get_strategy_files():
            strategy_class = self.load_strategy_from_file(filename)
            if strategy_class:
                strategies[filename] = strategy_class
        
        return strategies
    
    def create_strategy_file(self, name: str, description: str, code: str) -> str:
        """Create a new strategy file in the cursorstrategies folder."""
        # Clean the name for filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_').lower()
        
        # Ensure unique filename
        filename = f"{safe_name}.py"
        counter = 1
        while os.path.exists(os.path.join(self.strategies_dir, filename)):
            filename = f"{safe_name}_{counter}.py"
            counter += 1
        
        filepath = os.path.join(self.strategies_dir, filename)
        
        try:
            # Validate the code by trying to load it
            self._validate_strategy_code(code)
            
            # Write the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f'"""\n{description}\n"""\n\n')
                f.write(code)
            
            print(f"Strategy file created: {filepath}")
            return filename
            
        except Exception as e:
            # Clean up if file was created
            if os.path.exists(filepath):
                os.remove(filepath)
            raise ValueError(f"Failed to create strategy file: {e}")
    
    def _validate_strategy_code(self, code: str):
        """Validate strategy code by attempting to execute it."""
        # Namespace exposed to the user strategy code
        ns = {
            "Strategy": Strategy,
            "asyncio": asyncio,
            # expose ib_async classes to strategies
            "IB": IB,
            "Contract": Contract,
            "Order": Order,
            "LimitOrder": LimitOrder,
            "MarketOrder": MarketOrder,
            "ComboLeg": ComboLeg,
            "Option": Option,
        }
        
        try:
            exec(code, ns)
        except Exception as e:
            raise ValueError(f"Invalid strategy code: {e}")
        
        # Find Strategy subclass
        strategy_class = None
        for obj_name, obj in ns.items():
            if isinstance(obj, type) and issubclass(obj, Strategy) and obj is not Strategy:
                strategy_class = obj
                break
        
        if strategy_class is None:
            raise ValueError("No Strategy subclass found in code")
    
    def delete_strategy_file(self, filename: str) -> bool:
        """Delete a strategy file."""
        filepath = os.path.join(self.strategies_dir, filename)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            os.remove(filepath)
            print(f"Strategy file deleted: {filepath}")
            return True
        except Exception as e:
            print(f"Error deleting strategy file {filename}: {e}")
            return False
    
    def update_strategy_file(self, filename: str, description: str, code: str) -> bool:
        """Update an existing strategy file."""
        filepath = os.path.join(self.strategies_dir, filename)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            # Validate the code
            self._validate_strategy_code(code)
            
            # Update the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f'"""\n{description}\n"""\n\n')
                f.write(code)
            
            print(f"Strategy file updated: {filepath}")
            return True
            
        except Exception as e:
            print(f"Error updating strategy file {filename}: {e}")
            return False
    
    def get_strategy_info(self, filename: str) -> Optional[Dict]:
        """Get information about a strategy file."""
        filepath = os.path.join(self.strategies_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            strategy_class = self.load_strategy_from_file(filename)
            if not strategy_class:
                return None
            
            # Read the file content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract description from docstring
            description = ""
            if content.startswith('"""'):
                end = content.find('"""', 3)
                if end != -1:
                    description = content[3:end].strip()
            
            return {
                "filename": filename,
                "name": getattr(strategy_class, 'name', filename[:-3]),
                "description": description,
                "code": content,
                "class_name": strategy_class.__name__
            }
            
        except Exception as e:
            print(f"Error getting strategy info for {filename}: {e}")
            return None

# Global instance
file_strategy_loader = FileStrategyLoader()
