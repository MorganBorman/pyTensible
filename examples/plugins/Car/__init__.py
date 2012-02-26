class Car(Environment, Vehicle, Plugin): #@UndefinedVariable
	def __init__(self):
		Environment.__init__(self) #@UndefinedVariable
		Vehicle.__init__(self) #@UndefinedVariable
		Plugin.__init__(self) #@UndefinedVariable
		
	def load(self):
		pass
		
	def unload(self):
		pass
	
	def accelerate(self):
		return "Vehicle object is accelerating"
	
	def decelerate(self):
		return "Vehicle object is decelerating"
	
	def get_temperature(self):
		return 42
	
	def enter(self):
		print "you have entered"
		
	def leave(self):
		print "you have exited"