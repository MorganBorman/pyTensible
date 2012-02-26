class Events(Plugin):
	event_manager = None
	
	def __init__(self):
		Plugin.__init__(self)
		
	def load(self):
		self.event_manager = Event_Manager()
		
	def unload(self):
		pass
	
	def trigger_event(self, name, *args, **kwargs):
		"Trigger an event of the given name with the given arguments. Safe even if their is no handler yet registered for that named event."
		pluginLoader.logger.info("Events: Triggering event: %s with args: %s", str(name), str(args) + str(kwargs))
		self.event_manager.trigger_event(name, *args, **kwargs)
		
	def register_handler(self, name, handler):
		pluginLoader.logger.info("Events: Registering handler: %s for: %s", str(handler), str(name))
		self.event_manager.register_handler(name, handler)
	
class Event_Manager:
	"An event manager allowing multiple handlers of any callable type to be supplied for each named event."
	
	#dictionary of event handlers indexed by the event name handled
	handlers = {}
	
	def __init__(self):
		pass
	
	def trigger_event(self, name, *args, **kwargs):
		if name in self.handlers.keys():
			for handler in self.handlers[name]:
				handler(name, *args, **kwargs)
				
	def register_handler(self, name, handler):
		if not name in self.handlers.keys():
			self.handlers[name] = []
			
		self.handlers[name].append(handler)