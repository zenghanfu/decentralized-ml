import tests.context

import time
import logging
import os
import pytest
import numpy as np
import ipfsapi

from core.scheduler             import DMLScheduler
from core.configuration         import ConfigurationManager
from tests.testing_utils        import (make_initialize_job, make_model_json, \
                                        make_split_job, make_communicate_job)


# @pytest.fixture(scope='session')
# def config_manager():
config_manager = ConfigurationManager()
config_manager.bootstrap(
    config_filepath='tests/artifacts/runner_scheduler/configuration.ini'
)
    # return config_manager

# @pytest.fixture(scope='session')
# def ipfs_client(config_manager):
config = config_manager.get_config()
ipfs_client = ipfsapi.connect(config.get('BLOCKCHAIN', 'host'), 
                        config.getint('BLOCKCHAIN', 'ipfs_port'))


@pytest.fixture(scope='session')
def mnist_filepath():
    return 'tests/artifacts/runner_scheduler/mnist'

class MockCommunicationManager:
    def inform(self, dummy1, dummy2):
        pass

# @pytest.fixture()
# def communication_manager():
communication_manager = MockCommunicationManager()
    # return communication_manager
# @pytest.fixture()
# def scheduler(communication_manager, config_manager, ipfs_client):
scheduler = DMLScheduler(config_manager)
scheduler.configure(communication_manager, ipfs_client)
    # return scheduler

def test_dmlscheduler_sanity():
    """
    Check that the scheduling/running functionality is maintained.
    """
    scheduler.reset()
    model_json = make_model_json()
    initialize_job = make_initialize_job(model_json)
    scheduler.add_job(initialize_job)
    scheduler.runners_run_next_jobs()
    timeout = time.time
    while not scheduler.processed:
        time.sleep(0.1)
        scheduler.runners_run_next_jobs()
    output = scheduler.processed.pop(0)
    initial_weights = output.results['weights']
    assert type(initial_weights) == list
    assert type(initial_weights[0]) == np.ndarray

# TODO: The below test transiently fails. Why???
def test_dmlscheduler_communicate():
    """
    Test that the Scheduler can schedule/run Communicate Jobs.
    """
    scheduler.reset()
    m = 3
    for _ in range(m):
        communicate_job = make_communicate_job("testkey", "testweights")
        scheduler.add_job(communicate_job)
    scheduler.start_cron(period_in_mins=0.01)
    timeout = time.time() + 6
    while time.time() < timeout and len(scheduler.processed) < m:
        time.sleep(1)
    scheduler.stop_cron()
    assert len(scheduler.processed) == m, \
        "Jobs {} failed/not completed in time!".format([
        result.job.job_type for result in scheduler.processed])

# TODO: Uncomment to see a bug manifest!
def test_dmlscheduler_arbitrary_scheduling():
    """
    Manually schedule events and check that all jobs are completed.
    """
    scheduler.reset()
    model_json = make_model_json()
    first = make_initialize_job(model_json)
    second = make_initialize_job(model_json)
    scheduler.add_job(first)
    scheduler.add_job(second)
    while len(scheduler.processed) == 0:
        scheduler.runners_run_next_jobs()
    third = make_initialize_job(model_json)
    fourth = make_initialize_job(model_json)
    scheduler.add_job(third)
    scheduler.add_job(fourth)
    while len(scheduler.processed) < 4:
        scheduler.runners_run_next_jobs()
    fifth = make_initialize_job(model_json)
    scheduler.add_job(fifth)
    while len(scheduler.processed) < 5:
        scheduler.runners_run_next_jobs()
    assert len(scheduler.processed) == 5, \
        "Jobs {} failed/not completed in time!".format([
        result.job.job_type for result in scheduler.processed])
    while scheduler.processed:
        output = scheduler.processed.pop(0)
        initial_weights = output.results['weights']
        assert type(initial_weights) == list
        assert type(initial_weights[0]) == np.ndarray

def test_dmlscheduler_cron():
    """
    Test that the scheduler's cron works.
    """
    scheduler.reset()
    model_json = make_model_json()
    m = 2
    for _ in range(m):
        initialize_job = make_initialize_job(model_json)
        scheduler.add_job(initialize_job)
    scheduler.start_cron(period_in_mins = 0.01)
    timeout = time.time() + 6
    while time.time() < timeout and len(scheduler.processed) != m:
        time.sleep(1)
    scheduler.stop_cron()
    assert len(scheduler.processed) == m
    while scheduler.processed:
        output = scheduler.processed.pop(0)
        initial_weights = output.results['weights']
        assert type(initial_weights) == list
        assert type(initial_weights[0]) == np.ndarray
