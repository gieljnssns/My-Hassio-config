import{ec as e,ed as t,l as a,dN as n,dL as r,dK as i,dI as s,j as l,ee as c}from"./card-61074723.js";class u{constructor(t,a,n){this._destroyCallbacks=[],this._stateChangeHandler=t=>{this._eventCallback?.({cameraID:this.getID(),type:e(t.newState.state)?"new":"end"})},this._config=t,this._engine=a,this._capabilities=n?.capabilities,this._eventCallback=n?.eventCallback}async initialize(e){return e.stateWatcher.subscribe(this._stateChangeHandler,this._config.triggers.entities),this._onDestroy((()=>e.stateWatcher.unsubscribe(this._stateChangeHandler))),this}async destroy(){this._destroyCallbacks.forEach((e=>e()))}getConfig(){return this._config}setID(e){this._config.id=e}getID(){if(this._config.id)return this._config.id;throw new t(a("error.no_camera_id"))}getEngine(){return this._engine}getCapabilities(){return this._capabilities??null}_onDestroy(e){this._destroyCallbacks.push(e)}}const o=(e,t)=>{const a=t?.url??e.go2rtc?.url,n=t?.stream??e.go2rtc?.stream;if(!a||!n)return null;const r=`${a}/api/ws?src=${n}`;return{endpoint:r,sign:r.startsWith("/")}};class g{constructor(e,t){this._stateWatcher=e,this._eventCallback=t}getEngineType(){return n.Generic}async createCamera(e,t){return await new u(t,this,{capabilities:new r({"favorite-events":!1,"favorite-recordings":!1,clips:!1,live:!0,menu:!0,recordings:!1,seek:!1,snapshots:!1,substream:!0,ptz:i(t)??void 0},{disable:t.capabilities?.disable,disableExcept:t.capabilities?.disable_except}),eventCallback:this._eventCallback}).initialize({stateWatcher:this._stateWatcher})}generateDefaultEventQuery(e,t,a){return null}generateDefaultRecordingQuery(e,t,a){return null}generateDefaultRecordingSegmentsQuery(e,t,a){return null}async getEvents(e,t,a,n){return null}async getRecordings(e,t,a,n){return null}async getRecordingSegments(e,t,a,n){return null}generateMediaFromEvents(e,t,a,n){return null}generateMediaFromRecordings(e,t,a,n){return null}async getMediaDownloadPath(e,t,a){return null}async favoriteMedia(e,t,a,n){}getQueryResultMaxAge(e){return null}async getMediaSeekTime(e,t,a,n,r){return null}async getMediaMetadata(e,t,a,n){return null}getCameraMetadata(e,t){const a=s(t);return{title:t.title??l(e,t.camera_entity)??l(e,t.webrtc_card?.entity)??t.id??"",icon:t?.icon??(a?c(e,a,"mdi:video"):"mdi:video")}}getMediaCapabilities(e){return null}getCameraEndpoints(e,t){const a=o(e);return a?{go2rtc:a}:null}async executePTZAction(e,t,a,n){}}var d=Object.freeze({__proto__:null,GenericCameraManagerEngine:g});export{u as C,g as G,d as e,o as g};
