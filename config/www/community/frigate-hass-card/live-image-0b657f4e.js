import{a,cO as e,x as s,cT as t,r as i,cM as r,_ as m,n as o,t as n}from"./card-6478c77c.js";import{g as u}from"./live-8ae8d6c3.js";import"./image-c3d15958.js";import"./media-actions-controller-00f7d258.js";import"./surround-5f886854.js";import"./surround-basic-1ad71e7d.js";let g=class extends a{constructor(){super(...arguments),this._refImage=e()}async play(){await(this._refImage.value?.play())}async pause(){await(this._refImage.value?.pause())}async mute(){await(this._refImage.value?.mute())}async unmute(){await(this._refImage.value?.unmute())}isMuted(){return!!this._refImage.value?.isMuted()}async seek(a){await(this._refImage.value?.seek(a))}async setControls(a){await(this._refImage.value?.setControls(a))}isPaused(){return this._refImage.value?.isPaused()??!0}async getScreenshotURL(){return await(this._refImage.value?.getScreenshotURL())??null}render(){if(this.hass&&this.cameraConfig)return u(this,this.hass,this.cameraConfig),s`
      <frigate-card-image
        ${t(this._refImage)}
        .hass=${this.hass}
        .imageConfig=${this.cameraConfig.image}
        .cameraConfig=${this.cameraConfig}
      >
      </frigate-card-image>
    `}static get styles(){return i(r)}};m([o({attribute:!1})],g.prototype,"hass",void 0),m([o({attribute:!1})],g.prototype,"cameraConfig",void 0),g=m([n("frigate-card-live-image")],g);export{g as FrigateCardLiveImage};
