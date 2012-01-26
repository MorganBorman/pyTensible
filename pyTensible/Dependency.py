"""
Lets assume all version numbers have three numeric parts and an optional
comment part as demonstrated below.
1.2.3
1.2.3.52x2

Keep in mind that the optional part will not get evaluated and is intended
for keeping track of revision numbers or something like that.
so:
1.2.3 equals 1.2.3.52x2

version strings look like this:
"[1.0.0,2.0.0)"
Which means the range from 1.0.0 inclusive to 2.0.0 exclusive is acceptable.
[] = inclusive
() = exclusive
"""

def getVersionParts(version):
	version = version.split('.')
	if len(version) > 3:
		version = version[:3]
	version = map(int, version)
	return version

def versionLess(version1, version2):
	version1 = getVersionParts(version1)
	version2 = getVersionParts(version2)
	for i in range(3):
		if version1[i] > version2[i]:
			return False
		elif version1[i] < version2[i]:
			return True
		else: #==
			pass #and look at the next part
	return False
	
def versionGreater(version1, version2):
	version1 = getVersionParts(version1)
	version2 = getVersionParts(version2)
	for i in range(3):
		if version1[i] > version2[i]:
			return True
		elif version1[i] < version2[i]:
			return False
		else: #==
			pass #and look at the next part
	return False
	
def versionEqual(version1, version2):
	version1 = getVersionParts(version1)
	version2 = getVersionParts(version2)
	for i in range(3):
		if version1[i] != version2[i]:
			return False
		else: #==
			pass #and look at the next part
	return True
	
def satisfiesRange(version1, versionRange):
	"""checks one parameter against the version given"""
	if not versionRange[0] in ['[', '(']:
		raise MalformedVersionRange()
	
	if not versionRange[-1] in [']', ')']:
		raise MalformedVersionRange()
	
	values = versionRange[1:-1].split(',')
	lower = values[0]
	upper = values[1]
	
	if versionRange[0] == '[':
		if versionLess(version1, lower):
			return False
	else:
		if versionLess(version1, lower) or versionEqual(version1, lower):
			return False
		
	if versionRange[-1] == ']':
		if versionGreater(version1, upper):
			return False
	else:
		if versionGreater(version1, upper) or versionEqual(version1, upper):
			return False
		
	return True

class Dependency:
	"""A class to hold a dependency and encapsulate dependency satisfaction checks"""
	def __init__(self, dependencyName, dependencyString):
		"""takes a dependency name and version string"""
		self.dependencyName = dependencyName
		self.dependencyString = dependencyString
		self.dependencyRange = dependencyString.rstrip().lstrip()
		
	def satisfied(self, dependencyName, version):
		"""Determines whether a dependency would be satisfied by the indicated version of plugin"""
		if dependencyName != self.dependencyName:
			return False
		
		if not satisfiesRange(version, self.dependencyRange):
			return False
		return True

class MalformedVersionRange(Exception):
	'''Invalid plugin form'''
	def __init__(self, value=''):
		Exception.__init__(self, value)