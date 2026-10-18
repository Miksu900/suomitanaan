# Suomi Tänään

Uutiset suoraan alkuperäislähteistä. Faktat kokonaan. Myös se, mitä muut eivät kerro.

- `worker/` – sivusto, toimituksen hyväksyntäjono (`/toimitus`) ja rajapinta (Cloudflare Worker + KV)
- `scripts/luonnokset.mjs` – päivittäiset uutisluonnokset alkuperäislähteistä (Claude API)
- `.github/workflows/` – julkaisu Cloudflareen ja luonnosten ajastus

Mitään ei julkaista ilman toimittajan hyväksyntää.
