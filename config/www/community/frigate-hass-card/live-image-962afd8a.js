import{a,cO as e,x as s,cU as t,r as i,cM as r,_ as m,n as u,t as n}from"./card-a62abdb3.js";import{g as o}from"./live-c59cad26.js";import"./image-5a7f7ab7.js";import"./ptz-b280ab54.js";import"./surround-3f609054.js";import"./surround-basic-4a3afec5.js";let g=class extends a{constructor(){super(...arguments),this._refImage=e()}async play(){await(this._refImage.value?.play())}async pause(){await(this._refImage.value?.pause())}async mute(){await(this._refImage.value?.mute())}async unmute(){await(this._refImage.value?.unmute())}isMuted(){return!!this._refImage.value?.isMuted()}async seek(a){await(this._refImage.value?.seek(a))}async setControls(a){await(this._refImage.value?.setControls(a))}isPaused(){return this._refImage.value?.isPaused()??!0}async getScreenshotURL(){return await(this._refImage.value?.getScreenshotURL())??null}render(){if(this.hass&&this.cameraConfig)return o(this,this.hass,this.cameraConfig),s`
      <frigate-card-image
        ${t(this._refImage)}
        .hass=${this.hass}
        .imageConfig=${this.cameraConfig.image}
        .cameraConfig=${this.cameraConfig}
      >
      </frigate-card-image>
    `}static get styles(){return i(r)}};m([u({attribute:!1})],g.prototype,"hass",void 0),m([u({attribute:!1})],g.prototype,"cameraConfig",void 0),g=m([n("frigate-card-live-image")],g);export{g as FrigateCardLiveImage};
