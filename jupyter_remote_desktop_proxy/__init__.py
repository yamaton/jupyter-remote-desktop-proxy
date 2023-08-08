import os
import pathlib
import shlex
import tempfile
from shutil import which

HERE = pathlib.Path(__file__).parent.absolute()

def setup_bandage():
    return gen_setup('bandage')

def setup_igv():
    return gen_setup('igv')


def gen_setup(program: str):
    # make a secure temporary directory for sockets
    # This is only readable, writeable & searchable by our uid
    sockets_dir = tempfile.mkdtemp(prefix=program)
    sockets_path = os.path.join(sockets_dir, 'vnc-socket')

    if (vnc_path := which('vncserver')):
        # Use bundled tigervnc
        vncserver = pathlib.Path(vnc_path)
    else:
        vncserver = HERE / 'share/tigervnc/bin/vncserver'


    # TigerVNC provides the option to connect a Unix socket. TurboVNC does not.
    # TurboVNC and TigerVNC share the same origin and both use a Perl script
    # as the executable vncserver. We can determine if vncserver is TigerVNC
    # by searching TigerVNC string in the Perl script.
    with vncserver.open() as vncserver_file:
        is_tigervnc = "TigerVNC" in vncserver_file.read()

    if is_tigervnc:
        vnc_args = [vncserver.as_posix(), '-rfbunixpath', sockets_path]
        socket_args = ['--unix-target', sockets_path]
    else:
        vnc_args = [vncserver.as_posix()]
        socket_args = []

    xstartup_file = HERE / f'share/{program}'
    assert xstartup_file.exists()

    vnc_command = ' '.join(
        shlex.quote(p)
        for p in (
            vnc_args
            + [
                '-verbose',
                '-xstartup',
                xstartup_file.as_posix(),
                '-SecurityTypes',
                'None',
                '-fg',
            ]
        )
    )
    return {
        'command': [
            'websockify',
            '-v',
            '--web',
            (HERE / 'share/web/noVNC-1.2.0').as_posix(),
            '--heartbeat',
            '30',
            '{port}',
        ]
        + socket_args
        + ['--', '/bin/sh', '-c', f'cd {os.getcwd()} && {vnc_command}'],
        'timeout': 30,
        'mappath': {'/': '/vnc_lite.html'},
        'new_browser_window': True,
        'launcher_entry': {
            'icon_path': (HERE / f'share/icons/{program}.svg').as_posix(),
        }
    }
