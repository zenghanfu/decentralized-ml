import tests.context

import pytest
import numpy as np
import pandas as pd
import os
import shutil

from core.runner                import DMLRunner
from core.configuration         import ConfigurationManager
from core.utils.keras           import serialize_weights, deserialize_weights
from core.utils.enums           import JobTypes
from tests.testing_utils        import make_initialize_job, make_model_json, make_communicate_job
from tests.testing_utils        import make_train_job, make_validate_job, make_hyperparams
from tests.testing_utils        import make_split_job
 

session_filepaths = set()
# @pytest.fixture(scope="function")
# def cleanup():
#     yield
#     for session_filepath in session_filepaths:
#         if os.path.isdir(session_filepath):
#             shutil.rmtree(session_filepath)
#     assert len((os.listdir('tests/artifacts/runner_scheduler/mnist/transformed/'))) == 0, \
#         "Cleanup failed!"
@pytest.fixture
def config_manager():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/runner_scheduler/configuration.ini'
    )
    return config_manager

@pytest.fixture
def mnist_filepath():
    return 'tests/artifacts/runner_scheduler/mnist'

@pytest.fixture
def small_filepath():
    return 'tests/artifacts/runner_scheduler/test'

@pytest.fixture
def init_dmlresult_obj(config_manager, small_filepath):
    runner = DMLRunner(config_manager)
    initialize_job = make_initialize_job(make_model_json(), small_filepath)
    result = runner.run_job(initialize_job)
    return result

@pytest.fixture
def split_dmlresult_obj(config_manager, mnist_filepath):
    model_json = make_model_json()
    runner = DMLRunner(config_manager)
    split_job = make_split_job(
                            model_json, 
                            mnist_filepath,
                        )
    split_job.hyperparams['split'] = 0.75
    job_results = runner.run_job(split_job)
    session_filepath = job_results.job.session_filepath
    # Clean up
    if session_filepath and os.path.isdir(session_filepath):
        session_filepaths.add(session_filepath)
    return job_results

@pytest.fixture
def train_dmlresult_obj(config_manager, split_dmlresult_obj, init_dmlresult_obj, small_filepath):
    runner = DMLRunner(config_manager)
    initial_weights = init_dmlresult_obj.results['weights']
    session_filepath = split_dmlresult_obj.results['session_filepath']
    datapoint_count = split_dmlresult_obj.results['datapoint_count']
    train_job = make_train_job(
                    make_model_json(), 
                    initial_weights, 
                    make_hyperparams(split=1),
                    session_filepath,
                    datapoint_count
                )
    result = runner.run_job(train_job)
    # Clean up
    if session_filepath and os.path.isdir(session_filepath):
        session_filepaths.add(session_filepath)
    return result

def test_dmlrunner_communicate_job(config_manager, train_dmlresult_obj):
    runner = DMLRunner(config_manager)
    comm_job = train_dmlresult_obj.job
    comm_job.job_type = JobTypes.JOB_COMM.name
    comm_job.key = "test"
    result = runner.run_job(comm_job)
    assert result.results["receipt"]
    session_filepath = train_dmlresult_obj.job.session_filepath
    # Clean up
    if session_filepath and os.path.isdir(session_filepath):
        session_filepaths.add(session_filepath)

def test_dmlrunner_initialize_job_returns_list_of_nparray(config_manager, init_dmlresult_obj):
    assert init_dmlresult_obj.status == 'successful'
    results = init_dmlresult_obj.results
    initial_weights = results['weights']
    assert init_dmlresult_obj.job.job_type is JobTypes.JOB_INIT.name
    assert type(initial_weights) == list
    assert type(initial_weights[0]) == np.ndarray
    session_filepath = init_dmlresult_obj.job.session_filepath
    # Clean up
    if session_filepath and os.path.isdir(session_filepath):
        session_filepaths.add(session_filepath)

def test_dmlrunner_transform_and_split( \
        config_manager, small_filepath):
    model_json = make_model_json()
    runner = DMLRunner(config_manager)
    split_job = make_split_job(
                            model_json, 
                            small_filepath
                        )
    split_job.hyperparams['split'] = 0.75
    job_results = runner.run_job(split_job)
    session_filepath = job_results.results['session_filepath']
    assert os.path.isdir(session_filepath), \
        "Session folder does not exist!"
    train_filepath = os.path.join(session_filepath, 'train.csv')
    test_filepath = os.path.join(session_filepath, 'test.csv')
    assert os.path.isfile(train_filepath) and os.path.isfile(test_filepath), \
        "Training and test set not created!"
    train = pd.read_csv(train_filepath)
    test = pd.read_csv(test_filepath)
    assert len(train) == 6 and len(test) == 2, \
        "Train test split was not performed correctly."

    # Clean up
    if session_filepath and os.path.isdir(session_filepath):
        session_filepaths.add(session_filepath)

def test_dmlrunner_train_job_returns_weights_omega_and_stats( \
        config_manager, mnist_filepath, train_dmlresult_obj):
    result = train_dmlresult_obj
    session_filepath = result.job.session_filepath
    results = result.results
    new_weights = results['weights']
    omega = results['omega']
    train_stats = results['train_stats']
    assert result.job.job_type is JobTypes.JOB_TRAIN.name
    assert type(new_weights) == list
    assert type(new_weights[0]) == np.ndarray
    assert type(omega) == int or type(omega) == float
    assert type(train_stats) == dict

    # Clean up
    if session_filepath and os.path.isdir(session_filepath):
        session_filepaths.add(session_filepath)

def test_dmlrunner_same_train_job_with_split_1( \
        config_manager, mnist_filepath):
    model_json = make_model_json()
    hyperparams = make_hyperparams(split=1)
    runner = DMLRunner(config_manager)
    initialize_job = make_initialize_job(model_json)
    initial_weights = runner.run_job(initialize_job).results['weights']
    split_job = make_split_job(
                            model_json, 
                            mnist_filepath
                        )
    job_results = runner.run_job(split_job)
    session_filepath = job_results.results['session_filepath']
    datapoint_count = job_results.results['datapoint_count']
    train_job = make_train_job(
                    model_json, 
                    initial_weights, 
                    hyperparams, 
                    session_filepath,
                    datapoint_count
                )
    result = runner.run_job(train_job)
    assert result.status == 'successful'
    results = result.results
    new_weights = results['weights']
    omega = results['omega']
    train_stats = results['train_stats']
    assert result.job.job_type is JobTypes.JOB_TRAIN.name
    assert type(new_weights) == list
    assert type(new_weights[0]) == np.ndarray
    assert type(omega) == int or type(omega) == float
    assert type(train_stats) == dict

    # Clean up
    if session_filepath and os.path.isdir(session_filepath):
        session_filepaths.add(session_filepath)
        


def test_dmlrunner_validate_job_returns_stats( \
        config_manager, mnist_filepath, train_dmlresult_obj):
    model_json = make_model_json()
    hyperparams = make_hyperparams()
    runner = DMLRunner(config_manager)
    job_results = train_dmlresult_obj
    session_filepath = job_results.job.session_filepath
    datapoint_count = job_results.job.datapoint_count
    result = train_dmlresult_obj
    assert result.status == 'successful'
    results = result.results
    new_weights = results['weights']
    omega = results['omega']
    train_stats = results['train_stats']
    hyperparams['split'] = 1 - hyperparams['split']
    validate_job = make_validate_job(model_json, 
                    new_weights, 
                    hyperparams, 
                    session_filepath,
                    datapoint_count
                )
    result = runner.run_job(validate_job)
    assert result.status == 'successful'
    results = result.results
    val_stats = results['val_stats']
    assert result.job.job_type is JobTypes.JOB_VAL.name
    assert type(val_stats) == dict

    # Clean up
    if session_filepath and os.path.isdir(session_filepath):
        session_filepaths.add(session_filepath)

def test_dmlrunner_initialize_job_weights_can_be_serialized(config_manager, init_dmlresult_obj):
    initial_weights = init_dmlresult_obj.results['weights']
    same_weights = deserialize_weights(serialize_weights(initial_weights))
    assert all(np.allclose(arr1, arr2) for arr1,arr2 in zip(same_weights, initial_weights)) 
    session_filepath = init_dmlresult_obj.job.session_filepath
    # Clean up
    if session_filepath and os.path.isdir(session_filepath):
        session_filepaths.add(session_filepath)

def test_dmlrunner_averaging_weights(config_manager, train_dmlresult_obj):
    runner = DMLRunner(config_manager)
    avg_job = train_dmlresult_obj.job
    initial_weights = train_dmlresult_obj.results['weights']
    assert initial_weights
    avg_job.weights = initial_weights
    avg_job.new_weights = initial_weights
    avg_job.omega = train_dmlresult_obj.results['omega']
    avg_job.sigma_omega = avg_job.omega
    averaged_weights = runner._average(avg_job).results['weights']
    assert all(np.allclose(arr1, arr2) for arr1,arr2 in zip(averaged_weights, initial_weights))
    session_filepath = train_dmlresult_obj.job.session_filepath
    # Clean up
    if session_filepath and os.path.isdir(session_filepath):
        session_filepaths.add(session_filepath)

def test_cleanup():
    for session_filepath in session_filepaths:
        if os.path.isdir(session_filepath):
            shutil.rmtree(session_filepath)
    assert len((os.listdir('tests/artifacts/runner_scheduler/mnist/transformed/'))) == 0, \
        "Cleanup failed!"
