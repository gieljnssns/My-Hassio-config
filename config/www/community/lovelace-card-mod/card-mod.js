<<<<<<< HEAD
var t,e,n,r,i,o,a,s;function u(t,e){return e||(e=t.slice(0)),Object.freeze(Object.defineProperties(t,{raw:{value:Object.freeze(e)}}))}function c(t,e){var n=Object.keys(t);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(t);e&&(r=r.filter((function(e){return Object.getOwnPropertyDescriptor(t,e).enumerable}))),n.push.apply(n,r)}return n}function l(t){for(var e=1;e<arguments.length;e++){var n=null!=arguments[e]?arguments[e]:{};e%2?c(Object(n),!0).forEach((function(e){d(t,e,n[e])})):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(n)):c(Object(n)).forEach((function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(n,e))}))}return t}function d(t,e,n){return(e=T(e))in t?Object.defineProperty(t,e,{value:n,enumerable:!0,configurable:!0,writable:!0}):t[e]=n,t}function h(){return h="undefined"!=typeof Reflect&&Reflect.get?Reflect.get.bind():function(t,e,n){var r=function(t,e){for(;!Object.prototype.hasOwnProperty.call(t,e)&&null!==(t=E(t)););return t}(t,e);if(r){var i=Object.getOwnPropertyDescriptor(r,e);return i.get?i.get.call(arguments.length<3?t:n):i.value}},h.apply(this,arguments)}function f(t){return function(t){if(Array.isArray(t))return O(t)}(t)||function(t){if("undefined"!=typeof Symbol&&null!=t[Symbol.iterator]||null!=t["@@iterator"])return Array.from(t)}(t)||S(t)||function(){throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}()}function v(t,e){return function(t){if(Array.isArray(t))return t}(t)||function(t,e){var n=null==t?null:"undefined"!=typeof Symbol&&t[Symbol.iterator]||t["@@iterator"];if(null!=n){var r,i,o,a,s=[],u=!0,c=!1;try{if(o=(n=n.call(t)).next,0===e){if(Object(n)!==n)return;u=!1}else for(;!(u=(r=o.call(n)).done)&&(s.push(r.value),s.length!==e);u=!0);}catch(t){c=!0,i=t}finally{try{if(!u&&null!=n.return&&(a=n.return(),Object(a)!==a))return}finally{if(c)throw i}}return s}}(t,e)||S(t,e)||function(){throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}()}function p(){p=function(){return e};var t,e={},n=Object.prototype,r=n.hasOwnProperty,i=Object.defineProperty||function(t,e,n){t[e]=n.value},o="function"==typeof Symbol?Symbol:{},a=o.iterator||"@@iterator",s=o.asyncIterator||"@@asyncIterator",u=o.toStringTag||"@@toStringTag";function c(t,e,n){return Object.defineProperty(t,e,{value:n,enumerable:!0,configurable:!0,writable:!0}),t[e]}try{c({},"")}catch(t){c=function(t,e,n){return t[e]=n}}function l(t,e,n,r){var o=e&&e.prototype instanceof g?e:g,a=Object.create(o.prototype),s=new j(r||[]);return i(a,"_invoke",{value:S(t,n,s)}),a}function d(t,e,n){try{return{type:"normal",arg:t.call(e,n)}}catch(t){return{type:"throw",arg:t}}}e.wrap=l;var h="suspendedStart",f="suspendedYield",v="executing",y="completed",m={};function g(){}function b(){}function _(){}var w={};c(w,a,(function(){return this}));var k=Object.getPrototypeOf,x=k&&k(k(T([])));x&&x!==n&&r.call(x,a)&&(w=x);var $=_.prototype=g.prototype=Object.create(w);function E(t){["next","throw","return"].forEach((function(e){c(t,e,(function(t){return this._invoke(e,t)}))}))}function A(t,e){function n(i,o,a,s){var u=d(t[i],t,o);if("throw"!==u.type){var c=u.arg,l=c.value;return l&&"object"==N(l)&&r.call(l,"__await")?e.resolve(l.__await).then((function(t){n("next",t,a,s)}),(function(t){n("throw",t,a,s)})):e.resolve(l).then((function(t){c.value=t,a(c)}),(function(t){return n("throw",t,a,s)}))}s(u.arg)}var o;i(this,"_invoke",{value:function(t,r){function i(){return new e((function(e,i){n(t,r,e,i)}))}return o=o?o.then(i,i):i()}})}function S(e,n,r){var i=h;return function(o,a){if(i===v)throw new Error("Generator is already running");if(i===y){if("throw"===o)throw a;return{value:t,done:!0}}for(r.method=o,r.arg=a;;){var s=r.delegate;if(s){var u=O(s,r);if(u){if(u===m)continue;return u}}if("next"===r.method)r.sent=r._sent=r.arg;else if("throw"===r.method){if(i===h)throw i=y,r.arg;r.dispatchException(r.arg)}else"return"===r.method&&r.abrupt("return",r.arg);i=v;var c=d(e,n,r);if("normal"===c.type){if(i=r.done?y:f,c.arg===m)continue;return{value:c.arg,done:r.done}}"throw"===c.type&&(i=y,r.method="throw",r.arg=c.arg)}}}function O(e,n){var r=n.method,i=e.iterator[r];if(i===t)return n.delegate=null,"throw"===r&&e.iterator.return&&(n.method="return",n.arg=t,O(e,n),"throw"===n.method)||"return"!==r&&(n.method="throw",n.arg=new TypeError("The iterator does not provide a '"+r+"' method")),m;var o=d(i,e.iterator,n.arg);if("throw"===o.type)return n.method="throw",n.arg=o.arg,n.delegate=null,m;var a=o.arg;return a?a.done?(n[e.resultName]=a.value,n.next=e.nextLoc,"return"!==n.method&&(n.method="next",n.arg=t),n.delegate=null,m):a:(n.method="throw",n.arg=new TypeError("iterator result is not an object"),n.delegate=null,m)}function P(t){var e={tryLoc:t[0]};1 in t&&(e.catchLoc=t[1]),2 in t&&(e.finallyLoc=t[2],e.afterLoc=t[3]),this.tryEntries.push(e)}function C(t){var e=t.completion||{};e.type="normal",delete e.arg,t.completion=e}function j(t){this.tryEntries=[{tryLoc:"root"}],t.forEach(P,this),this.reset(!0)}function T(e){if(e||""===e){var n=e[a];if(n)return n.call(e);if("function"==typeof e.next)return e;if(!isNaN(e.length)){var i=-1,o=function n(){for(;++i<e.length;)if(r.call(e,i))return n.value=e[i],n.done=!1,n;return n.value=t,n.done=!0,n};return o.next=o}}throw new TypeError(N(e)+" is not iterable")}return b.prototype=_,i($,"constructor",{value:_,configurable:!0}),i(_,"constructor",{value:b,configurable:!0}),b.displayName=c(_,u,"GeneratorFunction"),e.isGeneratorFunction=function(t){var e="function"==typeof t&&t.constructor;return!!e&&(e===b||"GeneratorFunction"===(e.displayName||e.name))},e.mark=function(t){return Object.setPrototypeOf?Object.setPrototypeOf(t,_):(t.__proto__=_,c(t,u,"GeneratorFunction")),t.prototype=Object.create($),t},e.awrap=function(t){return{__await:t}},E(A.prototype),c(A.prototype,s,(function(){return this})),e.AsyncIterator=A,e.async=function(t,n,r,i,o){void 0===o&&(o=Promise);var a=new A(l(t,n,r,i),o);return e.isGeneratorFunction(n)?a:a.next().then((function(t){return t.done?t.value:a.next()}))},E($),c($,u,"Generator"),c($,a,(function(){return this})),c($,"toString",(function(){return"[object Generator]"})),e.keys=function(t){var e=Object(t),n=[];for(var r in e)n.push(r);return n.reverse(),function t(){for(;n.length;){var r=n.pop();if(r in e)return t.value=r,t.done=!1,t}return t.done=!0,t}},e.values=T,j.prototype={constructor:j,reset:function(e){if(this.prev=0,this.next=0,this.sent=this._sent=t,this.done=!1,this.delegate=null,this.method="next",this.arg=t,this.tryEntries.forEach(C),!e)for(var n in this)"t"===n.charAt(0)&&r.call(this,n)&&!isNaN(+n.slice(1))&&(this[n]=t)},stop:function(){this.done=!0;var t=this.tryEntries[0].completion;if("throw"===t.type)throw t.arg;return this.rval},dispatchException:function(e){if(this.done)throw e;var n=this;function i(r,i){return s.type="throw",s.arg=e,n.next=r,i&&(n.method="next",n.arg=t),!!i}for(var o=this.tryEntries.length-1;o>=0;--o){var a=this.tryEntries[o],s=a.completion;if("root"===a.tryLoc)return i("end");if(a.tryLoc<=this.prev){var u=r.call(a,"catchLoc"),c=r.call(a,"finallyLoc");if(u&&c){if(this.prev<a.catchLoc)return i(a.catchLoc,!0);if(this.prev<a.finallyLoc)return i(a.finallyLoc)}else if(u){if(this.prev<a.catchLoc)return i(a.catchLoc,!0)}else{if(!c)throw new Error("try statement without catch or finally");if(this.prev<a.finallyLoc)return i(a.finallyLoc)}}}},abrupt:function(t,e){for(var n=this.tryEntries.length-1;n>=0;--n){var i=this.tryEntries[n];if(i.tryLoc<=this.prev&&r.call(i,"finallyLoc")&&this.prev<i.finallyLoc){var o=i;break}}o&&("break"===t||"continue"===t)&&o.tryLoc<=e&&e<=o.finallyLoc&&(o=null);var a=o?o.completion:{};return a.type=t,a.arg=e,o?(this.method="next",this.next=o.finallyLoc,m):this.complete(a)},complete:function(t,e){if("throw"===t.type)throw t.arg;return"break"===t.type||"continue"===t.type?this.next=t.arg:"return"===t.type?(this.rval=this.arg=t.arg,this.method="return",this.next="end"):"normal"===t.type&&e&&(this.next=e),m},finish:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var n=this.tryEntries[e];if(n.finallyLoc===t)return this.complete(n.completion,n.afterLoc),C(n),m}},catch:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var n=this.tryEntries[e];if(n.tryLoc===t){var r=n.completion;if("throw"===r.type){var i=r.arg;C(n)}return i}}throw new Error("illegal catch attempt")},delegateYield:function(e,n,r){return this.delegate={iterator:T(e),resultName:n,nextLoc:r},"next"===this.method&&(this.arg=t),m}},e}function y(t,e,n,r,i,o,a){try{var s=t[o](a),u=s.value}catch(t){return void n(t)}s.done?e(u):Promise.resolve(u).then(r,i)}function m(t){return function(){var e=this,n=arguments;return new Promise((function(r,i){var o=t.apply(e,n);function a(t){y(o,r,i,a,s,"next",t)}function s(t){y(o,r,i,a,s,"throw",t)}a(void 0)}))}}function g(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&$(t,e)}function b(t){var e=x();return function(){var n,r=E(t);if(e){var i=E(this).constructor;n=Reflect.construct(r,arguments,i)}else n=r.apply(this,arguments);return function(t,e){if(e&&("object"===N(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return _(t)}(this,n)}}function _(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function w(t){var e="function"==typeof Map?new Map:void 0;return w=function(t){if(null===t||!function(t){try{return-1!==Function.toString.call(t).indexOf("[native code]")}catch(e){return"function"==typeof t}}(t))return t;if("function"!=typeof t)throw new TypeError("Super expression must either be null or a function");if(void 0!==e){if(e.has(t))return e.get(t);e.set(t,n)}function n(){return k(t,arguments,E(this).constructor)}return n.prototype=Object.create(t.prototype,{constructor:{value:n,enumerable:!1,writable:!0,configurable:!0}}),$(n,t)},w(t)}function k(t,e,n){return k=x()?Reflect.construct.bind():function(t,e,n){var r=[null];r.push.apply(r,e);var i=new(Function.bind.apply(t,r));return n&&$(i,n.prototype),i},k.apply(null,arguments)}function x(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}function $(t,e){return $=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},$(t,e)}function E(t){return E=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},E(t)}function A(t,e){var n="undefined"!=typeof Symbol&&t[Symbol.iterator]||t["@@iterator"];if(!n){if(Array.isArray(t)||(n=S(t))||e&&t&&"number"==typeof t.length){n&&(t=n);var r=0,i=function(){};return{s:i,n:function(){return r>=t.length?{done:!0}:{done:!1,value:t[r++]}},e:function(t){throw t},f:i}}throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}var o,a=!0,s=!1;return{s:function(){n=n.call(t)},n:function(){var t=n.next();return a=t.done,t},e:function(t){s=!0,o=t},f:function(){try{a||null==n.return||n.return()}finally{if(s)throw o}}}}function S(t,e){if(t){if("string"==typeof t)return O(t,e);var n=Object.prototype.toString.call(t).slice(8,-1);return"Object"===n&&t.constructor&&(n=t.constructor.name),"Map"===n||"Set"===n?Array.from(t):"Arguments"===n||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?O(t,e):void 0}}function O(t,e){(null==e||e>t.length)&&(e=t.length);for(var n=0,r=new Array(e);n<e;n++)r[n]=t[n];return r}function P(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}function C(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,T(r.key),r)}}function j(t,e,n){return e&&C(t.prototype,e),n&&C(t,n),Object.defineProperty(t,"prototype",{writable:!1}),t}function T(t){var e=function(t,e){if("object"!=N(t)||!t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,e||"default");if("object"!=N(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return("string"===e?String:Number)(t)}(t,"string");return"symbol"==N(e)?e:String(e)}function N(t){return N="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},N(t)}function M(t,e,n,r){var i,o=arguments.length,a=o<3?e:null===r?r=Object.getOwnPropertyDescriptor(e,n):r;if("object"===("undefined"==typeof Reflect?"undefined":N(Reflect))&&"function"==typeof Reflect.decorate)a=Reflect.decorate(t,e,n,r);else for(var s=t.length-1;s>=0;s--)(i=t[s])&&(a=(o<3?i(a):o>3?i(e,n,a):i(e,n))||a);return o>3&&a&&Object.defineProperty(e,n,a),a}"function"==typeof SuppressedError&&SuppressedError;var R=globalThis,L=R.ShadowRoot&&(void 0===R.ShadyCSS||R.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,U=Symbol(),D=new WeakMap,H=function(){function t(e,n,r){if(P(this,t),this._$cssResult$=!0,r!==U)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=n}return j(t,[{key:"styleSheet",get:function(){var t=this.o,e=this.t;if(L&&void 0===t){var n=void 0!==e&&1===e.length;n&&(t=D.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),n&&D.set(e,t))}return t}},{key:"toString",value:function(){return this.cssText}}]),t}(),I=L?function(t){return t}:function(t){return t instanceof CSSStyleSheet?function(t){var e,n="",r=A(t.cssRules);try{for(r.s();!(e=r.n()).done;){n+=e.value.cssText}}catch(t){r.e(t)}finally{r.f()}return function(t){return new H("string"==typeof t?t:t+"",void 0,U)}(n)}(t):t},z=Object.is,q=Object.defineProperty,B=Object.getOwnPropertyDescriptor,V=Object.getOwnPropertyNames,J=Object.getOwnPropertySymbols,W=Object.getPrototypeOf,G=globalThis,F=G.trustedTypes,Y=F?F.emptyScript:"",K=G.reactiveElementPolyfillSupport,Z=function(t,e){return t},Q={toAttribute:function(t,e){switch(e){case Boolean:t=t?Y:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute:function(t,e){var n=t;switch(e){case Boolean:n=null!==t;break;case Number:n=null===t?null:Number(t);break;case Object:case Array:try{n=JSON.parse(t)}catch(t){n=null}}return n}},X=function(t,e){return!z(t,e)},tt={attribute:!0,type:String,converter:Q,reflect:!1,hasChanged:X};null!==(t=Symbol.metadata)&&void 0!==t||(Symbol.metadata=Symbol("metadata")),null!==(e=G.litPropertyMetadata)&&void 0!==e||(G.litPropertyMetadata=new WeakMap);var et=function(t){g(r,w(HTMLElement));var e,n=b(r);function r(){var t;return P(this,r),(t=n.call(this))._$Ep=void 0,t.isUpdatePending=!1,t.hasUpdated=!1,t._$Em=null,t._$Ev(),t}return j(r,[{key:"_$Ev",value:function(){var t,e=this;this._$Eg=new Promise((function(t){return e.enableUpdating=t})),this._$AL=new Map,this._$ES(),this.requestUpdate(),null===(t=this.constructor.l)||void 0===t||t.forEach((function(t){return t(e)}))}},{key:"addController",value:function(t){var e,n;(null!==(e=this._$E_)&&void 0!==e?e:this._$E_=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&(null===(n=t.hostConnected)||void 0===n||n.call(t))}},{key:"removeController",value:function(t){var e;null===(e=this._$E_)||void 0===e||e.delete(t)}},{key:"_$ES",value:function(){var t,e=new Map,n=A(this.constructor.elementProperties.keys());try{for(n.s();!(t=n.n()).done;){var r=t.value;this.hasOwnProperty(r)&&(e.set(r,this[r]),delete this[r])}}catch(t){n.e(t)}finally{n.f()}e.size>0&&(this._$Ep=e)}},{key:"createRenderRoot",value:function(){var t,e=null!==(t=this.shadowRoot)&&void 0!==t?t:this.attachShadow(this.constructor.shadowRootOptions);return function(t,e){if(L)t.adoptedStyleSheets=e.map((function(t){return t instanceof CSSStyleSheet?t:t.styleSheet}));else{var n,r=A(e);try{for(r.s();!(n=r.n()).done;){var i=n.value,o=document.createElement("style"),a=R.litNonce;void 0!==a&&o.setAttribute("nonce",a),o.textContent=i.cssText,t.appendChild(o)}}catch(t){r.e(t)}finally{r.f()}}}(e,this.constructor.elementStyles),e}},{key:"connectedCallback",value:function(){var t,e;null!==(t=this.renderRoot)&&void 0!==t||(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),null===(e=this._$E_)||void 0===e||e.forEach((function(t){var e;return null===(e=t.hostConnected)||void 0===e?void 0:e.call(t)}))}},{key:"enableUpdating",value:function(t){}},{key:"disconnectedCallback",value:function(){var t;null===(t=this._$E_)||void 0===t||t.forEach((function(t){var e;return null===(e=t.hostDisconnected)||void 0===e?void 0:e.call(t)}))}},{key:"attributeChangedCallback",value:function(t,e,n){this._$AK(t,n)}},{key:"_$EO",value:function(t,e){var n=this.constructor.elementProperties.get(t),r=this.constructor._$Eu(t,n);if(void 0!==r&&!0===n.reflect){var i,o=(void 0!==(null===(i=n.converter)||void 0===i?void 0:i.toAttribute)?n.converter:Q).toAttribute(e,n.type);this._$Em=t,null==o?this.removeAttribute(r):this.setAttribute(r,o),this._$Em=null}}},{key:"_$AK",value:function(t,e){var n=this.constructor,r=n._$Eh.get(t);if(void 0!==r&&this._$Em!==r){var i,o=n.getPropertyOptions(r),a="function"==typeof o.converter?{fromAttribute:o.converter}:void 0!==(null===(i=o.converter)||void 0===i?void 0:i.fromAttribute)?o.converter:Q;this._$Em=r,this[r]=a.fromAttribute(e,o.type),this._$Em=null}}},{key:"requestUpdate",value:function(t,e,n){var r=arguments.length>3&&void 0!==arguments[3]&&arguments[3],i=arguments.length>4?arguments[4]:void 0;if(void 0!==t){var o,a;if(null!==(o=n)&&void 0!==o||(n=this.constructor.getPropertyOptions(t)),!(null!==(a=n.hasChanged)&&void 0!==a?a:X)(r?i:this[t],e))return;this.C(t,e,n)}!1===this.isUpdatePending&&(this._$Eg=this._$EP())}},{key:"C",value:function(t,e,n){var r;this._$AL.has(t)||this._$AL.set(t,e),!0===n.reflect&&this._$Em!==t&&(null!==(r=this._$Ej)&&void 0!==r?r:this._$Ej=new Set).add(t)}},{key:"_$EP",value:(e=m(p().mark((function t(){var e;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return this.isUpdatePending=!0,t.prev=1,t.next=4,this._$Eg;case 4:t.next=9;break;case 6:t.prev=6,t.t0=t.catch(1),Promise.reject(t.t0);case 9:if(e=this.scheduleUpdate(),t.t1=null!=e,!t.t1){t.next=14;break}return t.next=14,e;case 14:return t.abrupt("return",!this.isUpdatePending);case 15:case"end":return t.stop()}}),t,this,[[1,6]])}))),function(){return e.apply(this,arguments)})},{key:"scheduleUpdate",value:function(){return this.performUpdate()}},{key:"performUpdate",value:function(){if(this.isUpdatePending){if(!this.hasUpdated){var t;if(null!==(t=this.renderRoot)&&void 0!==t||(this.renderRoot=this.createRenderRoot()),this._$Ep){var e,n=A(this._$Ep);try{for(n.s();!(e=n.n()).done;){var r=v(e.value,2),i=r[0],o=r[1];this[i]=o}}catch(t){n.e(t)}finally{n.f()}this._$Ep=void 0}var a=this.constructor.elementProperties;if(a.size>0){var s,u=A(a);try{for(u.s();!(s=u.n()).done;){var c=v(s.value,2),l=c[0],d=c[1];!0!==d.wrapped||this._$AL.has(l)||void 0===this[l]||this.C(l,this[l],d)}}catch(t){u.e(t)}finally{u.f()}}}var h=!1,f=this._$AL;try{var p;(h=this.shouldUpdate(f))?(this.willUpdate(f),null!==(p=this._$E_)&&void 0!==p&&p.forEach((function(t){var e;return null===(e=t.hostUpdate)||void 0===e?void 0:e.call(t)})),this.update(f)):this._$ET()}catch(f){throw h=!1,this._$ET(),f}h&&this._$AE(f)}}},{key:"willUpdate",value:function(t){}},{key:"_$AE",value:function(t){var e;null!==(e=this._$E_)&&void 0!==e&&e.forEach((function(t){var e;return null===(e=t.hostUpdated)||void 0===e?void 0:e.call(t)})),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}},{key:"_$ET",value:function(){this._$AL=new Map,this.isUpdatePending=!1}},{key:"updateComplete",get:function(){return this.getUpdateComplete()}},{key:"getUpdateComplete",value:function(){return this._$Eg}},{key:"shouldUpdate",value:function(t){return!0}},{key:"update",value:function(t){var e=this;this._$Ej&&(this._$Ej=this._$Ej.forEach((function(t){return e._$EO(t,e[t])}))),this._$ET()}},{key:"updated",value:function(t){}},{key:"firstUpdated",value:function(t){}}],[{key:"addInitializer",value:function(t){var e;this._$Ei(),(null!==(e=this.l)&&void 0!==e?e:this.l=[]).push(t)}},{key:"observedAttributes",get:function(){return this.finalize(),this._$Eh&&f(this._$Eh.keys())}},{key:"createProperty",value:function(t){var e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:tt;if(e.state&&(e.attribute=!1),this._$Ei(),this.elementProperties.set(t,e),!e.noAccessor){var n=Symbol(),r=this.getPropertyDescriptor(t,n,e);void 0!==r&&q(this.prototype,t,r)}}},{key:"getPropertyDescriptor",value:function(t,e,n){var r,i=null!==(r=B(this.prototype,t))&&void 0!==r?r:{get:function(){return this[e]},set:function(t){this[e]=t}},o=i.get,a=i.set;return{get:function(){return null==o?void 0:o.call(this)},set:function(e){var r=null==o?void 0:o.call(this);a.call(this,e),this.requestUpdate(t,r,n)},configurable:!0,enumerable:!0}}},{key:"getPropertyOptions",value:function(t){var e;return null!==(e=this.elementProperties.get(t))&&void 0!==e?e:tt}},{key:"_$Ei",value:function(){if(!this.hasOwnProperty(Z("elementProperties"))){var t=W(this);t.finalize(),void 0!==t.l&&(this.l=f(t.l)),this.elementProperties=new Map(t.elementProperties)}}},{key:"finalize",value:function(){if(!this.hasOwnProperty(Z("finalized"))){if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(Z("properties"))){var t,e=this.properties,n=A([].concat(f(V(e)),f(J(e))));try{for(n.s();!(t=n.n()).done;){var r=t.value;this.createProperty(r,e[r])}}catch(t){n.e(t)}finally{n.f()}}var i=this[Symbol.metadata];if(null!==i){var o=litPropertyMetadata.get(i);if(void 0!==o){var a,s=A(o);try{for(s.s();!(a=s.n()).done;){var u=v(a.value,2),c=u[0],l=u[1];this.elementProperties.set(c,l)}}catch(t){s.e(t)}finally{s.f()}}}this._$Eh=new Map;var d,h=A(this.elementProperties);try{for(h.s();!(d=h.n()).done;){var p=v(d.value,2),y=p[0],m=p[1],g=this._$Eu(y,m);void 0!==g&&this._$Eh.set(g,y)}}catch(t){h.e(t)}finally{h.f()}this.elementStyles=this.finalizeStyles(this.styles)}}},{key:"finalizeStyles",value:function(t){var e=[];if(Array.isArray(t)){var n,r=A(new Set(t.flat(1/0).reverse()));try{for(r.s();!(n=r.n()).done;){var i=n.value;e.unshift(I(i))}}catch(t){r.e(t)}finally{r.f()}}else void 0!==t&&e.push(I(t));return e}},{key:"_$Eu",value:function(t,e){var n=e.attribute;return!1===n?void 0:"string"==typeof n?n:"string"==typeof t?t.toLowerCase():void 0}}]),r}();et.elementStyles=[],et.shadowRootOptions={mode:"open"},et[Z("elementProperties")]=new Map,et[Z("finalized")]=new Map,null!=K&&K({ReactiveElement:et}),(null!==(n=G.reactiveElementVersions)&&void 0!==n?n:G.reactiveElementVersions=[]).push("2.0.2");var nt=globalThis,rt=nt.trustedTypes,it=rt?rt.createPolicy("lit-html",{createHTML:function(t){return t}}):void 0,ot="$lit$",at="lit$".concat((Math.random()+"").slice(9),"$"),st="?"+at,ut="<".concat(st,">"),ct=document,lt=function(){return ct.createComment("")},dt=function(t){return null===t||"object"!=N(t)&&"function"!=typeof t},ht=Array.isArray,ft="[ \t\n\f\r]",vt=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,pt=/-->/g,yt=/>/g,mt=RegExp(">|".concat(ft,"(?:([^\\s\"'>=/]+)(").concat(ft,"*=").concat(ft,"*(?:[^ \t\n\f\r\"'`<>=]|(\"|')|))|$)"),"g"),gt=/'/g,bt=/"/g,_t=/^(?:script|style|textarea|title)$/i,wt=function(t){return function(e){for(var n=arguments.length,r=new Array(n>1?n-1:0),i=1;i<n;i++)r[i-1]=arguments[i];return{_$litType$:t,strings:e,values:r}}}(1),kt=Symbol.for("lit-noChange"),xt=Symbol.for("lit-nothing"),$t=new WeakMap,Et=ct.createTreeWalker(ct,129);function At(t,e){if(!Array.isArray(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==it?it.createHTML(e):e}var St=function(t,e){for(var n,r=t.length-1,i=[],o=2===e?"<svg>":"",a=vt,s=0;s<r;s++){for(var u=t[s],c=void 0,l=void 0,d=-1,h=0;h<u.length&&(a.lastIndex=h,null!==(l=a.exec(u)));){var f;h=a.lastIndex,a===vt?"!--"===l[1]?a=pt:void 0!==l[1]?a=yt:void 0!==l[2]?(_t.test(l[2])&&(n=RegExp("</"+l[2],"g")),a=mt):void 0!==l[3]&&(a=mt):a===mt?">"===l[0]?(a=null!==(f=n)&&void 0!==f?f:vt,d=-1):void 0===l[1]?d=-2:(d=a.lastIndex-l[2].length,c=l[1],a=void 0===l[3]?mt:'"'===l[3]?bt:gt):a===bt||a===gt?a=mt:a===pt||a===yt?a=vt:(a=mt,n=void 0)}var v=a===mt&&t[s+1].startsWith("/>")?" ":"";o+=a===vt?u+ut:d>=0?(i.push(c),u.slice(0,d)+ot+u.slice(d)+at+v):u+at+(-2===d?s:v)}return[At(t,o+(t[r]||"<?>")+(2===e?"</svg>":"")),i]},Ot=function(){function t(e,n){var r,i=e.strings,o=e._$litType$;P(this,t),this.parts=[];var a=0,s=0,u=i.length-1,c=this.parts,l=v(St(i,o),2),d=l[0],h=l[1];if(this.el=t.createElement(d,n),Et.currentNode=this.el.content,2===o){var p=this.el.content.firstChild;p.replaceWith.apply(p,f(p.childNodes))}for(;null!==(r=Et.nextNode())&&c.length<u;){if(1===r.nodeType){if(r.hasAttributes()){var y,m=A(r.getAttributeNames());try{for(m.s();!(y=m.n()).done;){var g=y.value;if(g.endsWith(ot)){var b=h[s++],_=r.getAttribute(g).split(at),w=/([.?@])?(.*)/.exec(b);c.push({type:1,index:a,name:w[2],strings:_,ctor:"."===w[1]?Nt:"?"===w[1]?Mt:"@"===w[1]?Rt:Tt}),r.removeAttribute(g)}else g.startsWith(at)&&(c.push({type:6,index:a}),r.removeAttribute(g))}}catch(t){m.e(t)}finally{m.f()}}if(_t.test(r.tagName)){var k=r.textContent.split(at),x=k.length-1;if(x>0){r.textContent=rt?rt.emptyScript:"";for(var $=0;$<x;$++)r.append(k[$],lt()),Et.nextNode(),c.push({type:2,index:++a});r.append(k[x],lt())}}}else if(8===r.nodeType)if(r.data===st)c.push({type:2,index:a});else for(var E=-1;-1!==(E=r.data.indexOf(at,E+1));)c.push({type:7,index:a}),E+=at.length-1;a++}}return j(t,null,[{key:"createElement",value:function(t,e){var n=ct.createElement("template");return n.innerHTML=t,n}}]),t}();function Pt(t,e){var n,r,i,o,a,s=arguments.length>2&&void 0!==arguments[2]?arguments[2]:t,u=arguments.length>3?arguments[3]:void 0;if(e===kt)return e;var c=void 0!==u?null===(n=s._$Co)||void 0===n?void 0:n[u]:s._$Cl,l=dt(e)?void 0:e._$litDirective$;return(null===(r=c)||void 0===r?void 0:r.constructor)!==l&&(null!==(i=c)&&void 0!==i&&null!==(o=i._$AO)&&void 0!==o&&o.call(i,!1),void 0===l?c=void 0:(c=new l(t))._$AT(t,s,u),void 0!==u?(null!==(a=s._$Co)&&void 0!==a?a:s._$Co=[])[u]=c:s._$Cl=c),void 0!==c&&(e=Pt(t,c._$AS(t,e.values),c,u)),e}var Ct=function(){function t(e,n){P(this,t),this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=n}return j(t,[{key:"parentNode",get:function(){return this._$AM.parentNode}},{key:"_$AU",get:function(){return this._$AM._$AU}},{key:"u",value:function(t){var e,n=this._$AD,r=n.el.content,i=n.parts,o=(null!==(e=null==t?void 0:t.creationScope)&&void 0!==e?e:ct).importNode(r,!0);Et.currentNode=o;for(var a=Et.nextNode(),s=0,u=0,c=i[0];void 0!==c;){var l;if(s===c.index){var d=void 0;2===c.type?d=new jt(a,a.nextSibling,this,t):1===c.type?d=new c.ctor(a,c.name,c.strings,this,t):6===c.type&&(d=new Lt(a,this,t)),this._$AV.push(d),c=i[++u]}s!==(null===(l=c)||void 0===l?void 0:l.index)&&(a=Et.nextNode(),s++)}return Et.currentNode=ct,o}},{key:"p",value:function(t){var e,n=0,r=A(this._$AV);try{for(r.s();!(e=r.n()).done;){var i=e.value;void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,n),n+=i.strings.length-2):i._$AI(t[n])),n++}}catch(t){r.e(t)}finally{r.f()}}}]),t}(),jt=function(){function t(e,n,r,i){var o;P(this,t),this.type=2,this._$AH=xt,this._$AN=void 0,this._$AA=e,this._$AB=n,this._$AM=r,this.options=i,this._$Cv=null===(o=null==i?void 0:i.isConnected)||void 0===o||o}return j(t,[{key:"_$AU",get:function(){var t,e;return null!==(t=null===(e=this._$AM)||void 0===e?void 0:e._$AU)&&void 0!==t?t:this._$Cv}},{key:"parentNode",get:function(){var t,e=this._$AA.parentNode,n=this._$AM;return void 0!==n&&11===(null===(t=e)||void 0===t?void 0:t.nodeType)&&(e=n.parentNode),e}},{key:"startNode",get:function(){return this._$AA}},{key:"endNode",get:function(){return this._$AB}},{key:"_$AI",value:function(t){t=Pt(this,t,arguments.length>1&&void 0!==arguments[1]?arguments[1]:this),dt(t)?t===xt||null==t||""===t?(this._$AH!==xt&&this._$AR(),this._$AH=xt):t!==this._$AH&&t!==kt&&this._(t):void 0!==t._$litType$?this.g(t):void 0!==t.nodeType?this.$(t):function(t){return ht(t)||"function"==typeof(null==t?void 0:t[Symbol.iterator])}(t)?this.T(t):this._(t)}},{key:"k",value:function(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}},{key:"$",value:function(t){this._$AH!==t&&(this._$AR(),this._$AH=this.k(t))}},{key:"_",value:function(t){this._$AH!==xt&&dt(this._$AH)?this._$AA.nextSibling.data=t:this.$(ct.createTextNode(t)),this._$AH=t}},{key:"g",value:function(t){var e,n=t.values,r=t._$litType$,i="number"==typeof r?this._$AC(t):(void 0===r.el&&(r.el=Ot.createElement(At(r.h,r.h[0]),this.options)),r);if((null===(e=this._$AH)||void 0===e?void 0:e._$AD)===i)this._$AH.p(n);else{var o=new Ct(i,this),a=o.u(this.options);o.p(n),this.$(a),this._$AH=o}}},{key:"_$AC",value:function(t){var e=$t.get(t.strings);return void 0===e&&$t.set(t.strings,e=new Ot(t)),e}},{key:"T",value:function(e){ht(this._$AH)||(this._$AH=[],this._$AR());var n,r,i=this._$AH,o=0,a=A(e);try{for(a.s();!(r=a.n()).done;){var s=r.value;o===i.length?i.push(n=new t(this.k(lt()),this.k(lt()),this,this.options)):n=i[o],n._$AI(s),o++}}catch(t){a.e(t)}finally{a.f()}o<i.length&&(this._$AR(n&&n._$AB.nextSibling,o),i.length=o)}},{key:"_$AR",value:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:this._$AA.nextSibling,e=arguments.length>1?arguments[1]:void 0;for(null===(n=this._$AP)||void 0===n||n.call(this,!1,!0,e);t&&t!==this._$AB;){var n,r=t.nextSibling;t.remove(),t=r}}},{key:"setConnected",value:function(t){var e;void 0===this._$AM&&(this._$Cv=t,null===(e=this._$AP)||void 0===e||e.call(this,t))}}]),t}(),Tt=function(){function t(e,n,r,i,o){P(this,t),this.type=1,this._$AH=xt,this._$AN=void 0,this.element=e,this.name=n,this._$AM=i,this.options=o,r.length>2||""!==r[0]||""!==r[1]?(this._$AH=Array(r.length-1).fill(new String),this.strings=r):this._$AH=xt}return j(t,[{key:"tagName",get:function(){return this.element.tagName}},{key:"_$AU",get:function(){return this._$AM._$AU}},{key:"_$AI",value:function(t){var e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:this,n=arguments.length>2?arguments[2]:void 0,r=arguments.length>3?arguments[3]:void 0,i=this.strings,o=!1;if(void 0===i)t=Pt(this,t,e,0),(o=!dt(t)||t!==this._$AH&&t!==kt)&&(this._$AH=t);else{var a,s,u=t;for(t=i[0],a=0;a<i.length-1;a++){var c;(s=Pt(this,u[n+a],e,a))===kt&&(s=this._$AH[a]),o||(o=!dt(s)||s!==this._$AH[a]),s===xt?t=xt:t!==xt&&(t+=(null!==(c=s)&&void 0!==c?c:"")+i[a+1]),this._$AH[a]=s}}o&&!r&&this.O(t)}},{key:"O",value:function(t){t===xt?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,null!=t?t:"")}}]),t}(),Nt=function(t){g(n,Tt);var e=b(n);function n(){var t;return P(this,n),(t=e.apply(this,arguments)).type=3,t}return j(n,[{key:"O",value:function(t){this.element[this.name]=t===xt?void 0:t}}]),n}(),Mt=function(t){g(n,Tt);var e=b(n);function n(){var t;return P(this,n),(t=e.apply(this,arguments)).type=4,t}return j(n,[{key:"O",value:function(t){this.element.toggleAttribute(this.name,!!t&&t!==xt)}}]),n}(),Rt=function(t){g(n,Tt);var e=b(n);function n(t,r,i,o,a){var s;return P(this,n),(s=e.call(this,t,r,i,o,a)).type=5,s}return j(n,[{key:"_$AI",value:function(t){var e;if((t=null!==(e=Pt(this,t,arguments.length>1&&void 0!==arguments[1]?arguments[1]:this,0))&&void 0!==e?e:xt)!==kt){var n=this._$AH,r=t===xt&&n!==xt||t.capture!==n.capture||t.once!==n.once||t.passive!==n.passive,i=t!==xt&&(n===xt||r);r&&this.element.removeEventListener(this.name,this,n),i&&this.element.addEventListener(this.name,this,t),this._$AH=t}}},{key:"handleEvent",value:function(t){var e,n;"function"==typeof this._$AH?this._$AH.call(null!==(e=null===(n=this.options)||void 0===n?void 0:n.host)&&void 0!==e?e:this.element,t):this._$AH.handleEvent(t)}}]),n}(),Lt=function(){function t(e,n,r){P(this,t),this.element=e,this.type=6,this._$AN=void 0,this._$AM=n,this.options=r}return j(t,[{key:"_$AU",get:function(){return this._$AM._$AU}},{key:"_$AI",value:function(t){Pt(this,t)}}]),t}(),Ut=nt.litHtmlPolyfillSupport;null!=Ut&&Ut(Ot,jt),(null!==(r=nt.litHtmlVersions)&&void 0!==r?r:nt.litHtmlVersions=[]).push("3.1.0");var Dt=function(t){g(n,et);var e=b(n);function n(){var t;return P(this,n),(t=e.apply(this,arguments)).renderOptions={host:_(t)},t._$Do=void 0,t}return j(n,[{key:"createRenderRoot",value:function(){var t,e,r=h(E(n.prototype),"createRenderRoot",this).call(this);return null!==(e=(t=this.renderOptions).renderBefore)&&void 0!==e||(t.renderBefore=r.firstChild),r}},{key:"update",value:function(t){var e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),h(E(n.prototype),"update",this).call(this,t),this._$Do=function(t,e,n){var r,i=null!==(r=null==n?void 0:n.renderBefore)&&void 0!==r?r:e,o=i._$litPart$;if(void 0===o){var a,s=null!==(a=null==n?void 0:n.renderBefore)&&void 0!==a?a:null;i._$litPart$=o=new jt(e.insertBefore(lt(),s),s,void 0,null!=n?n:{})}return o._$AI(t),o}(e,this.renderRoot,this.renderOptions)}},{key:"connectedCallback",value:function(){var t;h(E(n.prototype),"connectedCallback",this).call(this),null===(t=this._$Do)||void 0===t||t.setConnected(!0)}},{key:"disconnectedCallback",value:function(){var t;h(E(n.prototype),"disconnectedCallback",this).call(this),null===(t=this._$Do)||void 0===t||t.setConnected(!1)}},{key:"render",value:function(){return kt}}]),n}();Dt._$litElement$=!0,Dt.finalized=!0,null===(i=globalThis.litElementHydrateSupport)||void 0===i||i.call(globalThis,{LitElement:Dt});var Ht=globalThis.litElementPolyfillSupport;null==Ht||Ht({LitElement:Dt}),(null!==(o=globalThis.litElementVersions)&&void 0!==o?o:globalThis.litElementVersions=[]).push("4.0.2");var It={attribute:!0,type:String,converter:Q,reflect:!1,hasChanged:X},zt=function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:It,e=arguments.length>1?arguments[1]:void 0,n=arguments.length>2?arguments[2]:void 0,r=n.kind,i=n.metadata,o=globalThis.litPropertyMetadata.get(i);if(void 0===o&&globalThis.litPropertyMetadata.set(i,o=new Map),o.set(n.name,t),"accessor"===r){var a=n.name;return{set:function(n){var r=e.get.call(this);e.set.call(this,n),this.requestUpdate(a,r,t)},init:function(e){return void 0!==e&&this.C(a,void 0,t),e}}}if("setter"===r){var s=n.name;return function(n){var r=this[s];e.call(this,n),this.requestUpdate(s,r,t)}}throw Error("Unsupported decorator location: "+r)};function qt(t){return function(e,n){return"object"==N(n)?zt(t,e,n):function(t,e,n){var r=e.hasOwnProperty(n);return e.constructor.createProperty(n,r?l(l({},t),{},{wrapped:!0}):t),r?Object.getOwnPropertyDescriptor(e,n):void 0}(t,e,n)}}function Bt(){return Vt.apply(this,arguments)}function Vt(){return Vt=m(p().mark((function t(){var e;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,Promise.race([customElements.whenDefined("home-assistant"),customElements.whenDefined("hc-main")]);case 2:e=customElements.get("home-assistant")?"home-assistant":"hc-main";case 3:if(document.querySelector(e)){t.next=8;break}return t.next=6,new Promise((function(t){return window.setTimeout(t,100)}));case 6:t.next=3;break;case 8:return t.abrupt("return",document.querySelector(e));case 9:case"end":return t.stop()}}),t)}))),Vt.apply(this,arguments)}function Jt(){return Wt.apply(this,arguments)}function Wt(){return Wt=m(p().mark((function t(){var e;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,Bt();case 2:e=t.sent;case 3:if(e.hass){t.next=8;break}return t.next=6,new Promise((function(t){return window.setTimeout(t,100)}));case 6:t.next=3;break;case 8:return t.abrupt("return",e.hass);case 9:case"end":return t.stop()}}),t)}))),Wt.apply(this,arguments)}var Gt="browser_mod-browser-id";window.cardMod_template_cache=window.cardMod_template_cache||{};var Ft=window.cardMod_template_cache;function Yt(t,e){var n=Ft[t];n&&(n.value=e.result,n.callbacks.forEach((function(t){return t(e.result)})))}function Kt(t,e,n){return Zt.apply(this,arguments)}function Zt(){return(Zt=m(p().mark((function t(e,n,r){var i,o,a,s;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,Jt();case 2:i=t.sent,o=i.connection,a=JSON.stringify([n,r]),(s=Ft[a])?(s.callbacks.has(e)||Qt(e),e(s.value),s.callbacks.add(e)):(Qt(e),e(""),r=Object.assign({user:i.user.name,browser:document.querySelector("hc-main")?"CAST":localStorage[Gt]?localStorage[Gt]:"",hash:location.hash.substr(1)||""},r),Ft[a]=s={template:n,variables:r,value:"",callbacks:new Set([e]),unsubscribe:o.subscribeMessage((function(t){return Yt(a,t)}),{type:"render_template",template:n,variables:r})});case 7:case"end":return t.stop()}}),t)})))).apply(this,arguments)}function Qt(t){return Xt.apply(this,arguments)}function Xt(){return(Xt=m(p().mark((function t(e){var n,r,i,o,a,s;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:r=0,i=Object.entries(Ft);case 1:if(!(r<i.length)){t.next=10;break}if(o=v(i[r],2),a=o[0],!(s=o[1]).callbacks.has(e)){t.next=7;break}return s.callbacks.delete(e),0==s.callbacks.size&&(n=s.unsubscribe,delete Ft[a]),t.abrupt("break",10);case 7:r++,t.next=1;break;case 10:if(!n){t.next=16;break}return t.next=13,n;case 13:return t.t0=t.sent,t.next=16,(0,t.t0)();case 16:case"end":return t.stop()}}),t)})))).apply(this,arguments)}var te="3.4.3",ee=function(){var t=m(p().mark((function t(){var e,n;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(!customElements.get("developer-tools-event")){t.next=2;break}return t.abrupt("return");case 2:return t.next=4,customElements.whenDefined("partial-panel-resolver");case 4:return(e=document.createElement("partial-panel-resolver")).hass={panels:[{url_path:"tmp",component_name:"developer-tools"}]},e._updateRoutes(),t.next=9,e.routerOptions.routes.tmp.load();case 9:return t.next=11,customElements.whenDefined("developer-tools-router");case 11:return n=document.createElement("developer-tools-router"),t.next=14,n.routerOptions.routes.event.load();case 14:case"end":return t.stop()}}),t)})));return function(){return t.apply(this,arguments)}}(),ne=function(){var t=m(p().mark((function t(e){var n;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,ee();case 2:return(n=document.createElement("ha-yaml-editor"))._onChange(new CustomEvent("yaml",{detail:{value:e}})),t.abrupt("return",n.value);case 5:case"end":return t.stop()}}),t)})));return function(e){return t.apply(this,arguments)}}();function re(t){return ie.apply(this,arguments)}function ie(){return ie=m(p().mark((function t(e){var n,r,i,o,a;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(e.type){t.next=2;break}return t.abrupt("return",null);case 2:return r=e.parentElement?e.parentElement:e,i=window.getComputedStyle(r).getPropertyValue("--card-mod-theme"),t.next=6,Jt();case 6:if(o=t.sent){t.next=9;break}return t.abrupt("return",{});case 9:if((a=null!==(n=null==o?void 0:o.themes.themes)&&void 0!==n?n:{})[i]){t.next=12;break}return t.abrupt("return",{});case 12:if(!a[i]["card-mod-".concat(e.type,"-yaml")]){t.next=16;break}return t.abrupt("return",ne(a[i]["card-mod-".concat(e.type,"-yaml")]));case 16:if(!a[i]["card-mod-".concat(e.type)]){t.next=20;break}return t.abrupt("return",{".":a[i]["card-mod-".concat(e.type)]});case 20:return t.abrupt("return",{});case 21:case"end":return t.stop()}}),t)}))),ie.apply(this,arguments)}var oe="SELECTTREE-TIMEOUT";function ae(t){return se.apply(this,arguments)}function se(){return se=m(p().mark((function t(e){var n,r,i,o=arguments;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(n=o.length>1&&void 0!==o[1]&&o[1],!(null===(r=e.localName)||void 0===r?void 0:r.includes("-"))){t.next=4;break}return t.next=4,customElements.whenDefined(e.localName);case 4:if(!e.updateComplete){t.next=7;break}return t.next=7,e.updateComplete;case 7:if(!n){t.next=18;break}if(!e.pageRendered){t.next=11;break}return t.next=11,e.pageRendered;case 11:if(!e._panelState){t.next=18;break}i=0;case 13:if(!("loaded"!==e._panelState&&i++<5)){t.next=18;break}return t.next=16,new Promise((function(t){return setTimeout(t,100)}));case 16:t.next=13;break;case 18:case"end":return t.stop()}}),t)}))),se.apply(this,arguments)}function ue(t,e){return ce.apply(this,arguments)}function ce(){return ce=m(p().mark((function t(e,n){var r,i,o,a,s,u,c,l=arguments;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:for(r=l.length>2&&void 0!==l[2]&&l[2],i=[e],"string"==typeof n&&(n=n.split(/(\$| )/));""===n[n.length-1];)n.pop();o=A(n.entries()),t.prev=5,o.s();case 7:if((a=o.n()).done){t.next=21;break}if(s=v(a.value,2),s[0],"$"!==(u=s[1])){t.next=12;break}return i=f(i).map((function(t){return t.shadowRoot})),t.abrupt("continue",19);case 12:if(c=i[0]){t.next=15;break}return t.abrupt("return",null);case 15:if(u.trim().length){t.next=17;break}return t.abrupt("continue",19);case 17:ae(c),i=c.querySelectorAll(u);case 19:t.next=7;break;case 21:t.next=26;break;case 23:t.prev=23,t.t0=t.catch(5),o.e(t.t0);case 26:return t.prev=26,o.f(),t.finish(26);case 29:return t.abrupt("return",r?i:i[0]);case 30:case"end":return t.stop()}}),t,null,[[5,23,26,29]])}))),ce.apply(this,arguments)}function le(t,e){return de.apply(this,arguments)}function de(){return de=m(p().mark((function t(e,n){var r,i,o=arguments;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return r=o.length>2&&void 0!==o[2]&&o[2],i=o.length>3&&void 0!==o[3]?o[3]:1e4,t.abrupt("return",Promise.race([ue(e,n,r),new Promise((function(t,e){return setTimeout((function(){return e(new Error(oe))}),i)}))]).catch((function(t){if(!t.message||t.message!==oe)throw t;return null})));case 3:case"end":return t.stop()}}),t)}))),de.apply(this,arguments)}var he=function(t){g(n,Dt);var e=b(n);function n(){var t;return P(this,n),(t=e.apply(this,arguments))._cardMod=[],t}return j(n,[{key:"setConfig",value:function(t,e){for(var n=arguments.length,r=new Array(n>2?n-2:0),i=2;i<n;i++)r[i-2]=arguments[i];null==t||t.apply(void 0,[e].concat(r)),this._cardMod.forEach((function(t){var n;t.variables={config:e},t.styles=(null===(n=e.card_mod)||void 0===n?void 0:n.style)||{}}))}},{key:"updated",value:function(t){for(var e=this,n=arguments.length,r=new Array(n>1?n-1:0),i=1;i<n;i++)r[i-1]=arguments[i];null==t||t.apply(void 0,r),Promise.all([this.updateComplete]).then((function(){return e._cardMod.forEach((function(t){var e;return null===(e=t.refresh)||void 0===e?void 0:e.call(t)}))}))}}]),n}();function fe(t,e){return ve.apply(this,arguments)}function ve(){return ve=m(p().mark((function t(e,n){var r,i,o,a,s,u,c,l=arguments;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return i=l.length>3&&void 0!==l[3]?l[3]:{},o=!(l.length>4&&void 0!==l[4])||l[4],c=!1,void 0!==(a=l.length>5&&void 0!==l[5]?l[5]:void 0)&&"string"!=typeof a&&(c=!0,o=a,a=void 0),"boolean"!=typeof o&&(o=!0,c=!0),"string"==typeof(r=l.length>2&&void 0!==l[2]?l[2]:void 0)&&(r={style:r},c=!0),r&&0!==Object.keys(r).length&&void 0===(null!==(u=null!==(s=null==r?void 0:r.style)&&void 0!==s?s:null==r?void 0:r.class)&&void 0!==u?u:null==r?void 0:r.debug)&&(r={style:r},c=!0),c&&!window.cm_compatibility_warning&&(window.cm_compatibility_warning=!0,console.groupCollapsed("Card-mod warning"),console.info("You are using a custom card which relies on card-mod, and uses an outdated signature for applyToElement."),console.info("The outdated signature will be removed at some point in the future. Hopefully the developer of your card will have updated their card by then."),console.info("The card used card-mod to apply styles here:",e),console.groupEnd()),t.abrupt("return",pe(e,n,r,i,o,a));case 11:case"end":return t.stop()}}),t)}))),ve.apply(this,arguments)}function pe(t,e){return ye.apply(this,arguments)}function ye(){return ye=m(p().mark((function t(e,n){var r,i,o,a,s,u,c,l,d,h,v,y,g,b,_,w=arguments;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(o=w.length>3&&void 0!==w[3]?w[3]:{},a=!(w.length>4&&void 0!==w[4])||w[4],s=w.length>5&&void 0!==w[5]?w[5]:void 0,g=(null==(i=w.length>2&&void 0!==w[2]?w[2]:void 0)?void 0:i.debug)?function(){for(var t,e=arguments.length,n=new Array(e),r=0;r<e;r++)n[r]=arguments[r];return(t=console).log.apply(t,["CardMod Debug:"].concat(n))}:function(){},g.apply(void 0,["Applying card-mod to:"].concat(f((null==e?void 0:e.host)?["#shadow-root of:",null==e?void 0:e.host]:[e]),["type: ",n,"configuration: ",i])),e){t.next=8;break}return t.abrupt("return");case 8:if(!(null===(u=e.localName)||void 0===u?void 0:u.includes("-"))){t.next=11;break}return t.next=11,customElements.whenDefined(e.localName);case 11:return e._cardMod=e._cardMod||[],b=null!==(c=e._cardMod.find((function(t){return t.type===n})))&&void 0!==c?c:document.createElement("card-mod"),g("Applying card-mod in:",b),b.type=n,b.debug=null!==(l=null==i?void 0:i.debug)&&void 0!==l&&l,e._cardMod.includes(b)||e._cardMod.push(b),window.setTimeout(m(p().mark((function t(){var n,r,s,u;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,Promise.all([e.updateComplete]);case 2:(u=(null!==(n=e.modElement)&&void 0!==n?n:a)&&null!==(r=e.shadowRoot)&&void 0!==r?r:e).contains(b)||u.appendChild(b),b.variables=o,b.styles=null!==(s=null==i?void 0:i.style)&&void 0!==s?s:"";case 6:case"end":return t.stop()}}),t)}))),1),_=null!==(v="string"==typeof(null==i?void 0:i.class)?null===(h=null===(d=null==i?void 0:i.class)||void 0===d?void 0:d.split)||void 0===h?void 0:h.call(d," "):null==i?void 0:i.class)&&void 0!==v?v:[],null===(y=e.classList)||void 0===y||(r=y).add.apply(r,f(_).concat([s])),t.abrupt("return",b);case 21:case"end":return t.stop()}}),t)}))),ye.apply(this,arguments)}function me(t,e){var n=function(t){return t&&"object"===N(t)&&!Array.isArray(t)};if(n(t)&&n(e))for(var r in e)n(e[r])?(t[r]||Object.assign(t,d({},r,{})),"string"==typeof t[r]&&(t[r]={".":t[r]}),me(t[r],e[r])):t[r]?t[r]=e[r]+t[r]:t[r]=e[r];return t}function ge(t,e){if(t===e)return!0;if(N(t)!==N(e))return!1;if(!(t instanceof Object&&e instanceof Object))return!1;for(var n in t)if(t.hasOwnProperty(n)){if(!e.hasOwnProperty(n))return!1;if(t[n]!==e[n]){if("object"!==N(t[n]))return!1;if(!ge(t[n],e[n]))return!1}}for(var r in e)if(e.hasOwnProperty(r)&&!t.hasOwnProperty(r))return!1;return!0}var be=function(t){g(s,Dt);var e,n,r,i,o=b(s);function s(){var t;return P(this,s),(t=o.call(this)).card_mod_children={},t.card_mod_parent=void 0,t.debug=!1,t._fixed_styles={},t._styles="",t._rendered_styles="",t._observer=new MutationObserver((function(e){var n,r=A(e);try{for(r.s();!(n=r.n()).done;){var i=n.value;if("card-mod"===i.target.localName)return;i.addedNodes.length&&i.addedNodes.forEach((function(t){t.localName})),i.removedNodes.length&&i.removedNodes.forEach((function(t){t.localName}))}}catch(t){r.e(t)}finally{r.f()}stop||t.refresh()})),document.addEventListener("cm_update",(function(){t._process_styles(t.card_mod_input)})),t}return j(s,[{key:"connectedCallback",value:function(){h(E(s.prototype),"connectedCallback",this).call(this),this.refresh(),this.setAttribute("slot","none"),this.style.display="none"}},{key:"disconnectedCallback",value:function(){h(E(s.prototype),"disconnectedCallback",this).call(this),this._disconnect()}},{key:"styles",get:function(){return this._styles},set:function(t){ge(t,this.card_mod_input)||(this.card_mod_input=t,this._process_styles(t))}},{key:"refresh",value:function(){this._connect()}},{key:"_debug",value:function(){for(var t,e=arguments.length,n=new Array(e),r=0;r<e;r++)n[r]=arguments[r];this.debug&&(t=console).log.apply(t,["CardMod Debug:"].concat(n))}},{key:"_process_styles",value:(i=m(p().mark((function t(e){var n,r;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return n="string"==typeof e?{".":e}:JSON.parse(JSON.stringify(e)),t.next=3,re(this);case 3:r=t.sent,me(n,r),this._fixed_styles=n,this.refresh();case 7:case"end":return t.stop()}}),t,this)}))),function(t){return i.apply(this,arguments)})},{key:"_style_child",value:(r=m(p().mark((function t(e,n){var r,i,o,a=this,s=arguments;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return r=s.length>2&&void 0!==s[2]?s[2]:0,i=this.parentElement||this.parentNode,t.next=4,le(i,e,!0);case 4:if((o=t.sent)&&o.length){t.next=11;break}if(!(r>5)){t.next=8;break}throw new Error("NoElements");case 8:return t.next=10,new Promise((function(t){return setTimeout(t,100*r)}));case 10:return t.abrupt("return",this._style_child(e,n,r+1));case 11:return t.abrupt("return",f(o).map(function(){var t=m(p().mark((function t(e){var r;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,pe(e,"".concat(a.type,"-child"),{style:n,debug:a.debug},a.variables,!1);case 2:return(r=t.sent)&&(r.card_mod_parent=a),t.abrupt("return",r);case 5:case"end":return t.stop()}}),t)})));return function(e){return t.apply(this,arguments)}}()));case 12:case"end":return t.stop()}}),t,this)}))),function(t,e){return r.apply(this,arguments)})},{key:"_connect",value:(n=m(p().mark((function t(){var e,n,r,i,o,a,s,u,c,l,d,h,f,y=this;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:o=null!==(e=this._fixed_styles)&&void 0!==e?e:{},a={},s="",u=!1,this.parentElement||this.parentNode,this._debug("(Re)connecting",this),c=p().mark((function t(){var e,n,r;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:e=v(d[l],2),n=e[0],r=e[1],"."===n?"string"==typeof r?s=r:y._debug("Style of '.' must be a string: ",r):(u=!0,a[n]=y._style_child(n,r).catch((function(t){if("NoElements"!=t.message)throw t;y.debug&&(console.groupCollapsed("card-mod found no elements"),console.info("Looked for ".concat(n)),console.info(y),console.groupEnd())})));case 2:case"end":return t.stop()}}),t)})),l=0,d=Object.entries(o);case 8:if(!(l<d.length)){t.next=13;break}return t.delegateYield(c(),"t0",10);case 10:l++,t.next=8;break;case 13:t.t1=p().keys(this.card_mod_children);case 14:if((t.t2=t.t1()).done){t.next=30;break}if(h=t.t2.value,a[h]){t.next=28;break}return t.next=19,this.card_mod_children[h];case 19:if(t.t4=n=t.sent,t.t3=null===t.t4,t.t3){t.next=23;break}t.t3=void 0===n;case 23:if(!t.t3){t.next=27;break}t.next=28;break;case 27:n.forEach(function(){var t=m(p().mark((function t(e){return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,e;case 2:return t.abrupt("return",t.sent.styles="");case 3:case"end":return t.stop()}}),t)})));return function(e){return t.apply(this,arguments)}}());case 28:t.next=14;break;case 30:if(this.card_mod_children=a,this._styles!==s){t.next=33;break}return t.abrupt("return");case 33:this._styles=s,(g=this._styles)&&(String(g).includes("{%")||String(g).includes("{{"))?(this._renderer=this._renderer||this._style_rendered.bind(this),Kt(this._renderer,this._styles,this.variables)):this._style_rendered(this._styles||""),u&&(this._observer.disconnect(),f=null!==(r=this.parentElement)&&void 0!==r?r:this.parentNode,this._observer.observe(null!==(i=null==f?void 0:f.host)&&void 0!==i?i:f,{childList:!0}));case 36:case"end":return t.stop()}var g}),t,this)}))),function(){return n.apply(this,arguments)})},{key:"_disconnect",value:(e=m(p().mark((function t(){var e,n;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return this._observer.disconnect(),this._styles="",t.next=4,Qt(this._renderer);case 4:null===(n=null===(e=this.card_mod_parent)||void 0===e?void 0:e.refresh)||void 0===n||n.call(e);case 5:case"end":return t.stop()}}),t,this)}))),function(){return e.apply(this,arguments)})},{key:"_style_rendered",value:function(t){this._rendered_styles!==t&&(this._rendered_styles=t),this.dispatchEvent(new Event("card-mod-update"))}},{key:"createRenderRoot",value:function(){return this}},{key:"render",value:function(){return wt(a||(a=u(["\n      <style>\n        ","\n      </style>\n    "])),this._rendered_styles)}}],[{key:"applyToElement",get:function(){return fe}}]),s}();M([qt({attribute:"card-mod-type",reflect:!0})],be.prototype,"type",void 0),M([qt()],be.prototype,"_rendered_styles",void 0),customElements.get("card-mod")||(customElements.define("card-mod",be),console.info("%cCARD-MOD ".concat(te," IS INSTALLED"),"color: green; font-weight: bold")),m(p().mark((function t(){return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(void 0!==customElements.get("home-assistant")){t.next=5;break}return t.next=3,new Promise((function(t){return window.setTimeout(t,100)}));case 3:t.next=0;break;case 5:customElements.get("card-mod")||customElements.define("card-mod",be);case 6:case"end":return t.stop()}}),t)})))();var _e=function(t,e,n){if("constructor"!==e){var r=t[e];if(!(null==r?void 0:r.cm_patched)){var i=function(){for(var t=arguments.length,e=new Array(t),i=0;i<t;i++)e[i]=arguments[i];try{return n.call.apply(n,[this,null==r?void 0:r.bind(this)].concat(e))}catch(t){return console.error("Card-mod",t),null==r?void 0:r.bind(this).apply(void 0,e)}};i.cm_patched=!0,t[e]=i}}},we=function(t,e){if(t)for(var n in Object.getOwnPropertyDescriptors(e.prototype))_e(t,n,e.prototype[n])},ke=function(){var t=m(p().mark((function t(e,n,r){var i;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if("string"!=typeof e){t.next=4;break}return t.next=3,customElements.whenDefined(e);case 3:e=customElements.get(e);case 4:return i=we(e.prototype,n),null==r||r(),t.abrupt("return",i);case 7:case"end":return t.stop()}}),t)})));return function(e,n,r){return t.apply(this,arguments)}}();function xe(t,e){return function(n){ke(t,n,e)}}var $e=function(t){g(r,he);var e,n=b(r);function r(){var t;return P(this,r),(t=n.apply(this,arguments))._cardMod=[],t}return j(r,[{key:"firstUpdated",value:(e=m(p().mark((function t(e){var n,r,i,o,a,s,u,c,l,d=arguments;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:for(o=d.length,a=new Array(o>1?o-1:0),s=1;s<o;s++)a[s-1]=d[s];return t.next=3,null==e?void 0:e.apply(void 0,a);case 3:return u=Ee(this),c="type-".concat(null===(r=null===(n=null==u?void 0:u.type)||void 0===n?void 0:n.replace)||void 0===r?void 0:r.call(n,":","-")),t.next=7,pe(this,"card",null==u?void 0:u.card_mod,{config:u},!1,c);case 7:if(l=null===(i=this.parentNode)||void 0===i?void 0:i.host){t.next=10;break}return t.abrupt("return");case 10:we(l,he),l._cardMod=this._cardMod;case 12:case"end":return t.stop()}}),t,this)}))),function(t){return e.apply(this,arguments)})}]),r}();function Ee(t){return t.config?t.config:t._config?t._config:t.host?Ee(t.host):t.parentElement?Ee(t.parentElement):t.parentNode?Ee(t.parentNode):null}$e=M([xe("ha-card")],$e);var Ae=function(t){g(n,he);var e=b(n);function n(){return P(this,n),e.apply(this,arguments)}return j(n,[{key:"renderEntity",value:function(t,e){for(var n,r,i=arguments.length,o=new Array(i>2?i-2:0),a=2;a<i;a++)o[a-2]=arguments[a];var s=null==t?void 0:t.apply(void 0,[e].concat(o));if("custom:mod-card"===(null==e?void 0:e.type))return s;if(!(null==s?void 0:s.values))return s;var u=s.values[0];if(!u)return s;var c="type-".concat(null===(r=null===(n=null==e?void 0:e.type)||void 0===n?void 0:n.replace)||void 0===r?void 0:r.call(n,":","-")),l=function(){var t=m(p().mark((function t(){return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,ae(u);case 2:we(u,he),pe(u,"row",null==e?void 0:e.card_mod,{config:e},!0,c),u.addEventListener("ll-rebuild",l);case 5:case"end":return t.stop()}}),t)})));return function(){return t.apply(this,arguments)}}();return Promise.all([this.updateComplete]).then((function(){return l()})),s}}]),n}();Ae=M([xe("hui-entities-card")],Ae);var Se=function(t){g(n,he);var e=b(n);function n(){return P(this,n),e.apply(this,arguments)}return j(n,[{key:"updated",value:function(t){for(var e,n,r,i=arguments.length,o=new Array(i>1?i-1:0),a=1;a<i;a++)o[a-1]=arguments[a];null==t||t.apply(void 0,o);var s,u=A(this.shadowRoot.querySelectorAll("ha-card div.entity"));try{for(u.s();!(s=u.n()).done;){var c=s.value;we(c,he);for(var l=null!==(e=c.shadowRoot)&&void 0!==e?e:c.attachShadow({mode:"open"});c.firstChild;)l.append(c.firstChild);var d=null!==(n=c.querySelector("style[card-mod]"))&&void 0!==n?n:document.createElement("style");d.setAttribute("card-mod",""),d.innerHTML="\ndiv {\n  width: 100%;\n  text-align: center;\n  white-space: nowrap;\n  overflow: hidden;\n  text-overflow: ellipsis;\n}\n.name {\n  min-height: var(--paper-font-body1_-_line-height, 20px);\n}\nstate-badge {\n  margin: 8px 0;\n}\n",l.append(d);var h=null!==(r=c.config)&&void 0!==r?r:c.entityConfig;pe(c,"glance",null==h?void 0:h.card_mod,{config:h})}}catch(t){u.e(t)}finally{u.f()}}}]),n}();Se=M([xe("hui-glance-card")],Se);var Oe=function(t){g(r,he);var e,n=b(r);function r(){return P(this,r),n.apply(this,arguments)}return j(r,[{key:"firstUpdated",value:(e=m(p().mark((function t(e){var n,r,i,o,a=arguments;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:for(n=a.length,r=new Array(n>1?n-1:0),i=1;i<n;i++)r[i-1]=a[i];return t.next=3,null==e?void 0:e.apply(void 0,r);case 3:return o=this._config,t.next=6,pe(this,"badge",null==o?void 0:o.card_mod,{config:o});case 6:case"end":return t.stop()}}),t,this)}))),function(t){return e.apply(this,arguments)})}]),r}();Oe=M([xe("hui-state-label-badge")],Oe);var Pe=function(t){g(n,he);var e=b(n);function n(){return P(this,n),e.apply(this,arguments)}return j(n,[{key:"updated",value:function(t){for(var e=arguments.length,n=new Array(e>1?e-1:0),r=1;r<e;r++)n[r-1]=arguments[r];null==t||t.apply(void 0,n),pe(this,"view",void 0,{},!1)}}]),n}();Pe=M([xe("hui-view")],Pe);var Ce=function(t){g(n,he);var e=b(n);function n(){return P(this,n),e.apply(this,arguments)}return j(n,[{key:"firstUpdated",value:function(t){for(var e=arguments.length,n=new Array(e>1?e-1:0),r=1;r<e;r++)n[r-1]=arguments[r];null==t||t.apply(void 0,n),pe(this,"root")}}]),n}();Ce=M([xe("hui-root",(function(){le(document,"home-assistant$home-assistant-main$partial-panel-resolver ha-panel-lovelace$hui-root",!1).then((function(t){return null==t?void 0:t.firstUpdated()}))}))],Ce);var je=function(t){g(n,he);var e=b(n);function n(){return P(this,n),e.apply(this,arguments)}return j(n,[{key:"showDialog",value:function(t,e){for(var n=this,r=arguments.length,i=new Array(r>2?r-2:0),o=2;o<r;o++)i[o-2]=arguments[o];null==t||t.apply(void 0,[e].concat(i)),this.requestUpdate(),this.updateComplete.then(m(p().mark((function t(){var r;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(r=n.shadowRoot.querySelector("ha-dialog")){t.next=3;break}return t.abrupt("return");case 3:pe(r,"more-info",void 0,{config:e},!1);case 4:case"end":return t.stop()}}),t)}))))}}]),n}();je=M([xe("ha-more-info-dialog")],je);var Te=function(t){g(n,he);var e=b(n);function n(){return P(this,n),e.apply(this,arguments)}return j(n,[{key:"firstUpdated",value:function(t){for(var e=arguments.length,n=new Array(e>1?e-1:0),r=1;r<e;r++)n[r-1]=arguments[r];null==t||t.apply(void 0,n),pe(this,"sidebar")}}]),n}();Te=M([xe("ha-sidebar",(function(){le(document,"home-assistant$home-assistant-main$ha-sidebar",!1).then((function(t){return null==t?void 0:t.firstUpdated()}))}))],Te);var Ne=function(t){g(n,Dt);var e=b(n);function n(){return P(this,n),e.apply(this,arguments)}return j(n,[{key:"setConfig",value:function(t,e){var n,r,i,o,a,s=JSON.parse(JSON.stringify(e));if(this._cardModData={card:s.card_mod,entities:[]},delete s.card_mod,Array.isArray(s.entities)){var u,c=A(null===(r=null===(n=s.entities)||void 0===n?void 0:n.entries)||void 0===r?void 0:r.call(n));try{for(c.s();!(u=c.n()).done;){var l=v(u.value,2),d=l[0],h=l[1];this._cardModData.entities[d]=h.card_mod,delete h.card_mod}}catch(t){c.e(t)}finally{c.f()}}for(var f=arguments.length,p=new Array(f>2?f-2:0),y=2;y<f;y++)p[y-2]=arguments[y];if(t.apply(void 0,[s].concat(p)),Array.isArray(s.entities)){var m,g=A(null===(o=null===(i=s.entities)||void 0===i?void 0:i.entries)||void 0===o?void 0:o.call(i));try{for(g.s();!(m=g.n()).done;){var b=v(m.value,2),_=b[0],w=b[1];(null===(a=this._cardModData)||void 0===a?void 0:a.entities[_])&&(w.card_mod=this._cardModData.entities[_])}}catch(t){g.e(t)}finally{g.f()}}}}]),n}(),Me=function(t){g(r,Dt);var e,n=b(r);function r(){return P(this,r),n.apply(this,arguments)}return j(r,[{key:"getConfigElement",value:(e=m(p().mark((function t(e){var n,r,i,o,a=arguments;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:for(n=a.length,r=new Array(n>1?n-1:0),i=1;i<n;i++)r[i-1]=a[i];return t.next=3,e.apply(void 0,r);case 3:return o=t.sent,we(o,Ne),t.abrupt("return",o);case 6:case"end":return t.stop()}}),t)}))),function(t){return e.apply(this,arguments)})},{key:"_handleUIConfigChanged",value:function(t,e){var n,r=null===(n=this._configElement)||void 0===n?void 0:n._cardModData;r&&(e.detail.config.card_mod=r.card);for(var i=arguments.length,o=new Array(i>2?i-2:0),a=2;a<i;a++)o[a-2]=arguments[a];t.apply(void 0,[e].concat(o))}}]),r}();Me=M([xe("hui-card-element-editor")],Me);var Re=function(t){g(n,Dt);var e=b(n);function n(){return P(this,n),e.apply(this,arguments)}return j(n,[{key:"updated",value:function(t){for(var e,n,r,i,o,a=arguments.length,s=new Array(a>1?a-1:0),u=1;u<a;u++)s[u-1]=arguments[u];null==t||t.apply(void 0,s),this._cardModIcon||(this._cardModIcon=document.createElement("ha-icon"),this._cardModIcon.icon="mdi:brush");var c=this.shadowRoot.querySelector("mwc-button[slot=secondaryAction]");c&&(c.appendChild(this._cardModIcon),(null===(e=this._cardConfig)||void 0===e?void 0:e.card_mod)||Array.isArray(null===(n=this._cardConfig)||void 0===n?void 0:n.entities)&&(null===(o=null===(i=null===(r=this._cardConfig)||void 0===r?void 0:r.entities)||void 0===i?void 0:i.some)||void 0===o?void 0:o.call(i,(function(t){return t.card_mod})))?this._cardModIcon.style.visibility="visible":this._cardModIcon.style.visibility="hidden")}}]),n}();Re=M([xe("hui-dialog-edit-card")],Re);var Le=function(t){g(n,he);var e=b(n);function n(){return P(this,n),e.apply(this,arguments)}return j(n,[{key:"setConfig",value:function(t){for(var e,n,r=arguments.length,i=new Array(r>1?r-1:0),o=1;o<r;o++)i[o-1]=arguments[o];null==t||t.apply(void 0,i);var a,s=A(this._elements.entries());try{for(s.s();!(a=s.n()).done;){var u=v(a.value,2),c=u[0],l=u[1];ae(l),we(l,he);var d=this._config.elements[c],h="type-".concat(null===(n=null===(e=null==d?void 0:d.type)||void 0===e?void 0:e.replace)||void 0===n?void 0:n.call(e,":","-"));pe(l,"element",null==d?void 0:d.card_mod,{config:d},!0,h)}}catch(t){s.e(t)}finally{s.f()}}}]),n}();Le=M([xe("hui-picture-elements-card")],Le);var Ue=function(t){var e=window.getComputedStyle(t),n=e.getPropertyValue("--card-mod-icon");n&&(t.icon=n.trim());var r=e.getPropertyValue("--card-mod-icon-color");r&&(t.style.color=r),"none"===e.getPropertyValue("--card-mod-icon-dim")&&(t.style.filter="none")},De=function(){var t=m(p().mark((function t(e){var n,r,i,o,a;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return Ue(e),e._boundCardMod=null!==(n=e._boundCardMod)&&void 0!==n?n:new Set,t.next=4,Be(e);case 4:r=t.sent,i=A(r),t.prev=6,a=p().mark((function t(){var n;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(n=o.value,!e._boundCardMod.has(n)){t.next=3;break}return t.abrupt("return",1);case 3:n.addEventListener("card-mod-update",m(p().mark((function t(){return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,n.updateComplete;case 2:Ue(e);case 3:case"end":return t.stop()}}),t)})))),e._boundCardMod.add(n);case 5:case"end":return t.stop()}}),t)})),i.s();case 9:if((o=i.n()).done){t.next=15;break}return t.delegateYield(a(),"t0",11);case 11:if(!t.t0){t.next=13;break}return t.abrupt("continue",13);case 13:t.next=9;break;case 15:t.next=20;break;case 17:t.prev=17,t.t1=t.catch(6),i.e(t.t1);case 20:return t.prev=20,i.f(),t.finish(20);case 23:if(!(e.cm_retries<5)){t.next=26;break}return e.cm_retries++,t.abrupt("return",window.setTimeout((function(){return De(e)}),250*e.cm_retries));case 26:case"end":return t.stop()}}),t,null,[[6,17,20,23]])})));return function(e){return t.apply(this,arguments)}}(),He=function(t){g(n,he);var e=b(n);function n(){var t;return P(this,n),(t=e.apply(this,arguments)).cm_retries=0,t}return j(n,[{key:"updated",value:function(t){for(var e=arguments.length,n=new Array(e>1?e-1:0),r=1;r<e;r++)n[r-1]=arguments[r];null==t||t.apply(void 0,n),this.cm_retries=0,De(this)}}]),n}();He=M([xe("ha-state-icon")],He);var Ie=function(t){g(n,he);var e=b(n);function n(){var t;return P(this,n),(t=e.apply(this,arguments)).cm_retries=0,t}return j(n,[{key:"updated",value:function(t){for(var e=arguments.length,n=new Array(e>1?e-1:0),r=1;r<e;r++)n[r-1]=arguments[r];null==t||t.apply(void 0,n),this.cm_retries=0,De(this)}}]),n}();Ie=M([xe("ha-icon")],Ie);var ze=function(t){g(n,he);var e=b(n);function n(){var t;return P(this,n),(t=e.apply(this,arguments)).cm_retries=0,t}return j(n,[{key:"updated",value:function(t){for(var e,n,r=arguments.length,i=new Array(r>1?r-1:0),o=1;o<r;o++)i[o-1]=arguments[o];null==t||t.apply(void 0,i),"ha-icon"!==(null===(n=null===(e=this.parentNode)||void 0===e?void 0:e.host)||void 0===n?void 0:n.localName)&&(this.cm_retries=0,De(this))}}]),n}();function qe(t,e){var n,r=A(e);try{for(r.s();!(n=r.n()).done;){var i=n.value;t.add(i)}}catch(t){r.e(t)}finally{r.f()}}function Be(t){return Ve.apply(this,arguments)}function Ve(){return Ve=m(p().mark((function t(e){var n,r,i,o,a,s=arguments;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(n=s.length>1&&void 0!==s[1]?s[1]:0,r=new Set,10!=n){t.next=4;break}return t.abrupt("return",r);case 4:if(e){t.next=6;break}return t.abrupt("return",r);case 6:if(!e.updateComplete){t.next=9;break}return t.next=9,e.updateComplete;case 9:if(e._cardMod){i=A(e._cardMod);try{for(i.s();!(o=i.n()).done;)(a=o.value).styles&&r.add(a)}catch(t){i.e(t)}finally{i.f()}}if(!e.parentElement){t.next=19;break}return t.t0=qe,t.t1=r,t.next=15,Be(e.parentElement,n+1);case 15:t.t2=t.sent,(0,t.t0)(t.t1,t.t2),t.next=26;break;case 19:if(!e.parentNode){t.next=26;break}return t.t3=qe,t.t4=r,t.next=24,Be(e.parentNode,n+1);case 24:t.t5=t.sent,(0,t.t3)(t.t4,t.t5);case 26:if(!e.host){t.next=33;break}return t.t6=qe,t.t7=r,t.next=31,Be(e.host,n+1);case 31:t.t8=t.sent,(0,t.t6)(t.t7,t.t8);case 33:return t.abrupt("return",r);case 34:case"end":return t.stop()}}),t)}))),Ve.apply(this,arguments)}ze=M([xe("ha-svg-icon")],ze);var Je="\nha-card {\n  background: none;\n  box-shadow: none;\n  border: none;\n  transition: none;\n}",We=function(t){g(r,Dt);var e,n=b(r);function r(){return P(this,r),n.apply(this,arguments)}return j(r,[{key:"setConfig",value:function(t){var e;this._config=JSON.parse(JSON.stringify(t));var n=(null===(e=this._config.card_mod)||void 0===e?void 0:e.style)||this._config.style;void 0===n?n=Je:"string"==typeof n?n=Je+n:n["."]?n["."]=Je+n["."]:n["."]=Je,this._config.card_mod={style:n},this.build_card(t.card)}},{key:"build_card",value:(e=m(p().mark((function t(e){var n,r=this;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(void 0!==this._hass){t.next=3;break}return t.next=3,new Promise((function(t){return r._hassResolve=t}));case 3:return this._hassResolve=void 0,t.next=6,window.loadCardHelpers();case 6:return n=t.sent,t.next=9,n.createCardElement(e);case 9:this.card=t.sent,this.card.hass=this._hass;case 11:case"end":return t.stop()}}),t,this)}))),function(t){return e.apply(this,arguments)})},{key:"firstUpdated",value:function(){var t=this;window.setTimeout((function(){var e,n;if(null===(n=null===(e=t.card)||void 0===e?void 0:e.shadowRoot)||void 0===n?void 0:n.querySelector("ha-card")){console.info("%cYou are doing it wrong!","color: red; font-weight: bold");var r=t.card.localName.replace(/hui-(.*)-card/,"$1");console.info("mod-card should NEVER be used with a card that already has a ha-card element, such as ".concat(r))}}),3e3)}},{key:"hass",set:function(t){this._hass=t,this.card&&(this.card.hass=t),this._hassResolve&&this._hassResolve()}},{key:"render",value:function(){return wt(s||(s=u([" <ha-card modcard> "," </ha-card> "])),this.card)}},{key:"getCardSize",value:function(){if(this._config.report_size)return this._config.report_size;var t=this.shadowRoot;return t&&(t=t.querySelector("ha-card card-maker")),t&&(t=t.getCardSize),t&&(t=t()),t||1}}]),r}();function Ge(){document.dispatchEvent(new Event("cm_update"))}M([qt()],We.prototype,"card",void 0),customElements.get("mod-card")||customElements.define("mod-card",We),m(p().mark((function t(){return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(void 0!==customElements.get("home-assistant")){t.next=5;break}return t.next=3,new Promise((function(t){return window.setTimeout(t,100)}));case 3:t.next=0;break;case 5:customElements.get("mod-card")||customElements.define("mod-card",We);case 6:case"end":return t.stop()}}),t)})))();var Fe,Ye,Ke,Ze=[customElements.whenDefined("home-assistant"),customElements.whenDefined("hc-main")];Promise.race(Ze).then((function(){window.setTimeout(m(p().mark((function t(){var e,n,r;return p().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,Jt();case 2:r=t.sent;case 3:if(r){t.next=8;break}return t.next=6,new Promise((function(t){return window.setTimeout(t,500)}));case 6:t.next=3;break;case 8:r.connection.subscribeEvents((function(){window.setTimeout(Ge,500)}),"themes_updated"),null===(e=document.querySelector("home-assistant"))||void 0===e||e.addEventListener("settheme",Ge),null===(n=document.querySelector("hc-main"))||void 0===n||n.addEventListener("settheme",Ge);case 11:case"end":return t.stop()}}),t)}))),1e3)}));var Qe,Xe=[],tn=A(document.querySelectorAll("script"));try{for(tn.s();!(Qe=tn.n()).done;){var en=Qe.value;if(null===(Ye=null===(Fe=null==en?void 0:en.innerText)||void 0===Fe?void 0:Fe.trim())||void 0===Ye?void 0:Ye.startsWith("import(")){var nn,rn=null===(Ke=en.innerText.split("\n"))||void 0===Ke?void 0:Ke.map((function(t){return t.trim()})),on=A(rn);try{for(on.s();!(nn=on.n()).done;){var an=nn.value;Xe.push(an.replace(/^import\(\"/,"").replace(/\"\);/,""))}}catch(t){on.e(t)}finally{on.f()}}}}catch(t){tn.e(t)}finally{tn.f()}Xe.some((function(t){return t.includes("/card-mod.js")}))||console.info("You may not be getting optimal performance out of card-mod.\nSee https://github.com/thomasloven/lovelace-card-mod#performance-improvements");
=======
/******************************************************************************
Copyright (c) Microsoft Corporation.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
***************************************************************************** */

function __decorate(decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
}

/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$1=window,e$3=t$1.ShadowRoot&&(void 0===t$1.ShadyCSS||t$1.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s$3=Symbol(),n$4=new WeakMap;let o$3 = class o{constructor(t,e,n){if(this._$cssResult$=!0,n!==s$3)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e;}get styleSheet(){let t=this.o;const s=this.t;if(e$3&&void 0===t){const e=void 0!==s&&1===s.length;e&&(t=n$4.get(s)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),e&&n$4.set(s,t));}return t}toString(){return this.cssText}};const r$2=t=>new o$3("string"==typeof t?t:t+"",void 0,s$3),S$1=(s,n)=>{e$3?s.adoptedStyleSheets=n.map((t=>t instanceof CSSStyleSheet?t:t.styleSheet)):n.forEach((e=>{const n=document.createElement("style"),o=t$1.litNonce;void 0!==o&&n.setAttribute("nonce",o),n.textContent=e.cssText,s.appendChild(n);}));},c$1=e$3?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return r$2(e)})(t):t;

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */var s$2;const e$2=window,r$1=e$2.trustedTypes,h$1=r$1?r$1.emptyScript:"",o$2=e$2.reactiveElementPolyfillSupport,n$3={toAttribute(t,i){switch(i){case Boolean:t=t?h$1:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t);}return t},fromAttribute(t,i){let s=t;switch(i){case Boolean:s=null!==t;break;case Number:s=null===t?null:Number(t);break;case Object:case Array:try{s=JSON.parse(t);}catch(t){s=null;}}return s}},a$1=(t,i)=>i!==t&&(i==i||t==t),l$2={attribute:!0,type:String,converter:n$3,reflect:!1,hasChanged:a$1};let d$1 = class d extends HTMLElement{constructor(){super(),this._$Ei=new Map,this.isUpdatePending=!1,this.hasUpdated=!1,this._$El=null,this.u();}static addInitializer(t){var i;this.finalize(),(null!==(i=this.h)&&void 0!==i?i:this.h=[]).push(t);}static get observedAttributes(){this.finalize();const t=[];return this.elementProperties.forEach(((i,s)=>{const e=this._$Ep(s,i);void 0!==e&&(this._$Ev.set(e,s),t.push(e));})),t}static createProperty(t,i=l$2){if(i.state&&(i.attribute=!1),this.finalize(),this.elementProperties.set(t,i),!i.noAccessor&&!this.prototype.hasOwnProperty(t)){const s="symbol"==typeof t?Symbol():"__"+t,e=this.getPropertyDescriptor(t,s,i);void 0!==e&&Object.defineProperty(this.prototype,t,e);}}static getPropertyDescriptor(t,i,s){return {get(){return this[i]},set(e){const r=this[t];this[i]=e,this.requestUpdate(t,r,s);},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)||l$2}static finalize(){if(this.hasOwnProperty("finalized"))return !1;this.finalized=!0;const t=Object.getPrototypeOf(this);if(t.finalize(),void 0!==t.h&&(this.h=[...t.h]),this.elementProperties=new Map(t.elementProperties),this._$Ev=new Map,this.hasOwnProperty("properties")){const t=this.properties,i=[...Object.getOwnPropertyNames(t),...Object.getOwnPropertySymbols(t)];for(const s of i)this.createProperty(s,t[s]);}return this.elementStyles=this.finalizeStyles(this.styles),!0}static finalizeStyles(i){const s=[];if(Array.isArray(i)){const e=new Set(i.flat(1/0).reverse());for(const i of e)s.unshift(c$1(i));}else void 0!==i&&s.push(c$1(i));return s}static _$Ep(t,i){const s=i.attribute;return !1===s?void 0:"string"==typeof s?s:"string"==typeof t?t.toLowerCase():void 0}u(){var t;this._$E_=new Promise((t=>this.enableUpdating=t)),this._$AL=new Map,this._$Eg(),this.requestUpdate(),null===(t=this.constructor.h)||void 0===t||t.forEach((t=>t(this)));}addController(t){var i,s;(null!==(i=this._$ES)&&void 0!==i?i:this._$ES=[]).push(t),void 0!==this.renderRoot&&this.isConnected&&(null===(s=t.hostConnected)||void 0===s||s.call(t));}removeController(t){var i;null===(i=this._$ES)||void 0===i||i.splice(this._$ES.indexOf(t)>>>0,1);}_$Eg(){this.constructor.elementProperties.forEach(((t,i)=>{this.hasOwnProperty(i)&&(this._$Ei.set(i,this[i]),delete this[i]);}));}createRenderRoot(){var t;const s=null!==(t=this.shadowRoot)&&void 0!==t?t:this.attachShadow(this.constructor.shadowRootOptions);return S$1(s,this.constructor.elementStyles),s}connectedCallback(){var t;void 0===this.renderRoot&&(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),null===(t=this._$ES)||void 0===t||t.forEach((t=>{var i;return null===(i=t.hostConnected)||void 0===i?void 0:i.call(t)}));}enableUpdating(t){}disconnectedCallback(){var t;null===(t=this._$ES)||void 0===t||t.forEach((t=>{var i;return null===(i=t.hostDisconnected)||void 0===i?void 0:i.call(t)}));}attributeChangedCallback(t,i,s){this._$AK(t,s);}_$EO(t,i,s=l$2){var e;const r=this.constructor._$Ep(t,s);if(void 0!==r&&!0===s.reflect){const h=(void 0!==(null===(e=s.converter)||void 0===e?void 0:e.toAttribute)?s.converter:n$3).toAttribute(i,s.type);this._$El=t,null==h?this.removeAttribute(r):this.setAttribute(r,h),this._$El=null;}}_$AK(t,i){var s;const e=this.constructor,r=e._$Ev.get(t);if(void 0!==r&&this._$El!==r){const t=e.getPropertyOptions(r),h="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==(null===(s=t.converter)||void 0===s?void 0:s.fromAttribute)?t.converter:n$3;this._$El=r,this[r]=h.fromAttribute(i,t.type),this._$El=null;}}requestUpdate(t,i,s){let e=!0;void 0!==t&&(((s=s||this.constructor.getPropertyOptions(t)).hasChanged||a$1)(this[t],i)?(this._$AL.has(t)||this._$AL.set(t,i),!0===s.reflect&&this._$El!==t&&(void 0===this._$EC&&(this._$EC=new Map),this._$EC.set(t,s))):e=!1),!this.isUpdatePending&&e&&(this._$E_=this._$Ej());}async _$Ej(){this.isUpdatePending=!0;try{await this._$E_;}catch(t){Promise.reject(t);}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){var t;if(!this.isUpdatePending)return;this.hasUpdated,this._$Ei&&(this._$Ei.forEach(((t,i)=>this[i]=t)),this._$Ei=void 0);let i=!1;const s=this._$AL;try{i=this.shouldUpdate(s),i?(this.willUpdate(s),null===(t=this._$ES)||void 0===t||t.forEach((t=>{var i;return null===(i=t.hostUpdate)||void 0===i?void 0:i.call(t)})),this.update(s)):this._$Ek();}catch(t){throw i=!1,this._$Ek(),t}i&&this._$AE(s);}willUpdate(t){}_$AE(t){var i;null===(i=this._$ES)||void 0===i||i.forEach((t=>{var i;return null===(i=t.hostUpdated)||void 0===i?void 0:i.call(t)})),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t);}_$Ek(){this._$AL=new Map,this.isUpdatePending=!1;}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$E_}shouldUpdate(t){return !0}update(t){void 0!==this._$EC&&(this._$EC.forEach(((t,i)=>this._$EO(i,this[i],t))),this._$EC=void 0),this._$Ek();}updated(t){}firstUpdated(t){}};d$1.finalized=!0,d$1.elementProperties=new Map,d$1.elementStyles=[],d$1.shadowRootOptions={mode:"open"},null==o$2||o$2({ReactiveElement:d$1}),(null!==(s$2=e$2.reactiveElementVersions)&&void 0!==s$2?s$2:e$2.reactiveElementVersions=[]).push("1.4.2");

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
var t;const i$1=window,s$1=i$1.trustedTypes,e$1=s$1?s$1.createPolicy("lit-html",{createHTML:t=>t}):void 0,o$1=`lit$${(Math.random()+"").slice(9)}$`,n$2="?"+o$1,l$1=`<${n$2}>`,h=document,r=(t="")=>h.createComment(t),d=t=>null===t||"object"!=typeof t&&"function"!=typeof t,u=Array.isArray,c=t=>u(t)||"function"==typeof(null==t?void 0:t[Symbol.iterator]),v=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,a=/-->/g,f=/>/g,_=RegExp(">|[ \t\n\f\r](?:([^\\s\"'>=/]+)([ \t\n\f\r]*=[ \t\n\f\r]*(?:[^ \t\n\f\r\"'`<>=]|(\"|')|))|$)","g"),m=/'/g,p=/"/g,$=/^(?:script|style|textarea|title)$/i,g=t=>(i,...s)=>({_$litType$:t,strings:i,values:s}),y=g(1),x=Symbol.for("lit-noChange"),b=Symbol.for("lit-nothing"),T=new WeakMap,A=h.createTreeWalker(h,129,null,!1),E=(t,i)=>{const s=t.length-1,n=[];let h,r=2===i?"<svg>":"",d=v;for(let i=0;i<s;i++){const s=t[i];let e,u,c=-1,g=0;for(;g<s.length&&(d.lastIndex=g,u=d.exec(s),null!==u);)g=d.lastIndex,d===v?"!--"===u[1]?d=a:void 0!==u[1]?d=f:void 0!==u[2]?($.test(u[2])&&(h=RegExp("</"+u[2],"g")),d=_):void 0!==u[3]&&(d=_):d===_?">"===u[0]?(d=null!=h?h:v,c=-1):void 0===u[1]?c=-2:(c=d.lastIndex-u[2].length,e=u[1],d=void 0===u[3]?_:'"'===u[3]?p:m):d===p||d===m?d=_:d===a||d===f?d=v:(d=_,h=void 0);const y=d===_&&t[i+1].startsWith("/>")?" ":"";r+=d===v?s+l$1:c>=0?(n.push(e),s.slice(0,c)+"$lit$"+s.slice(c)+o$1+y):s+o$1+(-2===c?(n.push(void 0),i):y);}const u=r+(t[s]||"<?>")+(2===i?"</svg>":"");if(!Array.isArray(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return [void 0!==e$1?e$1.createHTML(u):u,n]};class C{constructor({strings:t,_$litType$:i},e){let l;this.parts=[];let h=0,d=0;const u=t.length-1,c=this.parts,[v,a]=E(t,i);if(this.el=C.createElement(v,e),A.currentNode=this.el.content,2===i){const t=this.el.content,i=t.firstChild;i.remove(),t.append(...i.childNodes);}for(;null!==(l=A.nextNode())&&c.length<u;){if(1===l.nodeType){if(l.hasAttributes()){const t=[];for(const i of l.getAttributeNames())if(i.endsWith("$lit$")||i.startsWith(o$1)){const s=a[d++];if(t.push(i),void 0!==s){const t=l.getAttribute(s.toLowerCase()+"$lit$").split(o$1),i=/([.?@])?(.*)/.exec(s);c.push({type:1,index:h,name:i[2],strings:t,ctor:"."===i[1]?M:"?"===i[1]?k:"@"===i[1]?H:S});}else c.push({type:6,index:h});}for(const i of t)l.removeAttribute(i);}if($.test(l.tagName)){const t=l.textContent.split(o$1),i=t.length-1;if(i>0){l.textContent=s$1?s$1.emptyScript:"";for(let s=0;s<i;s++)l.append(t[s],r()),A.nextNode(),c.push({type:2,index:++h});l.append(t[i],r());}}}else if(8===l.nodeType)if(l.data===n$2)c.push({type:2,index:h});else {let t=-1;for(;-1!==(t=l.data.indexOf(o$1,t+1));)c.push({type:7,index:h}),t+=o$1.length-1;}h++;}}static createElement(t,i){const s=h.createElement("template");return s.innerHTML=t,s}}function P(t,i,s=t,e){var o,n,l,h;if(i===x)return i;let r=void 0!==e?null===(o=s._$Co)||void 0===o?void 0:o[e]:s._$Cl;const u=d(i)?void 0:i._$litDirective$;return (null==r?void 0:r.constructor)!==u&&(null===(n=null==r?void 0:r._$AO)||void 0===n||n.call(r,!1),void 0===u?r=void 0:(r=new u(t),r._$AT(t,s,e)),void 0!==e?(null!==(l=(h=s)._$Co)&&void 0!==l?l:h._$Co=[])[e]=r:s._$Cl=r),void 0!==r&&(i=P(t,r._$AS(t,i.values),r,e)),i}class V{constructor(t,i){this.u=[],this._$AN=void 0,this._$AD=t,this._$AM=i;}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}v(t){var i;const{el:{content:s},parts:e}=this._$AD,o=(null!==(i=null==t?void 0:t.creationScope)&&void 0!==i?i:h).importNode(s,!0);A.currentNode=o;let n=A.nextNode(),l=0,r=0,d=e[0];for(;void 0!==d;){if(l===d.index){let i;2===d.type?i=new N(n,n.nextSibling,this,t):1===d.type?i=new d.ctor(n,d.name,d.strings,this,t):6===d.type&&(i=new I(n,this,t)),this.u.push(i),d=e[++r];}l!==(null==d?void 0:d.index)&&(n=A.nextNode(),l++);}return o}p(t){let i=0;for(const s of this.u)void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,i),i+=s.strings.length-2):s._$AI(t[i])),i++;}}class N{constructor(t,i,s,e){var o;this.type=2,this._$AH=b,this._$AN=void 0,this._$AA=t,this._$AB=i,this._$AM=s,this.options=e,this._$Cm=null===(o=null==e?void 0:e.isConnected)||void 0===o||o;}get _$AU(){var t,i;return null!==(i=null===(t=this._$AM)||void 0===t?void 0:t._$AU)&&void 0!==i?i:this._$Cm}get parentNode(){let t=this._$AA.parentNode;const i=this._$AM;return void 0!==i&&11===t.nodeType&&(t=i.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,i=this){t=P(this,t,i),d(t)?t===b||null==t||""===t?(this._$AH!==b&&this._$AR(),this._$AH=b):t!==this._$AH&&t!==x&&this.g(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):c(t)?this.k(t):this.g(t);}O(t,i=this._$AB){return this._$AA.parentNode.insertBefore(t,i)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t));}g(t){this._$AH!==b&&d(this._$AH)?this._$AA.nextSibling.data=t:this.T(h.createTextNode(t)),this._$AH=t;}$(t){var i;const{values:s,_$litType$:e}=t,o="number"==typeof e?this._$AC(t):(void 0===e.el&&(e.el=C.createElement(e.h,this.options)),e);if((null===(i=this._$AH)||void 0===i?void 0:i._$AD)===o)this._$AH.p(s);else {const t=new V(o,this),i=t.v(this.options);t.p(s),this.T(i),this._$AH=t;}}_$AC(t){let i=T.get(t.strings);return void 0===i&&T.set(t.strings,i=new C(t)),i}k(t){u(this._$AH)||(this._$AH=[],this._$AR());const i=this._$AH;let s,e=0;for(const o of t)e===i.length?i.push(s=new N(this.O(r()),this.O(r()),this,this.options)):s=i[e],s._$AI(o),e++;e<i.length&&(this._$AR(s&&s._$AB.nextSibling,e),i.length=e);}_$AR(t=this._$AA.nextSibling,i){var s;for(null===(s=this._$AP)||void 0===s||s.call(this,!1,!0,i);t&&t!==this._$AB;){const i=t.nextSibling;t.remove(),t=i;}}setConnected(t){var i;void 0===this._$AM&&(this._$Cm=t,null===(i=this._$AP)||void 0===i||i.call(this,t));}}class S{constructor(t,i,s,e,o){this.type=1,this._$AH=b,this._$AN=void 0,this.element=t,this.name=i,this._$AM=e,this.options=o,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=b;}get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}_$AI(t,i=this,s,e){const o=this.strings;let n=!1;if(void 0===o)t=P(this,t,i,0),n=!d(t)||t!==this._$AH&&t!==x,n&&(this._$AH=t);else {const e=t;let l,h;for(t=o[0],l=0;l<o.length-1;l++)h=P(this,e[s+l],i,l),h===x&&(h=this._$AH[l]),n||(n=!d(h)||h!==this._$AH[l]),h===b?t=b:t!==b&&(t+=(null!=h?h:"")+o[l+1]),this._$AH[l]=h;}n&&!e&&this.j(t);}j(t){t===b?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,null!=t?t:"");}}class M extends S{constructor(){super(...arguments),this.type=3;}j(t){this.element[this.name]=t===b?void 0:t;}}const R=s$1?s$1.emptyScript:"";class k extends S{constructor(){super(...arguments),this.type=4;}j(t){t&&t!==b?this.element.setAttribute(this.name,R):this.element.removeAttribute(this.name);}}class H extends S{constructor(t,i,s,e,o){super(t,i,s,e,o),this.type=5;}_$AI(t,i=this){var s;if((t=null!==(s=P(this,t,i,0))&&void 0!==s?s:b)===x)return;const e=this._$AH,o=t===b&&e!==b||t.capture!==e.capture||t.once!==e.once||t.passive!==e.passive,n=t!==b&&(e===b||o);o&&this.element.removeEventListener(this.name,this,e),n&&this.element.addEventListener(this.name,this,t),this._$AH=t;}handleEvent(t){var i,s;"function"==typeof this._$AH?this._$AH.call(null!==(s=null===(i=this.options)||void 0===i?void 0:i.host)&&void 0!==s?s:this.element,t):this._$AH.handleEvent(t);}}class I{constructor(t,i,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=i,this.options=s;}get _$AU(){return this._$AM._$AU}_$AI(t){P(this,t);}}const z=i$1.litHtmlPolyfillSupport;null==z||z(C,N),(null!==(t=i$1.litHtmlVersions)&&void 0!==t?t:i$1.litHtmlVersions=[]).push("2.4.0");const Z=(t,i,s)=>{var e,o;const n=null!==(e=null==s?void 0:s.renderBefore)&&void 0!==e?e:i;let l=n._$litPart$;if(void 0===l){const t=null!==(o=null==s?void 0:s.renderBefore)&&void 0!==o?o:null;n._$litPart$=l=new N(i.insertBefore(r(),t),t,void 0,null!=s?s:{});}return l._$AI(t),l};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */var l,o;class s extends d$1{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0;}createRenderRoot(){var t,e;const i=super.createRenderRoot();return null!==(t=(e=this.renderOptions).renderBefore)&&void 0!==t||(e.renderBefore=i.firstChild),i}update(t){const i=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=Z(i,this.renderRoot,this.renderOptions);}connectedCallback(){var t;super.connectedCallback(),null===(t=this._$Do)||void 0===t||t.setConnected(!0);}disconnectedCallback(){var t;super.disconnectedCallback(),null===(t=this._$Do)||void 0===t||t.setConnected(!1);}render(){return x}}s.finalized=!0,s._$litElement$=!0,null===(l=globalThis.litElementHydrateSupport)||void 0===l||l.call(globalThis,{LitElement:s});const n$1=globalThis.litElementPolyfillSupport;null==n$1||n$1({LitElement:s});(null!==(o=globalThis.litElementVersions)&&void 0!==o?o:globalThis.litElementVersions=[]).push("3.2.2");

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const i=(i,e)=>"method"===e.kind&&e.descriptor&&!("value"in e.descriptor)?{...e,finisher(n){n.createProperty(e.key,i);}}:{kind:"field",key:Symbol(),placement:"own",descriptor:{},originalKey:e.key,initializer(){"function"==typeof e.initializer&&(this[e.key]=e.initializer.call(this));},finisher(n){n.createProperty(e.key,i);}};function e(e){return (n,t)=>void 0!==t?((i,e,n)=>{e.constructor.createProperty(n,i);})(e,n,t):i(e,n)}

/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */var n;null!=(null===(n=window.HTMLSlotElement)||void 0===n?void 0:n.prototype.assignedElements)?(o,n)=>o.assignedElements(n):(o,n)=>o.assignedNodes(n).filter((o=>o.nodeType===Node.ELEMENT_NODE));

async function hass_base_el() {
    await Promise.race([
        customElements.whenDefined("home-assistant"),
        customElements.whenDefined("hc-main"),
    ]);
    const element = customElements.get("home-assistant")
        ? "home-assistant"
        : "hc-main";
    while (!document.querySelector(element))
        await new Promise((r) => window.setTimeout(r, 100));
    return document.querySelector(element);
}
async function hass() {
    const base = await hass_base_el();
    while (!base.hass)
        await new Promise((r) => window.setTimeout(r, 100));
    return base.hass;
}

const ID_STORAGE_KEY = "browser_mod-browser-id";
function BrowserID() {
    if (document.querySelector("hc-main"))
        return "CAST";
    if (localStorage[ID_STORAGE_KEY])
        return localStorage[ID_STORAGE_KEY];
    return "";
}

window.cardMod_template_cache =
    window.cardMod_template_cache || {};
const cachedTemplates = window
    .cardMod_template_cache;
function template_updated(key, result) {
    const cache = cachedTemplates[key];
    if (!cache) {
        return;
    }
    cache.value = result.result;
    cache.callbacks.forEach((f) => f(result.result));
}
function hasTemplate(str) {
    return String(str).includes("{%") || String(str).includes("{{");
}
async function bind_template(callback, template, variables) {
    const hs = await hass();
    const connection = hs.connection;
    const cacheKey = JSON.stringify([template, variables]);
    let cache = cachedTemplates[cacheKey];
    if (!cache) {
        unbind_template(callback);
        callback("");
        variables = Object.assign({ user: hs.user.name, browser: BrowserID(), hash: location.hash.substr(1) || "" }, variables);
        cachedTemplates[cacheKey] = cache = {
            template,
            variables,
            value: "",
            callbacks: new Set([callback]),
            unsubscribe: connection.subscribeMessage((result) => template_updated(cacheKey, result), {
                type: "render_template",
                template,
                variables,
            }),
        };
    }
    else {
        if (!cache.callbacks.has(callback))
            unbind_template(callback);
        callback(cache.value);
        cache.callbacks.add(callback);
    }
}
async function unbind_template(callback) {
    let unsubscriber;
    for (const [key, cache] of Object.entries(cachedTemplates)) {
        if (cache.callbacks.has(callback)) {
            cache.callbacks.delete(callback);
            if (cache.callbacks.size == 0) {
                unsubscriber = cache.unsubscribe;
                delete cachedTemplates[key];
            }
            break;
        }
    }
    if (unsubscriber)
        await (await unsubscriber)();
}

var name = "card-mod";
var version = "3.2.3";
var description = "";
var scripts = {
	build: "rollup -c",
	watch: "rollup -c --watch"
};
var keywords = [
];
var author = "Thomas Lovén";
var license = "MIT";
var devDependencies = {
	"rollup-plugin-terser": "^7.0.2"
};
var dependencies = {
	"@babel/core": "^7.20.2",
	"@rollup/plugin-babel": "^6.0.2",
	"@rollup/plugin-json": "^5.0.1",
	"@rollup/plugin-node-resolve": "^15.0.1",
	lit: "^2.4.1",
	rollup: "^3.4.0",
	"rollup-plugin-typescript2": "^0.34.1",
	typescript: "^4.9.3"
};
var pjson = {
	name: name,
	"private": true,
	version: version,
	description: description,
	scripts: scripts,
	keywords: keywords,
	author: author,
	license: license,
	devDependencies: devDependencies,
	dependencies: dependencies
};

const _load_yaml2json = async () => {
    if (customElements.get("developer-tools-event"))
        return;
    await customElements.whenDefined("partial-panel-resolver");
    const ppr = document.createElement("partial-panel-resolver");
    ppr.hass = {
        panels: [
            {
                url_path: "tmp",
                component_name: "developer-tools",
            },
        ],
    };
    ppr._updateRoutes();
    await ppr.routerOptions.routes.tmp.load();
    await customElements.whenDefined("developer-tools-router");
    const dtr = document.createElement("developer-tools-router");
    await dtr.routerOptions.routes.event.load();
};
const yaml2json = async (yaml) => {
    await _load_yaml2json();
    const el = document.createElement("ha-yaml-editor");
    el._onChange(new CustomEvent("yaml", { detail: { value: yaml } }));
    return el.value;
};

async function applyToElement(el, type, styles = "", variables = {}, entity_ids = null, // deprecated
shadow = true) {
    var _a;
    if (!el)
        return;
    if ((_a = el.localName) === null || _a === void 0 ? void 0 : _a.includes("-"))
        await customElements.whenDefined(el.localName);
    if (el.updateComplete)
        await el.updateComplete;
    if (el._cardMod === undefined) {
        el._cardMod = [];
    }
    let cardMod;
    for (const cm of el._cardMod) {
        if (cm.type === type) {
            cardMod = cm;
            break;
        }
    }
    if (!cardMod) {
        cardMod = document.createElement("card-mod");
        cardMod.type = type;
        el._cardMod.push(cardMod);
    }
    queueMicrotask(async () => {
        const target = el.modElement
            ? el.modElement
            : shadow
                ? el.shadowRoot || el
                : el;
        if (!target.contains(cardMod))
            target.appendChild(cardMod);
        cardMod.variables = variables;
        cardMod.styles = styles;
    });
    return cardMod;
}
async function get_theme(root) {
    var _a;
    if (!root.type)
        return null;
    const el = root.parentElement ? root.parentElement : root;
    const theme = window
        .getComputedStyle(el)
        .getPropertyValue("--card-mod-theme");
    const hs = await hass();
    if (!hs)
        return {};
    const themes = (_a = hs === null || hs === void 0 ? void 0 : hs.themes.themes) !== null && _a !== void 0 ? _a : {};
    if (!themes[theme])
        return {};
    if (themes[theme][`card-mod-${root.type}-yaml`]) {
        return yaml2json(themes[theme][`card-mod-${root.type}-yaml`]);
    }
    else if (themes[theme][`card-mod-${root.type}`]) {
        return { ".": themes[theme][`card-mod-${root.type}`] };
    }
    else {
        return {};
    }
}
function merge_deep(target, source) {
    const isObject = (i) => {
        return i && typeof i === "object" && !Array.isArray(i);
    };
    if (isObject(target) && isObject(source)) {
        for (const key in source) {
            if (isObject(source[key])) {
                if (!target[key])
                    Object.assign(target, { [key]: {} });
                if (typeof target[key] === "string")
                    target[key] = { ".": target[key] };
                merge_deep(target[key], source[key]);
            }
            else {
                if (target[key])
                    target[key] = source[key] + target[key];
                else
                    target[key] = source[key];
            }
        }
    }
    return target;
}
function compare_deep(a, b) {
    if (a === b)
        return true;
    if (typeof a !== typeof b)
        return false;
    if (!(a instanceof Object && b instanceof Object))
        return false;
    for (const x in a) {
        if (!a.hasOwnProperty(x))
            continue;
        if (!b.hasOwnProperty(x))
            return false;
        if (a[x] === b[x])
            continue;
        if (typeof a[x] !== "object")
            return false;
        if (!compare_deep(a[x], b[x]))
            return false;
    }
    for (const x in b) {
        if (!b.hasOwnProperty(x))
            continue;
        if (!a.hasOwnProperty(x))
            return false;
    }
    return true;
}
function findConfig(node) {
    if (node.config)
        return node.config;
    if (node._config)
        return node._config;
    if (node.host)
        return findConfig(node.host);
    if (node.parentElement)
        return findConfig(node.parentElement);
    if (node.parentNode)
        return findConfig(node.parentNode);
    return null;
}
function joinSet(dst, src) {
    for (const s of src)
        dst.add(s);
}
async function findParentCardMod(node, step = 0) {
    let cardMods = new Set();
    if (step == 10)
        return cardMods;
    if (!node)
        return cardMods;
    if (node._cardMod) {
        for (const cm of node._cardMod) {
            if (cm.styles)
                cardMods.add(cm);
        }
    }
    if (node.updateComplete)
        await node.updateComplete;
    if (node.parentElement)
        joinSet(cardMods, await findParentCardMod(node.parentElement, step + 1));
    else if (node.parentNode)
        joinSet(cardMods, await findParentCardMod(node.parentNode, step + 1));
    if (node.host)
        joinSet(cardMods, await findParentCardMod(node.host, step + 1));
    return cardMods;
}
function parentElement(el) {
    if (!el)
        return undefined;
    const node = el.parentElement || el.parentNode;
    if (!node)
        return undefined;
    return node.host ? node.host : node;
}
function getResources() {
    var _a, _b, _c;
    const scriptElements = document.querySelectorAll("script");
    const retval = [];
    for (const script of scriptElements) {
        if ((_b = (_a = script === null || script === void 0 ? void 0 : script.innerText) === null || _a === void 0 ? void 0 : _a.trim()) === null || _b === void 0 ? void 0 : _b.startsWith("import(")) {
            const imports = (_c = script.innerText.split("\n")) === null || _c === void 0 ? void 0 : _c.map((e) => e.trim());
            for (const imp of imports) {
                retval.push(imp.replace(/^import\(\"/, "").replace(/\"\);/, ""));
            }
        }
    }
    return retval;
}

const TIMEOUT_ERROR = "SELECTTREE-TIMEOUT";
async function await_element(el, hard = false) {
    var _a;
    if ((_a = el.localName) === null || _a === void 0 ? void 0 : _a.includes("-"))
        await customElements.whenDefined(el.localName);
    if (el.updateComplete)
        await el.updateComplete;
    if (hard) {
        if (el.pageRendered)
            await el.pageRendered;
        if (el._panelState) {
            let rounds = 0;
            while (el._panelState !== "loaded" && rounds++ < 5)
                await new Promise((r) => setTimeout(r, 100));
        }
    }
}
async function _selectTree(root, path, all = false) {
    let el = [root];
    if (typeof path === "string") {
        path = path.split(/(\$| )/);
    }
    while (path[path.length - 1] === "")
        path.pop();
    for (const [i, p] of path.entries()) {
        const e = el[0];
        if (!e)
            return null;
        if (!p.trim().length)
            continue;
        await_element(e);
        el = p === "$" ? [e.shadowRoot] : e.querySelectorAll(p);
    }
    return all ? el : el[0];
}
async function selectTree(root, path, all = false, timeout = 10000) {
    return Promise.race([
        _selectTree(root, path, all),
        new Promise((_, reject) => setTimeout(() => reject(new Error(TIMEOUT_ERROR)), timeout)),
    ]).catch((err) => {
        if (!err.message || err.message !== TIMEOUT_ERROR)
            throw err;
        return null;
    });
}

class CardMod extends s {
    static get applyToElement() {
        return applyToElement;
    }
    constructor() {
        super();
        this._rendered_styles = "";
        this._styleChildren = new Set();
        this._observer = new MutationObserver((mutations) => {
            for (const m of mutations) {
                if (m.target.localName === "card-mod")
                    return;
                if (m.addedNodes.length)
                    m.addedNodes.forEach((n) => {
                        if (n.localName !== "card-mod")
                            ;
                    });
                if (m.removedNodes.length)
                    m.removedNodes.forEach((n) => {
                        if (n.localName !== "card-mod")
                            ;
                    });
            }
            if (stop)
                return;
            this.refresh();
        });
        document.addEventListener("cm_update", () => {
            this.refresh();
        });
    }
    connectedCallback() {
        super.connectedCallback();
        this._connect();
        this.setAttribute("slot", "none");
    }
    disconnectedCallback() {
        super.disconnectedCallback();
        this._disconnect();
    }
    set styles(stl) {
        if (compare_deep(stl, this._input_styles))
            return;
        this._input_styles = stl;
        (async () => {
            // Always work with yaml styles internally
            let styles = JSON.parse(JSON.stringify(stl || {}));
            if (typeof styles === "string")
                styles = { ".": styles };
            // Merge card_mod styles with theme styles
            const theme_styles = await get_theme(this);
            merge_deep(styles, theme_styles);
            this._fixed_styles = styles;
            this._connect();
        })();
    }
    get styles() {
        return this._styles;
    }
    refresh() {
        this._connect();
    }
    async _styleChildEl(element, value = undefined) {
        if (value === undefined) {
            // Find the style for the element
            const styles = this._fixed_styles;
            for (const [key, val] of Object.entries(styles)) {
                if (key === ".")
                    continue;
                const elements = await selectTree(this.parentElement || this.parentNode, key, true);
                elements.forEach((el) => {
                    if (el === element) {
                        value = val;
                    }
                });
                if (value !== undefined)
                    break;
            }
            if (value === undefined)
                return;
        }
        if (!element)
            return;
        const child = await applyToElement(element, `${this.type}-child`, value, this.variables, null, false);
        child.refresh;
        return child;
    }
    async _connect() {
        var _a;
        const styles = (_a = this._fixed_styles) !== null && _a !== void 0 ? _a : {};
        const styleChildren = new Set();
        let thisStyle = "";
        let hasChildren = false;
        const parent = this.parentElement || this.parentNode;
        for (const [key, value] of Object.entries(styles)) {
            if (key === ".") {
                thisStyle = value;
            }
            else {
                hasChildren = true;
                const elements = await selectTree(parent, key, true);
                if (!elements)
                    continue;
                for (const el of elements) {
                    const ch = await this._styleChildEl(el, value);
                    if (ch)
                        styleChildren.add(ch);
                }
            }
        }
        // Prune old child elements
        for (const oldCh of this._styleChildren) {
            if (!styleChildren.has(oldCh)) {
                if (oldCh)
                    oldCh.styles = "";
            }
        }
        this._styleChildren = styleChildren;
        if (this._styles === thisStyle)
            return;
        this._styles = thisStyle;
        if (this._styles && hasTemplate(this._styles)) {
            this._renderer = this._renderer || this._style_rendered.bind(this);
            bind_template(this._renderer, this._styles, this.variables);
        }
        else {
            this._style_rendered(this._styles || "");
        }
        if (hasChildren) {
            this._observer.disconnect();
            this._observer.observe(parentElement(this), { childList: true });
        }
    }
    async _disconnect() {
        this._observer.disconnect();
        this._styles = "";
        await unbind_template(this._renderer);
    }
    _style_rendered(result) {
        if (this._rendered_styles !== result)
            this._rendered_styles = result;
        this.dispatchEvent(new Event("card-mod-update"));
    }
    createRenderRoot() {
        return this;
    }
    render() {
        return y `
      <style>
        ${this._rendered_styles}
      </style>
    `;
    }
}
__decorate([
    e()
], CardMod.prototype, "_rendered_styles", void 0);
(async () => {
    // Wait for scoped customElements registry to be set up
    // otherwise the customElements registry card-mod is defined in
    // may get overwritten by the polyfill if card-mod is loaded as a module
    while (customElements.get("home-assistant") === undefined)
        await new Promise((resolve) => window.setTimeout(resolve, 100));
    if (!customElements.get("card-mod")) {
        customElements.define("card-mod", CardMod);
        console.info(`%cCARD-MOD ${pjson.version} IS INSTALLED`, "color: green; font-weight: bold");
    }
})();

customElements.whenDefined("ha-card").then(() => {
    const HaCard = customElements.get("ha-card");
    if (HaCard.prototype.cardmod_patched)
        return;
    HaCard.prototype.cardmod_patched = true;
    const _firstUpdated = HaCard.prototype.firstUpdated;
    HaCard.prototype.firstUpdated = function (...args) {
        var _a, _b;
        _firstUpdated === null || _firstUpdated === void 0 ? void 0 : _firstUpdated.bind(this)(...args);
        const config = findConfig(this);
        if ((_a = config === null || config === void 0 ? void 0 : config.card_mod) === null || _a === void 0 ? void 0 : _a.class)
            this.classList.add(config.card_mod.class);
        if (config === null || config === void 0 ? void 0 : config.type)
            this.classList.add(`type-${config.type.replace(":", "-")}`);
        applyToElement(this, "card", ((_b = config === null || config === void 0 ? void 0 : config.card_mod) === null || _b === void 0 ? void 0 : _b.style) || (config === null || config === void 0 ? void 0 : config.style) || "", { config }, null, false).then((cardMod) => {
            var _a;
            const pn = (_a = this.parentNode) === null || _a === void 0 ? void 0 : _a.host;
            if (!pn)
                return;
            if (pn.setConfig && !pn.setConfig.cm_patched) {
                // Patch the setConfig function to get live updates in GUI editor
                const _setConfig = pn.setConfig;
                pn.setConfig = function (config, ...rest) {
                    var _a;
                    _setConfig.bind(this)(config, ...rest);
                    cardMod.variables = { config };
                    cardMod.styles = ((_a = config.card_mod) === null || _a === void 0 ? void 0 : _a.style) || {};
                };
                pn.setConfig.cm_patched = true;
            }
            if (pn.update && !pn.update.cm_patched) {
                const _update = pn.update;
                pn.update = function (...args) {
                    _update.bind(this)(...args);
                    if (this.updateComplete)
                        this.updateComplete.then(() => {
                            cardMod.refresh();
                        });
                    else
                        cardMod.refresh();
                };
                pn.update.cm_patched = true;
            }
        });
    };
});

customElements.whenDefined("hui-entities-card").then(() => {
    const EntitiesCard = customElements.get("hui-entities-card");
    if (EntitiesCard.prototype.cardmod_patched)
        return;
    EntitiesCard.prototype.cardmod_patched = true;
    const _renderEntity = EntitiesCard.prototype.renderEntity;
    EntitiesCard.prototype.renderEntity = function (config, ...rest) {
        var _a;
        const retval = _renderEntity.bind(this)(config, ...rest);
        if (!retval || !retval.values)
            return retval;
        const row = retval.values[0];
        if (!row)
            return retval;
        if ((config === null || config === void 0 ? void 0 : config.type) === "custom:mod-card")
            return retval;
        if ((_a = config === null || config === void 0 ? void 0 : config.card_mod) === null || _a === void 0 ? void 0 : _a.class)
            row.classList.add(config.card_mod.class);
        if (config === null || config === void 0 ? void 0 : config.type)
            row.classList.add(`type-${config.type.replace(":", "-")}`);
        const apply = async () => {
            var _a;
            return applyToElement(row, "row", ((_a = config === null || config === void 0 ? void 0 : config.card_mod) === null || _a === void 0 ? void 0 : _a.style) || (config === null || config === void 0 ? void 0 : config.style) || "", { config });
        };
        (async () => {
            const cardMod = await apply();
            if (row.update && !row.update.cm_patched) {
                const _update = row.update;
                row.update = function (...args) {
                    _update.bind(this)(...args);
                    if (this.updateComplete)
                        this.updateComplete.then(() => {
                            cardMod.refresh();
                        });
                    else
                        cardMod.refresh();
                };
            }
        })();
        this.updateComplete.then(() => apply());
        if (retval.values[0])
            retval.values[0].addEventListener("ll-rebuild", apply);
        return retval;
    };
});

const ENTITY_STYLES = `
div {
  width: 100%;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.name {
  min-height: var(--paper-font-body1_-_line-height, 20px);
}
state-badge {
  margin: 8px 0;
}
`;
customElements.whenDefined("hui-glance-card").then(() => {
    const GlanceCard = customElements.get("hui-glance-card");
    if (GlanceCard.prototype.cardmod_patched)
        return;
    GlanceCard.prototype.cardmod_patched = true;
    const _updated = GlanceCard.prototype.updated;
    GlanceCard.prototype.updated = function (...args) {
        var _a, _b;
        _updated === null || _updated === void 0 ? void 0 : _updated.bind(this)(...args);
        for (const e of this.shadowRoot.querySelectorAll("ha-card div.entity")) {
            if (!e.cardmod_patched) {
                e.cardmod_patched = true;
                // Move everything into a shadowRoot so it can be styled more easily
                const root = e.attachShadow({ mode: "open" });
                while (e.firstChild)
                    root.append(e.firstChild);
                // Add the default styles to the shadowRoot too
                const styletag = document.createElement("style");
                root.appendChild(styletag);
                styletag.innerHTML = ENTITY_STYLES;
            }
            const config = e.config || e.entityConf;
            if ((_a = config === null || config === void 0 ? void 0 : config.card_mod) === null || _a === void 0 ? void 0 : _a.class)
                e.classList.add(config.card_mod.class);
            applyToElement(e, "glance", ((_b = config === null || config === void 0 ? void 0 : config.card_mod) === null || _b === void 0 ? void 0 : _b.style) || (config === null || config === void 0 ? void 0 : config.style) || "", { config });
        }
    };
});

customElements.whenDefined("hui-state-label-badge").then(() => {
    const HuiStateLabelBadge = customElements.get("hui-state-label-badge");
    if (HuiStateLabelBadge.prototype.cardmod_patched)
        return;
    HuiStateLabelBadge.prototype.cardmod_patched = true;
    const _firstUpdated = HuiStateLabelBadge.prototype.firstUpdated;
    HuiStateLabelBadge.prototype.firstUpdated = function (...args) {
        var _a, _b;
        _firstUpdated === null || _firstUpdated === void 0 ? void 0 : _firstUpdated.bind(this)(...args);
        const config = this._config;
        if ((_a = config === null || config === void 0 ? void 0 : config.card_mod) === null || _a === void 0 ? void 0 : _a.class)
            this.classList.add(config.card_mod.class);
        applyToElement(this, "badge", ((_b = config === null || config === void 0 ? void 0 : config.card_mod) === null || _b === void 0 ? void 0 : _b.style) || (config === null || config === void 0 ? void 0 : config.style) || "", {
            config,
        });
    };
});

customElements.whenDefined("hui-view").then(() => {
    const HuiView = customElements.get("hui-view");
    if (HuiView.prototype.cardmod_patched)
        return;
    HuiView.prototype.cardmod_patched = true;
    const _firstUpdated = HuiView.prototype.updated;
    HuiView.prototype.updated = function (...args) {
        _firstUpdated === null || _firstUpdated === void 0 ? void 0 : _firstUpdated.bind(this)(...args);
        applyToElement(this, "view", "", {}, null, false);
    };
});

customElements.whenDefined("hui-root").then(() => {
    const HuiRoot = customElements.get("hui-root");
    if (HuiRoot.prototype.cardmod_patched)
        return;
    HuiRoot.prototype.cardmod_patched = true;
    const _firstUpdated = HuiRoot.prototype.firstUpdated;
    HuiRoot.prototype.firstUpdated = async function (...args) {
        _firstUpdated === null || _firstUpdated === void 0 ? void 0 : _firstUpdated.bind(this)(...args);
        applyToElement(this, "root");
    };
    selectTree(document, "home-assistant$home-assistant-main$partial-panel-resolver ha-panel-lovelace$hui-root", false).then((root) => {
        root === null || root === void 0 ? void 0 : root.firstUpdated();
    });
});

customElements.whenDefined("ha-more-info-dialog").then(() => {
    const HaMoreInfoDialog = customElements.get("ha-more-info-dialog");
    if (HaMoreInfoDialog.prototype.cardmod_patched)
        return;
    HaMoreInfoDialog.prototype.cardmod_patched = true;
    const _showDialog = HaMoreInfoDialog.prototype.showDialog;
    HaMoreInfoDialog.prototype.showDialog = function (params, ...rest) {
        _showDialog === null || _showDialog === void 0 ? void 0 : _showDialog.bind(this)(params, ...rest);
        this.requestUpdate();
        this.updateComplete.then(async () => {
            const haDialog = this.shadowRoot.querySelector("ha-dialog");
            if (haDialog) {
                applyToElement(haDialog, "more-info", "", { config: params }, null, false);
            }
        });
    };
    selectTree(document, "home-assistant$ha-more-info-dialog", false).then((root) => {
        if (root) {
            root.showDialog = HaMoreInfoDialog.prototype.showDialog.bind(root);
            root.showDialog({ entityId: root.entityId });
        }
    });
});

customElements.whenDefined("ha-sidebar").then(() => {
    const HaSidebar = customElements.get("ha-sidebar");
    if (HaSidebar.prototype.cardmod_patched)
        return;
    HaSidebar.prototype.cardmod_patched = true;
    const _firstUpdated = HaSidebar.prototype.firstUpdated;
    HaSidebar.prototype.firstUpdated = async function (...args) {
        _firstUpdated === null || _firstUpdated === void 0 ? void 0 : _firstUpdated.bind(this)(...args);
        applyToElement(this, "sidebar");
    };
    selectTree(document, "home-assistant$home-assistant-main$ ha-sidebar", false).then((root) => {
        root === null || root === void 0 ? void 0 : root.firstUpdated();
    });
});

customElements.whenDefined("hui-card-element-editor").then(() => {
    const HuiCardElementEditor = customElements.get("hui-card-element-editor");
    if (HuiCardElementEditor.prototype.cardmod_patched)
        return;
    HuiCardElementEditor.prototype.cardmod_patched = true;
    const _getConfigElement = HuiCardElementEditor.prototype.getConfigElement;
    HuiCardElementEditor.prototype.getConfigElement = async function () {
        const retval = await _getConfigElement.bind(this)();
        // Catch and patch the configElement
        if (retval) {
            const _setConfig = retval.setConfig;
            retval.setConfig = function (config, ...rest) {
                var _a, _b;
                // Strip card_mod from the data that's sent to the config element
                // and put it back after the config has been checked
                const newConfig = JSON.parse(JSON.stringify(config));
                this._cardModData = {
                    card: newConfig.card_mod,
                    entities: [],
                };
                if (newConfig.entities) {
                    for (const [i, e] of (_a = newConfig.entities) === null || _a === void 0 ? void 0 : _a.entries()) {
                        this._cardModData.entities[i] = e.card_mod;
                        delete e.card_mod;
                    }
                }
                delete newConfig.card_mod;
                _setConfig.bind(this)(newConfig, ...rest);
                if (newConfig.entities) {
                    for (const [i, e] of (_b = newConfig.entities) === null || _b === void 0 ? void 0 : _b.entries()) {
                        if (this._cardModData.entities[i])
                            e.card_mod = this._cardModData.entities[i];
                    }
                }
            };
        }
        return retval;
    };
    const _handleUIConfigChanged = HuiCardElementEditor.prototype._handleUIConfigChanged;
    HuiCardElementEditor.prototype._handleUIConfigChanged = function (ev, ...rest) {
        if (this._configElement && this._configElement._cardModData) {
            const cardMod = this._configElement._cardModData;
            if (cardMod.card)
                ev.detail.config.card_mod = cardMod.card;
        }
        _handleUIConfigChanged.bind(this)(ev, ...rest);
    };
});
customElements.whenDefined("hui-dialog-edit-card").then(() => {
    const HuiDialogEditCard = customElements.get("hui-dialog-edit-card");
    if (HuiDialogEditCard.prototype.cardmod_patched)
        return;
    HuiDialogEditCard.prototype.cardmod_patched = true;
    const _updated = HuiDialogEditCard.prototype.updated;
    HuiDialogEditCard.prototype.updated = function (...args) {
        _updated === null || _updated === void 0 ? void 0 : _updated.bind(this)(...args);
        this.updateComplete.then(async () => {
            var _a, _b, _c;
            if (!this._cardModIcon) {
                this._cardModIcon = document.createElement("ha-icon");
                this._cardModIcon.icon = "mdi:brush";
            }
            const button = this.shadowRoot.querySelector("mwc-button[slot=secondaryAction]");
            if (!button)
                return;
            button.appendChild(this._cardModIcon);
            if (((_a = this._cardConfig) === null || _a === void 0 ? void 0 : _a.card_mod) ||
                ((_c = (_b = this._cardConfig) === null || _b === void 0 ? void 0 : _b.entities) === null || _c === void 0 ? void 0 : _c.some((e) => e.card_mod))) {
                this._cardModIcon.style.visibility = "visible";
            }
            else {
                this._cardModIcon.style.visibility = "hidden";
            }
        });
    };
});

customElements.whenDefined("hui-picture-elements-card").then(() => {
    const HuiPictureElementsCard = customElements.get("hui-picture-elements-card");
    if (HuiPictureElementsCard.prototype.cardmod_patched)
        return;
    HuiPictureElementsCard.prototype.cardmod_patched = true;
    const _setConfig = HuiPictureElementsCard.prototype.setConfig;
    HuiPictureElementsCard.prototype.setConfig = function (...args) {
        var _a, _b;
        _setConfig === null || _setConfig === void 0 ? void 0 : _setConfig.bind(this)(...args);
        for (const [i, el] of this._elements.entries()) {
            const config = this._config.elements[i];
            if ((_a = config === null || config === void 0 ? void 0 : config.card_mod) === null || _a === void 0 ? void 0 : _a.class)
                el.classList.add(config.card_mod.class);
            if (config === null || config === void 0 ? void 0 : config.type)
                el.classList.add(`type-${config.type.replace(":", "-")}`);
            applyToElement(el, "element", (_b = config === null || config === void 0 ? void 0 : config.card_mod) === null || _b === void 0 ? void 0 : _b.style, { config });
        }
    };
});

const updateIcon = (el) => {
    const styles = window.getComputedStyle(el);
    const filter = styles.getPropertyValue("--card-mod-icon-dim");
    if (filter === "none")
        el.style.filter = "none";
    const icon = styles.getPropertyValue("--card-mod-icon");
    if (icon)
        el.icon = icon.trim();
    const color = styles.getPropertyValue("--card-mod-icon-color");
    if (color)
        el.style.color = color;
};
const bindCardMod = async (el) => {
    if (el.cardmod_bound)
        return;
    el.cardmod_bound = true;
    const _bind = async () => {
        const cardMods = await findParentCardMod(el);
        for (const cm of cardMods) {
            cm.addEventListener("card-mod-update", async () => {
                await cm.updateComplete;
                updateIcon(el);
            });
        }
        updateIcon(el);
        return cardMods;
    };
    if ((await _bind()).size == 0)
        window.setTimeout(() => _bind(), 1000);
};
customElements.whenDefined("ha-state-icon").then(() => {
    const HaStateIcon = customElements.get("ha-state-icon");
    if (HaStateIcon.prototype.cardmod_patched)
        return;
    HaStateIcon.prototype.cardmod_patched = true;
    const _updated = HaStateIcon.prototype.updated;
    HaStateIcon.prototype.updated = function (...args) {
        _updated.bind(this)(...args);
        bindCardMod(this);
        updateIcon(this);
    };
});
customElements.whenDefined("ha-icon").then(() => {
    const HaIcon = customElements.get("ha-icon");
    if (HaIcon.prototype.cardmod_patched)
        return;
    HaIcon.prototype.cardmod_patched = true;
    const _updated = HaIcon.prototype.updated;
    HaIcon.prototype.updated = function (...args) {
        _updated === null || _updated === void 0 ? void 0 : _updated.bind(this)(...args);
        bindCardMod(this);
    };
});
customElements.whenDefined("ha-svg-icon").then(() => {
    const HaSvgIcon = customElements.get("ha-svg-icon");
    if (HaSvgIcon.prototype.cardmod_patched)
        return;
    HaSvgIcon.prototype.cardmod_patched = true;
    const _updated = HaSvgIcon.prototype.updated;
    HaSvgIcon.prototype.updated = function (...args) {
        var _a, _b;
        _updated === null || _updated === void 0 ? void 0 : _updated.bind(this)(...args);
        if (((_b = (_a = this.parentNode) === null || _a === void 0 ? void 0 : _a.host) === null || _b === void 0 ? void 0 : _b.localName) === "ha-icon")
            return;
        bindCardMod(this);
    };
});

const NO_STYLE = `
ha-card {
  background: none;
  box-shadow: none;
  border: none;
  transition: none;
}`;
class ModCard extends s {
    setConfig(config) {
        var _a;
        this._config = JSON.parse(JSON.stringify(config));
        let style = ((_a = this._config.card_mod) === null || _a === void 0 ? void 0 : _a.style) || this._config.style;
        if (style === undefined) {
            style = NO_STYLE;
        }
        else if (typeof style === "string") {
            style = NO_STYLE + style;
        }
        else if (style["."]) {
            style["."] = NO_STYLE + style["."];
        }
        else {
            style["."] = NO_STYLE;
        }
        this._config.card_mod = { style };
        this.build_card(config.card);
    }
    async build_card(config) {
        if (this._hass === undefined)
            await new Promise((resolve) => (this._hassResolve = resolve));
        this._hassResolve = undefined;
        const helpers = await window.loadCardHelpers();
        this.card = await helpers.createCardElement(config);
        this.card.hass = this._hass;
    }
    firstUpdated() {
        window.setTimeout(() => {
            var _a, _b;
            if ((_b = (_a = this.card) === null || _a === void 0 ? void 0 : _a.shadowRoot) === null || _b === void 0 ? void 0 : _b.querySelector("ha-card")) {
                console.info("%cYou are doing it wrong!", "color: red; font-weight: bold");
                let cardName = this.card.localName.replace(/hui-(.*)-card/, "$1");
                console.info(`mod-card should NEVER be used with a card that already has a ha-card element, such as ${cardName}`);
            }
        }, 3000);
    }
    set hass(hass) {
        this._hass = hass;
        if (this.card)
            this.card.hass = hass;
        if (this._hassResolve)
            this._hassResolve();
    }
    render() {
        return y ` <ha-card modcard> ${this.card} </ha-card> `;
    }
    getCardSize() {
        if (this._config.report_size)
            return this._config.report_size;
        let ret = this.shadowRoot;
        if (ret)
            ret = ret.querySelector("ha-card card-maker");
        if (ret)
            ret = ret.getCardSize;
        if (ret)
            ret = ret();
        if (ret)
            return ret;
        return 1;
    }
}
__decorate([
    e()
], ModCard.prototype, "card", void 0);
(async () => {
    // See explanation in card-mod.ts
    while (customElements.get("home-assistant") === undefined)
        await new Promise((resolve) => window.setTimeout(resolve, 100));
    if (!customElements.get("mod-card")) {
        customElements.define("mod-card", ModCard);
    }
})();

function refresh_theme() {
    document.dispatchEvent(new Event("cm_update"));
}
const bases = [
    customElements.whenDefined("home-assistant"),
    customElements.whenDefined("hc-main"),
];
Promise.race(bases).then(() => {
    window.setTimeout(async () => {
        var _a, _b;
        const hs = await hass();
        while (!hs) {
            await new Promise((resolve) => window.setTimeout(resolve, 500));
        }
        hs.connection.subscribeEvents(() => {
            window.setTimeout(refresh_theme, 500);
        }, "themes_updated");
        (_a = document
            .querySelector("home-assistant")) === null || _a === void 0 ? void 0 : _a.addEventListener("settheme", refresh_theme);
        (_b = document
            .querySelector("hc-main")) === null || _b === void 0 ? void 0 : _b.addEventListener("settheme", refresh_theme);
    }, 1000);
});

const resources = getResources();
if (resources.some((r) => r.endsWith("card-mod.js"))) ;
else {
    console.info("You may not be getting optimal performance out of card-mod.\nSee https://github.com/thomasloven/lovelace-card-mod#performance-improvements");
}
>>>>>>> 4b6478cc1da50dcfe767b0ef9c6feb0210e1e647
