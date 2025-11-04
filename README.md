# Swiss Transport — Home Assistant Integration

This is a small Home Assistant custom integration to fetch departure times from the Swiss public transport API (https://transport.opendata.ch).

Features
- Configure a station via the Home Assistant integration UI.
- A sensor that shows the next departure time (minutes) and an attribute with upcoming departures.

Install
1. Add this repository to HACS (Custom repositories) as an "Integration" type and install it.
2. Restart Home Assistant.
3. Configure the integration via Settings → Devices & Services → + Add Integration → Swiss Transport.

Notes
- This integration uses the public transport.opendata.ch API. No API key required.
- The integration polls the API periodically; default update interval is 60 seconds.

Lovelace card

This repo includes a small custom Lovelace card that displays upcoming departures using the sensor created by the integration.

Files
- `custom_components/swiss_transport/www/swiss-transport-card.js` — the Lovelace card file.

Add the resource
- If you installed via HACS, HACS can add the frontend resource for you. The resource URL typically looks like `/hacsfiles/<repo>/swiss-transport-card.js` (HACS provides the exact path). Alternatively, copy the `www/swiss-transport-card.js` file into your Home Assistant `www` folder and add the resource `/local/swiss-transport-card.js`.

Example card
In Lovelace YAML or the Raw editor, add a card like:

```yaml
type: 'custom:swiss-transport-card'
entity: sensor.your_swiss_transport_sensor
count: 5 # optional, default 5
title: 'Next departures - My Station' # optional
```

The card expects the sensor entity to have an attribute `departures` — the integration's sensor sets this attribute as a list of departures with `stop` (ISO datetime), `platform`, `name`, `category`, `number`, and `to`.

Repository
This repo is intended to be installed via HACS. Place `custom_components/swiss_transport` into your HA `custom_components` directory if installing manually.
