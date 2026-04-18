"""Primary wx frame: mode selection, paths, proposal options, validate/generate."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

import wx

from suite_gui.jobs import (
    GenerateOutcome,
    MakerMode,
    ProposalGenerateOptions,
    ValidateOutcome,
    generate_mode,
    validate_mode,
)


def _reveal_in_file_manager(path: Path) -> None:
    path = path.resolve()
    target = path if path.is_dir() else path.parent
    if not target.exists():
        return
    if sys.platform == "darwin":
        subprocess.run(["open", str(target)], check=False)
    elif sys.platform == "win32":
        subprocess.run(["explorer", str(target)], check=False)
    else:
        subprocess.run(["xdg-open", str(target)], check=False)


_MODE_LABELS: list[tuple[str, MakerMode]] = [
    ("Project pack (project.yaml)", MakerMode.PROJECT),
    ("Timeline", MakerMode.TIMELINE),
    ("Quote", MakerMode.QUOTE),
    ("Proposal (YAML or Markdown)", MakerMode.PROPOSAL),
    ("Deck", MakerMode.DECK),
]


class MainFrame(wx.Frame):
    def __init__(self) -> None:
        super().__init__(
            None,
            title="Project Maker",
            size=(720, 560),
            style=wx.DEFAULT_FRAME_STYLE,
        )

        self._busy = False
        self._last_output: Path | None = None
        self._last_outputs: tuple[Path, ...] = ()

        root = wx.Panel(self)
        outer = wx.BoxSizer(wx.VERTICAL)

        choices = [label for label, _ in _MODE_LABELS]
        self._mode_radio = wx.RadioBox(
            root,
            choices=choices,
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        self._mode_radio.Bind(wx.EVT_RADIOBOX, self._on_mode_changed)
        outer.Add(self._mode_radio, 0, wx.EXPAND | wx.ALL, 8)

        self._hint = wx.StaticText(
            root,
            label=self._mode_hint(MakerMode.PROJECT),
        )
        outer.Add(self._hint, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        input_row = wx.BoxSizer(wx.HORIZONTAL)
        input_row.Add(
            wx.StaticText(root, label="Input:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            6,
        )
        self._input_path = wx.TextCtrl(root, style=wx.TE_READONLY)
        input_row.Add(self._input_path, 1, wx.EXPAND)
        browse_in = wx.Button(root, label="Browse…")
        browse_in.Bind(wx.EVT_BUTTON, self._on_browse_input)
        input_row.Add(browse_in, 0, wx.LEFT, 6)
        outer.Add(input_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        out_row = wx.BoxSizer(wx.HORIZONTAL)
        out_row.Add(
            wx.StaticText(root, label="Output:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            6,
        )
        self._output_path = wx.TextCtrl(root, style=wx.TE_READONLY)
        out_row.Add(self._output_path, 1, wx.EXPAND)
        browse_out = wx.Button(root, label="Browse…")
        browse_out.Bind(wx.EVT_BUTTON, self._on_browse_output)
        out_row.Add(browse_out, 0, wx.LEFT, 6)
        outer.Add(out_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        self._proposal_wrap = wx.Panel(root)
        proposal_box = wx.StaticBox(self._proposal_wrap, label="Proposal options")
        prop_sz = wx.StaticBoxSizer(proposal_box, wx.VERTICAL)
        flags = wx.BoxSizer(wx.HORIZONTAL)
        self._pdf_check = wx.CheckBox(
            self._proposal_wrap,
            label="Also write PDF (needs LibreOffice or docx2pdf)",
        )
        self._net_check = wx.CheckBox(
            self._proposal_wrap,
            label="Allow downloading remote images (http/https)",
        )
        flags.Add(self._pdf_check, 0, wx.RIGHT, 16)
        flags.Add(self._net_check, 0)
        prop_sz.Add(flags, 0, wx.ALL, 4)

        tpl_row = wx.BoxSizer(wx.HORIZONTAL)
        tpl_row.Add(
            wx.StaticText(self._proposal_wrap, label="Template .docx:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            6,
        )
        self._template_path = wx.TextCtrl(self._proposal_wrap, style=wx.TE_READONLY)
        tpl_row.Add(self._template_path, 1, wx.EXPAND)
        tpl_btn = wx.Button(self._proposal_wrap, label="Browse…")
        tpl_btn.Bind(wx.EVT_BUTTON, self._on_browse_template)
        tpl_row.Add(tpl_btn, 0, wx.LEFT, 6)
        prop_sz.Add(tpl_row, 0, wx.EXPAND | wx.ALL, 4)

        th_row = wx.BoxSizer(wx.HORIZONTAL)
        th_row.Add(
            wx.StaticText(self._proposal_wrap, label="Theme YAML:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            6,
        )
        self._theme_path = wx.TextCtrl(self._proposal_wrap, style=wx.TE_READONLY)
        th_row.Add(self._theme_path, 1, wx.EXPAND)
        th_btn = wx.Button(self._proposal_wrap, label="Browse…")
        th_btn.Bind(wx.EVT_BUTTON, self._on_browse_theme)
        th_row.Add(th_btn, 0, wx.LEFT, 6)
        prop_sz.Add(th_row, 0, wx.EXPAND | wx.ALL, 4)

        self._proposal_wrap.SetSizer(prop_sz)
        outer.Add(self._proposal_wrap, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._validate_btn = wx.Button(root, label="Validate")
        self._validate_btn.Bind(wx.EVT_BUTTON, self._on_validate)
        self._generate_btn = wx.Button(root, label="Generate")
        self._generate_btn.Bind(wx.EVT_BUTTON, self._on_generate)
        self._open_btn = wx.Button(root, label="Open output folder")
        self._open_btn.Bind(wx.EVT_BUTTON, self._on_open_output)
        self._open_btn.Enable(False)
        btn_row.Add(self._validate_btn, 0, wx.RIGHT, 8)
        btn_row.Add(self._generate_btn, 0, wx.RIGHT, 8)
        btn_row.Add(self._open_btn, 0)
        outer.Add(btn_row, 0, wx.ALL, 8)

        outer.Add(wx.StaticText(root, label="Log:"), 0, wx.LEFT | wx.RIGHT, 8)
        self._log = wx.TextCtrl(root, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        outer.Add(self._log, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        root.SetSizer(outer)
        self._on_mode_changed(None)
        self.Centre()

    def _current_mode(self) -> MakerMode:
        idx = self._mode_radio.GetSelection()
        return _MODE_LABELS[idx][1]

    @staticmethod
    def _mode_hint(mode: MakerMode) -> str:
        if mode is MakerMode.PROJECT:
            return (
                "Orchestrator YAML (timeline + quote + proposal; optional deck). "
                "Output is a folder."
            )
        if mode is MakerMode.TIMELINE:
            return "Timeline YAML → single .xlsx path."
        if mode is MakerMode.QUOTE:
            return "Quote YAML → single .xlsx path."
        if mode is MakerMode.PROPOSAL:
            return (
                "Proposal YAML or Markdown → .docx path. "
                "Relative images resolve next to the source file."
            )
        return "Deck YAML → .pptx path. Relative images resolve from the YAML directory."

    def _on_mode_changed(self, _evt: wx.Event | None) -> None:
        mode = self._current_mode()
        self._hint.SetLabel(self._mode_hint(mode))
        self._proposal_wrap.Show(mode is MakerMode.PROPOSAL)
        self.Layout()

    def _input_wildcard(self) -> str:
        mode = self._current_mode()
        if mode is MakerMode.PROPOSAL:
            return (
                "Proposal specs (*.yaml;*.yml;*.md;*.markdown)|*.yaml;*.yml;*.md;*.markdown|"
                "All files (*.*)|*.*"
            )
        return "YAML (*.yaml;*.yml)|*.yaml;*.yml|All files (*.*)|*.*"

    def _on_browse_input(self, _evt: wx.Event) -> None:
        with wx.FileDialog(
            self,
            "Choose input file",
            wildcard=self._input_wildcard(),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            self._input_path.SetValue(dlg.GetPath())
            self._append_log(f"Input set to {dlg.GetPath()}")

    def _on_browse_output(self, _evt: wx.Event) -> None:
        mode = self._current_mode()
        if mode is MakerMode.PROJECT:
            with wx.DirDialog(self, "Choose output directory", style=wx.DD_DEFAULT_STYLE) as dlg:
                if dlg.ShowModal() != wx.ID_OK:
                    return
                self._output_path.SetValue(dlg.GetPath())
        else:
            wildcards = {
                MakerMode.TIMELINE: "Excel (*.xlsx)|*.xlsx",
                MakerMode.QUOTE: "Excel (*.xlsx)|*.xlsx",
                MakerMode.PROPOSAL: "Word (*.docx)|*.docx",
                MakerMode.DECK: "PowerPoint (*.pptx)|*.pptx",
            }
            with wx.FileDialog(
                self,
                "Choose output file",
                wildcard=wildcards[mode],
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            ) as dlg:
                if dlg.ShowModal() != wx.ID_OK:
                    return
                self._output_path.SetValue(dlg.GetPath())
        self._append_log(f"Output set to {self._output_path.GetValue()}")

    def _on_browse_template(self, _evt: wx.Event) -> None:
        with wx.FileDialog(
            self,
            "Template DOCX",
            wildcard="Word (*.docx)|*.docx|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            self._template_path.SetValue(dlg.GetPath())

    def _on_browse_theme(self, _evt: wx.Event) -> None:
        with wx.FileDialog(
            self,
            "Theme YAML",
            wildcard="YAML (*.yaml;*.yml)|*.yaml;*.yml|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            self._theme_path.SetValue(dlg.GetPath())

    def _append_log(self, text: str) -> None:
        self._log.AppendText(text + "\n")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._validate_btn.Enable(not busy)
        self._generate_btn.Enable(not busy)

    def _require_paths(self) -> tuple[Path, Path] | None:
        inp = self._input_path.GetValue().strip()
        out = self._output_path.GetValue().strip()
        if not inp:
            wx.MessageBox("Choose an input file.", "Missing input", wx.OK | wx.ICON_WARNING)
            return None
        if not out:
            wx.MessageBox(
                "Choose an output path or folder.",
                "Missing output",
                wx.OK | wx.ICON_WARNING,
            )
            return None
        return Path(inp), Path(out)

    def _proposal_options(self) -> ProposalGenerateOptions:
        tpl = self._template_path.GetValue().strip()
        th = self._theme_path.GetValue().strip()
        return ProposalGenerateOptions(
            template=Path(tpl) if tpl else None,
            theme=Path(th) if th else None,
            pdf=self._pdf_check.GetValue(),
            allow_network=self._net_check.GetValue(),
        )

    def _on_validate(self, _evt: wx.Event) -> None:
        if self._busy:
            return
        paths = self._require_paths()
        if paths is None:
            return
        input_path, _output_path = paths
        mode = self._current_mode()

        self._set_busy(True)
        self._append_log("--- validate ---")

        def work() -> None:
            outcome = validate_mode(mode, input_path)
            wx.CallAfter(self._finish_validate, outcome)

        threading.Thread(target=work, daemon=True).start()

    def _finish_validate(self, outcome: ValidateOutcome) -> None:
        self._set_busy(False)
        for line in outcome.lines:
            self._append_log(line)
        if outcome.ok:
            wx.MessageBox("Validation succeeded.", "OK", wx.OK | wx.ICON_INFORMATION)
        else:
            msg = outcome.lines[-1] if outcome.lines else "Validation failed."
            wx.MessageBox(msg, "Error", wx.OK | wx.ICON_ERROR)

    def _on_generate(self, _evt: wx.Event) -> None:
        if self._busy:
            return
        paths = self._require_paths()
        if paths is None:
            return
        input_path, output_path = paths
        mode = self._current_mode()
        prop_opts = self._proposal_options() if mode is MakerMode.PROPOSAL else None

        self._set_busy(True)
        self._append_log("--- generate ---")

        def work() -> None:
            outcome = generate_mode(
                mode,
                input_path,
                output_path,
                proposal_opts=prop_opts,
            )
            wx.CallAfter(self._finish_generate, outcome, output_path)

        threading.Thread(target=work, daemon=True).start()

    def _finish_generate(self, outcome: GenerateOutcome, output_path: Path) -> None:
        self._set_busy(False)
        for line in outcome.lines:
            self._append_log(line)
        if outcome.ok:
            self._last_outputs = outcome.output_paths
            self._last_output = output_path
            self._open_btn.Enable(True)
            wx.MessageBox("Generation finished.", "OK", wx.OK | wx.ICON_INFORMATION)
        else:
            msg = outcome.lines[-1] if outcome.lines else "Generate failed."
            wx.MessageBox(msg, "Error", wx.OK | wx.ICON_ERROR)

    def _on_open_output(self, _evt: wx.Event) -> None:
        mode = self._current_mode()
        if mode is MakerMode.PROJECT and self._last_output is not None:
            _reveal_in_file_manager(self._last_output)
            return
        if self._last_outputs:
            first = self._last_outputs[0]
            _reveal_in_file_manager(first)
            return
        out = self._output_path.GetValue().strip()
        if out:
            _reveal_in_file_manager(Path(out))
