class Environment:
	__metaclass__ = abc.ABCMeta
	
	@abc.abstractmethod
	def get_temperature(self):
		pass
	
	@abc.abstractmethod
	def enter(self):
		pass
	
	@abc.abstractmethod
	def leave(self):
		pass