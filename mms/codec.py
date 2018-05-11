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
import base64
import io
import json
import sys

import numpy as np
from PIL import Image

from mms.log import get_logger


# TODO refactor this? Better pattern than simple codec classes?
# TODO add error handling and tests
class Codec(object):
    """
    Abstract class for serializing and deserializing data
    """
    __metaclass__ = ABCMeta

    @staticmethod
    @abstractmethod
    def serialize(data):
        pass

    @staticmethod
    @abstractmethod
    def deserialize(data):
        pass


class ImageCodec(Codec):
    """
    Codec for serializing and deserializing images
    """

    @staticmethod
    def serialize(data):
        im = Image.open(io.BytesIO(data))
        w, h = im.size
        im = im.copy(order='C')
        return base64.b64encode(im).decode('utf-8'), (1, w, h, 3)

    @staticmethod
    def deserialize(data, **kwargs):
        if sys.version_info.major == 3:
            data = bytes(data, encoding='utf-8')

        data = np.frombuffer(base64.decodestring(data), dtype='float32')
        return data.reshape(kwargs['shape'])


class JsonCodec(Codec):
    """
    Codec for serializing and deserializing python objects
    """

    @staticmethod
    def serialize(data):
        return json.dumps(data)

    @staticmethod
    def deserialize(data):
        data = data.decode('utf-8')
        return json.loads(data)
