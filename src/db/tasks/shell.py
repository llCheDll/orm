import os
import subprocess
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
import config

from invoke import task


def _escape_pgpass(txt):
    """
    Escape a fragment of a PostgreSQL .pgpass file.
    """
    return txt.replace('\\', '\\\\').replace(':', '\\:')


@task
def shell(ctx):
    """
    command-line PostgreSQL client
    """
    executable = 'psql'
    conn_obj = urlsplit(config.DATABASE_DSN)

    host = conn_obj.hostname
    port = conn_obj.port if conn_obj.port is not None else ''
    name = conn_obj.path[1:]
    user = conn_obj.username
    passwd = conn_obj.password

    args = [executable]
    if user:
        args += ['-U', user]
    if host:
        args += ['-h', host]
    if port:
        args += ['-p', str(port)]
    args += [name]

    temp_pgpass = None
    try:
        if passwd:
            # Create temporary .pgpass file.
            temp_pgpass = NamedTemporaryFile(mode='w+')
            try:
                print(
                    _escape_pgpass(host) or '*',
                    str(port) or '*',
                    _escape_pgpass(name) or '*',
                    _escape_pgpass(user) or '*',
                    _escape_pgpass(passwd),
                    file=temp_pgpass,
                    sep=':',
                    flush=True,
                )
                os.environ['PGPASSFILE'] = temp_pgpass.name
            except UnicodeEncodeError:
                # If the current locale can't encode the data, we let
                # the user input the password manually.
                pass

        subprocess.call(args)
    finally:
        if temp_pgpass:
            temp_pgpass.close()
            if 'PGPASSFILE' in os.environ:  # unit tests need cleanup
                del os.environ['PGPASSFILE']
