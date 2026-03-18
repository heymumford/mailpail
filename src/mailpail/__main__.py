# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import argparse
import datetime
import getpass
import logging
import os
import sys

from mailpail import __version__

logger = logging.getLogger(__name__)

_VALID_FORMATS = ("csv", "excel", "excel-sheets", "pdf", "mbox", "eml")


def _build_parser() -> argparse.ArgumentParser:
    from mailpail.plugin import load_plugins
    from mailpail.providers import PROVIDERS

    load_plugins()  # discover installed plugin providers

    p = argparse.ArgumentParser(
        prog="mailpail",
        description="Download email via IMAP and export to CSV, Excel, or PDF.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Mode selection
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--gui", action="store_true", help="Launch the graphical wizard (default when no args)")
    mode.add_argument("--cli", action="store_true", help="Run in command-line mode")

    # Connection
    conn = p.add_argument_group("connection")
    conn.add_argument("-u", "--username", default=None, help="Email address")
    conn.add_argument("-p", "--password", default=None, help="App password")
    conn.add_argument(
        "--password-env",
        default="MAILPAIL_APP_PASSWORD",
        help="Environment variable containing the app password (default: MAILPAIL_APP_PASSWORD)",
    )
    conn.add_argument(
        "--provider",
        choices=sorted(PROVIDERS.keys()),
        default="aol",
        help="Email provider (default: aol). Sets server/port automatically unless overridden.",
    )
    conn.add_argument("--server", default=None, help="IMAP server (overrides provider default)")
    conn.add_argument("--port", type=int, default=None, help="IMAP port (overrides provider default)")

    # Filters
    filt = p.add_argument_group("filters")
    filt.add_argument("--date-from", default=None, help="Start date YYYY-MM-DD")
    filt.add_argument("--date-to", default=None, help="End date YYYY-MM-DD")
    filt.add_argument("--sender", default=None, help="Filter by sender (substring)")
    filt.add_argument("--subject", default=None, help="Filter by subject (substring)")
    filt.add_argument("--folder", default="INBOX", help="IMAP folder (default: INBOX)")
    filt.add_argument("--unread-only", action="store_true", help="Fetch unread messages only")

    # Export
    exp = p.add_argument_group("export")
    exp.add_argument(
        "-f", "--format", nargs="+", choices=_VALID_FORMATS, default=["csv"], help="Export format(s) (default: csv)"
    )
    exp.add_argument("-o", "--output-dir", default="./export", help="Output directory (default: ./export)")
    exp.add_argument("--incremental", action="store_true", help="Skip already-exported emails (track by UID)")
    exp.add_argument("--prefix", default="mail_export", help="Filename prefix (default: mail_export)")
    exp.add_argument(
        "--group-by",
        choices=("folder", "sender", "date"),
        default="folder",
        help="Grouping for excel-sheets format (default: folder)",
    )

    # Logging
    log = p.add_argument_group("logging")
    log.add_argument(
        "--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO", help="Log level (default: INFO)"
    )
    log.add_argument(
        "--log-file", nargs="?", const="", default=None, help="Log file path (omit value for platform default)"
    )
    log.add_argument("--syslog", action="store_true", help="Enable syslog (POSIX only)")

    # Actions
    act = p.add_argument_group("actions")
    act.add_argument("--list-folders", action="store_true", help="List available IMAP folders and exit")
    act.add_argument("--dry-run", action="store_true", help="Show matching email count without exporting")
    act.add_argument(
        "--batch",
        default=None,
        metavar="CSV_FILE",
        help="Process multiple accounts from a CSV file (columns: username,password,provider,folder,format)",
    )

    return p


def _resolve_password(args: argparse.Namespace) -> str:
    if args.password:
        return args.password
    env_val = os.environ.get(args.password_env)
    if env_val:
        logger.debug("Using password from environment variable %s", args.password_env)
        return env_val
    return getpass.getpass(f"App password for {args.username}: ")


def _parse_date(value: str | None) -> datetime.date | None:
    if value is None:
        return None
    return datetime.date.fromisoformat(value)


def _run_gui() -> None:
    """Launch the graphical wizard."""
    from mailpail.logging_config import setup_logging
    from mailpail.plugin import load_plugins
    from mailpail.ui.app import launch_gui

    load_plugins()  # discover installed plugin providers
    setup_logging(level="INFO")
    logger.debug("Launching GUI wizard")
    launch_gui()


def _run_batch(args: argparse.Namespace) -> None:
    """Run batch export from a CSV credential file."""
    from pathlib import Path

    from mailpail.auth import Credential
    from mailpail.batch import load_batch_file
    from mailpail.exporters import get_exporter
    from mailpail.exporters.export_log import write_export_log
    from mailpail.exporters.incremental import save_exported_uids
    from mailpail.exporters.manifest import write_manifest
    from mailpail.exporters.zipper import zip_export
    from mailpail.filters import apply_filters
    from mailpail.models import ExportConfig, FilterParams
    from mailpail.providers import get_provider_info

    batch_path = Path(args.batch)
    try:
        entries = load_batch_file(batch_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Batch: {len(entries)} account(s) from {batch_path.name}\n")
    any_failure = False

    for i, entry in enumerate(entries, start=1):
        print(f"[{i}/{len(entries)}] {entry.username} ({entry.provider})")
        account_dir = Path(args.output_dir) / entry.username.replace("@", "_at_")
        account_dir.mkdir(parents=True, exist_ok=True)

        try:
            descriptor = get_provider_info(entry.provider)
            credential = Credential(
                provider_key=descriptor.key,
                data={"username": entry.username, "password": entry.password},
            )
            client_obj = descriptor.adapter_factory(credential)

            with client_obj as client:
                filters = FilterParams(folder=entry.folder)
                records = client.fetch_emails(filters)
                records = apply_filters(records, filters)

                if not records:
                    print("  No emails matched. Skipping.")
                    continue

                config = ExportConfig(
                    output_dir=str(account_dir),
                    formats=(entry.format,),
                    filename_prefix=f"{entry.username.split('@')[0]}_{entry.folder}",
                )

                exporter = get_exporter(entry.format)
                result = exporter.export(records, config)

                if result.success:
                    att_info = f" ({result.attachment_count} attachments)" if result.attachment_count else ""
                    print(f"  {result.record_count} emails -> {result.file_path}{att_info}")
                else:
                    print(f"  FAILED: {result.error}")
                    any_failure = True
                    continue

                write_export_log(
                    account_dir,
                    [result],
                    len(records),
                    filters=filters,
                    folders=[entry.folder],
                    provider_key=entry.provider,
                    username=entry.username,
                )
                save_exported_uids(account_dir, {r.uid for r in records})
                write_manifest(account_dir, [result], len(records))
                zip_export(account_dir)

        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR: {exc}")
            any_failure = True

    print()
    if any_failure:
        print("Some accounts failed — check output directories for details.")
        sys.exit(1)
    else:
        print(f"All {len(entries)} account(s) exported successfully.")


def _run_cli(args: argparse.Namespace) -> None:
    """Execute the CLI export pipeline."""
    from pathlib import Path

    from mailpail.auth import Credential
    from mailpail.exporters import get_exporter
    from mailpail.filters import apply_filters
    from mailpail.logging_config import setup_logging
    from mailpail.models import ExportConfig, FilterParams
    from mailpail.providers import get_provider_info

    setup_logging(level=args.log_level, log_file=args.log_file, syslog=args.syslog)
    logger.debug("mailpail %s starting (CLI mode)", __version__)

    if args.batch:
        _run_batch(args)
        return

    if not args.username:
        print("Error: --username is required in CLI mode.", file=sys.stderr)
        sys.exit(1)

    # Resolve provider descriptor.
    descriptor = get_provider_info(args.provider)

    # For IMAP providers, check server is available.
    server = args.server if args.server else descriptor.server
    port = args.port if args.port else descriptor.port

    if not server and not descriptor.auth_flow.requires_browser:
        print("Error: --server is required for custom IMAP provider.", file=sys.stderr)
        sys.exit(1)

    try:
        password = _resolve_password(args)

        # Build credential and create adapter via the provider's factory.
        credential = Credential(
            provider_key=descriptor.key,
            data={"username": args.username, "password": password},
        )

        # If server/port were overridden, use IMAPClient directly; otherwise use factory.
        if args.server or args.port:
            from mailpail.client import IMAPClient

            client_obj = IMAPClient(username=args.username, password=password, server=server, port=port)
        else:
            client_obj = descriptor.adapter_factory(credential)

        with client_obj as client:
            if args.list_folders:
                folders = client.list_folders()
                print("Available folders:")
                for f in folders:
                    print(f"  {f}")
                return

            filters = FilterParams(
                date_from=_parse_date(args.date_from),
                date_to=_parse_date(args.date_to),
                sender=args.sender,
                subject=args.subject,
                folder=args.folder,
                unread_only=args.unread_only,
            )

            logger.info("Fetching emails with filters: %s", filters)
            records = client.fetch_emails(filters)
            records = apply_filters(records, filters)

            if args.incremental:
                from mailpail.exporters.incremental import filter_new_records

                os.makedirs(args.output_dir, exist_ok=True)
                before = len(records)
                records = filter_new_records(records, Path(args.output_dir))
                skipped = before - len(records)
                if skipped:
                    print(f"Incremental: skipping {skipped} already-exported, {len(records)} new.")

            if args.dry_run:
                print(f"Matched {len(records)} email(s) — dry run, nothing exported.")
                return

            if not records:
                print("No emails matched the given filters. Nothing to export.")
                return

            config = ExportConfig(
                output_dir=args.output_dir,
                formats=tuple(args.format),
                excel_group_by=args.group_by,
                filename_prefix=args.prefix,
            )

            print(f"\nExporting {len(records)} email(s)...\n")
            any_failure = False
            results = []

            for fmt in config.formats:
                exporter = get_exporter(fmt)
                result = exporter.export(records, config)
                results.append(result)
                if result.success:
                    att_info = f" ({result.attachment_count} attachments)" if result.attachment_count else ""
                    print(f"  [{fmt}] {result.record_count} records -> {result.file_path}{att_info}")
                    for w in result.warnings:
                        print(f"    WARNING: {w}")
                else:
                    print(f"  [{fmt}] FAILED: {result.error}")
                    any_failure = True

            # Write export log
            from mailpail.exporters.export_log import write_export_log

            write_export_log(
                Path(config.output_dir),
                results,
                len(records),
                filters=filters,
                folders=[args.folder],
                provider_key=args.provider,
                username=args.username,
            )

            # Save incremental UIDs only if all exports succeeded
            if not any_failure:
                from mailpail.exporters.incremental import save_exported_uids

                save_exported_uids(Path(config.output_dir), {r.uid for r in records})

            # Write manifest
            from mailpail.exporters.manifest import write_manifest
            from mailpail.exporters.zipper import zip_export

            manifest_path = write_manifest(Path(config.output_dir), results, len(records))
            print(f"\n  Manifest: {manifest_path}")

            # Zip everything
            zip_path = zip_export(Path(config.output_dir))
            print(f"  Zip: {zip_path}")

            print()
            if any_failure:
                print("Some exports failed — check the log for details.")
                sys.exit(1)
            else:
                print("All exports completed successfully.")

    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except ConnectionError as exc:
        logger.error("%s", exc)
        print(f"\nConnection error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error")
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    # No arguments at all → launch GUI
    if len(sys.argv) <= 1:
        _run_gui()
        return

    parser = _build_parser()
    args = parser.parse_args()

    if args.gui:
        _run_gui()
    elif args.cli or args.username:
        _run_cli(args)
    else:
        # If only flags like --log-level were set but no mode, default to GUI
        _run_gui()


if __name__ == "__main__":
    main()
