import base64
import hashlib
import io
import json
import os
import urllib
from io import BytesIO
from random import randrange

import numpy
import pandas
import requests
from PIL import Image
from textblob import TextBlob


def convert(o):
    if isinstance(o, numpy.int64) or isinstance(o, numpy.int32):
        return int(o)
    if isinstance(o, TextBlob):
        return str(o)
    raise TypeError

def dump_json(file_path, data, indent=4, sort_keys=True):
    os.makedirs(os.path.join('\\'.join(file_path.split('\\')[:-1])), exist_ok=True)
    with open(os.path.join(file_path), 'w+') as f:
        json.dump(data, f, indent=indent, sort_keys=sort_keys, default=convert)
        f.close()

def get_json(file_path):
    with open(os.path.join(file_path), encoding="utf8") as f:
        response = json.load(f)
        f.close()
        return response

def get_xlsx(file_path, column_by=None):
    try:
        xlsx_as_pandas = pandas.read_excel(file_path)
    except:
        xlsx_as_pandas = pandas.read_csv(file_path)
    if column_by is not None:
        xlsx_as_pandas = xlsx_as_pandas.set_index(column_by)
    xlsx_as_json_str = xlsx_as_pandas.to_json()
    xlsx_as_json = json.loads(xlsx_as_json_str)
    return xlsx_as_json

def get_random_number(num_of_digits):
    if num_of_digits >= 1:
        return randrange(1 * pow(10, (num_of_digits - 1)), 1 * pow(10, num_of_digits))
    return None


def get_base64_format(img_source):
    try:
        return img_source[img_source.index('base64,') + 7:], img_source[img_source.index('data:image/') + len('data:image/'): img_source.index(';')]
    except:
        return None, None


def get_str_hash(string):
    return str(int(hashlib.sha256(string.encode('utf-8')).hexdigest(), 16))


def get_cv2_image_by_url(url):
    pil_image = open_image_by_url(url, 'PIL')
    open_cv_image = numpy.array(pil_image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image


def convert_to_jpeg(im):
    with BytesIO() as f:
        im.save(f, format='JPEG')
        return f.getvalue()


def open_image_by_string(url):
    try:
        return Image.open(io.BytesIO(base64.decodebytes(bytes(url, "utf-8"))))
    except Exception as e:
        print(f'[OPEN_IMAGE_BY_STRING]: ${url} image is not base64')
        raise Exception(f'[OPEN_IMAGE_BY_STRING]: ${url} mage is not base64')


open_image_cache = dict()


def open_image_by_url(url, format='Bytes'):
    global open_image_cache

    if open_image_cache.get(url) is not None:
        opened_image = open_image_cache.get(url)
    else:
        try:
            opened_image = Image.open(BytesIO(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=5).read())).convert('RGB')
        except Exception as e:
            try:
                opened_image = Image.open(BytesIO(requests.get(url).content)).convert('RGB')
            except:
                try:
                    opened_image = open_image_by_string(url).convert('RGB')
                except:
                    print(f'[OPEN_IMAGE_BY_URL]: ${url} not opened')
                    return None
        open_image_cache.update({url: opened_image})

    if format == 'Bytes':
        return convert_to_jpeg(opened_image)
    elif format == 'PIL':
        return opened_image
    else:
        raise Exception('[OPEN_IMAGE_BY_URL]: ERR unknown format')


def get_image_size(img_path):
    im = open_image_by_url(img_path, 'PIL')
    width, height = im.size
    return width * height


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))
