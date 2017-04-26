from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

from firebird import CASSANDRA_CONTACT_POINTS
from firebird import CASSANDRA_USER
from firebird import CASSANDRA_PASS
from firebird import CASSANDRA_KEYSPACE

auth_provider = PlainTextAuthProvider(username=CASSANDRA_USER, password=CASSANDRA_PASS)
cluster = Cluster(CASSANDRA_CONTACT_POINTS.split(','), auth_provider=auth_provider)

RESULT_INPUT = {'tile_x': '', 'tile_y': '', 'x': '', 'y': '', 'algorithm': '', 'result': '', 'result_ok': '',
                'result_produced': '', 'inputs_md5': '', 'result_md5': ''}

INSERT_CQL = "INSERT INTO {}.results (y, tile_x, tile_y, algorithm, x, result_ok, inputs_md5, result, " \
             "result_produced, result_md5) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)".format(CASSANDRA_KEYSPACE)


def execute(statement, args):
    try:
        with cluster.connect() as session:
            for _ag in args:
                prepared = session.prepare(statement)
                session.execute(prepared, _ag)
    except Exception as e:
        raise e


