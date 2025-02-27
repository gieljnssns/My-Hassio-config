/* Version: 1.3.7-beta.1 - 2025-02-17 19:37:00 */
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
/* global Reflect, Promise, SuppressedError, Symbol, Iterator */

var extendStatics = function(d, b) {
    extendStatics = Object.setPrototypeOf ||
        ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
        function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
    return extendStatics(d, b);
};

function __extends$1(d, b) {
    if (typeof b !== "function" && b !== null)
        throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
    extendStatics(d, b);
    function __() { this.constructor = d; }
    d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
}

var __assign$2 = function() {
    __assign$2 = Object.assign || function __assign(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p)) t[p] = s[p];
        }
        return t;
    };
    return __assign$2.apply(this, arguments);
};

function __rest(s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
}

function __decorate(decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
}

function __param(paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
}

function __esDecorate(ctor, descriptorIn, decorators, contextIn, initializers, extraInitializers) {
    function accept(f) { if (f !== void 0 && typeof f !== "function") throw new TypeError("Function expected"); return f; }
    var kind = contextIn.kind, key = kind === "getter" ? "get" : kind === "setter" ? "set" : "value";
    var target = !descriptorIn && ctor ? contextIn["static"] ? ctor : ctor.prototype : null;
    var descriptor = descriptorIn || (target ? Object.getOwnPropertyDescriptor(target, contextIn.name) : {});
    var _, done = false;
    for (var i = decorators.length - 1; i >= 0; i--) {
        var context = {};
        for (var p in contextIn) context[p] = p === "access" ? {} : contextIn[p];
        for (var p in contextIn.access) context.access[p] = contextIn.access[p];
        context.addInitializer = function (f) { if (done) throw new TypeError("Cannot add initializers after decoration has completed"); extraInitializers.push(accept(f || null)); };
        var result = (0, decorators[i])(kind === "accessor" ? { get: descriptor.get, set: descriptor.set } : descriptor[key], context);
        if (kind === "accessor") {
            if (result === void 0) continue;
            if (result === null || typeof result !== "object") throw new TypeError("Object expected");
            if (_ = accept(result.get)) descriptor.get = _;
            if (_ = accept(result.set)) descriptor.set = _;
            if (_ = accept(result.init)) initializers.unshift(_);
        }
        else if (_ = accept(result)) {
            if (kind === "field") initializers.unshift(_);
            else descriptor[key] = _;
        }
    }
    if (target) Object.defineProperty(target, contextIn.name, descriptor);
    done = true;
};

function __runInitializers(thisArg, initializers, value) {
    var useValue = arguments.length > 2;
    for (var i = 0; i < initializers.length; i++) {
        value = useValue ? initializers[i].call(thisArg, value) : initializers[i].call(thisArg);
    }
    return useValue ? value : void 0;
};

function __propKey(x) {
    return typeof x === "symbol" ? x : "".concat(x);
};

function __setFunctionName(f, name, prefix) {
    if (typeof name === "symbol") name = name.description ? "[".concat(name.description, "]") : "";
    return Object.defineProperty(f, "name", { configurable: true, value: prefix ? "".concat(prefix, " ", name) : name });
};

function __metadata(metadataKey, metadataValue) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(metadataKey, metadataValue);
}

function __awaiter(thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
}

function __generator(thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
}

var __createBinding = Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
        desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
});

function __exportStar(m, o) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(o, p)) __createBinding(o, m, p);
}

function __values(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
}

function __read(o, n) {
    var m = typeof Symbol === "function" && o[Symbol.iterator];
    if (!m) return o;
    var i = m.call(o), r, ar = [], e;
    try {
        while ((n === void 0 || n-- > 0) && !(r = i.next()).done) ar.push(r.value);
    }
    catch (error) { e = { error: error }; }
    finally {
        try {
            if (r && !r.done && (m = i["return"])) m.call(i);
        }
        finally { if (e) throw e.error; }
    }
    return ar;
}

/** @deprecated */
function __spread() {
    for (var ar = [], i = 0; i < arguments.length; i++)
        ar = ar.concat(__read(arguments[i]));
    return ar;
}

/** @deprecated */
function __spreadArrays() {
    for (var s = 0, i = 0, il = arguments.length; i < il; i++) s += arguments[i].length;
    for (var r = Array(s), k = 0, i = 0; i < il; i++)
        for (var a = arguments[i], j = 0, jl = a.length; j < jl; j++, k++)
            r[k] = a[j];
    return r;
}

function __spreadArray(to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
}

function __await(v) {
    return this instanceof __await ? (this.v = v, this) : new __await(v);
}

function __asyncGenerator(thisArg, _arguments, generator) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var g = generator.apply(thisArg, _arguments || []), i, q = [];
    return i = Object.create((typeof AsyncIterator === "function" ? AsyncIterator : Object).prototype), verb("next"), verb("throw"), verb("return", awaitReturn), i[Symbol.asyncIterator] = function () { return this; }, i;
    function awaitReturn(f) { return function (v) { return Promise.resolve(v).then(f, reject); }; }
    function verb(n, f) { if (g[n]) { i[n] = function (v) { return new Promise(function (a, b) { q.push([n, v, a, b]) > 1 || resume(n, v); }); }; if (f) i[n] = f(i[n]); } }
    function resume(n, v) { try { step(g[n](v)); } catch (e) { settle(q[0][3], e); } }
    function step(r) { r.value instanceof __await ? Promise.resolve(r.value.v).then(fulfill, reject) : settle(q[0][2], r); }
    function fulfill(value) { resume("next", value); }
    function reject(value) { resume("throw", value); }
    function settle(f, v) { if (f(v), q.shift(), q.length) resume(q[0][0], q[0][1]); }
}

function __asyncDelegator(o) {
    var i, p;
    return i = {}, verb("next"), verb("throw", function (e) { throw e; }), verb("return"), i[Symbol.iterator] = function () { return this; }, i;
    function verb(n, f) { i[n] = o[n] ? function (v) { return (p = !p) ? { value: __await(o[n](v)), done: false } : f ? f(v) : v; } : f; }
}

function __asyncValues(o) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var m = o[Symbol.asyncIterator], i;
    return m ? m.call(o) : (o = typeof __values === "function" ? __values(o) : o[Symbol.iterator](), i = {}, verb("next"), verb("throw"), verb("return"), i[Symbol.asyncIterator] = function () { return this; }, i);
    function verb(n) { i[n] = o[n] && function (v) { return new Promise(function (resolve, reject) { v = o[n](v), settle(resolve, reject, v.done, v.value); }); }; }
    function settle(resolve, reject, d, v) { Promise.resolve(v).then(function(v) { resolve({ value: v, done: d }); }, reject); }
}

function __makeTemplateObject(cooked, raw) {
    if (Object.defineProperty) { Object.defineProperty(cooked, "raw", { value: raw }); } else { cooked.raw = raw; }
    return cooked;
};

var __setModuleDefault = Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
};

var ownKeys = function(o) {
    ownKeys = Object.getOwnPropertyNames || function (o) {
        var ar = [];
        for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
        return ar;
    };
    return ownKeys(o);
};

function __importStar(mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
    __setModuleDefault(result, mod);
    return result;
}

function __importDefault(mod) {
    return (mod && mod.__esModule) ? mod : { default: mod };
}

function __classPrivateFieldGet(receiver, state, kind, f) {
    if (kind === "a" && !f) throw new TypeError("Private accessor was defined without a getter");
    if (typeof state === "function" ? receiver !== state || !f : !state.has(receiver)) throw new TypeError("Cannot read private member from an object whose class did not declare it");
    return kind === "m" ? f : kind === "a" ? f.call(receiver) : f ? f.value : state.get(receiver);
}

function __classPrivateFieldSet(receiver, state, value, kind, f) {
    if (kind === "m") throw new TypeError("Private method is not writable");
    if (kind === "a" && !f) throw new TypeError("Private accessor was defined without a setter");
    if (typeof state === "function" ? receiver !== state || !f : !state.has(receiver)) throw new TypeError("Cannot write private member to an object whose class did not declare it");
    return (kind === "a" ? f.call(receiver, value) : f ? f.value = value : state.set(receiver, value)), value;
}

function __classPrivateFieldIn(state, receiver) {
    if (receiver === null || (typeof receiver !== "object" && typeof receiver !== "function")) throw new TypeError("Cannot use 'in' operator on non-object");
    return typeof state === "function" ? receiver === state : state.has(receiver);
}

function __addDisposableResource(env, value, async) {
    if (value !== null && value !== void 0) {
        if (typeof value !== "object" && typeof value !== "function") throw new TypeError("Object expected.");
        var dispose, inner;
        if (async) {
            if (!Symbol.asyncDispose) throw new TypeError("Symbol.asyncDispose is not defined.");
            dispose = value[Symbol.asyncDispose];
        }
        if (dispose === void 0) {
            if (!Symbol.dispose) throw new TypeError("Symbol.dispose is not defined.");
            dispose = value[Symbol.dispose];
            if (async) inner = dispose;
        }
        if (typeof dispose !== "function") throw new TypeError("Object not disposable.");
        if (inner) dispose = function() { try { inner.call(this); } catch (e) { return Promise.reject(e); } };
        env.stack.push({ value: value, dispose: dispose, async: async });
    }
    else if (async) {
        env.stack.push({ async: true });
    }
    return value;

}

var _SuppressedError = typeof SuppressedError === "function" ? SuppressedError : function (error, suppressed, message) {
    var e = new Error(message);
    return e.name = "SuppressedError", e.error = error, e.suppressed = suppressed, e;
};

function __disposeResources(env) {
    function fail(e) {
        env.error = env.hasError ? new _SuppressedError(e, env.error, "An error was suppressed during disposal.") : e;
        env.hasError = true;
    }
    var r, s = 0;
    function next() {
        while (r = env.stack.pop()) {
            try {
                if (!r.async && s === 1) return s = 0, env.stack.push(r), Promise.resolve().then(next);
                if (r.dispose) {
                    var result = r.dispose.call(r.value);
                    if (r.async) return s |= 2, Promise.resolve(result).then(next, function(e) { fail(e); return next(); });
                }
                else s |= 1;
            }
            catch (e) {
                fail(e);
            }
        }
        if (s === 1) return env.hasError ? Promise.reject(env.error) : Promise.resolve();
        if (env.hasError) throw env.error;
    }
    return next();
}

function __rewriteRelativeImportExtension(path, preserveJsx) {
    if (typeof path === "string" && /^\.\.?\//.test(path)) {
        return path.replace(/\.(tsx)$|((?:\.d)?)((?:\.[^./]+?)?)\.([cm]?)ts$/i, function (m, tsx, d, ext, cm) {
            return tsx ? preserveJsx ? ".jsx" : ".js" : d && (!ext || !cm) ? m : (d + ext + "." + cm.toLowerCase() + "js");
        });
    }
    return path;
}

var tslib_es6 = {
    __extends: __extends$1,
    __assign: __assign$2,
    __rest: __rest,
    __decorate: __decorate,
    __param: __param,
    __esDecorate: __esDecorate,
    __runInitializers: __runInitializers,
    __propKey: __propKey,
    __setFunctionName: __setFunctionName,
    __metadata: __metadata,
    __awaiter: __awaiter,
    __generator: __generator,
    __createBinding: __createBinding,
    __exportStar: __exportStar,
    __values: __values,
    __read: __read,
    __spread: __spread,
    __spreadArrays: __spreadArrays,
    __spreadArray: __spreadArray,
    __await: __await,
    __asyncGenerator: __asyncGenerator,
    __asyncDelegator: __asyncDelegator,
    __asyncValues: __asyncValues,
    __makeTemplateObject: __makeTemplateObject,
    __importStar: __importStar,
    __importDefault: __importDefault,
    __classPrivateFieldGet: __classPrivateFieldGet,
    __classPrivateFieldSet: __classPrivateFieldSet,
    __classPrivateFieldIn: __classPrivateFieldIn,
    __addDisposableResource: __addDisposableResource,
    __disposeResources: __disposeResources,
    __rewriteRelativeImportExtension: __rewriteRelativeImportExtension,
};

/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$4=window,e$9=t$4.ShadowRoot&&(void 0===t$4.ShadyCSS||t$4.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s$4=Symbol(),n$6=new WeakMap;let o$7 = class o{constructor(t,e,n){if(this._$cssResult$=!0,n!==s$4)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e;}get styleSheet(){let t=this.o;const s=this.t;if(e$9&&void 0===t){const e=void 0!==s&&1===s.length;e&&(t=n$6.get(s)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),e&&n$6.set(s,t));}return t}toString(){return this.cssText}};const r$4=t=>new o$7("string"==typeof t?t:t+"",void 0,s$4),i$4=(t,...e)=>{const n=1===t.length?t[0]:e.reduce(((e,s,n)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[n+1]),t[0]);return new o$7(n,t,s$4)},S$2=(s,n)=>{e$9?s.adoptedStyleSheets=n.map((t=>t instanceof CSSStyleSheet?t:t.styleSheet)):n.forEach((e=>{const n=document.createElement("style"),o=t$4.litNonce;void 0!==o&&n.setAttribute("nonce",o),n.textContent=e.cssText,s.appendChild(n);}));},c$2=e$9?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return r$4(e)})(t):t;

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */var s$3;const e$8=window,r$3=e$8.trustedTypes,h$3=r$3?r$3.emptyScript:"",o$6=e$8.reactiveElementPolyfillSupport,n$5={toAttribute(t,i){switch(i){case Boolean:t=t?h$3:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t);}return t},fromAttribute(t,i){let s=t;switch(i){case Boolean:s=null!==t;break;case Number:s=null===t?null:Number(t);break;case Object:case Array:try{s=JSON.parse(t);}catch(t){s=null;}}return s}},a$2=(t,i)=>i!==t&&(i==i||t==t),l$4={attribute:!0,type:String,converter:n$5,reflect:!1,hasChanged:a$2},d$2="finalized";let u$2 = class u extends HTMLElement{constructor(){super(),this._$Ei=new Map,this.isUpdatePending=!1,this.hasUpdated=!1,this._$El=null,this._$Eu();}static addInitializer(t){var i;this.finalize(),(null!==(i=this.h)&&void 0!==i?i:this.h=[]).push(t);}static get observedAttributes(){this.finalize();const t=[];return this.elementProperties.forEach(((i,s)=>{const e=this._$Ep(s,i);void 0!==e&&(this._$Ev.set(e,s),t.push(e));})),t}static createProperty(t,i=l$4){if(i.state&&(i.attribute=!1),this.finalize(),this.elementProperties.set(t,i),!i.noAccessor&&!this.prototype.hasOwnProperty(t)){const s="symbol"==typeof t?Symbol():"__"+t,e=this.getPropertyDescriptor(t,s,i);void 0!==e&&Object.defineProperty(this.prototype,t,e);}}static getPropertyDescriptor(t,i,s){return {get(){return this[i]},set(e){const r=this[t];this[i]=e,this.requestUpdate(t,r,s);},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)||l$4}static finalize(){if(this.hasOwnProperty(d$2))return !1;this[d$2]=!0;const t=Object.getPrototypeOf(this);if(t.finalize(),void 0!==t.h&&(this.h=[...t.h]),this.elementProperties=new Map(t.elementProperties),this._$Ev=new Map,this.hasOwnProperty("properties")){const t=this.properties,i=[...Object.getOwnPropertyNames(t),...Object.getOwnPropertySymbols(t)];for(const s of i)this.createProperty(s,t[s]);}return this.elementStyles=this.finalizeStyles(this.styles),!0}static finalizeStyles(i){const s=[];if(Array.isArray(i)){const e=new Set(i.flat(1/0).reverse());for(const i of e)s.unshift(c$2(i));}else void 0!==i&&s.push(c$2(i));return s}static _$Ep(t,i){const s=i.attribute;return !1===s?void 0:"string"==typeof s?s:"string"==typeof t?t.toLowerCase():void 0}_$Eu(){var t;this._$E_=new Promise((t=>this.enableUpdating=t)),this._$AL=new Map,this._$Eg(),this.requestUpdate(),null===(t=this.constructor.h)||void 0===t||t.forEach((t=>t(this)));}addController(t){var i,s;(null!==(i=this._$ES)&&void 0!==i?i:this._$ES=[]).push(t),void 0!==this.renderRoot&&this.isConnected&&(null===(s=t.hostConnected)||void 0===s||s.call(t));}removeController(t){var i;null===(i=this._$ES)||void 0===i||i.splice(this._$ES.indexOf(t)>>>0,1);}_$Eg(){this.constructor.elementProperties.forEach(((t,i)=>{this.hasOwnProperty(i)&&(this._$Ei.set(i,this[i]),delete this[i]);}));}createRenderRoot(){var t;const s=null!==(t=this.shadowRoot)&&void 0!==t?t:this.attachShadow(this.constructor.shadowRootOptions);return S$2(s,this.constructor.elementStyles),s}connectedCallback(){var t;void 0===this.renderRoot&&(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),null===(t=this._$ES)||void 0===t||t.forEach((t=>{var i;return null===(i=t.hostConnected)||void 0===i?void 0:i.call(t)}));}enableUpdating(t){}disconnectedCallback(){var t;null===(t=this._$ES)||void 0===t||t.forEach((t=>{var i;return null===(i=t.hostDisconnected)||void 0===i?void 0:i.call(t)}));}attributeChangedCallback(t,i,s){this._$AK(t,s);}_$EO(t,i,s=l$4){var e;const r=this.constructor._$Ep(t,s);if(void 0!==r&&!0===s.reflect){const h=(void 0!==(null===(e=s.converter)||void 0===e?void 0:e.toAttribute)?s.converter:n$5).toAttribute(i,s.type);this._$El=t,null==h?this.removeAttribute(r):this.setAttribute(r,h),this._$El=null;}}_$AK(t,i){var s;const e=this.constructor,r=e._$Ev.get(t);if(void 0!==r&&this._$El!==r){const t=e.getPropertyOptions(r),h="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==(null===(s=t.converter)||void 0===s?void 0:s.fromAttribute)?t.converter:n$5;this._$El=r,this[r]=h.fromAttribute(i,t.type),this._$El=null;}}requestUpdate(t,i,s){let e=!0;void 0!==t&&(((s=s||this.constructor.getPropertyOptions(t)).hasChanged||a$2)(this[t],i)?(this._$AL.has(t)||this._$AL.set(t,i),!0===s.reflect&&this._$El!==t&&(void 0===this._$EC&&(this._$EC=new Map),this._$EC.set(t,s))):e=!1),!this.isUpdatePending&&e&&(this._$E_=this._$Ej());}async _$Ej(){this.isUpdatePending=!0;try{await this._$E_;}catch(t){Promise.reject(t);}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){var t;if(!this.isUpdatePending)return;this.hasUpdated,this._$Ei&&(this._$Ei.forEach(((t,i)=>this[i]=t)),this._$Ei=void 0);let i=!1;const s=this._$AL;try{i=this.shouldUpdate(s),i?(this.willUpdate(s),null===(t=this._$ES)||void 0===t||t.forEach((t=>{var i;return null===(i=t.hostUpdate)||void 0===i?void 0:i.call(t)})),this.update(s)):this._$Ek();}catch(t){throw i=!1,this._$Ek(),t}i&&this._$AE(s);}willUpdate(t){}_$AE(t){var i;null===(i=this._$ES)||void 0===i||i.forEach((t=>{var i;return null===(i=t.hostUpdated)||void 0===i?void 0:i.call(t)})),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t);}_$Ek(){this._$AL=new Map,this.isUpdatePending=!1;}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$E_}shouldUpdate(t){return !0}update(t){void 0!==this._$EC&&(this._$EC.forEach(((t,i)=>this._$EO(i,this[i],t))),this._$EC=void 0),this._$Ek();}updated(t){}firstUpdated(t){}};u$2[d$2]=!0,u$2.elementProperties=new Map,u$2.elementStyles=[],u$2.shadowRootOptions={mode:"open"},null==o$6||o$6({ReactiveElement:u$2}),(null!==(s$3=e$8.reactiveElementVersions)&&void 0!==s$3?s$3:e$8.reactiveElementVersions=[]).push("1.6.3");

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
var t$3;const i$3=window,s$2=i$3.trustedTypes,e$7=s$2?s$2.createPolicy("lit-html",{createHTML:t=>t}):void 0,o$5="$lit$",n$4=`lit$${(Math.random()+"").slice(9)}$`,l$3="?"+n$4,h$2=`<${l$3}>`,r$2=document,u$1=()=>r$2.createComment(""),d$1=t=>null===t||"object"!=typeof t&&"function"!=typeof t,c$1=Array.isArray,v$1=t=>c$1(t)||"function"==typeof(null==t?void 0:t[Symbol.iterator]),a$1="[ \t\n\f\r]",f$1=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,_$1=/-->/g,m$1=/>/g,p$1=RegExp(`>|${a$1}(?:([^\\s"'>=/]+)(${a$1}*=${a$1}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),g$1=/'/g,$$1=/"/g,y$1=/^(?:script|style|textarea|title)$/i,w$1=t=>(i,...s)=>({_$litType$:t,strings:i,values:s}),x$1=w$1(1),b$1=w$1(2),T$1=Symbol.for("lit-noChange"),A$1=Symbol.for("lit-nothing"),E$1=new WeakMap,C$1=r$2.createTreeWalker(r$2,129,null,!1);function P$1(t,i){if(!Array.isArray(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==e$7?e$7.createHTML(i):i}const V$1=(t,i)=>{const s=t.length-1,e=[];let l,r=2===i?"<svg>":"",u=f$1;for(let i=0;i<s;i++){const s=t[i];let d,c,v=-1,a=0;for(;a<s.length&&(u.lastIndex=a,c=u.exec(s),null!==c);)a=u.lastIndex,u===f$1?"!--"===c[1]?u=_$1:void 0!==c[1]?u=m$1:void 0!==c[2]?(y$1.test(c[2])&&(l=RegExp("</"+c[2],"g")),u=p$1):void 0!==c[3]&&(u=p$1):u===p$1?">"===c[0]?(u=null!=l?l:f$1,v=-1):void 0===c[1]?v=-2:(v=u.lastIndex-c[2].length,d=c[1],u=void 0===c[3]?p$1:'"'===c[3]?$$1:g$1):u===$$1||u===g$1?u=p$1:u===_$1||u===m$1?u=f$1:(u=p$1,l=void 0);const w=u===p$1&&t[i+1].startsWith("/>")?" ":"";r+=u===f$1?s+h$2:v>=0?(e.push(d),s.slice(0,v)+o$5+s.slice(v)+n$4+w):s+n$4+(-2===v?(e.push(void 0),i):w);}return [P$1(t,r+(t[s]||"<?>")+(2===i?"</svg>":"")),e]};let N$1 = class N{constructor({strings:t,_$litType$:i},e){let h;this.parts=[];let r=0,d=0;const c=t.length-1,v=this.parts,[a,f]=V$1(t,i);if(this.el=N.createElement(a,e),C$1.currentNode=this.el.content,2===i){const t=this.el.content,i=t.firstChild;i.remove(),t.append(...i.childNodes);}for(;null!==(h=C$1.nextNode())&&v.length<c;){if(1===h.nodeType){if(h.hasAttributes()){const t=[];for(const i of h.getAttributeNames())if(i.endsWith(o$5)||i.startsWith(n$4)){const s=f[d++];if(t.push(i),void 0!==s){const t=h.getAttribute(s.toLowerCase()+o$5).split(n$4),i=/([.?@])?(.*)/.exec(s);v.push({type:1,index:r,name:i[2],strings:t,ctor:"."===i[1]?H$1:"?"===i[1]?L$1:"@"===i[1]?z$1:k$1});}else v.push({type:6,index:r});}for(const i of t)h.removeAttribute(i);}if(y$1.test(h.tagName)){const t=h.textContent.split(n$4),i=t.length-1;if(i>0){h.textContent=s$2?s$2.emptyScript:"";for(let s=0;s<i;s++)h.append(t[s],u$1()),C$1.nextNode(),v.push({type:2,index:++r});h.append(t[i],u$1());}}}else if(8===h.nodeType)if(h.data===l$3)v.push({type:2,index:r});else {let t=-1;for(;-1!==(t=h.data.indexOf(n$4,t+1));)v.push({type:7,index:r}),t+=n$4.length-1;}r++;}}static createElement(t,i){const s=r$2.createElement("template");return s.innerHTML=t,s}};function S$1(t,i,s=t,e){var o,n,l,h;if(i===T$1)return i;let r=void 0!==e?null===(o=s._$Co)||void 0===o?void 0:o[e]:s._$Cl;const u=d$1(i)?void 0:i._$litDirective$;return (null==r?void 0:r.constructor)!==u&&(null===(n=null==r?void 0:r._$AO)||void 0===n||n.call(r,!1),void 0===u?r=void 0:(r=new u(t),r._$AT(t,s,e)),void 0!==e?(null!==(l=(h=s)._$Co)&&void 0!==l?l:h._$Co=[])[e]=r:s._$Cl=r),void 0!==r&&(i=S$1(t,r._$AS(t,i.values),r,e)),i}let M$1 = class M{constructor(t,i){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=i;}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){var i;const{el:{content:s},parts:e}=this._$AD,o=(null!==(i=null==t?void 0:t.creationScope)&&void 0!==i?i:r$2).importNode(s,!0);C$1.currentNode=o;let n=C$1.nextNode(),l=0,h=0,u=e[0];for(;void 0!==u;){if(l===u.index){let i;2===u.type?i=new R$1(n,n.nextSibling,this,t):1===u.type?i=new u.ctor(n,u.name,u.strings,this,t):6===u.type&&(i=new Z$1(n,this,t)),this._$AV.push(i),u=e[++h];}l!==(null==u?void 0:u.index)&&(n=C$1.nextNode(),l++);}return C$1.currentNode=r$2,o}v(t){let i=0;for(const s of this._$AV)void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,i),i+=s.strings.length-2):s._$AI(t[i])),i++;}};let R$1 = class R{constructor(t,i,s,e){var o;this.type=2,this._$AH=A$1,this._$AN=void 0,this._$AA=t,this._$AB=i,this._$AM=s,this.options=e,this._$Cp=null===(o=null==e?void 0:e.isConnected)||void 0===o||o;}get _$AU(){var t,i;return null!==(i=null===(t=this._$AM)||void 0===t?void 0:t._$AU)&&void 0!==i?i:this._$Cp}get parentNode(){let t=this._$AA.parentNode;const i=this._$AM;return void 0!==i&&11===(null==t?void 0:t.nodeType)&&(t=i.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,i=this){t=S$1(this,t,i),d$1(t)?t===A$1||null==t||""===t?(this._$AH!==A$1&&this._$AR(),this._$AH=A$1):t!==this._$AH&&t!==T$1&&this._(t):void 0!==t._$litType$?this.g(t):void 0!==t.nodeType?this.$(t):v$1(t)?this.T(t):this._(t);}k(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}$(t){this._$AH!==t&&(this._$AR(),this._$AH=this.k(t));}_(t){this._$AH!==A$1&&d$1(this._$AH)?this._$AA.nextSibling.data=t:this.$(r$2.createTextNode(t)),this._$AH=t;}g(t){var i;const{values:s,_$litType$:e}=t,o="number"==typeof e?this._$AC(t):(void 0===e.el&&(e.el=N$1.createElement(P$1(e.h,e.h[0]),this.options)),e);if((null===(i=this._$AH)||void 0===i?void 0:i._$AD)===o)this._$AH.v(s);else {const t=new M$1(o,this),i=t.u(this.options);t.v(s),this.$(i),this._$AH=t;}}_$AC(t){let i=E$1.get(t.strings);return void 0===i&&E$1.set(t.strings,i=new N$1(t)),i}T(t){c$1(this._$AH)||(this._$AH=[],this._$AR());const i=this._$AH;let s,e=0;for(const o of t)e===i.length?i.push(s=new R(this.k(u$1()),this.k(u$1()),this,this.options)):s=i[e],s._$AI(o),e++;e<i.length&&(this._$AR(s&&s._$AB.nextSibling,e),i.length=e);}_$AR(t=this._$AA.nextSibling,i){var s;for(null===(s=this._$AP)||void 0===s||s.call(this,!1,!0,i);t&&t!==this._$AB;){const i=t.nextSibling;t.remove(),t=i;}}setConnected(t){var i;void 0===this._$AM&&(this._$Cp=t,null===(i=this._$AP)||void 0===i||i.call(this,t));}};let k$1 = class k{constructor(t,i,s,e,o){this.type=1,this._$AH=A$1,this._$AN=void 0,this.element=t,this.name=i,this._$AM=e,this.options=o,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=A$1;}get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}_$AI(t,i=this,s,e){const o=this.strings;let n=!1;if(void 0===o)t=S$1(this,t,i,0),n=!d$1(t)||t!==this._$AH&&t!==T$1,n&&(this._$AH=t);else {const e=t;let l,h;for(t=o[0],l=0;l<o.length-1;l++)h=S$1(this,e[s+l],i,l),h===T$1&&(h=this._$AH[l]),n||(n=!d$1(h)||h!==this._$AH[l]),h===A$1?t=A$1:t!==A$1&&(t+=(null!=h?h:"")+o[l+1]),this._$AH[l]=h;}n&&!e&&this.j(t);}j(t){t===A$1?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,null!=t?t:"");}};let H$1 = class H extends k$1{constructor(){super(...arguments),this.type=3;}j(t){this.element[this.name]=t===A$1?void 0:t;}};const I$1=s$2?s$2.emptyScript:"";let L$1 = class L extends k$1{constructor(){super(...arguments),this.type=4;}j(t){t&&t!==A$1?this.element.setAttribute(this.name,I$1):this.element.removeAttribute(this.name);}};let z$1 = class z extends k$1{constructor(t,i,s,e,o){super(t,i,s,e,o),this.type=5;}_$AI(t,i=this){var s;if((t=null!==(s=S$1(this,t,i,0))&&void 0!==s?s:A$1)===T$1)return;const e=this._$AH,o=t===A$1&&e!==A$1||t.capture!==e.capture||t.once!==e.once||t.passive!==e.passive,n=t!==A$1&&(e===A$1||o);o&&this.element.removeEventListener(this.name,this,e),n&&this.element.addEventListener(this.name,this,t),this._$AH=t;}handleEvent(t){var i,s;"function"==typeof this._$AH?this._$AH.call(null!==(s=null===(i=this.options)||void 0===i?void 0:i.host)&&void 0!==s?s:this.element,t):this._$AH.handleEvent(t);}};let Z$1 = class Z{constructor(t,i,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=i,this.options=s;}get _$AU(){return this._$AM._$AU}_$AI(t){S$1(this,t);}};const j$1={O:o$5,P:n$4,A:l$3,C:1,M:V$1,L:M$1,R:v$1,D:S$1,I:R$1,V:k$1,H:L$1,N:z$1,U:H$1,F:Z$1},B$1=i$3.litHtmlPolyfillSupport;null==B$1||B$1(N$1,R$1),(null!==(t$3=i$3.litHtmlVersions)&&void 0!==t$3?t$3:i$3.litHtmlVersions=[]).push("2.8.0");const D$1=(t,i,s)=>{var e,o;const n=null!==(e=null==s?void 0:s.renderBefore)&&void 0!==e?e:i;let l=n._$litPart$;if(void 0===l){const t=null!==(o=null==s?void 0:s.renderBefore)&&void 0!==o?o:null;n._$litPart$=l=new R$1(i.insertBefore(u$1(),t),t,void 0,null!=s?s:{});}return l._$AI(t),l};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */var l$2,o$4;const r$1=u$2;let s$1 = class s extends u$2{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0;}createRenderRoot(){var t,e;const i=super.createRenderRoot();return null!==(t=(e=this.renderOptions).renderBefore)&&void 0!==t||(e.renderBefore=i.firstChild),i}update(t){const i=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=D$1(i,this.renderRoot,this.renderOptions);}connectedCallback(){var t;super.connectedCallback(),null===(t=this._$Do)||void 0===t||t.setConnected(!0);}disconnectedCallback(){var t;super.disconnectedCallback(),null===(t=this._$Do)||void 0===t||t.setConnected(!1);}render(){return T$1}};s$1.finalized=!0,s$1._$litElement$=!0,null===(l$2=globalThis.litElementHydrateSupport)||void 0===l$2||l$2.call(globalThis,{LitElement:s$1});const n$3=globalThis.litElementPolyfillSupport;null==n$3||n$3({LitElement:s$1});const h$1={_$AK:(t,e,i)=>{t._$AK(e,i);},_$AL:t=>t._$AL};(null!==(o$4=globalThis.litElementVersions)&&void 0!==o$4?o$4:globalThis.litElementVersions=[]).push("3.3.3");

/**
 * @license
 * Copyright 2022 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const o$3=!1;

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const e$6=e=>n=>"function"==typeof n?((e,n)=>(customElements.define(e,n),n))(e,n):((e,n)=>{const{kind:t,elements:s}=n;return {kind:t,elements:s,finisher(n){customElements.define(e,n);}}})(e,n);

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const i$2=(i,e)=>"method"===e.kind&&e.descriptor&&!("value"in e.descriptor)?{...e,finisher(n){n.createProperty(e.key,i);}}:{kind:"field",key:Symbol(),placement:"own",descriptor:{},originalKey:e.key,initializer(){"function"==typeof e.initializer&&(this[e.key]=e.initializer.call(this));},finisher(n){n.createProperty(e.key,i);}},e$5=(i,e,n)=>{e.constructor.createProperty(n,i);};function n$2(n){return (t,o)=>void 0!==o?e$5(n,t,o):i$2(n,t)}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function t$2(t){return n$2({...t,state:!0})}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const e$4=(e,t,o)=>{Object.defineProperty(t,o,e);},t$1=(e,t)=>({kind:"method",placement:"prototype",key:t.key,descriptor:e}),o$2=({finisher:e,descriptor:t})=>(o,n)=>{var r;if(void 0===n){const n=null!==(r=o.originalKey)&&void 0!==r?r:o.key,i=null!=t?{kind:"method",placement:"prototype",key:n,descriptor:t(o.key)}:{...o,key:n};return null!=e&&(i.finisher=function(t){e(t,n);}),i}{const r=o.constructor;void 0!==t&&Object.defineProperty(o,n,t(n)),null==e||e(r,n);}};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function e$3(e){return o$2({finisher:(r,t)=>{Object.assign(r.prototype[t],e);}})}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function i$1(i,n){return o$2({descriptor:o=>{const t={get(){var o,n;return null!==(n=null===(o=this.renderRoot)||void 0===o?void 0:o.querySelector(i))&&void 0!==n?n:null},enumerable:!0,configurable:!0};if(n){const n="symbol"==typeof o?Symbol():"__"+o;t.get=function(){var o,t;return void 0===this[n]&&(this[n]=null!==(t=null===(o=this.renderRoot)||void 0===o?void 0:o.querySelector(i))&&void 0!==t?t:null),this[n]};}return t}})}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function e$2(e){return o$2({descriptor:r=>({get(){var r,o;return null!==(o=null===(r=this.renderRoot)||void 0===r?void 0:r.querySelectorAll(e))&&void 0!==o?o:[]},enumerable:!0,configurable:!0})})}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function e$1(e){return o$2({descriptor:r=>({async get(){var r;return await this.updateComplete,null===(r=this.renderRoot)||void 0===r?void 0:r.querySelector(e)},enumerable:!0,configurable:!0})})}

/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */var n$1;const e=null!=(null===(n$1=window.HTMLSlotElement)||void 0===n$1?void 0:n$1.prototype.assignedElements)?(o,n)=>o.assignedElements(n):(o,n)=>o.assignedNodes(n).filter((o=>o.nodeType===Node.ELEMENT_NODE));function l$1(n){const{slot:l,selector:t}=null!=n?n:{};return o$2({descriptor:o=>({get(){var o;const r="slot"+(l?`[name=${l}]`:":not([name])"),i=null===(o=this.renderRoot)||void 0===o?void 0:o.querySelector(r),s=null!=i?e(i,n):[];return t?s.filter((o=>o.matches(t))):s},enumerable:!0,configurable:!0})})}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function o$1(o,n,r){let l,s=o;return "object"==typeof o?(s=o.slot,l=o):l={flatten:n},r?l$1({slot:s,flatten:n,selector:r}):o$2({descriptor:e=>({get(){var e,t;const o="slot"+(s?`[name=${s}]`:":not([name])"),n=null===(e=this.renderRoot)||void 0===e?void 0:e.querySelector(o);return null!==(t=null==n?void 0:n.assignedNodes(l))&&void 0!==t?t:[]},enumerable:!0,configurable:!0})})}

var __assign$1 = (window && window.__assign) || function () {
    __assign$1 = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign$1.apply(this, arguments);
};
var MS_PER_SECOND = 1e3;
var SECS_PER_MIN = 60;
var SECS_PER_HOUR = SECS_PER_MIN * 60;
var SECS_PER_DAY = SECS_PER_HOUR * 24;
var SECS_PER_WEEK = SECS_PER_DAY * 7;
function selectUnit(from, to, thresholds) {
    if (to === void 0) { to = Date.now(); }
    if (thresholds === void 0) { thresholds = {}; }
    var resolvedThresholds = __assign$1(__assign$1({}, DEFAULT_THRESHOLDS), (thresholds || {}));
    var secs = (+from - +to) / MS_PER_SECOND;
    if (Math.abs(secs) < resolvedThresholds.second) {
        return {
            value: Math.round(secs),
            unit: 'second',
        };
    }
    var mins = secs / SECS_PER_MIN;
    if (Math.abs(mins) < resolvedThresholds.minute) {
        return {
            value: Math.round(mins),
            unit: 'minute',
        };
    }
    var hours = secs / SECS_PER_HOUR;
    if (Math.abs(hours) < resolvedThresholds.hour) {
        return {
            value: Math.round(hours),
            unit: 'hour',
        };
    }
    var days = secs / SECS_PER_DAY;
    if (Math.abs(days) < resolvedThresholds.day) {
        return {
            value: Math.round(days),
            unit: 'day',
        };
    }
    var fromDate = new Date(from);
    var toDate = new Date(to);
    var years = fromDate.getFullYear() - toDate.getFullYear();
    if (Math.round(Math.abs(years)) > 0) {
        return {
            value: Math.round(years),
            unit: 'year',
        };
    }
    var months = years * 12 + fromDate.getMonth() - toDate.getMonth();
    if (Math.round(Math.abs(months)) > 0) {
        return {
            value: Math.round(months),
            unit: 'month',
        };
    }
    var weeks = secs / SECS_PER_WEEK;
    return {
        value: Math.round(weeks),
        unit: 'week',
    };
}
var DEFAULT_THRESHOLDS = {
    second: 45,
    minute: 45,
    hour: 22,
    day: 5,
};

function invariant(condition, message, Err) {
    if (Err === void 0) { Err = Error; }
    if (!condition) {
        throw new Err(message);
    }
}

// https://tc39.es/ecma402/#sec-issanctionedsimpleunitidentifier
var SANCTIONED_UNITS = [
    'angle-degree',
    'area-acre',
    'area-hectare',
    'concentr-percent',
    'digital-bit',
    'digital-byte',
    'digital-gigabit',
    'digital-gigabyte',
    'digital-kilobit',
    'digital-kilobyte',
    'digital-megabit',
    'digital-megabyte',
    'digital-petabyte',
    'digital-terabit',
    'digital-terabyte',
    'duration-day',
    'duration-hour',
    'duration-millisecond',
    'duration-minute',
    'duration-month',
    'duration-second',
    'duration-week',
    'duration-year',
    'length-centimeter',
    'length-foot',
    'length-inch',
    'length-kilometer',
    'length-meter',
    'length-mile-scandinavian',
    'length-mile',
    'length-millimeter',
    'length-yard',
    'mass-gram',
    'mass-kilogram',
    'mass-ounce',
    'mass-pound',
    'mass-stone',
    'temperature-celsius',
    'temperature-fahrenheit',
    'volume-fluid-ounce',
    'volume-gallon',
    'volume-liter',
    'volume-milliliter',
];
// In CLDR, the unit name always follows the form `namespace-unit` pattern.
// For example: `digital-bit` instead of `bit`. This function removes the namespace prefix.
function removeUnitNamespace(unit) {
    return unit.replace(/^(.*?)-/, '');
}

function hasOwnProperty(o, key) {
    return Object.prototype.hasOwnProperty.call(o, key);
}
/**
 * https://tc39.es/ecma262/#sec-toobject
 * @param arg
 */
function toObject(arg) {
    if (arg == null) {
        throw new TypeError('undefined/null cannot be converted to object');
    }
    return Object(arg);
}
/**
 * https://tc39.es/ecma262/#sec-tostring
 */
function toString(o) {
    // Only symbol is irregular...
    if (typeof o === 'symbol') {
        throw TypeError('Cannot convert a Symbol value to a string');
    }
    return String(o);
}
/**
 * https://tc39.es/ecma402/#sec-getoption
 * @param opts
 * @param prop
 * @param type
 * @param values
 * @param fallback
 */
function getOption(opts, prop, type, values, fallback) {
    // const descriptor = Object.getOwnPropertyDescriptor(opts, prop);
    var value = opts[prop];
    if (value !== undefined) {
        if (type !== 'boolean' && type !== 'string') {
            throw new TypeError('invalid type');
        }
        if (type === 'boolean') {
            value = Boolean(value);
        }
        if (type === 'string') {
            value = toString(value);
        }
        if (values !== undefined && !values.filter(function (val) { return val == value; }).length) {
            throw new RangeError(value + " is not within " + values.join(', '));
        }
        return value;
    }
    return fallback;
}
/**
 * https://tc39.es/ecma402/#sec-defaultnumberoption
 * @param val
 * @param min
 * @param max
 * @param fallback
 */
function defaultNumberOption(val, min, max, fallback) {
    if (val !== undefined) {
        val = Number(val);
        if (isNaN(val) || val < min || val > max) {
            throw new RangeError(val + " is outside of range [" + min + ", " + max + "]");
        }
        return Math.floor(val);
    }
    return fallback;
}
/**
 * https://tc39.es/ecma402/#sec-getnumberoption
 * @param options
 * @param property
 * @param min
 * @param max
 * @param fallback
 */
function getNumberOption(options, property, minimum, maximum, fallback) {
    var val = options[property];
    return defaultNumberOption(val, minimum, maximum, fallback);
}
function setInternalSlot(map, pl, field, value) {
    if (!map.get(pl)) {
        map.set(pl, Object.create(null));
    }
    var slots = map.get(pl);
    slots[field] = value;
}
function setMultiInternalSlots(map, pl, props) {
    for (var _i = 0, _a = Object.keys(props); _i < _a.length; _i++) {
        var k = _a[_i];
        setInternalSlot(map, pl, k, props[k]);
    }
}
function getInternalSlot(map, pl, field) {
    return getMultiInternalSlots(map, pl, field)[field];
}
function getMultiInternalSlots(map, pl) {
    var fields = [];
    for (var _i = 2; _i < arguments.length; _i++) {
        fields[_i - 2] = arguments[_i];
    }
    var slots = map.get(pl);
    if (!slots) {
        throw new TypeError(pl + " InternalSlot has not been initialized");
    }
    return fields.reduce(function (all, f) {
        all[f] = slots[f];
        return all;
    }, Object.create(null));
}
function isLiteralPart(patternPart) {
    return patternPart.type === 'literal';
}
function partitionPattern(pattern) {
    var result = [];
    var beginIndex = pattern.indexOf('{');
    var endIndex = 0;
    var nextIndex = 0;
    var length = pattern.length;
    while (beginIndex < pattern.length && beginIndex > -1) {
        endIndex = pattern.indexOf('}', beginIndex);
        invariant(endIndex > beginIndex, "Invalid pattern " + pattern);
        if (beginIndex > nextIndex) {
            result.push({
                type: 'literal',
                value: pattern.substring(nextIndex, beginIndex),
            });
        }
        result.push({
            type: pattern.substring(beginIndex + 1, endIndex),
            value: undefined,
        });
        nextIndex = endIndex + 1;
        beginIndex = pattern.indexOf('{', nextIndex);
    }
    if (nextIndex < length) {
        result.push({
            type: 'literal',
            value: pattern.substring(nextIndex, length),
        });
    }
    return result;
}
/**
 * https://tc39.es/ecma402/#sec-setnfdigitoptions
 */
function setNumberFormatDigitOptions(internalSlots, opts, mnfdDefault, mxfdDefault, notation) {
    var mnid = getNumberOption(opts, 'minimumIntegerDigits', 1, 21, 1);
    var mnfd = opts.minimumFractionDigits;
    var mxfd = opts.maximumFractionDigits;
    var mnsd = opts.minimumSignificantDigits;
    var mxsd = opts.maximumSignificantDigits;
    internalSlots.minimumIntegerDigits = mnid;
    if (mnsd !== undefined || mxsd !== undefined) {
        internalSlots.roundingType = 'significantDigits';
        mnsd = defaultNumberOption(mnsd, 1, 21, 1);
        mxsd = defaultNumberOption(mxsd, mnsd, 21, 21);
        internalSlots.minimumSignificantDigits = mnsd;
        internalSlots.maximumSignificantDigits = mxsd;
    }
    else if (mnfd !== undefined || mxfd !== undefined) {
        internalSlots.roundingType = 'fractionDigits';
        mnfd = defaultNumberOption(mnfd, 0, 20, mnfdDefault);
        var mxfdActualDefault = Math.max(mnfd, mxfdDefault);
        mxfd = defaultNumberOption(mxfd, mnfd, 20, mxfdActualDefault);
        internalSlots.minimumFractionDigits = mnfd;
        internalSlots.maximumFractionDigits = mxfd;
    }
    else if (notation === 'compact') {
        internalSlots.roundingType = 'compactRounding';
    }
    else {
        internalSlots.roundingType = 'fractionDigits';
        internalSlots.minimumFractionDigits = mnfdDefault;
        internalSlots.maximumFractionDigits = mxfdDefault;
    }
}
function objectIs(x, y) {
    if (Object.is) {
        return Object.is(x, y);
    }
    // SameValue algorithm
    if (x === y) {
        // Steps 1-5, 7-10
        // Steps 6.b-6.e: +0 != -0
        return x !== 0 || 1 / x === 1 / y;
    }
    // Step 6.a: NaN == NaN
    return x !== x && y !== y;
}
var NOT_A_Z_REGEX = /[^A-Z]/;
/**
 * This follows https://tc39.es/ecma402/#sec-case-sensitivity-and-case-mapping
 * @param str string to convert
 */
function toUpperCase(str) {
    return str.replace(/([a-z])/g, function (_, c) { return c.toUpperCase(); });
}
/**
 * https://tc39.es/ecma402/#sec-iswellformedcurrencycode
 */
function isWellFormedCurrencyCode(currency) {
    currency = toUpperCase(currency);
    if (currency.length !== 3) {
        return false;
    }
    if (NOT_A_Z_REGEX.test(currency)) {
        return false;
    }
    return true;
}
/**
 * https://tc39.es/ecma402/#sec-formatnumberstring
 * TODO: dedup with intl-pluralrules
 */
function formatNumericToString(internalSlots, x) {
    var isNegative = x < 0 || objectIs(x, -0);
    if (isNegative) {
        x = -x;
    }
    var result;
    var rourndingType = internalSlots.roundingType;
    switch (rourndingType) {
        case 'significantDigits':
            result = toRawPrecision(x, internalSlots.minimumSignificantDigits, internalSlots.maximumSignificantDigits);
            break;
        case 'fractionDigits':
            result = toRawFixed(x, internalSlots.minimumFractionDigits, internalSlots.maximumFractionDigits);
            break;
        default:
            result = toRawPrecision(x, 1, 2);
            if (result.integerDigitsCount > 1) {
                result = toRawFixed(x, 0, 0);
            }
            break;
    }
    x = result.roundedNumber;
    var string = result.formattedString;
    var int = result.integerDigitsCount;
    var minInteger = internalSlots.minimumIntegerDigits;
    if (int < minInteger) {
        var forwardZeros = repeat('0', minInteger - int);
        string = forwardZeros + string;
    }
    if (isNegative) {
        x = -x;
    }
    return { roundedNumber: x, formattedString: string };
}
/**
 * TODO: dedup with intl-pluralrules and support BigInt
 * https://tc39.es/ecma402/#sec-torawfixed
 * @param x a finite non-negative Number or BigInt
 * @param minFraction and integer between 0 and 20
 * @param maxFraction and integer between 0 and 20
 */
function toRawFixed(x, minFraction, maxFraction) {
    var f = maxFraction;
    var n = Math.round(x * Math.pow(10, f));
    var xFinal = n / Math.pow(10, f);
    // n is a positive integer, but it is possible to be greater than 1e21.
    // In such case we will go the slow path.
    // See also: https://tc39.es/ecma262/#sec-numeric-types-number-tostring
    var m;
    if (n < 1e21) {
        m = n.toString();
    }
    else {
        m = n.toString();
        var _a = m.split('e'), mantissa = _a[0], exponent = _a[1];
        m = mantissa.replace('.', '');
        m = m + repeat('0', Math.max(+exponent - m.length + 1, 0));
    }
    var int;
    if (f !== 0) {
        var k = m.length;
        if (k <= f) {
            var z = repeat('0', f + 1 - k);
            m = z + m;
            k = f + 1;
        }
        var a = m.slice(0, k - f);
        var b = m.slice(k - f);
        m = a + "." + b;
        int = a.length;
    }
    else {
        int = m.length;
    }
    var cut = maxFraction - minFraction;
    while (cut > 0 && m[m.length - 1] === '0') {
        m = m.slice(0, -1);
        cut--;
    }
    if (m[m.length - 1] === '.') {
        m = m.slice(0, -1);
    }
    return { formattedString: m, roundedNumber: xFinal, integerDigitsCount: int };
}
// https://tc39.es/ecma402/#sec-torawprecision
function toRawPrecision(x, minPrecision, maxPrecision) {
    var p = maxPrecision;
    var m;
    var e;
    var xFinal;
    if (x === 0) {
        m = repeat('0', p);
        e = 0;
        xFinal = 0;
    }
    else {
        var xToString = x.toString();
        // If xToString is formatted as scientific notation, the number is either very small or very
        // large. If the precision of the formatted string is lower that requested max precision, we
        // should still infer them from the formatted string, otherwise the formatted result might have
        // precision loss (e.g. 1e41 will not have 0 in every trailing digits).
        var xToStringExponentIndex = xToString.indexOf('e');
        var _a = xToString.split('e'), xToStringMantissa = _a[0], xToStringExponent = _a[1];
        var xToStringMantissaWithoutDecimalPoint = xToStringMantissa.replace('.', '');
        if (xToStringExponentIndex >= 0 &&
            xToStringMantissaWithoutDecimalPoint.length <= p) {
            e = +xToStringExponent;
            m =
                xToStringMantissaWithoutDecimalPoint +
                    repeat('0', p - xToStringMantissaWithoutDecimalPoint.length);
            xFinal = x;
        }
        else {
            e = getMagnitude(x);
            var decimalPlaceOffset = e - p + 1;
            // n is the integer containing the required precision digits. To derive the formatted string,
            // we will adjust its decimal place in the logic below.
            var n = Math.round(adjustDecimalPlace(x, decimalPlaceOffset));
            // The rounding caused the change of magnitude, so we should increment `e` by 1.
            if (adjustDecimalPlace(n, p - 1) >= 10) {
                e = e + 1;
                // Divide n by 10 to swallow one precision.
                n = Math.floor(n / 10);
            }
            m = n.toString();
            // Equivalent of n * 10 ** (e - p + 1)
            xFinal = adjustDecimalPlace(n, p - 1 - e);
        }
    }
    var int;
    if (e >= p - 1) {
        m = m + repeat('0', e - p + 1);
        int = e + 1;
    }
    else if (e >= 0) {
        m = m.slice(0, e + 1) + "." + m.slice(e + 1);
        int = e + 1;
    }
    else {
        m = "0." + repeat('0', -e - 1) + m;
        int = 1;
    }
    if (m.indexOf('.') >= 0 && maxPrecision > minPrecision) {
        var cut = maxPrecision - minPrecision;
        while (cut > 0 && m[m.length - 1] === '0') {
            m = m.slice(0, -1);
            cut--;
        }
        if (m[m.length - 1] === '.') {
            m = m.slice(0, -1);
        }
    }
    return { formattedString: m, roundedNumber: xFinal, integerDigitsCount: int };
    // x / (10 ** magnitude), but try to preserve as much floating point precision as possible.
    function adjustDecimalPlace(x, magnitude) {
        return magnitude < 0 ? x * Math.pow(10, -magnitude) : x / Math.pow(10, magnitude);
    }
}
function repeat(s, times) {
    if (typeof s.repeat === 'function') {
        return s.repeat(times);
    }
    var arr = new Array(times);
    for (var i = 0; i < arr.length; i++) {
        arr[i] = s;
    }
    return arr.join('');
}
/**
 * Cannot do Math.log(x) / Math.log(10) bc if IEEE floating point issue
 * @param x number
 */
function getMagnitude(x) {
    // Cannot count string length via Number.toString because it may use scientific notation
    // for very small or very large numbers.
    return Math.floor(Math.log(x) * Math.LOG10E);
}
/**
 * This follows https://tc39.es/ecma402/#sec-case-sensitivity-and-case-mapping
 * @param str string to convert
 */
function toLowerCase(str) {
    return str.replace(/([A-Z])/g, function (_, c) { return c.toLowerCase(); });
}
var SHORTENED_SACTION_UNITS = SANCTIONED_UNITS.map(function (unit) {
    return unit.replace(/^(.*?)-/, '');
});
/**
 * https://tc39.es/ecma402/#sec-iswellformedunitidentifier
 * @param unit
 */
function isWellFormedUnitIdentifier(unit) {
    unit = toLowerCase(unit);
    if (SHORTENED_SACTION_UNITS.indexOf(unit) > -1) {
        return true;
    }
    var units = unit.split('-per-');
    if (units.length !== 2) {
        return false;
    }
    if (SHORTENED_SACTION_UNITS.indexOf(units[0]) < 0 ||
        SHORTENED_SACTION_UNITS.indexOf(units[1]) < 0) {
        return false;
    }
    return true;
}
/*
  17 ECMAScript Standard Built-in Objects:
    Every built-in Function object, including constructors, that is not
    identified as an anonymous function has a name property whose value
    is a String.

    Unless otherwise specified, the name property of a built-in Function
    object, if it exists, has the attributes { [[Writable]]: false,
    [[Enumerable]]: false, [[Configurable]]: true }.
*/
function defineProperty(target, name, _a) {
    var value = _a.value;
    Object.defineProperty(target, name, {
        configurable: true,
        enumerable: false,
        writable: true,
        value: value,
    });
}

var __extends = (window && window.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
var __assign = (window && window.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
function createResolveLocale(getDefaultLocale) {
    var lookupMatcher = createLookupMatcher(getDefaultLocale);
    var bestFitMatcher = createBestFitMatcher(getDefaultLocale);
    /**
     * https://tc39.es/ecma402/#sec-resolvelocale
     */
    return function resolveLocale(availableLocales, requestedLocales, options, relevantExtensionKeys, localeData) {
        var matcher = options.localeMatcher;
        var r;
        if (matcher === 'lookup') {
            r = lookupMatcher(availableLocales, requestedLocales);
        }
        else {
            r = bestFitMatcher(availableLocales, requestedLocales);
        }
        var foundLocale = r.locale;
        var result = { locale: '', dataLocale: foundLocale };
        var supportedExtension = '-u';
        for (var _i = 0, relevantExtensionKeys_1 = relevantExtensionKeys; _i < relevantExtensionKeys_1.length; _i++) {
            var key = relevantExtensionKeys_1[_i];
            var foundLocaleData = localeData[foundLocale];
            invariant(typeof foundLocaleData === 'object' && foundLocaleData !== null, "locale data " + key + " must be an object");
            var keyLocaleData = foundLocaleData[key];
            invariant(Array.isArray(keyLocaleData), "keyLocaleData for " + key + " must be an array");
            var value = keyLocaleData[0];
            invariant(typeof value === 'string' || value === null, "value must be string or null but got " + typeof value + " in key " + key);
            var supportedExtensionAddition = '';
            if (r.extension) {
                var requestedValue = unicodeExtensionValue(r.extension, key);
                if (requestedValue !== undefined) {
                    if (requestedValue !== '') {
                        if (~keyLocaleData.indexOf(requestedValue)) {
                            value = requestedValue;
                            supportedExtensionAddition = "-" + key + "-" + value;
                        }
                    }
                    else if (~requestedValue.indexOf('true')) {
                        value = 'true';
                        supportedExtensionAddition = "-" + key;
                    }
                }
            }
            if (key in options) {
                var optionsValue = options[key];
                invariant(typeof optionsValue === 'string' ||
                    typeof optionsValue === 'undefined' ||
                    optionsValue === null, 'optionsValue must be String, Undefined or Null');
                if (~keyLocaleData.indexOf(optionsValue)) {
                    if (optionsValue !== value) {
                        value = optionsValue;
                        supportedExtensionAddition = '';
                    }
                }
            }
            result[key] = value;
            supportedExtension += supportedExtensionAddition;
        }
        if (supportedExtension.length > 2) {
            var privateIndex = foundLocale.indexOf('-x-');
            if (privateIndex === -1) {
                foundLocale = foundLocale + supportedExtension;
            }
            else {
                var preExtension = foundLocale.slice(0, privateIndex);
                var postExtension = foundLocale.slice(privateIndex, foundLocale.length);
                foundLocale = preExtension + supportedExtension + postExtension;
            }
            foundLocale = Intl.getCanonicalLocales(foundLocale)[0];
        }
        result.locale = foundLocale;
        return result;
    };
}
/**
 * https://tc39.es/ecma402/#sec-unicodeextensionvalue
 * @param extension
 * @param key
 */
function unicodeExtensionValue(extension, key) {
    invariant(key.length === 2, 'key must have 2 elements');
    var size = extension.length;
    var searchValue = "-" + key + "-";
    var pos = extension.indexOf(searchValue);
    if (pos !== -1) {
        var start = pos + 4;
        var end = start;
        var k = start;
        var done = false;
        while (!done) {
            var e = extension.indexOf('-', k);
            var len = void 0;
            if (e === -1) {
                len = size - k;
            }
            else {
                len = e - k;
            }
            if (len === 2) {
                done = true;
            }
            else if (e === -1) {
                end = size;
                done = true;
            }
            else {
                end = e;
                k = e + 1;
            }
        }
        return extension.slice(start, end);
    }
    searchValue = "-" + key;
    pos = extension.indexOf(searchValue);
    if (pos !== -1 && pos + 3 === size) {
        return '';
    }
    return undefined;
}
var UNICODE_EXTENSION_SEQUENCE_REGEX = /-u(?:-[0-9a-z]{2,8})+/gi;
/**
 * https://tc39.es/ecma402/#sec-bestavailablelocale
 * @param availableLocales
 * @param locale
 */
function bestAvailableLocale(availableLocales, locale) {
    var candidate = locale;
    while (true) {
        if (~availableLocales.indexOf(candidate)) {
            return candidate;
        }
        var pos = candidate.lastIndexOf('-');
        if (!~pos) {
            return undefined;
        }
        if (pos >= 2 && candidate[pos - 2] === '-') {
            pos -= 2;
        }
        candidate = candidate.slice(0, pos);
    }
}
function createLookupMatcher(getDefaultLocale) {
    /**
     * https://tc39.es/ecma402/#sec-lookupmatcher
     */
    return function lookupMatcher(availableLocales, requestedLocales) {
        var result = { locale: '' };
        for (var _i = 0, requestedLocales_1 = requestedLocales; _i < requestedLocales_1.length; _i++) {
            var locale = requestedLocales_1[_i];
            var noExtensionLocale = locale.replace(UNICODE_EXTENSION_SEQUENCE_REGEX, '');
            var availableLocale = bestAvailableLocale(availableLocales, noExtensionLocale);
            if (availableLocale) {
                result.locale = availableLocale;
                if (locale !== noExtensionLocale) {
                    result.extension = locale.slice(noExtensionLocale.length + 1, locale.length);
                }
                return result;
            }
        }
        result.locale = getDefaultLocale();
        return result;
    };
}
function createBestFitMatcher(getDefaultLocale) {
    return function bestFitMatcher(availableLocales, requestedLocales) {
        var result = { locale: '' };
        for (var _i = 0, requestedLocales_2 = requestedLocales; _i < requestedLocales_2.length; _i++) {
            var locale = requestedLocales_2[_i];
            var noExtensionLocale = locale.replace(UNICODE_EXTENSION_SEQUENCE_REGEX, '');
            var availableLocale = bestAvailableLocale(availableLocales, noExtensionLocale);
            if (availableLocale) {
                result.locale = availableLocale;
                if (locale !== noExtensionLocale) {
                    result.extension = locale.slice(noExtensionLocale.length + 1, locale.length);
                }
                return result;
            }
        }
        result.locale = getDefaultLocale();
        return result;
    };
}
function getLocaleHierarchy(locale) {
    var results = [locale];
    var localeParts = locale.split('-');
    for (var i = localeParts.length; i > 1; i--) {
        results.push(localeParts.slice(0, i - 1).join('-'));
    }
    return results;
}
function lookupSupportedLocales(availableLocales, requestedLocales) {
    var subset = [];
    for (var _i = 0, requestedLocales_3 = requestedLocales; _i < requestedLocales_3.length; _i++) {
        var locale = requestedLocales_3[_i];
        var noExtensionLocale = locale.replace(UNICODE_EXTENSION_SEQUENCE_REGEX, '');
        var availableLocale = bestAvailableLocale(availableLocales, noExtensionLocale);
        if (availableLocale) {
            subset.push(availableLocale);
        }
    }
    return subset;
}
function supportedLocales(availableLocales, requestedLocales, options) {
    var matcher = 'best fit';
    if (options !== undefined) {
        options = toObject(options);
        matcher = getOption(options, 'localeMatcher', 'string', ['lookup', 'best fit'], 'best fit');
    }
    if (matcher === 'best fit') {
        return lookupSupportedLocales(availableLocales, requestedLocales);
    }
    return lookupSupportedLocales(availableLocales, requestedLocales);
}
var MissingLocaleDataError = /** @class */ (function (_super) {
    __extends(MissingLocaleDataError, _super);
    function MissingLocaleDataError() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.type = 'MISSING_LOCALE_DATA';
        return _this;
    }
    return MissingLocaleDataError;
}(Error));
function isMissingLocaleDataError(e) {
    return e.type === 'MISSING_LOCALE_DATA';
}
function unpackData(locale, localeData, 
/** By default shallow merge the dictionaries. */
reducer) {
    if (reducer === void 0) { reducer = function (all, d) { return (__assign(__assign({}, all), d)); }; }
    var localeHierarchy = getLocaleHierarchy(locale);
    var dataToMerge = localeHierarchy
        .map(function (l) { return localeData.data[l]; })
        .filter(Boolean);
    if (!dataToMerge.length) {
        throw new MissingLocaleDataError("Missing locale data for \"" + locale + "\", lookup hierarchy: " + localeHierarchy.join(', '));
    }
    dataToMerge.reverse();
    return dataToMerge.reduce(reducer, {});
}

var t,r,n=function(e,t){return i(t).format(e)},i=function(e){return new Intl.DateTimeFormat(e.language,{weekday:"long",month:"long",day:"numeric"})},a=function(e,t){return o(t).format(e)},o=function(e){return new Intl.DateTimeFormat(e.language,{year:"numeric",month:"long",day:"numeric"})},u=function(e,t){return c(t).format(e)},c=function(e){return new Intl.DateTimeFormat(e.language,{year:"numeric",month:"numeric",day:"numeric"})},m=function(e,t){return s(t).format(e)},s=function(e){return new Intl.DateTimeFormat(e.language,{day:"numeric",month:"short"})},l=function(e,t){return d(t).format(e)},d=function(e){return new Intl.DateTimeFormat(e.language,{month:"long",year:"numeric"})},f=function(e,t){return g(t).format(e)},g=function(e){return new Intl.DateTimeFormat(e.language,{month:"long"})},p=function(e,t){return h(t).format(e)},h=function(e){return new Intl.DateTimeFormat(e.language,{year:"numeric"})};!function(e){e.language="language",e.system="system",e.comma_decimal="comma_decimal",e.decimal_comma="decimal_comma",e.space_comma="space_comma",e.none="none";}(t||(t={})),function(e){e.language="language",e.system="system",e.am_pm="12",e.twenty_four="24";}(r||(r={}));var b=function(e){if(e.time_format===r.language||e.time_format===r.system){var t=e.time_format===r.language?e.language:void 0,n=(new Date).toLocaleString(t);return n.includes("AM")||n.includes("PM")}return e.time_format===r.am_pm},v=function(e,t){return _(t).format(e)},_=function(e){return new Intl.DateTimeFormat(e.language,{year:"numeric",month:"long",day:"numeric",hour:b(e)?"numeric":"2-digit",minute:"2-digit",hour12:b(e)})},y=function(e,t){return w(t).format(e)},w=function(e){return new Intl.DateTimeFormat(e.language,{year:"numeric",month:"long",day:"numeric",hour:b(e)?"numeric":"2-digit",minute:"2-digit",second:"2-digit",hour12:b(e)})},k=function(e,t){return x(t).format(e)},x=function(e){return new Intl.DateTimeFormat(e.language,{year:"numeric",month:"numeric",day:"numeric",hour:"numeric",minute:"2-digit",hour12:b(e)})},D=function(e,t){return S(t).format(e)},S=function(e){return new Intl.DateTimeFormat(e.language,{hour:"numeric",minute:"2-digit",hour12:b(e)})},F=function(e,t){return T(t).format(e)},T=function(e){return new Intl.DateTimeFormat(e.language,{hour:b(e)?"numeric":"2-digit",minute:"2-digit",second:"2-digit",hour12:b(e)})},I=function(e,t){return N(t).format(e)},N=function(e){return new Intl.DateTimeFormat(e.language,{hour:b(e)?"numeric":"2-digit",minute:"2-digit",second:"2-digit",hour12:b(e)})},M=function(t,r,n,i){void 0===i&&(i=!0);var a=selectUnit(t,n);return i?function(e){return new Intl.RelativeTimeFormat(e.language,{numeric:"auto"})}(r).format(a.value,a.unit):Intl.NumberFormat(r.language,{style:"unit",unit:a.unit,unitDisplay:"long"}).format(Math.abs(a.value))};function C(e){var t,r=3600*(t=e.attributes.remaining.split(":").map(Number))[0]+60*t[1]+t[2];if("active"===e.state){var n=(new Date).getTime(),i=new Date(e.last_changed).getTime();r=Math.max(r-(n-i)/1e3,0);}return r}function O(){return (O=Object.assign||function(e){for(var t=1;t<arguments.length;t++){var r=arguments[t];for(var n in r)Object.prototype.hasOwnProperty.call(r,n)&&(e[n]=r[n]);}return e}).apply(this,arguments)}var q=function(e,t,r,n){void 0===n&&(n=!1),e._themes||(e._themes={});var i=t.default_theme;("default"===r||r&&t.themes[r])&&(i=r);var a=O({},e._themes);if("default"!==i){var o=t.themes[i];Object.keys(o).forEach(function(t){var r="--"+t;e._themes[r]="",a[r]=o[t];});}if(e.updateStyles?e.updateStyles(a):window.ShadyCSS&&window.ShadyCSS.styleSubtree(e,a),n){var u=document.querySelector("meta[name=theme-color]");if(u){u.hasAttribute("default-content")||u.setAttribute("default-content",u.getAttribute("content"));var c=a["--primary-color"]||u.getAttribute("default-content");u.setAttribute("content",c);}}},A=function(e){return "function"==typeof e.getCardSize?e.getCardSize():4};function E(e){return e.substr(0,e.indexOf("."))}function j(e){return e.substr(e.indexOf(".")+1)}function R(e){var t,r=(null==e||null==(t=e.locale)?void 0:t.language)||"en";return e.translationMetadata.translations[r]&&e.translationMetadata.translations[r].isRTL||!1}function z(e){return R(e)?"rtl":"ltr"}function L(e){return E(e.entity_id)}var P=function(e){return !!e.attributes.unit_of_measurement||!!e.attributes.state_class},U=function(e){switch(e.number_format){case t.comma_decimal:return ["en-US","en"];case t.decimal_comma:return ["de","es","it"];case t.space_comma:return ["fr","sv","cs"];case t.system:return;default:return e.language}},B=function(e,t){return void 0===t&&(t=2),Math.round(e*Math.pow(10,t))/Math.pow(10,t)},H=function(e,r,n){var i=r?U(r):void 0;if(Number.isNaN=Number.isNaN||function e(t){return "number"==typeof t&&e(t)},(null==r?void 0:r.number_format)!==t.none&&!Number.isNaN(Number(e))&&Intl)try{return new Intl.NumberFormat(i,V(e,n)).format(Number(e))}catch(t){return console.error(t),new Intl.NumberFormat(void 0,V(e,n)).format(Number(e))}return "string"==typeof e?e:B(e,null==n?void 0:n.maximumFractionDigits).toString()+("currency"===(null==n?void 0:n.style)?" "+n.currency:"")},V=function(e,t){var r=O({maximumFractionDigits:2},t);if("string"!=typeof e)return r;if(!t||!t.minimumFractionDigits&&!t.maximumFractionDigits){var n=e.indexOf(".")>-1?e.split(".")[1].length:0;r.minimumFractionDigits=n,r.maximumFractionDigits=n;}return r},W=function(e,t,r,n){var i=void 0!==n?n:t.state;if("unknown"===i||"unavailable"===i)return e("state.default."+i);if(P(t)){if("monetary"===t.attributes.device_class)try{return H(i,r,{style:"currency",currency:t.attributes.unit_of_measurement})}catch(e){}return H(i,r)+(t.attributes.unit_of_measurement?" "+t.attributes.unit_of_measurement:"")}var o=L(t);if("input_datetime"===o){var u;if(void 0===n)return t.attributes.has_date&&t.attributes.has_time?(u=new Date(t.attributes.year,t.attributes.month-1,t.attributes.day,t.attributes.hour,t.attributes.minute),v(u,r)):t.attributes.has_date?(u=new Date(t.attributes.year,t.attributes.month-1,t.attributes.day),a(u,r)):t.attributes.has_time?((u=new Date).setHours(t.attributes.hour,t.attributes.minute),D(u,r)):t.state;try{var c=n.split(" ");if(2===c.length)return v(new Date(c.join("T")),r);if(1===c.length){if(n.includes("-"))return a(new Date(n+"T00:00"),r);if(n.includes(":")){var m=new Date;return D(new Date(m.toISOString().split("T")[0]+"T"+n),r)}}return n}catch(e){return n}}return "humidifier"===o&&"on"===i&&t.attributes.humidity?t.attributes.humidity+" %":"counter"===o||"number"===o||"input_number"===o?H(i,r):t.attributes.device_class&&e("component."+o+".state."+t.attributes.device_class+"."+i)||e("component."+o+".state._."+i)||i},G="mdi:bookmark",J="lovelace",K=["climate","cover","configurator","input_select","input_number","input_text","lock","media_player","scene","script","timer","vacuum","water_heater","weblink"],Q=["alarm_control_panel","automation","camera","climate","configurator","cover","fan","group","history_graph","input_datetime","light","lock","media_player","script","sun","updater","vacuum","water_heater","weather"],X=["input_number","input_select","input_text","scene","weblink"],Y=["camera","configurator","history_graph","scene"],Z=["closed","locked","off"],$=new Set(["fan","input_boolean","light","switch","group","automation"]),ee="°C",te="°F",re="group.default_view",ne=function(e,t,r,n){n=n||{},r=null==r?{}:r;var i=new Event(t,{bubbles:void 0===n.bubbles||n.bubbles,cancelable:Boolean(n.cancelable),composed:void 0===n.composed||n.composed});return i.detail=r,e.dispatchEvent(i),i},ie=new Set(["call-service","divider","section","weblink","cast","select"]),ae={alert:"toggle",automation:"toggle",climate:"climate",cover:"cover",fan:"toggle",group:"group",input_boolean:"toggle",input_number:"input-number",input_select:"input-select",input_text:"input-text",light:"toggle",lock:"lock",media_player:"media-player",remote:"toggle",scene:"scene",script:"script",sensor:"sensor",timer:"timer",switch:"toggle",vacuum:"toggle",water_heater:"climate",input_datetime:"input-datetime"},oe=function(e,t){void 0===t&&(t=!1);var r=function(e,t){return n("hui-error-card",{type:"error",error:e,config:t})},n=function(e,t){var n=window.document.createElement(e);try{if(!n.setConfig)return;n.setConfig(t);}catch(n){return console.error(e,n),r(n.message,t)}return n};if(!e||"object"!=typeof e||!t&&!e.type)return r("No type defined",e);var i=e.type;if(i&&i.startsWith("custom:"))i=i.substr("custom:".length);else if(t)if(ie.has(i))i="hui-"+i+"-row";else {if(!e.entity)return r("Invalid config given.",e);var a=e.entity.split(".",1)[0];i="hui-"+(ae[a]||"text")+"-entity-row";}else i="hui-"+i+"-card";if(customElements.get(i))return n(i,e);var o=r("Custom element doesn't exist: "+e.type+".",e);o.style.display="None";var u=setTimeout(function(){o.style.display="";},2e3);return customElements.whenDefined(e.type).then(function(){clearTimeout(u),ne(o,"ll-rebuild",{},o);}),o},ue=function(e,t,r){var n;return void 0===r&&(r=!1),function(){var i=[].slice.call(arguments),a=this,o=function(){n=null,r||e.apply(a,i);},u=r&&!n;clearTimeout(n),n=setTimeout(o,t),u&&e.apply(a,i);}},ce={alert:"mdi:alert",automation:"mdi:playlist-play",calendar:"mdi:calendar",camera:"mdi:video",climate:"mdi:thermostat",configurator:"mdi:settings",conversation:"mdi:text-to-speech",device_tracker:"mdi:account",fan:"mdi:fan",group:"mdi:google-circles-communities",history_graph:"mdi:chart-line",homeassistant:"mdi:home-assistant",homekit:"mdi:home-automation",image_processing:"mdi:image-filter-frames",input_boolean:"mdi:drawing",input_datetime:"mdi:calendar-clock",input_number:"mdi:ray-vertex",input_select:"mdi:format-list-bulleted",input_text:"mdi:textbox",light:"mdi:lightbulb",mailbox:"mdi:mailbox",notify:"mdi:comment-alert",person:"mdi:account",plant:"mdi:flower",proximity:"mdi:apple-safari",remote:"mdi:remote",scene:"mdi:google-pages",script:"mdi:file-document",sensor:"mdi:eye",simple_alarm:"mdi:bell",sun:"mdi:white-balance-sunny",switch:"mdi:flash",timer:"mdi:timer",updater:"mdi:cloud-upload",vacuum:"mdi:robot-vacuum",water_heater:"mdi:thermometer",weblink:"mdi:open-in-new"};function me(e,t){if(e in ce)return ce[e];switch(e){case "alarm_control_panel":switch(t){case "armed_home":return "mdi:bell-plus";case "armed_night":return "mdi:bell-sleep";case "disarmed":return "mdi:bell-outline";case "triggered":return "mdi:bell-ring";default:return "mdi:bell"}case "binary_sensor":return t&&"off"===t?"mdi:radiobox-blank":"mdi:checkbox-marked-circle";case "cover":return "closed"===t?"mdi:window-closed":"mdi:window-open";case "lock":return t&&"unlocked"===t?"mdi:lock-open":"mdi:lock";case "media_player":return t&&"off"!==t&&"idle"!==t?"mdi:cast-connected":"mdi:cast";case "zwave":switch(t){case "dead":return "mdi:emoticon-dead";case "sleeping":return "mdi:sleep";case "initializing":return "mdi:timer-sand";default:return "mdi:z-wave"}default:return console.warn("Unable to find icon for domain "+e+" ("+t+")"),"mdi:bookmark"}}var se=function(e,t){var r=t.value||t,n=t.attribute?e.attributes[t.attribute]:e.state;switch(t.operator||"=="){case "==":return n===r;case "<=":return n<=r;case "<":return n<r;case ">=":return n>=r;case ">":return n>r;case "!=":return n!==r;case "regex":return n.match(r);default:return !1}},le=function(e){ne(window,"haptic",e);},de=function(e,t,r){void 0===r&&(r=!1),r?history.replaceState(null,"",t):history.pushState(null,"",t),ne(window,"location-changed",{replace:r});},fe=function(e,t,r){void 0===r&&(r=!0);var n,i=E(t),a="group"===i?"homeassistant":i;switch(i){case "lock":n=r?"unlock":"lock";break;case "cover":n=r?"open_cover":"close_cover";break;default:n=r?"turn_on":"turn_off";}return e.callService(a,n,{entity_id:t})},ge=function(e,t){var r=Z.includes(e.states[t].state);return fe(e,t,r)},pe=function(e,t,r,n){if(n||(n={action:"more-info"}),!n.confirmation||n.confirmation.exemptions&&n.confirmation.exemptions.some(function(e){return e.user===t.user.id})||(le("warning"),confirm(n.confirmation.text||"Are you sure you want to "+n.action+"?")))switch(n.action){case "more-info":(r.entity||r.camera_image)&&ne(e,"hass-more-info",{entityId:r.entity?r.entity:r.camera_image});break;case "navigate":n.navigation_path&&de(0,n.navigation_path);break;case "url":n.url_path&&window.open(n.url_path);break;case "toggle":r.entity&&(ge(t,r.entity),le("success"));break;case "call-service":if(!n.service)return void le("failure");var i=n.service.split(".",2);t.callService(i[0],i[1],n.service_data,n.target),le("success");break;case "fire-dom-event":ne(e,"ll-custom",n);}},he=function(e,t,r,n){var i;"double_tap"===n&&r.double_tap_action?i=r.double_tap_action:"hold"===n&&r.hold_action?i=r.hold_action:"tap"===n&&r.tap_action&&(i=r.tap_action),pe(e,t,r,i);},be=function(e,t,r,n,i){var a;if(i&&r.double_tap_action?a=r.double_tap_action:n&&r.hold_action?a=r.hold_action:!n&&r.tap_action&&(a=r.tap_action),a||(a={action:"more-info"}),!a.confirmation||a.confirmation.exemptions&&a.confirmation.exemptions.some(function(e){return e.user===t.user.id})||confirm(a.confirmation.text||"Are you sure you want to "+a.action+"?"))switch(a.action){case "more-info":(a.entity||r.entity||r.camera_image)&&(ne(e,"hass-more-info",{entityId:a.entity?a.entity:r.entity?r.entity:r.camera_image}),a.haptic&&le(a.haptic));break;case "navigate":a.navigation_path&&(de(0,a.navigation_path),a.haptic&&le(a.haptic));break;case "url":a.url_path&&window.open(a.url_path),a.haptic&&le(a.haptic);break;case "toggle":r.entity&&(ge(t,r.entity),a.haptic&&le(a.haptic));break;case "call-service":if(!a.service)return;var o=a.service.split(".",2),u=o[0],c=o[1],m=O({},a.service_data);"entity"===m.entity_id&&(m.entity_id=r.entity),t.callService(u,c,m,a.target),a.haptic&&le(a.haptic);break;case "fire-dom-event":ne(e,"ll-custom",a),a.haptic&&le(a.haptic);}};function ve(e){return void 0!==e&&"none"!==e.action}function _e(e,t,r){if(t.has("config")||r)return !0;if(e.config.entity){var n=t.get("hass");return !n||n.states[e.config.entity]!==e.hass.states[e.config.entity]}return !1}function ye(e){return void 0!==e&&"none"!==e.action}var we=function(e,t,r){void 0===r&&(r=!0);var n={};t.forEach(function(t){if(Z.includes(e.states[t].state)===r){var i=E(t),a=["cover","lock"].includes(i)?i:"homeassistant";a in n||(n[a]=[]),n[a].push(t);}}),Object.keys(n).forEach(function(t){var i;switch(t){case "lock":i=r?"unlock":"lock";break;case "cover":i=r?"open_cover":"close_cover";break;default:i=r?"turn_on":"turn_off";}e.callService(t,i,{entity_id:n[t]});});},ke=function(){var e=document.querySelector("home-assistant");if(e=(e=(e=(e=(e=(e=(e=(e=e&&e.shadowRoot)&&e.querySelector("home-assistant-main"))&&e.shadowRoot)&&e.querySelector("app-drawer-layout partial-panel-resolver"))&&e.shadowRoot||e)&&e.querySelector("ha-panel-lovelace"))&&e.shadowRoot)&&e.querySelector("hui-root")){var t=e.lovelace;return t.current_view=e.___curView,t}return null},xe={humidity:"mdi:water-percent",illuminance:"mdi:brightness-5",temperature:"mdi:thermometer",pressure:"mdi:gauge",power:"mdi:flash",signal_strength:"mdi:wifi"},De={binary_sensor:function(e,t){var r="off"===e;switch(null==t?void 0:t.attributes.device_class){case "battery":return r?"mdi:battery":"mdi:battery-outline";case "battery_charging":return r?"mdi:battery":"mdi:battery-charging";case "cold":return r?"mdi:thermometer":"mdi:snowflake";case "connectivity":return r?"mdi:server-network-off":"mdi:server-network";case "door":return r?"mdi:door-closed":"mdi:door-open";case "garage_door":return r?"mdi:garage":"mdi:garage-open";case "power":return r?"mdi:power-plug-off":"mdi:power-plug";case "gas":case "problem":case "safety":case "tamper":return r?"mdi:check-circle":"mdi:alert-circle";case "smoke":return r?"mdi:check-circle":"mdi:smoke";case "heat":return r?"mdi:thermometer":"mdi:fire";case "light":return r?"mdi:brightness-5":"mdi:brightness-7";case "lock":return r?"mdi:lock":"mdi:lock-open";case "moisture":return r?"mdi:water-off":"mdi:water";case "motion":return r?"mdi:walk":"mdi:run";case "occupancy":return r?"mdi:home-outline":"mdi:home";case "opening":return r?"mdi:square":"mdi:square-outline";case "plug":return r?"mdi:power-plug-off":"mdi:power-plug";case "presence":return r?"mdi:home-outline":"mdi:home";case "running":return r?"mdi:stop":"mdi:play";case "sound":return r?"mdi:music-note-off":"mdi:music-note";case "update":return r?"mdi:package":"mdi:package-up";case "vibration":return r?"mdi:crop-portrait":"mdi:vibrate";case "window":return r?"mdi:window-closed":"mdi:window-open";default:return r?"mdi:radiobox-blank":"mdi:checkbox-marked-circle"}},cover:function(e){var t="closed"!==e.state;switch(e.attributes.device_class){case "garage":return t?"mdi:garage-open":"mdi:garage";case "door":return t?"mdi:door-open":"mdi:door-closed";case "shutter":return t?"mdi:window-shutter-open":"mdi:window-shutter";case "blind":return t?"mdi:blinds-open":"mdi:blinds";case "window":return t?"mdi:window-open":"mdi:window-closed";default:return me("cover",e.state)}},sensor:function(e){var t=e.attributes.device_class;if(t&&t in xe)return xe[t];if("battery"===t){var r=Number(e.state);if(isNaN(r))return "mdi:battery-unknown";var n=10*Math.round(r/10);return n>=100?"mdi:battery":n<=0?"mdi:battery-alert":"hass:battery-"+n}var i=e.attributes.unit_of_measurement;return "°C"===i||"°F"===i?"mdi:thermometer":me("sensor")},input_datetime:function(e){return e.attributes.has_date?e.attributes.has_time?me("input_datetime"):"mdi:calendar":"mdi:clock"}},Se=function(e){if(!e)return "mdi:bookmark";if(e.attributes.icon)return e.attributes.icon;var t=E(e.entity_id);return t in De?De[t](e):me(t,e.state)};

const VERSION = '1.3.7-beta.1';

function isString(testObj) {
    return (typeof testObj === 'string' || testObj instanceof String);
}

console.info(`%c  CONFIG-TEMPLATE-CARD  \n%c  Version ${VERSION}         `, 'color: orange; font-weight: bold; background: black', 'color: white; font-weight: bold; background: dimgray');
let ConfigTemplateCard = class ConfigTemplateCard extends s$1 {
    constructor() {
        super(...arguments);
        this._initialized = false;
    }
    setConfig(config) {
        if (!config) {
            throw new Error('Invalid configuration');
        }
        if (!config.card && !config.row && !config.element) {
            throw new Error('No card or row or element defined');
        }
        if (config.card && !config.card.type) {
            throw new Error('No card type defined');
        }
        if (config.card && config.card.type === 'picture-elements') {
            console.warn('WARNING: config-template-card should not be used with the picture-elements card itself. Instead use it as one of the elements. Check the README for details');
        }
        if (config.element && !config.element.type) {
            throw new Error('No element type defined');
        }
        if (!config.entities) {
            throw new Error('No entities defined');
        }
        this._config = config;
        void this.loadCardHelpers();
    }
    getLovelacePanel() {
        const ha = document.querySelector('home-assistant');
        if (ha === null || ha === void 0 ? void 0 : ha.shadowRoot) {
            const haMain = ha.shadowRoot.querySelector('home-assistant-main');
            if (haMain === null || haMain === void 0 ? void 0 : haMain.shadowRoot) {
                return haMain.shadowRoot.querySelector('ha-panel-lovelace');
            }
        }
        return null;
    }
    getLovelaceConfig() {
        var _a, _b;
        const panel = this.getLovelacePanel();
        if ((_b = (_a = panel === null || panel === void 0 ? void 0 : panel.lovelace) === null || _a === void 0 ? void 0 : _a.config) === null || _b === void 0 ? void 0 : _b.config_template_card_vars) {
            return panel.lovelace.config.config_template_card_vars;
        }
        return {};
    }
    shouldUpdate(changedProps) {
        if (!this._initialized) {
            this._initialize();
        }
        if (changedProps.has('_config')) {
            return true;
        }
        if (this._config) {
            const oldHass = changedProps.get('hass');
            if (oldHass) {
                this._evaluateVars();
                for (const entity of this._evaluateStructure(structuredClone(this._config.entities))) {
                    if (this.hass && oldHass.states[entity] !== this.hass.states[entity]) {
                        return true;
                    }
                }
                return false;
            }
        }
        return true;
    }
    getCardSize() {
        if (this.shadowRoot) {
            // eslint detects this assertion as unnecessary, but typescript requires it.
            // eslint-disable-next-line @typescript-eslint/no-unnecessary-type-assertion
            const element = this.shadowRoot.querySelector('#card > *');
            if (element) {
                Promise.resolve(A(element)).then((size) => {
                    console.log('computeCardSize is ' + size.toString());
                }, () => undefined);
                return A(element);
            }
        }
        return 1;
    }
    render() {
        if (!this._config ||
            !this.hass ||
            !this._helpers ||
            (!this._config.card && !this._config.row && !this._config.element)) {
            return x$1 ``;
        }
        let configSection = this._config.card
            ? structuredClone(this._config.card)
            : this._config.row
                ? structuredClone(this._config.row)
                : structuredClone(this._config.element);
        let style = this._config.style ? structuredClone(this._config.style) : {};
        // render() is usually called shortly after shouldUpdate(), in which case we probably don't need
        // to re-evaluate variables.
        if (!this._curVars) {
            this._evaluateVars();
        }
        configSection = this._evaluateStructure(configSection);
        style = this._evaluateStructure(style);
        // In case the next call to render() is not preceded by a call to shouldUpdate(), force the next
        // render() call to re-evaluate variables.
        this._curVars = undefined;
        const element = this._config.card
            ? this._helpers.createCardElement(configSection)
            : this._config.row
                ? this._helpers.createRowElement(configSection)
                : this._helpers.createHuiElement(configSection);
        element.hass = this.hass;
        if (this._config.element) {
            Object.keys(style).forEach((prop) => {
                this.style.setProperty(prop, style[prop]);
            });
            if (configSection === null || configSection === void 0 ? void 0 : configSection.style) {
                Object.keys(configSection.style).forEach((prop) => {
                    if (configSection.style) { // TypeScript requires a redundant check here, not sure why
                        element.style.setProperty(prop, configSection.style[prop]);
                    }
                });
            }
        }
        return x$1 `<div id="card">${element}</div>`;
    }
    _initialize() {
        if (this.hass === undefined)
            return;
        if (this._config === undefined)
            return;
        if (this._helpers === undefined)
            return;
        this._initialized = true;
    }
    async loadCardHelpers() {
        this._helpers = await window.loadCardHelpers();
    }
    _evaluateStructure(struct) {
        if (struct instanceof Array) {
            for (let i = 0; i < struct.length; ++i) {
                const value = struct[i];
                struct[i] = this._evaluateStructure(value);
            }
        }
        else if (typeof struct === 'object') {
            // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
            Object.entries(struct).forEach(entry => {
                const key = entry[0];
                const value = entry[1];
                struct[key] = this._evaluateStructure(value);
            });
        }
        else if (isString(struct) && struct.includes('${')) {
            return this._evaluateTemplate(struct);
        }
        return struct;
    }
    _evaluateTemplate(template) {
        var _a;
        if (template.startsWith('${') && template.endsWith('}')) {
            // The entire property is a template, return eval's result directly
            // to preserve types other than string (eg. numbers)
            return this._evalWithVars(template.substring(2, template.length - 1));
        }
        (_a = /\${[^}]+}/.exec(template)) === null || _a === void 0 ? void 0 : _a.forEach(m => {
            const repl = this._evalWithVars(m.substring(2, m.length - 1)).toString();
            template = template.replace(m, repl);
        });
        return template;
    }
    _evaluateVars() {
        var _a, _b, _c;
        const vars = [];
        const namedVars = {};
        const arrayVars = [];
        const cv = this._curVars = {
            hass: this.hass, states: (_a = this.hass) === null || _a === void 0 ? void 0 : _a.states, user: (_b = this.hass) === null || _b === void 0 ? void 0 : _b.user, vars: vars,
            _evalInit: '',
        };
        cv._evalInit += "var hass = this._curVars.hass;\n";
        cv._evalInit += "var states = this._curVars.states;\n";
        cv._evalInit += "var user = this._curVars.user;\n";
        cv._evalInit += "var vars = this._curVars.vars;\n";
        if ((_c = this._config) === null || _c === void 0 ? void 0 : _c.variables) {
            if (Array.isArray(this._config.variables)) {
                // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
                arrayVars.push(...this._config.variables);
            }
            else {
                Object.assign(namedVars, this._config.variables);
            }
        }
        const localVars = this.getLovelaceConfig();
        if (localVars) {
            if (Array.isArray(localVars)) {
                // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
                arrayVars.push(...localVars);
            }
            else {
                Object.assign(namedVars, localVars);
            }
        }
        for (let v of arrayVars) {
            if (isString(v)) {
                v = this._evalWithVars(v);
            }
            else {
                v = structuredClone(v);
            }
            vars.push(v);
        }
        for (const varName in namedVars) {
            let v = namedVars[varName];
            if (isString(v)) {
                v = this._evalWithVars(v);
            }
            else {
                v = structuredClone(v);
            }
            vars[varName] = v;
            cv._evalInit += `var ${varName} = vars['${varName}'];\n`;
        }
    }
    _evalWithVars(template) {
        // Be aware that `this.hass` must be available to evaluated templates for backward compatibility
        // with old config-template-card configs.
        var _a;
        const init = (((_a = this._curVars) === null || _a === void 0 ? void 0 : _a._evalInit) ? this._curVars._evalInit : '');
        // "direct" eval() is considered insecure and generates warnings, so use "indirect" eval(),
        // which uses global scope as local scope (this === window, so this.hass should work).
        const tsWindow = window; // Silence typescript errors about setting variables on window
        const origCurVars = tsWindow._curVars; // Just in case there is a conflicting global variable
        tsWindow._curVars = this._curVars;
        const indirectEval = eval;
        const ret = indirectEval(init + template);
        if (origCurVars) {
            tsWindow._curVars = origCurVars;
        }
        else {
            delete tsWindow._curVars;
        }
        return ret;
    }
};
__decorate([
    n$2({ attribute: false })
], ConfigTemplateCard.prototype, "hass", void 0);
__decorate([
    t$2()
], ConfigTemplateCard.prototype, "_config", void 0);
__decorate([
    t$2()
], ConfigTemplateCard.prototype, "_helpers", void 0);
ConfigTemplateCard = __decorate([
    e$6('config-template-card')
], ConfigTemplateCard);

export { ConfigTemplateCard };
//# sourceMappingURL=config-template-card.js.map
