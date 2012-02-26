import os, sys, traceback, abc

from Manifest import Manifest, MalformedManifest
from Errors import * #@UnusedWildImport
from Logging import logger

manifest_filename = "plugin.manifest"

class PluginLoader:
	'''
	A class which handles loading of plug-directories and their associated class hierarchies.
	'''
	######################################################################
	######################### Public Attributes ##########################
	######################################################################
	
	logger = logger
	
	######################################################################
	######################### Private Atrributes #########################
	######################################################################
	
	#This is the global list of symbolic_names which are ignored.
	_suppress_list = []
	
	#This holds all the manifest objects
	_manifests = {}
	
	#These are the plug0in modules
	_plugin_modules = {}
	
	#These are the plug-in classes.
	_plugin_classes = {}
	
	#These are the interfaces which a plug-in may claim to implement.
	_interfaces = {}
	
	#These are the real plug-in objects which can be retrieved with pluginLoader.get_resource(symbolic_name)
	_resources = {}
	
	#This holds dictionaries of plug-ins which implement specific interfaces, keyed as follows: self._providers[interface][symbolic_name] = resource
	_providers = {}
	
	#This holds the lists of manifests in a dictionary keyed by the interface name
	_provider_manifests = {}
	
	#This is a list of plug-ins which have previously failed to load. Used to save time while loading.
	_failed = []
	
	#Keep track of the plug-ins in dependency order. Useful for reloading and unloading in the correct order without recalculating it.
	_load_order = []
	
	def __init__(self, local_logger=None):
		"If necessary set a local logger for this instance of the pluginLoader."
		if local_logger != None:
			self.logger = local_logger
			
		base_path = os.path.join(os.path.dirname(__file__), 'base')
		self.load_plugins(base_path)
		
		self.Plugin_class = self._interfaces['Plugin']
		
	######################################################################
	########################### Public methods ###########################
	######################################################################
	
	def load_suppress_list(self, suppress_list=[]):
		"Provide a list of plug-in SymbolicNames which should not be loaded from any plug-in directory."
		pass
	
	def load_plugins(self, plugin_path, local_suppress_list=[]):
		"Load all plug-ins (except those in the suppress list) from the specified directory."
		logger.info('Loading plug-ins from: ' + plugin_path)
		
		if not os.path.isdir(plugin_path):
			raise InvalidPluginDirectory("Given path is not a directory: " + plugin_path)
		
		sys.path.append(plugin_path)
		
		self._scan_manifests(plugin_path)
		
		for symbolic_name in self._manifests.keys():
			depend_list = []
			self._load_item(symbolic_name, None, depend_list, self._suppress_list + local_suppress_list)
		
		sys.path.remove(plugin_path)
	
	def get_resource(self, symbolic_name):
		"Get the loaded plug-in object. This is the key to accessing resources provided by plug-ins."
		try:
			return self._resources[symbolic_name]
		except KeyError:
			raise UnavailableResource(symbolic_name)
	
	def get_providers(self, interface):
		"Get all loaded plug-in objects which implement this interface as a dictionary indexed by symbolic_name."
		pass
	
	def unload_all(self):
		"Call the unload method on all plug-ins."
		pass
		
	######################################################################
	########################## Private methods ###########################
	######################################################################
	
	def _scan_manifests(self, plugin_path):
		plugin_directories = os.listdir(plugin_path)
		
		for directory in plugin_directories:
			
			plugin_directory = os.path.join(plugin_path, directory)
			manifest_path = os.path.join(plugin_directory, manifest_filename)
			
			if os.path.isdir(plugin_directory) and os.path.exists(manifest_path):
				try:
					manifest = Manifest(plugin_directory, manifest_filename)
					self._process_manifest(manifest)
					
				except MalformedManifest:
					logger.error("Malformed plug-in manifest: " + manifest_path)
			else:
				logger.error("Cannot read plug-in: " + plugin_directory)
				
	def _process_manifest(self, manifest):
		if manifest.enabled:
			if manifest.interfaces_implemented != None:
				for extension_point in manifest.interfaces_implemented:
					
					extension_point_name = extension_point.dependency_name
					
					if not extension_point_name in self._provider_manifests.keys():
						self._provider_manifests[extension_point_name] = []
						
					self._provider_manifests[extension_point_name].append(manifest)
	
			self._manifests[manifest.symbolic_name] = manifest
		else:
			logger.info("plug-in disabled: " + manifest.symbolic_name)
			
	def _load_item(self, symbolic_name, dependency, depend_list, suppress_list):
		#logger.debug("trying to load plug-in: " + symbolic_name)
		"""Wrapper to _process_item to provide nested exception handling for all loading of interfaces and plug-ins"""
		try:
			if not symbolic_name in suppress_list:
				self._process_item(symbolic_name, dependency, depend_list, suppress_list)
			else:
				logger.info("Ignore loading: " + symbolic_name + " -- present in suppress list.")
		except UnsatisfiedDependency as e:
			logger.error("Ignore loading: " + symbolic_name + " -- unsatisfied dependency: " + str(e))
		except UnavailableResource as e:
			logger.error("Failed loading: " + symbolic_name + " -- unsatisfied dependency: " + str(e))
		except MalformedPlugin as e:
			logger.error("Failed loading: " + symbolic_name + " -- failed loading dependency: " + str(e))
		except FailedDependency as e:
			logger.error("Failed loading: " + symbolic_name + " -- dependency previously failed to load: " + str(e))
		except InvalidResourceComponent as e:
			logger.error("Failed loading: " + symbolic_name + " required resource: " + e.resource + " did not provide a valid " + e.componentType + e.component)
			
	def _process_item(self, symbolic_name, dependency, depend_list, suppress_list):
		#depend_list holds the list of dependencies along the depth-first cross section of the tree. Used to find cycles.
		depend_list = depend_list[:]
		depend_list.append(symbolic_name)
		
		#get the manifest from the manifest list
		try:
			manifest = self._manifests[symbolic_name]
		except KeyError:
			self._failed.append(symbolic_name)
			raise UnsatisfiedDependency(symbolic_name + ":" + str(dependency.dependency_range))
		
		#to check whether the dependency can actually be satisfied by loading this plug-in
		if dependency != None:
			if dependency.satisfied(manifest.symbolic_name, manifest.version):
				pass #dependency is satisfied
			else:
				self._failed.append(manifest.symbolic_name)
				raise UnsatisfiedDependency(symbolic_name + ":" + dependency.dependency_string + ". version present is: " + manifest.version)
			
		if manifest.defines:
			self._process_interface(manifest, depend_list, suppress_list)
		else:
			self._process_plugin(manifest, depend_list, suppress_list)
			
	def _process_interface(self, manifest, depend_list, suppress_list):
		"preliminary checks done. Start actually loading the interface now"
		
		if not manifest.symbolic_name in self._interfaces.keys():
			
			#load the dependencies
			self._load_dependencies(manifest, depend_list, suppress_list)
			
			#load the requests
			self._load_requests(manifest, depend_list, suppress_list)
			
			#load the extension points
			interfaces_dictionary = self._load_interfaces(manifest, depend_list, suppress_list)
			
			#this is the dictionary of stuff that we give the plug-in for free at load time
			plugin_environment = {}
			
			plugin_environment.update(interfaces_dictionary)

			plugin_environment["abc"] = abc
			
			#import the plug-in
			try:
				#place the interface classes which this module implements into the __builtins__ module so they are available to subclass
				backups = _replace_builtins(plugin_environment)
				
				#Actually load the plug-in's module
				plugin_module = __import__(manifest.symbolic_name)
				
				#add the interface classes from which the plug-in object was derived to the global scope of the plugin
				#this makes it possible for later reference of static methods and things like this.
				plugin_module.__dict__.update(plugin_environment)
				
				#also add the PluginLoader object to there for similar reasons
				plugin_module.__dict__['pluginLoader'] = self
				
			except ImportError:
				exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()	#@UnusedVariable
				logger.error('Uncaught exception occurred in interface.')
				logger.error(traceback.format_exc())
				raise MalformedPlugin(manifest.symbolic_name + ": failed to import.")
			finally:
				_restore_builtins(backups)
			
			#get the plug-in class from the module
			try:
				interface_class = plugin_module.__getattribute__(manifest.symbolic_name)
			except AttributeError:
				self._failed.append(manifest.symbolic_name)
				raise MalformedPlugin(manifest.symbolic_name + ": class is not present.")
			
			#check whether they actually subclassed the bases which they claimed they would
			for interface_name in interfaces_dictionary.keys():
				if not issubclass(interface_class, plugin_environment[interface_name]):
					raise MalformedPlugin(manifest.symbolic_name + ": is not derived from interface class '%s' as specified." %interface_name)
			
			self._interfaces[manifest.symbolic_name] = interface_class
			
			logger.info("Loaded plug-in interface: " + manifest.symbolic_name)
				
			self._load_order.append(manifest.symbolic_name)
		else:
			logger.debug("Already loaded: " + manifest.symbolic_name)
	
	def _process_plugin(self, manifest, depend_list, suppress_list):
		"preliminary checks done. Start actually loading the plug-in now"
		
		if not manifest.symbolic_name in self._resources.keys():
			
			#load the dependencies
			self._load_dependencies(manifest, depend_list, suppress_list)
			
			#load the requests
			self._load_requests(manifest, depend_list, suppress_list)
			
			#load the extension points
			interfaces_dictionary = self._load_interfaces(manifest, depend_list, suppress_list)
			
			#this is the dictionary of stuff that we give the plug-in for free at load time
			plugin_environment = {}
			
			plugin_environment.update(interfaces_dictionary)
			
			#import the plug-in
			try:
				#place the interface classes which this module implements into the __builtins__ module so they are available to subclass
				backups = _replace_builtins(plugin_environment)
				
				#Actually load the plug-in's module
				plugin_module = __import__(manifest.symbolic_name)
				
				#add the interface classes from which the plug-in object was derived to the global scope of the plugin
				#this makes it possible for later reference of static methods and things like this.
				plugin_module.__dict__.update(plugin_environment)
				
				#also add the PluginLoader object to there for similar reasons
				plugin_module.__dict__['pluginLoader'] = self
				
			except ImportError:
				exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()	#@UnusedVariable
				logger.error('Uncaught exception occurred in plug-in.')
				logger.error(traceback.format_exc())
				raise MalformedPlugin(manifest.symbolic_name + ": failed to import.")
			finally:
				_restore_builtins(backups)
			
			#get the plug-in class from the module
			try:
				plugin_class = plugin_module.__getattribute__(manifest.symbolic_name)
			except AttributeError:
				self._failed.append(manifest.symbolic_name)
				raise MalformedPlugin(manifest.symbolic_name + ": class is not present.")
			
			#check that the plug-in's class is a subclass of 'Plugin'
			if not issubclass(plugin_class, self.Plugin_class):
				self._failed.append(manifest.symbolic_name)
				raise MalformedPlugin(manifest.symbolic_name + ": is not derived from the Plugin class.")
			
			#check whether they actually subclassed the bases which they claimed they would
			for interface_name in interfaces_dictionary.keys():
				if not issubclass(plugin_class, plugin_environment[interface_name]):
					raise MalformedPlugin(manifest.symbolic_name + ": is not derived from base class '%s' as specified." %interface_name)
			
			#add the plug-in module, class, and object to the correct dictionaries
			self._plugin_modules[manifest.symbolic_name] = plugin_module
			self._plugin_classes[manifest.symbolic_name] = plugin_class
			self._resources[manifest.symbolic_name] = plugin_class()
			
			for interface_name in interfaces_dictionary.keys():
				
				if not interface_name in self._providers.keys():
					self._providers[interface_name] = {}
					
				self._providers[interface_name][manifest.symbolic_name] = self._resources[manifest.symbolic_name]
			
			#load the actual plug-in
			self._resources[manifest.symbolic_name].load()
			logger.info("Loaded plug-in: " + manifest.symbolic_name)
				
			self._load_order.append(manifest.symbolic_name)
		else:
			logger.debug("Already loaded: " + manifest.symbolic_name)
			
	def _load_interfaces(self, manifest, depend_list, suppress_list):
		"Load the base plug-ins whose defined interfaces the specified plug-in claims to implement and return the dictionary of them keyed by their symbolicNames."
		interfaces_dictionary = {}
		
		for interface_dependency in manifest.interfaces_implemented:
			#check if we have a cycle forming
			if interface_dependency.dependency_name in depend_list:
				#append the name here for showing the cycle in the exception
				depend_list.append(interface_dependency.dependency_name)
			
				self._failed.append(manifest.symbolic_name)
				raise DependencyCycle(str("->".join(depend_list)))
		
			#skip ones that have previously failed to load
			if interface_dependency.dependency_name in self._failed:
				logger.error("The interface, " + interface_dependency.dependency_name + ", previously failed to load.")
			#else load the provider
			else:
				try:
					self._load_item(interface_dependency.dependency_name, interface_dependency, depend_list, suppress_list)
					interfaces_dictionary[interface_dependency.dependency_name] = self._interfaces[interface_dependency.dependency_name]
				except KeyError:
					logger.error("Loading the interface, " + interface_dependency.dependency_name + " failed: unknown (interface missing from interfaces dictionary).")
					raise UnsatisfiedInterface(interface_dependency.dependency_name + " was not loaded correctly.")
				except UnsatisfiedDependency:
					logger.error("Loading the interface, " + interface_dependency.dependency_name + " failed: missing dependencies.")
				except MalformedPlugin:
					logger.error("Loading the interface, " + interface_dependency.dependency_name + " failed: malformed plug-in.")
		
		return interfaces_dictionary
	
	def _load_dependencies(self, manifest, depend_list, suppress_list):
		for dependency in manifest.dependencies:
			#check if we have a cycle forming
			if dependency.dependency_name in depend_list:
				#append the name here for showing the cycle in the exception
				depend_list.append(dependency.dependency_name)
				
				self._failed.append(manifest.symbolic_name)
				raise DependencyCycle(str("->".join(depend_list)))
			
			#skip ones that have previously failed to load
			if dependency.dependency_name in self._failed:
				#add this one to the list of failed
				self._failed.append(manifest.symbolic_name)
				raise FailedDependency(dependency.dependency_name)
			#else load the plug-in
			else: 
				self._load_item(dependency.dependency_name, dependency, depend_list, suppress_list)
	
	def _load_requests(self, manifest, depend_list, suppress_list):
		for request in manifest.requests:
			for provider in self._get_provider_manifests(request.requestName):
				#check if we have a cycle forming
				if provider.symbolic_name in depend_list:
					#append the name here for showing the cycle in the exception
					depend_list.append(provider.symbolic_name)
				
					self._failed.append(manifest.symbolic_name)
					raise DependencyCycle(str("->".join(depend_list)))
			
				#skip ones that have previously failed to load
				if provider.symbolic_name in self._failed:
					logger.error(provider.name + " a " + provider.Provides + " provider previously _failed to load.")
				#else load the provider
				else: 
					try:
						self._load_plugin(provider.symbolic_name, request, depend_list, suppress_list)
					except UnsatisfiedDependency:
						logger.error(provider.name + " a " + provider.Provides + " provider failed: missing dependencies.")
					except MalformedPlugin:
						logger.error(provider.name + " a " + provider.Provides + " provider failed: malformed plug-in.")
						
	def _get_provider_manifests(self, provides):
		try:
			return self._provider_manifests[provides][:]
		except KeyError:
			return []
		
def _replace_builtins(replacements={}):
	"Places the items in the replacements dictionary and returns a backup dictionary of the replaced items if any."
	backups = {}
	for key in replacements.keys():
		if key in __builtins__.keys():
			backups[key] = __builtins__[key]
		__builtins__[key] = replacements[key]
			
	return backups

def _restore_builtins(backups):
	"Restores the previously replaced __builtins__ with those in the provided backups dictionary."
	for key in backups.keys():
		__builtins__[key] = backups[key]