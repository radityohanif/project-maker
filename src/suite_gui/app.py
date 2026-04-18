"""wx entrypoint for suite-gui."""

from __future__ import annotations


def main() -> None:
    import wx

    from suite_gui.main_frame import MainFrame

    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
