import sys,types,unittest
from unittest.mock import Mock,patch
import launch

class LaunchTests(unittest.TestCase):
    def test_cli_arguments_use_diagnostic_entrypoint(self):
        cli=types.SimpleNamespace(main=Mock(return_value=7))
        with patch.object(sys,'argv',['app.exe','--rom','local.bin']),patch.dict(sys.modules,{'ecu_workbench.cli':cli}):
            self.assertEqual(launch.main(),7)
        cli.main.assert_called_once_with()

    def test_no_arguments_start_gui(self):
        gui=types.SimpleNamespace(start=Mock())
        with patch.object(sys,'argv',['app.exe']),patch.dict(sys.modules,{'ecu_workbench.gui':gui}):
            self.assertEqual(launch.main(),0)
        gui.start.assert_called_once_with()
