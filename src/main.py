"""prinzclaw — Entry point and agent lifecycle management."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

from src.config import Config
from src.database import Database
from src.scanner import Scanner
from src.analyzer import Analyzer
from src.crafter import Crafter
from src.publisher import Publisher
from src.gateway import Gateway


def setup_logging(config: Config) -> None:
    """Configure logging to both file and stdout."""
    log_dir = Path(config.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(config.log_file)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger("prinzclaw")
    root_logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


class PrinzclawAgent:
    """Main agent — manages lifecycle and orchestrates the TACO engine."""

    def __init__(self, config_path: str | None = None):
        self.config = Config(config_path)
        setup_logging(self.config)
        self.logger = logging.getLogger("prinzclaw")

        # Ensure data directory exists
        Path(self.config.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.db = Database(self.config.db_path)
        self.scanner = Scanner(self.config)
        self.analyzer = Analyzer(self.config)
        self.crafter = Crafter(self.config)
        self.publisher = Publisher(self.config, self.db)
        self.gateway = Gateway(
            self.config, self.db,
            self.scanner, self.analyzer,
            self.crafter, self.publisher,
        )

        self._running = False
        self._scan_task: asyncio.Task | None = None

    def start(self) -> None:
        """Start the prinzclaw agent."""
        self.logger.info("=" * 60)
        self.logger.info("PRINZCLAW AGENT v1.0.0")
        self.logger.info("FORGED WITH PRINZCLAW")
        self.logger.info("=" * 60)
        self.logger.info("AI Provider: %s (%s)", self.config.ai_provider, self.config.ai_model)
        self.logger.info("Gateway: %s:%d", self.config.gateway_host, self.config.gateway_port)
        self.logger.info("Database: %s", self.config.db_path)
        self.logger.info("Output mode: %s", self.config.output_mode)
        self.logger.info("Review required: %s", self.config.review_required)
        self.logger.info("Targets: %d configured", len(self.config.targets))
        self.logger.info("=" * 60)

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        self._running = True

        # Start the gateway (this blocks)
        self.gateway.run()

    def _handle_shutdown(self, signum, frame) -> None:
        """Handle graceful shutdown."""
        self.logger.info("Shutdown signal received — stopping agent")
        self._running = False
        self.db.close()
        self.logger.info("prinzclaw agent stopped")
        sys.exit(0)

    async def run_taco_cycle(self, statement_text: str, target_name: str = "",
                              target_role: str = "", target_type: str = "person",
                              source_url: str = "", date: str = "",
                              style: str = "") -> dict | None:
        """Execute a full TACO cycle on a statement.

        Returns the Strike dict or None if the statement is filtered out.
        """
        # T — Tension/Scan
        scan_result = self.scanner.scan_statement(
            text=statement_text,
            target_name=target_name,
            target_role=target_role,
            target_type=target_type,
            source_url=source_url,
            date=date,
        )

        if not scan_result:
            self.logger.info("Statement filtered out by scanner")
            return None

        target = scan_result["target"]
        statement = scan_result["statement"]

        # A — Acceleration/Analyze
        analysis = self.analyzer.analyze(target, statement)

        # C — Curvature/Craft
        strike = await self.crafter.craft(
            target=target,
            statement=statement,
            evidence=analysis["evidence"],
            style=style,
        )

        # O — Observer/Output
        self.publisher.queue_for_review(strike)

        return strike.to_dict()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="prinzclaw — Truth-strike weapon system",
        epilog="FORGED WITH PRINZCLAW",
    )
    parser.add_argument(
        "-c", "--config",
        default=None,
        help="Path to prinzclaw.yaml config file",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Gateway host (overrides config)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Gateway port (overrides config)",
    )

    args = parser.parse_args()

    agent = PrinzclawAgent(config_path=args.config)

    if args.host:
        agent.config._data["gateway"]["host"] = args.host
    if args.port:
        agent.config._data["gateway"]["port"] = args.port

    agent.start()


if __name__ == "__main__":
    main()
