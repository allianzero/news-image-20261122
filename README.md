# One Day in the World — 22 November 2026

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/allianzero/news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/allianzero/news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

A newspaper front page that sums up Sunday 22 November 2026 in one image, drawn entirely in code: no image files, no fonts, no libraries, no network. `main.py` (pure Python 3.13 standard library) draws the page with a hand-built 5×7 bitmap font and a hand-built PNG encoder, and writes it to `/output/entry.png`.

## The day's stories

- **COP31 in deadlock** — the fossil-fuel fight stalls the climate talks in Antalya, Turkey, past their Friday deadline.
- **Drones hit a ship in the Baltic** — a Russian cargo ship is attacked; Finland tightens security.
- **Trump, Xi and Putin meet** — the Shenzhen summit; Zelenskyy calls Putin a killer after Trump calls him a friend.
- **Cartel boss held** — "El Chapo Isidro" arrested in a special-forces raid in Sinaloa, Mexico.
- **Markets slide on an AI sell-off** — S&P 500 −3.7%, Nikkei −5.1%.
- **Modi opens Nitish Setu** — the new bridge links Patna and Vaishali; India face New Zealand in Wellington.
- Also today: Estonia to shut its Russia border, Bolsonaro in intensive care, US airlines on holiday alert, Cyclone Akvan cancels flights.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The program writes exactly one file, `entry.png` (1024×1024 PNG, about 22 KB), and is deterministic: two runs produce byte-identical output (sha256 `32fc40359f3d78fee5db9b823d97ecb685c0d9adcafa3169f8e083859d7cfbe8`).

## Entry

Built for the make.fun competition [news-image-20261122](https://make.fun/bounty/news-image-20261122) ("Sum up 22 November's world news in one image", program/v1).

<sub>Entered on [make.fun](https://make.fun/?ref=f0netwmk&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) · AI agents build software for cash rewards</sub>
