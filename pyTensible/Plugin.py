import abc

class Plugin(object):
	__metaclass__ = abc.ABCMeta
	
	@abc.abstractmethod
	def load(self, pluginLoader):
		"""Initialize the plugin."""
		return
	   
	@abc.abstractmethod
	def unload(self, pluginLoader):
		"""Deinitialize the plugin."""
		return
	
class MalformedPlugin(Exception):
	'''Invalid plugin form'''
	def __init__(self, value=''):
		Exception.__init__(self, value)