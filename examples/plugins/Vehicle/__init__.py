class Vehicle:
	__metaclass__ = abc.ABCMeta
	
	@abc.abstractmethod
	def accelerate(self):
		pass
	
	@abc.abstractmethod
	def decelerate(self):
		pass