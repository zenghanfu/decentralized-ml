import shutil
import logging
import datetime
import string
import random
import os

import numpy as np
import pandas as pd

import core.utils.context
from core.configuration import ConfigurationManager


logging.basicConfig(level=logging.INFO,
                format='[DatasetManager] %(asctime)s %(levelname)s %(message)s')

class DatasetManager():
    """
    Dataset Manager


    IMPORTANT: ALL FILEPATHS ARE ABSOLUTE FILEPATHS.
    If you have a relative filepath, simply:

        import os
        absolute_path = os.path.abspath(relative_path)

    to get the absolute filepath.


    This class takes in an filepath to raw data upon initialization.
    Some functionalities include:

        1. Taking in a transform function, transforming the data, and putting
        this transformed data in a new directory within the same directory as
        the raw data

        2. Returning the raw data and transformed data (if it exists)

        3. Resetting data in transformed folder to the raw data. (NOT IN USE
        UNTIL WE FIGURE OUT SESSIONS)

    Each instance corresponds to a set of raw data and its corresponding
    transformed data (if it exists). After transformation, the filepath to raw
    data would look something like:

    main/
        dataset1/
            dataset1.csv
            md_dataset1.csv
        dataset2/
            dataset2.csv
            md_dataset2.csv
        transformed/
            dataset1/
                06/10/16sgf.csv
            dataset2/
                06/10/16mlf.csv

    The Dataset Manager will be initialized in the Bootstrapper. At the start
    of each session, transform_data will be called with the identity transform
    (essentially copying over the raw data) as a default transform before
    training.

    TODO: Will each session have its own instance of Dataset Manager? Or will 
    Dataset Manager maps session ids to transformed datasets?
    """

    def __init__(self, config_manager):
        """
        Take in an filepath to the raw data, no filepath to transformed exists
        yet.

        For now, throw an exception if a valid dataset path is not provided.

        TODO: In the event of a invalid dataset path, log a useful message 
        for the user and don't terminate the service
        """
        config = config_manager.get_config()
        raw_filepath = config['GENERAL']['dataset_path']
        assert os.path.isdir(raw_filepath), "The dataset filepath provided is not valid."
        self.rfp = raw_filepath
        self.tfp = None

    def transform_data(self, transform_function):
        """
        Taking in a transform function, transforming the data, and putting this
        transformed data in a new directory (called 'transformed') in the same
        directory as the raw data. File names consist of a timestamp with the
        addition of a few random characters.
        """
        def random_string(length):
            return ''.join(
                random.choice(string.ascii_letters) for m in range(length)
            )

        #1. Extracts all of the raw data from raw data filepath
        raw_data = self._get_raw_data()
        self.tfp = os.path.join(self.rfp, "transformed")

        #2. Tranforms data using provided transform function and puts data in
        #'transformed'. Names in this folder are generated using a timestamp
        #joined with some random characters.
        for name,data in raw_data.items():
            new_folder = os.path.join(self.tfp, name)
            if not os.path.exists(new_folder):
                os.makedirs(new_folder)
            transformed_data = transform_function(data)
            timestamp = str(datetime.datetime.now())
            r_string = random_string(5)
            new_name = timestamp + r_string
            transformed_data.to_csv(
                os.path.join(new_folder, new_name + '.csv'),
                index=False
            )

    def _get_raw_data(self):
        """
        Extracts all raw data from raw data filepath. Assumes filepath contains
        csv files. Returns where each (key, value) represents a csv file. Each
        key is the filename of the csv (i.e. key.csv) and each value is a
        DataFrame of the actual data.
        """
        raw_dict = {}
        folders = []
        for file in os.listdir(self.rfp):
            if os.path.isdir(os.path.join(os.path.abspath(self.rfp), file)):
                folders.append(file)
        for folder in folders:
            folder_dict = {}
            folder_path = os.path.join(os.path.abspath(self.rfp), folder)
            files = os.listdir(folder_path)
            for file in files:
                if not file.endswith(".csv"): continue
                if file[:2] != 'md':
                    file_path = os.path.join(folder_path, file)
                    dataset = pd.read_csv(file_path)
                    raw_dict[file[:-4]] = dataset
        return raw_dict

    def get_transformed_data(self):
        """
        Extracts all transformed data from transform data filepath.

        Assumes filepath contains csvfiles. Returns where
        each (key, value) represents a csv file. Each key is the filename of the
        csv (i.e. key.csv) and each value is a DataFrame of the actual data.
        """
        transform_dict = {}
        for folder in os.listdir(self.tfp):
            folder_path = os.path.join(self.tfp, folder)
            for file in os.listdir(folder_path):
                if file[-4:] == '.csv':
                    data = pd.read_csv(os.path.join(folder_path, file))
                    transform_dict[file] = data
        return transform_dict

    def clean_up(self):
        """
        Resets class as though transformed data never existed.

        If transform data filepath exists, then replace files in directory 
        with raw data files.
        """
        if self.tfp:
            shutil.rmtree(self.tfp)
        assert not os.path.isdir(self.tfp)
        self.tfp = None

    def check_key_length(key):
        """
        Keys for datasets can only be at most 30 characters long.
        """
        if len(key) > 30:
            raise InvalidKeyError(key)

    def post_dataset_with_md(self, name):
        """
        Post samples of datasets on blockchain along with provided metadata
        under the provided name as the key

        IMPORTANT: NOT FINISHED DEBUGGING, DO NOT USE
        """
        filepath = self.rfp
        self.check_key_length(name)
        value = {}
        folders = []
        for file in os.listdir(filepath):
            if os.path.isdir(os.path.join(os.path.abspath(filepath), file)):
                folders.append(file)
        for folder in folders:
            folder_dict = {}
            folder_path = os.path.join(os.path.abspath(filepath), folder)
            files = os.listdir(folder_path)
            for file in files:
                if file[:2] == 'md':
                    file_path = os.path.join(folder_path, file)
                    metadata = pd.read_csv(file_path)
                    folder_dict['md'] = metadata.to_json()
                else:
                    file_path = os.path.join(folder_path, file)
                    dataset = pd.read_csv(file_path)
                    sample = dataset.sample(frac=0.1)
                    folder_dict['ds'] = sample.to_json()
            if 'md' not in folder_dict:
                raise NoMetadataFoundError(folder)
            value[folder] = folder_dict
        self.client.setter(name, value)

    def post_dataset(self, name):
        """
        Post samples of datasets on blockchain with automatically generated
        metadata under provided name as the key

        IMPORTANT: NOT FINISHED DEBUGGING, DO NOT USE
        """
        filepath = self.rfp
        self.check_key_length(name)
        value = {}
        folders = []
        for file in os.listdir(filepath):
            if os.path.isdir(os.path.join(os.path.abspath(filepath), file)):
                folders.append(file)
        for folder in folders:
            folder_dict = {}
            folder_path = os.path.join(os.path.abspath(filepath), folder)
            file = list(os.listdir(folder_path))[0]
            file_path = os.path.join(folder_path, file)
            dataset = pd.read_csv(file_path)
            md = pd.DataFrame(dataset.describe())
            sample = dataset.sample(frac=0.1)
            folder_dict['ds'] = sample.to_json()
            folder_dict['md'] = md.to_json()
            value[folder] = folder_dict
        self.client.setter(name, value)
