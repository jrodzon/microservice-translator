"""
Entry point for running the Project Translator application as a module.

This allows the application to be run with: python -m project_translator
"""

from .main import cli

if __name__ == "__main__":
    cli()
