import ipfsapi
import json
from filelock import FileLock
import base58

from keras.models import load_model, model_from_json
import os

from pathlib import Path
import keras

#api = ipfsapi.connect('127.0.0.1', 5001)
CONFIG = None

# print('starting to load model from IPFS')
# catted = api.cat('QmVm4yB2jxPwXXVXM6n86TuwA4jCQ7EfNPjguFrhoCbPiJ')
# print('loaded in model from IPFS as bytes')
# model = model.load_weights(catted)
def content_hash(data):
    return api.add(data)

def keras2ipfs(model):
    return api.add_bytes(serialize_keras_model(model))

def ipfs2keras(model, model_addr):
    return deserialize_keras_model(model, api.cat(model_addr))

def ipfs2bytes(ipfs_hash):
    bytez = api.cat(ipfs_hash)
    # print("Type of data is {}".format(isinstance(bytez, bytes)))
    return bytez

def serialize_keras_model(model):
    lock = FileLock('temp_model.h5.lock')
    with lock:
        model.save('temp_model.h5')
        with open('temp_model.h5', 'rb') as f:
            model_bin = f.read()
            f.close()
        return model_bin


def deserialize_keras_model(model, model_bin):
    lock = FileLock('temp_model2.h5.lock')
    with lock:
        with open('temp_model2.h5', 'wb') as g:
            g.write(model_bin)
            g.close()
        model = model.load_weights('temp_model2.h5')
        return model
def json2bytes32(json):
    content_hash = api.add_json(json)
    return ipfs2bytes32(content_hash)
def bytes322json(bytes32):
    ipfs_hash = bytes322ipfs(bytes32)
    return api.get_json(ipfs_hash)
def bytes322ipfs(bytes32):
    ipfs_hash = base58.b58encode(b'\x12 ' + bytes32)
    return ipfs_hash
def ipfs2bytes32(ipfs_hash):
    bytes_array = base58.b58decode(ipfs_hash)
    return bytes_array[2:]
def weights2bytes32(weights):
    addr = api.add_bytes(weights)
    return ipfs2bytes32(addr)
def bytes322weights(model, bytes32):
    addr = bytes322ipfs(bytes32)
    return ipfs2keras(model, addr)
def bytes322bytes(bytes32):
    addr = bytes322ipfs(bytes32)
    bytez = ipfs2bytes(addr)
    # print("Type of data is {}".format(isinstance(bytez, bytes)))
    return bytez
# def bytes322numpy(bytes32)
#     bytez = bytes322bytes(byt)
# def send_model():
#     dict_of_stuff = keras2ipfs()
#     return dict_of_stuff
# if __name__ == '__main__':
    # print(ipfs2base32('QmZf6NVYgxTMA6996744sbakRN9Ks8xE6HWAEb3x6JN5i9'))
    # print(base322ipfs(ipfs2base32('QmZf6NVYgxTMA6996744sbakRN9Ks8xE6HWAEb3x6JN5i9')))
