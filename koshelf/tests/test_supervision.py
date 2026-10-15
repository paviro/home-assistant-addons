import contextlib
import io
import json
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import addon


class Child:
    def __init__(self, status=None):
        self.status = status
        self.terminated = False

    def poll(self):
        return self.status

    def terminate(self):
        self.terminated = True
        self.status = -15

    def wait(self, timeout):
        return self.status


class SupervisionTests(unittest.TestCase):
    def exercise(self, children, on_sleep=None):
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            root = Path(directory)
            config = root / 'options.json'
            config.write_text(json.dumps({'library_path': ['/share/books'], 'direct_access_enabled': False}))
            for key, value in {'OPTIONS': config, 'RUNTIME': root / 'run', 'RESET_MARKER': root / 'reset'}.items():
                stack.enter_context(patch.object(addon, key, value))
            stack.enter_context(patch.object(addon.sys, 'argv', ['addon.py']))
            stack.enter_context(patch.object(addon.subprocess, 'check_output', return_value='--bind-address --auth-proxy-peers'))
            stack.enter_context(patch.object(addon.subprocess, 'run'))
            stack.enter_context(patch.dict(addon.os.environ, {'SUPERVISOR_TOKEN': 'private', 'HASSIO_TOKEN': 'private'}))
            handlers = {}
            stack.enter_context(patch.object(addon.signal, 'signal', side_effect=lambda signum, handler: handlers.update({signum: handler})))
            stack.enter_context(patch.object(addon.time, 'sleep', side_effect=lambda _: on_sleep(handlers) if on_sleep else None))
            spawn = stack.enter_context(patch.object(addon.subprocess, 'Popen', side_effect=children))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            result = addon.main()
            for call in spawn.call_args_list:
                self.assertNotIn('SUPERVISOR_TOKEN', call.kwargs['env'])
                self.assertNotIn('HASSIO_TOKEN', call.kwargs['env'])
            return result

    def test_exited_backend_stops_proxy_and_fails_container(self):
        backend, proxy = Child(1), Child()
        self.assertEqual(self.exercise([backend, proxy]), 1)
        self.assertTrue(proxy.terminated)

    def test_sigterm_stops_both_children(self):
        backend, proxy = Child(), Child()
        result = self.exercise([backend, proxy], lambda handlers: handlers[signal.SIGTERM](signal.SIGTERM, None))
        self.assertEqual(result, 0)
        self.assertTrue(backend.terminated and proxy.terminated)

    def test_failure_starting_proxy_cleans_up_backend(self):
        backend = Child()
        with self.assertRaises(OSError):
            self.exercise([backend, OSError('cannot launch nginx')])
        self.assertTrue(backend.terminated)
