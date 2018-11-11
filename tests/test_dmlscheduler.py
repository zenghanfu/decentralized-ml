import tests.context

import time
import logging
import os
import pytest
import numpy as np

from core.scheduler             import DMLScheduler
from core.configuration         import ConfigurationManager
from tests.testing_utils        import make_initialize_job, make_model_json, make_train_job, make_hyperparams


config_manager = ConfigurationManager()
config_manager.bootstrap(
    config_filepath='tests/artifacts/runner_scheduler/configuration.ini'
)

class MockCommunicationManager:
    def inform(self, dummy1, dummy2):
        pass

communication_manager = MockCommunicationManager()
scheduler = DMLScheduler(config_manager)
scheduler.configure(communication_manager)

def test_dmlscheduler_sanity():
    """
    Check that the scheduling/running functionality is maintained.
    """
    model_json = make_model_json()
    initialize_job = make_initialize_job(model_json)
    scheduler.add_job(initialize_job)
    scheduler.runners_run_next_jobs()
    while not scheduler.processed:
        time.sleep(0.1)
        scheduler.runners_run_next_jobs()
    output = scheduler.processed.pop(0)
    initial_weights = output.results['weights']
    assert type(initial_weights) == list
    assert type(initial_weights[0]) == np.ndarray


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
    assert len(scheduler.processed) == 5
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
    m = 1
    for _ in range(m):
        initialize_job = make_initialize_job(model_json)
        scheduler.add_job(initialize_job)
    scheduler.start_cron(period_in_mins = 0.01)
    time.sleep(2)
    assert len(scheduler.processed) == m
    while scheduler.processed:
        output = scheduler.processed.pop(0)
        initial_weights = output.results['weights']
        assert type(initial_weights) == list
        assert type(initial_weights[0]) == np.ndarray
    n = 6
    hyperparams = make_hyperparams()
    for _ in range(n):
        train_job = make_train_job(model_json, initial_weights, hyperparams)
        scheduler.add_job(train_job)
    time.sleep(4)
    scheduler.stop_cron()
    assert len(scheduler.processed) == n