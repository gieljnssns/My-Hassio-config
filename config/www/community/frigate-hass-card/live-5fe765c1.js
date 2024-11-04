import{cF as e,cG as i,cH as t,cI as a,cJ as r,cK as o,l as s,_ as n,n as d,cL as g,t as c,b as h,a as l,x as m,r as v,cM as u,cN as p,cO as C,cC as f,cP as I,cQ as M,cR as _,cS as w,cT as b,cU as y,cV as L,cW as A,cX as D,cY as $,e as j}from"./card-fe58fbb1.js";import{M as z,A as k,a as S,b as E,i as N,p as x,u as T}from"./ptz-511eb79b.js";import"./surround-d22852c0.js";
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const P=e(class extends i{constructor(){super(...arguments),this.key=t}render(e,i){return this.key=e,i}update(e,[i,t]){return i!==this.key&&(a(e),this.key=i),t}});class Z{constructor(e){this._inBackground=!1,this._messageReceived=!1,this._lastMediaLoadedInfo=null,this._renderEpoch=0,this._handleMessage=e=>{this._messageReceived=!0,this._inBackground&&(e.stopPropagation(),this._renderEpoch++)},this._handleMediaLoaded=e=>{this._lastMediaLoadedInfo={source:e.composedPath()[0],mediaLoadedInfo:e.detail},this._inBackground&&e.stopPropagation()},this._host=e,e.addController(this),this._intersectionObserver=new IntersectionObserver(this._intersectionHandler.bind(this))}shouldUpdate(){return!(this._inBackground&&this._messageReceived)}hostConnected(){this._intersectionObserver.observe(this._host),this._host.addEventListener("frigate-card:media:loaded",this._handleMediaLoaded),this._host.addEventListener("frigate-card:message",this._handleMessage)}hostDisconnected(){this._intersectionObserver.disconnect(),this._host.removeEventListener("frigate-card:media:loaded",this._handleMediaLoaded),this._host.removeEventListener("frigate-card:message",this._handleMessage)}clearMessageReceived(){this._messageReceived=!1}isInBackground(){return this._inBackground}getRenderEpoch(){return this._renderEpoch}_intersectionHandler(e){const i=this._inBackground;this._inBackground=!e.some((e=>e.isIntersecting)),this._inBackground||this._messageReceived||!this._lastMediaLoadedInfo||r(this._lastMediaLoadedInfo.source,this._lastMediaLoadedInfo.mediaLoadedInfo),i!==this._inBackground&&this._host.requestUpdate()}}const O=(e,i,t)=>{if(!t?.camera_entity)return o(e,s("error.no_live_camera"),{context:t}),null;const a=i.states[t.camera_entity];return a||(o(e,s("error.live_camera_not_found"),{context:t}),null)},G="frigate-card-live-provider";let W=class extends l{constructor(){super(...arguments),this._controller=new Z(this)}shouldUpdate(e){return this._controller.shouldUpdate()}willUpdate(){this._controller.clearMessageReceived()}render(){if(this.hass&&this.nonOverriddenLiveConfig&&this.cameraManager)return m`${P(this._controller.getRenderEpoch(),m`
        <frigate-card-live-grid
          .hass=${this.hass}
          .viewManagerEpoch=${this.viewManagerEpoch}
          .nonOverriddenLiveConfig=${this.nonOverriddenLiveConfig}
          .overriddenLiveConfig=${this.overriddenLiveConfig}
          .inBackground=${this._controller.isInBackground()}
          .conditionsManagerEpoch=${this.conditionsManagerEpoch}
          .overrides=${this.overrides}
          .cardWideConfig=${this.cardWideConfig}
          .cameraManager=${this.cameraManager}
          .microphoneManager=${this.microphoneManager}
          .triggeredCameraIDs=${this.triggeredCameraIDs}
        >
        </frigate-card-live-grid>
      `)}`}static get styles(){return v(u)}};n([d({attribute:!1})],W.prototype,"conditionsManagerEpoch",void 0),n([d({attribute:!1})],W.prototype,"hass",void 0),n([d({attribute:!1})],W.prototype,"viewManagerEpoch",void 0),n([d({attribute:!1})],W.prototype,"nonOverriddenLiveConfig",void 0),n([d({attribute:!1})],W.prototype,"overriddenLiveConfig",void 0),n([d({attribute:!1,hasChanged:g})],W.prototype,"overrides",void 0),n([d({attribute:!1})],W.prototype,"cameraManager",void 0),n([d({attribute:!1})],W.prototype,"cardWideConfig",void 0),n([d({attribute:!1})],W.prototype,"microphoneManager",void 0),n([d({attribute:!1})],W.prototype,"triggeredCameraIDs",void 0),W=n([c("frigate-card-live")],W);let U=class extends l{_renderCarousel(e){const i=this.viewManagerEpoch?.manager.getView(),t=e??i?.camera;return m`
      <frigate-card-live-carousel
        grid-id=${p(e)}
        .hass=${this.hass}
        .viewManagerEpoch=${this.viewManagerEpoch}
        .viewFilterCameraID=${e}
        .nonOverriddenLiveConfig=${this.nonOverriddenLiveConfig}
        .overriddenLiveConfig=${this.overriddenLiveConfig}
        .conditionsManagerEpoch=${this.conditionsManagerEpoch}
        .overrides=${this.overrides}
        .cardWideConfig=${this.cardWideConfig}
        .cameraManager=${this.cameraManager}
        .microphoneManager=${this.microphoneManager}
        ?triggered=${t&&!!this.triggeredCameraIDs?.has(t)}
      >
      </frigate-card-live-carousel>
    `}_gridSelectCamera(e){this.viewManagerEpoch?.manager.setViewByParameters({params:{camera:e}})}_needsGrid(){const e=this.cameraManager?.getStore().getCameraIDsWithCapability("live"),i=this.viewManagerEpoch?.manager.getView();return!!i?.isGrid()&&!!i?.supportsMultipleDisplayModes()&&!!e&&e.size>1}willUpdate(e){e.has("viewManagerEpoch")&&this._needsGrid()&&import("./media-grid-412ec164.js")}render(){if(!this.conditionsManagerEpoch||!this.nonOverriddenLiveConfig)return;const e=this.cameraManager?.getStore().getCameraIDsWithCapability("live");return e?.size&&this._needsGrid()?m`
      <frigate-card-media-grid
        .selected=${this.viewManagerEpoch?.manager.getView()?.camera}
        .displayConfig=${this.overriddenLiveConfig?.display}
        @frigate-card:media-grid:selected=${e=>this._gridSelectCamera(e.detail.selected)}
      >
        ${[...e].map((e=>this._renderCarousel(e)))}
      </frigate-card-media-grid>
    `:this._renderCarousel()}static get styles(){return v(":host {\n  width: 100%;\n  height: 100%;\n  display: block;\n}\n\n@keyframes warning-pulse {\n  0% {\n    border: solid 2px var(--frigate-card-triggered-color-1, rgba(0, 0, 0, 0));\n  }\n  50% {\n    border: solid 2px var(--frigate-card-triggered-color-2, var(--warning-color));\n  }\n  100% {\n    border: solid 2px var(--frigate-card-triggered-color-1, rgba(0, 0, 0, 0));\n  }\n}\nfrigate-card-live-carousel[triggered] {\n  animation: warning-pulse 5s infinite;\n}\n\nfrigate-card-live-carousel[selected] {\n  --frigate-card-triggered-color-1: var(--primary-color);\n}")}};n([d({attribute:!1})],U.prototype,"hass",void 0),n([d({attribute:!1})],U.prototype,"viewManagerEpoch",void 0),n([d({attribute:!1})],U.prototype,"nonOverriddenLiveConfig",void 0),n([d({attribute:!1})],U.prototype,"overriddenLiveConfig",void 0),n([d({attribute:!1,hasChanged:g})],U.prototype,"overrides",void 0),n([d({attribute:!1})],U.prototype,"conditionsManagerEpoch",void 0),n([d({attribute:!1})],U.prototype,"cardWideConfig",void 0),n([d({attribute:!1})],U.prototype,"cameraManager",void 0),n([d({attribute:!1})],U.prototype,"microphoneManager",void 0),n([d({attribute:!1})],U.prototype,"triggeredCameraIDs",void 0),U=n([c("frigate-card-live-grid")],U);let B=class extends l{constructor(){super(...arguments),this._cameraToSlide={},this._refPTZControl=C(),this._refCarousel=C(),this._mediaActionsController=new z,this._mediaHasLoaded=!1}connectedCallback(){super.connectedCallback(),this.requestUpdate()}disconnectedCallback(){this._mediaActionsController.destroy(),super.disconnectedCallback()}_getTransitionEffect(){return this.overriddenLiveConfig?.transition_effect??f.live.transition_effect}_getSelectedCameraIndex(){if(this.viewFilterCameraID)return 0;const e=this.cameraManager?.getStore().getCameraIDsWithCapability("live"),i=this.viewManagerEpoch?.manager.getView();return e?.size&&i?Math.max(0,Array.from(e).indexOf(i.camera)):0}willUpdate(e){(e.has("microphoneManager")||e.has("overriddenLiveConfig"))&&this._mediaActionsController.setOptions({playerSelector:G,...this.overriddenLiveConfig?.auto_play&&{autoPlayConditions:this.overriddenLiveConfig.auto_play},...this.overriddenLiveConfig?.auto_pause&&{autoPauseConditions:this.overriddenLiveConfig.auto_pause},...this.overriddenLiveConfig?.auto_mute&&{autoMuteConditions:this.overriddenLiveConfig.auto_mute},...this.overriddenLiveConfig?.auto_unmute&&{autoUnmuteConditions:this.overriddenLiveConfig.auto_unmute},...(this.overriddenLiveConfig?.auto_unmute||this.overriddenLiveConfig?.auto_mute)&&{microphoneManager:this.microphoneManager,microphoneMuteSeconds:this.overriddenLiveConfig.microphone.mute_after_microphone_mute_seconds}})}_getPlugins(){return[k({...this.overriddenLiveConfig?.lazy_load&&{lazyLoadCallback:(e,i)=>this._lazyloadOrUnloadSlide("load",e,i)},lazyUnloadConditions:this.overriddenLiveConfig?.lazy_unload,lazyUnloadCallback:(e,i)=>this._lazyloadOrUnloadSlide("unload",e,i)}),S(),E()]}_getLazyLoadCount(){return!1===this.overriddenLiveConfig?.lazy_load?null:0}_getSlides(){if(!this.cameraManager)return[[],{}];const e=this.viewManagerEpoch?.manager.getView(),i=this.viewFilterCameraID?new Set([this.viewFilterCameraID]):this.cameraManager?.getStore().getCameraIDsWithCapability("live"),t=[],a={};for(const[r,o]of this.cameraManager.getStore().getCameraConfigEntries(i)){const i=this._getSubstreamCameraID(r,e),s=r===i?o:this.cameraManager?.getStore().getCameraConfig(i),n=s?this._renderLive(i,s):null;n&&(a[r]=t.length,t.push(n))}return[t,a]}_setViewHandler(e){const i=this.cameraManager?.getStore().getCameraIDsWithCapability("live");i?.size&&e.detail.index!==this._getSelectedCameraIndex()&&this._setViewCameraID([...i][e.detail.index])}_setViewCameraID(e){e&&this.viewManagerEpoch?.manager.setViewByParametersWithNewQuery({params:{camera:e}})}_lazyloadOrUnloadSlide(e,i,t){t instanceof HTMLSlotElement&&(t=t.assignedElements({flatten:!0})[0]);const a=t?.querySelector(G);a&&(a.load="load"===e)}_renderLive(e,i){if(!(this.overriddenLiveConfig&&this.nonOverriddenLiveConfig&&this.hass&&this.cameraManager&&this.conditionsManagerEpoch))return;let t=null;try{t=I(this.conditionsManagerEpoch.manager,{live:this.nonOverriddenLiveConfig},{configOverrides:this.overrides,stateOverrides:{camera:e},schema:M}).live}catch(e){return _(this,e)}const a=this.cameraManager.getCameraMetadata(e),r=this.viewManagerEpoch?.manager.getView();return m`
      <div class="embla__slide">
        <frigate-card-live-provider
          ?load=${!t.lazy_load}
          .microphoneStream=${r?.camera===e?this.microphoneManager?.getStream():void 0}
          .cameraConfig=${i}
          .cameraEndpoints=${N([this.cameraManager,e],(()=>this.cameraManager?.getCameraEndpoints(e)??void 0))}
          .label=${a?.title??""}
          .liveConfig=${t}
          .hass=${this.hass}
          .cardWideConfig=${this.cardWideConfig}
          .zoomSettings=${r?.context?.zoom?.[e]?.requested}
          @frigate-card:zoom:change=${i=>w(i,this.viewManagerEpoch?.manager,e)}
        >
        </frigate-card-live-provider>
      </div>
    `}_getCameraIDsOfNeighbors(){const e=this.cameraManager?[...this.cameraManager?.getStore().getCameraIDsWithCapability("live")]:[],i=this.viewManagerEpoch?.manager.getView();if(this.viewFilterCameraID||e.length<=1||!i||!this.hass)return[null,null];const t=this.viewFilterCameraID??i.camera,a=e.indexOf(t);return a<0?[null,null]:[e[a>0?a-1:e.length-1],e[a+1<e.length?a+1:0]]}_getSubstreamCameraID(e,i){return i?.context?.live?.overrides?.get(e)??e}render(){const e=this.viewManagerEpoch?.manager.getView();if(!(this.overriddenLiveConfig&&this.hass&&e&&this.cameraManager))return;const[i,t]=this._getSlides();if(this._cameraToSlide=t,!i.length)return;const a=i.length>1,[r,o]=this._getCameraIDsOfNeighbors(),s=r?this.cameraManager.getCameraMetadata(this._getSubstreamCameraID(r,e)):null,n=o?this.cameraManager.getCameraMetadata(this._getSubstreamCameraID(o,e)):null,d=!(!this._mediaHasLoaded||this.viewFilterCameraID&&this.viewFilterCameraID!==e.camera||!1===e.context?.ptzControls?.enabled)&&e.context?.ptzControls?.enabled;return m`
      <frigate-card-carousel
        ${b(this._refCarousel)}
        .loop=${a}
        .dragEnabled=${a&&this.overriddenLiveConfig?.draggable}
        .plugins=${N([this.cameraManager,this.overriddenLiveConfig,this.microphoneManager],this._getPlugins.bind(this))}
        .selected=${this._getSelectedCameraIndex()}
        transitionEffect=${this._getTransitionEffect()}
        @frigate-card:carousel:select=${this._setViewHandler.bind(this)}
        @frigate-card:media:loaded=${()=>{this._mediaHasLoaded=!0}}
        @frigate-card:media:unloaded=${()=>{this._mediaHasLoaded=!1}}
      >
        <frigate-card-next-previous-control
          slot="previous"
          .hass=${this.hass}
          .direction=${"previous"}
          .controlConfig=${this.overriddenLiveConfig.controls.next_previous}
          .label=${s?.title??""}
          .icon=${s?.icon}
          ?disabled=${null===r}
          @click=${e=>{this._setViewCameraID(r),y(e)}}
        >
        </frigate-card-next-previous-control>
        ${i}
        <frigate-card-next-previous-control
          slot="next"
          .hass=${this.hass}
          .direction=${"next"}
          .controlConfig=${this.overriddenLiveConfig.controls.next_previous}
          .label=${n?.title??""}
          .icon=${n?.icon}
          ?disabled=${null===o}
          @click=${e=>{this._setViewCameraID(o),y(e)}}
        >
        </frigate-card-next-previous-control>
      </frigate-card-carousel>
      <frigate-card-ptz
        .config=${this.overriddenLiveConfig.controls.ptz}
        .cameraManager=${this.cameraManager}
        .cameraID=${L(e,this.viewFilterCameraID)}
        .forceVisibility=${d}
      >
      </frigate-card-ptz>
    `}_setMediaTarget(){const e=this.viewManagerEpoch?.manager.getView(),i=this._getSelectedCameraIndex();this.viewFilterCameraID?this._mediaActionsController.setTarget(i,e?.camera===this.viewFilterCameraID):this._mediaActionsController.setTarget(i,!0)}updated(e){super.updated(e);let i=!1;!this._mediaActionsController.hasRoot()&&this._refCarousel.value&&(this._mediaActionsController.initialize(this._refCarousel.value),i=!0),(i||e.has("viewManagerEpoch"))&&this._setMediaTarget()}static get styles(){return v(":host {\n  display: block;\n  --video-max-height: none;\n}\n\n:host(:not([grid-id])) {\n  height: 100%;\n}\n\n:host([unselected]) frigate-card-carousel {\n  pointer-events: none;\n}\n\n.embla__slide {\n  display: flex;\n  justify-content: center;\n  height: 100%;\n  flex: 0 0 100%;\n}")}};n([d({attribute:!1})],B.prototype,"hass",void 0),n([d({attribute:!1})],B.prototype,"viewManagerEpoch",void 0),n([d({attribute:!1})],B.prototype,"nonOverriddenLiveConfig",void 0),n([d({attribute:!1})],B.prototype,"overriddenLiveConfig",void 0),n([d({attribute:!1,hasChanged:g})],B.prototype,"overrides",void 0),n([d({attribute:!1})],B.prototype,"conditionsManagerEpoch",void 0),n([d({attribute:!1})],B.prototype,"cardWideConfig",void 0),n([d({attribute:!1})],B.prototype,"cameraManager",void 0),n([d({attribute:!1})],B.prototype,"microphoneManager",void 0),n([d({attribute:!1})],B.prototype,"viewFilterCameraID",void 0),n([h()],B.prototype,"_mediaHasLoaded",void 0),B=n([c("frigate-card-live-carousel")],B);let V=class extends l{constructor(){super(...arguments),this.load=!1,this.label="",this._isVideoMediaLoaded=!1,this._refProvider=C(),this._importPromises=[]}async play(){await this.updateComplete,await(this._refProvider.value?.updateComplete),await x(this,this._refProvider.value)}async pause(){await this.updateComplete,await(this._refProvider.value?.updateComplete),await(this._refProvider.value?.pause())}async mute(){await this.updateComplete,await(this._refProvider.value?.updateComplete),await(this._refProvider.value?.mute())}async unmute(){await this.updateComplete,await(this._refProvider.value?.updateComplete),await(this._refProvider.value?.unmute())}isMuted(){return this._refProvider.value?.isMuted()??!0}async seek(e){await this.updateComplete,await(this._refProvider.value?.updateComplete),await(this._refProvider.value?.seek(e))}async setControls(e){await this.updateComplete,await(this._refProvider.value?.updateComplete),await(this._refProvider.value?.setControls(e))}isPaused(){return this._refProvider.value?.isPaused()??!0}async getScreenshotURL(){return await this.updateComplete,await(this._refProvider.value?.updateComplete),await(this._refProvider.value?.getScreenshotURL())??null}_getResolvedProvider(){return"auto"===this.cameraConfig?.live_provider?this.cameraConfig?.webrtc_card?.entity||this.cameraConfig?.webrtc_card?.url?"webrtc-card":this.cameraConfig?.camera_entity?"ha":this.cameraConfig?.frigate.camera_name?"jsmpeg":f.cameras.live_provider:this.cameraConfig?.live_provider||"image"}_shouldShowImageDuringLoading(){return!!this.cameraConfig?.camera_entity&&!!this.hass&&!!this.liveConfig?.show_image_during_load}disconnectedCallback(){this._isVideoMediaLoaded=!1}_videoMediaShowHandler(){this._isVideoMediaLoaded=!0}willUpdate(e){if(e.has("load")&&(this.load||(this._isVideoMediaLoaded=!1,A(this))),e.has("liveConfig")&&(this.liveConfig?.show_image_during_load&&this._importPromises.push(import("./live-image-f220c957.js")),this.liveConfig?.zoomable&&this._importPromises.push(import("./zoomer-354967a7.js"))),e.has("cameraConfig")){const e=this._getResolvedProvider();"jsmpeg"===e?this._importPromises.push(import("./live-jsmpeg-a5a67efd.js")):"ha"===e?this._importPromises.push(import("./live-ha-08323924.js")):"webrtc-card"===e?this._importPromises.push(import("./live-webrtc-card-5e85d38b.js")):"image"===e?this._importPromises.push(import("./live-image-f220c957.js")):"go2rtc"===e&&this._importPromises.push(import("./live-go2rtc-fb41c006.js")),T(this,this.cameraConfig?.dimensions?.layout),this.style.aspectRatio=D({ratio:this.cameraConfig?.dimensions?.aspect_ratio})}}async getUpdateComplete(){const e=await super.getUpdateComplete();return await Promise.all(this._importPromises),this._importPromises=[],e}_useZoomIfRequired(e){return this.liveConfig?.zoomable?m` <frigate-card-zoomer
          .defaultSettings=${N([this.cameraConfig?.dimensions?.layout],(()=>this.cameraConfig?.dimensions?.layout?{pan:this.cameraConfig.dimensions.layout.pan,zoom:this.cameraConfig.dimensions.layout.zoom}:void 0))}
          .settings=${this.zoomSettings}
          @frigate-card:zoom:zoomed=${()=>this.setControls(!1)}
          @frigate-card:zoom:unzoomed=${()=>this.setControls()}
        >
          ${e}
        </frigate-card-zoomer>`:e}render(){if(!(this.load&&this.hass&&this.liveConfig&&this.cameraConfig))return;this.title=this.label,this.ariaLabel=this.label;const e=this._getResolvedProvider(),i=!this._isVideoMediaLoaded&&this._shouldShowImageDuringLoading(),t={hidden:i};if("ha"===e||"image"===e){const e=O(this,this.hass,this.cameraConfig);if(!e)return;if("unavailable"===e.state)return A(this),$({message:`${s("error.live_camera_unavailable")}${this.label?`: ${this.label}`:""}`,type:"info",icon:"mdi:cctv-off",dotdotdot:!0})}return m`${this._useZoomIfRequired(m`
      ${i||"image"===e?m` <frigate-card-live-image
            ${b(this._refProvider)}
            .hass=${this.hass}
            .cameraConfig=${this.cameraConfig}
            @frigate-card:media:loaded=${i=>{"image"===e?this._videoMediaShowHandler():i.stopPropagation()}}
          >
          </frigate-card-live-image>`:m``}
      ${"ha"===e?m` <frigate-card-live-ha
            ${b(this._refProvider)}
            class=${j(t)}
            .hass=${this.hass}
            .cameraConfig=${this.cameraConfig}
            ?controls=${this.liveConfig.controls.builtin}
            @frigate-card:media:loaded=${this._videoMediaShowHandler.bind(this)}
          >
          </frigate-card-live-ha>`:"go2rtc"===e?m`<frigate-card-live-go2rtc
              ${b(this._refProvider)}
              class=${j(t)}
              .hass=${this.hass}
              .cameraConfig=${this.cameraConfig}
              .cameraEndpoints=${this.cameraEndpoints}
              .microphoneStream=${this.microphoneStream}
              .microphoneConfig=${this.liveConfig.microphone}
              ?controls=${this.liveConfig.controls.builtin}
              @frigate-card:media:loaded=${this._videoMediaShowHandler.bind(this)}
            >
            </frigate-card-live-go2rtc>`:"webrtc-card"===e?m`<frigate-card-live-webrtc-card
                ${b(this._refProvider)}
                class=${j(t)}
                .hass=${this.hass}
                .cameraConfig=${this.cameraConfig}
                .cameraEndpoints=${this.cameraEndpoints}
                .cardWideConfig=${this.cardWideConfig}
                ?controls=${this.liveConfig.controls.builtin}
                @frigate-card:media:loaded=${this._videoMediaShowHandler.bind(this)}
              >
              </frigate-card-live-webrtc-card>`:"jsmpeg"===e?m` <frigate-card-live-jsmpeg
                  ${b(this._refProvider)}
                  class=${j(t)}
                  .hass=${this.hass}
                  .cameraConfig=${this.cameraConfig}
                  .cameraEndpoints=${this.cameraEndpoints}
                  .cardWideConfig=${this.cardWideConfig}
                  @frigate-card:media:loaded=${this._videoMediaShowHandler.bind(this)}
                >
                </frigate-card-live-jsmpeg>`:m``}
    `)}
    ${i&&!this._isVideoMediaLoaded?m`<ha-icon
          title=${s("error.awaiting_live")}
          icon="mdi:progress-helper"
        ></ha-icon>`:""} `}static get styles(){return v(':host {\n  background-color: var(--primary-background-color);\n  background-position: center;\n  background-repeat: no-repeat;\n  background-image: url("data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgaW5rc2NhcGU6dmVyc2lvbj0iMS4yLjIgKGIwYTg0ODY1NDEsIDIwMjItMTItMDEpIgogICBzb2RpcG9kaTpkb2NuYW1lPSJjYW1lcmEtaXJpcy5zdmciCiAgIGlkPSJzdmc0IgogICB2ZXJzaW9uPSIxLjEiCiAgIHZpZXdCb3g9IjAgMCAyNCAyNCIKICAgeG1sbnM6aW5rc2NhcGU9Imh0dHA6Ly93d3cuaW5rc2NhcGUub3JnL25hbWVzcGFjZXMvaW5rc2NhcGUiCiAgIHhtbG5zOnNvZGlwb2RpPSJodHRwOi8vc29kaXBvZGkuc291cmNlZm9yZ2UubmV0L0RURC9zb2RpcG9kaS0wLmR0ZCIKICAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogICB4bWxuczpzdmc9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8ZGVmcwogICAgIGlkPSJkZWZzOCIgLz4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgaWQ9Im5hbWVkdmlldzYiCiAgICAgcGFnZWNvbG9yPSIjYjkzZTNlIgogICAgIGJvcmRlcmNvbG9yPSIjMDAwMDAwIgogICAgIGJvcmRlcm9wYWNpdHk9IjAuMjUiCiAgICAgaW5rc2NhcGU6c2hvd3BhZ2VzaGFkb3c9IjIiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAuNjA3ODQzMTQiCiAgICAgaW5rc2NhcGU6cGFnZWNoZWNrZXJib2FyZD0iZmFsc2UiCiAgICAgaW5rc2NhcGU6ZGVza2NvbG9yPSIjZDFkMWQxIgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIyNi42MjUwNiIKICAgICBpbmtzY2FwZTpjeD0iLTEuOTM0MjY4IgogICAgIGlua3NjYXBlOmN5PSIxNS42ODA3MTYiCiAgICAgaW5rc2NhcGU6d2luZG93LXdpZHRoPSIzODQwIgogICAgIGlua3NjYXBlOndpbmRvdy1oZWlnaHQ9IjE1MjciCiAgICAgaW5rc2NhcGU6d2luZG93LXg9IjEwODAiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9IjIyNyIKICAgICBpbmtzY2FwZTp3aW5kb3ctbWF4aW1pemVkPSIxIgogICAgIGlua3NjYXBlOmN1cnJlbnQtbGF5ZXI9InN2ZzQiIC8+CiAgPGcKICAgICBpZD0iZzExMTkiCiAgICAgc3R5bGU9ImZpbGwtb3BhY2l0eTowLjA1O2ZpbGw6I2ZmZmZmZiI+CiAgICA8Y2lyY2xlCiAgICAgICBzdHlsZT0iZmlsbDojZmZmZmZmO2ZpbGwtb3BhY2l0eTowLjA1O3N0cm9rZS13aWR0aDoxLjM5NzI5IgogICAgICAgaWQ9InBhdGgxNzAiCiAgICAgICBjeD0iMTIiCiAgICAgICBjeT0iMTIiCiAgICAgICBpbmtzY2FwZTpsYWJlbD0iV2hpdGUgQmFja2dyb3VuZCIKICAgICAgIHI9IjExLjI1IiAvPgogICAgPHBhdGgKICAgICAgIGQ9Ik0gMTMuNzMwMDAxLDE1IDkuODMwMDAwMywyMS43NiBDIDEwLjUzLDIxLjkxIDExLjI1LDIyIDEyLDIyIGMgMi40MDAwMDEsMCA0LjYsLTAuODUgNi4zMiwtMi4yNSBMIDE0LjY2MDAwMSwxMy40IE0gMi40NjAwMDAzLDE1IGMgMC45MiwyLjkyIDMuMTUsNS4yNiA1Ljk5LDYuMzQgTCAxMi4xMiwxNSBtIC0zLjU3OTk5OTcsLTMgLTMuOSwtNi43NDk5OTk2IGMgLTEuNjQsMS43NDk5OTkgLTIuNjQsNC4xMzk5OTkzIC0yLjY0LDYuNzQ5OTk5NiAwLDAuNjggMC4wNywxLjM1IDAuMiwyIGggNy40OSBNIDIxLjgsOS45OTk5OTk3IEggMTQuMzEwMDAxIEwgMTQuNjAwMDAxLDEwLjUgMTkuMzYsMTguNzUgQyAyMSwxNi45NyAyMiwxNC42IDIyLDEyIDIyLDExLjMxIDIxLjkzLDEwLjY0IDIxLjgsOS45OTk5OTk3IG0gLTAuMjYsLTEgQyAyMC42Miw2LjA3MDAwMDUgMTguMzksMy43NDAwMDAyIDE1LjU1MDAwMSwyLjY2MDAwMDIgTCAxMS44OCw4Ljk5OTk5OTcgTSA5LjQwMDAwMDMsMTAuNSAxNC4xNzAwMDEsMi4yNDAwMDAyIGMgLTAuNywtMC4xNSAtMS40MjAwMDEsLTAuMjQgLTIuMTcwMDAxLC0wLjI0IC0yLjM5OTk5OTcsMCAtNC41OTk5OTk3LDAuODQgLTYuMzE5OTk5NywyLjI1MDAwMDMgbCAzLjY2LDYuMzQ5OTk5NSB6IgogICAgICAgaWQ9InBhdGgyIgogICAgICAgaW5rc2NhcGU6bGFiZWw9IklyaXMiCiAgICAgICBzdHlsZT0iZmlsbC1vcGFjaXR5OjAuMDU7ZmlsbDojZmZmZmZmIiAvPgogIDwvZz4KPC9zdmc+Cg==");\n  background-size: 10%;\n  background-position: center;\n}\n\n:host {\n  display: block;\n  height: 100%;\n  width: 100%;\n  position: relative;\n}\n\n.hidden {\n  display: none;\n}\n\nha-icon {\n  position: absolute;\n  top: 10px;\n  right: 10px;\n  color: var(--primary-color);\n}')}};n([d({attribute:!1})],V.prototype,"hass",void 0),n([d({attribute:!1})],V.prototype,"cameraConfig",void 0),n([d({attribute:!1})],V.prototype,"cameraEndpoints",void 0),n([d({attribute:!1})],V.prototype,"liveConfig",void 0),n([d({attribute:!0,type:Boolean})],V.prototype,"load",void 0),n([d({attribute:!1})],V.prototype,"label",void 0),n([d({attribute:!1})],V.prototype,"cardWideConfig",void 0),n([d({attribute:!1})],V.prototype,"microphoneStream",void 0),n([d({attribute:!1})],V.prototype,"zoomSettings",void 0),n([h()],V.prototype,"_isVideoMediaLoaded",void 0),V=n([c(G)],V);var Y=Object.freeze({__proto__:null,get FrigateCardLive(){return W},get FrigateCardLiveCarousel(){return B},get FrigateCardLiveGrid(){return U},get FrigateCardLiveProvider(){return V}});export{O as g,Y as l};
