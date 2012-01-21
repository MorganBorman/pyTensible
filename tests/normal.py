import sys, os

def addToPath(path):
	absPath = os.path.abspath(path)
	sys.path.append(absPath)
	
addToPath("../")

import pyTensible

pyTensible.setup_logging("normal.log")
pluginLoader = pyTensible.PluginLoader()

pluginLoader.loadPlugins(os.path.abspath("./plugins"))