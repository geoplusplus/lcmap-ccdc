from pyspark import SparkConf
from pyspark import SparkContext
from pyspark import sql
import datetime
import logging
import os
import socket
import sys

HOST = socket.gethostbyname(socket.getfqdn())

AARDVARK = os.getenv('AARDVARK', 'http://localhost:5678')
AARDVARK_SPECS = os.getenv('AARDVARK_SPECS', '/v1/landsat/chip-specs')
AARDVARK_CHIPS = os.getenv('AARDVARK_CHIPS', '/v1/landsat/chips')
CHIPS_URL = ''.join([AARDVARK, AARDVARK_CHIPS])
SPECS_URL = ''.join([AARDVARK, AARDVARK_SPECS])

CASSANDRA_CONTACT_POINTS = os.getenv('CASSANDRA_CONTACT_POINTS', '0.0.0.0')
CASSANDRA_USER = os.getenv('CASSANDRA_USER')
CASSANDRA_PASS = os.getenv('CASSANDRA_PASS')
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'lcmap_changes_local')
CASSANDRA_RESULTS_TABLE = os.getenv('CASSANDRA_RESULTS_TABLE', 'results')
CASSANDRA_JOBCONF_TABLE = os.getenv('CASSANDRA_JOBCONF_TABLE', 'jobconf')

INITIAL_PARTITION_COUNT = os.getenv('INITIAL_PARTITION_COUNT')
PRODUCT_PARTITION_COUNT = os.getenv('PRODUCT_PARTITION_COUNT')
STORAGE_PARTITION_COUNT = os.getenv('STORAGE_PARTITION_COUNT')

DRIVER_HOST = os.getenv('DRIVER_HOST', HOST)

LOG_LEVEL = os.getenv('FIREBIRD_LOG_LEVEL', 'WARN')

SPARK_MASTER = os.getenv('SPARK_MASTER', 'spark://localhost:7077')
SPARK_EXECUTOR_IMAGE = os.getenv('SPARK_EXECUTOR_IMAGE')
SPARK_EXECUTOR_CORES = os.getenv('SPARK_EXECUTOR_CORES', 1)
SPARK_EXECUTOR_FORCE_PULL = os.getenv('SPARK_EXECUTOR_FORCE_PULL', 'false')

QA_BIT_PACKED = os.getenv('CCD_QA_BITPACKED', 'True')

# log format needs to be
# 2017-06-29 13:09:04,109 DEBUG lcmap.aardvark.chip-spec - initializing GDAL
# 2017-06-29 13:09:04,138 DEBUG lcmap.aardvark.chip - initializing GDAL
# 2017-06-29 13:09:04,146 INFO  lcmap.aardvark.server - start server
#
# Normal python logging setup doesnt work even though the log level can be
# passed into the SparkContext) for executors because it's actually the jvm
# that's handling it.
# In order to configure logging, need to manipulate the log4j.properties
# instead of Python logging configs.

#logging.basicConfig(
#    level=LOG_LEVEL,
#    format='%(asctime)s %(levelname)s %(module)s.%(funcName)-20s - %(message)s',
##    stream=sys.stdout)

logger = logging.getLogger('firebird')


def trace(msg):
    logger.trace(msg)

def debug(msg):
    logger.debug(msg)

def info(msg):
    logger.info(msg)

def warning(msg):
    logger.warning(msg)

def error(msg):
    logger.error(msg)

def fatal(msg):
    logger.fatal(msg)


def sparkcontext():
    try:
        ts = datetime.datetime.now().isoformat()
        conf = (SparkConf().setAppName("lcmap-firebird-{}".format(ts))
                .setMaster(SPARK_MASTER)
                .set("spark.mesos.executor.docker.image", SPARK_EXECUTOR_IMAGE)
                .set("spark.executor.cores", SPARK_EXECUTOR_CORES)
                .set("spark.mesos.executor.docker.forcePullImage",
                     SPARK_EXECUTOR_FORCE_PULL))
        return SparkContext(conf=conf)
    except Exception as e:
        logger.info("Exception creating SparkContext: {}".format(e))
        raise e


def ccd_params():
    params = {}
    if QA_BIT_PACKED is not 'True':
        params = {'QA_BITPACKED': False,
                  'QA_FILL': 255,
                  'QA_CLEAR': 0,
                  'QA_WATER': 1,
                  'QA_SHADOW': 2,
                  'QA_SNOW': 3,
                  'QA_CLOUD': 4}
    return params


def chip_spec_queries(url):
    """A map of pyccd spectra to chip-spec queries
    :param url: full url (http://host:port/context) for chip-spec endpoint
    :return: map of spectra to chip spec queries
    :example:
    >>> chip_spec_queries('http://host/v1/landsat/chip-specs')
    {'reds':     'http://host/v1/landsat/chip-specs?q=tags:red AND sr',
     'greens':   'http://host/v1/landsat/chip-specs?q=tags:green AND sr'
     'blues':    'http://host/v1/landsat/chip-specs?q=tags:blue AND sr'
     'nirs':     'http://host/v1/landsat/chip-specs?q=tags:nir AND sr'
     'swir1s':   'http://host/v1/landsat/chip-specs?q=tags:swir1 AND sr'
     'swir2s':   'http://host/v1/landsat/chip-specs?q=tags:swir2 AND sr'
     'thermals': 'http://host/v1/landsat/chip-specs?q=tags:thermal AND ta'
     'quality':  'http://host/v1/landsat/chip-specs?q=tags:pixelqa'}
    """
    return {'reds':     ''.join([url, '?q=tags:red AND sr']),
            'greens':   ''.join([url, '?q=tags:green AND sr']),
            'blues':    ''.join([url, '?q=tags:blue AND sr']),
            'nirs':     ''.join([url, '?q=tags:nir AND sr']),
            'swir1s':   ''.join([url, '?q=tags:swir1 AND sr']),
            'swir2s':   ''.join([url, '?q=tags:swir2 AND sr']),
            'thermals': ''.join([url, '?q=tags:bt AND thermal AND NOT tirs2']),
            'quality':  ''.join([url, '?q=tags:pixelqa'])}
