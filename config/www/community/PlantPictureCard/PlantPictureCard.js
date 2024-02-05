const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class PlantPictureCard extends HTMLElement {

  static getConfigElement() {
    return document.createElement("plant-picture-card-editor");
  }

  static getStubConfig() {
    return {entity: "",
            image: "" };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  _click(entity) {
      this._fire("hass-more-info", { entityId: entity });
  }

  _fire(type, detail) {

      const event = new Event(type, {
          bubbles: true,
          cancelable: false,
          composed: true
      });
      event.detail = detail || {};
      this.shadowRoot.dispatchEvent(event);
      return event;
  }

  set hass(hass) {
    const config = this.config;

    var _title = config.title;

    if(!config.title){
      _title = hass.states[config.entity].attributes.friendly_name;
    }

    this.shadowRoot.getElementById("box").innerHTML = `
      <div class="title">${_title}</div>
      <div id="sensors">
      </div>
    `;

    var _entities = [
      hass.states[config.entity].attributes.sensors.moisture,
      hass.states[config.entity].attributes.sensors.temperature,
      hass.states[config.entity].attributes.sensors.brightness,
      hass.states[config.entity].attributes.sensors.conductivity,
      hass.states[config.entity].attributes.sensors.battery
    ];

    var _sensors = [
        "moisture",
        "temperature",
        "brightness",
        "conductivity",
        "battery"
    ];

    const _icons = [
      "mdi:water",
      "mdi:thermometer",
      "mdi:white-balance-sunny",
      "mdi:emoticon-poop",
      "mdi:battery"
    ];

    var i;
    for (i = 0; i < _entities.length; i++) {
      if (typeof _entities[parseInt(i)] == "undefined") { continue; }
      var _sensor = _entities[parseInt(i)];
      var _name = hass.states[String(_sensor)].attributes.friendly_name;
      var _state = hass.states[String(_sensor)].state;
      var _uom = hass.states[String(_sensor)].attributes.unit_of_measurement;
      var _icon = hass.states[String(_sensor)].attributes.icon;
      var _class = "state-on";
      if ( hass.states[config.entity].attributes.problem.indexOf(_sensors[parseInt(i)]) !== -1){
        _class += " state-problem";
      }

      this.shadowRoot.getElementById("sensors").innerHTML += `
        <div id="sensor${i}" class="sensor">
          <div class="icon"><ha-icon icon="${_icons[parseInt(i)]}"></ha-icon></div>
          <div class="${_class}">${_state}</div>
          <div class="uom">${_uom}</div>
        </div>
      `;
    }

    var j;
    for (j = 0; j < _entities.length; j++) {
       if (typeof _entities[parseInt(j)] == "undefined") { continue; }
       this.shadowRoot.getElementById("sensor"+[parseInt(j)]).onclick = this._click.bind(this, _entities[parseInt(j)]);
    }
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("You need to define an entity");
    }
    if (!config.image) {
      throw new Error("You need to define an image");
    }

    const root = this.shadowRoot;
    if (root.lastChild) {
      root.removeChild(root.lastChild);
    }

    this.config = config;

    const card = document.createElement("ha-card");
    const content = document.createElement("div");
    const style = document.createElement("style");

    style.textContent = `

      ha-card {
        position: relative;
        padding: 0;
        background-size: 100%;
      }

      img {
          display: block;
          height: auto;
          transition: filter .2s linear;
          width: 100%;
      }

      .box {
          position: absolute;
          left: 0;
          right: 0;
          bottom: 0;
          height: 16%;
          min-height: 64px;
          background-color: rgba(0, 0, 0, 0.5);
          padding: 4px 8px;
          color: white;
          display: flex;
          flex-wrap: wrap;
          justify-content: space-evenly;
          align-items: center;
          text-align: center;
      }

      div.title {
        flex: 0 1 20%;
      }

      div#sensors {
        display: flex;
        justify-content: space-between;
        flex: 1;
      }

      .sensor {
        flex-grow: 1;
      }

      ha-icon {
        cursor: pointer;
        color: var(--primary-color);
      }

      .state-problem {
        color: var(--accent-color);
      }

      .uom {
        color: var(--primary-text-color);
      }

    `;

    content.id = "container";
    content.innerHTML = `
    <div id="wrapper">
      <img src="${config.image} " />
    </div>
    <div class="box" id="box"></div>
    `;
    card.appendChild(content);
    card.appendChild(style);
    root.appendChild(card);
  }


  // The height of your card. Home Assistant uses this to automatically
  // distribute all cards over the available columns.
  getCardSize() {
    return 3;
  }
}

customElements.define("plant-picture-card", PlantPictureCard);


function deepClone(value) {
  if (!(!!value && typeof value === "object")) {
    return value;
  }
  if (Object.prototype.toString.call(value) === "[object Date]") {
    return new Date(value.getTime());
  }
  if (Array.isArray(value)) {
    return value.map(deepClone);
  }
  var result = {};
  Object.keys(value).forEach(
    function(key) { result[String(key)] = deepClone(value[String(key)]); });
  return result;
}

export class PlantPictureCardEditor extends LitElement {

  setConfig(config) {
    this.config = deepClone(config);
  }

  render() {
    if (!this.hass) {
      return html``;
    }

    const entities = Object.keys(this.hass.states).filter((eid) => eid.substr(0, eid.indexOf(".")) === "plant");

    return html`
      <div class="card-config">
        <div class="side-by-side">
          <paper-input
            label="Title"
            .value="${this.config.title}"
            .configValue="${"title"}"
            @value-changed="${this._valueChanged}"
          ></paper-input>
          <paper-dropdown-menu
            label="Entity"
            .configValue="${"entity"}"
            @value-changed="${this._valueChanged}"
           >
             <paper-listbox slot="dropdown-content" .selected=${entities.indexOf(this.config.entity)}>
               ${entities.map((entity) => {
                  return html`
                    <paper-item>${entity}</paper-item>
                  `;
                 })}
             </paper-listbox>
          </paper-dropdown-menu>
          <paper-input
            label="Image"
            .value="${this.config.image}"
            .configValue="${"image"}"
            @value-changed="${this._valueChanged}"
          ></paper-input>
        </div>
      </div>
    `;
  }

  _valueChanged(ev) {
    if (!this.config || !this.hass) {
      return;
    }
    const target = ev.target;
    if (this.config[`${target.configValue}`] === (target.value||target.__checked)) {
      return;
    }
    if (target.configValue) {
      if (target.value === "") {
        delete this.config[target.configValue];
      } else {
        this.config = {
          ...this.config,
          [target.configValue]: target.value||target.__checked
        };
      }
    }
    this.configChanged(this.config);
  }

  configChanged(newConfig) {
    const event = new Event("config-changed", {
      bubbles: true,
      composed: true
    });
    event.detail = {config: newConfig};
    this.dispatchEvent(event);
  }
}

customElements.define("plant-picture-card-editor", PlantPictureCardEditor);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "plant-picture-card",
  name: "Plant Picture Card",
  preview: true, // Optional - defaults to false
  description: "Like a picture glance card but for plant data" // Optional
});
