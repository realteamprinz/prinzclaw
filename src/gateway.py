"""OpenClaw-compatible HTTP gateway for prinzclaw agent."""

from __future__ import annotations

import logging

from aiohttp import web

from src.config import Config
from src.database import Database
from src.scanner import Scanner
from src.analyzer import Analyzer
from src.crafter import Crafter
from src.publisher import Publisher
from src.utils import sanitize_input

logger = logging.getLogger("prinzclaw")


class Gateway:
    """OpenClaw-compatible HTTP gateway (default port 8100)."""

    def __init__(self, config: Config, db: Database, scanner: Scanner,
                 analyzer: Analyzer, crafter: Crafter, publisher: Publisher):
        self.config = config
        self.db = db
        self.scanner = scanner
        self.analyzer = analyzer
        self.crafter = crafter
        self.publisher = publisher
        self.app = web.Application(middlewares=[self._cors_middleware, self._rate_limit_middleware])
        self._setup_routes()
        self._request_counts: dict[str, list[float]] = {}

    def _setup_routes(self) -> None:
        self.app.router.add_post("/analyze", self.handle_analyze)
        self.app.router.add_post("/scan", self.handle_scan)
        self.app.router.add_get("/queue", self.handle_queue)
        self.app.router.add_post("/approve/{id}", self.handle_approve)
        self.app.router.add_get("/archive", self.handle_archive)
        self.app.router.add_get("/stats", self.handle_stats)
        self.app.router.add_get("/health", self.handle_health)

    @web.middleware
    async def _cors_middleware(self, request: web.Request, handler) -> web.Response:
        if request.method == "OPTIONS":
            response = web.Response(status=204)
        else:
            response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @web.middleware
    async def _rate_limit_middleware(self, request: web.Request, handler) -> web.Response:
        """Simple in-memory rate limiter: 60 requests/minute per IP."""
        import time
        ip = request.remote or "unknown"
        now = time.time()
        window = 60

        if ip not in self._request_counts:
            self._request_counts[ip] = []

        # Prune old entries
        self._request_counts[ip] = [t for t in self._request_counts[ip] if now - t < window]

        if len(self._request_counts[ip]) >= 60:
            return web.json_response(
                {"error": "Rate limit exceeded. Max 60 requests/minute."},
                status=429,
            )

        self._request_counts[ip].append(now)
        return await handler(request)

    async def handle_analyze(self, request: web.Request) -> web.Response:
        """POST /analyze — Submit a statement for analysis, returns Strike JSON."""
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        statement_text = sanitize_input(body.get("statement", ""))
        if not statement_text:
            return web.json_response(
                {"error": "Missing required field: statement"}, status=400
            )

        target_name = sanitize_input(body.get("target", "Unknown"))
        target_role = sanitize_input(body.get("role", "Unknown"))
        target_type = body.get("type", "person")
        source_url = sanitize_input(body.get("source_url", ""))
        date = sanitize_input(body.get("date", ""))
        style = body.get("style", "")

        # Stage T — Scan
        scan_result = self.scanner.scan_statement(
            text=statement_text,
            target_name=target_name,
            target_role=target_role,
            target_type=target_type,
            source_url=source_url,
            date=date,
        )

        if not scan_result:
            return web.json_response(
                {"error": "Statement does not contain verifiable factual claims",
                 "confidence": "below_threshold"},
                status=422,
            )

        target = scan_result["target"]
        statement = scan_result["statement"]

        # Stage A — Analyze
        analysis = self.analyzer.analyze(target, statement)

        # Stage C — Craft
        strike = await self.crafter.craft(
            target=target,
            statement=statement,
            evidence=analysis["evidence"],
            style=style,
        )

        # Stage O — Output
        report_id = self.publisher.queue_for_review(strike)

        result = strike.to_dict()
        result["queued_for_review"] = self.config.review_required
        return web.json_response(result, status=201)

    async def handle_scan(self, request: web.Request) -> web.Response:
        """POST /scan — Start monitoring a target."""
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        target_name = sanitize_input(body.get("target_name", ""))
        if not target_name:
            return web.json_response(
                {"error": "Missing required field: target_name"}, status=400
            )

        twitter_handle = sanitize_input(body.get("twitter_handle", ""))
        keywords = body.get("keywords", [])
        if isinstance(keywords, list):
            keywords = [sanitize_input(k) for k in keywords]

        target_id = self.db.add_scan_target(
            name=target_name,
            twitter_handle=twitter_handle,
            keywords=keywords,
        )

        return web.json_response({
            "status": "scanning",
            "target_name": target_name,
            "target_id": target_id,
        }, status=201)

    async def handle_queue(self, request: web.Request) -> web.Response:
        """GET /queue — Get pending Strike drafts awaiting review."""
        queue = self.publisher.get_queue()
        return web.json_response({"pending": queue, "count": len(queue)})

    async def handle_approve(self, request: web.Request) -> web.Response:
        """POST /approve/{id} — Approve a Strike for publication."""
        strike_id = request.match_info.get("id", "")
        if not strike_id:
            return web.json_response(
                {"error": "Missing strike ID"}, status=400
            )

        result = self.publisher.approve(strike_id)
        if result is None:
            return web.json_response(
                {"error": "Strike not found", "strike_id": strike_id}, status=404
            )

        return web.json_response({
            "published": True,
            "strike_id": strike_id,
            "strike": result,
        })

    async def handle_archive(self, request: web.Request) -> web.Response:
        """GET /archive — Get all published Strikes."""
        archive = self.publisher.get_archive()
        return web.json_response({"strikes": archive, "count": len(archive)})

    async def handle_stats(self, request: web.Request) -> web.Response:
        """GET /stats — Get agent statistics."""
        stats = self.publisher.get_stats()
        stats["agent_id"] = "prinzclaw-agent"
        stats["version"] = "1.0.0"
        return web.json_response(stats)

    async def handle_health(self, request: web.Request) -> web.Response:
        """GET /health — Agent health check."""
        return web.json_response({
            "status": "operational",
            "agent": "prinzclaw",
            "version": "1.0.0",
            "protocol": "openclaw-v1",
            "port": self.config.gateway_port,
        })

    def run(self) -> None:
        """Start the gateway server."""
        host = self.config.gateway_host
        port = self.config.gateway_port
        logger.info("prinzclaw gateway starting on %s:%d", host, port)
        web.run_app(self.app, host=host, port=port, print=None)
