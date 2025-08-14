"""
Safely load and instantiate Strategy classes from user code.
"""
import sys
import os
from typing import Dict, Any
from strategies.base import Strategy
import asyncio

# Use ib_async consistently across the app
from ib_async import (
    IB, Contract, Order, LimitOrder, MarketOrder, ComboLeg, Option
)

def load_strategy_from_code(code: str) -> Strategy:
    """
    Load a Strategy subclass from user code.
    
    Args:
        code: Python code containing a Strategy subclass
        
    Returns:
        Instance of the Strategy subclass
        
    Raises:
        ValueError: If no Strategy subclass is found
    """
    print(f"DEBUG: Loading strategy from code (length: {len(code)})")
    print(f"DEBUG: Code preview: {code[:200]}...")
    
    # Ensure the strategies directory is in the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    print(f"DEBUG: Current directory: {current_dir}")
    print(f"DEBUG: Parent directory: {parent_dir}")
    print(f"DEBUG: Python path: {sys.path[:3]}...")
    
    # Namespace exposed to the user strategy code
    ns: Dict[str, Any] = {
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
    
    print(f"DEBUG: Strategy base class: {Strategy}")
    print(f"DEBUG: Strategy base class type: {type(Strategy)}")
    print(f"DEBUG: Strategy base class module: {Strategy.__module__}")

    try:
        exec(code, ns)
        print(f"DEBUG: Code executed successfully")
        print(f"DEBUG: Namespace keys: {list(ns.keys())}")
        print(f"DEBUG: Namespace values types: {[(k, type(v)) for k, v in ns.items() if k.startswith('NewStrategy') or k.startswith('strategy')]}")
    except Exception as e:
        print(f"DEBUG: Code execution failed: {e}")
        raise ValueError(f"Failed to execute strategy code: {e}")

    # Find first Strategy subclass
    strategy_class = None
    for obj_name, obj in ns.items():
        if isinstance(obj, type) and issubclass(obj, Strategy) and obj is not Strategy:
            print(f"DEBUG: Found Strategy subclass: {obj_name} = {obj}")
            strategy_class = obj
            break
    
    if strategy_class is None:
        print(f"DEBUG: No Strategy subclass found in namespace")
        print(f"DEBUG: All namespace objects: {[(k, type(v)) for k, v in ns.items()]}")
        raise ValueError("No Strategy subclass found in code")

    try:
        instance = strategy_class()
        print(f"DEBUG: Successfully instantiated strategy: {instance}")
        return instance
    except Exception as e:
        print(f"DEBUG: Failed to instantiate strategy: {e}")
        raise ValueError(f"Failed to instantiate strategy: {e}")
