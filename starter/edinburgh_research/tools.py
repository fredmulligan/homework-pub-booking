"""Ex5 tools. Four tools the agent uses to research an Edinburgh booking.

Each tool:
  1. Reads its fixture from sample_data/ (DO NOT modify the fixtures).
  2. Logs its arguments and output into _TOOL_CALL_LOG (see integrity.py).
  3. Returns a ToolResult with success=True/False, output=dict, summary=str.

The grader checks for:
  * Correct parallel_safe flags (reads True, generate_flyer False).
  * Every tool's results appear in _TOOL_CALL_LOG.
  * Tools fail gracefully on missing fixtures or bad inputs (ToolError,
    not RuntimeError).
"""

from __future__ import annotations

import json
from pathlib import Path

from sovereign_agent.errors import ToolError
from sovereign_agent.session.directory import Session
from sovereign_agent.tools.registry import ToolRegistry, ToolResult, _RegisteredTool

from starter.edinburgh_research.integrity import record_tool_call

_SAMPLE_DATA = Path(__file__).parent / "sample_data"


# ---------------------------------------------------------------------------
# TODO 1 — venue_search  (Implemented — Claude)
# ---------------------------------------------------------------------------
def venue_search(near: str, party_size: int, budget_max_gbp: int = 1000) -> ToolResult:
    """Search for Edinburgh venues near <near> that can seat the party."""
    fixture = _SAMPLE_DATA / "venues.json"
    if not fixture.exists():
        # The grader can plant a missing fixture to test our failure handling.
        # Return success=False with a ToolError, don't crash.
        err = ToolError(
            code="SA_TOOL_DEPENDENCY_MISSING",
            message=f"venues.json fixture missing at {fixture}",
        )
        return ToolResult(success=False, output={}, summary=str(err), error=err)

    venues = json.loads(fixture.read_text(encoding="utf-8"))

    near_lower = (near or "").lower()
    results = [
        v
        for v in venues
        if v.get("open_now")
        and near_lower in v.get("area", "").lower()
        and v.get("seats_available_evening", 0) >= party_size
        and (v.get("hire_fee_gbp", 0) + v.get("min_spend_gbp", 0)) <= budget_max_gbp
    ]

    output = {
        "near": near,
        "party_size": party_size,
        "results": results,
        "count": len(results),
    }
    summary = f"venue_search({near}, party={party_size}): {len(results)} result(s)"

    # Log before returning so the integrity check can verify the output.
    record_tool_call(
        "venue_search",
        {"near": near, "party_size": party_size, "budget_max_gbp": budget_max_gbp},
        output,
    )
    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# TODO 2 — get_weather  (Implemented — Claude)
# ---------------------------------------------------------------------------
def get_weather(city: str, date: str) -> ToolResult:
    """Look up the scripted weather for <city> on <date> (YYYY-MM-DD)."""
    fixture = _SAMPLE_DATA / "weather.json"
    if not fixture.exists():
        err = ToolError(
            code="SA_TOOL_DEPENDENCY_MISSING",
            message=f"weather.json fixture missing at {fixture}",
        )
        return ToolResult(success=False, output={}, summary=str(err), error=err)

    data = json.loads(fixture.read_text(encoding="utf-8"))
    city_key = (city or "").lower()

    if city_key not in data:
        err = ToolError(
            code="SA_TOOL_INVALID_INPUT",
            message=f"no weather data for city '{city}' (known: {list(data.keys())})",
        )
        return ToolResult(success=False, output={}, summary=str(err), error=err)

    if date not in data[city_key]:
        err = ToolError(
            code="SA_TOOL_INVALID_INPUT",
            message=f"no weather data for {city} on {date}",
        )
        return ToolResult(success=False, output={}, summary=str(err), error=err)

    forecast = data[city_key][date]
    output = {
        "city": city,
        "date": date,
        "condition": forecast["condition"],
        "temperature_c": forecast["temperature_c"],
        "precip_mm": forecast.get("precip_mm", 0.0),
        "wind_kph": forecast.get("wind_kph", 0),
    }
    summary = f"get_weather({city}, {date}): {forecast['condition']}, {forecast['temperature_c']}C"

    record_tool_call("get_weather", {"city": city, "date": date}, output)
    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# TODO 3 — calculate_cost  (Implemented — Claude)
# ---------------------------------------------------------------------------
def calculate_cost(
    venue_id: str,
    party_size: int,
    duration_hours: int,
    catering_tier: str = "bar_snacks",
) -> ToolResult:
    """Compute the total cost for a booking."""
    catering_path = _SAMPLE_DATA / "catering.json"
    venues_path = _SAMPLE_DATA / "venues.json"
    for p in (catering_path, venues_path):
        if not p.exists():
            err = ToolError(
                code="SA_TOOL_DEPENDENCY_MISSING",
                message=f"required fixture missing: {p.name}",
            )
            return ToolResult(success=False, output={}, summary=str(err), error=err)

    catering = json.loads(catering_path.read_text(encoding="utf-8"))
    venues = json.loads(venues_path.read_text(encoding="utf-8"))
    venue = next((v for v in venues if v["id"] == venue_id), None)

    if venue is None:
        err = ToolError(
            code="SA_TOOL_INVALID_INPUT",
            message=f"unknown venue_id '{venue_id}'",
        )
        return ToolResult(success=False, output={}, summary=str(err), error=err)

    rates = catering["base_rates_gbp_per_head"]
    if catering_tier not in rates:
        err = ToolError(
            code="SA_TOOL_INVALID_INPUT",
            message=f"unknown catering_tier '{catering_tier}' (known: {list(rates.keys())})",
        )
        return ToolResult(success=False, output={}, summary=str(err), error=err)

    base_per_head = rates[catering_tier]
    venue_mult = catering["venue_modifiers"].get(venue_id, 1.0)
    service_pct = catering["service_charge_percent"]

    # Per docstring formula:
    subtotal = base_per_head * venue_mult * party_size * max(1, duration_hours)
    service = subtotal * service_pct / 100.0
    total = subtotal + service + venue.get("hire_fee_gbp", 0) + venue.get("min_spend_gbp", 0)

    # Deposit rule from deposit_policy thresholds.
    if total < 300:
        deposit = 0
    elif total <= 1000:
        deposit = int(round(total * 0.20))
    else:
        deposit = int(round(total * 0.30))

    output = {
        "venue_id": venue_id,
        "party_size": party_size,
        "duration_hours": duration_hours,
        "catering_tier": catering_tier,
        "subtotal_gbp": int(round(subtotal)),
        "service_gbp": int(round(service)),
        "total_gbp": int(round(total)),
        "deposit_required_gbp": deposit,
    }
    summary = (
        f"calculate_cost({venue_id}, party={party_size}): "
        f"total £{output['total_gbp']}, deposit £{output['deposit_required_gbp']}"
    )

    record_tool_call(
        "calculate_cost",
        {
            "venue_id": venue_id,
            "party_size": party_size,
            "duration_hours": duration_hours,
            "catering_tier": catering_tier,
        },
        output,
    )
    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# TODO 4 — generate_flyer  (Implemented — Claude)
# ---------------------------------------------------------------------------
def generate_flyer(session: Session, event_details: dict) -> ToolResult:
    """Produce an HTML flyer and write it to workspace/flyer.html.

    IMPORTANT: registered with parallel_safe=False because it writes a file.
    Every concrete fact (venue, date, money, temp, condition) is tagged with
    data-testid so the integrity check can find them.
    """
    venue_name = event_details.get("venue_name", "Unknown venue")
    venue_address = event_details.get("venue_address", "")
    date = event_details.get("date", "")
    time = event_details.get("time", "")
    party_size = event_details.get("party_size", 0)
    condition = event_details.get("condition", "")
    temperature_c = event_details.get("temperature_c", "")
    total_gbp = event_details.get("total_gbp", 0)
    deposit_required_gbp = event_details.get("deposit_required_gbp", 0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pub booking — {venue_name}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 640px; margin: 2em auto; padding: 1em; }}
  h1 {{ color: #4a1c1c; border-bottom: 2px solid #4a1c1c; padding-bottom: 0.3em; }}
  h2 {{ color: #4a1c1c; margin-top: 1.5em; }}
  dl {{ display: grid; grid-template-columns: max-content 1fr; gap: 0.4em 1em; }}
  dt {{ font-weight: bold; }}
  .meta {{ color: #666; font-size: 0.9em; }}
</style>
</head>
<body>
  <h1>Event at <span data-testid="venue">{venue_name}</span></h1>
  <p class="meta" data-testid="address">{venue_address}</p>

  <h2>When</h2>
  <dl>
    <dt>Date</dt><dd data-testid="date">{date}</dd>
    <dt>Time</dt><dd data-testid="time">{time}</dd>
    <dt>Party size</dt><dd data-testid="party-size">{party_size}</dd>
  </dl>

  <h2>Weather forecast</h2>
  <p>
    Expecting <span data-testid="condition">{condition}</span> conditions
    at around <span data-testid="temperature">{temperature_c}°C</span>.
  </p>

  <h2>Cost</h2>
  <dl>
    <dt>Total</dt><dd data-testid="total">£{total_gbp}</dd>
    <dt>Deposit required</dt><dd data-testid="deposit">£{deposit_required_gbp}</dd>
  </dl>
</body>
</html>
"""

    # Write into the session's workspace/ directory.
    flyer_path = session.workspace_dir / "flyer.html"
    flyer_path.parent.mkdir(parents=True, exist_ok=True)
    flyer_path.write_text(html, encoding="utf-8")
    bytes_written = len(html.encode("utf-8"))

    output = {"path": "workspace/flyer.html", "bytes_written": bytes_written}
    summary = f"generate_flyer: wrote {output['path']} ({bytes_written} chars)"

    record_tool_call("generate_flyer", {"event_details": event_details}, output)
    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# Registry builder — DO NOT MODIFY the name, signature, or registration calls.
# The grader imports and calls this to pick up your tools.
# ---------------------------------------------------------------------------
def build_tool_registry(session: Session) -> ToolRegistry:
    """Build a session-scoped tool registry with all four Ex5 tools plus
    the sovereign-agent builtins (read_file, write_file, list_files,
    handoff_to_structured, complete_task).

    DO NOT change the tool names — the tests and grader call them by name.
    """
    from sovereign_agent.tools.builtin import make_builtin_registry

    reg = make_builtin_registry(session)

    # venue_search
    reg.register(
        _RegisteredTool(
            name="venue_search",
            description="Search Edinburgh venues by area, party size, and max budget.",
            fn=venue_search,
            parameters_schema={
                "type": "object",
                "properties": {
                    "near": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "budget_max_gbp": {"type": "integer", "default": 1000},
                },
                "required": ["near", "party_size"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # read-only
            examples=[
                {
                    "input": {"near": "Haymarket", "party_size": 6, "budget_max_gbp": 800},
                    "output": {"count": 1, "results": [{"id": "haymarket_tap"}]},
                }
            ],
        )
    )

    # get_weather
    reg.register(
        _RegisteredTool(
            name="get_weather",
            description="Get scripted weather for a city on a YYYY-MM-DD date.",
            fn=get_weather,
            parameters_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["city", "date"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # read-only
            examples=[
                {
                    "input": {"city": "Edinburgh", "date": "2026-04-25"},
                    "output": {"condition": "cloudy", "temperature_c": 12},
                }
            ],
        )
    )

    # calculate_cost
    reg.register(
        _RegisteredTool(
            name="calculate_cost",
            description="Compute total cost and deposit for a booking.",
            fn=calculate_cost,
            parameters_schema={
                "type": "object",
                "properties": {
                    "venue_id": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "duration_hours": {"type": "integer"},
                    "catering_tier": {
                        "type": "string",
                        "enum": ["drinks_only", "bar_snacks", "sit_down_meal", "three_course_meal"],
                        "default": "bar_snacks",
                    },
                },
                "required": ["venue_id", "party_size", "duration_hours"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # pure compute, no shared state
            examples=[
                {
                    "input": {
                        "venue_id": "haymarket_tap",
                        "party_size": 6,
                        "duration_hours": 3,
                    },
                    "output": {"total_gbp": 540, "deposit_required_gbp": 0},
                }
            ],
        )
    )

    # generate_flyer — parallel_safe=False because it writes a file
    def _flyer_adapter(event_details: dict) -> ToolResult:
        return generate_flyer(session, event_details)

    reg.register(
        _RegisteredTool(
            name="generate_flyer",
            description="Write an HTML flyer for the event to workspace/flyer.html.",
            fn=_flyer_adapter,
            parameters_schema={
                "type": "object",
                "properties": {"event_details": {"type": "object"}},
                "required": ["event_details"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=False,  # writes a file — MUST be False
            examples=[
                {
                    "input": {
                        "event_details": {
                            "venue_name": "Haymarket Tap",
                            "date": "2026-04-25",
                            "party_size": 6,
                        }
                    },
                    "output": {"path": "workspace/flyer.html"},
                }
            ],
        )
    )

    return reg


__all__ = [
    "build_tool_registry",
    "venue_search",
    "get_weather",
    "calculate_cost",
    "generate_flyer",
]
