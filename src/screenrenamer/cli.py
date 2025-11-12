"""Command-line interface for ScreenRenamer."""

import argparse
import os
import signal
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .config import ScreenRenamerConfig
from .logger import get_logger
from .orchestrator import ScreenRenamerOrchestrator


class ScreenRenamerCLI:
    """Command-line interface for ScreenRenamer."""

    def __init__(self):
        self.console = Console()
        self.logger = get_logger("cli")
        self.orchestrator: ScreenRenamerOrchestrator | None = None
        self._shutdown_requested = False
        self._shutdown_complete = False

    def _check_configuration_exists(self) -> bool:
        """Check if a valid watch path is configured."""
        try:
            config = ScreenRenamerConfig.from_env()
            return config.watcher.watch_path.exists() and config.watcher.watch_path.is_dir()
        except Exception:
            return False

    def _create_env_file(self, watch_path: str) -> None:
        """Create or update .env file with the watch path."""
        env_path = Path(".env")
        env_content = f"# ScreenRenamer Configuration\nSCREENRENAMER_WATCH_PATH={watch_path}\n"

        try:
            if env_path.exists():
                # Read existing content and update/replace the watch path
                existing_content = env_path.read_text()
                lines = existing_content.split("\n")
                updated_lines = []
                watch_path_found = False

                for line in lines:
                    if line.startswith("SCREENRENAMER_WATCH_PATH="):
                        updated_lines.append(f"SCREENRENAMER_WATCH_PATH={watch_path}")
                        watch_path_found = True
                    else:
                        updated_lines.append(line)

                if not watch_path_found:
                    updated_lines.append(f"SCREENRENAMER_WATCH_PATH={watch_path}")

                env_path.write_text("\n".join(updated_lines) + "\n")
            else:
                env_path.write_text(env_content)

            self.console.print(f"[green]✓ Configuration saved to {env_path}[/green]")

        except Exception as e:
            self.console.print(f"[red]Failed to save configuration: {e}[/red]")

    def _prompt_for_configuration(self) -> ScreenRenamerConfig:
        """Prompt user to configure the watch path."""
        self.console.print()
        self.console.print("[bold yellow]📁 ScreenRenamer Setup[/bold yellow]")
        self.console.print("[dim]Let's configure which folder to watch for screenshots.[/dim]")
        self.console.print()

        # Show common screenshot locations
        common_paths = [
            Path.home() / "Pictures" / "Screenshots",
            Path.home() / "Desktop",
            Path.home() / "Downloads",
            Path.cwd() / "screenshots",
        ]

        self.console.print("[cyan]Common locations:[/cyan]")
        for i, path in enumerate(common_paths, 1):
            exists = "✓" if path.exists() else "✗"
            self.console.print(f"  {i}. {exists} {path}")
        self.console.print()

        # Ask user for path
        while True:
            watch_path_str = Prompt.ask(
                "[bold]Enter the full path to your screenshots folder[/bold]",
                default=str(common_paths[0]),
            ).strip()

            watch_path = Path(watch_path_str).expanduser().resolve()

            if not watch_path.exists():
                create_dir = Confirm.ask(f"Directory {watch_path} doesn't exist. Create it?")
                if create_dir:
                    try:
                        watch_path.mkdir(parents=True, exist_ok=True)
                        self.console.print(f"[green]✓ Created directory: {watch_path}[/green]")
                        break
                    except Exception as e:
                        self.console.print(f"[red]Failed to create directory: {e}[/red]")
                        continue
                else:
                    continue
            elif not watch_path.is_dir():
                self.console.print(f"[red]Error: {watch_path} is not a directory[/red]")
                continue
            else:
                self.console.print(f"[green]✓ Using existing directory: {watch_path}[/green]")
                break

        # Ask about saving configuration
        save_config = Confirm.ask(
            "\n[bold]Save this configuration for future use?[/bold]", default=True
        )

        if save_config:
            self._create_env_file(str(watch_path))

        # Create config with the chosen path
        config = ScreenRenamerConfig.from_env()
        config.watcher.watch_path = watch_path

        return config

    def _cmd_setup(self, args):
        """Handle setup command."""
        try:
            self._show_banner()
            config = self._prompt_for_configuration()

            self.console.print("\n[green]✓ Setup complete![/green]")
            self.console.print(f"[dim]Watching: {config.watcher.watch_path}[/dim]")
            self.console.print(
                "\n[dim]You can now run other commands like 'screenrenamer start'[/dim]"
            )

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Setup cancelled.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Setup failed: {e}[/red]")
            sys.exit(1)

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            """Handle shutdown signals gracefully."""
            if self._shutdown_requested:
                # Second signal - force immediate exit
                self.console.print("\n[red]Force shutdown requested...[/red]")
                os._exit(1)  # Force exit without cleanup

            self._shutdown_requested = True
            signal_name = "SIGINT (Ctrl+C)" if signum == signal.SIGINT else f"Signal {signum}"
            self.console.print(f"\n[yellow]🛑 {signal_name} received - shutting down gracefully...[/yellow]")
            # Don't do cleanup here - let the main loop handle it

        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.logger.debug("Signal handlers configured for graceful shutdown")

    def _perform_graceful_shutdown(self):
        """Perform comprehensive cleanup during shutdown."""
        try:
            self.logger.info("Starting graceful shutdown sequence...")

            # Step 1: Stop the orchestrator/watcher
            if self.orchestrator:
                self.console.print("[dim]Stopping file watcher...[/dim]")
                self.orchestrator.stop_watching()

                # Wait a bit for any in-progress operations to complete
                time.sleep(1.0)

                # Log final statistics if available
                try:
                    status = self.orchestrator.get_status()
                    processed_count = status.get('processed_files_count', 0)
                    if processed_count > 0:
                        self.console.print(f"[dim]Processed {processed_count} files during session[/dim]")
                except Exception:
                    pass  # Ignore errors during shutdown

            # Step 2: Clean up any temporary resources
            self._cleanup_resources()

            # Step 3: Flush any pending logs
            self.logger.info("Shutdown sequence completed")

        except Exception as e:
            self.logger.error(f"Error during shutdown cleanup: {e}")
            # Continue with shutdown even if cleanup fails

    def _cleanup_resources(self):
        """Clean up any remaining resources."""
        try:
            # Close any open file handles, connections, etc.
            # For now, this is a placeholder for future resource cleanup
            pass
        except Exception as e:
            self.logger.error(f"Error during resource cleanup: {e}")

    def _create_config_from_args(self, args) -> ScreenRenamerConfig:
        """Create configuration from command line arguments."""
        # Start with environment-based config
        config = ScreenRenamerConfig.from_env()

        # Override with CLI arguments
        if args.watch_path:
            config.watcher.watch_path = Path(args.watch_path)

        if args.model:
            config.llm.model_name = args.model

        if args.llm_url:
            config.llm.base_url = args.llm_url

        if args.log_level:
            config.logging.level = args.log_level.upper()

        if args.log_file:
            config.logging.file_path = Path(args.log_file)

        return config

    def _show_banner(self):
        """Show the application banner."""
        banner = Panel.fit(
            "[bold blue]ScreenRenamer[/bold blue]\n"
            "[dim]AI-powered screenshot renamer using local LLM vision models[/dim]",
            border_style="blue",
        )
        self.console.print(banner)

    def _show_status(self):
        """Show current status."""
        if not self.orchestrator:
            self.console.print("[red]Orchestrator not initialized[/red]")
            return

        status = self.orchestrator.get_status()

        table = Table(title="Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")

        table.add_row(
            "Watcher",
            "🟢 Running" if status["watching"] else "🔴 Stopped",
            f"Watching: {status['watch_path']}",
        )

        table.add_row(
            "LLM Service",
            "🟢 Available" if status["llm_available"] else "🔴 Unavailable",
            f"Model: {status['llm_model']}",
        )

        table.add_row(
            "File Processing",
            "🟢 Active" if status["watching"] else "🟡 Ready",
            f"Processed: {status['processed_files_count']} files",
        )

        table.add_row("Patterns", "📁", f"Watching: {', '.join(status['file_patterns'])}")

        self.console.print(table)

    def _cmd_start(self, args):
        """Handle start command."""
        try:
            config = self._create_config_from_args(args)
            self.orchestrator = ScreenRenamerOrchestrator(config)

            self._show_banner()
            self.console.print("[green]Starting ScreenRenamer...[/green]")
            self.console.print(f"[dim]Watch path: {config.watcher.watch_path}[/dim]")
            self.console.print(f"[dim]LLM model: {config.llm.model_name}[/dim]")

            self.orchestrator.start_watching()
            self._show_status()

            self.console.print("\n[green]🎯 ScreenRenamer is now watching for screenshots![/green]")
            self.console.print(f"[dim]📁 Watching: {config.watcher.watch_path}[/dim]")
            self.console.print(f"[dim]🤖 Model: {config.llm.model_name}[/dim]")
            self.console.print("[yellow]🛑 Press Ctrl+C to stop gracefully...[/yellow]")

            # Keep running - signal handlers will set shutdown flag
            self.logger.info("Entering watch loop - press Ctrl+C to stop")
            try:
                while self.orchestrator.watcher and self.orchestrator.watcher.is_running():
                    if self._shutdown_requested:
                        self.logger.info("Shutdown requested, exiting watch loop")
                        break
                    # Use a short sleep to allow signal processing
                    time.sleep(0.1)
            except KeyboardInterrupt:
                # This should not happen if signal handlers work, but just in case
                self.console.print("\n[yellow]KeyboardInterrupt caught - shutting down...[/yellow]")
                self._shutdown_requested = True

            # Perform graceful shutdown if requested
            if self._shutdown_requested:
                self._perform_graceful_shutdown()
                self.console.print("\n[green]✅ Shutdown complete![/green]")
        except Exception as e:
            self.console.print(f"[red]Error starting ScreenRenamer: {e}[/red]")
            sys.exit(1)

    def _cmd_once(self, args):
        """Handle once command (process one specific photo)."""
        try:
            config = self._create_config_from_args(args)
            self.orchestrator = ScreenRenamerOrchestrator(config)

            self._show_banner()

            # Get the watch path
            watch_path = config.watcher.watch_path
            patterns = config.watcher.patterns

            # Find available photos
            available_files = []
            for pattern in patterns:
                for file_path in watch_path.glob(pattern):
                    if file_path.is_file():
                        available_files.append(file_path)

            if not available_files:
                self.console.print(f"[yellow]No image files found in {watch_path}[/yellow]")
                return

            # Show available files
            self.console.print(f"[cyan]Found {len(available_files)} image files:[/cyan]")
            for i, file_path in enumerate(available_files, 1):
                self.console.print(f"  {i}. {file_path.name}")
            self.console.print()

            # Ask user to select a file
            while True:
                try:
                    choice = Prompt.ask(
                        f"[bold]Enter the number (1-{len(available_files)}) of the file to process[/bold]",
                        default="1"
                    ).strip()

                    index = int(choice) - 1
                    if 0 <= index < len(available_files):
                        selected_file = available_files[index]
                        break
                    else:
                        self.console.print(f"[red]Please enter a number between 1 and {len(available_files)}[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a valid number[/red]")

            self.console.print(f"[green]Processing: {selected_file.name}[/green]")

            # Process the selected file
            self.orchestrator._process_screenshot(selected_file)

            self.console.print("[green]Finished processing selected file![/green]")

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Cancelled.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error processing file: {e}[/red]")
            sys.exit(1)

    def _cmd_all(self, args):
        """Handle all command (process all existing files)."""
        try:
            config = self._create_config_from_args(args)
            self.orchestrator = ScreenRenamerOrchestrator(config)

            self._show_banner()
            self.console.print("[green]Processing all screenshots in watch folder...[/green]")

            self.orchestrator.run_once()

            self.console.print("[green]Finished processing all files![/green]")

        except Exception as e:
            self.console.print(f"[red]Error processing files: {e}[/red]")
            sys.exit(1)

    def _cmd_test(self, args):
        """Handle test command."""
        try:
            config = self._create_config_from_args(args)
            self.orchestrator = ScreenRenamerOrchestrator(config)

            self._show_banner()
            self.console.print("[green]Testing LLM connection...[/green]")

            if self.orchestrator.test_llm_connection():
                self.console.print("[green]✓ LLM service is available and ready![/green]")
            else:
                self.console.print("[red]✗ LLM service is not available[/red]")
                self.console.print(
                    "[dim]Make sure Ollama is running and the model is installed[/dim]"
                )
                sys.exit(1)

        except Exception as e:
            self.console.print(f"[red]Error testing LLM: {e}[/red]")
            sys.exit(1)

    def _cmd_status(self, args):
        """Handle status command."""
        try:
            if not self.orchestrator:
                config = self._create_config_from_args(args)
                self.orchestrator = ScreenRenamerOrchestrator(config)

            self._show_banner()
            self._show_status()

        except Exception as e:
            self.console.print(f"[red]Error getting status: {e}[/red]")
            sys.exit(1)

    def run(self):
        """Run the CLI application."""
        self._setup_signal_handlers()

        parser = argparse.ArgumentParser(
            description="AI-powered screenshot renamer using local LLM vision models",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  screenrenamer start                    # Start watching with default settings
  screenrenamer start --watch-path ./screenshots
  screenrenamer once                     # Process one specific photo
  screenrenamer all                      # Process all photos in watch folder
  screenrenamer test                     # Test LLM connection
  screenrenamer status                   # Show current status
  screenrenamer setup                    # Configure watch directory

Environment Variables:
  SCREENRENAMER_WATCH_PATH    Directory to watch for screenshots
  SCREENRENAMER_LLM_MODEL     Ollama model name (default: llama3.2-vision:11b)
  SCREENRENAMER_LLM_URL       Ollama server URL (default: http://localhost:11434)
  SCREENRENAMER_LLM_TIMEOUT   Request timeout in seconds (default: 120)
            """,
        )

        parser.add_argument(
            "command", choices=["start", "once", "all", "test", "status", "setup"], help="Command to run"
        )

        parser.add_argument("--watch-path", type=str, help="Directory to watch for screenshots")

        parser.add_argument(
            "--model", type=str, help="Ollama model name (default: llama3.2-vision:11b)"
        )

        parser.add_argument(
            "--llm-url", type=str, help="Ollama server URL (default: http://localhost:11434)"
        )

        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            help="Logging level (default: INFO)",
        )

        parser.add_argument("--log-file", type=str, help="Log file path (default: console only)")

        # Parse known args first to check for setup command
        args, _unknown = parser.parse_known_args()

        # Handle setup command specially
        if args.command == "setup":
            self._cmd_setup(args)
            return

        # For other commands, check if configuration exists
        if not self._check_configuration_exists():
            self.console.print("[yellow]⚠️  No screenshot folder configured yet.[/yellow]")
            use_setup = Confirm.ask("Would you like to run setup now?", default=True)
            if use_setup:
                self._cmd_setup(args)
                return
            else:
                self.console.print(
                    "[red]Cannot proceed without a configured screenshot folder.[/red]"
                )
                self.console.print("[dim]Run 'screenrenamer setup' to configure.[/dim]")
                sys.exit(1)

        # Continue with normal command processing
        args = parser.parse_args()  # Re-parse to ensure all args are handled

        # Dispatch to command handler
        command_map = {
            "start": self._cmd_start,
            "once": self._cmd_once,
            "all": self._cmd_all,
            "test": self._cmd_test,
            "status": self._cmd_status,
        }

        command_map[args.command](args)


def main():
    """Entry point for the CLI."""
    cli = ScreenRenamerCLI()
    cli.run()


if __name__ == "__main__":
    main()
