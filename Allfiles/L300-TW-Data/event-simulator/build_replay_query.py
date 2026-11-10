"""Render a read-only verification query for one actual replay. No credentials or sends."""
import argparse
from pathlib import Path
import re


def render(replay: str) -> str:
    match = re.fullmatch(r'(?:SIM-)?([0-9a-f]{8})', replay)
    if not match:
        raise ValueError('Use the eight lowercase hex digits, or SIM- followed by those digits, from the actual full replay.')
    template = Path(__file__).with_name('verify_operational_replay.kql').read_text(encoding='utf-8')
    return template.replace('REPLACE_WITH_ACTUAL_REPLAY_ID', match[1])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay-id', required=True)
    args = parser.parse_args()
    try:
        print(render(args.replay_id))
    except ValueError as error:
        parser.error(str(error))
