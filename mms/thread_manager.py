# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#     http://www.apache.org/licenses/LICENSE-2.0
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import inspect
import threading

import mms.model_service.mxnet_model_service as mxnet_model_service
from mms.model_service.model_service import load_service
from mms.model_service.mxnet_model_service import MXNetBaseService
from mms.model_thread import ModelThread
from mms.storage import KVStorage


class ThreadManager(object):
    """ThreadManager is responsible for storing information and managing
    model service threads. In later phase, ThreadManager will also be
    responsible for model versioning, and caching.
    """

    def __init__(self):
        """
        Initialize Thread Manager.
        """

        # registry for model definition and user defined functions
        self.model_service_registry = KVStorage('model_services')
        self.func_registry = KVStorage('func')

        # loaded model service threads
        self.loaded_model_services = KVStorage('loaded_model_services')

    def get_model_services_registry(self, model_service_names=None):
        """
        Get all registered Model Service Class Definitions in a dictionary 
        from internal registry according to name or list of names. 
        If nothing is passed, all registered model threads will be returned.

        Parameters
        ----------
        model_service_names : List, optional
            Names to retrieve registered model services.
            
        Returns
        ----------
        Dict of name, model service pairs
            Registered model services according to given names.
        """
        if model_service_names is None:
            return self.model_service_registry

        return {
            model_service_name: self.model_service_registry[model_service_name]
            for model_service_name in model_service_names
        }

    def add_model_service_to_registry(self, model_service_name, ModelServiceClassDef):
        """
        Add a model service to internal registry.

        Parameters
        ----------
        model_service_name : string
            Model service name to be added.
        ModelServiceClassDef: python class
            Model Service Class Definition which can initialize a model service.
        """
        self.model_service_registry[model_service_name] = ModelServiceClassDef

    def get_loaded_model_services(self, model_service_names=None):
        """
        Get all model services which are loaded in the system into a dictionary 
        according to name or list of names. 
        If nothing is passed, all loaded model services will be returned.

        Parameters
        ----------
        model_service_names : List, optional
             Model thread names to retrieve loaded model threads.
            
        Returns
        ----------
        Dict of name, model thread pairs
            Loaded model threads according to given names.
        """
        if model_service_names is None:
            return self.loaded_model_services

        return {
            model_service_name: self.loaded_model_services[model_service_name]
            for model_service_name in model_service_names
        }

    def load_model(self, service_name, model_name, model_path, manifest, ModelServiceClassDef, gpu=None):
        """
        Load a single model into a model thread by using
        user passed Model Service Class Definitions.

        Parameters
        ----------
        service_name : string
            Service name
        model_name : string
            Model name
        model_path: string
            Model path which can be url or local file path.
        manifest: string
            Model manifest
        ModelServiceClassDef: python class
            Model Service Class Definition which can initialize a model service.
        gpu : int
            Id of gpu device. If machine has two gpus, this number can be 0 or 1.
            If it is not set, cpu will be used.
        """
        model_service = ModelServiceClassDef(model_name, model_path, manifest, gpu)
        t = threading.Thread(target=ModelThread(model_name, model_service).start, args=())
        t.daemon = True
        t.start()

        # TODO refactor so that model endpoints are service names
        self.loaded_model_services[model_name] = model_service

    @staticmethod
    def parse_model_services_from_module(service_file):
        """
        Parse user defined module to get all model service classe in it.

        Parameters
        ----------
        service_file : User defined module file path 
            A python module which will be parsed by given name.
            
        Returns
        ----------
        List of model service class definitions.
            Those parsed python class can be used to initialize model service.
        """
        module = load_service(service_file) if service_file else mxnet_model_service
        # Parsing the module to get all defined classes
        classes = [cls[1] for cls in inspect.getmembers(module, inspect.isclass)]
        # Check if class is subclass of base ModelService class
        return list(filter(lambda cls: issubclass(cls, MXNetBaseService), classes))
