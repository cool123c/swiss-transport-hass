class SwissTransportCard extends HTMLElement {
  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error('You must define an entity in the card configuration');
    }
    this.config = Object.assign({count: 5, title: 'Next departures'}, config);
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _formatTime(isoString) {
    try {
      const d = new Date(isoString);
      if (isNaN(d)) return isoString;
      return d.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
    } catch (e) {
      return isoString;
    }
  }

  _render() {
    if (!this._hass) return;
    const entityId = this.config.entity;
    const stateObj = this._hass.states[entityId];

    if (!stateObj) {
      this.innerHTML = `<div class="card"><div class="card-content">Entity ${entityId} not found</div></div>`;
      return;
    }

    const attrs = stateObj.attributes || {};
    const station = attrs.station || stateObj.attributes.friendly_name || this.config.title;
    const departures = Array.isArray(attrs.departures) ? attrs.departures : [];
    const count = this.config.count || departures.length;

    let html = `<ha-card><div class="card-header"><span class="name">${this.config.title}</span></div>`;
    html += `<div class="card-content"><div class="station">${station}</div>`;

    if (!departures.length) {
      html += `<div class="empty">No upcoming departures</div>`;
    } else {
      html += `<ul class="departures">`;
      departures.slice(0, count).forEach((d) => {
        const time = d.stop ? this._formatTime(d.stop) : '';
        const platform = d.platform ? `<span class="platform">P ${d.platform}</span>` : '';
        const line = d.name || `${d.category || ''} ${d.number || ''}`;
        const to = d.to ? `<span class="to">→ ${d.to}</span>` : '';
        html += `<li class="departure"><span class="time">${time}</span><span class="line">${line}</span>${to}${platform}</li>`;
      });
      html += `</ul>`;
    }

    html += `</div></ha-card>`;

    // basic styles
    const style = `
      <style>
        ha-card { display:block; }
        .card-header { padding: 8px 16px; font-weight:600; }
        .card-content { padding: 8px 16px; }
        .station { color: var(--primary-text-color); margin-bottom: 6px; }
        .departures { list-style:none; padding:0; margin:0; }
        .departure { display:flex; gap:8px; align-items:center; padding:6px 0; border-bottom:1px solid rgba(0,0,0,0.04); }
        .time { width:64px; font-weight:600; color: var(--secondary-text-color); }
        .line { flex:1; }
        .platform { margin-left:8px; color: var(--secondary-text-color); }
        .empty { color: var(--secondary-text-color); }
      </style>
    `;

    this.innerHTML = style + html;
  }

  getCardSize() {
    return 1;
  }
}

customElements.define('swiss-transport-card', SwissTransportCard);

// Register with Lovelace if available
if (window && window.customCards) {
  window.customCards.push({
    type: 'swiss-transport-card',
    name: 'Swiss Transport departures',
    description: 'Display next departures from a Swiss station (uses swiss_transport sensor)',
  });
}
