import os.path
import ConfigParser
import Dependency
import Request

class MalformedManifest(Exception):
	'''Invalid manifest form'''
	def __init__(self, value=''):
		Exception.__init__(self, value)

class Manifest(object):
	'''
	A class which pulls the fields out of the manifests and stores them as public class attributes.
	It is expected that these attributes will be read but not modified.
	'''
	name = ""
	symbolic_name = ""
	defines = False
	version = None
	author = None
	enabled = False
	
	requests = None
	interfaces_implemented = None
	dependencies = None
	
	def __init__(self, manifest_path, manifest_file):
		
		self.requests = []
		self.interfaces_implemented = []
		self.dependencies = []
		
		self.manifest_path = manifest_path
		self.manifest_file = manifest_file
		self.full_manifest_file_path = os.path.join(manifest_path, manifest_file)
		
		manifest = ConfigParser.ConfigParser()

		#Remove case insensitivity from the key part of the ConfigParser
		manifest.optionxform = str
		manifest.read(self.full_manifest_file_path)
		
		self.symbolic_name = manifest.get("Plug-in", "SymbolicName")
		
		#does this module specify a new resource class
		self.defines = manifest.get("Plug-in", "Defines") == "True"
		
		self.version = manifest.get("Plug-in", "Version")
		self.author = manifest.get("Plug-in", "Author")
		self.enabled = manifest.get("Plug-in", "Enabled") == "True"
		
		######################################################################
		######################### Read Dependencies ##########################
		######################################################################
		'''
		These specify basic single plug-in dependencies.
	
		Used when a plug-in will use pluginLoader.get_resource(symbolic_name)
		'''
		try:
			dependencies = manifest.items("Dependencies")
		except:
			dependencies = {}
		
		for dependency_name, dependency_string in dependencies:
			dependency = Dependency.Dependency(dependency_name, dependency_string)
			self.dependencies.append(dependency)
			
		######################################################################
		########################### Read Requests ############################
		######################################################################
		'''
		These specify that we want things which implement the given interface 
		to be loaded before this plug-in is.
		
		Used when a plug-in will use pluginLoader.get_providers(interface)
		'''
		try:
			requests = manifest.items("Requests")
		except:
			requests = {}
		
		for requestName, requestString in requests:
			request = Request.Request(requestName, requestString)
			self.requests.append(request)
			
		######################################################################
		########################## Read Interfaces ###########################
		######################################################################
		'''
		These specify which interfaces this plug-in will implement.
		
		Used to tell the pluginLoader which interfaces to make available at
		module load time for subclassing.
		'''
		try:
			interfaces_implemented = manifest.items("Implements")
		except:
			interfaces_implemented = {}
		
		for interface_name, interface_version_string in interfaces_implemented:
			implementation_base_dependency = Dependency.Dependency(interface_name, interface_version_string)
			self.interfaces_implemented.append(implementation_base_dependency)
