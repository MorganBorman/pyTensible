import pyTensible

class Plugin(pyTensible.Plugin):
	def __init__(self):
		pyTensible.Plugin.__init__(self)
		
	def load(self, pluginLoader):
		Events = pluginLoader.get_resource("Events")
		
		Events.register_handler("rawr", self.print_event)
		
	def unload(self, pluginLoader):
		pass
	
	def print_event(self, *args):
		print "print event speaking:", args