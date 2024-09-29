import{_ as i,n as t,t as e,a,x as r,r as o,cM as s}from"./card-6e374789.js";import"./surround-0a22b6f1.js";import"./timeline-core-1837c402.js";import"./surround-basic-3d1110ad.js";import"./startOfHour-0e6d6e06.js";import"./endOfDay-f5f6b201.js";import"./date-picker-3558a5f2.js";let n=class extends a{render(){return this.timelineConfig?r`
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
