import{eh as t,ei as e,db as i,dC as n,i as o,da as s,cJ as r,cW as a,s as h,_ as l,n as d,t as u,a as c,cO as f,x as m,cT as p,r as g}from"./card-fe58fbb1.js";var v,y={exports:{}},_={exports:{}},b={exports:{}};function C(){return v||(v=1,e=b,i="undefined"!=typeof window?window:t,n=function(){function t(){}var e=t.prototype;return e.on=function(t,e){if(t&&e){var i=this._events=this._events||{},n=i[t]=i[t]||[];return-1==n.indexOf(e)&&n.push(e),this}},e.once=function(t,e){if(t&&e){this.on(t,e);var i=this._onceEvents=this._onceEvents||{};return(i[t]=i[t]||{})[e]=!0,this}},e.off=function(t,e){var i=this._events&&this._events[t];if(i&&i.length){var n=i.indexOf(e);return-1!=n&&i.splice(n,1),this}},e.emitEvent=function(t,e){var i=this._events&&this._events[t];if(i&&i.length){i=i.slice(0),e=e||[];for(var n=this._onceEvents&&this._onceEvents[t],o=0;o<i.length;o++){var s=i[o];n&&n[s]&&(this.off(t,s),delete n[s]),s.apply(this,e)}return this}},e.allOff=function(){delete this._events,delete this._onceEvents},t},e.exports?e.exports=n():i.EvEmitter=n()),b.exports;var e,i,n}var E,z={exports:{}};
/*!
 * getSize v2.0.3
 * measure size of elements
 * MIT license
 */function x(){return E||(E=1,t=z,function(e,i){t.exports?t.exports=i():e.getSize=i()}(window,(function(){function t(t){var e=parseFloat(t);return-1==t.indexOf("%")&&!isNaN(e)&&e}var e="undefined"==typeof console?function(){}:function(t){console.error(t)},i=["paddingLeft","paddingRight","paddingTop","paddingBottom","marginLeft","marginRight","marginTop","marginBottom","borderLeftWidth","borderRightWidth","borderTopWidth","borderBottomWidth"],n=i.length;function o(t){var i=getComputedStyle(t);return i||e("Style returned "+i+". Are you running this code in a hidden iframe on Firefox? See https://bit.ly/getsizebug1"),i}var s,r=!1;function a(e){if(function(){if(!r){r=!0;var e=document.createElement("div");e.style.width="200px",e.style.padding="1px 2px 3px 4px",e.style.borderStyle="solid",e.style.borderWidth="1px 2px 3px 4px",e.style.boxSizing="border-box";var i=document.body||document.documentElement;i.appendChild(e);var n=o(e);s=200==Math.round(t(n.width)),a.isBoxSizeOuter=s,i.removeChild(e)}}(),"string"==typeof e&&(e=document.querySelector(e)),e&&"object"==typeof e&&e.nodeType){var h=o(e);if("none"==h.display)return function(){for(var t={width:0,height:0,innerWidth:0,innerHeight:0,outerWidth:0,outerHeight:0},e=0;e<n;e++)t[i[e]]=0;return t}();var l={};l.width=e.offsetWidth,l.height=e.offsetHeight;for(var d=l.isBorderBox="border-box"==h.boxSizing,u=0;u<n;u++){var c=i[u],f=h[c],m=parseFloat(f);l[c]=isNaN(m)?0:m}var p=l.paddingLeft+l.paddingRight,g=l.paddingTop+l.paddingBottom,v=l.marginLeft+l.marginRight,y=l.marginTop+l.marginBottom,_=l.borderLeftWidth+l.borderRightWidth,b=l.borderTopWidth+l.borderBottomWidth,C=d&&s,E=t(h.width);!1!==E&&(l.width=E+(C?0:p+_));var z=t(h.height);return!1!==z&&(l.height=z+(C?0:g+b)),l.innerWidth=l.width-(p+_),l.innerHeight=l.height-(g+b),l.outerWidth=l.width+v,l.outerHeight=l.height+y,l}}return a}))),z.exports;var t}var S,L,I={exports:{}},O={exports:{}};function T(){return S||(S=1,t=O,function(e,i){t.exports?t.exports=i():e.matchesSelector=i()}(window,(function(){var t=function(){var t=window.Element.prototype;if(t.matches)return"matches";if(t.matchesSelector)return"matchesSelector";for(var e=["webkit","moz","ms","o"],i=0;i<e.length;i++){var n=e[i]+"MatchesSelector";if(t[n])return n}}();return function(e,i){return e[t](i)}}))),O.exports;var t}function W(){return L||(L=1,t=I,function(e,i){t.exports?t.exports=i(e,T()):e.fizzyUIUtils=i(e,e.matchesSelector)}(window,(function(t,e){var i={extend:function(t,e){for(var i in e)t[i]=e[i];return t},modulo:function(t,e){return(t%e+e)%e}},n=Array.prototype.slice;i.makeArray=function(t){return Array.isArray(t)?t:null==t?[]:"object"==typeof t&&"number"==typeof t.length?n.call(t):[t]},i.removeFrom=function(t,e){var i=t.indexOf(e);-1!=i&&t.splice(i,1)},i.getParent=function(t,i){for(;t.parentNode&&t!=document.body;)if(t=t.parentNode,e(t,i))return t},i.getQueryElement=function(t){return"string"==typeof t?document.querySelector(t):t},i.handleEvent=function(t){var e="on"+t.type;this[e]&&this[e](t)},i.filterFindElements=function(t,n){t=i.makeArray(t);var o=[];return t.forEach((function(t){if(t instanceof HTMLElement)if(n){e(t,n)&&o.push(t);for(var i=t.querySelectorAll(n),s=0;s<i.length;s++)o.push(i[s])}else o.push(t)})),o},i.debounceMethod=function(t,e,i){i=i||100;var n=t.prototype[e],o=e+"Timeout";t.prototype[e]=function(){var t=this[o];clearTimeout(t);var e=arguments,s=this;this[o]=setTimeout((function(){n.apply(s,e),delete s[o]}),i)}},i.docReady=function(t){var e=document.readyState;"complete"==e||"interactive"==e?setTimeout(t):document.addEventListener("DOMContentLoaded",t)},i.toDashed=function(t){return t.replace(/(.)([A-Z])/g,(function(t,e,i){return e+"-"+i})).toLowerCase()};var o=t.console;return i.htmlInit=function(e,n){i.docReady((function(){var s=i.toDashed(n),r="data-"+s,a=document.querySelectorAll("["+r+"]"),h=document.querySelectorAll(".js-"+s),l=i.makeArray(a).concat(i.makeArray(h)),d=r+"-options",u=t.jQuery;l.forEach((function(t){var i,s=t.getAttribute(r)||t.getAttribute(d);try{i=s&&JSON.parse(s)}catch(e){return void(o&&o.error("Error parsing "+r+" on "+t.className+": "+e))}var a=new e(t,i);u&&u.data(t,n,a)}))}))},i}))),I.exports;var t}var w,M,R,H={exports:{}};function P(){return w||(w=1,t=H,function(e,i){t.exports?t.exports=i(C(),x()):(e.Outlayer={},e.Outlayer.Item=i(e.EvEmitter,e.getSize))}(window,(function(t,e){var i=document.documentElement.style,n="string"==typeof i.transition?"transition":"WebkitTransition",o="string"==typeof i.transform?"transform":"WebkitTransform",s={WebkitTransition:"webkitTransitionEnd",transition:"transitionend"}[n],r={transform:o,transition:n,transitionDuration:n+"Duration",transitionProperty:n+"Property",transitionDelay:n+"Delay"};function a(t,e){t&&(this.element=t,this.layout=e,this.position={x:0,y:0},this._create())}var h=a.prototype=Object.create(t.prototype);h.constructor=a,h._create=function(){this._transn={ingProperties:{},clean:{},onEnd:{}},this.css({position:"absolute"})},h.handleEvent=function(t){var e="on"+t.type;this[e]&&this[e](t)},h.getSize=function(){this.size=e(this.element)},h.css=function(t){var e=this.element.style;for(var i in t)e[r[i]||i]=t[i]},h.getPosition=function(){var t=getComputedStyle(this.element),e=this.layout._getOption("originLeft"),i=this.layout._getOption("originTop"),n=t[e?"left":"right"],o=t[i?"top":"bottom"],s=parseFloat(n),r=parseFloat(o),a=this.layout.size;-1!=n.indexOf("%")&&(s=s/100*a.width),-1!=o.indexOf("%")&&(r=r/100*a.height),s=isNaN(s)?0:s,r=isNaN(r)?0:r,s-=e?a.paddingLeft:a.paddingRight,r-=i?a.paddingTop:a.paddingBottom,this.position.x=s,this.position.y=r},h.layoutPosition=function(){var t=this.layout.size,e={},i=this.layout._getOption("originLeft"),n=this.layout._getOption("originTop"),o=i?"paddingLeft":"paddingRight",s=i?"left":"right",r=i?"right":"left",a=this.position.x+t[o];e[s]=this.getXValue(a),e[r]="";var h=n?"paddingTop":"paddingBottom",l=n?"top":"bottom",d=n?"bottom":"top",u=this.position.y+t[h];e[l]=this.getYValue(u),e[d]="",this.css(e),this.emitEvent("layout",[this])},h.getXValue=function(t){var e=this.layout._getOption("horizontal");return this.layout.options.percentPosition&&!e?t/this.layout.size.width*100+"%":t+"px"},h.getYValue=function(t){var e=this.layout._getOption("horizontal");return this.layout.options.percentPosition&&e?t/this.layout.size.height*100+"%":t+"px"},h._transitionTo=function(t,e){this.getPosition();var i=this.position.x,n=this.position.y,o=t==this.position.x&&e==this.position.y;if(this.setPosition(t,e),!o||this.isTransitioning){var s=t-i,r=e-n,a={};a.transform=this.getTranslate(s,r),this.transition({to:a,onTransitionEnd:{transform:this.layoutPosition},isCleaning:!0})}else this.layoutPosition()},h.getTranslate=function(t,e){return"translate3d("+(t=this.layout._getOption("originLeft")?t:-t)+"px, "+(e=this.layout._getOption("originTop")?e:-e)+"px, 0)"},h.goTo=function(t,e){this.setPosition(t,e),this.layoutPosition()},h.moveTo=h._transitionTo,h.setPosition=function(t,e){this.position.x=parseFloat(t),this.position.y=parseFloat(e)},h._nonTransition=function(t){for(var e in this.css(t.to),t.isCleaning&&this._removeStyles(t.to),t.onTransitionEnd)t.onTransitionEnd[e].call(this)},h.transition=function(t){if(parseFloat(this.layout.options.transitionDuration)){var e=this._transn;for(var i in t.onTransitionEnd)e.onEnd[i]=t.onTransitionEnd[i];for(i in t.to)e.ingProperties[i]=!0,t.isCleaning&&(e.clean[i]=!0);t.from&&(this.css(t.from),this.element.offsetHeight),this.enableTransition(t.to),this.css(t.to),this.isTransitioning=!0}else this._nonTransition(t)};var l="opacity,"+o.replace(/([A-Z])/g,(function(t){return"-"+t.toLowerCase()}));h.enableTransition=function(){if(!this.isTransitioning){var t=this.layout.options.transitionDuration;t="number"==typeof t?t+"ms":t,this.css({transitionProperty:l,transitionDuration:t,transitionDelay:this.staggerDelay||0}),this.element.addEventListener(s,this,!1)}},h.onwebkitTransitionEnd=function(t){this.ontransitionend(t)},h.onotransitionend=function(t){this.ontransitionend(t)};var d={"-webkit-transform":"transform"};h.ontransitionend=function(t){if(t.target===this.element){var e=this._transn,i=d[t.propertyName]||t.propertyName;delete e.ingProperties[i],function(t){for(var e in t)return!1;return!0}(e.ingProperties)&&this.disableTransition(),i in e.clean&&(this.element.style[t.propertyName]="",delete e.clean[i]),i in e.onEnd&&(e.onEnd[i].call(this),delete e.onEnd[i]),this.emitEvent("transitionEnd",[this])}},h.disableTransition=function(){this.removeTransitionStyles(),this.element.removeEventListener(s,this,!1),this.isTransitioning=!1},h._removeStyles=function(t){var e={};for(var i in t)e[i]="";this.css(e)};var u={transitionProperty:"",transitionDuration:"",transitionDelay:""};return h.removeTransitionStyles=function(){this.css(u)},h.stagger=function(t){t=isNaN(t)?0:t,this.staggerDelay=t+"ms"},h.removeElem=function(){this.element.parentNode.removeChild(this.element),this.css({display:""}),this.emitEvent("remove",[this])},h.remove=function(){n&&parseFloat(this.layout.options.transitionDuration)?(this.once("transitionEnd",(function(){this.removeElem()})),this.hide()):this.removeElem()},h.reveal=function(){delete this.isHidden,this.css({display:""});var t=this.layout.options,e={};e[this.getHideRevealTransitionEndProperty("visibleStyle")]=this.onRevealTransitionEnd,this.transition({from:t.hiddenStyle,to:t.visibleStyle,isCleaning:!0,onTransitionEnd:e})},h.onRevealTransitionEnd=function(){this.isHidden||this.emitEvent("reveal")},h.getHideRevealTransitionEndProperty=function(t){var e=this.layout.options[t];if(e.opacity)return"opacity";for(var i in e)return i},h.hide=function(){this.isHidden=!0,this.css({display:""});var t=this.layout.options,e={};e[this.getHideRevealTransitionEndProperty("hiddenStyle")]=this.onHideTransitionEnd,this.transition({from:t.visibleStyle,to:t.hiddenStyle,isCleaning:!0,onTransitionEnd:e})},h.onHideTransitionEnd=function(){this.isHidden&&(this.css({display:"none"}),this.emitEvent("hide"))},h.destroy=function(){this.css({position:"",left:"",right:"",top:"",bottom:"",transition:"",transform:""})},a}))),H.exports;var t}
/*!
 * Outlayer v2.1.1
 * the brains and guts of a layout library
 * MIT license
 */function F(){return M||(M=1,t=_,function(e,i){t.exports?t.exports=i(e,C(),x(),W(),P()):e.Outlayer=i(e,e.EvEmitter,e.getSize,e.fizzyUIUtils,e.Outlayer.Item)}(window,(function(t,e,i,n,o){var s=t.console,r=t.jQuery,a=function(){},h=0,l={};function d(t,e){var i=n.getQueryElement(t);if(i){this.element=i,r&&(this.$element=r(this.element)),this.options=n.extend({},this.constructor.defaults),this.option(e);var o=++h;this.element.outlayerGUID=o,l[o]=this,this._create(),this._getOption("initLayout")&&this.layout()}else s&&s.error("Bad element for "+this.constructor.namespace+": "+(i||t))}d.namespace="outlayer",d.Item=o,d.defaults={containerStyle:{position:"relative"},initLayout:!0,originLeft:!0,originTop:!0,resize:!0,resizeContainer:!0,transitionDuration:"0.4s",hiddenStyle:{opacity:0,transform:"scale(0.001)"},visibleStyle:{opacity:1,transform:"scale(1)"}};var u=d.prototype;function c(t){function e(){t.apply(this,arguments)}return e.prototype=Object.create(t.prototype),e.prototype.constructor=e,e}n.extend(u,e.prototype),u.option=function(t){n.extend(this.options,t)},u._getOption=function(t){var e=this.constructor.compatOptions[t];return e&&void 0!==this.options[e]?this.options[e]:this.options[t]},d.compatOptions={initLayout:"isInitLayout",horizontal:"isHorizontal",layoutInstant:"isLayoutInstant",originLeft:"isOriginLeft",originTop:"isOriginTop",resize:"isResizeBound",resizeContainer:"isResizingContainer"},u._create=function(){this.reloadItems(),this.stamps=[],this.stamp(this.options.stamp),n.extend(this.element.style,this.options.containerStyle),this._getOption("resize")&&this.bindResize()},u.reloadItems=function(){this.items=this._itemize(this.element.children)},u._itemize=function(t){for(var e=this._filterFindItemElements(t),i=this.constructor.Item,n=[],o=0;o<e.length;o++){var s=new i(e[o],this);n.push(s)}return n},u._filterFindItemElements=function(t){return n.filterFindElements(t,this.options.itemSelector)},u.getItemElements=function(){return this.items.map((function(t){return t.element}))},u.layout=function(){this._resetLayout(),this._manageStamps();var t=this._getOption("layoutInstant"),e=void 0!==t?t:!this._isLayoutInited;this.layoutItems(this.items,e),this._isLayoutInited=!0},u._init=u.layout,u._resetLayout=function(){this.getSize()},u.getSize=function(){this.size=i(this.element)},u._getMeasurement=function(t,e){var n,o=this.options[t];o?("string"==typeof o?n=this.element.querySelector(o):o instanceof HTMLElement&&(n=o),this[t]=n?i(n)[e]:o):this[t]=0},u.layoutItems=function(t,e){t=this._getItemsForLayout(t),this._layoutItems(t,e),this._postLayout()},u._getItemsForLayout=function(t){return t.filter((function(t){return!t.isIgnored}))},u._layoutItems=function(t,e){if(this._emitCompleteOnItems("layout",t),t&&t.length){var i=[];t.forEach((function(t){var n=this._getItemLayoutPosition(t);n.item=t,n.isInstant=e||t.isLayoutInstant,i.push(n)}),this),this._processLayoutQueue(i)}},u._getItemLayoutPosition=function(){return{x:0,y:0}},u._processLayoutQueue=function(t){this.updateStagger(),t.forEach((function(t,e){this._positionItem(t.item,t.x,t.y,t.isInstant,e)}),this)},u.updateStagger=function(){var t=this.options.stagger;if(null!=t)return this.stagger=function(t){if("number"==typeof t)return t;var e=t.match(/(^\d*\.?\d*)(\w*)/),i=e&&e[1],n=e&&e[2];if(!i.length)return 0;i=parseFloat(i);var o=f[n]||1;return i*o}(t),this.stagger;this.stagger=0},u._positionItem=function(t,e,i,n,o){n?t.goTo(e,i):(t.stagger(o*this.stagger),t.moveTo(e,i))},u._postLayout=function(){this.resizeContainer()},u.resizeContainer=function(){if(this._getOption("resizeContainer")){var t=this._getContainerSize();t&&(this._setContainerMeasure(t.width,!0),this._setContainerMeasure(t.height,!1))}},u._getContainerSize=a,u._setContainerMeasure=function(t,e){if(void 0!==t){var i=this.size;i.isBorderBox&&(t+=e?i.paddingLeft+i.paddingRight+i.borderLeftWidth+i.borderRightWidth:i.paddingBottom+i.paddingTop+i.borderTopWidth+i.borderBottomWidth),t=Math.max(t,0),this.element.style[e?"width":"height"]=t+"px"}},u._emitCompleteOnItems=function(t,e){var i=this;function n(){i.dispatchEvent(t+"Complete",null,[e])}var o=e.length;if(e&&o){var s=0;e.forEach((function(e){e.once(t,r)}))}else n();function r(){++s==o&&n()}},u.dispatchEvent=function(t,e,i){var n=e?[e].concat(i):i;if(this.emitEvent(t,n),r)if(this.$element=this.$element||r(this.element),e){var o=r.Event(e);o.type=t,this.$element.trigger(o,i)}else this.$element.trigger(t,i)},u.ignore=function(t){var e=this.getItem(t);e&&(e.isIgnored=!0)},u.unignore=function(t){var e=this.getItem(t);e&&delete e.isIgnored},u.stamp=function(t){(t=this._find(t))&&(this.stamps=this.stamps.concat(t),t.forEach(this.ignore,this))},u.unstamp=function(t){(t=this._find(t))&&t.forEach((function(t){n.removeFrom(this.stamps,t),this.unignore(t)}),this)},u._find=function(t){if(t)return"string"==typeof t&&(t=this.element.querySelectorAll(t)),t=n.makeArray(t)},u._manageStamps=function(){this.stamps&&this.stamps.length&&(this._getBoundingRect(),this.stamps.forEach(this._manageStamp,this))},u._getBoundingRect=function(){var t=this.element.getBoundingClientRect(),e=this.size;this._boundingRect={left:t.left+e.paddingLeft+e.borderLeftWidth,top:t.top+e.paddingTop+e.borderTopWidth,right:t.right-(e.paddingRight+e.borderRightWidth),bottom:t.bottom-(e.paddingBottom+e.borderBottomWidth)}},u._manageStamp=a,u._getElementOffset=function(t){var e=t.getBoundingClientRect(),n=this._boundingRect,o=i(t);return{left:e.left-n.left-o.marginLeft,top:e.top-n.top-o.marginTop,right:n.right-e.right-o.marginRight,bottom:n.bottom-e.bottom-o.marginBottom}},u.handleEvent=n.handleEvent,u.bindResize=function(){t.addEventListener("resize",this),this.isResizeBound=!0},u.unbindResize=function(){t.removeEventListener("resize",this),this.isResizeBound=!1},u.onresize=function(){this.resize()},n.debounceMethod(d,"onresize",100),u.resize=function(){this.isResizeBound&&this.needsResizeLayout()&&this.layout()},u.needsResizeLayout=function(){var t=i(this.element);return this.size&&t&&t.innerWidth!==this.size.innerWidth},u.addItems=function(t){var e=this._itemize(t);return e.length&&(this.items=this.items.concat(e)),e},u.appended=function(t){var e=this.addItems(t);e.length&&(this.layoutItems(e,!0),this.reveal(e))},u.prepended=function(t){var e=this._itemize(t);if(e.length){var i=this.items.slice(0);this.items=e.concat(i),this._resetLayout(),this._manageStamps(),this.layoutItems(e,!0),this.reveal(e),this.layoutItems(i)}},u.reveal=function(t){if(this._emitCompleteOnItems("reveal",t),t&&t.length){var e=this.updateStagger();t.forEach((function(t,i){t.stagger(i*e),t.reveal()}))}},u.hide=function(t){if(this._emitCompleteOnItems("hide",t),t&&t.length){var e=this.updateStagger();t.forEach((function(t,i){t.stagger(i*e),t.hide()}))}},u.revealItemElements=function(t){var e=this.getItems(t);this.reveal(e)},u.hideItemElements=function(t){var e=this.getItems(t);this.hide(e)},u.getItem=function(t){for(var e=0;e<this.items.length;e++){var i=this.items[e];if(i.element==t)return i}},u.getItems=function(t){t=n.makeArray(t);var e=[];return t.forEach((function(t){var i=this.getItem(t);i&&e.push(i)}),this),e},u.remove=function(t){var e=this.getItems(t);this._emitCompleteOnItems("remove",e),e&&e.length&&e.forEach((function(t){t.remove(),n.removeFrom(this.items,t)}),this)},u.destroy=function(){var t=this.element.style;t.height="",t.position="",t.width="",this.items.forEach((function(t){t.destroy()})),this.unbindResize();var e=this.element.outlayerGUID;delete l[e],delete this.element.outlayerGUID,r&&r.removeData(this.element,this.constructor.namespace)},d.data=function(t){var e=(t=n.getQueryElement(t))&&t.outlayerGUID;return e&&l[e]},d.create=function(t,e){var i=c(d);return i.defaults=n.extend({},d.defaults),n.extend(i.defaults,e),i.compatOptions=n.extend({},d.compatOptions),i.namespace=t,i.data=d.data,i.Item=c(o),n.htmlInit(i,t),r&&r.bridget&&r.bridget(t,i),i};var f={ms:1,s:1e3};return d.Item=o,d}))),_.exports;var t}
/*!
 * Masonry v4.2.2
 * Cascading grid layout library
 * https://masonry.desandro.com
 * MIT License
 * by David DeSandro
 */R=y,function(t,e){R.exports?R.exports=e(F(),x()):t.Masonry=e(t.Outlayer,t.getSize)}(window,(function(t,e){var i=t.create("masonry");i.compatOptions.fitWidth="isFitWidth";var n=i.prototype;return n._resetLayout=function(){this.getSize(),this._getMeasurement("columnWidth","outerWidth"),this._getMeasurement("gutter","outerWidth"),this.measureColumns(),this.colYs=[];for(var t=0;t<this.cols;t++)this.colYs.push(0);this.maxY=0,this.horizontalColIndex=0},n.measureColumns=function(){if(this.getContainerWidth(),!this.columnWidth){var t=this.items[0],i=t&&t.element;this.columnWidth=i&&e(i).outerWidth||this.containerWidth}var n=this.columnWidth+=this.gutter,o=this.containerWidth+this.gutter,s=o/n,r=n-o%n;s=Math[r&&r<1?"round":"floor"](s),this.cols=Math.max(s,1)},n.getContainerWidth=function(){var t=this._getOption("fitWidth")?this.element.parentNode:this.element,i=e(t);this.containerWidth=i&&i.innerWidth},n._getItemLayoutPosition=function(t){t.getSize();var e=t.size.outerWidth%this.columnWidth,i=Math[e&&e<1?"round":"ceil"](t.size.outerWidth/this.columnWidth);i=Math.min(i,this.cols);for(var n=this[this.options.horizontalOrder?"_getHorizontalColPosition":"_getTopColPosition"](i,t),o={x:this.columnWidth*n.col,y:n.y},s=n.y+t.size.outerHeight,r=i+n.col,a=n.col;a<r;a++)this.colYs[a]=s;return o},n._getTopColPosition=function(t){var e=this._getTopColGroup(t),i=Math.min.apply(Math,e);return{col:e.indexOf(i),y:i}},n._getTopColGroup=function(t){if(t<2)return this.colYs;for(var e=[],i=this.cols+1-t,n=0;n<i;n++)e[n]=this._getColGroupY(n,t);return e},n._getColGroupY=function(t,e){if(e<2)return this.colYs[t];var i=this.colYs.slice(t,t+e);return Math.max.apply(Math,i)},n._getHorizontalColPosition=function(t,e){var i=this.horizontalColIndex%this.cols;i=t>1&&i+t>this.cols?0:i;var n=e.size.outerWidth&&e.size.outerHeight;return this.horizontalColIndex=n?i+t:this.horizontalColIndex,{col:i,y:this._getColGroupY(i,t)}},n._manageStamp=function(t){var i=e(t),n=this._getElementOffset(t),o=this._getOption("originLeft")?n.left:n.right,s=o+i.outerWidth,r=Math.floor(o/this.columnWidth);r=Math.max(0,r);var a=Math.floor(s/this.columnWidth);a-=s%this.columnWidth?0:1,a=Math.min(this.cols-1,a);for(var h=(this._getOption("originTop")?n.top:n.bottom)+i.outerHeight,l=r;l<=a;l++)this.colYs[l]=Math.max(h,this.colYs[l])},n._getContainerSize=function(){this.maxY=Math.max.apply(Math,this.colYs);var t={height:this.maxY};return this._getOption("fitWidth")&&(t.width=this._getContainerFitWidth()),t},n._getContainerFitWidth=function(){for(var t=0,e=this.cols;--e&&0===this.colYs[e];)t++;return(this.cols-t)*this.columnWidth-this.gutter},n.needsResizeLayout=function(){var t=this.containerWidth;return this.getContainerWidth(),t!=this.containerWidth},i}));var B=e(y.exports);class A{constructor(t,e){this._mediaLoadedInfoMap=new Map,this._gridContents=new Map,this._masonry=null,this._displayConfig=null,this._throttledLayout=i((()=>this._masonry?.layout?.()),300,{trailing:!0,leading:!1}),this._hostMutationObserver=new MutationObserver(((t,e)=>this._calculateGridContentsFromHost())),this._cellMutationObserver=new MutationObserver(((t,e)=>this._calculateGridContentsFromHost())),this._hostResizeObserver=new ResizeObserver(this._hostResizeHandler.bind(this)),this._cellResizeObserver=new ResizeObserver(this._cellResizeHandler.bind(this)),this._calculateGridContentsFromHost=()=>{const t=n(this._host),e=new Map;for(const i of t){const t=i.getAttribute(this._idAttribute)||String(e.size);e.set(t,i)}this._setGridContents(e)},this._handleMediaLoadedInfoEvent=t=>{const e=t.composedPath();for(const[i,n]of this._gridContents.entries())
/* istanbul ignore else: the else path cannot be reached -- @preserve */
if(e.includes(n)){this._mediaLoadedInfoMap.set(i,t.detail),i!==this._selected&&t.stopPropagation();break}},this._handleSelectGridCellEvent=t=>{const e=t.composedPath();for(const[i,n]of this._gridContents.entries())
/* istanbul ignore else: the else path cannot be reached -- @preserve */
if(e.includes(n)){this._selected!==i&&(this.selectCell(i),t.stopPropagation());break}},this._host=t,this._selected=e?.selected??null,this._idAttribute=e?.idAttribute??"grid-id",this._hostWidth=this._host.getBoundingClientRect().width,this._hostResizeObserver.observe(t),this._displayConfig=e?.displayConfig??null,this._hostMutationObserver.observe(t,{childList:!0}),t instanceof HTMLSlotElement&&t.addEventListener("slotchange",this._calculateGridContentsFromHost),this._calculateGridContentsFromHost()}destroy(){this._hostResizeObserver.disconnect(),this._cellResizeObserver.disconnect(),this._hostMutationObserver.disconnect(),this._cellMutationObserver.disconnect(),this._host instanceof HTMLSlotElement&&this._host.removeEventListener("slotchange",this._calculateGridContentsFromHost),this._mediaLoadedInfoMap.clear(),this._masonry?.destroy?.(),this._masonry=null;for(const t of this._gridContents.values())this._removeChildEventListeners(t);this._gridContents.clear()}setDisplayConfig(t){o(t,this._displayConfig)||(this._displayConfig=t,this._calculateGridContentsFromHost())}getGridContents(){return this._gridContents}getGridSize(){return this._gridContents.size}getSelected(){return this._selected}selectCell(t){if(this._selected===t)return;this._selected=t,s(this._host,"media-grid:selected",{selected:t});const e=this._mediaLoadedInfoMap.get(t);e&&r(this._host,e),this._updateSelectedStylesOnElements(),this._throttledLayout()}unselectAll(){null!==this._selected&&(a(this._host),s(this._host,"media-grid:unselected")),this._selected=null,this._updateSelectedStylesOnElements()}_setGridContents(t){this._gridContents=t;for(const e of this._mediaLoadedInfoMap.keys())t.has(e)||this._mediaLoadedInfoMap.delete(e);null===this._selected||this._gridContents.has(this._selected)||this.unselectAll();for(const e of t.values())this._removeChildEventListeners(e),this._addChildEventListeners(e);this._setColumnSizeStyles(),this._createMasonry(),this._cellMutationObserver.disconnect(),this._cellResizeObserver.disconnect();for(const e of t.values())this._cellMutationObserver.observe(e,{attributeFilter:[this._idAttribute],attributes:!0}),this._cellResizeObserver.observe(e);this._updateSelectedStylesOnElements(),this._setColumnSizeStyles()}_hostResizeHandler(){const t=this._host.getBoundingClientRect();t.width!==this._hostWidth&&(this._hostWidth=t.width,this._setColumnSizeStyles(),this._createMasonry())}_cellResizeHandler(){this._throttledLayout()}_addChildEventListeners(t){t.addEventListener("click",this._handleSelectGridCellEvent,{capture:!0}),t.addEventListener("frigate-card:media:loaded",this._handleMediaLoadedInfoEvent)}_removeChildEventListeners(t){t.removeEventListener("click",this._handleSelectGridCellEvent,{capture:!0}),t.removeEventListener("frigate-card:media:loaded",this._handleMediaLoadedInfoEvent)}_createMasonry(){this._masonry&&this._masonry.destroy?.(),this._masonry=new B(this._host,{columnWidth:this._getColumnSize(),initLayout:!1,percentPosition:!0,transitionDuration:"0.2s"}),this._masonry.addItems?.([...this._gridContents.values()]),this._throttledLayout()}_updateSelectedStylesOnElements(){for(const[t,e]of this._gridContents.entries())h(e,t===this._selected,"selected"),h(e,t!==this._selected,"unselected")}_getColumnSize(){return Math.round(this._hostWidth/this._getColumns())}_getColumns(){if(this._displayConfig?.grid_columns)return this._displayConfig?.grid_columns;const t=this._displayConfig?.grid_max_columns??1/0,e=Math.min(t,Math.floor(this._hostWidth/600));if(e>1)return e;const i=Math.floor(Math.min(t,this._hostWidth/190));return Math.max(1,i)}_setColumnSizeStyles(){this._host.style.setProperty("--frigate-card-grid-column-size",`${this._getColumnSize()}px`),this._host.style.setProperty("--frigate-card-grid-selected-width-factor",`${this._displayConfig?.grid_selected_width_factor??2}`)}}let k=class extends c{constructor(){super(...arguments),this._controller=null,this._refSlot=f()}connectedCallback(){super.connectedCallback(),this.requestUpdate()}disconnectedCallback(){this._controller?.destroy(),this._controller=null,super.disconnectedCallback()}updated(t){!this._controller&&this._refSlot.value&&(this._controller=new A(this._refSlot.value,{selected:this.selected,displayConfig:this.displayConfig})),t.has("selected")&&(this.selected?this._controller?.selectCell(this.selected):this._controller?.unselectAll()),t.has("displayConfig")&&this._controller?.setDisplayConfig(this.displayConfig??null)}render(){return m`<slot ${p(this._refSlot)}></slot> `}static get styles(){return g(":host {\n  display: block;\n  width: 100%;\n  height: 100%;\n  --frigate-card-grid-border-size: 3px;\n  --frigate-card-grid-column-size: 100%;\n  --frigate-card-grid-selected-width-factor: 2;\n  overflow: auto;\n  scrollbar-width: none;\n  -ms-overflow-style: none;\n}\n\n/* Hide scrollbar for Chrome, Safari and Opera */\n:host::-webkit-scrollbar {\n  display: none;\n}\n\n::slotted(*) {\n  box-sizing: border-box;\n  border-radius: var(--ha-card-border-radius, 4px);\n  overflow: hidden;\n  width: var(--frigate-card-grid-column-size);\n  border: var(--frigate-card-grid-border-size) solid transparent;\n}\n\n::slotted([selected]) {\n  border: var(--frigate-card-grid-border-size) solid var(--primary-color);\n  width: min(100%, var(--frigate-card-grid-selected-width-factor) * var(--frigate-card-grid-column-size));\n  z-index: 2;\n}\n\nslot {\n  display: block;\n}")}};l([d({attribute:!1})],k.prototype,"selected",void 0),l([d({attribute:!1})],k.prototype,"displayConfig",void 0),k=l([u("frigate-card-media-grid")],k);export{k as FrigateCardMediaGrid};
