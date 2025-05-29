"""
Refactored Lambda function entry point.

This is the main entry point for AWS Lambda. It delegates all processing
to the new modular architecture in the src/ directory.
"""

import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.handlers.lambda_handler import lambda_handler

# Re-export the lambda_handler for AWS Lambda
__all__ = ['lambda_handler']