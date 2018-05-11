# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#     http://www.apache.org/licenses/LICENSE-2.0
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import traceback
import base64

from flask import abort

from mms.batching import ManualBatchingStrategy
from mms.hashmap import RedisHashMap
from mms.queue import RedisQueue
from mms.log import get_logger
from mms.metrics_manager import MetricsManager
from mms.codec import ImageCodec, JsonCodec


logger = get_logger()


class ModelThread(object):
    """
    ModelThread is a wrapper on top of ModelService that runs the main loop
    """

    # TODO set sleep_time, batch size, and strategy via cli
    def __init__(self, model_name, model_service):
        """
        Initialize ModelThread
        """
        self.model_name = model_name
        self.model_service = model_service

        self.queue = RedisQueue()
        self.hashmap = RedisHashMap()

        self.batching_strategy = ManualBatchingStrategy(batch_size=16)

    def start(self):
        """
        Main ModelThread loop
        Get data batch from queue, reshape module, run inference, send results back

        """
        while True:
            # TODO generate new id for queue each run time
            # config class for queue generated when endpoint is created?
            batch, batch_size = self.batching_strategy.wait_for_batch(self.queue, self.model_name)

            data = []
            ids = []
            for item in batch:
                item = JsonCodec.deserialize(item)
                ids.append(item['id'])
                # data_item = []
                for input in item['data']:
                    # data_item.append(base64.decodestring(input))
                    data.append(base64.decodestring(input))
                # data.append(data_item)

            # assert len(data) == batch_size

            # will padding be faster than reshaping?
            # TODO fix this
            # self.model_service.set_batch_size(batch_size)

            try:
                output = self.model_service.inference(data)
            except Exception:
                if self.model_name + '_Prediction5XX' in MetricsManager.metrics:
                    MetricsManager.metrics[self.model_name + '_Prediction5XX'].update(metric=1)
                logger.error(str(traceback.format_exc()))
                abort(500, "Error occurs while inference was executed on server.")

            # TODO add error handling and support for image response
            for id, response in zip(ids, output):
                self.hashmap.put(id, JsonCodec.serialize(response))
