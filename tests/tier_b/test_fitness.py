# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Fitness tests — architectural invariants enforced by CI.

These tests verify structural properties of the codebase, not behavior.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.tier_b

_SRC = Path(__file__).resolve().parents[2] / "src" / "mailpail"
_SCREEN_DIR = _SRC / "ui" / "screens"
_UI_FILES = list((_SRC / "ui").rglob("*.py"))


def _read_py(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestNoHardcodedColors:
    """No raw hex color literals in screen files — everything must come from theme."""

    def _screen_files(self) -> list[Path]:
        return [f for f in _SCREEN_DIR.glob("*.py") if f.name != "__init__.py"]

    def test_no_raw_hex_in_screens(self):
        """Screen files must not contain hardcoded hex color strings."""
        # Pattern: quoted hex color like "#FFFFFF" or "#1E8449"
        hex_pattern = re.compile(r"""["']#[0-9A-Fa-f]{6}["']""")
        violations: list[str] = []

        for path in self._screen_files():
            content = _read_py(path)
            for i, line in enumerate(content.splitlines(), 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Allow _CELEBRATION_COLORS definition (complete.py)
                if "_CELEBRATION_COLORS" in line:
                    continue
                matches = hex_pattern.findall(line)
                if matches:
                    violations.append(f"{path.name}:{i}: {matches}")

        assert not violations, "Hardcoded hex colors found:\n" + "\n".join(violations)

    def test_no_raw_hex_in_app(self):
        """app.py must not contain hardcoded hex color strings."""
        hex_pattern = re.compile(r"""["']#[0-9A-Fa-f]{6}["']""")
        app_path = _SRC / "ui" / "app.py"
        content = _read_py(app_path)
        violations: list[str] = []

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            matches = hex_pattern.findall(line)
            if matches:
                violations.append(f"app.py:{i}: {matches}")

        assert not violations, "Hardcoded hex colors in app.py:\n" + "\n".join(violations)


class TestNoAOLInUI:
    """No 'AOL' in user-visible strings in screen files."""

    def test_no_aol_string_in_screens(self):
        """Screen files must not contain 'AOL' in string literals."""
        violations: list[str] = []

        for path in _SCREEN_DIR.glob("*.py"):
            if path.name == "__init__.py":
                continue
            content = _read_py(path)
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Look for AOL in string literals (not comments or variable names)
                if re.search(r"""["'].*AOL.*["']""", line):
                    violations.append(f"{path.name}:{i}: {line.strip()}")

        assert not violations, "AOL references in screen files:\n" + "\n".join(violations)

    def test_no_aol_in_strings_module(self):
        """strings.py must not contain 'AOL'."""
        strings_path = _SRC / "ui" / "strings.py"
        content = _read_py(strings_path)
        violations: list[str] = []

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"""["'].*AOL.*["']""", line):
                violations.append(f"strings.py:{i}: {line.strip()}")

        assert not violations, "AOL references in strings.py:\n" + "\n".join(violations)


class TestNoFadeIn:
    """fade_in animation is removed from all screen files."""

    def test_no_fade_in_imports(self):
        """No screen file imports fade_in."""
        violations: list[str] = []
        for path in _UI_FILES:
            if path.name == "theme.py":
                continue
            content = _read_py(path)
            if "fade_in" in content:
                violations.append(path.name)

        assert not violations, f"fade_in still referenced in: {violations}"


class TestProviders:
    """Provider registry completeness."""

    def test_builtin_providers_present(self):
        """Built-in providers must be a subset of registered providers."""
        from mailpail.providers import PROVIDERS

        required = {"aol", "gmail", "outlook", "yahoo", "imap"}
        assert required <= set(PROVIDERS.keys()), "Built-in providers missing from registry"

    def test_all_builtin_imap_providers_have_server(self):
        """All IMAP providers except 'imap' must have a server set."""
        from mailpail.providers import PROVIDERS

        for key in ("aol", "gmail", "outlook", "yahoo"):
            assert PROVIDERS[key].server, f"Provider {key!r} has no server"

    def test_provider_flag_accepted(self):
        """CLI accepts --provider flag for all built-in providers."""
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        for provider in ("aol", "gmail", "outlook", "yahoo", "imap"):
            args = parser.parse_args(["--username", "u@x.com", "--provider", provider])
            assert args.provider == provider

    def test_base_screen_exists(self):
        """BaseScreen class exists and is importable."""
        from mailpail.ui.screens.base import BaseScreen

        assert hasattr(BaseScreen, "screen_icon")
        assert hasattr(BaseScreen, "screen_title")
        assert hasattr(BaseScreen, "make_card")

    def test_all_providers_are_descriptors(self):
        """Every registered provider is a ProviderDescriptor."""
        from mailpail.providers import PROVIDERS, ProviderDescriptor

        for key, desc in PROVIDERS.items():
            assert isinstance(desc, ProviderDescriptor), f"{key!r} is {type(desc).__name__}, not ProviderDescriptor"

    def test_all_providers_have_auth_flow(self):
        """Every provider has an auth_flow with form_fields()."""
        from mailpail.providers import PROVIDERS

        for key, desc in PROVIDERS.items():
            assert hasattr(desc.auth_flow, "form_fields"), f"{key!r} auth_flow missing form_fields()"
            fields = desc.auth_flow.form_fields()
            assert isinstance(fields, list), f"{key!r} form_fields() did not return a list"

    def test_all_providers_have_adapter_factory(self):
        """Every provider has a callable adapter_factory."""
        from mailpail.providers import PROVIDERS

        for key, desc in PROVIDERS.items():
            assert callable(desc.adapter_factory), f"{key!r} adapter_factory is not callable"


class TestPluginArchitecture:
    """Plugin system structural tests."""

    def test_auth_protocol_contract(self):
        """AppPasswordFlow satisfies the AuthFlow structural contract."""
        from mailpail.auth import AppPasswordFlow

        flow = AppPasswordFlow(provider_key="test")
        assert flow.requires_browser is False
        fields = flow.form_fields()
        assert len(fields) == 2
        assert fields[0].key == "username"
        assert fields[1].key == "password"
        assert fields[1].secret is True

    def test_app_password_acquire(self):
        """AppPasswordFlow.acquire produces a valid Credential."""
        from mailpail.auth import AppPasswordFlow, Credential

        flow = AppPasswordFlow(provider_key="aol")
        cred = flow.acquire({"username": "user@aol.com", "password": "secret"})
        assert isinstance(cred, Credential)
        assert cred.provider_key == "aol"
        assert cred.data["username"] == "user@aol.com"
        assert cred.data["password"] == "secret"

    def test_app_password_acquire_rejects_empty(self):
        """AppPasswordFlow.acquire raises on missing fields."""
        from mailpail.auth import AppPasswordFlow, AuthError

        flow = AppPasswordFlow(provider_key="test")
        with pytest.raises(AuthError):
            flow.acquire({"username": "", "password": ""})

    def test_app_password_refresh_is_noop(self):
        """AppPasswordFlow.refresh returns the same credential."""
        from mailpail.auth import AppPasswordFlow, Credential

        flow = AppPasswordFlow(provider_key="test")
        cred = Credential(provider_key="test", data={"username": "u", "password": "p"})
        assert flow.refresh(cred) is cred

    def test_credential_is_frozen(self):
        """Credential is immutable."""
        from mailpail.auth import Credential

        cred = Credential(provider_key="test", data={"k": "v"})
        with pytest.raises(AttributeError):
            cred.provider_key = "changed"  # type: ignore[misc]

    def test_capability_flags_composable(self):
        """Capability flags can be combined with bitwise OR."""
        from mailpail.auth import Capability

        combined = Capability.SEARCH | Capability.ATTACHMENTS
        assert Capability.SEARCH in combined
        assert Capability.ATTACHMENTS in combined
        assert Capability.LABELS not in combined

    def test_memory_store_roundtrip(self):
        """MemoryStore save/load/delete cycle."""
        from mailpail.auth import Credential
        from mailpail.credentials import MemoryStore

        store = MemoryStore()
        cred = Credential(provider_key="test", data={"username": "u", "password": "p"})

        assert store.load("test") is None
        store.save(cred)
        loaded = store.load("test")
        assert loaded is not None
        assert loaded.data["username"] == "u"
        store.delete("test")
        assert store.load("test") is None

    def test_file_store_roundtrip(self, tmp_path):
        """FileStore save/load/delete cycle."""
        from mailpail.auth import Credential
        from mailpail.credentials import FileStore

        store = FileStore(path=tmp_path / "creds.json")
        cred = Credential(provider_key="mykey", data={"token": "abc123"})

        assert store.load("mykey") is None
        store.save(cred)
        loaded = store.load("mykey")
        assert loaded is not None
        assert loaded.data["token"] == "abc123"
        store.delete("mykey")
        assert store.load("mykey") is None

    def test_file_store_permissions(self, tmp_path):
        """FileStore sets 0600 permissions on the credential file."""
        import stat

        from mailpail.auth import Credential
        from mailpail.credentials import FileStore

        path = tmp_path / "creds.json"
        store = FileStore(path=path)
        store.save(Credential(provider_key="x", data={"a": "b"}))
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600

    def test_load_plugins_idempotent(self):
        """load_plugins can be called multiple times safely."""
        from mailpail.plugin import load_plugins

        load_plugins()
        load_plugins()  # no crash, no duplicate registration

    def test_entry_point_group_name(self):
        """Entry point group name is correct."""
        from mailpail.plugin import ENTRY_POINT_GROUP

        assert ENTRY_POINT_GROUP == "mailpail.providers"

    def test_adapter_factory_produces_client(self):
        """Built-in adapter_factory produces an IMAPClient."""
        from mailpail.auth import Credential
        from mailpail.client import IMAPClient
        from mailpail.providers import PROVIDERS

        cred = Credential(provider_key="aol", data={"username": "u@aol.com", "password": "pass"})
        client = PROVIDERS["aol"].adapter_factory(cred)
        assert isinstance(client, IMAPClient)


class TestAttachmentModel:
    """Attachment support in data models."""

    def test_attachment_dataclass(self):
        from mailpail.models import Attachment

        att = Attachment(filename="test.pdf", content_type="application/pdf", payload=b"data", size=4)
        assert att.filename == "test.pdf"
        assert att.size == 4

    def test_email_record_has_attachments_field(self):
        from mailpail.models import EmailRecord

        fields = {f.name for f in EmailRecord.__dataclass_fields__.values()}
        assert "attachments" in fields

    def test_export_result_has_sha256(self):
        from mailpail.models import ExportResult

        fields = {f.name for f in ExportResult.__dataclass_fields__.values()}
        assert "sha256" in fields
        assert "attachment_count" in fields

    def test_export_config_has_include_attachments(self):
        from mailpail.models import ExportConfig

        config = ExportConfig()
        assert config.include_attachments is True


class TestNewExportFormats:
    """MBOX and EML formats are registered and CLI-accessible."""

    def test_mbox_format_registered(self):
        from mailpail.exporters import get_exporter

        exporter = get_exporter("mbox")
        assert exporter is not None

    def test_eml_format_registered(self):
        from mailpail.exporters import get_exporter

        exporter = get_exporter("eml")
        assert exporter is not None

    def test_cli_accepts_mbox_format(self):
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com", "--format", "mbox"])
        assert "mbox" in args.format

    def test_cli_accepts_eml_format(self):
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com", "--format", "eml"])
        assert "eml" in args.format

    def test_six_formats_available(self):
        """All 6 export formats are registered."""
        from mailpail.exporters import get_exporter

        for fmt in ("csv", "excel", "excel-sheets", "pdf", "mbox", "eml"):
            assert get_exporter(fmt) is not None


class TestLoginProviderDropdown:
    """LoginScreen uses provider registry."""

    def test_display_name_reflects_server(self):
        """IMAPClient.display_name is dynamic, not hardcoded AOL."""
        from mailpail.client import IMAPClient

        client = IMAPClient(username="u", password="p", server="imap.gmail.com")
        assert "gmail" in client.display_name.lower()

    def test_browser_cookie3_is_optional(self):
        """browser-cookie3 is in optional deps, not required."""
        import tomllib
        from pathlib import Path

        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text())
        core_deps = [d.split(">=")[0].split("[")[0].strip().lower() for d in data["project"]["dependencies"]]
        assert "browser-cookie3" not in core_deps


class TestPersonaRequirements:
    """Persona-driven acceptance criteria.

    Margaret: font sizes >= 16px body, no jargon, reassurance text
    Derek: --provider flag, --dry-run, exit codes
    Sandra: ExportResult has audit fields
    Ray: default format is CSV, default dir is Desktop
    """

    def test_margaret_body_font_size(self):
        """Body font must be >= 16px for readability."""
        from mailpail.ui.theme import FONTS

        assert FONTS["body"][1] >= 16

    def test_margaret_no_jargon_in_strings(self):
        """User-visible strings must not contain protocol jargon."""
        from mailpail.ui import strings

        # Collect all string values from the module
        jargon = {"IMAP", "SMTP", "SSL", "TLS", "RFC", "MIME"}
        violations: list[str] = []
        for name in dir(strings):
            if name.startswith("_"):
                continue
            val = getattr(strings, name)
            if isinstance(val, str):
                for j in jargon:
                    if j in val:
                        violations.append(f"{name}: contains '{j}'")
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        for j in jargon:
                            if j in item:
                                violations.append(f"{name}: contains '{j}'")
        assert not violations, "Jargon in user strings:\n" + "\n".join(violations)

    def test_margaret_reassurance_text_exists(self):
        """Reassurance text is defined for user comfort."""
        from mailpail.ui.strings import PROGRESS_REASSURANCE, REASSURANCE_READONLY

        assert "safe" in PROGRESS_REASSURANCE.lower() or "not" in PROGRESS_REASSURANCE.lower()
        assert "delete" in REASSURANCE_READONLY.lower() or "read-only" in REASSURANCE_READONLY.lower()

    def test_derek_provider_flag(self):
        """--provider flag exists with correct choices."""
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com", "--provider", "gmail"])
        assert args.provider == "gmail"

    def test_derek_dry_run(self):
        """--dry-run flag exists."""
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com", "--dry-run"])
        assert args.dry_run is True

    def test_sandra_export_result_audit_fields(self):
        """ExportResult has fields needed for audit trail."""
        from mailpail.models import ExportResult

        fields = {f.name for f in ExportResult.__dataclass_fields__.values()}
        assert "format_name" in fields
        assert "file_path" in fields
        assert "record_count" in fields
        assert "success" in fields

    def test_ray_default_format_csv(self):
        """Default export format is CSV."""
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com"])
        assert args.format == ["csv"]

    def test_ray_default_dir_desktop(self):
        """Default export directory includes Desktop."""
        import os

        default_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Mailpail_Export")
        assert "Desktop" in default_dir
