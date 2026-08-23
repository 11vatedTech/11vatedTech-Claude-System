"""``growthos`` command-line interface.

Commands: doctor, setup (ai/database/gmail/linkedin/sms/remote-access), migrate,
api, worker.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess

import typer

from growthos.cli.doctor import format_doctor, run_doctor
from growthos.config import get_settings

app = typer.Typer(
    name="growthos",
    help="11vatedTech GrowthOS — local-first commercial intelligence OS",
    no_args_is_help=True,
)

setup_app = typer.Typer(help="Guided setup", no_args_is_help=True)
app.add_typer(setup_app, name="setup")


@app.command()
def doctor(tests: bool = typer.Option(False, "--tests", help="Validate PostgreSQL-backed integration test infrastructure")) -> None:
    """Validate the environment and report PASS/FAIL/BLOCKED."""
    typer.echo(format_doctor(run_doctor(include_tests=tests)))
    if tests:
        from growthos.cli.doctor import CheckStatus
        checks = run_doctor(include_tests=True)
        if any(c.name == "Test database" and c.status != CheckStatus.PASS for c in checks):
            raise typer.Exit(1)


@app.command()
def migrate() -> None:
    """Apply database migrations."""
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    typer.echo("Migrations applied.")


@app.command()
def reclassify() -> None:
    """Reclassify all real Gmail evidence and rebuild the Founder Inbox.

    Recomputes structured commercial classification for every stored message
    and re-runs the pipeline-scoped Founder Inbox gate. Source evidence and
    Communications records are preserved. Prints a classification report.
    """
    import asyncio
    import json

    from growthos.db import build_engine, build_session_factory
    from growthos.services.reclassify import reclassify_all

    engine = build_engine()
    factory = build_session_factory(engine)

    async def run() -> None:
        async with factory() as session:
            report = await reclassify_all(session)
            await session.commit()
        typer.echo(json.dumps(report, indent=2, default=str))

    asyncio.run(run())


@app.command()
def api(host: str | None = None, port: int | None = None) -> None:
    """Run the authenticated API server."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "growthos.api.app:app",
        host=host or settings.api_host,
        port=port or settings.api_port,
        reload=False,
    )


@app.command()
def worker(poll_seconds: float = 1.0) -> None:
    """Run the persistent job worker loop."""
    import asyncio

    import growthos.workers.handlers  # noqa: F401  (registers job handlers)
    from growthos.db import build_engine, build_session_factory
    from growthos.workers.handlers import ensure_scheduled
    from growthos.workers.jobs import JobWorker

    engine = build_engine()
    factory = build_session_factory(engine)
    worker = JobWorker(factory, poll_seconds=poll_seconds)

    async def bootstrap() -> None:
        async with factory() as session:
            from growthos.config import get_settings
            from growthos.integrations.gmail_oauth import load_refresh_token

            settings = get_settings()
            await ensure_scheduled(
                session,
                "session.cleanup",
                settings.session_cleanup_interval_seconds,
                idempotency_key="session.cleanup.recurring",
            )
            # Only schedule Gmail sync when the founder has authorized Gmail;
            # otherwise it would fail-retry until dead-letter.
            if load_refresh_token():
                await ensure_scheduled(
                    session,
                    "gmail.sync",
                    settings.gmail_sync_interval_seconds,
                    idempotency_key="gmail.sync.recurring",
                )
            # Revenue Scout recurring loops.
            await ensure_scheduled(
                session,
                "scout.daily",
                settings.scout_daily_interval_seconds,
                idempotency_key="scout.daily.recurring",
            )
            await ensure_scheduled(
                session,
                "scout.light",
                settings.scout_light_interval_seconds,
                idempotency_key="scout.light.recurring",
            )
            await session.commit()

    async def run_all() -> None:
        # Bootstrap and the worker loop MUST share one event loop: the async
        # engine pools connections per loop, so a second asyncio.run() would
        # reuse closed-loop connections and crash with "Event loop is closed".
        await bootstrap()
        typer.echo(f"Worker started (poll={poll_seconds}s). Ctrl+C to stop.")
        await worker.run()

    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        worker.stop()
        typer.echo("Worker stopped.")


@app.command()
def capability_intelligence(
    root: str | None = typer.Option(None, "--root", help="Trusted local repository root"),
) -> None:
    """Inspect configured trusted repositories and propose capabilities."""
    import asyncio
    import json
    from pathlib import Path

    from growthos.db import build_engine, build_session_factory
    from growthos.domain.models_capability import TrustedRepositoryRoot
    from growthos.intelligence.capability import inspect_trusted_root
    from growthos.shared.ids import new_id

    async def run() -> None:
        engine = build_engine()
        factory = build_session_factory(engine)
        async with factory() as session:
            if root:
                path = Path(root).expanduser().resolve()
                if not path.is_dir():
                    raise typer.BadParameter("Root must be an existing directory")
                row = (await session.execute(__import__('sqlalchemy', fromlist=['select']).select(TrustedRepositoryRoot).where(TrustedRepositoryRoot.path == str(path)))).scalar_one_or_none()
                if row is None:
                    row = TrustedRepositoryRoot(id=new_id(), path=str(path), label="CLI trusted root")
                    session.add(row)
                    await session.flush()
            else:
                row = (await session.execute(__import__('sqlalchemy', fromlist=['select']).select(TrustedRepositoryRoot).where(TrustedRepositoryRoot.enabled.is_(True)))).scalars().first()
                if row is None:
                    typer.echo("No trusted repository root configured. Pass --root PATH.")
                    return
            report = await inspect_trusted_root(session, row)
            await session.commit()
            typer.echo(json.dumps(report, indent=2, default=str))

    asyncio.run(run())


@app.command()
def capability_activation(
    confirm_sprite: bool = typer.Option(False, "--confirm-sprite", help="Edit & Confirm the sprite capability per the founder decision"),
    reject_frontend: bool = typer.Option(False, "--reject-frontend", help="Reject the frontend proposal for GSPL-Sprites evidence"),
    activate: bool = typer.Option(False, "--activate", help="Run the downstream pipeline for the confirmed capability"),
    discover: bool = typer.Option(False, "--discover", help="Run the bounded capability-driven discovery experiment"),
    process_events: bool = typer.Option(False, "--process-events", help="Process pending Capability Canon events"),
    limit: int = typer.Option(15, "--limit", help="Max organizations for the discovery experiment"),
) -> None:
    """Apply the founder Capability decision and run the activation pipeline.

    Examples:
      growthos capability-activation --confirm-sprite --reject-frontend
      growthos capability-activation --activate
      growthos capability-activation --discover --limit 15
      growthos capability-activation --process-events
    """
    import asyncio
    import json

    from sqlalchemy import select

    from growthos.db import build_engine, build_session_factory
    from growthos.domain.models_scout import CapabilityCanon
    from growthos.services.capability_activation import (
        FRONTEND_PROPOSAL_NAME,
        FRONTEND_REJECT_REASON,
        SPRITE_CANONICAL_DEFINITION,
        SPRITE_CANONICAL_NAME,
        SPRITE_EXTERNAL_SUMMARY,
        SPRITE_LIMITATIONS,
        SPRITE_PROPOSAL_NAME,
        activate_capability,
        confirm_capability,
        process_canon_events,
        reject_capability,
        run_capability_discovery,
    )

    engine = build_engine()
    factory = build_session_factory(engine)

    async def main() -> None:
        async with factory() as session:
            if confirm_sprite:
                cap = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.name == SPRITE_PROPOSAL_NAME))).scalar_one_or_none()
                if cap is None:
                    typer.echo(f"FAIL: proposal '{SPRITE_PROPOSAL_NAME}' not found")
                    raise typer.Exit(1)
                await confirm_capability(
                    session, cap,
                    name=SPRITE_CANONICAL_NAME,
                    definition=SPRITE_CANONICAL_DEFINITION,
                    maturity="PROTOTYPE_PROVEN",
                    limitations=SPRITE_LIMITATIONS,
                    external_summary=SPRITE_EXTERNAL_SUMMARY,
                    note="Founder Edit & Confirm: canonized with narrowed prototype scope.",
                )
                typer.echo(f"CONFIRMED: {cap.name} (FOUNDER_CONFIRMED, external_claimable=True)")
            if reject_frontend:
                cap = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.name == FRONTEND_PROPOSAL_NAME))).scalar_one_or_none()
                if cap is None:
                    typer.echo(f"WARN: proposal '{FRONTEND_PROPOSAL_NAME}' not found (already handled?)")
                else:
                    await reject_capability(session, cap, reason=FRONTEND_REJECT_REASON)
                    typer.echo(f"REJECTED: {cap.name} (REJECTED for this evidence chain)")
            if activate:
                cap = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.name == SPRITE_CANONICAL_NAME))).scalar_one_or_none()
                if cap is None:
                    typer.echo("FAIL: confirmed capability not found; run --confirm-sprite first")
                    raise typer.Exit(1)
                report = await activate_capability(session, cap)
                typer.echo(json.dumps(report, indent=2, default=str))
            if discover:
                cap = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.name == SPRITE_CANONICAL_NAME))).scalar_one_or_none()
                if cap is None:
                    typer.echo("FAIL: confirmed capability not found; run --confirm-sprite first")
                    raise typer.Exit(1)
                report = await run_capability_discovery(session, cap, limit=limit)
                typer.echo(json.dumps(report, indent=2, default=str))
            if process_events:
                report = await process_canon_events(session)
                typer.echo(json.dumps(report, indent=2, default=str))
            await session.commit()

    asyncio.run(main())


@app.command()
def entity_resolution(
    reclassify: bool = typer.Option(False, "--reclassify", help="Reclassify GitHub discoveries into Discovery Candidates"),
    enrich: bool = typer.Option(False, "--enrich", help="Run the real commercial-entity enrichment + qualification pass"),
    market: str = typer.Option("2D indie & mobile game studios", "--market", help="Market to reassess"),
) -> None:
    """Commercial Entity Resolution + Buyer Qualification.

    Moves GitHub discoveries out of the prospect funnel into the pre-prospect
    DiscoveryCandidate layer, enriches each candidate honestly, and computes
    source effectiveness + market reassessment. No outbound is ever sent.
    """
    import asyncio
    import json

    from growthos.db import build_engine, build_session_factory
    from growthos.services.entity_resolution import (
        reassess_market,
        reclassify_github_prospects,
        run_enrichment_pass,
    )

    engine = build_engine()
    factory = build_session_factory(engine)

    async def main() -> None:
        async with factory() as session:
            if reclassify and not enrich:
                report = await reclassify_github_prospects(session)
                await session.commit()
                typer.echo(json.dumps(report, indent=2, default=str))
                return
            if enrich:
                report = await run_enrichment_pass(session, market=market)
                await session.commit()
                typer.echo(json.dumps(report, indent=2, default=str))
                return
            result = await reassess_market(session, market, source="github")
            await session.commit()
            typer.echo(json.dumps(result, indent=2, default=str))

    asyncio.run(main())


@app.command()
def portfolio_census(
    run: bool = typer.Option(False, "--run", help="Enumerate + census both authorized GitHub profiles"),
) -> None:
    """GitHub Portfolio Evidence Census (read-only, founder-authorized).

    Enumerates public repositories under the authorized profiles
    (11vatedTech, 11vated), classifies evidence strength, scores repositories,
    clusters project families, and generates PROPOSED cross-project capability
    candidates. Nothing is modified and no capability is auto-confirmed.
    """
    import asyncio
    import json

    from growthos.db import build_engine, build_session_factory
    from growthos.services.portfolio_census import census_report, run_full_census

    engine = build_engine()
    factory = build_session_factory(engine)

    async def main() -> None:
        async with factory() as session:
            if run:
                report = await run_full_census(session)
                await session.commit()
            else:
                report = await census_report(session)
                await session.commit()
            typer.echo(json.dumps(report, indent=2, default=str))

    asyncio.run(main())


@app.command()
def portfolio_deep_evidence(
    run: bool = typer.Option(False, "--run", help="Run deep evidence analysis on 8 selected repositories"),
    report: bool = typer.Option(False, "--report", help="Show current deep evidence status and founder review"),
) -> None:
    """Portfolio Deep Evidence — multi-project verification before Capability Canon expansion.

    Fetches actual file contents from GitHub, performs lightweight code analysis,
    reassesses proposals, and produces a founder review report. No capability
    is auto-confirmed.

    Examples:
      growthos portfolio-deep-evidence --run
      growthos portfolio-deep-evidence --report
    """
    import asyncio
    import json

    from growthos.db import build_engine, build_session_factory

    engine = build_engine()
    factory = build_session_factory(engine)

    async def main() -> None:
        async with factory() as session:
            if run or report:
                from growthos.services.portfolio_deep_evidence import (
                    run_portfolio_deep_evidence_pass,
                )
                result = await run_portfolio_deep_evidence_pass(session)
                await session.commit()
                typer.echo(json.dumps(result, indent=2, default=str))
            else:
                typer.echo("Usage: growthos portfolio-deep-evidence --run | --report")

    asyncio.run(main())


@app.command()
def mirror(
    run: bool = typer.Option(False, "--run", help="Run local deep analysis on all selected repositories"),
    status: bool = typer.Option(False, "--status", help="Show mirror status for all repositories"),
    repo: str = typer.Option("", "--repo", help="Analyze a specific repository (owner/name)"),
    safety: bool = typer.Option(False, "--safety", help="Run safety checks on all mirrors"),
    rebuild: bool = typer.Option(False, "--rebuild", help="Rebuild capability recommendations from local evidence"),
) -> None:
    """Evidence Mirror — local deep analysis without GitHub API rate limits.

    Clones public repos as shallow read-only mirrors, performs filesystem-aware
    semantic analysis, and persists evidence for Capability Canon decisions.

    Examples:
      growthos mirror --status        # show mirror states
      growthos mirror --run           # analyze all 8 selected repos locally
      growthos mirror --repo 11vated/Nexus  # analyze one repo
      growthos mirror --safety        # verify all mirrors are safe
      growthos mirror --rebuild       # rebuild capability recommendations
    """
    import asyncio
    import json

    from growthos.db import build_engine, build_session_factory

    engine = build_engine()
    factory = build_session_factory(engine)

    async def main() -> None:
        async with factory() as session:
            if status:
                from sqlalchemy import select as sa_select

                from growthos.domain.models_capability import EvidenceMirror
                mirrors = list((await session.execute(sa_select(EvidenceMirror))).scalars().all())
                if not mirrors:
                    typer.echo("No evidence mirrors found.")
                else:
                    for m in mirrors:
                        state_icon = {
                            "READY": "✅", "CLONING": "⏳", "NOT_MIRRORED": "⬜",
                            "STALE": "⚠️", "FETCH_FAILED": "❌",
                            "REMOTE_UNAVAILABLE": "🔴", "CORRUPT": "💥",
                        }.get(m.mirror_state, "?")
                        typer.echo(
                            f"{state_icon} {m.full_name}: {m.mirror_state} "
                            f"(branch={m.default_branch}, sha={m.remote_commit_sha or 'N/A'[:8]}, "
                            f"files={m.files_discovered}, analysis={m.last_deep_analysis_at or 'never'})"
                        )
                return

            if safety:
                from growthos.domain.models_capability import EvidenceMirror
                from growthos.intelligence.evidence_mirror import (
                    verify_mirror_safety,
                    verify_no_remote_mutation,
                )
                mirrors = list((await session.execute(sa_select(EvidenceMirror))).scalars().all())
                for m in mirrors:
                    if m.mirror_state != "READY":
                        continue
                    safety_result = await verify_mirror_safety(m)
                    mutation_result = await verify_no_remote_mutation(m)
                    typer.echo(f"\n{m.full_name}:")
                    typer.echo(f"  Safety: {json.dumps(safety_result, indent=4)}")
                    typer.echo(f"  Mutation: {json.dumps(mutation_result, indent=4)}")
                return

            if repo:
                owner, name = repo.split("/", 1) if "/" in repo else ("", repo)
                if not owner:
                    typer.echo("Error: --repo must be owner/name format")
                    return
                from sqlalchemy import select as sa_select

                from growthos.domain.models_capability import RepositoryEvidence

                # Find or create repo evidence
                repo_ev = (
                    await session.execute(
                        sa_select(RepositoryEvidence).where(RepositoryEvidence.full_name == repo)
                    )
                ).scalar_one_or_none()
                if not repo_ev:
                    typer.echo(f"Repository {repo} not found in census. Run census first.")
                    return

                from growthos.services.evidence_mirror_service import run_local_deep_analysis
                result = await run_local_deep_analysis(session, repo_ev)
                await session.commit()
                typer.echo(json.dumps(result, indent=2, default=str))
                return

            if rebuild:
                from growthos.services.evidence_mirror_service import (
                    rebuild_capability_recommendations,
                )
                result = await rebuild_capability_recommendations(session)
                await session.commit()
                typer.echo(json.dumps(result, indent=2, default=str))
                return

            if run:
                from growthos.services.evidence_mirror_service import run_full_local_deep_pass
                result = await run_full_local_deep_pass(session)
                await session.commit()
                typer.echo(json.dumps(result, indent=2, default=str))
            else:
                typer.echo("Usage: growthos mirror --run | --status | --repo owner/name | --safety | --rebuild")

    asyncio.run(main())


@app.command()
def attribution(
    run: bool = typer.Option(False, "--run", help="Run the full capability evidence attribution pass"),
) -> None:
    """Capability Evidence Attribution — precise file/subsystem→capability linking.

    Replaces broad file-count attribution with per-file directness classes.
    Shows exact evidence numerator and denominator for each capability.

    Examples:
      growthos attribution --run   # attribute all capabilities from mirror evidence
    """
    import asyncio
    import json

    from growthos.db import build_engine, build_session_factory

    engine = build_engine()
    factory = build_session_factory(engine)

    async def main() -> None:
        async with factory() as session:
            if run:
                from growthos.services.capability_attribution_service import (
                    run_capability_attribution_pass,
                )
                result = await run_capability_attribution_pass(session)
                await session.commit()
                typer.echo(json.dumps(result, indent=2, default=str))
            else:
                typer.echo("Usage: growthos attribution --run")

    asyncio.run(main())


@app.command()
def scout(
    run: bool = typer.Option(False, "--run", help="Run one discovery pass now"),
    brief: bool = typer.Option(False, "--brief", help="Print the founder brief"),
    requalify: bool = typer.Option(False, "--requalify", help="Requalify existing real prospects"),
    limit: int = typer.Option(20, "--limit", help="Max organizations to discover"),
) -> None:
    """Revenue Scout — run discovery or print the founder brief.

    Examples:
      growthos scout --run            # discover + score real organizations
      growthos scout --run --limit 5  # smaller pass
      growthos scout --brief          # founder brief (pipeline, actions)
      growthos scout --requalify      # bounded public-web qualification cohort
    """
    import asyncio
    import json

    from growthos.db import build_engine, build_session_factory
    from growthos.services.scout import build_founder_brief, requalify_cohort, run_discovery

    engine = build_engine()
    factory = build_session_factory(engine)

    async def main() -> None:
        async with factory() as session:
            if run:
                report = await run_discovery(session, limit=limit, run_type="manual")
                await session.commit()
                typer.echo(json.dumps(report, indent=2, default=str))
            elif requalify:
                report = await requalify_cohort(session, limit=limit, actor="founder")
                await session.commit()
                typer.echo(json.dumps(report, indent=2, default=str))
            elif brief:
                b = await build_founder_brief(session)
                await session.commit()
                typer.echo(json.dumps(b, indent=2, default=str))
            else:
                typer.echo("Usage: growthos scout --run | --requalify | --brief [--limit N]")

    asyncio.run(main())


# ---------------------------------------------------------------------------
# Setup subcommands
# ---------------------------------------------------------------------------


@setup_app.command()
def ai(pull: bool = typer.Option(False, help="Pull the default local models")) -> None:
    """Configure and inspect local AI (Ollama)."""
    import httpx

    settings = get_settings()
    base = settings.ollama_base_url
    try:
        tags = httpx.get(f"{base}/api/tags", timeout=5)
        tags.raise_for_status()
        models = [m["name"] for m in tags.json().get("models", [])]
        typer.echo(f"Ollama reachable at {base}. Installed models:")
        for name in models:
            typer.echo(f"  - {name}")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"FAIL: Ollama unreachable at {base}: {exc}")
        raise typer.Exit(1) from exc

    for model in (settings.ollama_fast_model, settings.ollama_embedding_model):
        if model in models:
            typer.echo(f"PASS: {model} present.")
        elif pull:
            typer.echo(f"Pulling {model} ...")
            subprocess.run(["ollama", "pull", model], check=False)
        else:
            typer.echo(
                f"NOT CONFIGURED: {model} missing. Run "
                f"`growthos setup ai --pull` to download (~GBs, free/open)."
            )


@setup_app.command()
def database() -> None:
    """Provision the growthos database role and database."""
    pg_bin = _find_psql()
    if not pg_bin:
        typer.echo("BLOCKED: psql not found. Install PostgreSQL and retry.")
        raise typer.Exit(1)

    host = typer.prompt("PostgreSQL host", default="localhost")
    port = typer.prompt("PostgreSQL port", default="5433")
    admin_user = typer.prompt("PostgreSQL superuser", default="postgres")
    admin_password = typer.prompt(
        "PostgreSQL superuser password", hide_input=True
    )
    db_user = typer.prompt("GrowthOS DB user", default="growthos")
    db_password = typer.prompt(
        "GrowthOS DB password", default="growthos", hide_input=True
    )
    db_name = typer.prompt("GrowthOS DB name", default="growthos")

    env = {"PGPASSWORD": admin_password}
    sql = (
        f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = "
        f"'{db_user}') THEN CREATE ROLE {db_user} LOGIN PASSWORD "
        f"'{db_password}'; END IF; END $$;"
    )
    result = subprocess.run(
        [pg_bin, "-h", host, "-p", port, "-U", admin_user, "-c", sql],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        typer.echo(f"FAIL creating role: {result.stderr}")
        raise typer.Exit(1)

    create_db = subprocess.run(
        [pg_bin, "-h", host, "-p", port, "-U", admin_user, "-tc",
         f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"],
        env=env, capture_output=True, text=True,
    )
    if "1" not in create_db.stdout:
        subprocess.run(
            [pg_bin, "-h", host, "-p", port, "-U", admin_user, "-c",
             f'CREATE DATABASE {db_name} OWNER {db_user};'],
            env=env, capture_output=True, text=True,
        )

    typer.echo(
        f"Database ready. Set DATABASE_URL="
        f"postgresql+asyncpg://{db_user}:****@{host}:{port}/{db_name} "
        f"in .env and run `growthos migrate`."
    )


@setup_app.command()
def gmail() -> None:
    """Guide Gmail OAuth setup using the Desktop App loopback flow.

    Binds a temporary localhost callback, opens the default browser, captures
    the authorization code automatically, exchanges it server-side, stores
    credentials in the OS keychain, and verifies the connected account.
    No codes are ever copied or pasted.
    """
    import asyncio

    from growthos.integrations import gmail_oauth
    from growthos.integrations.gmail import GmailClient

    secret_path = gmail_oauth.client_secret_path()
    if not secret_path.is_file():
        typer.echo("BLOCKED: Gmail client secret not found.")
        typer.echo("Steps to reach this point (do these in Google Cloud Console):")
        typer.echo("  1. Create/select a Google Cloud project at console.cloud.google.com")
        typer.echo("  2. Enable the Gmail API")
        typer.echo("  3. Configure the OAuth consent screen; add your address as an "
                   "authorized/test user where required")
        typer.echo("  4. Create an OAuth 2.0 client (Desktop app type)")
        typer.echo("  5. Download the client_secret JSON and save it as: "
                   f"{secret_path} (gitignored)")
        typer.echo("Publishing-state warning: if the consent project is in "
                   "'Testing', refresh tokens expire after 7 days.")
        raise typer.Exit(1)

    try:
        gmail_oauth.load_client_secret()
    except gmail_oauth.GmailSetupError as exc:
        typer.echo(f"FAIL: {exc}")
        raise typer.Exit(1) from exc

    typer.echo("Scopes requested (least privilege, no gmail.modify):")
    for scope in gmail_oauth.GMAIL_SCOPES:
        typer.echo(f"  - {scope}")

    existing = gmail_oauth.load_refresh_token()
    if existing:
        typer.echo("A refresh token is already stored in the OS keychain.")
        if not typer.confirm("Re-authorize anyway?"):
            raise typer.Exit(0)

    typer.echo("Starting loopback OAuth (Desktop App flow)...")
    typer.echo("Your default browser will open; authorize GrowthOS there.")
    typer.echo("If it does not open, open this link manually:")
    try:
        tokens = asyncio.run(
            gmail_oauth.perform_loopback_flow(
                on_auth_url=lambda url: typer.echo(url)
            )
        )
    except (gmail_oauth.StateMismatchError, gmail_oauth.OAuthCallbackError) as exc:
        typer.echo(f"FAIL: {exc}")
        raise typer.Exit(1) from exc
    except gmail_oauth.CallbackTimeoutError as exc:
        typer.echo(f"FAIL: {exc}")
        raise typer.Exit(1) from exc

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        typer.echo("FAIL: no refresh token was returned.")
        raise typer.Exit(1)
    typer.echo("   Tokens stored in the OS keychain (never in the repo).")

    typer.echo("Verifying the connected account with a real API call...")
    try:
        fresh = asyncio.run(gmail_oauth.refresh_access_token(refresh_token))
        profile = asyncio.run(GmailClient(fresh).profile())
        typer.echo(f"   CONNECTED as: {profile.get('emailAddress')}")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"   FAIL: profile check failed: {exc}")
        raise typer.Exit(1) from exc
    typer.echo("\nGmail OAuth complete. Run `growthos worker` to start syncing.")


@setup_app.command()
def linkedin() -> None:
    """Guide LinkedIn developer-app setup (real approval required)."""
    typer.echo("LinkedIn setup — IMPLEMENTED, awaiting real OAuth/product approval.")
    typer.echo("Steps:")
    typer.echo("  1. Create a LinkedIn developer application")
    typer.echo("  2. Request the products you actually need (e.g. Sign In with LinkedIn)")
    typer.echo("  3. Configure redirect URIs")
    typer.echo("  4. Store client credentials via `growthos setup linkedin --authorize`")
    typer.echo("No scraping, no automated connection requests, no bulk DMs.")


@setup_app.command()
def sms() -> None:
    """Report SMS gateway hardware truth."""
    typer.echo(
        "SMS BRIDGE — BLOCKED: compatible gateway hardware/SIM required."
    )
    typer.echo("Preferred architecture: Android SMS Gateway device + SIM.")
    typer.echo("The iPhone texts the Android gateway number; no Twilio.")
    typer.echo("If no device+SIM is available, SMS remains BLOCKED (truthful).")


@setup_app.command()
def remote_access() -> None:
    """Guide private remote access (Tailscale)."""
    typer.echo("Remote access — use Tailscale (private device network).")
    typer.echo("  1. Install Tailscale and sign in on the workstation")
    typer.echo("  2. Install Tailscale on the founder phone")
    typer.echo("  3. Access GrowthOS at the workstation's Tailscale IP")
    typer.echo("Never expose PostgreSQL/Ollama/workers to the public internet.")


def _find_psql() -> str | None:
    candidates = [
        r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
    ]
    for candidate in candidates:
        if pathlib.Path(candidate).exists():
            return candidate
    return shutil.which("psql")


if __name__ == "__main__":
    app()
