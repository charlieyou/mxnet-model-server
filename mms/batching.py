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
import time

from mms.log import get_logger

logger = get_logger()


class BatchingStrategy(object):
    """
    Base class for backend batching strategies
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def wait_for_batch(self, queue, model_name):
        """

        Parameters
        ----------
        queue : mms.queue.Queue


        Returns
        -------
        data : dict
            {
                batch_size
                data
                ids
            }
        """
        pass


class ManualBatchingStrategy(BatchingStrategy):
    """
    Batching Strategy where a max batch size and polling time is set.
    Whatever is in the queue at the time of polling is returned up to the max batch size.
    """
    def __init__(self, batch_size=1, latency=0.25, sleep_time=0.01):
        self.batch_size = batch_size
        self.latency = latency
        self.sleep_time = sleep_time

    # TODO add latency timer
    def wait_for_batch(self, queue, model_name):
        logger.info("Waiting for batch from queue %s" % model_name)
        while True:
            batch = queue.pop(model_name, self.batch_size)
            if batch:
                return batch, len(batch)

            time.sleep(self.sleep_time)
