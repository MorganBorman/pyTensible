import Dependency

class Request(Dependency.Dependency):
	"""A class to hold a dependency and encapsulate dependency satisfation checks"""
	def __init__(self, requestName, requestString):
		Dependency.Dependency.__init__(self, requestName, requestString)
		self.requestName = requestName
		self.requestString = requestString
		self.requestRange = requestString.rstrip().lstrip()
		
	def satisfied(self, requestName, version):
		"""Determines whether a dependency would be satisfied by the indicated version of plugin"""		
		if requestName != self.requestName:
			return False
		
		if not Dependency.satisfies_range(version, self.reqeustRange):
			return False
		return True
