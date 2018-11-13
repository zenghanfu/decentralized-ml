import logging
import random
import uuid
import time
import os
<<<<<<< HEAD
import ipfsapi
=======
import pandas as pd
>>>>>>> 435b3085cfd0276de8faf2110b506e9e27a2a9a6
import numpy as np

from core.configuration import ConfigurationManager
from custom.keras import model_from_serialized, get_optimizer
from data.iterators import count_datapoints
from data.iterators import create_random_train_dataset_iterator
from data.iterators import create_random_test_dataset_iterator
from core.utils.keras import train_keras_model, validate_keras_model

from core.utils.keras import serialize_weights, deserialize_weights
from core.utils.dmlresult import DMLResult
from core.utils.dmljob import serialize_job
from core.utils.enums import JobTypes, callback_handler_no_default
from core.blockchain.blockchain_utils import setter


logging.basicConfig(level=logging.DEBUG,
                    format='[Runner] %(asctime)s %(levelname)s %(message)s')

class DMLRunner(object):
    """
    DML Runner

    This class manages the training and validation of a DML job. It trains or
    validate a specified machine learning model on a local dataset. An instance
    of this class has a one-to-one relationship with a DML job, and gets freed up
    for another DML job after executing the job. Once free, it can schedule a new
    DML job from any DML session and repeat the cycle.

    Note that this class does not schedule how jobs received should be executed
    nor listens to incoming jobs. This class only executes the jobs.

    """

    def __init__(self, config_manager):
        """
        Sets up the unique identifier of the DML Runner and the local dataset path.
        """
        config = config_manager.get_config()
        self.iden = str(uuid.uuid4())[:8]
        
        self.config = dict(config.items("RUNNER"))
<<<<<<< HEAD
        self.blockchain_config = config
        self.data_count = count_datapoints(self.dataset_path)
=======
>>>>>>> 435b3085cfd0276de8faf2110b506e9e27a2a9a6
        self.JOB_CALLBACKS = {
            JobTypes.JOB_TRAIN.name: self._train,
            JobTypes.JOB_INIT.name: self._initialize,
            JobTypes.JOB_VAL.name: self._validate,
            JobTypes.JOB_TRANSFORM_SPLIT.name: self._transform_and_split_data,
            JobTypes.JOB_AVG.name: self._average,
<<<<<<< HEAD
            JobTypes.JOB_COMM.name: self._communicate,
=======
            JobTypes.JOB_COMM.name: self._communicate
>>>>>>> 435b3085cfd0276de8faf2110b506e9e27a2a9a6
        }

    def run_job(self, job):
        """
        Identifies a DMLJob type and executes it.

        If the runner is already executing a job, it silently does nothing.
        """
        assert job.job_type.upper() in self.JOB_CALLBACKS, \
            'DMLJob type ({0}) is not valid'.format(job.job_type)
        logging.info("Running job (type: {0})...".format(job.job_type))
        callback = callback_handler_no_default(
            job.job_type,
            self.JOB_CALLBACKS,
        )
        results = callback(job)
        # try:
        #     results = callback(job)
        # except Exception as e:
        #     logging.error("RunnerError: " + str(e))
        #     results = DMLResult(
        #         status='failed',
        #         job=job,
        #         error_message=str(e),
        #         results={},
        #     )
        self.current_job = None
        logging.info("Finished running job! (type: {0})".format(job.job_type))
        return results

    def _set_up(self, job):
        assert job.session_filepath, \
            "Transformed training and test sets not created yet!"
        train_path = os.path.join(
                                job.session_filepath, 
                                'train.csv'
                            )
        test_path = os.path.join(
                                job.session_filepath, 
                                'test.csv'
                            )
        return train_path, test_path

    def _train(self, job):
        """
        Trains the specified machine learning model on all the local data,
        starting from the initial model state specified, until a stopping
        condition is met, and using the hyper-parameters specified.

        Returns a DMLResult with the updated model weights, the weighting factor
        omega, and stats about the training job.

        NOTE: Uses the same hyperparameters and labeler for training and
        validating during 'avg_type' of type 'val_acc'.

        NOTE2: Assumes 'job.weights' are the actual weights and not a path.
        """
        
        train_dataset_path, test_dataset_path = self._set_up(job)
        data_count = job.datapoint_count

        # Get the right dataset iterator based on the averaging type.
        avg_type = job.hyperparams['averaging_type']
        batch_size = job.hyperparams['batch_size']
        split = job.hyperparams['split']
        assert avg_type in ['data_size', 'val_acc'], \
            "Averaging type '{0}' is not supported.".format(avg_type)
        logging.info("Training model...")
        if avg_type == 'data_size':
            dataset_iterator = create_random_train_dataset_iterator(
                train_dataset_path,
                batch_size=batch_size,
                labeler=job.label_column_name,
            )
        elif avg_type == 'val_acc':
            dataset_iterator = create_random_train_dataset_iterator(
                train_dataset_path,
                batch_size=batch_size,
                labeler=job.label_column_name,
            )
            test_dataset_iterator = create_random_test_dataset_iterator(
                test_dataset_path,
                batch_size=batch_size,
                labeler=job.label_column_name,
            )

        # Train the model the right way based on the model type.
        assert job.framework_type in ['keras'], \
            "Model type '{0}' is not supported.".format(job.framework_type)

        if job.framework_type == 'keras':
            new_weights_path, train_stats = train_keras_model(
                job.serialized_model,
                job.weights,
                dataset_iterator,
                data_count*split,
                job.hyperparams,
                self.config
            )

        # Get the right omega based on the averaging type.
        if avg_type == 'data_size':
            omega = data_count * split
        elif avg_type == 'val_acc':
            val_stats = self._validate(
                job,
                custom_iterator=test_dataset_iterator
            ).results['val_stats']
            omega = val_stats['val_metric']['acc']
            train_stats.update(val_stats)

        # Return the results.
        # return new_weights_path, omega, train_stats
        results = DMLResult(
            status='successful',
            job=job,
            results={
                'weights': new_weights_path,
                'omega': omega,
                'train_stats': train_stats,
            },
            error_message="",
        )
        return results

    def _validate(self, job, custom_iterator=None):
        """
        Validates on all the local data the specified machine learning model at
        the state specified.

        Returns a DMLResult with the metrics returned by the model.

        NOTE: Assumes 'weights' are the actual weights and not a path.
        """
        logging.info("Validating model...")
        
        train_dataset_path, test_dataset_path = self._set_up(job)
        data_count = job.datapoint_count
        # Choose the dataset to validate on.
        batch_size = job.hyperparams['batch_size']
        split = job.hyperparams['split']
        if custom_iterator is None:
            dataset_iterator = create_random_test_dataset_iterator(
                test_dataset_path,
                batch_size=batch_size,
                labeler=job.label_column_name,
            )
        else:
            dataset_iterator = custom_iterator

        # Validate the model the right way based on the model type.
        assert job.framework_type in ['keras'], \
            "Model type '{0}' is not supported.".format(job.framework_type)
        if job.framework_type == 'keras':
            val_stats = validate_keras_model(
                job.serialized_model,
                job.weights,
                dataset_iterator,
                data_count*(1-split)
            )

        # Return the validation stats.
        results = DMLResult(
            status='successful',
            job=job,
            results={
                'val_stats': val_stats,
            },
            error_message="",
        )
        return results

    def _initialize(self, job):
        """
        Initializes and returns a DMLResult with the model
        weights as specified in the model.
        """
        assert job.framework_type in ['keras'], \
            "Model type '{0}' is not supported.".format(job.framework_type)
        logging.info("Initializing model...")
        if job.framework_type == 'keras':
            model = model_from_serialized(job.serialized_model)
            #model.summary()
            initial_weights = model.get_weights()
        results = DMLResult(
                    status='successful',
                    job=job,
                    results={
                        'weights': initial_weights,
                    },
                    error_message="",
                )
        return results

    def _communicate(self, job):
        """
        Communicates a message to the blockchain.
        """
        tx_receipt = setter(
            client = ipfsapi.connect(self.blockchain_config.get('BLOCKCHAIN', 'host'), 
                        self.blockchain_config.getint('BLOCKCHAIN', 'ipfs_port')),
            key = job.key,
            port = self.blockchain_config.getint('BLOCKCHAIN', 'http_port'),
            value = serialize_job(job),
        )
        results = DMLResult(
            status='successful',
            job=job,
            results={
                'receipt': tx_receipt,
            },
            error_message="",
        )
        return results

    def _transform_and_split_data(self, job):
        """
        Takes in a job, which should have the raw filepath assigned.

        1. In each folder, aggregate all data.
        2. Create session folder in transformed folder, along with data folders
           in session folder.
        3. Transform data in each raw data folder.
        4. Shuffle each transformed data and perform train-test split on each. 
        5. Put each training and test set in corresponding data folders in 
           session folder.
        6. Update session filepath in job.
        """

        # 1. Extracts all of the raw data from raw data filepath
        assert job.raw_filepath, \
            "Raw data filepath has not been set!"
        assert job.transform_function, \
            "Transform function has not been set!"
        files = os.listdir(job.raw_filepath)
        files = list(filter(lambda x: x.endswith('.csv'), files))
        assert len(files) == 1, \
            "Only supporting one file per dataset folder!"
        data_filepath = os.path.join(
                    job.raw_filepath,
                    files[0]
                )
        raw_data = pd.read_csv(data_filepath)

        # 2. Create transformed folder, if it doesn't exist.
        transformed_filepath = os.path.join(job.raw_filepath, "transformed")
        if not os.path.isdir(transformed_filepath):
            os.makedirs(transformed_filepath)

        # 3. Create session folder using timestamp and random characters.
        new_name = str(uuid.uuid4())
        session_filepath = os.path.join(transformed_filepath, new_name)
        os.makedirs(session_filepath)

        # 4. Retrieve transform function and train-test split from job.
        transform_function = job.transform_function
        split = job.hyperparams['split']

        # 5. Shuffle raw data, then split into train and test set.
        transformed_data = transform_function(raw_data)
        transformed_data = transformed_data.sample(frac=1)
        split_index = int(len(transformed_data)*split)
        train = transformed_data.iloc[:split_index] 
        test = transformed_data.iloc[split_index:]

        # 6. Create train.csv and test.csv in data folder.
        train.to_csv(
            os.path.join(session_filepath, 'train.csv'),
            index=False
        )

        test.to_csv(
            os.path.join(session_filepath, 'test.csv'),
            index=False
        )

        # 7. Get datapoint count to be used in future jobs
        datapoint_count = count_datapoints(session_filepath)

        # 8. Return job with assigned session folder filepath and
        #    datapoint count.
        results = DMLResult(
                    status='successful',
                    job=job,
                    results = {
                        'session_filepath': session_filepath,
                        'datapoint_count': datapoint_count
                    },
                    error_message=""
                )
        return results 
      
    def _average(self, job):
        """
        Average the weights in the job weighted by their omegas.
        """
        deserialized_new_weights = deserialize_weights(job.new_weights)
        averaged_weights = self._weighted_running_avg(job.weights, deserialized_new_weights, job.sigma_omega, job.omega)
        result = DMLResult(
            status='successful',
            job=job,
            results={
                'weights': averaged_weights,
            },
            error_message="",
        )
        return result
    
    def _weighted_running_avg(self, sigma_x_i_div_w_i, x_n, sigma_w_i, w_n):
        """
        Computes a weighting running average.
        w_n is the weight of datapoint n.
        x_n is a datapoint.
        Sigma_x_i_div_w_i is the current weighted average.
        Sigma_w_i is the sum of weights currently.
        """
        sigma_x_i = np.multiply(sigma_w_i, sigma_x_i_div_w_i)
        cma_n_plus_one = np.divide(np.add(x_n, sigma_x_i), np.add(w_n,sigma_w_i))
        return cma_n_plus_one
