import{bL as e,d as n,bM as t}from"./card-f444d6e4.js";class r{getEngineType(){return e.Generic}async initializeCamera(e,n,t){return t}generateDefaultEventQuery(e,n,t){return null}generateDefaultRecordingQuery(e,n,t){return null}generateDefaultRecordingSegmentsQuery(e,n,t){return null}async getEvents(e,n,t,r){return null}async getRecordings(e,n,t,r){return null}async getRecordingSegments(e,n,t,r){return null}generateMediaFromEvents(e,n,t,r){return null}generateMediaFromRecordings(e,n,t,r){return null}async getMediaDownloadPath(e,n,t){return null}async favoriteMedia(e,n,t,r){}getQueryResultMaxAge(e){return null}async getMediaSeekTime(e,n,t,r,a){return null}async getMediaMetadata(e,n,t,r){return null}getCameraMetadata(e,r){return{title:r.title??n(e,r.camera_entity)??n(e,r.webrtc_card?.entity)??r.id??"",icon:r?.icon??t(e,r.camera_entity)??"mdi:video"}}getCameraCapabilities(e){return{canFavoriteEvents:!1,canFavoriteRecordings:!1,canSeek:!1,supportsClips:!1,supportsRecordings:!1,supportsSnapshots:!1,supportsTimeline:!1}}getMediaCapabilities(e){return null}getCameraEndpoints(e,n){return null}}export{r as GenericCameraManagerEngine};
