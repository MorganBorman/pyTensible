import sys, os

def addToPath(path):
	absPath = os.path.abspath(path)
	sys.path.append(absPath)
	
addToPath("../")

import pyTensible

pyTensible.setup_logging("example.log")
pluginLoader = pyTensible.PluginLoader()

pluginLoader.loadPlugins(os.path.abspath("./plugins"))

Events = pluginLoader.getResource("Events")

def rawr_function(name, string_argument):
	print "rawr_function", string_argument

Events.register_handler("rawr", rawr_function)

Events.trigger_event("rawr", "A scary event in plugin history")