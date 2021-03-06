import sys, os

def addToPath(path):
	absPath = os.path.abspath(path)
	sys.path.append(absPath)
	
addToPath("../")

import pyTensible

pyTensible.setup_logging("example.log")
plugin_loader = pyTensible.PluginLoader()

plugin_loader.load_plugins(os.path.abspath("./plugins"))

import com

def handler_function(event):
	print "Event triggered:", event.name, event.args, event.kwargs

com.example.Events.event_manager.register_handler("first", handler_function)
com.example.Events.event_manager.register_handler("second", handler_function)

first_event = com.example.Events.Event('first', ("The first event",))
second_event = com.example.Events.Event('second', ("the second event",))

timer = com.example.Timers.Timer(5, second_event)

com.example.Timers.timer_manager.add_timer(timer)

print plugin_loader.get_providers("com.example.Events.IEvent")
print plugin_loader.get_instances("com.example.Events.IEventManager")

com.example.Events.event_manager.trigger_event(first_event)

plugin_loader.unload_all()