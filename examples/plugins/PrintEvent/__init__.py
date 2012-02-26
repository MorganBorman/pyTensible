class PrintEvent(Plugin):
	def __init__(self):
		Plugin.__init__(self)
		
	def load(self):
		Events = pluginLoader.get_resource("Events")
		
		Events.register_handler("rawr", self.print_event)
		
	def unload(self, pluginLoader):
		pass
	
	def print_event(self, *args):
		print "print event speaking:", args