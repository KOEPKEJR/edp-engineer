# Draws each day's EDP ranking and remembers the last one in TRMNL's saved
# state (https://help.trmnl.com/en/articles/16777795-saved-state), as
# fusion/transform.py does for the rotator's refresh count.
#
# Runs on every refresh with static_data (`engineers`, the roster) and
# input["trmnl"]["state"]. The first run of a day, in the user's time zone,
# shuffles the roster into a new ranking and keeps the one it replaces as the
# previous ranking; later runs that day reuse both, so the order holds all day.
# State is {"day": "YYYY-MM-DD", "ranks": {name: rank}, "prev": {name: rank}},
# well under TRMNL's 8192-byte limit for ten names.
#
# Returns `as_of` (the day of the draw) and `engineers` in rank order, each
# with `rank`, `prev_rank` (null when it was not in the last ranking) and
# `change` (places moved up; negative is down, null when new).

import datetime
import random


def _key(e):
    return "%s %s" % (e.get("first_name", ""), e.get("last_name", ""))


def run(input):
    trmnl = input.get("trmnl") or {}
    state = trmnl.get("state") or {}
    try:
        offset = int((trmnl.get("user") or {}).get("utc_offset") or 0)
    except (TypeError, ValueError):
        offset = 0
    now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=offset)
    day = now.date().isoformat()

    roster = list(input.get("engineers") or [])
    names = [_key(e) for e in roster]
    ranks = state.get("ranks") or {}
    prev = state.get("prev") or {}

    # A new day, or a roster that no longer matches the kept ranking: draw again.
    if state.get("day") != day or sorted(ranks) != sorted(names):
        if state.get("day") != day:
            prev = ranks
        order = names[:]
        random.shuffle(order)
        ranks = {name: i + 1 for i, name in enumerate(order)}

    engineers = []
    for e in roster:
        name = _key(e)
        was = prev.get(name)
        engineers.append(dict(e, rank=ranks[name], prev_rank=was, change=None if was is None else was - ranks[name]))
    engineers.sort(key=lambda e: e["rank"])

    data = {k: v for k, v in input.items() if k not in ("trmnl", "engineers", "as_of")}
    data["as_of"] = day
    data["engineers"] = engineers
    data["trmnl_state"] = {"day": day, "ranks": ranks, "prev": prev}
    return data
