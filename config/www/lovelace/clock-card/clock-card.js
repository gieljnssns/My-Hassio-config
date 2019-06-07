class ClockCard extends Polymer.Element {

    static get template() {
        return Polymer.html`
          <style>
        :host {
          cursor: pointer;
        }
        .content {
          padding: 24px 16px;
          display:flex;
        }
        .gtlogo{
	        background-image: url("/local/images/Antwerp-wide.png");
		    background-size: contain;
		    background-repeat: no-repeat;
		    width:92px;
        }
        .time {
          font-family: var(--paper-font-headline_-_font-family);
          -webkit-font-smoothing: var(--paper-font-headline_-_-webkit-font-smoothing);
          font-size: 3em;
          font-weight: var(--paper-font-headline_-_font-weight);
          letter-spacing: var(--paper-font-headline_-_letter-spacing);
          line-height: 1em;
          text-rendering: var(--paper-font-common-expensive-kerning_-_text-rendering);
        }
        .date {
	      color: var(--accent-color);
          font-family: var(--paper-font-headline_-_font-family);
          -webkit-font-smoothing: var(--paper-font-headline_-_-webkit-font-smoothing);
          font-size: 1.3em;
          font-weight: var(--paper-font-headline_-_font-weight);
          letter-spacing: var(--paper-font-headline_-_letter-spacing);
          line-height: var(--paper-font-headline_-_line-height);
          text-rendering: var(--paper-font-common-expensive-kerning_-_text-rendering);
        }
      </style>
      <ha-card>
        <div class="content">
	      <div class="gtlogo"></div>
	      <div class="clock">
		    <div class="time" id="time">3:45 PM</div>
		    <div class="date" id="date">Wednesday, December 3</div>
	      </div>
        </div>
      </ha-card>
     `
    }

    static get properties() {
        return {
            _hass: Object
        }
    }

    ready() {
        super.ready();
        this.time = this.$.time;
        this.date = this.$.date;

        this._updateTime();
        setInterval(() => this._updateTime(), 500);
    }

    setConfig(config) {
        this.config = config;
    }

    set hass(hass) {
        this._hass = hass;
    }

    _updateTime(force = false) {
        moment.locale('nl');
        this.time.innerHTML = moment().format('H:mm');
        this.date.innerHTML = moment().format('LL');
    }

    // The height of your card. Home Assistant uses this to automatically
    // distribute all cards over the available columns.
    getCardSize() {
        return 3;
    }
}

customElements.define('clock-card', ClockCard);