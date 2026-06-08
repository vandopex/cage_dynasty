"""WSGI entry point for PythonAnywhere deployment.
PA's web app config should point to this file.
"""
import sys

project_home = '/home/vandopegaming/cage_dynasty/cage_dynasty_web'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application
