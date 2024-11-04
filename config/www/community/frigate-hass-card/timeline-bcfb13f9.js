import{_ as i,n as t,t as e,a,x as r,r as o,cM as s}from"./card-7bfaa32a.js";import"./surround-06804641.js";import"./timeline-core-10dc010c.js";import"./surround-basic-185f20f6.js";import"./startOfHour-2e0d9bda.js";import"./endOfDay-910bd6a5.js";import"./date-picker-486cba3f.js";let n=class extends a{render(){return this.timelineConfig?r`
      <frigate-card-timeline-core
        .hass=${this.hass}
        .viewManagerEpoch=${this.viewManagerEpoch}
        .timelineConfig=${this.timelineConfig}
        .thumbnailConfig=${this.timelineConfig.controls.thumbnails}
        .cameraManager=${this.cameraManager}
        .cameraIDs=${this.cameraManager?.getStore().getCameraIDsWithCapability({anyCapabilities:["clips","snapshots","recordings"]})}
        .cardWideConfig=${this.cardWideConfig}
        .itemClickAction=${"none"===this.timelineConfig.controls.thumbnails.mode?"play":"select"}
      >
      </frigate-card-timeline-core>
    `:r``}static get styles(){return o(s)}};i([t({attribute:!1})],n.prototype,"hass",void 0),i([t({attribute:!1})],n.prototype,"viewManagerEpoch",void 0),i([t({attribute:!1})],n.prototype,"timelineConfig",void 0),i([t({attribute:!1})],n.prototype,"cameraManager",void 0),i([t({attribute:!1})],n.prototype,"cardWideConfig",void 0),n=i([e("frigate-card-timeline")],n);export{n as FrigateCardTimeline};
