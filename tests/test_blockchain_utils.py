import tests.context
import ipfsapi
import pytest

from core.blockchain.blockchain_utils import getter, setter
from core.configuration import ConfigurationManager

test_nonexistent_key = 'nonexistence'
test_single_key = 'singleton'
test_multiple_key = 'multiplicity'
test_value = 'World!'

@pytest.fixture
def config():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/blockchain/configuration.ini'
    )
    return config_manager.get_config()

@pytest.fixture
def ipfs_client(config):
    return ipfsapi.connect(config.get('BLOCKCHAIN', 'host'), 
                            config.getint('BLOCKCHAIN', 'ipfs_port'))

def test_blockchain_utils_getter_nonexistent_key(config, ipfs_client):
    get_val = getter(
        client=ipfs_client,
        key=test_nonexistent_key,
        local_state=[],
        port=config.getint('BLOCKCHAIN', 'http_port'),
        timeout=config.getint('BLOCKCHAIN', 'timeout')
    )
    assert get_val == []

def test_blockchain_utils_setter_simple(config, ipfs_client):
    get_val_before = getter(
        client=ipfs_client,
        key=test_single_key,
        local_state=[],
        port=config.getint('BLOCKCHAIN', 'http_port'),
        timeout=config.getint('BLOCKCHAIN', 'timeout')
    )
    tx_receipt = setter(client=ipfs_client,
        key=test_single_key,
        port=config.getint('BLOCKCHAIN', 'http_port'),
        value=test_value,
    )
    assert tx_receipt
    get_val_after = getter(
        client=ipfs_client,
        key=test_single_key,
        local_state=[],
        port=config.getint('BLOCKCHAIN', 'http_port'),
        timeout=config.getint('BLOCKCHAIN', 'timeout')
    )
    assert get_val_after == get_val_before + [test_value]

def test_blockchain_utils_setter_multiple_values(config, ipfs_client):
    get_val_before = getter(
        client=ipfs_client,
        key=test_multiple_key,
        local_state=[],
        port=config.getint('BLOCKCHAIN', 'http_port'),
        timeout=config.getint('BLOCKCHAIN', 'timeout')
    )
    tx_receipt = setter(client=ipfs_client,
        key=test_multiple_key,
        port=config.getint('BLOCKCHAIN', 'http_port'),
        value=test_value,
    )
    assert tx_receipt
    tx_receipt = setter(client=ipfs_client,
        key=test_multiple_key,
        port=config.getint('BLOCKCHAIN', 'http_port'),
        value=test_value,
    )
    assert tx_receipt
    get_val_after = getter(
        client=ipfs_client,
        key=test_multiple_key,
        local_state=[],
        port=config.getint('BLOCKCHAIN', 'http_port'),
        timeout=config.getint('BLOCKCHAIN', 'timeout')
    )
    assert get_val_after == get_val_before + [test_value, test_value]
