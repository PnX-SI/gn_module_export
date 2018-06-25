#!/usr/bin/python3
# TODO: PID.lockfile
# TODO: continue processing on export failure -> error handler

import os
import logging
import asyncio
import concurrent.futures
from datetime import datetime
from enum import IntEnum
# import hashlib
# import gzip
import psycopg2

dsn = "dbname='geonature2db' host='localhost' user='geonatuser' password='monpassachanger'"  # noqa E501
exports_path = '/home/pat/geonature/backend/static/exports/export_{lbl}_{id}.{ext}'  # noqa E501
num_workers = max(1, len(os.sched_getaffinity(0)) - 1)

queue = asyncio.Queue(maxsize=0)

logger = logging.getLogger(__name__)
console_logger = logging.StreamHandler()
logger.addHandler(console_logger)
logger.setLevel(logging.DEBUG)
asyncio_logger = logging.getLogger('asyncio')
asyncio_logger.setLevel(logging.DEBUG)
asyncio_console_logger = logging.StreamHandler()
asyncio_logger.addHandler(asyncio_console_logger)
loop = asyncio.get_event_loop()
loop.set_debug = True


class Format(IntEnum):
    CSV = 1
    JSON = 2
    RDF = 4


format_map_ext = {
    Format.CSV: 'csv',
    Format.JSON: 'json',
    Format.RDF: 'rdf'
}


format_map_transform = {
    Format.CSV: "COPY (SELECT * FROM v_export) TO STDOUT WITH CSV HEADER DELIMITER ',';",  # noqa E501
    Format.JSON: "COPY (SELECT json_agg(t) FROM (SELECT * FROM v_export) AS t) TO STDOUT;",  # noqa E501
    Format.RDF: ''
}


class Standard(IntEnum):
    NONE = 0
    SINP = 1
    DWC = 2
    ABCD = 4
    EML = 8


standard_map_label = {
    Standard.NONE: 'RAW',
    Standard.SINP: 'SINP',
    Standard.DWC: 'DarwinCore',
    Standard.ABCD: 'ABCD Schema',
    Standard.EML: 'EML'
}


def export(definition):
    print(definition)

    def ts(id):
        return (datetime.strptime(str(id), '%Y-%m-%d %H:%M:%S.%f')
                - datetime.utcfromtimestamp(0)).total_seconds()

    def prepare(transform, selection):
        return '\n'.join([
            'CREATE TEMPORARY VIEW v_export AS ({});'.format(selection),
            transform])

    with psycopg2.connect(dsn) as db:
        with db.cursor() as cursor:
            lbl, id, ext, selection = definition
            print(definition)
            ext = ext or Format.CSV
            transform = format_map_transform[ext]
            statement = prepare(transform, selection)
            # with gzip.open
            with open(exports_path.format(lbl=lbl, id=float(ts(id)), ext=format_map_ext[ext]), 'wb') as export_file:  # noqa E501
                # log_start
                row_count = -1
                cursor.execute(
                    'UPDATE gn_exports.t_exports_logs SET start=NOW() WHERE id=%s', (id,))  # noqa E501
                try:

                    cursor.copy_expert(statement, export_file)
                    row_count = cursor.rowcount
                    # log_end
                    cursor.execute('UPDATE gn_exports.t_exports_logs SET ("end", "log", "status")=(NOW(), %s, %s) WHERE id=%s',  # noqa E501
                                   (row_count, 0, id))
                except (psycopg2.InternalError, psycopg2.ProgrammingError, Exception) as e:  # noqa E501
                    db.rollback()
                    # log_fault
                    print(e)
                    cursor.execute('UPDATE gn_exports.t_exports_logs SET ("end", "log", "status")=(NULL, %s, -1) WHERE id=%s',  # noqa E501
                                   (str(e), id))
                finally:
                    db.commit()


async def process(executor, queue=queue, loop=loop):
        if queue.empty():
            return None
        task = await queue.get()
        return loop.run_in_executor(executor, task['func'], task['args'])


async def run(queue=queue, num_workers=num_workers):
    with psycopg2.connect(dsn) as db:
        with db.cursor() as cursor:
            cursor.execute(
                'SELECT e.label, l.id, l.format, e.selection FROM gn_exports.t_exports_logs l JOIN gn_exports.t_exports e ON e.id = l.id_export WHERE "start" IS NULL AND status=-2 ORDER BY id ASC;')  # noqa E501
            for record in cursor.fetchall():
                print(record)
                queue.put_nowait({'func': export, 'args': (record)})

    with concurrent.futures.ProcessPoolExecutor() as executor:
        while not queue.empty():
            tasks = [process(executor, queue) for i in range(num_workers)]
            for future in asyncio.as_completed(tasks):
                result = await future
                logger.debug('%s', result)


if __name__ == '__main__':

    loop.run_until_complete(run())
