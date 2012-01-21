from PluginLoader import PluginLoader
from Logging import setup_logging
from Plugin import Plugin

def addToPath(path):
	import sys, os
	absPath = os.path.abspath(path)
	sys.path.append(absPath)
