#!/usr/bin/env python3
"""
Busca o Fear & Greed Index na CNN e atualiza data/data.json.
Roda dentro do GitHub Actions (veja .github/workflows/update.yml).

Endpoint: https://production.dataviz.cnn.io/index/fearandgreed/graphdata/<AAAA-MM-DD>
Devolve, a partir da data informada até hoje:
  - fear_and_greed_historical.data: pontos diários [{x: timestamp_ms, y: valor}, ...]
  - fear_and_greed: leitura atual {score, rating, previous_close,
        previous_1_week, previous_1_month, previous_1_year, ...}
"""
import json
import sys
import urllib.request
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "data.json"
EPOCH = dt.date(1970, 1, 1)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://edition.cnn.com/markets/fear-and-greed",
}


def fetch(date_str: str) -> dict:
    url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{date_str}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def first_present(d: dict, *keys):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def main() -> int:
    if not DATA_FILE.exists():
        print(f"Não encontrei {DATA_FILE}", file=sys.stderr)
        return 1

    store = json.loads(DATA_FILE.read_text())
    D, V = store["D"], store["V"]
    day_index = {d: i for i, d in enumerate(D)}

    # 20 dias de folga garantem sobreposição mesmo se o robô ficar
    # um tempo sem rodar (feriados, falha do GitHub, etc.).
    start = (dt.date.today() - dt.timedelta(days=20)).isoformat()
    try:
        payload = fetch(start)
    except Exception as exc:  # rede instável, CNN fora do ar, bloqueio pontual...
        print(f"Falha ao buscar dados da CNN: {exc}", file=sys.stderr)
        return 1

    changed = False

    hist = (payload.get("fear_and_greed_historical") or {}).get("data") or []
    for point in hist:
        try:
            ts_ms, val = point["x"], float(point["y"])
        except (KeyError, TypeError, ValueError):
            continue
        day = dt.datetime.utcfromtimestamp(ts_ms / 1000).date()
        dnum = (day - EPOCH).days
        val = round(val, 1)
        if dnum in day_index:
            i = day_index[dnum]
            if V[i] != val:
                V[i] = val
                changed = True
        else:
            D.append(dnum)
            V.append(val)
            day_index[dnum] = len(D) - 1
            changed = True

    now = payload.get("fear_and_greed") or {}
    score = first_present(now, "score")
    if score is not None:
        today_num = (dt.date.today() - EPOCH).days
        val = round(float(score), 1)
        if today_num in day_index:
            i = day_index[today_num]
            if V[i] != val:
                V[i] = val
                changed = True
        else:
            D.append(today_num)
            V.append(val)
            day_index[today_num] = len(D) - 1
            changed = True

    if D:
        pairs = sorted(zip(D, V))
        D, V = [p[0] for p in pairs], [p[1] for p in pairs]
        store["D"], store["V"] = D, V

    week = first_present(now, "previous_1_week", "week_ago")
    month = first_present(now, "previous_1_month", "month_ago")
    year = first_present(now, "previous_1_year", "year_ago")
    if score is not None:
        store["now"] = {
            "score": round(float(score), 1),
            "rating": now.get("rating"),
            "week": round(float(week), 1) if week is not None else store.get("now", {}).get("week"),
            "month": round(float(month), 1) if month is not None else store.get("now", {}).get("month"),
            "year": round(float(year), 1) if year is not None else store.get("now", {}).get("year"),
        }
        changed = True

    if changed:
        store["updated"] = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        DATA_FILE.write_text(json.dumps(store, separators=(",", ":")))
        print(f"Atualizado: {len(D)} dias, leitura atual = {store['now']['score']}")
    else:
        print("Nada novo para gravar.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
