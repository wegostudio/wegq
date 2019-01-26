import requests
from .ierror import APIValueError


__all__ = ['get', 'post']


def get(url):
    data = requests.get(url).json()
    try:
        if data['errcode'] != 0:
            raise APIValueError(data)
    except KeyError:
        raise APIValueError(data)
    return data


def post(url, data):
    data = requests.post(url, json=data).json()
    try:
        if data['errcode'] != 0:
            raise APIValueError(data)
    except KeyError:
        raise APIValueError(data)
    return data