# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#     http://www.apache.org/licenses/LICENSE-2.0
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

from abc import ABCMeta, abstractmethod

import redis

from mms.log import get_logger


# TODO rename to functional description? (ResponseStore)
class HashMap(object):
    """
    HashMap is an abstract class for storing responses from the model engine
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def put(self, key, data):
        pass

    @abstractmethod
    def get(self, key, timeout):
        pass


class RedisHashMap(HashMap):
    """
    RedisHashMap implements HashMap with Redis as a persistent data store.
    """
    # TODO enable redis settings to be changed from cli
    def __init__(self):
        try:
            self.redis = redis.StrictRedis(host="localhost", port=6379, db=0)
        except Exception as e:
            raise Exception("Failed to connect to Redis: %s" % e)

    def put(self, key, data):
        self.redis.lpush(key, data)

    def get(self, key, timeout=60):
        data = self.redis.blpop(key, timeout)
        self.redis.delete(key)

        return data
