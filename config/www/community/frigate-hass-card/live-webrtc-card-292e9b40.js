import{a as t,er as e,dh as r,du as a,df as s,l as o,dl as i,dn as n,dp as c,dm as d,r as u,_ as l,n as h,t as g,cK as p,dH as m,x as y}from"./card-61074723.js";import{g as b}from"./get-technology-for-video-rtc-778a0c05.js";import{m as f}from"./audio-cf3a75aa.js";import{s as w,h as _,c as v}from"./ptz-33c2bf64.js";let C=class extends t{constructor(){super(...arguments),this.controls=!1,this._webrtcTask=new e(this,this._getWebRTCCardElement,(()=>[1]))}async play(){return this._getPlayer()?.play()}async pause(){this._getPlayer()?.pause()}async mute(){const t=this._getPlayer();t&&(t.muted=!0)}async unmute(){const t=this._getPlayer();t&&(t.muted=!1)}isMuted(){return this._getPlayer()?.muted??!0}async seek(t){const e=this._getPlayer();e&&(e.currentTime=t)}async setControls(t){const e=this._getPlayer();e&&w(e,t??this.controls)}isPaused(){return this._getPlayer()?.paused??!0}async getScreenshotURL(){const t=this._getPlayer();return t?r(t):null}connectedCallback(){super.connectedCallback(),this.requestUpdate()}_getVideoRTC(){return this.renderRoot?.querySelector("#webrtc")??null}_getPlayer(){return this._getVideoRTC()?.video??null}async _getWebRTCCardElement(){return await customElements.whenDefined("webrtc-camera"),customElements.get("webrtc-camera")}_createWebRTC(){const t=this._webrtcTask.value;if(t&&this.hass&&this.cameraConfig){const e=new t,r={intersection:0,...this.cameraConfig.webrtc_card};return r.url||r.entity||!this.cameraEndpoints?.webrtcCard||(r.url=this.cameraEndpoints.webrtcCard.endpoint),e.setConfig(r),e.hass=this.hass,e}return null}render(){return a(this,this._webrtcTask,(()=>{let t;try{t=this._createWebRTC()}catch(t){return p(this,t instanceof m?t.message:o("error.webrtc_card_reported_error")+": "+t.message,{context:t.context})}return t&&(t.id="webrtc"),y`${t}`}),{inProgressFunc:()=>s({message:o("error.webrtc_card_waiting"),cardWideConfig:this.cardWideConfig})})}updated(){this.updateComplete.then((()=>{const t=this._getVideoRTC(),e=this._getPlayer();e&&(w(e,this.controls),e.onloadeddata=()=>{this.controls&&_(e,v),i(this,e,{player:this,capabilities:{supportsPause:!0,hasAudio:f(e)},...t&&{technology:b(t)}})},e.onplay=()=>n(this),e.onpause=()=>c(this),e.onvolumechange=()=>d(this))}))}static get styles(){return u(":host {\n  width: 100%;\n  height: 100%;\n  display: block;\n}\n\n/* Don't drop shadow or have radius for nested webrtc card */\n#webrtc ha-card {\n  border-radius: 0px;\n  margin: 0px;\n  box-shadow: none;\n}\n\nha-card,\ndiv.fix-safari,\n#video {\n  background: unset;\n  background-color: unset;\n}\n\n#webrtc #video {\n  object-fit: var(--frigate-card-media-layout-fit, contain);\n  object-position: var(--frigate-card-media-layout-position-x, 50%) var(--frigate-card-media-layout-position-y, 50%);\n  object-view-box: inset(var(--frigate-card-media-layout-view-box-top, 0%) var(--frigate-card-media-layout-view-box-right, 0%) var(--frigate-card-media-layout-view-box-bottom, 0%) var(--frigate-card-media-layout-view-box-left, 0%));\n}")}};l([h({attribute:!1})],C.prototype,"cameraConfig",void 0),l([h({attribute:!1})],C.prototype,"cameraEndpoints",void 0),l([h({attribute:!1})],C.prototype,"cardWideConfig",void 0),l([h({attribute:!0,type:Boolean})],C.prototype,"controls",void 0),C=l([g("frigate-card-live-webrtc-card")],C);export{C as FrigateCardLiveWebRTCCard};
