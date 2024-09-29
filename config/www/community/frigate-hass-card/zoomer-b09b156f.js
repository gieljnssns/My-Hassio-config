import{dc as t,dB as e,db as n,eh as o,ei as a,ej as i,ek as r,el as s,em as c,en as l,a as d,s as h,x as u,eo as m,_ as p,n as f,b as v,t as g}from"./card-6e374789.js";var _=function(){return _=Object.assign||function(t){for(var e,n=1,o=arguments.length;n<o;n++)for(var a in e=arguments[n])Object.prototype.hasOwnProperty.call(e,a)&&(t[a]=e[a]);return t},_.apply(this,arguments)};function w(t,e){for(var n=t.length;n--;)if(t[n].pointerId===e.pointerId)return n;return-1}function y(t,e){var n;if(e.touches){n=0;for(var o=0,a=e.touches;o<a.length;o++){var i=a[o];i.pointerId=n++,y(t,i)}}else(n=w(t,e))>-1&&t.splice(n,1),t.push(e)}function z(t){for(var e,n=(t=t.slice(0)).pop();e=t.pop();)n={clientX:(e.clientX-n.clientX)/2+n.clientX,clientY:(e.clientY-n.clientY)/2+n.clientY};return n}function b(t){if(t.length<2)return 0;var e=t[0],n=t[1];return Math.sqrt(Math.pow(Math.abs(n.clientX-e.clientX),2)+Math.pow(Math.abs(n.clientY-e.clientY),2))}"undefined"!=typeof window&&(window.NodeList&&!NodeList.prototype.forEach&&(NodeList.prototype.forEach=Array.prototype.forEach),"function"!=typeof window.CustomEvent&&(window.CustomEvent=function(t,e){e=e||{bubbles:!1,cancelable:!1,detail:null};var n=document.createEvent("CustomEvent");return n.initCustomEvent(t,e.bubbles,e.cancelable,e.detail),n}));var x={down:"mousedown",move:"mousemove",up:"mouseup mouseleave"};function S(t,e,n,o){x[t].split(" ").forEach((function(t){e.addEventListener(t,n,o)}))}function E(t,e,n){x[t].split(" ").forEach((function(t){e.removeEventListener(t,n)}))}function P(t){if(t.parentElement)return t.parentElement;var e=t.getRootNode();return e instanceof ShadowRoot&&e.host instanceof HTMLElement?e.host:void 0}"undefined"!=typeof window&&("function"==typeof window.PointerEvent?x={down:"pointerdown",move:"pointermove",up:"pointerup pointerleave pointercancel"}:"function"==typeof window.TouchEvent&&(x={down:"touchstart",move:"touchmove",up:"touchend touchcancel"}));var M,C="undefined"!=typeof document&&!!document.documentMode;function A(){return M||(M=document.createElement("div").style)}var O=["webkit","moz","ms"],X={};function Y(t){if(X[t])return X[t];var e=A();if(t in e)return X[t]=t;for(var n=t[0].toUpperCase()+t.slice(1),o=O.length;o--;){var a="".concat(O[o]).concat(n);if(a in e)return X[t]=a}}function H(t,e){return parseFloat(e[Y(t)])||0}function T(t,e,n){void 0===n&&(n=window.getComputedStyle(t));var o="border"===e?"Width":"";return{left:H("".concat(e,"Left").concat(o),n),right:H("".concat(e,"Right").concat(o),n),top:H("".concat(e,"Top").concat(o),n),bottom:H("".concat(e,"Bottom").concat(o),n)}}function U(t,e,n){t.style[Y(e)]=n}function k(t){var e=P(t),n=window.getComputedStyle(t),o=window.getComputedStyle(e),a=t.getBoundingClientRect(),i=e.getBoundingClientRect();return{elem:{style:n,width:a.width,height:a.height,top:a.top,bottom:a.bottom,left:a.left,right:a.right,margin:T(t,"margin",n),border:T(t,"border",n)},parent:{style:o,width:i.width,height:i.height,top:i.top,bottom:i.bottom,left:i.left,right:i.right,padding:T(e,"padding",o),border:T(e,"border",o)}}}function L(t,e){return 1===t.nodeType&&" ".concat(function(t){return(t.getAttribute("class")||"").trim()}(t)," ").indexOf(" ".concat(e," "))>-1}var Z=/^http:[\w\.\/]+svg$/;var D={animate:!1,canvas:!1,cursor:"move",disablePan:!1,disableZoom:!1,disableXAxis:!1,disableYAxis:!1,duration:200,easing:"ease-in-out",exclude:[],excludeClass:"panzoom-exclude",handleStartEvent:function(t){t.preventDefault(),t.stopPropagation()},maxScale:4,minScale:.125,overflow:"hidden",panOnlyWhenZoomed:!1,pinchAndPan:!1,relative:!1,setTransform:function(t,e,n){var o=e.x,a=e.y,i=e.scale,r=e.isSVG;if(U(t,"transform","scale(".concat(i,") translate(").concat(o,"px, ").concat(a,"px)")),r&&C){var s=window.getComputedStyle(t).getPropertyValue("transform");t.setAttribute("transform",s)}},startX:0,startY:0,startScale:1,step:.3,touchAction:"none"};function N(t,e){if(!t)throw new Error("Panzoom requires an element as an argument");if(1!==t.nodeType)throw new Error("Panzoom requires an element with a nodeType of 1");if(!function(t){for(var e=t;e&&e.parentNode;){if(e.parentNode===document)return!0;e=e.parentNode instanceof ShadowRoot?e.parentNode.host:e.parentNode}return!1}(t))throw new Error("Panzoom should be called on elements that have been attached to the DOM");e=_(_({},D),e);var n=function(t){return Z.test(t.namespaceURI)&&"svg"!==t.nodeName.toLowerCase()}(t),o=P(t);o.style.overflow=e.overflow,o.style.userSelect="none",o.style.touchAction=e.touchAction,(e.canvas?o:t).style.cursor=e.cursor,t.style.userSelect="none",t.style.touchAction=e.touchAction,U(t,"transformOrigin","string"==typeof e.origin?e.origin:n?"0 0":"50% 50%");var a,i,r,s,c,l,d=0,h=0,u=1,m=!1;function p(e,n,o){if(!o.silent){var a=new CustomEvent(e,{detail:n});t.dispatchEvent(a)}}function f(e,o,a){var i={x:d,y:h,scale:u,isSVG:n,originalEvent:a};return requestAnimationFrame((function(){"boolean"==typeof o.animate&&(o.animate?function(t,e){var n=Y("transform");U(t,"transition","".concat(n," ").concat(e.duration,"ms ").concat(e.easing))}(t,o):U(t,"transition","none")),o.setTransform(t,i,o),p(e,i,o),p("panzoomchange",i,o)})),i}function v(n,o,a,i){var r=_(_({},e),i),s={x:d,y:h,opts:r};if(!r.force&&(r.disablePan||r.panOnlyWhenZoomed&&u===r.startScale))return s;if(n=parseFloat(n),o=parseFloat(o),r.disableXAxis||(s.x=(r.relative?d:0)+n),r.disableYAxis||(s.y=(r.relative?h:0)+o),r.contain){var c=k(t),l=c.elem.width/u,m=c.elem.height/u,p=l*a,f=m*a,v=(p-l)/2,g=(f-m)/2;if("inside"===r.contain){var w=(-c.elem.margin.left-c.parent.padding.left+v)/a,y=(c.parent.width-p-c.parent.padding.left-c.elem.margin.left-c.parent.border.left-c.parent.border.right+v)/a;s.x=Math.max(Math.min(s.x,y),w);var z=(-c.elem.margin.top-c.parent.padding.top+g)/a,b=(c.parent.height-f-c.parent.padding.top-c.elem.margin.top-c.parent.border.top-c.parent.border.bottom+g)/a;s.y=Math.max(Math.min(s.y,b),z)}else if("outside"===r.contain){w=(-(p-c.parent.width)-c.parent.padding.left-c.parent.border.left-c.parent.border.right+v)/a,y=(v-c.parent.padding.left)/a;s.x=Math.max(Math.min(s.x,y),w);z=(-(f-c.parent.height)-c.parent.padding.top-c.parent.border.top-c.parent.border.bottom+g)/a,b=(g-c.parent.padding.top)/a;s.y=Math.max(Math.min(s.y,b),z)}}return r.roundPixels&&(s.x=Math.round(s.x),s.y=Math.round(s.y)),s}function g(n,o){var a=_(_({},e),o),i={scale:u,opts:a};if(!a.force&&a.disableZoom)return i;var r=e.minScale,s=e.maxScale;if(a.contain){var c=k(t),l=c.elem.width/u,d=c.elem.height/u;if(l>1&&d>1){var h=(c.parent.width-c.parent.border.left-c.parent.border.right)/l,m=(c.parent.height-c.parent.border.top-c.parent.border.bottom)/d;"inside"===e.contain?s=Math.min(s,h,m):"outside"===e.contain&&(r=Math.max(r,h,m))}}return i.scale=Math.min(Math.max(n,r),s),i}function M(t,e,o,a){var i=v(t,e,u,o);return d!==i.x||h!==i.y?(d=i.x,h=i.y,f("panzoompan",i.opts,a)):{x:d,y:h,scale:u,isSVG:n,originalEvent:a}}function C(t,e,n){var o=g(t,e),a=o.opts;if(a.force||!a.disableZoom){t=o.scale;var i=d,r=h;if(a.focal){var s=a.focal;i=(s.x/t-s.x/u+d*t)/t,r=(s.y/t-s.y/u+h*t)/t}var c=v(i,r,t,{relative:!1,force:!0});return d=c.x,h=c.y,u=t,f("panzoomzoom",a,n)}}function A(t,n){var o=_(_(_({},e),{animate:!0}),n);return C(u*Math.exp((t?1:-1)*o.step),o)}function O(e,o,a,i){var r=k(t),s=r.parent.width-r.parent.padding.left-r.parent.padding.right-r.parent.border.left-r.parent.border.right,c=r.parent.height-r.parent.padding.top-r.parent.padding.bottom-r.parent.border.top-r.parent.border.bottom,l=o.clientX-r.parent.left-r.parent.padding.left-r.parent.border.left-r.elem.margin.left,d=o.clientY-r.parent.top-r.parent.padding.top-r.parent.border.top-r.elem.margin.top;n||(l-=r.elem.width/u/2,d-=r.elem.height/u/2);var h={x:l/s*(s*e),y:d/c*(c*e)};return C(e,_(_({},a),{animate:!1,focal:h}),i)}C(e.startScale,{animate:!1,force:!0}),setTimeout((function(){M(e.startX,e.startY,{animate:!1,force:!0})}));var X=[];function H(t){if(!function(t,e){for(var n=t;n;n=P(n))if(L(n,e.excludeClass)||e.exclude.indexOf(n)>-1)return!0;return!1}(t.target,e)){y(X,t),m=!0,e.handleStartEvent(t),a=d,i=h,p("panzoomstart",{x:d,y:h,scale:u,isSVG:n,originalEvent:t},e);var o=z(X);r=o.clientX,s=o.clientY,c=u,l=b(X)}}function T(t){if(m&&void 0!==a&&void 0!==i&&void 0!==r&&void 0!==s){y(X,t);var n=z(X),o=X.length>1,d=u;if(o)0===l&&(l=b(X)),O(d=g((b(X)-l)*e.step/80+c).scale,n,{animate:!1},t);o&&!e.pinchAndPan||M(a+(n.clientX-r)/d,i+(n.clientY-s)/d,{animate:!1},t)}}function N(t){1===X.length&&p("panzoomend",{x:d,y:h,scale:u,isSVG:n,originalEvent:t},e),function(t,e){if(e.touches)for(;t.length;)t.pop();else{var n=w(t,e);n>-1&&t.splice(n,1)}}(X,t),m&&(m=!1,a=i=r=s=void 0)}var R=!1;function B(){R||(R=!0,S("down",e.canvas?o:t,H),S("move",document,T,{passive:!0}),S("up",document,N,{passive:!0}))}return e.noBind||B(),{bind:B,destroy:function(){R=!1,E("down",e.canvas?o:t,H),E("move",document,T),E("up",document,N)},eventNames:x,getPan:function(){return{x:d,y:h}},getScale:function(){return u},getOptions:function(){return function(t){var e={};for(var n in t)t.hasOwnProperty(n)&&(e[n]=t[n]);return e}(e)},handleDown:H,handleMove:T,handleUp:N,pan:M,reset:function(t){var n=_(_(_({},e),{animate:!0,force:!0}),t);u=g(n.startScale,n).scale;var o=v(n.startX,n.startY,u,n);return d=o.x,h=o.y,f("panzoomreset",n)},resetStyle:function(){o.style.overflow="",o.style.userSelect="",o.style.touchAction="",o.style.cursor="",t.style.cursor="",t.style.userSelect="",t.style.touchAction="",U(t,"transformOrigin","")},setOptions:function(n){for(var a in void 0===n&&(n={}),n)n.hasOwnProperty(a)&&(e[a]=n[a]);(n.hasOwnProperty("cursor")||n.hasOwnProperty("canvas"))&&(o.style.cursor=t.style.cursor="",(e.canvas?o:t).style.cursor=e.cursor),n.hasOwnProperty("overflow")&&(o.style.overflow=n.overflow),n.hasOwnProperty("touchAction")&&(o.style.touchAction=n.touchAction,t.style.touchAction=n.touchAction)},setStyle:function(e,n){return U(t,e,n)},zoom:C,zoomIn:function(t){return A(!0,t)},zoomOut:function(t){return A(!1,t)},zoomToPoint:O,zoomWithWheel:function(t,n){t.preventDefault();var o=_(_(_({},e),n),{animate:!1}),a=(0===t.deltaY&&t.deltaX?t.deltaX:t.deltaY)<0?1:-1;return O(g(u*Math.exp(a*o.step/3),o).scale,t,o,t)}}}N.defaultOptions=D;class R{constructor(o,a){this._zoomed=!1,this._default=!0,this._allowClick=!0,this._debouncedChangeHandler=t(this._changeHandler.bind(this),50),this._debouncedUpdater=t(this._updateBasedOnConfig.bind(this),50),this._resizeObserver=new ResizeObserver(this._debouncedUpdater),this._events=e()?{down:["pointerdown"],move:["pointermove"],up:["pointerup","pointerleave","pointercancel"]}:{down:["touchstart"],move:["touchmove"],up:["touchend","touchcancel"]},this._downHandler=t=>{this._shouldZoomOrPan(t)?(this._panzoom?.handleDown(t),t.stopPropagation(),t.preventDefault(),this._allowClick=!1):this._allowClick=!0},this._clickHandler=t=>{this._allowClick||(t.stopPropagation(),n(this._element,"focus")),this._allowClick=!0},this._moveHandler=t=>{this._shouldZoomOrPan(t)&&(this._panzoom?.handleMove(t),t.stopPropagation())},this._upHandler=t=>{this._shouldZoomOrPan(t)&&(this._panzoom?.handleUp(t),t.stopPropagation())},this._wheelHandler=t=>{t instanceof WheelEvent&&this._shouldZoomOrPan(t)&&(this._panzoom?.zoomWithWheel(t),t.stopPropagation())},this._element=o,this._settings=a?.config??null,this._defaultSettings=a?.defaultConfig??null}activate(){const t=this._getConfigToUse(),e=this._convertPercentToXYPan(t?.pan?.x??o,t?.pan?.y??a,t?.zoom??i);this._panzoom=N(this._element,{contain:"outside",maxScale:10,minScale:1,noBind:!0,cursor:void 0,touchAction:"",...t&&e&&{startX:e.x},...t&&e&&{startY:e.y},...t&&e&&{startScale:t.zoom??
/* istanbul ignore next @preserve */
i}});const n=(t,e,n)=>{t.forEach((t=>{this._element.addEventListener(t,e,n)}))};n(this._events.down,this._downHandler,{capture:!0}),n(this._events.move,this._moveHandler,{capture:!0}),n(this._events.up,this._upHandler,{capture:!0}),n(["wheel"],this._wheelHandler),n(["click"],this._clickHandler,{capture:!0}),this._resizeObserver.observe(this._element),this._element.addEventListener("panzoomchange",this._debouncedChangeHandler)}deactivate(){const t=(t,e,n)=>{t.forEach((t=>{this._element.removeEventListener(t,e,n)}))};t(this._events.down,this._downHandler,{capture:!0}),t(this._events.move,this._moveHandler,{capture:!0}),t(this._events.up,this._upHandler,{capture:!0}),t(["wheel"],this._wheelHandler),t(["click"],this._clickHandler,{capture:!0}),this._resizeObserver.disconnect(),this._element.removeEventListener("panzoomchange",this._debouncedChangeHandler)}setDefaultSettings(t){this._defaultSettings=t,this._debouncedUpdater()}setSettings(t){this._settings=t,this._debouncedUpdater()}_changeHandler(t){const e=t.detail,i=this._isUnzoomed(e.scale);i&&this._zoomed?(this._zoomed=!1,this._setTouchAction(!0),n(this._element,"zoom:unzoomed")):i||this._zoomed||(this._zoomed=!0,this._setTouchAction(!1),n(this._element,"zoom:zoomed"));const r=this._convertXYPanToPercent(e.x,e.y,e.scale),s={pan:{x:r?.x??o,y:r?.y??a},zoom:e.scale,isDefault:this._isAtDefaultZoomAndPan(e.x,e.y,e.scale),unzoomed:i};n(this._element,"zoom:change",s)}_isZoomEqual(t,e){return r(
/* istanbul ignore next @preserve */
t.zoom??i,
/* istanbul ignore next @preserve */
e.zoom??i,l)&&r(
/* istanbul ignore next @preserve */
t.pan?.x??o,
/* istanbul ignore next @preserve */
e.pan?.x??o,l)&&r(
/* istanbul ignore next @preserve */
t.pan?.y??a,
/* istanbul ignore next @preserve */
e.pan?.y??a,l)}_getConfigToUse(){return s(this._settings)?this._defaultSettings:this._settings}_updateBasedOnConfig(){if(!this._panzoom)return;const t=this._getConfigToUse(),e=t?.zoom??i,n=this._convertPercentToXYPan(t?.pan?.x??o,t?.pan?.y??a,e),r=n?.x??0,s=n?.y??0;this._isZoomEqual({zoom:e,pan:{x:r,y:s}},{zoom:this._panzoom.getScale(),pan:this._panzoom.getPan()})||(this._panzoom.zoom(e,{animate:!1}),window.requestAnimationFrame((()=>{this._panzoom?.pan(r,s,{animate:!0,duration:100})})))}_convertPercentToXYPan(t,e,n){const o=this._getTransformMinMax(n,this._panzoom?.getScale());return null===o?null:{x:o.minX+(o.maxX-o.minX)*(t/100),y:o.minY+(o.maxY-o.minY)*(e/100)}}_convertXYPanToPercent(t,e,n){const o=this._getTransformMinMax(n,this._panzoom?.getScale());return null===o?null:{x:(-t+Math.abs(o.minX))/(Math.abs(o.maxX)+Math.abs(o.minX))*100,y:(-e+Math.abs(o.minY))/(Math.abs(o.maxY)+Math.abs(o.minY))*100}}_getTransformMinMax(t,e){const n=this._getRenderedSize(e);if(!n.width||!n.height)return null;const o=n.width*(t-1)/t/2,a=n.height*(t-1)/t/2;return r(o,0)||r(a,0)?null:{minX:o,maxX:-o,minY:a,maxY:-a}}_getRenderedSize(t){const e=this._element.getBoundingClientRect();return{width:e.width/(t??i),height:e.height/(t??i)}}_isUnzoomed(t){return void 0!==t&&c(t,l)<=1}_isAtDefaultZoomAndPan(t,e,n){if(!this._defaultSettings)return this._isUnzoomed(n);const s=this._convertPercentToXYPan(this._defaultSettings.pan?.x??o,this._defaultSettings.pan?.y??a,this._defaultSettings.zoom??i);return!s||r(t,s.x)&&r(e,s.y)&&r(n,this._defaultSettings.zoom??
/* istanbul ignore next @preserve */
i)}_shouldZoomOrPan(t){return!this._isUnzoomed(this._panzoom?.getScale())||window.TouchEvent&&t instanceof TouchEvent&&t.touches.length>1||t instanceof WheelEvent&&t.ctrlKey}_setTouchAction(t){this._element.style.touchAction=t?"":"none"}}let B=class extends d{constructor(){super(...arguments),this._zoom=null,this._zoomed=!1,this._zoomHandler=()=>this._zoomed=!0,this._unzoomHandler=()=>this._zoomed=!1}connectedCallback(){super.connectedCallback(),this.addEventListener("frigate-card:zoom:zoomed",this._zoomHandler),this.addEventListener("frigate-card:zoom:unzoomed",this._unzoomHandler),this.requestUpdate()}disconnectedCallback(){this._zoom?.deactivate(),this.removeEventListener("frigate-card:zoom:zoomed",this._zoomHandler),this.removeEventListener("frigate-card:zoom:unzoomed",this._unzoomHandler)}willUpdate(t){t.has("_zoomed")&&h(this,this._zoomed,"zoomed"),this._zoom?(t.has("defaultSettings")&&this._zoom.setDefaultSettings(this.defaultSettings??null),t.has("settings")&&this.settings&&this._zoom.setSettings(this.settings)):(this._zoom=new R(this,{config:this.settings,defaultConfig:this.defaultSettings}),this._zoom.activate())}render(){return u` <slot></slot> `}static get styles(){return m`
      :host {
        width: 100%;
        height: 100%;
        display: block;
        cursor: auto;
      }
      :host([zoomed]) {
        cursor: move;
      }
    `}};p([f({attribute:!1})],B.prototype,"defaultSettings",void 0),p([f({attribute:!1})],B.prototype,"settings",void 0),p([v()],B.prototype,"_zoomed",void 0),B=p([g("frigate-card-zoomer")],B);export{B as FrigateCardZoomer};
