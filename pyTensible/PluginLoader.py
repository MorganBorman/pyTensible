import os, sys, traceback

from Manifest import Manifest, MalformedManifest
from Plugin import Plugin, MalformedPlugin
from Errors import * #@UnusedWildImport
from Logging import logger

manifestFilename = "plugin.manifest"

class PluginLoader:
	def __init__(self):
		self.__manifests = {}
		self.__suppress_list = []
		self.__plugin_objects = {}
		self.__plugins = {}
		self.__providers = {}
		self.__failed = []
		self.__unloaded = False
		self.__reload_order = [] #Used to reload the plug-ins in dependency order
		
	def load_suppress_list(self, suppress_list=[]):
		"Provide a list of plug-in SymbolicNames which should not be loaded from any plug-in directory."
		self.__suppress_list += suppress_list
	
	def load_plugins(self, plugin_path, local_suppress_list=[]):
		"Load all plug-ins (except those in the suppress list) from the specified directory."
		logger.info('Loading plug-ins from: ' + plugin_path)
		
		if not os.path.isdir(plugin_path):
			raise InvalidPluginDirectory("Given path is not a directory: " + plugin_path)
		
		sys.path.append(plugin_path)
		
		self.__scan_manifests(plugin_path)
		
		for SymbolicName in self.__manifests.keys():
			self.__load_plugin(SymbolicName, None, [], self.__suppress_list + local_suppress_list)
		
		sys.path.remove(plugin_path)
		
	def get_resource(self, symbolicName):
		"Get the loaded plug-in object. This is the key to accessing resources provided by plug-ins."
		try:
			return self.__plugin_objects[symbolicName]
		except KeyError:
			raise UnavailableResource(symbolicName)
		
	def unload_all(self):
		"Unload all loaded plug-ins."
		logger.info('Unloading all plug-ins...')
		
		if not self.__unloaded:
			for pluginName, pluginObject in self.__plugin_objects.items():
				try:
					pluginObject.unload(self)
					logger.info("Unloaded plug-in: " + pluginName)
				except:
					exceptionType, exceptionValue, exceptionTraceback = sys.exc_info() #@UnusedVariable
					logger.error("Uncaught exception occurred while unloading plugin: " + traceback.format_exc())
				
			self.__unloaded = True
			
	def __scan_manifests(self, plugin_path):
		self.__manifests = {}
		
		pluginDirectories = os.listdir(plugin_path)
		
		for directory in pluginDirectories:
			
			pluginDirectory = plugin_path + '/' + directory
			manifestPath = pluginDirectory + '/' + manifestFilename
			
			if os.path.isdir(pluginDirectory) and os.path.exists(manifestPath):
				try:
					manifest = Manifest(pluginDirectory, manifestFilename)
					self.__process_manifest(manifest)
					
				except MalformedManifest:
					logger.error("Malformed plug-in manifest: " + manifestPath)
			else:
				logger.error("Cannot read plug-in: " + pluginDirectory)
				
	def __process_manifest(self, manifest):
		if manifest.Enabled:
	
			if manifest.Provides != None:
			
				if not manifest.Provides in self.__providers.keys():
					self.__providers[manifest.Provides] = {}
				self.__providers[manifest.Provides][manifest.SymbolicName] = manifest
	
			self.__manifests[manifest.SymbolicName] = manifest
		else:
			logger.info("plug-in disabled: " + manifest.Name)	
		
	def __load_dependencies(self, manifest, depend_list, suppress_list):
		for dependency in manifest.Dependencies:
			#check if we have a cycle forming
			if dependency.dependencyName in depend_list:
				#append the name here for showing the cycle in the exception
				depend_list.append(dependency.dependencyName)
				
				self.__failed.append(manifest.SymbolicName)
				raise DependencyCycle(str("->".join(depend_list)))
			
			#skip ones that have previously failed to load
			if dependency.dependencyName in self.__failed:
				#add this one to the list of failed
				self.__failed.append(manifest.SymbolicName)
				raise FailedDependency(dependency.dependencyName)
			#else load the plug-in
			else: 
				self.__load_plugin(dependency.dependencyName, dependency, depend_list, suppress_list)
	
	def __load_requests(self, manifest, depend_list, suppress_list):
		for request in manifest.Requests:
			for provider in self.__get_provider_manifests(request.requestName):
				#check if we have a cycle forming
				if provider.SymbolicName in depend_list:
					#append the name here for showing the cycle in the exception
					depend_list.append(provider.SymbolicName)
				
					self.__failed.append(manifest.SymbolicName)
					raise DependencyCycle(str("->".join(depend_list)))
			
				#skip ones that have previously failed to load
				if provider.SymbolicName in self.__failed:
					logger.error(provider.Name + " a " + provider.Provides + " provider previously __failed to load.")
				#else load the provider
				else: 
					try:
						self.__load_plugin(provider.SymbolicName, request, depend_list, suppress_list)
					except UnsatisfiedDependency:
						logger.error(provider.Name + " a " + provider.Provides + " provider failed: missing dependencies.")
					except MalformedPlugin:
						logger.error(provider.Name + " a " + provider.Provides + " provider failed: malformed plug-in.")
			
	def __load_plugin(self, symbolicName, dependency, depend_list, suppress_list):
		#logger.debug("trying to load plug-in: " + symbolicName)
		"""Wrapper to __process_plugin to provide nested exception handling for all loading of plug-ins"""
		try:
			if not symbolicName in suppress_list:
				self.__process_plugin(symbolicName, dependency, depend_list, suppress_list)
			else:
				logger.info("Ignore plug-in: " + symbolicName + " -- present in suppress list.")
		except UnsatisfiedDependency as e:
			logger.error("Ignore plug-in: " + symbolicName + " -- unsatisfied dependency: " + str(e))
		except UnavailableResource as e:
			logger.error("Failed plug-in: " + symbolicName + " -- unsatisfied dependency: " + str(e))
		except MalformedPlugin as e:
			logger.error("Failed plug-in: " + symbolicName + " -- __failed loading dependency: " + str(e))
		except FailedDependency as e:
			logger.error("Failed plug-in: " + symbolicName + " -- dependency previously __failed to load: " + str(e))
		except InvalidResourceComponent as e:
			logger.error("Failed plug-in: " + symbolicName + " Required resource: " + e.resource + " did not provide a valid " + e.componentType + e.component)
		
	def __process_plugin(self, symbolicName, dependency, depend_list, suppress_list):
		#depend_list holds the list of dependencies along the depth-first cross section of the tree. Used to find cycles.
		depend_list = depend_list[:]
		depend_list.append(symbolicName)
		
		#get the manifest from the manifest list
		try:
			manifest = self.__manifests[symbolicName]
		except KeyError:
			self.__failed.append(symbolicName)
			raise UnsatisfiedDependency(symbolicName + ":" + dependency.dependencyString)
		
		#to check whether the dependency can actually be satisfied by loading this plug-in
		if dependency != None:
			if dependency.satisfied(manifest.SymbolicName, manifest.Version):
				pass #dependency is satisfied
			else:
				self.__failed.append(manifest.SymbolicName)
				raise UnsatisfiedDependency(symbolicName + ":" + dependency.dependencyString + ". Version present is: " + manifest.Version)
		
		#preliminary checks done. Start actually loading the plug-in now
		if not manifest.SymbolicName in self.__plugins.keys():
			
			#load the dependencies
			self.__load_dependencies(manifest, depend_list, suppress_list)
			
			#load the requests
			self.__load_requests(manifest, depend_list, suppress_list)
			
			#import the plug-in
			try:
				plugin_module = __import__(manifest.SymbolicName)
			except ImportError:
				exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()	#@UnusedVariable
				logger.error('Uncaught exception occurred in command handler.')
				logger.error(traceback.format_exc())
				raise MalformedPlugin(manifest.SymbolicName + ": __failed to import.")
			
			#get the plug-in class from the module
			try:
				pluginObjectClass = plugin_module.__getattribute__("Plugin")
			except AttributeError:
				self.__failed.append(manifest.SymbolicName)
				raise MalformedPlugin(manifest.SymbolicName + ": class is not present.")
			
			#check that the plug-in's class is a subclass of 'Plugin'
			if not issubclass(pluginObjectClass, Plugin):
				self.__failed.append(manifest.SymbolicName)
				raise MalformedPlugin(manifest.SymbolicName + ": is not derived from the Plugin class.")
			
			#add the plug-in object and plug-in module to the correct dictionaries
			self.__plugin_objects[manifest.SymbolicName] = pluginObjectClass()
			self.__plugins[manifest.SymbolicName] = plugin_module
			
			#load the actual plug-in
			self.__plugin_objects[manifest.SymbolicName].load(self)
			logger.info("Loaded plug-in: " + manifest.Name)
			self.__reload_order.append(manifest.SymbolicName)
		else:
			logger.debug("Already loaded: " + manifest.Name)
			
	def __get_provider_manifests(self, provides):
		try:
			return self.__providers[provides].values()
		except KeyError:
			return []
