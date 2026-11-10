import argparse
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay simulated Caldova operational events to a Fabric eventstream custom endpoint."
    )
    parser.add_argument(
        "--templates",
        type=Path,
        default=Path(__file__).with_name("event_templates.json"),
        help="Path to the event template JSON file.",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=0.5,
        help="Delay between events. Use 0 for immediate replay.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print events without connecting to Fabric.",
    )
    parser.add_argument(
        "--prime",
        action="store_true",
        help="Send only the first nonexception event so a destination wizard can inspect the schema.",
    )
    return parser.parse_args()


def build_events(template_path: Path) -> list[dict]:
    templates = json.loads(template_path.read_text(encoding="utf-8"))
    if not isinstance(templates, list) or not templates:
        raise ValueError("The template file must contain a nonempty JSON array.")

    replay_id = uuid.uuid4().hex[:8]
    replay_start = datetime.now(timezone.utc)
    events = []
    for sequence, template in enumerate(templates, start=1):
        event = dict(template)
        offset = int(event.pop("OffsetSeconds", 0))
        event["EventID"] = f"SIM-{replay_id}-{sequence:03d}"
        event["EventTime"] = (
            replay_start + timedelta(seconds=offset)
        ).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        event["SourceSystem"] = "CaldovaLabSimulator"
        events.append(event)
    return events


def send_events(events: list[dict], delay_seconds: float) -> None:
    connection_string = os.getenv("EVENTSTREAM_CONNECTION_STRING")
    entity_name = os.getenv("EVENTSTREAM_ENTITY_NAME")
    if not connection_string or not entity_name:
        raise ValueError(
            "Set EVENTSTREAM_CONNECTION_STRING and EVENTSTREAM_ENTITY_NAME before replay."
        )

    from azure.eventhub import EventData, EventHubProducerClient

    producer = EventHubProducerClient.from_connection_string(
        conn_str=connection_string,
        eventhub_name=entity_name,
    )
    with producer:
        for event in events:
            producer.send_batch([EventData(json.dumps(event, separators=(",", ":")))])
            print(
                f"Sent {event['EventID']}: {event['EventType']} "
                f"{event['MetricValue']} {event['Unit']}"
            )
            if delay_seconds:
                time.sleep(delay_seconds)


def main() -> None:
    args = parse_args()
    events = build_events(args.templates)
    if args.prime:
        events = events[:1]
    if args.dry_run:
        for event in events:
            print(json.dumps(event, separators=(",", ":")))
        noun = "event" if len(events) == 1 else "events"
        print(f"Validated {len(events)} simulated {noun}.")
        return

    send_events(events, args.delay_seconds)
    noun = "event" if len(events) == 1 else "events"
    print(f"Replay complete: {len(events)} {noun} sent.")


if __name__ == "__main__":
    main()
