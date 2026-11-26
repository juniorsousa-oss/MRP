"""Safety checks for the visual-only MRP navigation change."""
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

import mrp_workspace


class WorkspaceTransitionTest(unittest.TestCase):
    def test_missing_script_falls_back_to_regular_navigation(self):
        display = Mock()
        with patch.dict("os.environ", {"MRP_DISABLE_TAB_TRANSITION": ""}), patch.object(
            mrp_workspace, "_workspace_transition_script", side_effect=FileNotFoundError()
        ) as script, self.assertLogs("mrp_workspace", level="WARNING"):
            mrp_workspace.workspace_transition(display)
        script.assert_called_once()
        display.html.assert_not_called()

    def test_disable_switch_does_not_read_asset(self):
        display = Mock()
        with patch.dict("os.environ", {"MRP_DISABLE_TAB_TRANSITION": "1"}), patch.object(
            mrp_workspace, "_workspace_transition_script"
        ) as script:
            mrp_workspace.workspace_transition(display)
        script.assert_not_called()
        display.html.assert_not_called()

    def test_real_entrypoint_opens_login_without_loading_transition(self):
        entrypoint = Path(__file__).resolve().parents[1] / "app_mrp.py"
        app = AppTest.from_file(entrypoint, default_timeout=20)
        offline = RuntimeError("External traffic disabled for the entrypoint test")
        with patch("requests.sessions.Session.request", side_effect=offline), patch(
            "httpx.Client.send", side_effect=offline
        ), patch.object(mrp_workspace, "_workspace_transition_script") as script:
            app.run()
        self.assertFalse(app.exception, app.exception)
        self.assertTrue(any(button.label == "ENTRAR" for button in app.button), app.button)
        script.assert_not_called()
