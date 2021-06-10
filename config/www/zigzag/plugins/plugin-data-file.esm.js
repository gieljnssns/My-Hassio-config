var commonjsGlobal = typeof globalThis !== 'undefined' ? globalThis : typeof window !== 'undefined' ? window : typeof global !== 'undefined' ? global : typeof self !== 'undefined' ? self : {};

function createCommonjsModule(fn) {
  var module = { exports: {} };
	return fn(module, module.exports), module.exports;
}

var util_1 = createCommonjsModule(function (module, exports) {
var __values = (commonjsGlobal && commonjsGlobal.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.INVALID = Symbol('invalid_data');
var util;
(function (util) {
    function assertNever(_x) {
        throw new Error();
    }
    util.assertNever = assertNever;
    util.arrayToEnum = function (items) {
        var e_1, _a;
        var obj = {};
        try {
            for (var items_1 = __values(items), items_1_1 = items_1.next(); !items_1_1.done; items_1_1 = items_1.next()) {
                var item = items_1_1.value;
                obj[item] = item;
            }
        }
        catch (e_1_1) { e_1 = { error: e_1_1 }; }
        finally {
            try {
                if (items_1_1 && !items_1_1.done && (_a = items_1.return)) _a.call(items_1);
            }
            finally { if (e_1) throw e_1.error; }
        }
        return obj;
    };
    util.getValidEnumValues = function (obj) {
        var e_2, _a;
        var validKeys = Object.keys(obj).filter(function (k) { return typeof obj[obj[k]] !== 'number'; });
        var filtered = {};
        try {
            for (var validKeys_1 = __values(validKeys), validKeys_1_1 = validKeys_1.next(); !validKeys_1_1.done; validKeys_1_1 = validKeys_1.next()) {
                var k = validKeys_1_1.value;
                filtered[k] = obj[k];
            }
        }
        catch (e_2_1) { e_2 = { error: e_2_1 }; }
        finally {
            try {
                if (validKeys_1_1 && !validKeys_1_1.done && (_a = validKeys_1.return)) _a.call(validKeys_1);
            }
            finally { if (e_2) throw e_2.error; }
        }
        return util.getValues(filtered);
    };
    util.getValues = function (obj) {
        return Object.keys(obj).map(function (e) {
            return obj[e];
        });
    };
    util.objectValues = function (obj) {
        return Object.keys(obj).map(function (e) {
            return obj[e];
        });
    };
    util.find = function (arr, checker) {
        var e_3, _a;
        try {
            for (var arr_1 = __values(arr), arr_1_1 = arr_1.next(); !arr_1_1.done; arr_1_1 = arr_1.next()) {
                var item = arr_1_1.value;
                if (checker(item))
                    return item;
            }
        }
        catch (e_3_1) { e_3 = { error: e_3_1 }; }
        finally {
            try {
                if (arr_1_1 && !arr_1_1.done && (_a = arr_1.return)) _a.call(arr_1);
            }
            finally { if (e_3) throw e_3.error; }
        }
        return undefined;
    };
})(util = exports.util || (exports.util = {}));

});

var __extends = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __read = (commonjsGlobal && commonjsGlobal.__read) || function (o, n) {
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
};
var __spread = (commonjsGlobal && commonjsGlobal.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read(arguments[i]));
    return ar;
};
var __values = (commonjsGlobal && commonjsGlobal.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};


var ZodIssueCode = util_1.util.arrayToEnum([
    'invalid_type',
    'nonempty_array_is_empty',
    'custom',
    'invalid_union',
    'invalid_literal_value',
    'invalid_enum_value',
    'unrecognized_keys',
    'invalid_arguments',
    'invalid_return_type',
    'invalid_date',
    'invalid_string',
    'too_small',
    'too_big',
    'invalid_intersection_types',
]);
var quotelessJson = function (obj) {
    var json = JSON.stringify(obj, null, 2);
    return json.replace(/"([^"]+)":/g, '$1:');
};
var ZodError = (function (_super) {
    __extends(ZodError, _super);
    function ZodError(issues) {
        var _newTarget = this.constructor;
        var _this = _super.call(this) || this;
        _this.issues = [];
        _this.addIssue = function (sub) {
            _this.issues = __spread(_this.issues, [sub]);
        };
        _this.addIssues = function (subs) {
            if (subs === void 0) { subs = []; }
            _this.issues = __spread(_this.issues, subs);
        };
        _this.flatten = function () {
            var e_1, _a;
            var fieldErrors = {};
            var formErrors = [];
            try {
                for (var _b = __values(_this.issues), _c = _b.next(); !_c.done; _c = _b.next()) {
                    var sub = _c.value;
                    if (sub.path.length > 0) {
                        fieldErrors[sub.path[0]] = fieldErrors[sub.path[0]] || [];
                        fieldErrors[sub.path[0]].push(sub.message);
                    }
                    else {
                        formErrors.push(sub.message);
                    }
                }
            }
            catch (e_1_1) { e_1 = { error: e_1_1 }; }
            finally {
                try {
                    if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
                }
                finally { if (e_1) throw e_1.error; }
            }
            return { formErrors: formErrors, fieldErrors: fieldErrors };
        };
        var actualProto = _newTarget.prototype;
        Object.setPrototypeOf(_this, actualProto);
        _this.issues = issues;
        return _this;
    }
    Object.defineProperty(ZodError.prototype, "errors", {
        get: function () {
            return this.issues;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodError.prototype, "message", {
        get: function () {
            return JSON.stringify(this.issues, null, 2);
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodError.prototype, "isEmpty", {
        get: function () {
            return this.issues.length === 0;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodError.prototype, "formErrors", {
        get: function () {
            return this.flatten();
        },
        enumerable: true,
        configurable: true
    });
    ZodError.create = function (issues) {
        var error = new ZodError(issues);
        return error;
    };
    return ZodError;
}(Error));
var ZodError_2 = ZodError;


var ZodError_1 = /*#__PURE__*/Object.defineProperty({
	ZodIssueCode: ZodIssueCode,
	quotelessJson: quotelessJson,
	ZodError: ZodError_2
}, '__esModule', {value: true});

var defaultErrorMap_1 = function (error, _ctx) {
    var message;
    switch (error.code) {
        case ZodError_1.ZodIssueCode.invalid_type:
            if (error.received === 'undefined') {
                message = 'Required';
            }
            else {
                message = "Expected " + error.expected + ", received " + error.received;
            }
            break;
        case ZodError_1.ZodIssueCode.nonempty_array_is_empty:
            message = "List must contain at least one item";
            break;
        case ZodError_1.ZodIssueCode.unrecognized_keys:
            message = "Unrecognized key(s) in object: " + error.keys
                .map(function (k) { return "'" + k + "'"; })
                .join(', ');
            break;
        case ZodError_1.ZodIssueCode.invalid_union:
            message = "Invalid input";
            break;
        case ZodError_1.ZodIssueCode.invalid_literal_value:
            message = "Input must be \"" + error.expected + "\"";
            break;
        case ZodError_1.ZodIssueCode.invalid_enum_value:
            message = "Input must be one of these values: " + error.options.join(', ');
            break;
        case ZodError_1.ZodIssueCode.invalid_arguments:
            message = "Invalid function arguments";
            break;
        case ZodError_1.ZodIssueCode.invalid_return_type:
            message = "Invalid function return type";
            break;
        case ZodError_1.ZodIssueCode.invalid_date:
            message = "Invalid date";
            break;
        case ZodError_1.ZodIssueCode.invalid_string:
            if (error.validation !== 'regex')
                message = "Invalid " + error.validation;
            else
                message = 'Invalid';
            break;
        case ZodError_1.ZodIssueCode.too_small:
            if (error.type === 'array')
                message = "Should have " + (error.inclusive ? "at least" : "more than") + " " + error.minimum + " items";
            else if (error.type === 'string')
                message = "Should be " + (error.inclusive ? "at least" : "over") + " " + error.minimum + " characters";
            else if (error.type === 'number')
                message = "Value should be greater than " + (error.inclusive ? "or equal to " : "") + error.minimum;
            else
                message = 'Invalid input';
            break;
        case ZodError_1.ZodIssueCode.too_big:
            if (error.type === 'array')
                message = "Should have " + (error.inclusive ? "at most" : "less than") + " " + error.maximum + " items";
            else if (error.type === 'string')
                message = "Should be " + (error.inclusive ? "at most" : "under") + " " + error.maximum + " characters long";
            else if (error.type === 'number')
                message = "Value should be less than " + (error.inclusive ? "or equal to " : "") + error.maximum;
            else
                message = 'Invalid input';
            break;
        case ZodError_1.ZodIssueCode.custom:
            message = "Invalid input.";
            break;
        case ZodError_1.ZodIssueCode.invalid_intersection_types:
            message = "Intersections only support objects";
            break;
        default:
            message = "Invalid input.";
            util_1.util.assertNever(error);
    }
    return { message: message };
};


var defaultErrorMap = /*#__PURE__*/Object.defineProperty({
	defaultErrorMap: defaultErrorMap_1
}, '__esModule', {value: true});

var PseudoPromise_1 = createCommonjsModule(function (module, exports) {
var __awaiter = (commonjsGlobal && commonjsGlobal.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (commonjsGlobal && commonjsGlobal.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
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
};
var __read = (commonjsGlobal && commonjsGlobal.__read) || function (o, n) {
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
};
var __spread = (commonjsGlobal && commonjsGlobal.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read(arguments[i]));
    return ar;
};
var __values = (commonjsGlobal && commonjsGlobal.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
Object.defineProperty(exports, "__esModule", { value: true });


exports.NOSET = Symbol('no_set');
var PseudoPromise = (function () {
    function PseudoPromise(funcs) {
        var _this = this;
        if (funcs === void 0) { funcs = []; }
        this.all = function (pps) {
            return _this.then(function (_arg, ctx) {
                if (ctx.async) {
                    var allValues = Promise.all(pps.map(function (pp) { return __awaiter(_this, void 0, void 0, function () {
                        var asdf, err_1;
                        return __generator(this, function (_a) {
                            switch (_a.label) {
                                case 0:
                                    _a.trys.push([0, 2, , 3]);
                                    return [4, pp.getValueAsync()];
                                case 1:
                                    asdf = _a.sent();
                                    return [2, asdf];
                                case 2:
                                    err_1 = _a.sent();
                                    return [2, util_1.INVALID];
                                case 3: return [2];
                            }
                        });
                    }); })).then(function (vals) {
                        return vals;
                    });
                    return allValues;
                }
                else {
                    return pps.map(function (pp) { return pp.getValueSync(); });
                }
            });
        };
        this.then = function (func) {
            return new PseudoPromise(__spread(_this.items, [
                { type: 'function', function: func },
            ]));
        };
        this.catch = function (catcher) {
            return new PseudoPromise(__spread(_this.items, [
                { type: 'catcher', catcher: catcher },
            ]));
        };
        this.getValueSync = function () {
            var val = undefined;
            var _loop_1 = function (index) {
                try {
                    var item = _this.items[index];
                    if (item.type === 'function') {
                        val = item.function(val, { async: false });
                    }
                }
                catch (err) {
                    var catcherIndex = _this.items.findIndex(function (x, i) { return x.type === 'catcher' && i > index; });
                    var catcherItem = _this.items[catcherIndex];
                    if (!catcherItem || catcherItem.type !== 'catcher') {
                        throw err;
                    }
                    else {
                        index = catcherIndex;
                        val = catcherItem.catcher(err, { async: false });
                    }
                }
                out_index_1 = index;
            };
            var out_index_1;
            for (var index = 0; index < _this.items.length; index++) {
                _loop_1(index);
                index = out_index_1;
            }
            return val;
        };
        this.getValueAsync = function () { return __awaiter(_this, void 0, void 0, function () {
            var val, _loop_2, this_1, out_index_2, index;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        val = undefined;
                        _loop_2 = function (index) {
                            var item, err_2, catcherIndex, catcherItem;
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        item = this_1.items[index];
                                        _a.label = 1;
                                    case 1:
                                        _a.trys.push([1, 4, , 8]);
                                        if (!(item.type === 'function')) return [3, 3];
                                        return [4, item.function(val, { async: true })];
                                    case 2:
                                        val = _a.sent();
                                        _a.label = 3;
                                    case 3: return [3, 8];
                                    case 4:
                                        err_2 = _a.sent();
                                        catcherIndex = this_1.items.findIndex(function (x, i) { return x.type === 'catcher' && i > index; });
                                        catcherItem = this_1.items[catcherIndex];
                                        if (!(!catcherItem || catcherItem.type !== 'catcher')) return [3, 5];
                                        throw err_2;
                                    case 5:
                                        index = catcherIndex;
                                        return [4, catcherItem.catcher(err_2, { async: true })];
                                    case 6:
                                        val = _a.sent();
                                        _a.label = 7;
                                    case 7: return [3, 8];
                                    case 8:
                                        if (val instanceof PseudoPromise) {
                                            throw new Error('ASYNC: DO NOT RETURN PSEUDOPROMISE FROM FUNCTIONS');
                                        }
                                        if (val instanceof Promise) {
                                            throw new Error('ASYNC: DO NOT RETURN PROMISE FROM FUNCTIONS');
                                        }
                                        out_index_2 = index;
                                        return [2];
                                }
                            });
                        };
                        this_1 = this;
                        index = 0;
                        _a.label = 1;
                    case 1:
                        if (!(index < this.items.length)) return [3, 4];
                        return [5, _loop_2(index)];
                    case 2:
                        _a.sent();
                        index = out_index_2;
                        _a.label = 3;
                    case 3:
                        index++;
                        return [3, 1];
                    case 4: return [2, val];
                }
            });
        }); };
        this.items = funcs;
    }
    PseudoPromise.all = function (pps) {
        return new PseudoPromise().all(pps);
    };
    PseudoPromise.object = function (pps) {
        return new PseudoPromise().then(function (_arg, ctx) {
            var e_1, _a;
            var value = {};
            var zerr = new ZodError_1.ZodError([]);
            if (ctx.async) {
                var getAsyncObject = function () { return __awaiter(void 0, void 0, void 0, function () {
                    var items, items_2, items_2_1, item;
                    var e_2, _a;
                    return __generator(this, function (_b) {
                        switch (_b.label) {
                            case 0: return [4, Promise.all(Object.keys(pps).map(function (k) { return __awaiter(void 0, void 0, void 0, function () {
                                    var v, err_3;
                                    return __generator(this, function (_a) {
                                        switch (_a.label) {
                                            case 0:
                                                _a.trys.push([0, 2, , 3]);
                                                return [4, pps[k].getValueAsync()];
                                            case 1:
                                                v = _a.sent();
                                                return [2, [k, v]];
                                            case 2:
                                                err_3 = _a.sent();
                                                if (err_3 instanceof ZodError_1.ZodError) {
                                                    zerr.addIssues(err_3.issues);
                                                    return [2, [k, util_1.INVALID]];
                                                }
                                                throw err_3;
                                            case 3: return [2];
                                        }
                                    });
                                }); }))];
                            case 1:
                                items = _b.sent();
                                if (!zerr.isEmpty)
                                    throw zerr;
                                try {
                                    for (items_2 = __values(items), items_2_1 = items_2.next(); !items_2_1.done; items_2_1 = items_2.next()) {
                                        item = items_2_1.value;
                                        if (item[1] !== exports.NOSET)
                                            value[item[0]] = item[1];
                                    }
                                }
                                catch (e_2_1) { e_2 = { error: e_2_1 }; }
                                finally {
                                    try {
                                        if (items_2_1 && !items_2_1.done && (_a = items_2.return)) _a.call(items_2);
                                    }
                                    finally { if (e_2) throw e_2.error; }
                                }
                                return [2, value];
                        }
                    });
                }); };
                return getAsyncObject();
            }
            else {
                var items = Object.keys(pps).map(function (k) {
                    try {
                        var v = pps[k].getValueSync();
                        return [k, v];
                    }
                    catch (err) {
                        if (err instanceof ZodError_1.ZodError) {
                            zerr.addIssues(err.issues);
                            return [k, util_1.INVALID];
                        }
                        throw err;
                    }
                });
                if (!zerr.isEmpty)
                    throw zerr;
                try {
                    for (var items_1 = __values(items), items_1_1 = items_1.next(); !items_1_1.done; items_1_1 = items_1.next()) {
                        var item = items_1_1.value;
                        if (item[1] !== exports.NOSET)
                            value[item[0]] = item[1];
                    }
                }
                catch (e_1_1) { e_1 = { error: e_1_1 }; }
                finally {
                    try {
                        if (items_1_1 && !items_1_1.done && (_a = items_1.return)) _a.call(items_1);
                    }
                    finally { if (e_1) throw e_1.error; }
                }
                return value;
            }
        });
    };
    PseudoPromise.resolve = function (value) {
        if (value instanceof PseudoPromise) {
            throw new Error('Do not pass PseudoPromise into PseudoPromise.resolve');
        }
        return new PseudoPromise().then(function () { return value; });
    };
    return PseudoPromise;
}());
exports.PseudoPromise = PseudoPromise;

});

var parser = createCommonjsModule(function (module, exports) {
var __assign = (commonjsGlobal && commonjsGlobal.__assign) || function () {
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
var __awaiter = (commonjsGlobal && commonjsGlobal.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (commonjsGlobal && commonjsGlobal.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
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
};
var __read = (commonjsGlobal && commonjsGlobal.__read) || function (o, n) {
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
};
var __spread = (commonjsGlobal && commonjsGlobal.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read(arguments[i]));
    return ar;
};
var __values = (commonjsGlobal && commonjsGlobal.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
var __importStar = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
var z = __importStar(base);





exports.getParsedType = function (data) {
    if (typeof data === 'string')
        return 'string';
    if (typeof data === 'number') {
        if (Number.isNaN(data))
            return 'nan';
        return 'number';
    }
    if (typeof data === 'boolean')
        return 'boolean';
    if (typeof data === 'bigint')
        return 'bigint';
    if (typeof data === 'symbol')
        return 'symbol';
    if (data instanceof Date)
        return 'date';
    if (typeof data === 'function')
        return 'function';
    if (data === undefined)
        return 'undefined';
    if (typeof data === 'undefined')
        return 'undefined';
    if (typeof data === 'object') {
        if (Array.isArray(data))
            return 'array';
        if (data === null)
            return 'null';
        if (data.then &&
            typeof data.then === 'function' &&
            data.catch &&
            typeof data.catch === 'function') {
            return 'promise';
        }
        if (data instanceof Map) {
            return 'map';
        }
        return 'object';
    }
    return 'unknown';
};
exports.ZodParsedType = util_1.util.arrayToEnum([
    'string',
    'nan',
    'number',
    'integer',
    'boolean',
    'date',
    'bigint',
    'symbol',
    'function',
    'undefined',
    'null',
    'array',
    'object',
    'unknown',
    'promise',
    'void',
    'never',
    'map',
]);
var makeError = function (params, data, errorData) {
    var errorArg = __assign(__assign({}, errorData), { path: __spread(params.path, (errorData.path || [])) });
    var ctxArg = { data: data };
    var defaultError = defaultErrorMap.defaultErrorMap === params.errorMap
        ? { message: "Invalid value." }
        : defaultErrorMap.defaultErrorMap(errorArg, __assign(__assign({}, ctxArg), { defaultError: "Invalid value." }));
    return __assign(__assign({}, errorData), { path: __spread(params.path, (errorData.path || [])), message: errorData.message ||
            params.errorMap(errorArg, __assign(__assign({}, ctxArg), { defaultError: defaultError.message })).message });
};
exports.ZodParser = function (schema) { return function (data, baseParams) {
    var e_1, _a, e_2, _b, e_3, _c, e_4, _d;
    if (baseParams === void 0) { baseParams = { seen: [], errorMap: defaultErrorMap.defaultErrorMap, path: [] }; }
    var _e, _f;
    var params = {
        seen: baseParams.seen || [],
        path: baseParams.path || [],
        errorMap: baseParams.errorMap || defaultErrorMap.defaultErrorMap,
        async: (_e = baseParams.async) !== null && _e !== void 0 ? _e : false,
        runAsyncValidationsInSeries: (_f = baseParams.runAsyncValidationsInSeries) !== null && _f !== void 0 ? _f : false,
    };
    var def = schema._def;
    var PROMISE = new PseudoPromise_1.PseudoPromise();
    PROMISE._default = true;
    var RESULT = {
        input: data,
        output: util_1.INVALID,
    };
    params.seen = params.seen || [];
    var ERROR = new ZodError_1.ZodError([]);
    var THROW = function () {
        RESULT.error = ERROR;
        throw ERROR;
    };
    var HANDLE = function (err) {
        if (err instanceof ZodError_1.ZodError) {
            ERROR.addIssues(err.issues);
            return util_1.INVALID;
        }
        throw ERROR;
    };
    var parsedType = exports.getParsedType(data);
    switch (def.t) {
        case z.ZodTypes.string:
            if (parsedType !== exports.ZodParsedType.string) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.string,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.number:
            if (parsedType !== exports.ZodParsedType.number) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.number,
                    received: parsedType,
                }));
                THROW();
            }
            if (Number.isNaN(data)) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.number,
                    received: exports.ZodParsedType.nan,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.bigint:
            if (parsedType !== exports.ZodParsedType.bigint) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.bigint,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.boolean:
            if (parsedType !== exports.ZodParsedType.boolean) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.boolean,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.undefined:
            if (parsedType !== exports.ZodParsedType.undefined) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.undefined,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.null:
            if (parsedType !== exports.ZodParsedType.null) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.null,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.any:
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.unknown:
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.never:
            ERROR.addIssue(makeError(params, data, {
                code: ZodError_1.ZodIssueCode.invalid_type,
                expected: exports.ZodParsedType.never,
                received: parsedType,
            }));
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(util_1.INVALID);
            break;
        case z.ZodTypes.void:
            if (parsedType !== exports.ZodParsedType.undefined &&
                parsedType !== exports.ZodParsedType.null) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.void,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.array:
            RESULT.output = [];
            if (parsedType !== exports.ZodParsedType.array) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.array,
                    received: parsedType,
                }));
                THROW();
            }
            if (def.nonempty === true && data.length === 0) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.nonempty_array_is_empty,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1.PseudoPromise.all(data.map(function (item, i) {
                return new PseudoPromise_1.PseudoPromise()
                    .then(function () {
                    return def.type.parse(item, __assign(__assign({}, params), { path: __spread(params.path, [i]) }));
                })
                    .catch(function (err) {
                    if (!(err instanceof ZodError_1.ZodError)) {
                        throw err;
                    }
                    ERROR.addIssues(err.issues);
                    return util_1.INVALID;
                });
            }));
            break;
        case z.ZodTypes.map:
            if (parsedType !== exports.ZodParsedType.map) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.map,
                    received: parsedType,
                }));
                THROW();
            }
            var dataMap = data;
            var returnedMap_1 = new Map();
            PROMISE = PseudoPromise_1.PseudoPromise.all(__spread(dataMap.entries()).map(function (_a, index) {
                var _b = __read(_a, 2), key = _b[0], value = _b[1];
                return PseudoPromise_1.PseudoPromise.all([
                    new PseudoPromise_1.PseudoPromise()
                        .then(function () {
                        return def.keyType.parse(key, __assign(__assign({}, params), { path: __spread(params.path, [index, 'key']) }));
                    })
                        .catch(HANDLE),
                    new PseudoPromise_1.PseudoPromise()
                        .then(function () {
                        var mapValue = def.valueType.parse(value, __assign(__assign({}, params), { path: __spread(params.path, [index, 'value']) }));
                        return [key, mapValue];
                    })
                        .catch(HANDLE),
                ])
                    .then(function (item) {
                    if (item[0] !== util_1.INVALID && item[1] !== util_1.INVALID) {
                        returnedMap_1.set(item[0], item[1]);
                    }
                })
                    .catch(HANDLE);
            }))
                .then(function () {
                if (!ERROR.isEmpty) {
                    throw ERROR;
                }
            })
                .then(function () {
                return returnedMap_1;
            })
                .then(function () {
                return returnedMap_1;
            });
            break;
        case z.ZodTypes.object:
            RESULT.output = {};
            if (parsedType !== exports.ZodParsedType.object) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.object,
                    received: parsedType,
                }));
                THROW();
            }
            var objectPromises_1 = {};
            var shape = def.shape();
            var shapeKeys_2 = Object.keys(shape);
            var dataKeys = Object.keys(data);
            var extraKeys = dataKeys.filter(function (k) { return shapeKeys_2.indexOf(k) === -1; });
            var _loop_1 = function (key) {
                var keyValidator = shapeKeys_2.includes(key)
                    ? shape[key]
                    : !(def.catchall instanceof cjs.ZodNever)
                        ? def.catchall
                        : undefined;
                if (!keyValidator) {
                    return "continue";
                }
                if (typeof data[key] === 'undefined' && !dataKeys.includes(key)) {
                    objectPromises_1[key] = new PseudoPromise_1.PseudoPromise()
                        .then(function () {
                        return keyValidator.parse(undefined, __assign(__assign({}, params), { path: __spread(params.path, [key]) }));
                    })
                        .then(function (output) {
                        if (output === undefined) {
                            return PseudoPromise_1.NOSET;
                        }
                        else {
                            return output;
                        }
                    })
                        .catch(function (err) {
                        if (err instanceof ZodError_1.ZodError) {
                            var zerr = err;
                            ERROR.addIssues(zerr.issues);
                            objectPromises_1[key] = PseudoPromise_1.PseudoPromise.resolve(util_1.INVALID);
                        }
                        else {
                            throw err;
                        }
                    });
                    return "continue";
                }
                objectPromises_1[key] = new PseudoPromise_1.PseudoPromise()
                    .then(function () {
                    return keyValidator.parse(data[key], __assign(__assign({}, params), { path: __spread(params.path, [key]) }));
                })
                    .catch(function (err) {
                    if (err instanceof ZodError_1.ZodError) {
                        var zerr = err;
                        ERROR.addIssues(zerr.issues);
                        return util_1.INVALID;
                    }
                    else {
                        throw err;
                    }
                });
            };
            try {
                for (var shapeKeys_1 = __values(shapeKeys_2), shapeKeys_1_1 = shapeKeys_1.next(); !shapeKeys_1_1.done; shapeKeys_1_1 = shapeKeys_1.next()) {
                    var key = shapeKeys_1_1.value;
                    _loop_1(key);
                }
            }
            catch (e_1_1) { e_1 = { error: e_1_1 }; }
            finally {
                try {
                    if (shapeKeys_1_1 && !shapeKeys_1_1.done && (_a = shapeKeys_1.return)) _a.call(shapeKeys_1);
                }
                finally { if (e_1) throw e_1.error; }
            }
            if (def.catchall instanceof cjs.ZodNever) {
                if (def.unknownKeys === 'passthrough') {
                    try {
                        for (var extraKeys_1 = __values(extraKeys), extraKeys_1_1 = extraKeys_1.next(); !extraKeys_1_1.done; extraKeys_1_1 = extraKeys_1.next()) {
                            var key = extraKeys_1_1.value;
                            objectPromises_1[key] = PseudoPromise_1.PseudoPromise.resolve(data[key]);
                        }
                    }
                    catch (e_2_1) { e_2 = { error: e_2_1 }; }
                    finally {
                        try {
                            if (extraKeys_1_1 && !extraKeys_1_1.done && (_b = extraKeys_1.return)) _b.call(extraKeys_1);
                        }
                        finally { if (e_2) throw e_2.error; }
                    }
                }
                else if (def.unknownKeys === 'strict') {
                    if (extraKeys.length > 0) {
                        ERROR.addIssue(makeError(params, data, {
                            code: ZodError_1.ZodIssueCode.unrecognized_keys,
                            keys: extraKeys,
                        }));
                    }
                }
                else if (def.unknownKeys === 'strip') ;
                else {
                    util_1.util.assertNever(def.unknownKeys);
                }
            }
            else {
                var _loop_2 = function (key) {
                    objectPromises_1[key] = new PseudoPromise_1.PseudoPromise()
                        .then(function () {
                        var parsedValue = def.catchall.parse(data[key], __assign(__assign({}, params), { path: __spread(params.path, [key]) }));
                        return parsedValue;
                    })
                        .catch(function (err) {
                        if (err instanceof ZodError_1.ZodError) {
                            ERROR.addIssues(err.issues);
                        }
                        else {
                            throw err;
                        }
                    });
                };
                try {
                    for (var extraKeys_2 = __values(extraKeys), extraKeys_2_1 = extraKeys_2.next(); !extraKeys_2_1.done; extraKeys_2_1 = extraKeys_2.next()) {
                        var key = extraKeys_2_1.value;
                        _loop_2(key);
                    }
                }
                catch (e_3_1) { e_3 = { error: e_3_1 }; }
                finally {
                    try {
                        if (extraKeys_2_1 && !extraKeys_2_1.done && (_c = extraKeys_2.return)) _c.call(extraKeys_2);
                    }
                    finally { if (e_3) throw e_3.error; }
                }
            }
            PROMISE = PseudoPromise_1.PseudoPromise.object(objectPromises_1)
                .then(function (resolvedObject) {
                Object.assign(RESULT.output, resolvedObject);
                return RESULT.output;
            })
                .then(function (finalObject) {
                if (ERROR.issues.length > 0) {
                    return util_1.INVALID;
                }
                return finalObject;
            })
                .catch(function (err) {
                if (err instanceof ZodError_1.ZodError) {
                    ERROR.addIssues(err.issues);
                    return util_1.INVALID;
                }
                throw err;
            });
            break;
        case z.ZodTypes.union:
            var isValid_1 = false;
            var unionErrors_1 = [];
            PROMISE = PseudoPromise_1.PseudoPromise.all(def.options.map(function (opt, _j) {
                return new PseudoPromise_1.PseudoPromise()
                    .then(function () {
                    return opt.parse(data, params);
                })
                    .then(function (optionData) {
                    isValid_1 = true;
                    return optionData;
                })
                    .catch(function (err) {
                    if (err instanceof ZodError_1.ZodError) {
                        unionErrors_1.push(err);
                        return util_1.INVALID;
                    }
                    throw err;
                });
            }))
                .then(function (unionResults) {
                if (!isValid_1) {
                    var nonTypeErrors = unionErrors_1.filter(function (err) {
                        return err.issues[0].code !== 'invalid_type';
                    });
                    if (nonTypeErrors.length === 1) {
                        ERROR.addIssues(nonTypeErrors[0].issues);
                    }
                    else {
                        ERROR.addIssue(makeError(params, data, {
                            code: ZodError_1.ZodIssueCode.invalid_union,
                            unionErrors: unionErrors_1,
                        }));
                    }
                    THROW();
                }
                return unionResults;
            })
                .then(function (unionResults) {
                return util_1.util.find(unionResults, function (val) { return val !== util_1.INVALID; });
            });
            break;
        case z.ZodTypes.intersection:
            PROMISE = PseudoPromise_1.PseudoPromise.all([
                new PseudoPromise_1.PseudoPromise()
                    .then(function () {
                    return def.left.parse(data, params);
                })
                    .catch(HANDLE),
                new PseudoPromise_1.PseudoPromise()
                    .then(function () {
                    return def.right.parse(data, params);
                })
                    .catch(HANDLE),
            ]).then(function (_a) {
                var _b = __read(_a, 2), parsedLeft = _b[0], parsedRight = _b[1];
                if (parsedLeft === util_1.INVALID || parsedRight === util_1.INVALID)
                    return util_1.INVALID;
                var parsedLeftType = exports.getParsedType(parsedLeft);
                var parsedRightType = exports.getParsedType(parsedRight);
                if (parsedLeft === parsedRight) {
                    return parsedLeft;
                }
                else if (parsedLeftType === exports.ZodParsedType.object &&
                    parsedRightType === exports.ZodParsedType.object) {
                    return __assign(__assign({}, parsedLeft), parsedRight);
                }
                else {
                    ERROR.addIssue(makeError(params, data, {
                        code: ZodError_1.ZodIssueCode.invalid_intersection_types,
                    }));
                }
            });
            break;
        case z.ZodTypes.optional:
            if (parsedType === exports.ZodParsedType.undefined) {
                PROMISE = PseudoPromise_1.PseudoPromise.resolve(undefined);
                break;
            }
            PROMISE = new PseudoPromise_1.PseudoPromise()
                .then(function () {
                return def.innerType.parse(data, params);
            })
                .catch(HANDLE);
            break;
        case z.ZodTypes.nullable:
            if (parsedType === exports.ZodParsedType.null) {
                PROMISE = PseudoPromise_1.PseudoPromise.resolve(null);
                break;
            }
            PROMISE = new PseudoPromise_1.PseudoPromise()
                .then(function () {
                return def.innerType.parse(data, params);
            })
                .catch(HANDLE);
            break;
        case z.ZodTypes.tuple:
            if (parsedType !== exports.ZodParsedType.array) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.array,
                    received: parsedType,
                }));
                THROW();
            }
            if (data.length > def.items.length) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.too_big,
                    maximum: def.items.length,
                    inclusive: true,
                    type: 'array',
                }));
            }
            else if (data.length < def.items.length) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.too_small,
                    minimum: def.items.length,
                    inclusive: true,
                    type: 'array',
                }));
            }
            var tupleData = data;
            PROMISE = PseudoPromise_1.PseudoPromise.all(tupleData.map(function (item, index) {
                var itemParser = def.items[index];
                return new PseudoPromise_1.PseudoPromise()
                    .then(function () {
                    var tupleDatum = itemParser.parse(item, __assign(__assign({}, params), { path: __spread(params.path, [index]) }));
                    return tupleDatum;
                })
                    .catch(function (err) {
                    if (err instanceof ZodError_1.ZodError) {
                        ERROR.addIssues(err.issues);
                        return;
                    }
                    throw err;
                })
                    .then(function (arg) {
                    return arg;
                });
            }))
                .then(function (tupleData) {
                if (!ERROR.isEmpty)
                    THROW();
                return tupleData;
            })
                .catch(function (err) {
                throw err;
            });
            break;
        case z.ZodTypes.lazy:
            var lazySchema = def.getter();
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(lazySchema.parse(data, params));
            break;
        case z.ZodTypes.literal:
            if (data !== def.value) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_literal_value,
                    expected: def.value,
                }));
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.enum:
            if (def.values.indexOf(data) === -1) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_enum_value,
                    options: def.values,
                }));
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.nativeEnum:
            if (util_1.util.getValidEnumValues(def.values).indexOf(data) === -1) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_enum_value,
                    options: util_1.util.objectValues(def.values),
                }));
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.function:
            if (parsedType !== exports.ZodParsedType.function) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.function,
                    received: parsedType,
                }));
                THROW();
            }
            var isAsyncFunction_1 = def.returns instanceof cjs.ZodPromise;
            var validatedFunction = function () {
                var args = [];
                for (var _i = 0; _i < arguments.length; _i++) {
                    args[_i] = arguments[_i];
                }
                var internalProm = new PseudoPromise_1.PseudoPromise()
                    .then(function () {
                    return def.args.parse(args, __assign(__assign({}, params), { async: isAsyncFunction_1 }));
                })
                    .catch(function (err) {
                    if (!(err instanceof ZodError_1.ZodError))
                        throw err;
                    var argsError = new ZodError_1.ZodError([]);
                    argsError.addIssue(makeError(params, data, {
                        code: ZodError_1.ZodIssueCode.invalid_arguments,
                        argumentsError: err,
                    }));
                    throw argsError;
                })
                    .then(function (args) {
                    return data.apply(void 0, __spread(args));
                })
                    .then(function (result) {
                    return def.returns.parse(result, __assign(__assign({}, params), { async: isAsyncFunction_1 }));
                })
                    .catch(function (err) {
                    if (err instanceof ZodError_1.ZodError) {
                        var returnsError = new ZodError_1.ZodError([]);
                        returnsError.addIssue(makeError(params, data, {
                            code: ZodError_1.ZodIssueCode.invalid_return_type,
                            returnTypeError: err,
                        }));
                        throw returnsError;
                    }
                    throw err;
                });
                if (isAsyncFunction_1) {
                    return internalProm.getValueAsync();
                }
                else {
                    return internalProm.getValueSync();
                }
            };
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(validatedFunction);
            break;
        case z.ZodTypes.record:
            if (parsedType !== exports.ZodParsedType.object) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.object,
                    received: parsedType,
                }));
                THROW();
            }
            var parsedRecordPromises = {};
            var _loop_3 = function (key) {
                parsedRecordPromises[key] = new PseudoPromise_1.PseudoPromise()
                    .then(function () {
                    return def.valueType.parse(data[key], __assign(__assign({}, params), { path: __spread(params.path, [key]) }));
                })
                    .catch(HANDLE);
            };
            for (var key in data) {
                _loop_3(key);
            }
            PROMISE = PseudoPromise_1.PseudoPromise.object(parsedRecordPromises);
            break;
        case z.ZodTypes.date:
            if (!(data instanceof Date)) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.date,
                    received: parsedType,
                }));
                THROW();
            }
            if (isNaN(data.getTime())) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_date,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.promise:
            if (parsedType !== exports.ZodParsedType.promise && params.async !== true) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.promise,
                    received: parsedType,
                }));
                THROW();
            }
            var promisified = parsedType === exports.ZodParsedType.promise ? data : Promise.resolve(data);
            PROMISE = PseudoPromise_1.PseudoPromise.resolve(promisified.then(function (resolvedData) {
                return def.type.parse(resolvedData, params);
            }));
            break;
        case z.ZodTypes.transformer:
            PROMISE = new PseudoPromise_1.PseudoPromise()
                .then(function () {
                return def.input.parse(data, params);
            })
                .then(function (inputParseResult) {
                var transformed = def.transformer(inputParseResult);
                if (transformed instanceof Promise && params.async === false) {
                    if (z.inputSchema(def.output)._def.t !== z.ZodTypes.promise) {
                        throw new Error("You can't call .parse on a schema containing async transformations.");
                    }
                }
                return transformed;
            })
                .then(function (transformedResult) {
                return def.output.parse(transformedResult, params);
            });
            break;
        default:
            PROMISE = PseudoPromise_1.PseudoPromise.resolve('adsf');
            util_1.util.assertNever(def);
    }
    if (PROMISE._default === true) {
        throw new Error('Result is not materialized.');
    }
    if (!ERROR.isEmpty) {
        THROW();
    }
    var customChecks = def.checks || [];
    var checkCtx = {
        addIssue: function (arg) {
            ERROR.addIssue(makeError(params, data, arg));
        },
        path: params.path,
    };
    if (params.async === false) {
        var resolvedValue = PROMISE.getValueSync();
        if (resolvedValue === util_1.INVALID && ERROR.isEmpty) {
            ERROR.addIssue(makeError(params, data, {
                code: ZodError_1.ZodIssueCode.custom,
                message: 'Invalid',
            }));
        }
        if (!ERROR.isEmpty) {
            THROW();
        }
        try {
            for (var customChecks_1 = __values(customChecks), customChecks_1_1 = customChecks_1.next(); !customChecks_1_1.done; customChecks_1_1 = customChecks_1.next()) {
                var check = customChecks_1_1.value;
                var checkResult = check.check(resolvedValue, checkCtx);
                if (checkResult instanceof Promise)
                    throw new Error("You can't use .parse on a schema containing async refinements. Use .parseAsync instead.");
            }
        }
        catch (e_4_1) { e_4 = { error: e_4_1 }; }
        finally {
            try {
                if (customChecks_1_1 && !customChecks_1_1.done && (_d = customChecks_1.return)) _d.call(customChecks_1);
            }
            finally { if (e_4) throw e_4.error; }
        }
        if (!ERROR.isEmpty) {
            THROW();
        }
        return resolvedValue;
    }
    else {
        var checker = function () { return __awaiter(void 0, void 0, void 0, function () {
            var resolvedValue, someError_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4, PROMISE.getValueAsync()];
                    case 1:
                        resolvedValue = _a.sent();
                        if (resolvedValue === util_1.INVALID && ERROR.isEmpty) {
                            ERROR.addIssue(makeError(params, data, {
                                code: ZodError_1.ZodIssueCode.custom,
                                message: 'Invalid',
                            }));
                        }
                        if (!ERROR.isEmpty) {
                            THROW();
                        }
                        if (!params.runAsyncValidationsInSeries) return [3, 3];
                        someError_1 = false;
                        return [4, customChecks.reduce(function (previousPromise, check) {
                                return previousPromise.then(function () { return __awaiter(void 0, void 0, void 0, function () {
                                    var len;
                                    return __generator(this, function (_a) {
                                        switch (_a.label) {
                                            case 0:
                                                if (!!someError_1) return [3, 2];
                                                len = ERROR.issues.length;
                                                return [4, check.check(resolvedValue, checkCtx)];
                                            case 1:
                                                _a.sent();
                                                if (len < ERROR.issues.length)
                                                    someError_1 = true;
                                                _a.label = 2;
                                            case 2: return [2];
                                        }
                                    });
                                }); });
                            }, Promise.resolve())];
                    case 2:
                        _a.sent();
                        return [3, 5];
                    case 3: return [4, Promise.all(customChecks.map(function (check) { return __awaiter(void 0, void 0, void 0, function () {
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0: return [4, check.check(resolvedValue, checkCtx)];
                                    case 1:
                                        _a.sent();
                                        return [2];
                                }
                            });
                        }); }))];
                    case 4:
                        _a.sent();
                        _a.label = 5;
                    case 5:
                        if (!ERROR.isEmpty) {
                            THROW();
                        }
                        return [2, resolvedValue];
                }
            });
        }); };
        return checker();
    }
}; };

});

var base = createCommonjsModule(function (module, exports) {
var __assign = (commonjsGlobal && commonjsGlobal.__assign) || function () {
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
var __awaiter = (commonjsGlobal && commonjsGlobal.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (commonjsGlobal && commonjsGlobal.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
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
};
var __read = (commonjsGlobal && commonjsGlobal.__read) || function (o, n) {
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
};
var __spread = (commonjsGlobal && commonjsGlobal.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read(arguments[i]));
    return ar;
};
Object.defineProperty(exports, "__esModule", { value: true });


var ZodTypes;
(function (ZodTypes) {
    ZodTypes["string"] = "string";
    ZodTypes["number"] = "number";
    ZodTypes["bigint"] = "bigint";
    ZodTypes["boolean"] = "boolean";
    ZodTypes["date"] = "date";
    ZodTypes["undefined"] = "undefined";
    ZodTypes["null"] = "null";
    ZodTypes["array"] = "array";
    ZodTypes["object"] = "object";
    ZodTypes["union"] = "union";
    ZodTypes["intersection"] = "intersection";
    ZodTypes["tuple"] = "tuple";
    ZodTypes["record"] = "record";
    ZodTypes["map"] = "map";
    ZodTypes["function"] = "function";
    ZodTypes["lazy"] = "lazy";
    ZodTypes["literal"] = "literal";
    ZodTypes["enum"] = "enum";
    ZodTypes["nativeEnum"] = "nativeEnum";
    ZodTypes["promise"] = "promise";
    ZodTypes["any"] = "any";
    ZodTypes["unknown"] = "unknown";
    ZodTypes["never"] = "never";
    ZodTypes["void"] = "void";
    ZodTypes["transformer"] = "transformer";
    ZodTypes["optional"] = "optional";
    ZodTypes["nullable"] = "nullable";
})(ZodTypes = exports.ZodTypes || (exports.ZodTypes = {}));
exports.inputSchema = function (schema) {
    if (schema instanceof cjs.ZodTransformer) {
        return exports.inputSchema(schema._def.input);
    }
    else {
        return schema;
    }
};
exports.outputSchema = function (schema) {
    if (schema instanceof cjs.ZodTransformer) {
        return exports.inputSchema(schema._def.output);
    }
    else {
        return schema;
    }
};
var ZodType = (function () {
    function ZodType(def) {
        var _this = this;
        this.parse = parser.ZodParser(this);
        this.safeParse = function (data, params) {
            try {
                var parsed = _this.parse(data, params);
                return { success: true, data: parsed };
            }
            catch (err) {
                if (err instanceof cjs.ZodError) {
                    return { success: false, error: err };
                }
                throw err;
            }
        };
        this.parseAsync = function (value, params) { return __awaiter(_this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4, this.parse(value, __assign(__assign({}, params), { async: true }))];
                    case 1: return [2, _a.sent()];
                }
            });
        }); };
        this.safeParseAsync = function (data, params) { return __awaiter(_this, void 0, void 0, function () {
            var parsed, err_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        _a.trys.push([0, 2, , 3]);
                        return [4, this.parseAsync(data, params)];
                    case 1:
                        parsed = _a.sent();
                        return [2, { success: true, data: parsed }];
                    case 2:
                        err_1 = _a.sent();
                        if (err_1 instanceof cjs.ZodError) {
                            return [2, { success: false, error: err_1 }];
                        }
                        throw err_1;
                    case 3: return [2];
                }
            });
        }); };
        this.spa = this.safeParseAsync;
        this.refine = function (check, message) {
            if (message === void 0) { message = 'Invalid value.'; }
            if (typeof message === 'string') {
                return _this._refinement(function (val, ctx) {
                    var result = check(val);
                    var setError = function () {
                        return ctx.addIssue({
                            code: cjs.ZodIssueCode.custom,
                            message: message,
                        });
                    };
                    if (result instanceof Promise) {
                        return result.then(function (data) {
                            if (!data)
                                setError();
                        });
                    }
                    if (!result) {
                        setError();
                        return result;
                    }
                });
            }
            if (typeof message === 'function') {
                return _this._refinement(function (val, ctx) {
                    var result = check(val);
                    var setError = function () {
                        return ctx.addIssue(__assign({ code: cjs.ZodIssueCode.custom }, message(val)));
                    };
                    if (result instanceof Promise) {
                        return result.then(function (data) {
                            if (!data)
                                setError();
                        });
                    }
                    if (!result) {
                        setError();
                        return result;
                    }
                });
            }
            return _this._refinement(function (val, ctx) {
                var result = check(val);
                var setError = function () {
                    return ctx.addIssue(__assign({ code: cjs.ZodIssueCode.custom }, message));
                };
                if (result instanceof Promise) {
                    return result.then(function (data) {
                        if (!data)
                            setError();
                    });
                }
                if (!result) {
                    setError();
                    return result;
                }
            });
        };
        this.refinement = function (check, refinementData) {
            return _this._refinement(function (val, ctx) {
                if (!check(val)) {
                    ctx.addIssue(typeof refinementData === 'function'
                        ? refinementData(val, ctx)
                        : refinementData);
                }
            });
        };
        this._refinement = function (refinement) {
            return new _this.constructor(__assign(__assign({}, _this._def), { checks: __spread((_this._def.checks || []), [{ check: refinement }]) }));
        };
        this.optional = function () { return cjs.ZodOptional.create(_this); };
        this.or = this.optional;
        this.nullable = function () {
            return cjs.ZodNullable.create(_this);
        };
        this.array = function () { return cjs.ZodArray.create(_this); };
        this.isOptional = function () { return _this.safeParse(undefined).success; };
        this.isNullable = function () { return _this.safeParse(null).success; };
        this._def = def;
        this.is = this.is.bind(this);
        this.check = this.check.bind(this);
        this.transform = this.transform.bind(this);
        this.default = this.default.bind(this);
    }
    ZodType.prototype.is = function (u) {
        try {
            this.parse(u);
            return true;
        }
        catch (err) {
            return false;
        }
    };
    ZodType.prototype.check = function (u) {
        try {
            this.parse(u);
            return true;
        }
        catch (err) {
            return false;
        }
    };
    ZodType.prototype.transform = function (input, transformer) {
        if (transformer) {
            return cjs.ZodTransformer.create(this, input, transformer);
        }
        return cjs.ZodTransformer.create(this, exports.outputSchema(this), input);
    };
    ZodType.prototype.default = function (def) {
        var _this = this;
        return cjs.ZodTransformer.create(this.optional(), this, function (x) {
            return x === undefined
                ? typeof def === 'function'
                    ? def(_this)
                    : def
                : x;
        });
    };
    return ZodType;
}());
exports.ZodType = ZodType;

});

var errorUtil_1 = createCommonjsModule(function (module, exports) {
Object.defineProperty(exports, "__esModule", { value: true });
var errorUtil;
(function (errorUtil) {
    errorUtil.errToObj = function (message) { return (typeof message === 'string' ? { message: message } : message || {}); };
})(errorUtil = exports.errorUtil || (exports.errorUtil = {}));

});

var __extends$1 = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __assign = (commonjsGlobal && commonjsGlobal.__assign) || function () {
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
var __importStar = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z = __importStar(base);


var emailRegex = /^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))$/i;
var uuidRegex = /([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}){1}/i;
var ZodString = (function (_super) {
    __extends$1(ZodString, _super);
    function ZodString() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.inputSchema = _this;
        _this.outputSchema = _this;
        _this.toJSON = function () { return _this._def; };
        _this.min = function (minLength, message) {
            return _this.refinement(function (data) { return data.length >= minLength; }, __assign({ code: ZodError_1.ZodIssueCode.too_small, minimum: minLength, type: 'string', inclusive: true }, errorUtil_1.errorUtil.errToObj(message)));
        };
        _this.max = function (maxLength, message) {
            return _this.refinement(function (data) { return data.length <= maxLength; }, __assign({ code: ZodError_1.ZodIssueCode.too_big, maximum: maxLength, type: 'string', inclusive: true }, errorUtil_1.errorUtil.errToObj(message)));
        };
        _this._regex = function (regex, validation, message) {
            return _this.refinement(function (data) { return regex.test(data); }, __assign({ validation: validation, code: ZodError_1.ZodIssueCode.invalid_string }, errorUtil_1.errorUtil.errToObj(message)));
        };
        _this.email = function (message) {
            return _this._regex(emailRegex, 'email', message);
        };
        _this.url = function (message) {
            return _this.refinement(function (data) {
                try {
                    new URL(data);
                    return true;
                }
                catch (_a) {
                    return false;
                }
            }, __assign({ code: ZodError_1.ZodIssueCode.invalid_string, validation: 'url' }, errorUtil_1.errorUtil.errToObj(message)));
        };
        _this.uuid = function (message) {
            return _this._regex(uuidRegex, 'uuid', message);
        };
        _this.regex = function (regexp, message) {
            return _this._regex(regexp, 'regex', message);
        };
        _this.nonempty = function (message) {
            return _this.min(1, errorUtil_1.errorUtil.errToObj(message));
        };
        return _this;
    }
    ZodString.prototype.length = function (len, message) {
        return this.min(len, message).max(len, message);
    };
    ZodString.create = function () {
        return new ZodString({
            t: z.ZodTypes.string,
            validation: {},
        });
    };
    return ZodString;
}(z.ZodType));
var ZodString_1 = ZodString;


var string = /*#__PURE__*/Object.defineProperty({
	ZodString: ZodString_1
}, '__esModule', {value: true});

var __extends$2 = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __assign$1 = (commonjsGlobal && commonjsGlobal.__assign) || function () {
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
var __importStar$1 = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$1 = __importStar$1(base);


var ZodNumber = (function (_super) {
    __extends$2(ZodNumber, _super);
    function ZodNumber() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        _this.min = function (minimum, message) {
            return _this.refinement(function (data) { return data >= minimum; }, __assign$1({ code: ZodError_1.ZodIssueCode.too_small, minimum: minimum, type: 'number', inclusive: true }, errorUtil_1.errorUtil.errToObj(message)));
        };
        _this.max = function (maximum, message) {
            return _this.refinement(function (data) { return data <= maximum; }, __assign$1({ code: ZodError_1.ZodIssueCode.too_big, maximum: maximum, type: 'number', inclusive: true }, errorUtil_1.errorUtil.errToObj(message)));
        };
        _this.int = function (message) {
            return _this.refinement(function (data) { return Number.isInteger(data); }, __assign$1({ code: ZodError_1.ZodIssueCode.invalid_type, expected: 'integer', received: 'number' }, errorUtil_1.errorUtil.errToObj(message)));
        };
        _this.positive = function (message) {
            return _this.refinement(function (data) { return data > 0; }, __assign$1({ code: ZodError_1.ZodIssueCode.too_small, minimum: 0, type: 'number', inclusive: false }, errorUtil_1.errorUtil.errToObj(message)));
        };
        _this.negative = function (message) {
            return _this.refinement(function (data) { return data < 0; }, __assign$1({ code: ZodError_1.ZodIssueCode.too_big, maximum: 0, type: 'number', inclusive: false }, errorUtil_1.errorUtil.errToObj(message)));
        };
        _this.nonpositive = function (message) {
            return _this.refinement(function (data) { return data <= 0; }, __assign$1({ code: ZodError_1.ZodIssueCode.too_big, maximum: 0, type: 'number', inclusive: true }, errorUtil_1.errorUtil.errToObj(message)));
        };
        _this.nonnegative = function (message) {
            return _this.refinement(function (data) { return data >= 0; }, __assign$1({ code: ZodError_1.ZodIssueCode.too_small, minimum: 0, type: 'number', inclusive: true }, errorUtil_1.errorUtil.errToObj(message)));
        };
        return _this;
    }
    ZodNumber.create = function () {
        return new ZodNumber({
            t: z$1.ZodTypes.number,
        });
    };
    return ZodNumber;
}(z$1.ZodType));
var ZodNumber_1 = ZodNumber;


var number = /*#__PURE__*/Object.defineProperty({
	ZodNumber: ZodNumber_1
}, '__esModule', {value: true});

var __extends$3 = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$2 = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$2 = __importStar$2(base);
var ZodBigInt = (function (_super) {
    __extends$3(ZodBigInt, _super);
    function ZodBigInt() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodBigInt.create = function () {
        return new ZodBigInt({
            t: z$2.ZodTypes.bigint,
        });
    };
    return ZodBigInt;
}(z$2.ZodType));
var ZodBigInt_1 = ZodBigInt;


var bigint = /*#__PURE__*/Object.defineProperty({
	ZodBigInt: ZodBigInt_1
}, '__esModule', {value: true});

var __extends$4 = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$3 = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$3 = __importStar$3(base);
var ZodBoolean = (function (_super) {
    __extends$4(ZodBoolean, _super);
    function ZodBoolean() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodBoolean.create = function () {
        return new ZodBoolean({
            t: z$3.ZodTypes.boolean,
        });
    };
    return ZodBoolean;
}(z$3.ZodType));
var ZodBoolean_1 = ZodBoolean;


var boolean = /*#__PURE__*/Object.defineProperty({
	ZodBoolean: ZodBoolean_1
}, '__esModule', {value: true});

var __extends$5 = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$4 = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$4 = __importStar$4(base);
var ZodDate = (function (_super) {
    __extends$5(ZodDate, _super);
    function ZodDate() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodDate.create = function () {
        return new ZodDate({
            t: z$4.ZodTypes.date,
        });
    };
    return ZodDate;
}(z$4.ZodType));
var ZodDate_1 = ZodDate;


var date = /*#__PURE__*/Object.defineProperty({
	ZodDate: ZodDate_1
}, '__esModule', {value: true});

var __extends$6 = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$5 = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$5 = __importStar$5(base);
var ZodUndefined = (function (_super) {
    __extends$6(ZodUndefined, _super);
    function ZodUndefined() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodUndefined.create = function () {
        return new ZodUndefined({
            t: z$5.ZodTypes.undefined,
        });
    };
    return ZodUndefined;
}(z$5.ZodType));
var ZodUndefined_1 = ZodUndefined;


var _undefined = /*#__PURE__*/Object.defineProperty({
	ZodUndefined: ZodUndefined_1
}, '__esModule', {value: true});

var __extends$7 = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$6 = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$6 = __importStar$6(base);
var ZodNull = (function (_super) {
    __extends$7(ZodNull, _super);
    function ZodNull() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodNull.create = function () {
        return new ZodNull({
            t: z$6.ZodTypes.null,
        });
    };
    return ZodNull;
}(z$6.ZodType));
var ZodNull_1 = ZodNull;


var _null = /*#__PURE__*/Object.defineProperty({
	ZodNull: ZodNull_1
}, '__esModule', {value: true});

var __extends$8 = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$7 = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$7 = __importStar$7(base);
var ZodAny = (function (_super) {
    __extends$8(ZodAny, _super);
    function ZodAny() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodAny.create = function () {
        return new ZodAny({
            t: z$7.ZodTypes.any,
        });
    };
    return ZodAny;
}(z$7.ZodType));
var ZodAny_1 = ZodAny;


var any = /*#__PURE__*/Object.defineProperty({
	ZodAny: ZodAny_1
}, '__esModule', {value: true});

var __extends$9 = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$8 = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$8 = __importStar$8(base);
var ZodUnknown = (function (_super) {
    __extends$9(ZodUnknown, _super);
    function ZodUnknown() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodUnknown.create = function () {
        return new ZodUnknown({
            t: z$8.ZodTypes.unknown,
        });
    };
    return ZodUnknown;
}(z$8.ZodType));
var ZodUnknown_1 = ZodUnknown;


var unknown = /*#__PURE__*/Object.defineProperty({
	ZodUnknown: ZodUnknown_1
}, '__esModule', {value: true});

var __extends$a = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$9 = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$9 = __importStar$9(base);
var ZodNever = (function (_super) {
    __extends$a(ZodNever, _super);
    function ZodNever() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodNever.create = function () {
        return new ZodNever({
            t: z$9.ZodTypes.never,
        });
    };
    return ZodNever;
}(z$9.ZodType));
var ZodNever_1 = ZodNever;


var never = /*#__PURE__*/Object.defineProperty({
	ZodNever: ZodNever_1
}, '__esModule', {value: true});

var __extends$b = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$a = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$a = __importStar$a(base);
var ZodVoid = (function (_super) {
    __extends$b(ZodVoid, _super);
    function ZodVoid() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodVoid.create = function () {
        return new ZodVoid({
            t: z$a.ZodTypes.void,
        });
    };
    return ZodVoid;
}(z$a.ZodType));
var ZodVoid_1 = ZodVoid;


var _void = /*#__PURE__*/Object.defineProperty({
	ZodVoid: ZodVoid_1
}, '__esModule', {value: true});

var __extends$c = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __assign$2 = (commonjsGlobal && commonjsGlobal.__assign) || function () {
    __assign$2 = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign$2.apply(this, arguments);
};
var __importStar$b = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$b = __importStar$b(base);

var ZodArray = (function (_super) {
    __extends$c(ZodArray, _super);
    function ZodArray() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () {
            return {
                t: _this._def.t,
                nonempty: _this._def.nonempty,
                type: _this._def.type.toJSON(),
            };
        };
        _this.min = function (minLength, message) {
            return _this.refinement(function (data) { return data.length >= minLength; }, __assign$2({ code: ZodError_1.ZodIssueCode.too_small, type: 'array', inclusive: true, minimum: minLength }, (typeof message === 'string' ? { message: message } : message)));
        };
        _this.max = function (maxLength, message) {
            return _this.refinement(function (data) { return data.length <= maxLength; }, __assign$2({ code: ZodError_1.ZodIssueCode.too_big, type: 'array', inclusive: true, maximum: maxLength }, (typeof message === 'string' ? { message: message } : message)));
        };
        _this.length = function (len, message) {
            return _this.min(len, { message: message }).max(len, { message: message });
        };
        _this.nonempty = function () {
            return new ZodNonEmptyArray(__assign$2(__assign$2({}, _this._def), { nonempty: true }));
        };
        return _this;
    }
    Object.defineProperty(ZodArray.prototype, "element", {
        get: function () {
            return this._def.type;
        },
        enumerable: true,
        configurable: true
    });
    ZodArray.create = function (schema) {
        return new ZodArray({
            t: z$b.ZodTypes.array,
            type: schema,
            nonempty: false,
        });
    };
    return ZodArray;
}(z$b.ZodType));
var ZodArray_1 = ZodArray;
var ZodNonEmptyArray = (function (_super) {
    __extends$c(ZodNonEmptyArray, _super);
    function ZodNonEmptyArray() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () {
            return {
                t: _this._def.t,
                type: _this._def.type.toJSON(),
            };
        };
        _this.min = function (minLength, message) {
            return _this.refinement(function (data) { return data.length >= minLength; }, __assign$2({ code: ZodError_1.ZodIssueCode.too_small, minimum: minLength, type: 'array', inclusive: true }, (typeof message === 'string' ? { message: message } : message)));
        };
        _this.max = function (maxLength, message) {
            return _this.refinement(function (data) { return data.length <= maxLength; }, __assign$2({ code: ZodError_1.ZodIssueCode.too_big, maximum: maxLength, type: 'array', inclusive: true }, (typeof message === 'string' ? { message: message } : message)));
        };
        _this.length = function (len, message) {
            return _this.min(len, { message: message }).max(len, { message: message });
        };
        return _this;
    }
    return ZodNonEmptyArray;
}(z$b.ZodType));
var ZodNonEmptyArray_1 = ZodNonEmptyArray;


var array = /*#__PURE__*/Object.defineProperty({
	ZodArray: ZodArray_1,
	ZodNonEmptyArray: ZodNonEmptyArray_1
}, '__esModule', {value: true});

var __extends$d = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$c = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$c = __importStar$c(base);
var ZodIntersection = (function (_super) {
    __extends$d(ZodIntersection, _super);
    function ZodIntersection() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            left: _this._def.left.toJSON(),
            right: _this._def.right.toJSON(),
        }); };
        return _this;
    }
    ZodIntersection.create = function (left, right) {
        return new ZodIntersection({
            t: z$c.ZodTypes.intersection,
            left: left,
            right: right,
        });
    };
    return ZodIntersection;
}(z$c.ZodType));
var ZodIntersection_1 = ZodIntersection;


var intersection = /*#__PURE__*/Object.defineProperty({
	ZodIntersection: ZodIntersection_1
}, '__esModule', {value: true});

var objectUtil_1 = createCommonjsModule(function (module, exports) {
var __assign = (commonjsGlobal && commonjsGlobal.__assign) || function () {
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
var __values = (commonjsGlobal && commonjsGlobal.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
var __read = (commonjsGlobal && commonjsGlobal.__read) || function (o, n) {
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
};
var __spread = (commonjsGlobal && commonjsGlobal.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read(arguments[i]));
    return ar;
};
Object.defineProperty(exports, "__esModule", { value: true });



var objectUtil;
(function (objectUtil) {
    objectUtil.mergeShapes = function (first, second) {
        var e_1, _a;
        var firstKeys = Object.keys(first);
        var secondKeys = Object.keys(second);
        var sharedKeys = firstKeys.filter(function (k) { return secondKeys.indexOf(k) !== -1; });
        var sharedShape = {};
        try {
            for (var sharedKeys_1 = __values(sharedKeys), sharedKeys_1_1 = sharedKeys_1.next(); !sharedKeys_1_1.done; sharedKeys_1_1 = sharedKeys_1.next()) {
                var k = sharedKeys_1_1.value;
                sharedShape[k] = intersection.ZodIntersection.create(first[k], second[k]);
            }
        }
        catch (e_1_1) { e_1 = { error: e_1_1 }; }
        finally {
            try {
                if (sharedKeys_1_1 && !sharedKeys_1_1.done && (_a = sharedKeys_1.return)) _a.call(sharedKeys_1);
            }
            finally { if (e_1) throw e_1.error; }
        }
        return __assign(__assign(__assign({}, first), second), sharedShape);
    };
    objectUtil.mergeObjects = function (first) { return function (second) {
        var mergedShape = objectUtil.mergeShapes(first._def.shape(), second._def.shape());
        var merged = new object.ZodObject({
            t: base.ZodTypes.object,
            checks: __spread((first._def.checks || []), (second._def.checks || [])),
            unknownKeys: first._def.unknownKeys,
            catchall: first._def.catchall,
            shape: function () { return mergedShape; },
        });
        return merged;
    }; };
})(objectUtil = exports.objectUtil || (exports.objectUtil = {}));

});

var isScalar = createCommonjsModule(function (module, exports) {
Object.defineProperty(exports, "__esModule", { value: true });


exports.isScalar = function (schema, params) {
    if (params === void 0) { params = { root: true }; }
    var def = schema._def;
    var returnValue = false;
    switch (def.t) {
        case base.ZodTypes.string:
            returnValue = true;
            break;
        case base.ZodTypes.number:
            returnValue = true;
            break;
        case base.ZodTypes.bigint:
            returnValue = true;
            break;
        case base.ZodTypes.boolean:
            returnValue = true;
            break;
        case base.ZodTypes.undefined:
            returnValue = true;
            break;
        case base.ZodTypes.null:
            returnValue = true;
            break;
        case base.ZodTypes.any:
            returnValue = false;
            break;
        case base.ZodTypes.unknown:
            returnValue = false;
            break;
        case base.ZodTypes.never:
            returnValue = false;
            break;
        case base.ZodTypes.void:
            returnValue = false;
            break;
        case base.ZodTypes.array:
            if (params.root === false)
                return false;
            returnValue = exports.isScalar(def.type, { root: false });
            break;
        case base.ZodTypes.object:
            returnValue = false;
            break;
        case base.ZodTypes.union:
            returnValue = def.options.every(function (x) { return exports.isScalar(x); });
            break;
        case base.ZodTypes.intersection:
            returnValue = exports.isScalar(def.left) && exports.isScalar(def.right);
            break;
        case base.ZodTypes.tuple:
            returnValue = def.items.every(function (x) { return exports.isScalar(x, { root: false }); });
            break;
        case base.ZodTypes.lazy:
            returnValue = exports.isScalar(def.getter());
            break;
        case base.ZodTypes.literal:
            returnValue = true;
            break;
        case base.ZodTypes.enum:
            returnValue = true;
            break;
        case base.ZodTypes.nativeEnum:
            returnValue = true;
            break;
        case base.ZodTypes.function:
            returnValue = false;
            break;
        case base.ZodTypes.record:
            returnValue = false;
            break;
        case base.ZodTypes.map:
            returnValue = false;
            break;
        case base.ZodTypes.date:
            returnValue = true;
            break;
        case base.ZodTypes.promise:
            returnValue = false;
            break;
        case base.ZodTypes.transformer:
            returnValue = exports.isScalar(def.output);
            break;
        case base.ZodTypes.optional:
            returnValue = exports.isScalar(def.innerType);
            break;
        case base.ZodTypes.nullable:
            returnValue = exports.isScalar(def.innerType);
            break;
        default:
            util_1.util.assertNever(def);
    }
    return returnValue;
};

});

var __extends$e = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __assign$3 = (commonjsGlobal && commonjsGlobal.__assign) || function () {
    __assign$3 = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign$3.apply(this, arguments);
};
var __read$1 = (commonjsGlobal && commonjsGlobal.__read) || function (o, n) {
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
};
var __spread$1 = (commonjsGlobal && commonjsGlobal.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read$1(arguments[i]));
    return ar;
};
var __importStar$d = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$d = __importStar$d(base);



var AugmentFactory = function (def) { return function (augmentation) {
    return new ZodObject(__assign$3(__assign$3({}, def), { shape: function () { return (__assign$3(__assign$3({}, def.shape()), augmentation)); } }));
}; };
var objectDefToJson = function (def) { return ({
    t: def.t,
    shape: Object.assign.apply(Object, __spread$1([{}], Object.keys(def.shape()).map(function (k) {
        var _a;
        return (_a = {},
            _a[k] = def.shape()[k].toJSON(),
            _a);
    }))),
}); };
var ZodObject = (function (_super) {
    __extends$e(ZodObject, _super);
    function ZodObject() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return objectDefToJson(_this._def); };
        _this.strict = function () {
            return new ZodObject(__assign$3(__assign$3({}, _this._def), { unknownKeys: 'strict' }));
        };
        _this.strip = function () {
            return new ZodObject(__assign$3(__assign$3({}, _this._def), { unknownKeys: 'strip' }));
        };
        _this.passthrough = function () {
            return new ZodObject(__assign$3(__assign$3({}, _this._def), { unknownKeys: 'passthrough' }));
        };
        _this.nonstrict = _this.passthrough;
        _this.augment = AugmentFactory(_this._def);
        _this.extend = AugmentFactory(_this._def);
        _this.setKey = function (key, schema) {
            var _a;
            return _this.augment((_a = {}, _a[key] = schema, _a));
        };
        _this.merge = objectUtil_1.objectUtil.mergeObjects(_this);
        _this.catchall = function (index) {
            return new ZodObject(__assign$3(__assign$3({}, _this._def), { catchall: index }));
        };
        _this.pick = function (mask) {
            var shape = {};
            Object.keys(mask).map(function (key) {
                shape[key] = _this.shape[key];
            });
            return new ZodObject(__assign$3(__assign$3({}, _this._def), { shape: function () { return shape; } }));
        };
        _this.omit = function (mask) {
            var shape = {};
            Object.keys(_this.shape).map(function (key) {
                if (Object.keys(mask).indexOf(key) === -1) {
                    shape[key] = _this.shape[key];
                }
            });
            return new ZodObject(__assign$3(__assign$3({}, _this._def), { shape: function () { return shape; } }));
        };
        _this.partial = function () {
            var newShape = {};
            for (var key in _this.shape) {
                var fieldSchema = _this.shape[key];
                newShape[key] = fieldSchema.isOptional()
                    ? fieldSchema
                    : fieldSchema.optional();
            }
            return new ZodObject(__assign$3(__assign$3({}, _this._def), { shape: function () { return newShape; } }));
        };
        _this.primitives = function () {
            var newShape = {};
            for (var key in _this.shape) {
                if (isScalar.isScalar(_this.shape[key])) {
                    newShape[key] = _this.shape[key];
                }
            }
            return new ZodObject(__assign$3(__assign$3({}, _this._def), { shape: function () { return newShape; } }));
        };
        _this.nonprimitives = function () {
            var newShape = {};
            for (var key in _this.shape) {
                if (!isScalar.isScalar(_this.shape[key])) {
                    newShape[key] = _this.shape[key];
                }
            }
            return new ZodObject(__assign$3(__assign$3({}, _this._def), { shape: function () { return newShape; } }));
        };
        _this.deepPartial = function () {
            var newShape = {};
            for (var key in _this.shape) {
                var fieldSchema = _this.shape[key];
                if (fieldSchema instanceof ZodObject) {
                    newShape[key] = fieldSchema.isOptional()
                        ? fieldSchema
                        : fieldSchema.deepPartial().optional();
                }
                else {
                    newShape[key] = fieldSchema.isOptional()
                        ? fieldSchema
                        : fieldSchema.optional();
                }
            }
            return new ZodObject(__assign$3(__assign$3({}, _this._def), { shape: function () { return newShape; } }));
        };
        return _this;
    }
    Object.defineProperty(ZodObject.prototype, "shape", {
        get: function () {
            return this._def.shape();
        },
        enumerable: true,
        configurable: true
    });
    ZodObject.create = function (shape) {
        return new ZodObject({
            t: z$d.ZodTypes.object,
            shape: function () { return shape; },
            unknownKeys: 'strip',
            catchall: cjs.ZodNever.create(),
        });
    };
    ZodObject.lazycreate = function (shape) {
        return new ZodObject({
            t: z$d.ZodTypes.object,
            shape: shape,
            unknownKeys: 'strip',
            catchall: cjs.ZodNever.create(),
        });
    };
    return ZodObject;
}(z$d.ZodType));
var ZodObject_1 = ZodObject;


var object = /*#__PURE__*/Object.defineProperty({
	ZodObject: ZodObject_1
}, '__esModule', {value: true});

var __extends$f = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$e = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$e = __importStar$e(base);
var ZodUnion = (function (_super) {
    __extends$f(ZodUnion, _super);
    function ZodUnion() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            options: _this._def.options.map(function (x) { return x.toJSON(); }),
        }); };
        return _this;
    }
    Object.defineProperty(ZodUnion.prototype, "options", {
        get: function () {
            return this._def.options;
        },
        enumerable: true,
        configurable: true
    });
    ZodUnion.create = function (types) {
        return new ZodUnion({
            t: z$e.ZodTypes.union,
            options: types,
        });
    };
    return ZodUnion;
}(z$e.ZodType));
var ZodUnion_1 = ZodUnion;


var union = /*#__PURE__*/Object.defineProperty({
	ZodUnion: ZodUnion_1
}, '__esModule', {value: true});

var __extends$g = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$f = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$f = __importStar$f(base);
var ZodTuple = (function (_super) {
    __extends$g(ZodTuple, _super);
    function ZodTuple() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            items: _this._def.items.map(function (item) { return item.toJSON(); }),
        }); };
        return _this;
    }
    Object.defineProperty(ZodTuple.prototype, "items", {
        get: function () {
            return this._def.items;
        },
        enumerable: true,
        configurable: true
    });
    ZodTuple.create = function (schemas) {
        return new ZodTuple({
            t: z$f.ZodTypes.tuple,
            items: schemas,
        });
    };
    return ZodTuple;
}(z$f.ZodType));
var ZodTuple_1 = ZodTuple;


var tuple = /*#__PURE__*/Object.defineProperty({
	ZodTuple: ZodTuple_1
}, '__esModule', {value: true});

var __extends$h = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$g = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$g = __importStar$g(base);
var ZodRecord = (function (_super) {
    __extends$h(ZodRecord, _super);
    function ZodRecord() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            valueType: _this._def.valueType.toJSON(),
        }); };
        return _this;
    }
    ZodRecord.create = function (valueType) {
        return new ZodRecord({
            t: z$g.ZodTypes.record,
            valueType: valueType,
        });
    };
    return ZodRecord;
}(z$g.ZodType));
var ZodRecord_1 = ZodRecord;


var record = /*#__PURE__*/Object.defineProperty({
	ZodRecord: ZodRecord_1
}, '__esModule', {value: true});

var __extends$i = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$h = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$h = __importStar$h(base);
var ZodMap = (function (_super) {
    __extends$i(ZodMap, _super);
    function ZodMap() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            valueType: _this._def.valueType.toJSON(),
            keyType: _this._def.keyType.toJSON(),
        }); };
        return _this;
    }
    ZodMap.create = function (keyType, valueType) {
        return new ZodMap({
            t: z$h.ZodTypes.map,
            valueType: valueType,
            keyType: keyType,
        });
    };
    return ZodMap;
}(z$h.ZodType));
var ZodMap_1 = ZodMap;


var map = /*#__PURE__*/Object.defineProperty({
	ZodMap: ZodMap_1
}, '__esModule', {value: true});

var __extends$j = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __assign$4 = (commonjsGlobal && commonjsGlobal.__assign) || function () {
    __assign$4 = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign$4.apply(this, arguments);
};
var __importStar$i = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$i = __importStar$i(base);


var ZodFunction = (function (_super) {
    __extends$j(ZodFunction, _super);
    function ZodFunction() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.args = function () {
            var items = [];
            for (var _i = 0; _i < arguments.length; _i++) {
                items[_i] = arguments[_i];
            }
            return new ZodFunction(__assign$4(__assign$4({}, _this._def), { args: tuple.ZodTuple.create(items) }));
        };
        _this.returns = function (returnType) {
            return new ZodFunction(__assign$4(__assign$4({}, _this._def), { returns: returnType }));
        };
        _this.implement = function (func) {
            var validatedFunc = _this.parse(func);
            return validatedFunc;
        };
        _this.validate = _this.implement;
        _this.toJSON = function () {
            return {
                t: _this._def.t,
                args: _this._def.args.toJSON(),
                returns: _this._def.returns.toJSON(),
            };
        };
        return _this;
    }
    ZodFunction.create = function (args, returns) {
        return new ZodFunction({
            t: z$i.ZodTypes.function,
            args: args || tuple.ZodTuple.create([]),
            returns: returns || unknown.ZodUnknown.create(),
        });
    };
    return ZodFunction;
}(z$i.ZodType));
var ZodFunction_1 = ZodFunction;


var _function = /*#__PURE__*/Object.defineProperty({
	ZodFunction: ZodFunction_1
}, '__esModule', {value: true});

var __extends$k = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$j = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$j = __importStar$j(base);
var ZodLazy = (function (_super) {
    __extends$k(ZodLazy, _super);
    function ZodLazy() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () {
            throw new Error("Can't JSONify recursive structure");
        };
        return _this;
    }
    Object.defineProperty(ZodLazy.prototype, "schema", {
        get: function () {
            return this._def.getter();
        },
        enumerable: true,
        configurable: true
    });
    ZodLazy.create = function (getter) {
        return new ZodLazy({
            t: z$j.ZodTypes.lazy,
            getter: getter,
        });
    };
    return ZodLazy;
}(z$j.ZodType));
var ZodLazy_1 = ZodLazy;


var lazy = /*#__PURE__*/Object.defineProperty({
	ZodLazy: ZodLazy_1
}, '__esModule', {value: true});

var __extends$l = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$k = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$k = __importStar$k(base);
var ZodLiteral = (function (_super) {
    __extends$l(ZodLiteral, _super);
    function ZodLiteral() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodLiteral.create = function (value) {
        return new ZodLiteral({
            t: z$k.ZodTypes.literal,
            value: value,
        });
    };
    return ZodLiteral;
}(z$k.ZodType));
var ZodLiteral_1 = ZodLiteral;


var literal = /*#__PURE__*/Object.defineProperty({
	ZodLiteral: ZodLiteral_1
}, '__esModule', {value: true});

var __extends$m = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __values$1 = (commonjsGlobal && commonjsGlobal.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
var __importStar$l = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$l = __importStar$l(base);
var ZodEnum = (function (_super) {
    __extends$m(ZodEnum, _super);
    function ZodEnum() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    Object.defineProperty(ZodEnum.prototype, "options", {
        get: function () {
            return this._def.values;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodEnum.prototype, "enum", {
        get: function () {
            var e_1, _a;
            var enumValues = {};
            try {
                for (var _b = __values$1(this._def.values), _c = _b.next(); !_c.done; _c = _b.next()) {
                    var val = _c.value;
                    enumValues[val] = val;
                }
            }
            catch (e_1_1) { e_1 = { error: e_1_1 }; }
            finally {
                try {
                    if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
                }
                finally { if (e_1) throw e_1.error; }
            }
            return enumValues;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodEnum.prototype, "Values", {
        get: function () {
            var e_2, _a;
            var enumValues = {};
            try {
                for (var _b = __values$1(this._def.values), _c = _b.next(); !_c.done; _c = _b.next()) {
                    var val = _c.value;
                    enumValues[val] = val;
                }
            }
            catch (e_2_1) { e_2 = { error: e_2_1 }; }
            finally {
                try {
                    if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
                }
                finally { if (e_2) throw e_2.error; }
            }
            return enumValues;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodEnum.prototype, "Enum", {
        get: function () {
            var e_3, _a;
            var enumValues = {};
            try {
                for (var _b = __values$1(this._def.values), _c = _b.next(); !_c.done; _c = _b.next()) {
                    var val = _c.value;
                    enumValues[val] = val;
                }
            }
            catch (e_3_1) { e_3 = { error: e_3_1 }; }
            finally {
                try {
                    if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
                }
                finally { if (e_3) throw e_3.error; }
            }
            return enumValues;
        },
        enumerable: true,
        configurable: true
    });
    ZodEnum.create = function (values) {
        return new ZodEnum({
            t: z$l.ZodTypes.enum,
            values: values,
        });
    };
    return ZodEnum;
}(z$l.ZodType));
var ZodEnum_1 = ZodEnum;


var _enum = /*#__PURE__*/Object.defineProperty({
	ZodEnum: ZodEnum_1
}, '__esModule', {value: true});

var __extends$n = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$m = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$m = __importStar$m(base);
var ZodNativeEnum = (function (_super) {
    __extends$n(ZodNativeEnum, _super);
    function ZodNativeEnum() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodNativeEnum.create = function (values) {
        return new ZodNativeEnum({
            t: z$m.ZodTypes.nativeEnum,
            values: values,
        });
    };
    return ZodNativeEnum;
}(z$m.ZodType));
var ZodNativeEnum_1 = ZodNativeEnum;


var nativeEnum = /*#__PURE__*/Object.defineProperty({
	ZodNativeEnum: ZodNativeEnum_1
}, '__esModule', {value: true});

var __extends$o = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$n = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$n = __importStar$n(base);
var ZodPromise = (function (_super) {
    __extends$o(ZodPromise, _super);
    function ZodPromise() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () {
            return {
                t: _this._def.t,
                type: _this._def.type.toJSON(),
            };
        };
        return _this;
    }
    ZodPromise.create = function (schema) {
        return new ZodPromise({
            t: z$n.ZodTypes.promise,
            type: schema,
        });
    };
    return ZodPromise;
}(z$n.ZodType));
var ZodPromise_1 = ZodPromise;


var promise = /*#__PURE__*/Object.defineProperty({
	ZodPromise: ZodPromise_1
}, '__esModule', {value: true});

var __extends$p = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$o = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$o = __importStar$o(base);
var ZodTransformer = (function (_super) {
    __extends$p(ZodTransformer, _super);
    function ZodTransformer() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            left: _this._def.input.toJSON(),
            right: _this._def.output.toJSON(),
        }); };
        return _this;
    }
    Object.defineProperty(ZodTransformer.prototype, "output", {
        get: function () {
            return this._def.output;
        },
        enumerable: true,
        configurable: true
    });
    ZodTransformer.create = function (input, output, transformer) {
        return new ZodTransformer({
            t: z$o.ZodTypes.transformer,
            input: input,
            output: output,
            transformer: transformer,
        });
    };
    ZodTransformer.fromSchema = function (input) {
        return new ZodTransformer({
            t: z$o.ZodTypes.transformer,
            input: input,
            output: input,
            transformer: function (x) { return x; },
        });
    };
    return ZodTransformer;
}(z$o.ZodType));
var ZodTransformer_1 = ZodTransformer;


var transformer = /*#__PURE__*/Object.defineProperty({
	ZodTransformer: ZodTransformer_1
}, '__esModule', {value: true});

var __extends$q = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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


var ZodOptional = (function (_super) {
    __extends$q(ZodOptional, _super);
    function ZodOptional() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            innerType: _this._def.innerType.toJSON(),
        }); };
        return _this;
    }
    ZodOptional.create = function (type) {
        if (type instanceof ZodOptional)
            return type;
        return new ZodOptional({
            t: base.ZodTypes.optional,
            innerType: type,
        });
    };
    return ZodOptional;
}(base.ZodType));
var ZodOptional_1 = ZodOptional;


var optional = /*#__PURE__*/Object.defineProperty({
	ZodOptional: ZodOptional_1
}, '__esModule', {value: true});

var __extends$r = (commonjsGlobal && commonjsGlobal.__extends) || (function () {
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
var __importStar$p = (commonjsGlobal && commonjsGlobal.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$p = __importStar$p(base);
var ZodNullable = (function (_super) {
    __extends$r(ZodNullable, _super);
    function ZodNullable() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            innerType: _this._def.innerType.toJSON(),
        }); };
        return _this;
    }
    ZodNullable.create = function (type) {
        if (type instanceof ZodNullable)
            return type;
        return new ZodNullable({
            t: z$p.ZodTypes.nullable,
            innerType: type,
        });
    };
    return ZodNullable;
}(z$p.ZodType));
var ZodNullable_1 = ZodNullable;


var nullable = /*#__PURE__*/Object.defineProperty({
	ZodNullable: ZodNullable_1
}, '__esModule', {value: true});

var __values$2 = (commonjsGlobal && commonjsGlobal.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};



var isOptional = function (schema) {
    return schema.isOptional();
};
var ZodCodeGenerator = (function () {
    function ZodCodeGenerator() {
        var _this = this;
        this.seen = [];
        this.serial = 0;
        this.randomId = function () {
            return "IZod" + _this.serial++;
        };
        this.findBySchema = function (schema) {
            return _this.seen.find(function (s) { return s.schema === schema; });
        };
        this.findById = function (id) {
            var found = _this.seen.find(function (s) { return s.id === id; });
            if (!found)
                throw new Error("Unfound ID: " + id);
            return found;
        };
        this.dump = function () {
            return "\ntype Identity<T> = T;\n\n" + _this.seen
                .map(function (item) { return "type " + item.id + " = Identity<" + item.type + ">;"; })
                .join('\n\n') + "\n";
        };
        this.setType = function (id, type) {
            var found = _this.findById(id);
            found.type = type;
            return found;
        };
        this.generate = function (schema) {
            var e_1, _a, e_2, _b;
            var found = _this.findBySchema(schema);
            if (found)
                return found;
            var def = schema._def;
            var id = _this.randomId();
            var ty = {
                schema: schema,
                id: id,
                type: "__INCOMPLETE__",
            };
            _this.seen.push(ty);
            switch (def.t) {
                case base.ZodTypes.string:
                    return _this.setType(id, "string");
                case base.ZodTypes.number:
                    return _this.setType(id, "number");
                case base.ZodTypes.bigint:
                    return _this.setType(id, "bigint");
                case base.ZodTypes.boolean:
                    return _this.setType(id, "boolean");
                case base.ZodTypes.date:
                    return _this.setType(id, "Date");
                case base.ZodTypes.undefined:
                    return _this.setType(id, "undefined");
                case base.ZodTypes.null:
                    return _this.setType(id, "null");
                case base.ZodTypes.any:
                    return _this.setType(id, "any");
                case base.ZodTypes.unknown:
                    return _this.setType(id, "unknown");
                case base.ZodTypes.never:
                    return _this.setType(id, "never");
                case base.ZodTypes.void:
                    return _this.setType(id, "void");
                case base.ZodTypes.literal:
                    var val = def.value;
                    var literalType = typeof val === 'string' ? "\"" + val + "\"" : "" + val;
                    return _this.setType(id, literalType);
                case base.ZodTypes.enum:
                    return _this.setType(id, def.values.map(function (v) { return "\"" + v + "\""; }).join(' | '));
                case base.ZodTypes.object:
                    var objectLines = [];
                    var shape = def.shape();
                    for (var key in shape) {
                        var childSchema = shape[key];
                        var childType = _this.generate(childSchema);
                        var OPTKEY = isOptional(childSchema) ? '?' : '';
                        objectLines.push("" + key + OPTKEY + ": " + childType.id);
                    }
                    var baseStruct = "{\n" + objectLines
                        .map(function (line) { return "  " + line + ";"; })
                        .join('\n') + "\n}";
                    _this.setType(id, "" + baseStruct);
                    break;
                case base.ZodTypes.tuple:
                    var tupleLines = [];
                    try {
                        for (var _c = __values$2(def.items), _d = _c.next(); !_d.done; _d = _c.next()) {
                            var elSchema = _d.value;
                            var elType = _this.generate(elSchema);
                            tupleLines.push(elType.id);
                        }
                    }
                    catch (e_1_1) { e_1 = { error: e_1_1 }; }
                    finally {
                        try {
                            if (_d && !_d.done && (_a = _c.return)) _a.call(_c);
                        }
                        finally { if (e_1) throw e_1.error; }
                    }
                    var baseTuple = "[\n" + tupleLines
                        .map(function (line) { return "  " + line + ","; })
                        .join('\n') + "\n]";
                    return _this.setType(id, "" + baseTuple);
                case base.ZodTypes.array:
                    return _this.setType(id, _this.generate(def.type).id + "[]");
                case base.ZodTypes.function:
                    var args = _this.generate(def.args);
                    var returns = _this.generate(def.returns);
                    return _this.setType(id, "(...args: " + args.id + ")=>" + returns.id);
                case base.ZodTypes.promise:
                    var promValue = _this.generate(def.type);
                    return _this.setType(id, "Promise<" + promValue.id + ">");
                case base.ZodTypes.union:
                    var unionLines = [];
                    try {
                        for (var _e = __values$2(def.options), _f = _e.next(); !_f.done; _f = _e.next()) {
                            var elSchema = _f.value;
                            var elType = _this.generate(elSchema);
                            unionLines.push(elType.id);
                        }
                    }
                    catch (e_2_1) { e_2 = { error: e_2_1 }; }
                    finally {
                        try {
                            if (_f && !_f.done && (_b = _e.return)) _b.call(_e);
                        }
                        finally { if (e_2) throw e_2.error; }
                    }
                    return _this.setType(id, unionLines.join(" | "));
                case base.ZodTypes.intersection:
                    return _this.setType(id, _this.generate(def.left).id + " & " + _this.generate(def.right).id);
                case base.ZodTypes.record:
                    return _this.setType(id, "{[k:string]: " + _this.generate(def.valueType).id + "}");
                case base.ZodTypes.transformer:
                    return _this.setType(id, _this.generate(def.output).id);
                case base.ZodTypes.map:
                    return _this.setType(id, "Map<" + _this.generate(def.keyType).id + ", " + _this.generate(def.valueType).id + ">");
                case base.ZodTypes.lazy:
                    var lazyType = def.getter();
                    return _this.setType(id, _this.generate(lazyType).id);
                case base.ZodTypes.nativeEnum:
                    return _this.setType(id, 'asdf');
                case base.ZodTypes.optional:
                    return _this.setType(id, _this.generate(def.innerType).id + " | undefined");
                case base.ZodTypes.nullable:
                    return _this.setType(id, _this.generate(def.innerType).id + " | null");
                default:
                    util_1.util.assertNever(def);
            }
            return _this.findById(id);
        };
    }
    ZodCodeGenerator.create = function () { return new ZodCodeGenerator(); };
    return ZodCodeGenerator;
}());
var ZodCodeGenerator_1 = ZodCodeGenerator;


var codegen = /*#__PURE__*/Object.defineProperty({
	ZodCodeGenerator: ZodCodeGenerator_1
}, '__esModule', {value: true});

var cjs = createCommonjsModule(function (module, exports) {
function __export(m) {
    for (var p in m) if (!exports.hasOwnProperty(p)) exports[p] = m[p];
}
Object.defineProperty(exports, "__esModule", { value: true });

exports.ZodString = string.ZodString;

exports.ZodNumber = number.ZodNumber;

exports.ZodBigInt = bigint.ZodBigInt;

exports.ZodBoolean = boolean.ZodBoolean;

exports.ZodDate = date.ZodDate;

exports.ZodUndefined = _undefined.ZodUndefined;

exports.ZodNull = _null.ZodNull;

exports.ZodAny = any.ZodAny;

exports.ZodUnknown = unknown.ZodUnknown;

exports.ZodNever = never.ZodNever;

exports.ZodVoid = _void.ZodVoid;

exports.ZodArray = array.ZodArray;

exports.ZodObject = object.ZodObject;

exports.ZodUnion = union.ZodUnion;

exports.ZodIntersection = intersection.ZodIntersection;

exports.ZodTuple = tuple.ZodTuple;

exports.ZodRecord = record.ZodRecord;


exports.ZodFunction = _function.ZodFunction;

exports.ZodLazy = lazy.ZodLazy;

exports.ZodLiteral = literal.ZodLiteral;

exports.ZodEnum = _enum.ZodEnum;

exports.ZodNativeEnum = nativeEnum.ZodNativeEnum;

exports.ZodPromise = promise.ZodPromise;

exports.ZodTransformer = transformer.ZodTransformer;

exports.ZodOptional = optional.ZodOptional;

exports.ZodNullable = nullable.ZodNullable;

exports.ZodType = base.ZodType;
exports.Schema = base.ZodType;
exports.ZodSchema = base.ZodType;
exports.ZodTypes = base.ZodTypes;

exports.ZodParsedType = parser.ZodParsedType;

exports.ZodCodeGenerator = codegen.ZodCodeGenerator;
var stringType = string.ZodString.create;
exports.string = stringType;
var numberType = number.ZodNumber.create;
exports.number = numberType;
var bigIntType = bigint.ZodBigInt.create;
exports.bigint = bigIntType;
var booleanType = boolean.ZodBoolean.create;
exports.boolean = booleanType;
var dateType = date.ZodDate.create;
exports.date = dateType;
var undefinedType = _undefined.ZodUndefined.create;
exports.undefined = undefinedType;
var nullType = _null.ZodNull.create;
exports.null = nullType;
var anyType = any.ZodAny.create;
exports.any = anyType;
var unknownType = unknown.ZodUnknown.create;
exports.unknown = unknownType;
var neverType = never.ZodNever.create;
exports.never = neverType;
var voidType = _void.ZodVoid.create;
exports.void = voidType;
var arrayType = array.ZodArray.create;
exports.array = arrayType;
var objectType = object.ZodObject.create;
exports.object = objectType;
var unionType = union.ZodUnion.create;
exports.union = unionType;
var intersectionType = intersection.ZodIntersection.create;
exports.intersection = intersectionType;
var tupleType = tuple.ZodTuple.create;
exports.tuple = tupleType;
var recordType = record.ZodRecord.create;
exports.record = recordType;
var mapType = map.ZodMap.create;
exports.map = mapType;
var functionType = _function.ZodFunction.create;
exports.function = functionType;
var lazyType = lazy.ZodLazy.create;
exports.lazy = lazyType;
var literalType = literal.ZodLiteral.create;
exports.literal = literalType;
var enumType = _enum.ZodEnum.create;
exports.enum = enumType;
var nativeEnumType = nativeEnum.ZodNativeEnum.create;
exports.nativeEnum = nativeEnumType;
var promiseType = promise.ZodPromise.create;
exports.promise = promiseType;
var transformerType = transformer.ZodTransformer.create;
exports.transformer = transformerType;
var optionalType = optional.ZodOptional.create;
exports.optional = optionalType;
var nullableType = nullable.ZodNullable.create;
exports.nullable = nullableType;
var ostring = function () { return stringType().optional(); };
exports.ostring = ostring;
var onumber = function () { return numberType().optional(); };
exports.onumber = onumber;
var oboolean = function () { return booleanType().optional(); };
exports.oboolean = oboolean;
var codegen$1 = codegen.ZodCodeGenerator.create;
exports.codegen = codegen$1;
exports.custom = function (check, params) {
    if (check)
        return anyType().refine(check, params);
    return anyType();
};
var instanceOfType = function (cls, params) {
    if (params === void 0) { params = {
        message: "Input not instance of " + cls.name,
    }; }
    return exports.custom(function (data) { return data instanceof cls; }, params);
};
exports.instanceof = instanceOfType;
exports.late = {
    object: object.ZodObject.lazycreate,
};
__export(ZodError_1);

});

const PluginConfigBaseSchema = cjs.object({
    apiVersionRequired: cjs.string(),
    pluginPath: cjs.string(),
    id: cjs.string(),
})
    .catchall(cjs.unknown());

let FORCE_COLOR, NODE_DISABLE_COLORS, NO_COLOR, TERM, isTTY=true;
if (typeof process !== 'undefined') {
	({ FORCE_COLOR, NODE_DISABLE_COLORS, NO_COLOR, TERM } = process.env);
	isTTY = process.stdout && process.stdout.isTTY;
}

const $ = {
	enabled: !NODE_DISABLE_COLORS && NO_COLOR == null && TERM !== 'dumb' && (
		FORCE_COLOR != null && FORCE_COLOR !== '0' || isTTY
	)
};

function init(x, y) {
	let rgx = new RegExp(`\\x1b\\[${y}m`, 'g');
	let open = `\x1b[${x}m`, close = `\x1b[${y}m`;

	return function (txt) {
		if (!$.enabled || txt == null) return txt;
		return open + ((''+txt).includes(close) ? txt.replace(rgx, close + open) : txt) + close;
	};
}
const grey = init(90, 39);

/* eslint-disable no-console */
// const bee = `\u{1F41D}`;
const debug = `\u{1F3F7}`;
const tick = `\u{2705}`;
const error = `\u{2757}`;
const warning = `\u{26A0}`;
const info = `\u{2139}`;
const fatal = `\u{203C}`;
const play = `\u{1F41D}`;
class Logger {
    constructor(module) {
        this._prefix = `${grey(`Zigzag`)} ${grey(`[${module}]`)}`;
    }
    debug(message) {
        console.log(`${this._prefix} ${debug} ${message}`);
    }
    error(message) {
        console.log(`${this._prefix} ${error} ${message}`);
    }
    fatal(message) {
        console.log(`${this._prefix} ${fatal} ${message}`);
    }
    info(message) {
        console.log(`${this._prefix} ${info} ${message}`);
    }
    success(message) {
        console.log(`${this._prefix} ${tick} ${message}`);
    }
    start(message) {
        console.log(`${this._prefix} ${play} ${message}`);
    }
    warn(message) {
        console.log(`${this._prefix} ${warning} ${message}`);
    }
}
/* eslint-enable no-console */

// Note: this is the semver.org version of the spec that it implements
// Not necessarily the package version of this code.
const SEMVER_SPEC_VERSION = '2.0.0';

const MAX_LENGTH = 256;
const MAX_SAFE_INTEGER = Number.MAX_SAFE_INTEGER ||
  /* istanbul ignore next */ 9007199254740991;

// Max safe segment length for coercion.
const MAX_SAFE_COMPONENT_LENGTH = 16;

var constants = {
  SEMVER_SPEC_VERSION,
  MAX_LENGTH,
  MAX_SAFE_INTEGER,
  MAX_SAFE_COMPONENT_LENGTH
};

const debug$1 = (
  typeof process === 'object' &&
  process.env &&
  process.env.NODE_DEBUG &&
  /\bsemver\b/i.test(process.env.NODE_DEBUG)
) ? (...args) => console.error('SEMVER', ...args)
  : () => {};

var debug_1 = debug$1;

var re_1 = createCommonjsModule(function (module, exports) {
const { MAX_SAFE_COMPONENT_LENGTH } = constants;

exports = module.exports = {};

// The actual regexps go on exports.re
const re = exports.re = [];
const src = exports.src = [];
const t = exports.t = {};
let R = 0;

const createToken = (name, value, isGlobal) => {
  const index = R++;
  debug_1(index, value);
  t[name] = index;
  src[index] = value;
  re[index] = new RegExp(value, isGlobal ? 'g' : undefined);
};

// The following Regular Expressions can be used for tokenizing,
// validating, and parsing SemVer version strings.

// ## Numeric Identifier
// A single `0`, or a non-zero digit followed by zero or more digits.

createToken('NUMERICIDENTIFIER', '0|[1-9]\\d*');
createToken('NUMERICIDENTIFIERLOOSE', '[0-9]+');

// ## Non-numeric Identifier
// Zero or more digits, followed by a letter or hyphen, and then zero or
// more letters, digits, or hyphens.

createToken('NONNUMERICIDENTIFIER', '\\d*[a-zA-Z-][a-zA-Z0-9-]*');

// ## Main Version
// Three dot-separated numeric identifiers.

createToken('MAINVERSION', `(${src[t.NUMERICIDENTIFIER]})\\.` +
                   `(${src[t.NUMERICIDENTIFIER]})\\.` +
                   `(${src[t.NUMERICIDENTIFIER]})`);

createToken('MAINVERSIONLOOSE', `(${src[t.NUMERICIDENTIFIERLOOSE]})\\.` +
                        `(${src[t.NUMERICIDENTIFIERLOOSE]})\\.` +
                        `(${src[t.NUMERICIDENTIFIERLOOSE]})`);

// ## Pre-release Version Identifier
// A numeric identifier, or a non-numeric identifier.

createToken('PRERELEASEIDENTIFIER', `(?:${src[t.NUMERICIDENTIFIER]
}|${src[t.NONNUMERICIDENTIFIER]})`);

createToken('PRERELEASEIDENTIFIERLOOSE', `(?:${src[t.NUMERICIDENTIFIERLOOSE]
}|${src[t.NONNUMERICIDENTIFIER]})`);

// ## Pre-release Version
// Hyphen, followed by one or more dot-separated pre-release version
// identifiers.

createToken('PRERELEASE', `(?:-(${src[t.PRERELEASEIDENTIFIER]
}(?:\\.${src[t.PRERELEASEIDENTIFIER]})*))`);

createToken('PRERELEASELOOSE', `(?:-?(${src[t.PRERELEASEIDENTIFIERLOOSE]
}(?:\\.${src[t.PRERELEASEIDENTIFIERLOOSE]})*))`);

// ## Build Metadata Identifier
// Any combination of digits, letters, or hyphens.

createToken('BUILDIDENTIFIER', '[0-9A-Za-z-]+');

// ## Build Metadata
// Plus sign, followed by one or more period-separated build metadata
// identifiers.

createToken('BUILD', `(?:\\+(${src[t.BUILDIDENTIFIER]
}(?:\\.${src[t.BUILDIDENTIFIER]})*))`);

// ## Full Version String
// A main version, followed optionally by a pre-release version and
// build metadata.

// Note that the only major, minor, patch, and pre-release sections of
// the version string are capturing groups.  The build metadata is not a
// capturing group, because it should not ever be used in version
// comparison.

createToken('FULLPLAIN', `v?${src[t.MAINVERSION]
}${src[t.PRERELEASE]}?${
  src[t.BUILD]}?`);

createToken('FULL', `^${src[t.FULLPLAIN]}$`);

// like full, but allows v1.2.3 and =1.2.3, which people do sometimes.
// also, 1.0.0alpha1 (prerelease without the hyphen) which is pretty
// common in the npm registry.
createToken('LOOSEPLAIN', `[v=\\s]*${src[t.MAINVERSIONLOOSE]
}${src[t.PRERELEASELOOSE]}?${
  src[t.BUILD]}?`);

createToken('LOOSE', `^${src[t.LOOSEPLAIN]}$`);

createToken('GTLT', '((?:<|>)?=?)');

// Something like "2.*" or "1.2.x".
// Note that "x.x" is a valid xRange identifer, meaning "any version"
// Only the first item is strictly required.
createToken('XRANGEIDENTIFIERLOOSE', `${src[t.NUMERICIDENTIFIERLOOSE]}|x|X|\\*`);
createToken('XRANGEIDENTIFIER', `${src[t.NUMERICIDENTIFIER]}|x|X|\\*`);

createToken('XRANGEPLAIN', `[v=\\s]*(${src[t.XRANGEIDENTIFIER]})` +
                   `(?:\\.(${src[t.XRANGEIDENTIFIER]})` +
                   `(?:\\.(${src[t.XRANGEIDENTIFIER]})` +
                   `(?:${src[t.PRERELEASE]})?${
                     src[t.BUILD]}?` +
                   `)?)?`);

createToken('XRANGEPLAINLOOSE', `[v=\\s]*(${src[t.XRANGEIDENTIFIERLOOSE]})` +
                        `(?:\\.(${src[t.XRANGEIDENTIFIERLOOSE]})` +
                        `(?:\\.(${src[t.XRANGEIDENTIFIERLOOSE]})` +
                        `(?:${src[t.PRERELEASELOOSE]})?${
                          src[t.BUILD]}?` +
                        `)?)?`);

createToken('XRANGE', `^${src[t.GTLT]}\\s*${src[t.XRANGEPLAIN]}$`);
createToken('XRANGELOOSE', `^${src[t.GTLT]}\\s*${src[t.XRANGEPLAINLOOSE]}$`);

// Coercion.
// Extract anything that could conceivably be a part of a valid semver
createToken('COERCE', `${'(^|[^\\d])' +
              '(\\d{1,'}${MAX_SAFE_COMPONENT_LENGTH}})` +
              `(?:\\.(\\d{1,${MAX_SAFE_COMPONENT_LENGTH}}))?` +
              `(?:\\.(\\d{1,${MAX_SAFE_COMPONENT_LENGTH}}))?` +
              `(?:$|[^\\d])`);
createToken('COERCERTL', src[t.COERCE], true);

// Tilde ranges.
// Meaning is "reasonably at or greater than"
createToken('LONETILDE', '(?:~>?)');

createToken('TILDETRIM', `(\\s*)${src[t.LONETILDE]}\\s+`, true);
exports.tildeTrimReplace = '$1~';

createToken('TILDE', `^${src[t.LONETILDE]}${src[t.XRANGEPLAIN]}$`);
createToken('TILDELOOSE', `^${src[t.LONETILDE]}${src[t.XRANGEPLAINLOOSE]}$`);

// Caret ranges.
// Meaning is "at least and backwards compatible with"
createToken('LONECARET', '(?:\\^)');

createToken('CARETTRIM', `(\\s*)${src[t.LONECARET]}\\s+`, true);
exports.caretTrimReplace = '$1^';

createToken('CARET', `^${src[t.LONECARET]}${src[t.XRANGEPLAIN]}$`);
createToken('CARETLOOSE', `^${src[t.LONECARET]}${src[t.XRANGEPLAINLOOSE]}$`);

// A simple gt/lt/eq thing, or just "" to indicate "any version"
createToken('COMPARATORLOOSE', `^${src[t.GTLT]}\\s*(${src[t.LOOSEPLAIN]})$|^$`);
createToken('COMPARATOR', `^${src[t.GTLT]}\\s*(${src[t.FULLPLAIN]})$|^$`);

// An expression to strip any whitespace between the gtlt and the thing
// it modifies, so that `> 1.2.3` ==> `>1.2.3`
createToken('COMPARATORTRIM', `(\\s*)${src[t.GTLT]
}\\s*(${src[t.LOOSEPLAIN]}|${src[t.XRANGEPLAIN]})`, true);
exports.comparatorTrimReplace = '$1$2$3';

// Something like `1.2.3 - 1.2.4`
// Note that these all use the loose form, because they'll be
// checked against either the strict or loose comparator form
// later.
createToken('HYPHENRANGE', `^\\s*(${src[t.XRANGEPLAIN]})` +
                   `\\s+-\\s+` +
                   `(${src[t.XRANGEPLAIN]})` +
                   `\\s*$`);

createToken('HYPHENRANGELOOSE', `^\\s*(${src[t.XRANGEPLAINLOOSE]})` +
                        `\\s+-\\s+` +
                        `(${src[t.XRANGEPLAINLOOSE]})` +
                        `\\s*$`);

// Star ranges basically just allow anything at all.
createToken('STAR', '(<|>)?=?\\s*\\*');
// >=0.0.0 is like a star
createToken('GTE0', '^\\s*>=\\s*0\.0\.0\\s*$');
createToken('GTE0PRE', '^\\s*>=\\s*0\.0\.0-0\\s*$');
});

// parse out just the options we care about so we always get a consistent
// obj with keys in a consistent order.
const opts = ['includePrerelease', 'loose', 'rtl'];
const parseOptions = options =>
  !options ? {}
  : typeof options !== 'object' ? { loose: true }
  : opts.filter(k => options[k]).reduce((options, k) => {
    options[k] = true;
    return options
  }, {});
var parseOptions_1 = parseOptions;

const numeric = /^[0-9]+$/;
const compareIdentifiers = (a, b) => {
  const anum = numeric.test(a);
  const bnum = numeric.test(b);

  if (anum && bnum) {
    a = +a;
    b = +b;
  }

  return a === b ? 0
    : (anum && !bnum) ? -1
    : (bnum && !anum) ? 1
    : a < b ? -1
    : 1
};

const rcompareIdentifiers = (a, b) => compareIdentifiers(b, a);

var identifiers = {
  compareIdentifiers,
  rcompareIdentifiers
};

const { MAX_LENGTH: MAX_LENGTH$1, MAX_SAFE_INTEGER: MAX_SAFE_INTEGER$1 } = constants;
const { re, t } = re_1;


const { compareIdentifiers: compareIdentifiers$1 } = identifiers;
class SemVer {
  constructor (version, options) {
    options = parseOptions_1(options);

    if (version instanceof SemVer) {
      if (version.loose === !!options.loose &&
          version.includePrerelease === !!options.includePrerelease) {
        return version
      } else {
        version = version.version;
      }
    } else if (typeof version !== 'string') {
      throw new TypeError(`Invalid Version: ${version}`)
    }

    if (version.length > MAX_LENGTH$1) {
      throw new TypeError(
        `version is longer than ${MAX_LENGTH$1} characters`
      )
    }

    debug_1('SemVer', version, options);
    this.options = options;
    this.loose = !!options.loose;
    // this isn't actually relevant for versions, but keep it so that we
    // don't run into trouble passing this.options around.
    this.includePrerelease = !!options.includePrerelease;

    const m = version.trim().match(options.loose ? re[t.LOOSE] : re[t.FULL]);

    if (!m) {
      throw new TypeError(`Invalid Version: ${version}`)
    }

    this.raw = version;

    // these are actually numbers
    this.major = +m[1];
    this.minor = +m[2];
    this.patch = +m[3];

    if (this.major > MAX_SAFE_INTEGER$1 || this.major < 0) {
      throw new TypeError('Invalid major version')
    }

    if (this.minor > MAX_SAFE_INTEGER$1 || this.minor < 0) {
      throw new TypeError('Invalid minor version')
    }

    if (this.patch > MAX_SAFE_INTEGER$1 || this.patch < 0) {
      throw new TypeError('Invalid patch version')
    }

    // numberify any prerelease numeric ids
    if (!m[4]) {
      this.prerelease = [];
    } else {
      this.prerelease = m[4].split('.').map((id) => {
        if (/^[0-9]+$/.test(id)) {
          const num = +id;
          if (num >= 0 && num < MAX_SAFE_INTEGER$1) {
            return num
          }
        }
        return id
      });
    }

    this.build = m[5] ? m[5].split('.') : [];
    this.format();
  }

  format () {
    this.version = `${this.major}.${this.minor}.${this.patch}`;
    if (this.prerelease.length) {
      this.version += `-${this.prerelease.join('.')}`;
    }
    return this.version
  }

  toString () {
    return this.version
  }

  compare (other) {
    debug_1('SemVer.compare', this.version, this.options, other);
    if (!(other instanceof SemVer)) {
      if (typeof other === 'string' && other === this.version) {
        return 0
      }
      other = new SemVer(other, this.options);
    }

    if (other.version === this.version) {
      return 0
    }

    return this.compareMain(other) || this.comparePre(other)
  }

  compareMain (other) {
    if (!(other instanceof SemVer)) {
      other = new SemVer(other, this.options);
    }

    return (
      compareIdentifiers$1(this.major, other.major) ||
      compareIdentifiers$1(this.minor, other.minor) ||
      compareIdentifiers$1(this.patch, other.patch)
    )
  }

  comparePre (other) {
    if (!(other instanceof SemVer)) {
      other = new SemVer(other, this.options);
    }

    // NOT having a prerelease is > having one
    if (this.prerelease.length && !other.prerelease.length) {
      return -1
    } else if (!this.prerelease.length && other.prerelease.length) {
      return 1
    } else if (!this.prerelease.length && !other.prerelease.length) {
      return 0
    }

    let i = 0;
    do {
      const a = this.prerelease[i];
      const b = other.prerelease[i];
      debug_1('prerelease compare', i, a, b);
      if (a === undefined && b === undefined) {
        return 0
      } else if (b === undefined) {
        return 1
      } else if (a === undefined) {
        return -1
      } else if (a === b) {
        continue
      } else {
        return compareIdentifiers$1(a, b)
      }
    } while (++i)
  }

  compareBuild (other) {
    if (!(other instanceof SemVer)) {
      other = new SemVer(other, this.options);
    }

    let i = 0;
    do {
      const a = this.build[i];
      const b = other.build[i];
      debug_1('prerelease compare', i, a, b);
      if (a === undefined && b === undefined) {
        return 0
      } else if (b === undefined) {
        return 1
      } else if (a === undefined) {
        return -1
      } else if (a === b) {
        continue
      } else {
        return compareIdentifiers$1(a, b)
      }
    } while (++i)
  }

  // preminor will bump the version up to the next minor release, and immediately
  // down to pre-release. premajor and prepatch work the same way.
  inc (release, identifier) {
    switch (release) {
      case 'premajor':
        this.prerelease.length = 0;
        this.patch = 0;
        this.minor = 0;
        this.major++;
        this.inc('pre', identifier);
        break
      case 'preminor':
        this.prerelease.length = 0;
        this.patch = 0;
        this.minor++;
        this.inc('pre', identifier);
        break
      case 'prepatch':
        // If this is already a prerelease, it will bump to the next version
        // drop any prereleases that might already exist, since they are not
        // relevant at this point.
        this.prerelease.length = 0;
        this.inc('patch', identifier);
        this.inc('pre', identifier);
        break
      // If the input is a non-prerelease version, this acts the same as
      // prepatch.
      case 'prerelease':
        if (this.prerelease.length === 0) {
          this.inc('patch', identifier);
        }
        this.inc('pre', identifier);
        break

      case 'major':
        // If this is a pre-major version, bump up to the same major version.
        // Otherwise increment major.
        // 1.0.0-5 bumps to 1.0.0
        // 1.1.0 bumps to 2.0.0
        if (
          this.minor !== 0 ||
          this.patch !== 0 ||
          this.prerelease.length === 0
        ) {
          this.major++;
        }
        this.minor = 0;
        this.patch = 0;
        this.prerelease = [];
        break
      case 'minor':
        // If this is a pre-minor version, bump up to the same minor version.
        // Otherwise increment minor.
        // 1.2.0-5 bumps to 1.2.0
        // 1.2.1 bumps to 1.3.0
        if (this.patch !== 0 || this.prerelease.length === 0) {
          this.minor++;
        }
        this.patch = 0;
        this.prerelease = [];
        break
      case 'patch':
        // If this is not a pre-release version, it will increment the patch.
        // If it is a pre-release it will bump up to the same patch version.
        // 1.2.0-5 patches to 1.2.0
        // 1.2.0 patches to 1.2.1
        if (this.prerelease.length === 0) {
          this.patch++;
        }
        this.prerelease = [];
        break
      // This probably shouldn't be used publicly.
      // 1.0.0 'pre' would become 1.0.0-0 which is the wrong direction.
      case 'pre':
        if (this.prerelease.length === 0) {
          this.prerelease = [0];
        } else {
          let i = this.prerelease.length;
          while (--i >= 0) {
            if (typeof this.prerelease[i] === 'number') {
              this.prerelease[i]++;
              i = -2;
            }
          }
          if (i === -1) {
            // didn't increment anything
            this.prerelease.push(0);
          }
        }
        if (identifier) {
          // 1.2.0-beta.1 bumps to 1.2.0-beta.2,
          // 1.2.0-beta.fooblz or 1.2.0-beta bumps to 1.2.0-beta.0
          if (this.prerelease[0] === identifier) {
            if (isNaN(this.prerelease[1])) {
              this.prerelease = [identifier, 0];
            }
          } else {
            this.prerelease = [identifier, 0];
          }
        }
        break

      default:
        throw new Error(`invalid increment argument: ${release}`)
    }
    this.format();
    this.raw = this.version;
    return this
  }
}

var semver = SemVer;

const {MAX_LENGTH: MAX_LENGTH$2} = constants;
const { re: re$1, t: t$1 } = re_1;



const parse = (version, options) => {
  options = parseOptions_1(options);

  if (version instanceof semver) {
    return version
  }

  if (typeof version !== 'string') {
    return null
  }

  if (version.length > MAX_LENGTH$2) {
    return null
  }

  const r = options.loose ? re$1[t$1.LOOSE] : re$1[t$1.FULL];
  if (!r.test(version)) {
    return null
  }

  try {
    return new semver(version, options)
  } catch (er) {
    return null
  }
};

var parse_1 = parse;

const valid = (version, options) => {
  const v = parse_1(version, options);
  return v ? v.version : null
};
var valid_1 = valid;

const clean = (version, options) => {
  const s = parse_1(version.trim().replace(/^[=v]+/, ''), options);
  return s ? s.version : null
};
var clean_1 = clean;

const inc = (version, release, options, identifier) => {
  if (typeof (options) === 'string') {
    identifier = options;
    options = undefined;
  }

  try {
    return new semver(version, options).inc(release, identifier).version
  } catch (er) {
    return null
  }
};
var inc_1 = inc;

const compare = (a, b, loose) =>
  new semver(a, loose).compare(new semver(b, loose));

var compare_1 = compare;

const eq = (a, b, loose) => compare_1(a, b, loose) === 0;
var eq_1 = eq;

const diff = (version1, version2) => {
  if (eq_1(version1, version2)) {
    return null
  } else {
    const v1 = parse_1(version1);
    const v2 = parse_1(version2);
    const hasPre = v1.prerelease.length || v2.prerelease.length;
    const prefix = hasPre ? 'pre' : '';
    const defaultResult = hasPre ? 'prerelease' : '';
    for (const key in v1) {
      if (key === 'major' || key === 'minor' || key === 'patch') {
        if (v1[key] !== v2[key]) {
          return prefix + key
        }
      }
    }
    return defaultResult // may be undefined
  }
};
var diff_1 = diff;

const major = (a, loose) => new semver(a, loose).major;
var major_1 = major;

const minor = (a, loose) => new semver(a, loose).minor;
var minor_1 = minor;

const patch = (a, loose) => new semver(a, loose).patch;
var patch_1 = patch;

const prerelease = (version, options) => {
  const parsed = parse_1(version, options);
  return (parsed && parsed.prerelease.length) ? parsed.prerelease : null
};
var prerelease_1 = prerelease;

const rcompare = (a, b, loose) => compare_1(b, a, loose);
var rcompare_1 = rcompare;

const compareLoose = (a, b) => compare_1(a, b, true);
var compareLoose_1 = compareLoose;

const compareBuild = (a, b, loose) => {
  const versionA = new semver(a, loose);
  const versionB = new semver(b, loose);
  return versionA.compare(versionB) || versionA.compareBuild(versionB)
};
var compareBuild_1 = compareBuild;

const sort = (list, loose) => list.sort((a, b) => compareBuild_1(a, b, loose));
var sort_1 = sort;

const rsort = (list, loose) => list.sort((a, b) => compareBuild_1(b, a, loose));
var rsort_1 = rsort;

const gt = (a, b, loose) => compare_1(a, b, loose) > 0;
var gt_1 = gt;

const lt = (a, b, loose) => compare_1(a, b, loose) < 0;
var lt_1 = lt;

const neq = (a, b, loose) => compare_1(a, b, loose) !== 0;
var neq_1 = neq;

const gte = (a, b, loose) => compare_1(a, b, loose) >= 0;
var gte_1 = gte;

const lte = (a, b, loose) => compare_1(a, b, loose) <= 0;
var lte_1 = lte;

const cmp = (a, op, b, loose) => {
  switch (op) {
    case '===':
      if (typeof a === 'object')
        a = a.version;
      if (typeof b === 'object')
        b = b.version;
      return a === b

    case '!==':
      if (typeof a === 'object')
        a = a.version;
      if (typeof b === 'object')
        b = b.version;
      return a !== b

    case '':
    case '=':
    case '==':
      return eq_1(a, b, loose)

    case '!=':
      return neq_1(a, b, loose)

    case '>':
      return gt_1(a, b, loose)

    case '>=':
      return gte_1(a, b, loose)

    case '<':
      return lt_1(a, b, loose)

    case '<=':
      return lte_1(a, b, loose)

    default:
      throw new TypeError(`Invalid operator: ${op}`)
  }
};
var cmp_1 = cmp;

const {re: re$2, t: t$2} = re_1;

const coerce = (version, options) => {
  if (version instanceof semver) {
    return version
  }

  if (typeof version === 'number') {
    version = String(version);
  }

  if (typeof version !== 'string') {
    return null
  }

  options = options || {};

  let match = null;
  if (!options.rtl) {
    match = version.match(re$2[t$2.COERCE]);
  } else {
    // Find the right-most coercible string that does not share
    // a terminus with a more left-ward coercible string.
    // Eg, '1.2.3.4' wants to coerce '2.3.4', not '3.4' or '4'
    //
    // Walk through the string checking with a /g regexp
    // Manually set the index so as to pick up overlapping matches.
    // Stop when we get a match that ends at the string end, since no
    // coercible string can be more right-ward without the same terminus.
    let next;
    while ((next = re$2[t$2.COERCERTL].exec(version)) &&
        (!match || match.index + match[0].length !== version.length)
    ) {
      if (!match ||
            next.index + next[0].length !== match.index + match[0].length) {
        match = next;
      }
      re$2[t$2.COERCERTL].lastIndex = next.index + next[1].length + next[2].length;
    }
    // leave it in a clean state
    re$2[t$2.COERCERTL].lastIndex = -1;
  }

  if (match === null)
    return null

  return parse_1(`${match[2]}.${match[3] || '0'}.${match[4] || '0'}`, options)
};
var coerce_1 = coerce;

var iterator = function (Yallist) {
  Yallist.prototype[Symbol.iterator] = function* () {
    for (let walker = this.head; walker; walker = walker.next) {
      yield walker.value;
    }
  };
};

var yallist = Yallist;

Yallist.Node = Node;
Yallist.create = Yallist;

function Yallist (list) {
  var self = this;
  if (!(self instanceof Yallist)) {
    self = new Yallist();
  }

  self.tail = null;
  self.head = null;
  self.length = 0;

  if (list && typeof list.forEach === 'function') {
    list.forEach(function (item) {
      self.push(item);
    });
  } else if (arguments.length > 0) {
    for (var i = 0, l = arguments.length; i < l; i++) {
      self.push(arguments[i]);
    }
  }

  return self
}

Yallist.prototype.removeNode = function (node) {
  if (node.list !== this) {
    throw new Error('removing node which does not belong to this list')
  }

  var next = node.next;
  var prev = node.prev;

  if (next) {
    next.prev = prev;
  }

  if (prev) {
    prev.next = next;
  }

  if (node === this.head) {
    this.head = next;
  }
  if (node === this.tail) {
    this.tail = prev;
  }

  node.list.length--;
  node.next = null;
  node.prev = null;
  node.list = null;

  return next
};

Yallist.prototype.unshiftNode = function (node) {
  if (node === this.head) {
    return
  }

  if (node.list) {
    node.list.removeNode(node);
  }

  var head = this.head;
  node.list = this;
  node.next = head;
  if (head) {
    head.prev = node;
  }

  this.head = node;
  if (!this.tail) {
    this.tail = node;
  }
  this.length++;
};

Yallist.prototype.pushNode = function (node) {
  if (node === this.tail) {
    return
  }

  if (node.list) {
    node.list.removeNode(node);
  }

  var tail = this.tail;
  node.list = this;
  node.prev = tail;
  if (tail) {
    tail.next = node;
  }

  this.tail = node;
  if (!this.head) {
    this.head = node;
  }
  this.length++;
};

Yallist.prototype.push = function () {
  for (var i = 0, l = arguments.length; i < l; i++) {
    push(this, arguments[i]);
  }
  return this.length
};

Yallist.prototype.unshift = function () {
  for (var i = 0, l = arguments.length; i < l; i++) {
    unshift(this, arguments[i]);
  }
  return this.length
};

Yallist.prototype.pop = function () {
  if (!this.tail) {
    return undefined
  }

  var res = this.tail.value;
  this.tail = this.tail.prev;
  if (this.tail) {
    this.tail.next = null;
  } else {
    this.head = null;
  }
  this.length--;
  return res
};

Yallist.prototype.shift = function () {
  if (!this.head) {
    return undefined
  }

  var res = this.head.value;
  this.head = this.head.next;
  if (this.head) {
    this.head.prev = null;
  } else {
    this.tail = null;
  }
  this.length--;
  return res
};

Yallist.prototype.forEach = function (fn, thisp) {
  thisp = thisp || this;
  for (var walker = this.head, i = 0; walker !== null; i++) {
    fn.call(thisp, walker.value, i, this);
    walker = walker.next;
  }
};

Yallist.prototype.forEachReverse = function (fn, thisp) {
  thisp = thisp || this;
  for (var walker = this.tail, i = this.length - 1; walker !== null; i--) {
    fn.call(thisp, walker.value, i, this);
    walker = walker.prev;
  }
};

Yallist.prototype.get = function (n) {
  for (var i = 0, walker = this.head; walker !== null && i < n; i++) {
    // abort out of the list early if we hit a cycle
    walker = walker.next;
  }
  if (i === n && walker !== null) {
    return walker.value
  }
};

Yallist.prototype.getReverse = function (n) {
  for (var i = 0, walker = this.tail; walker !== null && i < n; i++) {
    // abort out of the list early if we hit a cycle
    walker = walker.prev;
  }
  if (i === n && walker !== null) {
    return walker.value
  }
};

Yallist.prototype.map = function (fn, thisp) {
  thisp = thisp || this;
  var res = new Yallist();
  for (var walker = this.head; walker !== null;) {
    res.push(fn.call(thisp, walker.value, this));
    walker = walker.next;
  }
  return res
};

Yallist.prototype.mapReverse = function (fn, thisp) {
  thisp = thisp || this;
  var res = new Yallist();
  for (var walker = this.tail; walker !== null;) {
    res.push(fn.call(thisp, walker.value, this));
    walker = walker.prev;
  }
  return res
};

Yallist.prototype.reduce = function (fn, initial) {
  var acc;
  var walker = this.head;
  if (arguments.length > 1) {
    acc = initial;
  } else if (this.head) {
    walker = this.head.next;
    acc = this.head.value;
  } else {
    throw new TypeError('Reduce of empty list with no initial value')
  }

  for (var i = 0; walker !== null; i++) {
    acc = fn(acc, walker.value, i);
    walker = walker.next;
  }

  return acc
};

Yallist.prototype.reduceReverse = function (fn, initial) {
  var acc;
  var walker = this.tail;
  if (arguments.length > 1) {
    acc = initial;
  } else if (this.tail) {
    walker = this.tail.prev;
    acc = this.tail.value;
  } else {
    throw new TypeError('Reduce of empty list with no initial value')
  }

  for (var i = this.length - 1; walker !== null; i--) {
    acc = fn(acc, walker.value, i);
    walker = walker.prev;
  }

  return acc
};

Yallist.prototype.toArray = function () {
  var arr = new Array(this.length);
  for (var i = 0, walker = this.head; walker !== null; i++) {
    arr[i] = walker.value;
    walker = walker.next;
  }
  return arr
};

Yallist.prototype.toArrayReverse = function () {
  var arr = new Array(this.length);
  for (var i = 0, walker = this.tail; walker !== null; i++) {
    arr[i] = walker.value;
    walker = walker.prev;
  }
  return arr
};

Yallist.prototype.slice = function (from, to) {
  to = to || this.length;
  if (to < 0) {
    to += this.length;
  }
  from = from || 0;
  if (from < 0) {
    from += this.length;
  }
  var ret = new Yallist();
  if (to < from || to < 0) {
    return ret
  }
  if (from < 0) {
    from = 0;
  }
  if (to > this.length) {
    to = this.length;
  }
  for (var i = 0, walker = this.head; walker !== null && i < from; i++) {
    walker = walker.next;
  }
  for (; walker !== null && i < to; i++, walker = walker.next) {
    ret.push(walker.value);
  }
  return ret
};

Yallist.prototype.sliceReverse = function (from, to) {
  to = to || this.length;
  if (to < 0) {
    to += this.length;
  }
  from = from || 0;
  if (from < 0) {
    from += this.length;
  }
  var ret = new Yallist();
  if (to < from || to < 0) {
    return ret
  }
  if (from < 0) {
    from = 0;
  }
  if (to > this.length) {
    to = this.length;
  }
  for (var i = this.length, walker = this.tail; walker !== null && i > to; i--) {
    walker = walker.prev;
  }
  for (; walker !== null && i > from; i--, walker = walker.prev) {
    ret.push(walker.value);
  }
  return ret
};

Yallist.prototype.splice = function (start, deleteCount, ...nodes) {
  if (start > this.length) {
    start = this.length - 1;
  }
  if (start < 0) {
    start = this.length + start;
  }

  for (var i = 0, walker = this.head; walker !== null && i < start; i++) {
    walker = walker.next;
  }

  var ret = [];
  for (var i = 0; walker && i < deleteCount; i++) {
    ret.push(walker.value);
    walker = this.removeNode(walker);
  }
  if (walker === null) {
    walker = this.tail;
  }

  if (walker !== this.head && walker !== this.tail) {
    walker = walker.prev;
  }

  for (var i = 0; i < nodes.length; i++) {
    walker = insert(this, walker, nodes[i]);
  }
  return ret;
};

Yallist.prototype.reverse = function () {
  var head = this.head;
  var tail = this.tail;
  for (var walker = head; walker !== null; walker = walker.prev) {
    var p = walker.prev;
    walker.prev = walker.next;
    walker.next = p;
  }
  this.head = tail;
  this.tail = head;
  return this
};

function insert (self, node, value) {
  var inserted = node === self.head ?
    new Node(value, null, node, self) :
    new Node(value, node, node.next, self);

  if (inserted.next === null) {
    self.tail = inserted;
  }
  if (inserted.prev === null) {
    self.head = inserted;
  }

  self.length++;

  return inserted
}

function push (self, item) {
  self.tail = new Node(item, self.tail, null, self);
  if (!self.head) {
    self.head = self.tail;
  }
  self.length++;
}

function unshift (self, item) {
  self.head = new Node(item, null, self.head, self);
  if (!self.tail) {
    self.tail = self.head;
  }
  self.length++;
}

function Node (value, prev, next, list) {
  if (!(this instanceof Node)) {
    return new Node(value, prev, next, list)
  }

  this.list = list;
  this.value = value;

  if (prev) {
    prev.next = this;
    this.prev = prev;
  } else {
    this.prev = null;
  }

  if (next) {
    next.prev = this;
    this.next = next;
  } else {
    this.next = null;
  }
}

try {
  // add if support for Symbol.iterator is present
  iterator(Yallist);
} catch (er) {}

// A linked list to keep track of recently-used-ness


const MAX = Symbol('max');
const LENGTH = Symbol('length');
const LENGTH_CALCULATOR = Symbol('lengthCalculator');
const ALLOW_STALE = Symbol('allowStale');
const MAX_AGE = Symbol('maxAge');
const DISPOSE = Symbol('dispose');
const NO_DISPOSE_ON_SET = Symbol('noDisposeOnSet');
const LRU_LIST = Symbol('lruList');
const CACHE = Symbol('cache');
const UPDATE_AGE_ON_GET = Symbol('updateAgeOnGet');

const naiveLength = () => 1;

// lruList is a yallist where the head is the youngest
// item, and the tail is the oldest.  the list contains the Hit
// objects as the entries.
// Each Hit object has a reference to its Yallist.Node.  This
// never changes.
//
// cache is a Map (or PseudoMap) that matches the keys to
// the Yallist.Node object.
class LRUCache {
  constructor (options) {
    if (typeof options === 'number')
      options = { max: options };

    if (!options)
      options = {};

    if (options.max && (typeof options.max !== 'number' || options.max < 0))
      throw new TypeError('max must be a non-negative number')
    // Kind of weird to have a default max of Infinity, but oh well.
    const max = this[MAX] = options.max || Infinity;

    const lc = options.length || naiveLength;
    this[LENGTH_CALCULATOR] = (typeof lc !== 'function') ? naiveLength : lc;
    this[ALLOW_STALE] = options.stale || false;
    if (options.maxAge && typeof options.maxAge !== 'number')
      throw new TypeError('maxAge must be a number')
    this[MAX_AGE] = options.maxAge || 0;
    this[DISPOSE] = options.dispose;
    this[NO_DISPOSE_ON_SET] = options.noDisposeOnSet || false;
    this[UPDATE_AGE_ON_GET] = options.updateAgeOnGet || false;
    this.reset();
  }

  // resize the cache when the max changes.
  set max (mL) {
    if (typeof mL !== 'number' || mL < 0)
      throw new TypeError('max must be a non-negative number')

    this[MAX] = mL || Infinity;
    trim(this);
  }
  get max () {
    return this[MAX]
  }

  set allowStale (allowStale) {
    this[ALLOW_STALE] = !!allowStale;
  }
  get allowStale () {
    return this[ALLOW_STALE]
  }

  set maxAge (mA) {
    if (typeof mA !== 'number')
      throw new TypeError('maxAge must be a non-negative number')

    this[MAX_AGE] = mA;
    trim(this);
  }
  get maxAge () {
    return this[MAX_AGE]
  }

  // resize the cache when the lengthCalculator changes.
  set lengthCalculator (lC) {
    if (typeof lC !== 'function')
      lC = naiveLength;

    if (lC !== this[LENGTH_CALCULATOR]) {
      this[LENGTH_CALCULATOR] = lC;
      this[LENGTH] = 0;
      this[LRU_LIST].forEach(hit => {
        hit.length = this[LENGTH_CALCULATOR](hit.value, hit.key);
        this[LENGTH] += hit.length;
      });
    }
    trim(this);
  }
  get lengthCalculator () { return this[LENGTH_CALCULATOR] }

  get length () { return this[LENGTH] }
  get itemCount () { return this[LRU_LIST].length }

  rforEach (fn, thisp) {
    thisp = thisp || this;
    for (let walker = this[LRU_LIST].tail; walker !== null;) {
      const prev = walker.prev;
      forEachStep(this, fn, walker, thisp);
      walker = prev;
    }
  }

  forEach (fn, thisp) {
    thisp = thisp || this;
    for (let walker = this[LRU_LIST].head; walker !== null;) {
      const next = walker.next;
      forEachStep(this, fn, walker, thisp);
      walker = next;
    }
  }

  keys () {
    return this[LRU_LIST].toArray().map(k => k.key)
  }

  values () {
    return this[LRU_LIST].toArray().map(k => k.value)
  }

  reset () {
    if (this[DISPOSE] &&
        this[LRU_LIST] &&
        this[LRU_LIST].length) {
      this[LRU_LIST].forEach(hit => this[DISPOSE](hit.key, hit.value));
    }

    this[CACHE] = new Map(); // hash of items by key
    this[LRU_LIST] = new yallist(); // list of items in order of use recency
    this[LENGTH] = 0; // length of items in the list
  }

  dump () {
    return this[LRU_LIST].map(hit =>
      isStale(this, hit) ? false : {
        k: hit.key,
        v: hit.value,
        e: hit.now + (hit.maxAge || 0)
      }).toArray().filter(h => h)
  }

  dumpLru () {
    return this[LRU_LIST]
  }

  set (key, value, maxAge) {
    maxAge = maxAge || this[MAX_AGE];

    if (maxAge && typeof maxAge !== 'number')
      throw new TypeError('maxAge must be a number')

    const now = maxAge ? Date.now() : 0;
    const len = this[LENGTH_CALCULATOR](value, key);

    if (this[CACHE].has(key)) {
      if (len > this[MAX]) {
        del(this, this[CACHE].get(key));
        return false
      }

      const node = this[CACHE].get(key);
      const item = node.value;

      // dispose of the old one before overwriting
      // split out into 2 ifs for better coverage tracking
      if (this[DISPOSE]) {
        if (!this[NO_DISPOSE_ON_SET])
          this[DISPOSE](key, item.value);
      }

      item.now = now;
      item.maxAge = maxAge;
      item.value = value;
      this[LENGTH] += len - item.length;
      item.length = len;
      this.get(key);
      trim(this);
      return true
    }

    const hit = new Entry(key, value, len, now, maxAge);

    // oversized objects fall out of cache automatically.
    if (hit.length > this[MAX]) {
      if (this[DISPOSE])
        this[DISPOSE](key, value);

      return false
    }

    this[LENGTH] += hit.length;
    this[LRU_LIST].unshift(hit);
    this[CACHE].set(key, this[LRU_LIST].head);
    trim(this);
    return true
  }

  has (key) {
    if (!this[CACHE].has(key)) return false
    const hit = this[CACHE].get(key).value;
    return !isStale(this, hit)
  }

  get (key) {
    return get(this, key, true)
  }

  peek (key) {
    return get(this, key, false)
  }

  pop () {
    const node = this[LRU_LIST].tail;
    if (!node)
      return null

    del(this, node);
    return node.value
  }

  del (key) {
    del(this, this[CACHE].get(key));
  }

  load (arr) {
    // reset the cache
    this.reset();

    const now = Date.now();
    // A previous serialized cache has the most recent items first
    for (let l = arr.length - 1; l >= 0; l--) {
      const hit = arr[l];
      const expiresAt = hit.e || 0;
      if (expiresAt === 0)
        // the item was created without expiration in a non aged cache
        this.set(hit.k, hit.v);
      else {
        const maxAge = expiresAt - now;
        // dont add already expired items
        if (maxAge > 0) {
          this.set(hit.k, hit.v, maxAge);
        }
      }
    }
  }

  prune () {
    this[CACHE].forEach((value, key) => get(this, key, false));
  }
}

const get = (self, key, doUse) => {
  const node = self[CACHE].get(key);
  if (node) {
    const hit = node.value;
    if (isStale(self, hit)) {
      del(self, node);
      if (!self[ALLOW_STALE])
        return undefined
    } else {
      if (doUse) {
        if (self[UPDATE_AGE_ON_GET])
          node.value.now = Date.now();
        self[LRU_LIST].unshiftNode(node);
      }
    }
    return hit.value
  }
};

const isStale = (self, hit) => {
  if (!hit || (!hit.maxAge && !self[MAX_AGE]))
    return false

  const diff = Date.now() - hit.now;
  return hit.maxAge ? diff > hit.maxAge
    : self[MAX_AGE] && (diff > self[MAX_AGE])
};

const trim = self => {
  if (self[LENGTH] > self[MAX]) {
    for (let walker = self[LRU_LIST].tail;
      self[LENGTH] > self[MAX] && walker !== null;) {
      // We know that we're about to delete this one, and also
      // what the next least recently used key will be, so just
      // go ahead and set it now.
      const prev = walker.prev;
      del(self, walker);
      walker = prev;
    }
  }
};

const del = (self, node) => {
  if (node) {
    const hit = node.value;
    if (self[DISPOSE])
      self[DISPOSE](hit.key, hit.value);

    self[LENGTH] -= hit.length;
    self[CACHE].delete(hit.key);
    self[LRU_LIST].removeNode(node);
  }
};

class Entry {
  constructor (key, value, length, now, maxAge) {
    this.key = key;
    this.value = value;
    this.length = length;
    this.now = now;
    this.maxAge = maxAge || 0;
  }
}

const forEachStep = (self, fn, node, thisp) => {
  let hit = node.value;
  if (isStale(self, hit)) {
    del(self, node);
    if (!self[ALLOW_STALE])
      hit = undefined;
  }
  if (hit)
    fn.call(thisp, hit.value, hit.key, self);
};

var lruCache = LRUCache;

// hoisted class for cyclic dependency
class Range {
  constructor (range, options) {
    options = parseOptions_1(options);

    if (range instanceof Range) {
      if (
        range.loose === !!options.loose &&
        range.includePrerelease === !!options.includePrerelease
      ) {
        return range
      } else {
        return new Range(range.raw, options)
      }
    }

    if (range instanceof comparator) {
      // just put it in the set and return
      this.raw = range.value;
      this.set = [[range]];
      this.format();
      return this
    }

    this.options = options;
    this.loose = !!options.loose;
    this.includePrerelease = !!options.includePrerelease;

    // First, split based on boolean or ||
    this.raw = range;
    this.set = range
      .split(/\s*\|\|\s*/)
      // map the range to a 2d array of comparators
      .map(range => this.parseRange(range.trim()))
      // throw out any comparator lists that are empty
      // this generally means that it was not a valid range, which is allowed
      // in loose mode, but will still throw if the WHOLE range is invalid.
      .filter(c => c.length);

    if (!this.set.length) {
      throw new TypeError(`Invalid SemVer Range: ${range}`)
    }

    // if we have any that are not the null set, throw out null sets.
    if (this.set.length > 1) {
      // keep the first one, in case they're all null sets
      const first = this.set[0];
      this.set = this.set.filter(c => !isNullSet(c[0]));
      if (this.set.length === 0)
        this.set = [first];
      else if (this.set.length > 1) {
        // if we have any that are *, then the range is just *
        for (const c of this.set) {
          if (c.length === 1 && isAny(c[0])) {
            this.set = [c];
            break
          }
        }
      }
    }

    this.format();
  }

  format () {
    this.range = this.set
      .map((comps) => {
        return comps.join(' ').trim()
      })
      .join('||')
      .trim();
    return this.range
  }

  toString () {
    return this.range
  }

  parseRange (range) {
    range = range.trim();

    // memoize range parsing for performance.
    // this is a very hot path, and fully deterministic.
    const memoOpts = Object.keys(this.options).join(',');
    const memoKey = `parseRange:${memoOpts}:${range}`;
    const cached = cache.get(memoKey);
    if (cached)
      return cached

    const loose = this.options.loose;
    // `1.2.3 - 1.2.4` => `>=1.2.3 <=1.2.4`
    const hr = loose ? re$3[t$3.HYPHENRANGELOOSE] : re$3[t$3.HYPHENRANGE];
    range = range.replace(hr, hyphenReplace(this.options.includePrerelease));
    debug_1('hyphen replace', range);
    // `> 1.2.3 < 1.2.5` => `>1.2.3 <1.2.5`
    range = range.replace(re$3[t$3.COMPARATORTRIM], comparatorTrimReplace);
    debug_1('comparator trim', range, re$3[t$3.COMPARATORTRIM]);

    // `~ 1.2.3` => `~1.2.3`
    range = range.replace(re$3[t$3.TILDETRIM], tildeTrimReplace);

    // `^ 1.2.3` => `^1.2.3`
    range = range.replace(re$3[t$3.CARETTRIM], caretTrimReplace);

    // normalize spaces
    range = range.split(/\s+/).join(' ');

    // At this point, the range is completely trimmed and
    // ready to be split into comparators.

    const compRe = loose ? re$3[t$3.COMPARATORLOOSE] : re$3[t$3.COMPARATOR];
    const rangeList = range
      .split(' ')
      .map(comp => parseComparator(comp, this.options))
      .join(' ')
      .split(/\s+/)
      // >=0.0.0 is equivalent to *
      .map(comp => replaceGTE0(comp, this.options))
      // in loose mode, throw out any that are not valid comparators
      .filter(this.options.loose ? comp => !!comp.match(compRe) : () => true)
      .map(comp => new comparator(comp, this.options));

    // if any comparators are the null set, then replace with JUST null set
    // if more than one comparator, remove any * comparators
    // also, don't include the same comparator more than once
    const l = rangeList.length;
    const rangeMap = new Map();
    for (const comp of rangeList) {
      if (isNullSet(comp))
        return [comp]
      rangeMap.set(comp.value, comp);
    }
    if (rangeMap.size > 1 && rangeMap.has(''))
      rangeMap.delete('');

    const result = [...rangeMap.values()];
    cache.set(memoKey, result);
    return result
  }

  intersects (range, options) {
    if (!(range instanceof Range)) {
      throw new TypeError('a Range is required')
    }

    return this.set.some((thisComparators) => {
      return (
        isSatisfiable(thisComparators, options) &&
        range.set.some((rangeComparators) => {
          return (
            isSatisfiable(rangeComparators, options) &&
            thisComparators.every((thisComparator) => {
              return rangeComparators.every((rangeComparator) => {
                return thisComparator.intersects(rangeComparator, options)
              })
            })
          )
        })
      )
    })
  }

  // if ANY of the sets match ALL of its comparators, then pass
  test (version) {
    if (!version) {
      return false
    }

    if (typeof version === 'string') {
      try {
        version = new semver(version, this.options);
      } catch (er) {
        return false
      }
    }

    for (let i = 0; i < this.set.length; i++) {
      if (testSet(this.set[i], version, this.options)) {
        return true
      }
    }
    return false
  }
}
var range = Range;


const cache = new lruCache({ max: 1000 });





const {
  re: re$3,
  t: t$3,
  comparatorTrimReplace,
  tildeTrimReplace,
  caretTrimReplace
} = re_1;

const isNullSet = c => c.value === '<0.0.0-0';
const isAny = c => c.value === '';

// take a set of comparators and determine whether there
// exists a version which can satisfy it
const isSatisfiable = (comparators, options) => {
  let result = true;
  const remainingComparators = comparators.slice();
  let testComparator = remainingComparators.pop();

  while (result && remainingComparators.length) {
    result = remainingComparators.every((otherComparator) => {
      return testComparator.intersects(otherComparator, options)
    });

    testComparator = remainingComparators.pop();
  }

  return result
};

// comprised of xranges, tildes, stars, and gtlt's at this point.
// already replaced the hyphen ranges
// turn into a set of JUST comparators.
const parseComparator = (comp, options) => {
  debug_1('comp', comp, options);
  comp = replaceCarets(comp, options);
  debug_1('caret', comp);
  comp = replaceTildes(comp, options);
  debug_1('tildes', comp);
  comp = replaceXRanges(comp, options);
  debug_1('xrange', comp);
  comp = replaceStars(comp, options);
  debug_1('stars', comp);
  return comp
};

const isX = id => !id || id.toLowerCase() === 'x' || id === '*';

// ~, ~> --> * (any, kinda silly)
// ~2, ~2.x, ~2.x.x, ~>2, ~>2.x ~>2.x.x --> >=2.0.0 <3.0.0-0
// ~2.0, ~2.0.x, ~>2.0, ~>2.0.x --> >=2.0.0 <2.1.0-0
// ~1.2, ~1.2.x, ~>1.2, ~>1.2.x --> >=1.2.0 <1.3.0-0
// ~1.2.3, ~>1.2.3 --> >=1.2.3 <1.3.0-0
// ~1.2.0, ~>1.2.0 --> >=1.2.0 <1.3.0-0
const replaceTildes = (comp, options) =>
  comp.trim().split(/\s+/).map((comp) => {
    return replaceTilde(comp, options)
  }).join(' ');

const replaceTilde = (comp, options) => {
  const r = options.loose ? re$3[t$3.TILDELOOSE] : re$3[t$3.TILDE];
  return comp.replace(r, (_, M, m, p, pr) => {
    debug_1('tilde', comp, _, M, m, p, pr);
    let ret;

    if (isX(M)) {
      ret = '';
    } else if (isX(m)) {
      ret = `>=${M}.0.0 <${+M + 1}.0.0-0`;
    } else if (isX(p)) {
      // ~1.2 == >=1.2.0 <1.3.0-0
      ret = `>=${M}.${m}.0 <${M}.${+m + 1}.0-0`;
    } else if (pr) {
      debug_1('replaceTilde pr', pr);
      ret = `>=${M}.${m}.${p}-${pr
      } <${M}.${+m + 1}.0-0`;
    } else {
      // ~1.2.3 == >=1.2.3 <1.3.0-0
      ret = `>=${M}.${m}.${p
      } <${M}.${+m + 1}.0-0`;
    }

    debug_1('tilde return', ret);
    return ret
  })
};

// ^ --> * (any, kinda silly)
// ^2, ^2.x, ^2.x.x --> >=2.0.0 <3.0.0-0
// ^2.0, ^2.0.x --> >=2.0.0 <3.0.0-0
// ^1.2, ^1.2.x --> >=1.2.0 <2.0.0-0
// ^1.2.3 --> >=1.2.3 <2.0.0-0
// ^1.2.0 --> >=1.2.0 <2.0.0-0
const replaceCarets = (comp, options) =>
  comp.trim().split(/\s+/).map((comp) => {
    return replaceCaret(comp, options)
  }).join(' ');

const replaceCaret = (comp, options) => {
  debug_1('caret', comp, options);
  const r = options.loose ? re$3[t$3.CARETLOOSE] : re$3[t$3.CARET];
  const z = options.includePrerelease ? '-0' : '';
  return comp.replace(r, (_, M, m, p, pr) => {
    debug_1('caret', comp, _, M, m, p, pr);
    let ret;

    if (isX(M)) {
      ret = '';
    } else if (isX(m)) {
      ret = `>=${M}.0.0${z} <${+M + 1}.0.0-0`;
    } else if (isX(p)) {
      if (M === '0') {
        ret = `>=${M}.${m}.0${z} <${M}.${+m + 1}.0-0`;
      } else {
        ret = `>=${M}.${m}.0${z} <${+M + 1}.0.0-0`;
      }
    } else if (pr) {
      debug_1('replaceCaret pr', pr);
      if (M === '0') {
        if (m === '0') {
          ret = `>=${M}.${m}.${p}-${pr
          } <${M}.${m}.${+p + 1}-0`;
        } else {
          ret = `>=${M}.${m}.${p}-${pr
          } <${M}.${+m + 1}.0-0`;
        }
      } else {
        ret = `>=${M}.${m}.${p}-${pr
        } <${+M + 1}.0.0-0`;
      }
    } else {
      debug_1('no pr');
      if (M === '0') {
        if (m === '0') {
          ret = `>=${M}.${m}.${p
          }${z} <${M}.${m}.${+p + 1}-0`;
        } else {
          ret = `>=${M}.${m}.${p
          }${z} <${M}.${+m + 1}.0-0`;
        }
      } else {
        ret = `>=${M}.${m}.${p
        } <${+M + 1}.0.0-0`;
      }
    }

    debug_1('caret return', ret);
    return ret
  })
};

const replaceXRanges = (comp, options) => {
  debug_1('replaceXRanges', comp, options);
  return comp.split(/\s+/).map((comp) => {
    return replaceXRange(comp, options)
  }).join(' ')
};

const replaceXRange = (comp, options) => {
  comp = comp.trim();
  const r = options.loose ? re$3[t$3.XRANGELOOSE] : re$3[t$3.XRANGE];
  return comp.replace(r, (ret, gtlt, M, m, p, pr) => {
    debug_1('xRange', comp, ret, gtlt, M, m, p, pr);
    const xM = isX(M);
    const xm = xM || isX(m);
    const xp = xm || isX(p);
    const anyX = xp;

    if (gtlt === '=' && anyX) {
      gtlt = '';
    }

    // if we're including prereleases in the match, then we need
    // to fix this to -0, the lowest possible prerelease value
    pr = options.includePrerelease ? '-0' : '';

    if (xM) {
      if (gtlt === '>' || gtlt === '<') {
        // nothing is allowed
        ret = '<0.0.0-0';
      } else {
        // nothing is forbidden
        ret = '*';
      }
    } else if (gtlt && anyX) {
      // we know patch is an x, because we have any x at all.
      // replace X with 0
      if (xm) {
        m = 0;
      }
      p = 0;

      if (gtlt === '>') {
        // >1 => >=2.0.0
        // >1.2 => >=1.3.0
        gtlt = '>=';
        if (xm) {
          M = +M + 1;
          m = 0;
          p = 0;
        } else {
          m = +m + 1;
          p = 0;
        }
      } else if (gtlt === '<=') {
        // <=0.7.x is actually <0.8.0, since any 0.7.x should
        // pass.  Similarly, <=7.x is actually <8.0.0, etc.
        gtlt = '<';
        if (xm) {
          M = +M + 1;
        } else {
          m = +m + 1;
        }
      }

      if (gtlt === '<')
        pr = '-0';

      ret = `${gtlt + M}.${m}.${p}${pr}`;
    } else if (xm) {
      ret = `>=${M}.0.0${pr} <${+M + 1}.0.0-0`;
    } else if (xp) {
      ret = `>=${M}.${m}.0${pr
      } <${M}.${+m + 1}.0-0`;
    }

    debug_1('xRange return', ret);

    return ret
  })
};

// Because * is AND-ed with everything else in the comparator,
// and '' means "any version", just remove the *s entirely.
const replaceStars = (comp, options) => {
  debug_1('replaceStars', comp, options);
  // Looseness is ignored here.  star is always as loose as it gets!
  return comp.trim().replace(re$3[t$3.STAR], '')
};

const replaceGTE0 = (comp, options) => {
  debug_1('replaceGTE0', comp, options);
  return comp.trim()
    .replace(re$3[options.includePrerelease ? t$3.GTE0PRE : t$3.GTE0], '')
};

// This function is passed to string.replace(re[t.HYPHENRANGE])
// M, m, patch, prerelease, build
// 1.2 - 3.4.5 => >=1.2.0 <=3.4.5
// 1.2.3 - 3.4 => >=1.2.0 <3.5.0-0 Any 3.4.x will do
// 1.2 - 3.4 => >=1.2.0 <3.5.0-0
const hyphenReplace = incPr => ($0,
  from, fM, fm, fp, fpr, fb,
  to, tM, tm, tp, tpr, tb) => {
  if (isX(fM)) {
    from = '';
  } else if (isX(fm)) {
    from = `>=${fM}.0.0${incPr ? '-0' : ''}`;
  } else if (isX(fp)) {
    from = `>=${fM}.${fm}.0${incPr ? '-0' : ''}`;
  } else if (fpr) {
    from = `>=${from}`;
  } else {
    from = `>=${from}${incPr ? '-0' : ''}`;
  }

  if (isX(tM)) {
    to = '';
  } else if (isX(tm)) {
    to = `<${+tM + 1}.0.0-0`;
  } else if (isX(tp)) {
    to = `<${tM}.${+tm + 1}.0-0`;
  } else if (tpr) {
    to = `<=${tM}.${tm}.${tp}-${tpr}`;
  } else if (incPr) {
    to = `<${tM}.${tm}.${+tp + 1}-0`;
  } else {
    to = `<=${to}`;
  }

  return (`${from} ${to}`).trim()
};

const testSet = (set, version, options) => {
  for (let i = 0; i < set.length; i++) {
    if (!set[i].test(version)) {
      return false
    }
  }

  if (version.prerelease.length && !options.includePrerelease) {
    // Find the set of versions that are allowed to have prereleases
    // For example, ^1.2.3-pr.1 desugars to >=1.2.3-pr.1 <2.0.0
    // That should allow `1.2.3-pr.2` to pass.
    // However, `1.2.4-alpha.notready` should NOT be allowed,
    // even though it's within the range set by the comparators.
    for (let i = 0; i < set.length; i++) {
      debug_1(set[i].semver);
      if (set[i].semver === comparator.ANY) {
        continue
      }

      if (set[i].semver.prerelease.length > 0) {
        const allowed = set[i].semver;
        if (allowed.major === version.major &&
            allowed.minor === version.minor &&
            allowed.patch === version.patch) {
          return true
        }
      }
    }

    // Version has a -pre, but it's not one of the ones we like.
    return false
  }

  return true
};

const ANY = Symbol('SemVer ANY');
// hoisted class for cyclic dependency
class Comparator {
  static get ANY () {
    return ANY
  }
  constructor (comp, options) {
    options = parseOptions_1(options);

    if (comp instanceof Comparator) {
      if (comp.loose === !!options.loose) {
        return comp
      } else {
        comp = comp.value;
      }
    }

    debug_1('comparator', comp, options);
    this.options = options;
    this.loose = !!options.loose;
    this.parse(comp);

    if (this.semver === ANY) {
      this.value = '';
    } else {
      this.value = this.operator + this.semver.version;
    }

    debug_1('comp', this);
  }

  parse (comp) {
    const r = this.options.loose ? re$4[t$4.COMPARATORLOOSE] : re$4[t$4.COMPARATOR];
    const m = comp.match(r);

    if (!m) {
      throw new TypeError(`Invalid comparator: ${comp}`)
    }

    this.operator = m[1] !== undefined ? m[1] : '';
    if (this.operator === '=') {
      this.operator = '';
    }

    // if it literally is just '>' or '' then allow anything.
    if (!m[2]) {
      this.semver = ANY;
    } else {
      this.semver = new semver(m[2], this.options.loose);
    }
  }

  toString () {
    return this.value
  }

  test (version) {
    debug_1('Comparator.test', version, this.options.loose);

    if (this.semver === ANY || version === ANY) {
      return true
    }

    if (typeof version === 'string') {
      try {
        version = new semver(version, this.options);
      } catch (er) {
        return false
      }
    }

    return cmp_1(version, this.operator, this.semver, this.options)
  }

  intersects (comp, options) {
    if (!(comp instanceof Comparator)) {
      throw new TypeError('a Comparator is required')
    }

    if (!options || typeof options !== 'object') {
      options = {
        loose: !!options,
        includePrerelease: false
      };
    }

    if (this.operator === '') {
      if (this.value === '') {
        return true
      }
      return new range(comp.value, options).test(this.value)
    } else if (comp.operator === '') {
      if (comp.value === '') {
        return true
      }
      return new range(this.value, options).test(comp.semver)
    }

    const sameDirectionIncreasing =
      (this.operator === '>=' || this.operator === '>') &&
      (comp.operator === '>=' || comp.operator === '>');
    const sameDirectionDecreasing =
      (this.operator === '<=' || this.operator === '<') &&
      (comp.operator === '<=' || comp.operator === '<');
    const sameSemVer = this.semver.version === comp.semver.version;
    const differentDirectionsInclusive =
      (this.operator === '>=' || this.operator === '<=') &&
      (comp.operator === '>=' || comp.operator === '<=');
    const oppositeDirectionsLessThan =
      cmp_1(this.semver, '<', comp.semver, options) &&
      (this.operator === '>=' || this.operator === '>') &&
        (comp.operator === '<=' || comp.operator === '<');
    const oppositeDirectionsGreaterThan =
      cmp_1(this.semver, '>', comp.semver, options) &&
      (this.operator === '<=' || this.operator === '<') &&
        (comp.operator === '>=' || comp.operator === '>');

    return (
      sameDirectionIncreasing ||
      sameDirectionDecreasing ||
      (sameSemVer && differentDirectionsInclusive) ||
      oppositeDirectionsLessThan ||
      oppositeDirectionsGreaterThan
    )
  }
}

var comparator = Comparator;


const {re: re$4, t: t$4} = re_1;

const satisfies = (version, range$1, options) => {
  try {
    range$1 = new range(range$1, options);
  } catch (er) {
    return false
  }
  return range$1.test(version)
};
var satisfies_1 = satisfies;

// Mostly just for testing and legacy API reasons
const toComparators = (range$1, options) =>
  new range(range$1, options).set
    .map(comp => comp.map(c => c.value).join(' ').trim().split(' '));

var toComparators_1 = toComparators;

const maxSatisfying = (versions, range$1, options) => {
  let max = null;
  let maxSV = null;
  let rangeObj = null;
  try {
    rangeObj = new range(range$1, options);
  } catch (er) {
    return null
  }
  versions.forEach((v) => {
    if (rangeObj.test(v)) {
      // satisfies(v, range, options)
      if (!max || maxSV.compare(v) === -1) {
        // compare(max, v, true)
        max = v;
        maxSV = new semver(max, options);
      }
    }
  });
  return max
};
var maxSatisfying_1 = maxSatisfying;

const minSatisfying = (versions, range$1, options) => {
  let min = null;
  let minSV = null;
  let rangeObj = null;
  try {
    rangeObj = new range(range$1, options);
  } catch (er) {
    return null
  }
  versions.forEach((v) => {
    if (rangeObj.test(v)) {
      // satisfies(v, range, options)
      if (!min || minSV.compare(v) === 1) {
        // compare(min, v, true)
        min = v;
        minSV = new semver(min, options);
      }
    }
  });
  return min
};
var minSatisfying_1 = minSatisfying;

const minVersion = (range$1, loose) => {
  range$1 = new range(range$1, loose);

  let minver = new semver('0.0.0');
  if (range$1.test(minver)) {
    return minver
  }

  minver = new semver('0.0.0-0');
  if (range$1.test(minver)) {
    return minver
  }

  minver = null;
  for (let i = 0; i < range$1.set.length; ++i) {
    const comparators = range$1.set[i];

    let setMin = null;
    comparators.forEach((comparator) => {
      // Clone to avoid manipulating the comparator's semver object.
      const compver = new semver(comparator.semver.version);
      switch (comparator.operator) {
        case '>':
          if (compver.prerelease.length === 0) {
            compver.patch++;
          } else {
            compver.prerelease.push(0);
          }
          compver.raw = compver.format();
          /* fallthrough */
        case '':
        case '>=':
          if (!setMin || gt_1(compver, setMin)) {
            setMin = compver;
          }
          break
        case '<':
        case '<=':
          /* Ignore maximum versions */
          break
        /* istanbul ignore next */
        default:
          throw new Error(`Unexpected operation: ${comparator.operator}`)
      }
    });
    if (setMin && (!minver || gt_1(minver, setMin)))
      minver = setMin;
  }

  if (minver && range$1.test(minver)) {
    return minver
  }

  return null
};
var minVersion_1 = minVersion;

const validRange = (range$1, options) => {
  try {
    // Return '*' instead of '' so that truthiness works.
    // This will throw if it's invalid anyway
    return new range(range$1, options).range || '*'
  } catch (er) {
    return null
  }
};
var valid$1 = validRange;

const {ANY: ANY$1} = comparator;







const outside = (version, range$1, hilo, options) => {
  version = new semver(version, options);
  range$1 = new range(range$1, options);

  let gtfn, ltefn, ltfn, comp, ecomp;
  switch (hilo) {
    case '>':
      gtfn = gt_1;
      ltefn = lte_1;
      ltfn = lt_1;
      comp = '>';
      ecomp = '>=';
      break
    case '<':
      gtfn = lt_1;
      ltefn = gte_1;
      ltfn = gt_1;
      comp = '<';
      ecomp = '<=';
      break
    default:
      throw new TypeError('Must provide a hilo val of "<" or ">"')
  }

  // If it satisfies the range it is not outside
  if (satisfies_1(version, range$1, options)) {
    return false
  }

  // From now on, variable terms are as if we're in "gtr" mode.
  // but note that everything is flipped for the "ltr" function.

  for (let i = 0; i < range$1.set.length; ++i) {
    const comparators = range$1.set[i];

    let high = null;
    let low = null;

    comparators.forEach((comparator$1) => {
      if (comparator$1.semver === ANY$1) {
        comparator$1 = new comparator('>=0.0.0');
      }
      high = high || comparator$1;
      low = low || comparator$1;
      if (gtfn(comparator$1.semver, high.semver, options)) {
        high = comparator$1;
      } else if (ltfn(comparator$1.semver, low.semver, options)) {
        low = comparator$1;
      }
    });

    // If the edge version comparator has a operator then our version
    // isn't outside it
    if (high.operator === comp || high.operator === ecomp) {
      return false
    }

    // If the lowest version comparator has an operator and our version
    // is less than it then it isn't higher than the range
    if ((!low.operator || low.operator === comp) &&
        ltefn(version, low.semver)) {
      return false
    } else if (low.operator === ecomp && ltfn(version, low.semver)) {
      return false
    }
  }
  return true
};

var outside_1 = outside;

// Determine if version is greater than all the versions possible in the range.

const gtr = (version, range, options) => outside_1(version, range, '>', options);
var gtr_1 = gtr;

// Determine if version is less than all the versions possible in the range
const ltr = (version, range, options) => outside_1(version, range, '<', options);
var ltr_1 = ltr;

const intersects = (r1, r2, options) => {
  r1 = new range(r1, options);
  r2 = new range(r2, options);
  return r1.intersects(r2)
};
var intersects_1 = intersects;

// given a set of versions and a range, create a "simplified" range
// that includes the same versions that the original range does
// If the original range is shorter than the simplified one, return that.


var simplify = (versions, range, options) => {
  const set = [];
  let min = null;
  let prev = null;
  const v = versions.sort((a, b) => compare_1(a, b, options));
  for (const version of v) {
    const included = satisfies_1(version, range, options);
    if (included) {
      prev = version;
      if (!min)
        min = version;
    } else {
      if (prev) {
        set.push([min, prev]);
      }
      prev = null;
      min = null;
    }
  }
  if (min)
    set.push([min, null]);

  const ranges = [];
  for (const [min, max] of set) {
    if (min === max)
      ranges.push(min);
    else if (!max && min === v[0])
      ranges.push('*');
    else if (!max)
      ranges.push(`>=${min}`);
    else if (min === v[0])
      ranges.push(`<=${max}`);
    else
      ranges.push(`${min} - ${max}`);
  }
  const simplified = ranges.join(' || ');
  const original = typeof range.raw === 'string' ? range.raw : String(range);
  return simplified.length < original.length ? simplified : range
};

const { ANY: ANY$2 } = comparator;



// Complex range `r1 || r2 || ...` is a subset of `R1 || R2 || ...` iff:
// - Every simple range `r1, r2, ...` is a subset of some `R1, R2, ...`
//
// Simple range `c1 c2 ...` is a subset of simple range `C1 C2 ...` iff:
// - If c is only the ANY comparator
//   - If C is only the ANY comparator, return true
//   - Else return false
// - Let EQ be the set of = comparators in c
// - If EQ is more than one, return true (null set)
// - Let GT be the highest > or >= comparator in c
// - Let LT be the lowest < or <= comparator in c
// - If GT and LT, and GT.semver > LT.semver, return true (null set)
// - If EQ
//   - If GT, and EQ does not satisfy GT, return true (null set)
//   - If LT, and EQ does not satisfy LT, return true (null set)
//   - If EQ satisfies every C, return true
//   - Else return false
// - If GT
//   - If GT.semver is lower than any > or >= comp in C, return false
//   - If GT is >=, and GT.semver does not satisfy every C, return false
// - If LT
//   - If LT.semver is greater than any < or <= comp in C, return false
//   - If LT is <=, and LT.semver does not satisfy every C, return false
// - If any C is a = range, and GT or LT are set, return false
// - Else return true

const subset = (sub, dom, options) => {
  if (sub === dom)
    return true

  sub = new range(sub, options);
  dom = new range(dom, options);
  let sawNonNull = false;

  OUTER: for (const simpleSub of sub.set) {
    for (const simpleDom of dom.set) {
      const isSub = simpleSubset(simpleSub, simpleDom, options);
      sawNonNull = sawNonNull || isSub !== null;
      if (isSub)
        continue OUTER
    }
    // the null set is a subset of everything, but null simple ranges in
    // a complex range should be ignored.  so if we saw a non-null range,
    // then we know this isn't a subset, but if EVERY simple range was null,
    // then it is a subset.
    if (sawNonNull)
      return false
  }
  return true
};

const simpleSubset = (sub, dom, options) => {
  if (sub === dom)
    return true

  if (sub.length === 1 && sub[0].semver === ANY$2)
    return dom.length === 1 && dom[0].semver === ANY$2

  const eqSet = new Set();
  let gt, lt;
  for (const c of sub) {
    if (c.operator === '>' || c.operator === '>=')
      gt = higherGT(gt, c, options);
    else if (c.operator === '<' || c.operator === '<=')
      lt = lowerLT(lt, c, options);
    else
      eqSet.add(c.semver);
  }

  if (eqSet.size > 1)
    return null

  let gtltComp;
  if (gt && lt) {
    gtltComp = compare_1(gt.semver, lt.semver, options);
    if (gtltComp > 0)
      return null
    else if (gtltComp === 0 && (gt.operator !== '>=' || lt.operator !== '<='))
      return null
  }

  // will iterate one or zero times
  for (const eq of eqSet) {
    if (gt && !satisfies_1(eq, String(gt), options))
      return null

    if (lt && !satisfies_1(eq, String(lt), options))
      return null

    for (const c of dom) {
      if (!satisfies_1(eq, String(c), options))
        return false
    }

    return true
  }

  let higher, lower;
  let hasDomLT, hasDomGT;
  for (const c of dom) {
    hasDomGT = hasDomGT || c.operator === '>' || c.operator === '>=';
    hasDomLT = hasDomLT || c.operator === '<' || c.operator === '<=';
    if (gt) {
      if (c.operator === '>' || c.operator === '>=') {
        higher = higherGT(gt, c, options);
        if (higher === c && higher !== gt)
          return false
      } else if (gt.operator === '>=' && !satisfies_1(gt.semver, String(c), options))
        return false
    }
    if (lt) {
      if (c.operator === '<' || c.operator === '<=') {
        lower = lowerLT(lt, c, options);
        if (lower === c && lower !== lt)
          return false
      } else if (lt.operator === '<=' && !satisfies_1(lt.semver, String(c), options))
        return false
    }
    if (!c.operator && (lt || gt) && gtltComp !== 0)
      return false
  }

  // if there was a < or >, and nothing in the dom, then must be false
  // UNLESS it was limited by another range in the other direction.
  // Eg, >1.0.0 <1.0.1 is still a subset of <2.0.0
  if (gt && hasDomLT && !lt && gtltComp !== 0)
    return false

  if (lt && hasDomGT && !gt && gtltComp !== 0)
    return false

  return true
};

// >=1.2.3 is lower than >1.2.3
const higherGT = (a, b, options) => {
  if (!a)
    return b
  const comp = compare_1(a.semver, b.semver, options);
  return comp > 0 ? a
    : comp < 0 ? b
    : b.operator === '>' && a.operator === '>=' ? b
    : a
};

// <=1.2.3 is higher than <1.2.3
const lowerLT = (a, b, options) => {
  if (!a)
    return b
  const comp = compare_1(a.semver, b.semver, options);
  return comp < 0 ? a
    : comp > 0 ? b
    : b.operator === '<' && a.operator === '<=' ? b
    : a
};

var subset_1 = subset;

// just pre-load all the stuff that index.js lazily exports

var semver$1 = {
  re: re_1.re,
  src: re_1.src,
  tokens: re_1.t,
  SEMVER_SPEC_VERSION: constants.SEMVER_SPEC_VERSION,
  SemVer: semver,
  compareIdentifiers: identifiers.compareIdentifiers,
  rcompareIdentifiers: identifiers.rcompareIdentifiers,
  parse: parse_1,
  valid: valid_1,
  clean: clean_1,
  inc: inc_1,
  diff: diff_1,
  major: major_1,
  minor: minor_1,
  patch: patch_1,
  prerelease: prerelease_1,
  compare: compare_1,
  rcompare: rcompare_1,
  compareLoose: compareLoose_1,
  compareBuild: compareBuild_1,
  sort: sort_1,
  rsort: rsort_1,
  gt: gt_1,
  lt: lt_1,
  eq: eq_1,
  neq: neq_1,
  gte: gte_1,
  lte: lte_1,
  cmp: cmp_1,
  coerce: coerce_1,
  Comparator: comparator,
  Range: range,
  satisfies: satisfies_1,
  toComparators: toComparators_1,
  maxSatisfying: maxSatisfying_1,
  minSatisfying: minSatisfying_1,
  minVersion: minVersion_1,
  validRange: valid$1,
  outside: outside_1,
  gtr: gtr_1,
  ltr: ltr_1,
  intersects: intersects_1,
  simplifyRange: simplify,
  subset: subset_1,
};

const log = new Logger(`plugin`);

var commonjsGlobal$1 = typeof globalThis !== 'undefined' ? globalThis : typeof window !== 'undefined' ? window : typeof global !== 'undefined' ? global : typeof self !== 'undefined' ? self : {};

function createCommonjsModule$1(fn) {
  var module = { exports: {} };
	return fn(module, module.exports), module.exports;
}

var util_1$1 = createCommonjsModule$1(function (module, exports) {
var __values = (commonjsGlobal$1 && commonjsGlobal$1.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.INVALID = Symbol('invalid_data');
var util;
(function (util) {
    function assertNever(_x) {
        throw new Error();
    }
    util.assertNever = assertNever;
    util.arrayToEnum = function (items) {
        var e_1, _a;
        var obj = {};
        try {
            for (var items_1 = __values(items), items_1_1 = items_1.next(); !items_1_1.done; items_1_1 = items_1.next()) {
                var item = items_1_1.value;
                obj[item] = item;
            }
        }
        catch (e_1_1) { e_1 = { error: e_1_1 }; }
        finally {
            try {
                if (items_1_1 && !items_1_1.done && (_a = items_1.return)) _a.call(items_1);
            }
            finally { if (e_1) throw e_1.error; }
        }
        return obj;
    };
    util.getValidEnumValues = function (obj) {
        var e_2, _a;
        var validKeys = Object.keys(obj).filter(function (k) { return typeof obj[obj[k]] !== 'number'; });
        var filtered = {};
        try {
            for (var validKeys_1 = __values(validKeys), validKeys_1_1 = validKeys_1.next(); !validKeys_1_1.done; validKeys_1_1 = validKeys_1.next()) {
                var k = validKeys_1_1.value;
                filtered[k] = obj[k];
            }
        }
        catch (e_2_1) { e_2 = { error: e_2_1 }; }
        finally {
            try {
                if (validKeys_1_1 && !validKeys_1_1.done && (_a = validKeys_1.return)) _a.call(validKeys_1);
            }
            finally { if (e_2) throw e_2.error; }
        }
        return util.getValues(filtered);
    };
    util.getValues = function (obj) {
        return Object.keys(obj).map(function (e) {
            return obj[e];
        });
    };
    util.objectValues = function (obj) {
        return Object.keys(obj).map(function (e) {
            return obj[e];
        });
    };
    util.find = function (arr, checker) {
        var e_3, _a;
        try {
            for (var arr_1 = __values(arr), arr_1_1 = arr_1.next(); !arr_1_1.done; arr_1_1 = arr_1.next()) {
                var item = arr_1_1.value;
                if (checker(item))
                    return item;
            }
        }
        catch (e_3_1) { e_3 = { error: e_3_1 }; }
        finally {
            try {
                if (arr_1_1 && !arr_1_1.done && (_a = arr_1.return)) _a.call(arr_1);
            }
            finally { if (e_3) throw e_3.error; }
        }
        return undefined;
    };
})(util = exports.util || (exports.util = {}));

});

var __extends$s = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __read$2 = (commonjsGlobal$1 && commonjsGlobal$1.__read) || function (o, n) {
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
};
var __spread$2 = (commonjsGlobal$1 && commonjsGlobal$1.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read$2(arguments[i]));
    return ar;
};
var __values$3 = (commonjsGlobal$1 && commonjsGlobal$1.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};


var ZodIssueCode$1 = util_1$1.util.arrayToEnum([
    'invalid_type',
    'nonempty_array_is_empty',
    'custom',
    'invalid_union',
    'invalid_literal_value',
    'invalid_enum_value',
    'unrecognized_keys',
    'invalid_arguments',
    'invalid_return_type',
    'invalid_date',
    'invalid_string',
    'too_small',
    'too_big',
    'invalid_intersection_types',
]);
var quotelessJson$1 = function (obj) {
    var json = JSON.stringify(obj, null, 2);
    return json.replace(/"([^"]+)":/g, '$1:');
};
var ZodError$1 = (function (_super) {
    __extends$s(ZodError, _super);
    function ZodError(issues) {
        var _newTarget = this.constructor;
        var _this = _super.call(this) || this;
        _this.issues = [];
        _this.addIssue = function (sub) {
            _this.issues = __spread$2(_this.issues, [sub]);
        };
        _this.addIssues = function (subs) {
            if (subs === void 0) { subs = []; }
            _this.issues = __spread$2(_this.issues, subs);
        };
        _this.flatten = function () {
            var e_1, _a;
            var fieldErrors = {};
            var formErrors = [];
            try {
                for (var _b = __values$3(_this.issues), _c = _b.next(); !_c.done; _c = _b.next()) {
                    var sub = _c.value;
                    if (sub.path.length > 0) {
                        fieldErrors[sub.path[0]] = fieldErrors[sub.path[0]] || [];
                        fieldErrors[sub.path[0]].push(sub.message);
                    }
                    else {
                        formErrors.push(sub.message);
                    }
                }
            }
            catch (e_1_1) { e_1 = { error: e_1_1 }; }
            finally {
                try {
                    if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
                }
                finally { if (e_1) throw e_1.error; }
            }
            return { formErrors: formErrors, fieldErrors: fieldErrors };
        };
        var actualProto = _newTarget.prototype;
        Object.setPrototypeOf(_this, actualProto);
        _this.issues = issues;
        return _this;
    }
    Object.defineProperty(ZodError.prototype, "errors", {
        get: function () {
            return this.issues;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodError.prototype, "message", {
        get: function () {
            return JSON.stringify(this.issues, null, 2);
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodError.prototype, "isEmpty", {
        get: function () {
            return this.issues.length === 0;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodError.prototype, "formErrors", {
        get: function () {
            return this.flatten();
        },
        enumerable: true,
        configurable: true
    });
    ZodError.create = function (issues) {
        var error = new ZodError(issues);
        return error;
    };
    return ZodError;
}(Error));
var ZodError_2$1 = ZodError$1;


var ZodError_1$1 = /*#__PURE__*/Object.defineProperty({
	ZodIssueCode: ZodIssueCode$1,
	quotelessJson: quotelessJson$1,
	ZodError: ZodError_2$1
}, '__esModule', {value: true});

var defaultErrorMap_1$1 = function (error, _ctx) {
    var message;
    switch (error.code) {
        case ZodError_1$1.ZodIssueCode.invalid_type:
            if (error.received === 'undefined') {
                message = 'Required';
            }
            else {
                message = "Expected " + error.expected + ", received " + error.received;
            }
            break;
        case ZodError_1$1.ZodIssueCode.nonempty_array_is_empty:
            message = "List must contain at least one item";
            break;
        case ZodError_1$1.ZodIssueCode.unrecognized_keys:
            message = "Unrecognized key(s) in object: " + error.keys
                .map(function (k) { return "'" + k + "'"; })
                .join(', ');
            break;
        case ZodError_1$1.ZodIssueCode.invalid_union:
            message = "Invalid input";
            break;
        case ZodError_1$1.ZodIssueCode.invalid_literal_value:
            message = "Input must be \"" + error.expected + "\"";
            break;
        case ZodError_1$1.ZodIssueCode.invalid_enum_value:
            message = "Input must be one of these values: " + error.options.join(', ');
            break;
        case ZodError_1$1.ZodIssueCode.invalid_arguments:
            message = "Invalid function arguments";
            break;
        case ZodError_1$1.ZodIssueCode.invalid_return_type:
            message = "Invalid function return type";
            break;
        case ZodError_1$1.ZodIssueCode.invalid_date:
            message = "Invalid date";
            break;
        case ZodError_1$1.ZodIssueCode.invalid_string:
            if (error.validation !== 'regex')
                message = "Invalid " + error.validation;
            else
                message = 'Invalid';
            break;
        case ZodError_1$1.ZodIssueCode.too_small:
            if (error.type === 'array')
                message = "Should have " + (error.inclusive ? "at least" : "more than") + " " + error.minimum + " items";
            else if (error.type === 'string')
                message = "Should be " + (error.inclusive ? "at least" : "over") + " " + error.minimum + " characters";
            else if (error.type === 'number')
                message = "Value should be greater than " + (error.inclusive ? "or equal to " : "") + error.minimum;
            else
                message = 'Invalid input';
            break;
        case ZodError_1$1.ZodIssueCode.too_big:
            if (error.type === 'array')
                message = "Should have " + (error.inclusive ? "at most" : "less than") + " " + error.maximum + " items";
            else if (error.type === 'string')
                message = "Should be " + (error.inclusive ? "at most" : "under") + " " + error.maximum + " characters long";
            else if (error.type === 'number')
                message = "Value should be less than " + (error.inclusive ? "or equal to " : "") + error.maximum;
            else
                message = 'Invalid input';
            break;
        case ZodError_1$1.ZodIssueCode.custom:
            message = "Invalid input.";
            break;
        case ZodError_1$1.ZodIssueCode.invalid_intersection_types:
            message = "Intersections only support objects";
            break;
        default:
            message = "Invalid input.";
            util_1$1.util.assertNever(error);
    }
    return { message: message };
};


var defaultErrorMap$1 = /*#__PURE__*/Object.defineProperty({
	defaultErrorMap: defaultErrorMap_1$1
}, '__esModule', {value: true});

var PseudoPromise_1$1 = createCommonjsModule$1(function (module, exports) {
var __awaiter = (commonjsGlobal$1 && commonjsGlobal$1.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (commonjsGlobal$1 && commonjsGlobal$1.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
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
};
var __read = (commonjsGlobal$1 && commonjsGlobal$1.__read) || function (o, n) {
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
};
var __spread = (commonjsGlobal$1 && commonjsGlobal$1.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read(arguments[i]));
    return ar;
};
var __values = (commonjsGlobal$1 && commonjsGlobal$1.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
Object.defineProperty(exports, "__esModule", { value: true });


exports.NOSET = Symbol('no_set');
var PseudoPromise = (function () {
    function PseudoPromise(funcs) {
        var _this = this;
        if (funcs === void 0) { funcs = []; }
        this.all = function (pps) {
            return _this.then(function (_arg, ctx) {
                if (ctx.async) {
                    var allValues = Promise.all(pps.map(function (pp) { return __awaiter(_this, void 0, void 0, function () {
                        var asdf, err_1;
                        return __generator(this, function (_a) {
                            switch (_a.label) {
                                case 0:
                                    _a.trys.push([0, 2, , 3]);
                                    return [4, pp.getValueAsync()];
                                case 1:
                                    asdf = _a.sent();
                                    return [2, asdf];
                                case 2:
                                    err_1 = _a.sent();
                                    return [2, util_1$1.INVALID];
                                case 3: return [2];
                            }
                        });
                    }); })).then(function (vals) {
                        return vals;
                    });
                    return allValues;
                }
                else {
                    return pps.map(function (pp) { return pp.getValueSync(); });
                }
            });
        };
        this.then = function (func) {
            return new PseudoPromise(__spread(_this.items, [
                { type: 'function', function: func },
            ]));
        };
        this.catch = function (catcher) {
            return new PseudoPromise(__spread(_this.items, [
                { type: 'catcher', catcher: catcher },
            ]));
        };
        this.getValueSync = function () {
            var val = undefined;
            var _loop_1 = function (index) {
                try {
                    var item = _this.items[index];
                    if (item.type === 'function') {
                        val = item.function(val, { async: false });
                    }
                }
                catch (err) {
                    var catcherIndex = _this.items.findIndex(function (x, i) { return x.type === 'catcher' && i > index; });
                    var catcherItem = _this.items[catcherIndex];
                    if (!catcherItem || catcherItem.type !== 'catcher') {
                        throw err;
                    }
                    else {
                        index = catcherIndex;
                        val = catcherItem.catcher(err, { async: false });
                    }
                }
                out_index_1 = index;
            };
            var out_index_1;
            for (var index = 0; index < _this.items.length; index++) {
                _loop_1(index);
                index = out_index_1;
            }
            return val;
        };
        this.getValueAsync = function () { return __awaiter(_this, void 0, void 0, function () {
            var val, _loop_2, this_1, out_index_2, index;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        val = undefined;
                        _loop_2 = function (index) {
                            var item, err_2, catcherIndex, catcherItem;
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        item = this_1.items[index];
                                        _a.label = 1;
                                    case 1:
                                        _a.trys.push([1, 4, , 8]);
                                        if (!(item.type === 'function')) return [3, 3];
                                        return [4, item.function(val, { async: true })];
                                    case 2:
                                        val = _a.sent();
                                        _a.label = 3;
                                    case 3: return [3, 8];
                                    case 4:
                                        err_2 = _a.sent();
                                        catcherIndex = this_1.items.findIndex(function (x, i) { return x.type === 'catcher' && i > index; });
                                        catcherItem = this_1.items[catcherIndex];
                                        if (!(!catcherItem || catcherItem.type !== 'catcher')) return [3, 5];
                                        throw err_2;
                                    case 5:
                                        index = catcherIndex;
                                        return [4, catcherItem.catcher(err_2, { async: true })];
                                    case 6:
                                        val = _a.sent();
                                        _a.label = 7;
                                    case 7: return [3, 8];
                                    case 8:
                                        if (val instanceof PseudoPromise) {
                                            throw new Error('ASYNC: DO NOT RETURN PSEUDOPROMISE FROM FUNCTIONS');
                                        }
                                        if (val instanceof Promise) {
                                            throw new Error('ASYNC: DO NOT RETURN PROMISE FROM FUNCTIONS');
                                        }
                                        out_index_2 = index;
                                        return [2];
                                }
                            });
                        };
                        this_1 = this;
                        index = 0;
                        _a.label = 1;
                    case 1:
                        if (!(index < this.items.length)) return [3, 4];
                        return [5, _loop_2(index)];
                    case 2:
                        _a.sent();
                        index = out_index_2;
                        _a.label = 3;
                    case 3:
                        index++;
                        return [3, 1];
                    case 4: return [2, val];
                }
            });
        }); };
        this.items = funcs;
    }
    PseudoPromise.all = function (pps) {
        return new PseudoPromise().all(pps);
    };
    PseudoPromise.object = function (pps) {
        return new PseudoPromise().then(function (_arg, ctx) {
            var e_1, _a;
            var value = {};
            var zerr = new ZodError_1$1.ZodError([]);
            if (ctx.async) {
                var getAsyncObject = function () { return __awaiter(void 0, void 0, void 0, function () {
                    var items, items_2, items_2_1, item;
                    var e_2, _a;
                    return __generator(this, function (_b) {
                        switch (_b.label) {
                            case 0: return [4, Promise.all(Object.keys(pps).map(function (k) { return __awaiter(void 0, void 0, void 0, function () {
                                    var v, err_3;
                                    return __generator(this, function (_a) {
                                        switch (_a.label) {
                                            case 0:
                                                _a.trys.push([0, 2, , 3]);
                                                return [4, pps[k].getValueAsync()];
                                            case 1:
                                                v = _a.sent();
                                                return [2, [k, v]];
                                            case 2:
                                                err_3 = _a.sent();
                                                if (err_3 instanceof ZodError_1$1.ZodError) {
                                                    zerr.addIssues(err_3.issues);
                                                    return [2, [k, util_1$1.INVALID]];
                                                }
                                                throw err_3;
                                            case 3: return [2];
                                        }
                                    });
                                }); }))];
                            case 1:
                                items = _b.sent();
                                if (!zerr.isEmpty)
                                    throw zerr;
                                try {
                                    for (items_2 = __values(items), items_2_1 = items_2.next(); !items_2_1.done; items_2_1 = items_2.next()) {
                                        item = items_2_1.value;
                                        if (item[1] !== exports.NOSET)
                                            value[item[0]] = item[1];
                                    }
                                }
                                catch (e_2_1) { e_2 = { error: e_2_1 }; }
                                finally {
                                    try {
                                        if (items_2_1 && !items_2_1.done && (_a = items_2.return)) _a.call(items_2);
                                    }
                                    finally { if (e_2) throw e_2.error; }
                                }
                                return [2, value];
                        }
                    });
                }); };
                return getAsyncObject();
            }
            else {
                var items = Object.keys(pps).map(function (k) {
                    try {
                        var v = pps[k].getValueSync();
                        return [k, v];
                    }
                    catch (err) {
                        if (err instanceof ZodError_1$1.ZodError) {
                            zerr.addIssues(err.issues);
                            return [k, util_1$1.INVALID];
                        }
                        throw err;
                    }
                });
                if (!zerr.isEmpty)
                    throw zerr;
                try {
                    for (var items_1 = __values(items), items_1_1 = items_1.next(); !items_1_1.done; items_1_1 = items_1.next()) {
                        var item = items_1_1.value;
                        if (item[1] !== exports.NOSET)
                            value[item[0]] = item[1];
                    }
                }
                catch (e_1_1) { e_1 = { error: e_1_1 }; }
                finally {
                    try {
                        if (items_1_1 && !items_1_1.done && (_a = items_1.return)) _a.call(items_1);
                    }
                    finally { if (e_1) throw e_1.error; }
                }
                return value;
            }
        });
    };
    PseudoPromise.resolve = function (value) {
        if (value instanceof PseudoPromise) {
            throw new Error('Do not pass PseudoPromise into PseudoPromise.resolve');
        }
        return new PseudoPromise().then(function () { return value; });
    };
    return PseudoPromise;
}());
exports.PseudoPromise = PseudoPromise;

});

var parser$1 = createCommonjsModule$1(function (module, exports) {
var __assign = (commonjsGlobal$1 && commonjsGlobal$1.__assign) || function () {
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
var __awaiter = (commonjsGlobal$1 && commonjsGlobal$1.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (commonjsGlobal$1 && commonjsGlobal$1.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
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
};
var __read = (commonjsGlobal$1 && commonjsGlobal$1.__read) || function (o, n) {
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
};
var __spread = (commonjsGlobal$1 && commonjsGlobal$1.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read(arguments[i]));
    return ar;
};
var __values = (commonjsGlobal$1 && commonjsGlobal$1.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
var __importStar = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
var z = __importStar(base$1);





exports.getParsedType = function (data) {
    if (typeof data === 'string')
        return 'string';
    if (typeof data === 'number') {
        if (Number.isNaN(data))
            return 'nan';
        return 'number';
    }
    if (typeof data === 'boolean')
        return 'boolean';
    if (typeof data === 'bigint')
        return 'bigint';
    if (typeof data === 'symbol')
        return 'symbol';
    if (data instanceof Date)
        return 'date';
    if (typeof data === 'function')
        return 'function';
    if (data === undefined)
        return 'undefined';
    if (typeof data === 'undefined')
        return 'undefined';
    if (typeof data === 'object') {
        if (Array.isArray(data))
            return 'array';
        if (data === null)
            return 'null';
        if (data.then &&
            typeof data.then === 'function' &&
            data.catch &&
            typeof data.catch === 'function') {
            return 'promise';
        }
        if (data instanceof Map) {
            return 'map';
        }
        return 'object';
    }
    return 'unknown';
};
exports.ZodParsedType = util_1$1.util.arrayToEnum([
    'string',
    'nan',
    'number',
    'integer',
    'boolean',
    'date',
    'bigint',
    'symbol',
    'function',
    'undefined',
    'null',
    'array',
    'object',
    'unknown',
    'promise',
    'void',
    'never',
    'map',
]);
var makeError = function (params, data, errorData) {
    var errorArg = __assign(__assign({}, errorData), { path: __spread(params.path, (errorData.path || [])) });
    var ctxArg = { data: data };
    var defaultError = defaultErrorMap$1.defaultErrorMap === params.errorMap
        ? { message: "Invalid value." }
        : defaultErrorMap$1.defaultErrorMap(errorArg, __assign(__assign({}, ctxArg), { defaultError: "Invalid value." }));
    return __assign(__assign({}, errorData), { path: __spread(params.path, (errorData.path || [])), message: errorData.message ||
            params.errorMap(errorArg, __assign(__assign({}, ctxArg), { defaultError: defaultError.message })).message });
};
exports.ZodParser = function (schema) { return function (data, baseParams) {
    var e_1, _a, e_2, _b, e_3, _c, e_4, _d;
    if (baseParams === void 0) { baseParams = { seen: [], errorMap: defaultErrorMap$1.defaultErrorMap, path: [] }; }
    var _e, _f;
    var params = {
        seen: baseParams.seen || [],
        path: baseParams.path || [],
        errorMap: baseParams.errorMap || defaultErrorMap$1.defaultErrorMap,
        async: (_e = baseParams.async) !== null && _e !== void 0 ? _e : false,
        runAsyncValidationsInSeries: (_f = baseParams.runAsyncValidationsInSeries) !== null && _f !== void 0 ? _f : false,
    };
    var def = schema._def;
    var PROMISE = new PseudoPromise_1$1.PseudoPromise();
    PROMISE._default = true;
    var RESULT = {
        input: data,
        output: util_1$1.INVALID,
    };
    params.seen = params.seen || [];
    var ERROR = new ZodError_1$1.ZodError([]);
    var THROW = function () {
        RESULT.error = ERROR;
        throw ERROR;
    };
    var HANDLE = function (err) {
        if (err instanceof ZodError_1$1.ZodError) {
            ERROR.addIssues(err.issues);
            return util_1$1.INVALID;
        }
        throw ERROR;
    };
    var parsedType = exports.getParsedType(data);
    switch (def.t) {
        case z.ZodTypes.string:
            if (parsedType !== exports.ZodParsedType.string) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.string,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.number:
            if (parsedType !== exports.ZodParsedType.number) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.number,
                    received: parsedType,
                }));
                THROW();
            }
            if (Number.isNaN(data)) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.number,
                    received: exports.ZodParsedType.nan,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.bigint:
            if (parsedType !== exports.ZodParsedType.bigint) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.bigint,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.boolean:
            if (parsedType !== exports.ZodParsedType.boolean) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.boolean,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.undefined:
            if (parsedType !== exports.ZodParsedType.undefined) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.undefined,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.null:
            if (parsedType !== exports.ZodParsedType.null) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.null,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.any:
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.unknown:
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.never:
            ERROR.addIssue(makeError(params, data, {
                code: ZodError_1$1.ZodIssueCode.invalid_type,
                expected: exports.ZodParsedType.never,
                received: parsedType,
            }));
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(util_1$1.INVALID);
            break;
        case z.ZodTypes.void:
            if (parsedType !== exports.ZodParsedType.undefined &&
                parsedType !== exports.ZodParsedType.null) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.void,
                    received: parsedType,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.array:
            RESULT.output = [];
            if (parsedType !== exports.ZodParsedType.array) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.array,
                    received: parsedType,
                }));
                THROW();
            }
            if (def.nonempty === true && data.length === 0) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.nonempty_array_is_empty,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.all(data.map(function (item, i) {
                return new PseudoPromise_1$1.PseudoPromise()
                    .then(function () {
                    return def.type.parse(item, __assign(__assign({}, params), { path: __spread(params.path, [i]) }));
                })
                    .catch(function (err) {
                    if (!(err instanceof ZodError_1$1.ZodError)) {
                        throw err;
                    }
                    ERROR.addIssues(err.issues);
                    return util_1$1.INVALID;
                });
            }));
            break;
        case z.ZodTypes.map:
            if (parsedType !== exports.ZodParsedType.map) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.map,
                    received: parsedType,
                }));
                THROW();
            }
            var dataMap = data;
            var returnedMap_1 = new Map();
            PROMISE = PseudoPromise_1$1.PseudoPromise.all(__spread(dataMap.entries()).map(function (_a, index) {
                var _b = __read(_a, 2), key = _b[0], value = _b[1];
                return PseudoPromise_1$1.PseudoPromise.all([
                    new PseudoPromise_1$1.PseudoPromise()
                        .then(function () {
                        return def.keyType.parse(key, __assign(__assign({}, params), { path: __spread(params.path, [index, 'key']) }));
                    })
                        .catch(HANDLE),
                    new PseudoPromise_1$1.PseudoPromise()
                        .then(function () {
                        var mapValue = def.valueType.parse(value, __assign(__assign({}, params), { path: __spread(params.path, [index, 'value']) }));
                        return [key, mapValue];
                    })
                        .catch(HANDLE),
                ])
                    .then(function (item) {
                    if (item[0] !== util_1$1.INVALID && item[1] !== util_1$1.INVALID) {
                        returnedMap_1.set(item[0], item[1]);
                    }
                })
                    .catch(HANDLE);
            }))
                .then(function () {
                if (!ERROR.isEmpty) {
                    throw ERROR;
                }
            })
                .then(function () {
                return returnedMap_1;
            })
                .then(function () {
                return returnedMap_1;
            });
            break;
        case z.ZodTypes.object:
            RESULT.output = {};
            if (parsedType !== exports.ZodParsedType.object) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.object,
                    received: parsedType,
                }));
                THROW();
            }
            var objectPromises_1 = {};
            var shape = def.shape();
            var shapeKeys_2 = Object.keys(shape);
            var dataKeys = Object.keys(data);
            var extraKeys = dataKeys.filter(function (k) { return shapeKeys_2.indexOf(k) === -1; });
            var _loop_1 = function (key) {
                var keyValidator = shapeKeys_2.includes(key)
                    ? shape[key]
                    : !(def.catchall instanceof cjs$1.ZodNever)
                        ? def.catchall
                        : undefined;
                if (!keyValidator) {
                    return "continue";
                }
                if (typeof data[key] === 'undefined' && !dataKeys.includes(key)) {
                    objectPromises_1[key] = new PseudoPromise_1$1.PseudoPromise()
                        .then(function () {
                        return keyValidator.parse(undefined, __assign(__assign({}, params), { path: __spread(params.path, [key]) }));
                    })
                        .then(function (output) {
                        if (output === undefined) {
                            return PseudoPromise_1$1.NOSET;
                        }
                        else {
                            return output;
                        }
                    })
                        .catch(function (err) {
                        if (err instanceof ZodError_1$1.ZodError) {
                            var zerr = err;
                            ERROR.addIssues(zerr.issues);
                            objectPromises_1[key] = PseudoPromise_1$1.PseudoPromise.resolve(util_1$1.INVALID);
                        }
                        else {
                            throw err;
                        }
                    });
                    return "continue";
                }
                objectPromises_1[key] = new PseudoPromise_1$1.PseudoPromise()
                    .then(function () {
                    return keyValidator.parse(data[key], __assign(__assign({}, params), { path: __spread(params.path, [key]) }));
                })
                    .catch(function (err) {
                    if (err instanceof ZodError_1$1.ZodError) {
                        var zerr = err;
                        ERROR.addIssues(zerr.issues);
                        return util_1$1.INVALID;
                    }
                    else {
                        throw err;
                    }
                });
            };
            try {
                for (var shapeKeys_1 = __values(shapeKeys_2), shapeKeys_1_1 = shapeKeys_1.next(); !shapeKeys_1_1.done; shapeKeys_1_1 = shapeKeys_1.next()) {
                    var key = shapeKeys_1_1.value;
                    _loop_1(key);
                }
            }
            catch (e_1_1) { e_1 = { error: e_1_1 }; }
            finally {
                try {
                    if (shapeKeys_1_1 && !shapeKeys_1_1.done && (_a = shapeKeys_1.return)) _a.call(shapeKeys_1);
                }
                finally { if (e_1) throw e_1.error; }
            }
            if (def.catchall instanceof cjs$1.ZodNever) {
                if (def.unknownKeys === 'passthrough') {
                    try {
                        for (var extraKeys_1 = __values(extraKeys), extraKeys_1_1 = extraKeys_1.next(); !extraKeys_1_1.done; extraKeys_1_1 = extraKeys_1.next()) {
                            var key = extraKeys_1_1.value;
                            objectPromises_1[key] = PseudoPromise_1$1.PseudoPromise.resolve(data[key]);
                        }
                    }
                    catch (e_2_1) { e_2 = { error: e_2_1 }; }
                    finally {
                        try {
                            if (extraKeys_1_1 && !extraKeys_1_1.done && (_b = extraKeys_1.return)) _b.call(extraKeys_1);
                        }
                        finally { if (e_2) throw e_2.error; }
                    }
                }
                else if (def.unknownKeys === 'strict') {
                    if (extraKeys.length > 0) {
                        ERROR.addIssue(makeError(params, data, {
                            code: ZodError_1$1.ZodIssueCode.unrecognized_keys,
                            keys: extraKeys,
                        }));
                    }
                }
                else if (def.unknownKeys === 'strip') ;
                else {
                    util_1$1.util.assertNever(def.unknownKeys);
                }
            }
            else {
                var _loop_2 = function (key) {
                    objectPromises_1[key] = new PseudoPromise_1$1.PseudoPromise()
                        .then(function () {
                        var parsedValue = def.catchall.parse(data[key], __assign(__assign({}, params), { path: __spread(params.path, [key]) }));
                        return parsedValue;
                    })
                        .catch(function (err) {
                        if (err instanceof ZodError_1$1.ZodError) {
                            ERROR.addIssues(err.issues);
                        }
                        else {
                            throw err;
                        }
                    });
                };
                try {
                    for (var extraKeys_2 = __values(extraKeys), extraKeys_2_1 = extraKeys_2.next(); !extraKeys_2_1.done; extraKeys_2_1 = extraKeys_2.next()) {
                        var key = extraKeys_2_1.value;
                        _loop_2(key);
                    }
                }
                catch (e_3_1) { e_3 = { error: e_3_1 }; }
                finally {
                    try {
                        if (extraKeys_2_1 && !extraKeys_2_1.done && (_c = extraKeys_2.return)) _c.call(extraKeys_2);
                    }
                    finally { if (e_3) throw e_3.error; }
                }
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.object(objectPromises_1)
                .then(function (resolvedObject) {
                Object.assign(RESULT.output, resolvedObject);
                return RESULT.output;
            })
                .then(function (finalObject) {
                if (ERROR.issues.length > 0) {
                    return util_1$1.INVALID;
                }
                return finalObject;
            })
                .catch(function (err) {
                if (err instanceof ZodError_1$1.ZodError) {
                    ERROR.addIssues(err.issues);
                    return util_1$1.INVALID;
                }
                throw err;
            });
            break;
        case z.ZodTypes.union:
            var isValid_1 = false;
            var unionErrors_1 = [];
            PROMISE = PseudoPromise_1$1.PseudoPromise.all(def.options.map(function (opt, _j) {
                return new PseudoPromise_1$1.PseudoPromise()
                    .then(function () {
                    return opt.parse(data, params);
                })
                    .then(function (optionData) {
                    isValid_1 = true;
                    return optionData;
                })
                    .catch(function (err) {
                    if (err instanceof ZodError_1$1.ZodError) {
                        unionErrors_1.push(err);
                        return util_1$1.INVALID;
                    }
                    throw err;
                });
            }))
                .then(function (unionResults) {
                if (!isValid_1) {
                    var nonTypeErrors = unionErrors_1.filter(function (err) {
                        return err.issues[0].code !== 'invalid_type';
                    });
                    if (nonTypeErrors.length === 1) {
                        ERROR.addIssues(nonTypeErrors[0].issues);
                    }
                    else {
                        ERROR.addIssue(makeError(params, data, {
                            code: ZodError_1$1.ZodIssueCode.invalid_union,
                            unionErrors: unionErrors_1,
                        }));
                    }
                    THROW();
                }
                return unionResults;
            })
                .then(function (unionResults) {
                return util_1$1.util.find(unionResults, function (val) { return val !== util_1$1.INVALID; });
            });
            break;
        case z.ZodTypes.intersection:
            PROMISE = PseudoPromise_1$1.PseudoPromise.all([
                new PseudoPromise_1$1.PseudoPromise()
                    .then(function () {
                    return def.left.parse(data, params);
                })
                    .catch(HANDLE),
                new PseudoPromise_1$1.PseudoPromise()
                    .then(function () {
                    return def.right.parse(data, params);
                })
                    .catch(HANDLE),
            ]).then(function (_a) {
                var _b = __read(_a, 2), parsedLeft = _b[0], parsedRight = _b[1];
                if (parsedLeft === util_1$1.INVALID || parsedRight === util_1$1.INVALID)
                    return util_1$1.INVALID;
                var parsedLeftType = exports.getParsedType(parsedLeft);
                var parsedRightType = exports.getParsedType(parsedRight);
                if (parsedLeft === parsedRight) {
                    return parsedLeft;
                }
                else if (parsedLeftType === exports.ZodParsedType.object &&
                    parsedRightType === exports.ZodParsedType.object) {
                    return __assign(__assign({}, parsedLeft), parsedRight);
                }
                else {
                    ERROR.addIssue(makeError(params, data, {
                        code: ZodError_1$1.ZodIssueCode.invalid_intersection_types,
                    }));
                }
            });
            break;
        case z.ZodTypes.optional:
            if (parsedType === exports.ZodParsedType.undefined) {
                PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(undefined);
                break;
            }
            PROMISE = new PseudoPromise_1$1.PseudoPromise()
                .then(function () {
                return def.innerType.parse(data, params);
            })
                .catch(HANDLE);
            break;
        case z.ZodTypes.nullable:
            if (parsedType === exports.ZodParsedType.null) {
                PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(null);
                break;
            }
            PROMISE = new PseudoPromise_1$1.PseudoPromise()
                .then(function () {
                return def.innerType.parse(data, params);
            })
                .catch(HANDLE);
            break;
        case z.ZodTypes.tuple:
            if (parsedType !== exports.ZodParsedType.array) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.array,
                    received: parsedType,
                }));
                THROW();
            }
            if (data.length > def.items.length) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.too_big,
                    maximum: def.items.length,
                    inclusive: true,
                    type: 'array',
                }));
            }
            else if (data.length < def.items.length) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.too_small,
                    minimum: def.items.length,
                    inclusive: true,
                    type: 'array',
                }));
            }
            var tupleData = data;
            PROMISE = PseudoPromise_1$1.PseudoPromise.all(tupleData.map(function (item, index) {
                var itemParser = def.items[index];
                return new PseudoPromise_1$1.PseudoPromise()
                    .then(function () {
                    var tupleDatum = itemParser.parse(item, __assign(__assign({}, params), { path: __spread(params.path, [index]) }));
                    return tupleDatum;
                })
                    .catch(function (err) {
                    if (err instanceof ZodError_1$1.ZodError) {
                        ERROR.addIssues(err.issues);
                        return;
                    }
                    throw err;
                })
                    .then(function (arg) {
                    return arg;
                });
            }))
                .then(function (tupleData) {
                if (!ERROR.isEmpty)
                    THROW();
                return tupleData;
            })
                .catch(function (err) {
                throw err;
            });
            break;
        case z.ZodTypes.lazy:
            var lazySchema = def.getter();
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(lazySchema.parse(data, params));
            break;
        case z.ZodTypes.literal:
            if (data !== def.value) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_literal_value,
                    expected: def.value,
                }));
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.enum:
            if (def.values.indexOf(data) === -1) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_enum_value,
                    options: def.values,
                }));
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.nativeEnum:
            if (util_1$1.util.getValidEnumValues(def.values).indexOf(data) === -1) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_enum_value,
                    options: util_1$1.util.objectValues(def.values),
                }));
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.function:
            if (parsedType !== exports.ZodParsedType.function) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.function,
                    received: parsedType,
                }));
                THROW();
            }
            var isAsyncFunction_1 = def.returns instanceof cjs$1.ZodPromise;
            var validatedFunction = function () {
                var args = [];
                for (var _i = 0; _i < arguments.length; _i++) {
                    args[_i] = arguments[_i];
                }
                var internalProm = new PseudoPromise_1$1.PseudoPromise()
                    .then(function () {
                    return def.args.parse(args, __assign(__assign({}, params), { async: isAsyncFunction_1 }));
                })
                    .catch(function (err) {
                    if (!(err instanceof ZodError_1$1.ZodError))
                        throw err;
                    var argsError = new ZodError_1$1.ZodError([]);
                    argsError.addIssue(makeError(params, data, {
                        code: ZodError_1$1.ZodIssueCode.invalid_arguments,
                        argumentsError: err,
                    }));
                    throw argsError;
                })
                    .then(function (args) {
                    return data.apply(void 0, __spread(args));
                })
                    .then(function (result) {
                    return def.returns.parse(result, __assign(__assign({}, params), { async: isAsyncFunction_1 }));
                })
                    .catch(function (err) {
                    if (err instanceof ZodError_1$1.ZodError) {
                        var returnsError = new ZodError_1$1.ZodError([]);
                        returnsError.addIssue(makeError(params, data, {
                            code: ZodError_1$1.ZodIssueCode.invalid_return_type,
                            returnTypeError: err,
                        }));
                        throw returnsError;
                    }
                    throw err;
                });
                if (isAsyncFunction_1) {
                    return internalProm.getValueAsync();
                }
                else {
                    return internalProm.getValueSync();
                }
            };
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(validatedFunction);
            break;
        case z.ZodTypes.record:
            if (parsedType !== exports.ZodParsedType.object) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.object,
                    received: parsedType,
                }));
                THROW();
            }
            var parsedRecordPromises = {};
            var _loop_3 = function (key) {
                parsedRecordPromises[key] = new PseudoPromise_1$1.PseudoPromise()
                    .then(function () {
                    return def.valueType.parse(data[key], __assign(__assign({}, params), { path: __spread(params.path, [key]) }));
                })
                    .catch(HANDLE);
            };
            for (var key in data) {
                _loop_3(key);
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.object(parsedRecordPromises);
            break;
        case z.ZodTypes.date:
            if (!(data instanceof Date)) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.date,
                    received: parsedType,
                }));
                THROW();
            }
            if (isNaN(data.getTime())) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_date,
                }));
                THROW();
            }
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(data);
            break;
        case z.ZodTypes.promise:
            if (parsedType !== exports.ZodParsedType.promise && params.async !== true) {
                ERROR.addIssue(makeError(params, data, {
                    code: ZodError_1$1.ZodIssueCode.invalid_type,
                    expected: exports.ZodParsedType.promise,
                    received: parsedType,
                }));
                THROW();
            }
            var promisified = parsedType === exports.ZodParsedType.promise ? data : Promise.resolve(data);
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve(promisified.then(function (resolvedData) {
                return def.type.parse(resolvedData, params);
            }));
            break;
        case z.ZodTypes.transformer:
            PROMISE = new PseudoPromise_1$1.PseudoPromise()
                .then(function () {
                return def.input.parse(data, params);
            })
                .then(function (inputParseResult) {
                var transformed = def.transformer(inputParseResult);
                if (transformed instanceof Promise && params.async === false) {
                    if (z.inputSchema(def.output)._def.t !== z.ZodTypes.promise) {
                        throw new Error("You can't call .parse on a schema containing async transformations.");
                    }
                }
                return transformed;
            })
                .then(function (transformedResult) {
                return def.output.parse(transformedResult, params);
            });
            break;
        default:
            PROMISE = PseudoPromise_1$1.PseudoPromise.resolve('adsf');
            util_1$1.util.assertNever(def);
    }
    if (PROMISE._default === true) {
        throw new Error('Result is not materialized.');
    }
    if (!ERROR.isEmpty) {
        THROW();
    }
    var customChecks = def.checks || [];
    var checkCtx = {
        addIssue: function (arg) {
            ERROR.addIssue(makeError(params, data, arg));
        },
        path: params.path,
    };
    if (params.async === false) {
        var resolvedValue = PROMISE.getValueSync();
        if (resolvedValue === util_1$1.INVALID && ERROR.isEmpty) {
            ERROR.addIssue(makeError(params, data, {
                code: ZodError_1$1.ZodIssueCode.custom,
                message: 'Invalid',
            }));
        }
        if (!ERROR.isEmpty) {
            THROW();
        }
        try {
            for (var customChecks_1 = __values(customChecks), customChecks_1_1 = customChecks_1.next(); !customChecks_1_1.done; customChecks_1_1 = customChecks_1.next()) {
                var check = customChecks_1_1.value;
                var checkResult = check.check(resolvedValue, checkCtx);
                if (checkResult instanceof Promise)
                    throw new Error("You can't use .parse on a schema containing async refinements. Use .parseAsync instead.");
            }
        }
        catch (e_4_1) { e_4 = { error: e_4_1 }; }
        finally {
            try {
                if (customChecks_1_1 && !customChecks_1_1.done && (_d = customChecks_1.return)) _d.call(customChecks_1);
            }
            finally { if (e_4) throw e_4.error; }
        }
        if (!ERROR.isEmpty) {
            THROW();
        }
        return resolvedValue;
    }
    else {
        var checker = function () { return __awaiter(void 0, void 0, void 0, function () {
            var resolvedValue, someError_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4, PROMISE.getValueAsync()];
                    case 1:
                        resolvedValue = _a.sent();
                        if (resolvedValue === util_1$1.INVALID && ERROR.isEmpty) {
                            ERROR.addIssue(makeError(params, data, {
                                code: ZodError_1$1.ZodIssueCode.custom,
                                message: 'Invalid',
                            }));
                        }
                        if (!ERROR.isEmpty) {
                            THROW();
                        }
                        if (!params.runAsyncValidationsInSeries) return [3, 3];
                        someError_1 = false;
                        return [4, customChecks.reduce(function (previousPromise, check) {
                                return previousPromise.then(function () { return __awaiter(void 0, void 0, void 0, function () {
                                    var len;
                                    return __generator(this, function (_a) {
                                        switch (_a.label) {
                                            case 0:
                                                if (!!someError_1) return [3, 2];
                                                len = ERROR.issues.length;
                                                return [4, check.check(resolvedValue, checkCtx)];
                                            case 1:
                                                _a.sent();
                                                if (len < ERROR.issues.length)
                                                    someError_1 = true;
                                                _a.label = 2;
                                            case 2: return [2];
                                        }
                                    });
                                }); });
                            }, Promise.resolve())];
                    case 2:
                        _a.sent();
                        return [3, 5];
                    case 3: return [4, Promise.all(customChecks.map(function (check) { return __awaiter(void 0, void 0, void 0, function () {
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0: return [4, check.check(resolvedValue, checkCtx)];
                                    case 1:
                                        _a.sent();
                                        return [2];
                                }
                            });
                        }); }))];
                    case 4:
                        _a.sent();
                        _a.label = 5;
                    case 5:
                        if (!ERROR.isEmpty) {
                            THROW();
                        }
                        return [2, resolvedValue];
                }
            });
        }); };
        return checker();
    }
}; };

});

var base$1 = createCommonjsModule$1(function (module, exports) {
var __assign = (commonjsGlobal$1 && commonjsGlobal$1.__assign) || function () {
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
var __awaiter = (commonjsGlobal$1 && commonjsGlobal$1.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (commonjsGlobal$1 && commonjsGlobal$1.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
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
};
var __read = (commonjsGlobal$1 && commonjsGlobal$1.__read) || function (o, n) {
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
};
var __spread = (commonjsGlobal$1 && commonjsGlobal$1.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read(arguments[i]));
    return ar;
};
Object.defineProperty(exports, "__esModule", { value: true });


var ZodTypes;
(function (ZodTypes) {
    ZodTypes["string"] = "string";
    ZodTypes["number"] = "number";
    ZodTypes["bigint"] = "bigint";
    ZodTypes["boolean"] = "boolean";
    ZodTypes["date"] = "date";
    ZodTypes["undefined"] = "undefined";
    ZodTypes["null"] = "null";
    ZodTypes["array"] = "array";
    ZodTypes["object"] = "object";
    ZodTypes["union"] = "union";
    ZodTypes["intersection"] = "intersection";
    ZodTypes["tuple"] = "tuple";
    ZodTypes["record"] = "record";
    ZodTypes["map"] = "map";
    ZodTypes["function"] = "function";
    ZodTypes["lazy"] = "lazy";
    ZodTypes["literal"] = "literal";
    ZodTypes["enum"] = "enum";
    ZodTypes["nativeEnum"] = "nativeEnum";
    ZodTypes["promise"] = "promise";
    ZodTypes["any"] = "any";
    ZodTypes["unknown"] = "unknown";
    ZodTypes["never"] = "never";
    ZodTypes["void"] = "void";
    ZodTypes["transformer"] = "transformer";
    ZodTypes["optional"] = "optional";
    ZodTypes["nullable"] = "nullable";
})(ZodTypes = exports.ZodTypes || (exports.ZodTypes = {}));
exports.inputSchema = function (schema) {
    if (schema instanceof cjs$1.ZodTransformer) {
        return exports.inputSchema(schema._def.input);
    }
    else {
        return schema;
    }
};
exports.outputSchema = function (schema) {
    if (schema instanceof cjs$1.ZodTransformer) {
        return exports.inputSchema(schema._def.output);
    }
    else {
        return schema;
    }
};
var ZodType = (function () {
    function ZodType(def) {
        var _this = this;
        this.parse = parser$1.ZodParser(this);
        this.safeParse = function (data, params) {
            try {
                var parsed = _this.parse(data, params);
                return { success: true, data: parsed };
            }
            catch (err) {
                if (err instanceof cjs$1.ZodError) {
                    return { success: false, error: err };
                }
                throw err;
            }
        };
        this.parseAsync = function (value, params) { return __awaiter(_this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4, this.parse(value, __assign(__assign({}, params), { async: true }))];
                    case 1: return [2, _a.sent()];
                }
            });
        }); };
        this.safeParseAsync = function (data, params) { return __awaiter(_this, void 0, void 0, function () {
            var parsed, err_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        _a.trys.push([0, 2, , 3]);
                        return [4, this.parseAsync(data, params)];
                    case 1:
                        parsed = _a.sent();
                        return [2, { success: true, data: parsed }];
                    case 2:
                        err_1 = _a.sent();
                        if (err_1 instanceof cjs$1.ZodError) {
                            return [2, { success: false, error: err_1 }];
                        }
                        throw err_1;
                    case 3: return [2];
                }
            });
        }); };
        this.spa = this.safeParseAsync;
        this.refine = function (check, message) {
            if (message === void 0) { message = 'Invalid value.'; }
            if (typeof message === 'string') {
                return _this._refinement(function (val, ctx) {
                    var result = check(val);
                    var setError = function () {
                        return ctx.addIssue({
                            code: cjs$1.ZodIssueCode.custom,
                            message: message,
                        });
                    };
                    if (result instanceof Promise) {
                        return result.then(function (data) {
                            if (!data)
                                setError();
                        });
                    }
                    if (!result) {
                        setError();
                        return result;
                    }
                });
            }
            if (typeof message === 'function') {
                return _this._refinement(function (val, ctx) {
                    var result = check(val);
                    var setError = function () {
                        return ctx.addIssue(__assign({ code: cjs$1.ZodIssueCode.custom }, message(val)));
                    };
                    if (result instanceof Promise) {
                        return result.then(function (data) {
                            if (!data)
                                setError();
                        });
                    }
                    if (!result) {
                        setError();
                        return result;
                    }
                });
            }
            return _this._refinement(function (val, ctx) {
                var result = check(val);
                var setError = function () {
                    return ctx.addIssue(__assign({ code: cjs$1.ZodIssueCode.custom }, message));
                };
                if (result instanceof Promise) {
                    return result.then(function (data) {
                        if (!data)
                            setError();
                    });
                }
                if (!result) {
                    setError();
                    return result;
                }
            });
        };
        this.refinement = function (check, refinementData) {
            return _this._refinement(function (val, ctx) {
                if (!check(val)) {
                    ctx.addIssue(typeof refinementData === 'function'
                        ? refinementData(val, ctx)
                        : refinementData);
                }
            });
        };
        this._refinement = function (refinement) {
            return new _this.constructor(__assign(__assign({}, _this._def), { checks: __spread((_this._def.checks || []), [{ check: refinement }]) }));
        };
        this.optional = function () { return cjs$1.ZodOptional.create(_this); };
        this.or = this.optional;
        this.nullable = function () {
            return cjs$1.ZodNullable.create(_this);
        };
        this.array = function () { return cjs$1.ZodArray.create(_this); };
        this.isOptional = function () { return _this.safeParse(undefined).success; };
        this.isNullable = function () { return _this.safeParse(null).success; };
        this._def = def;
        this.is = this.is.bind(this);
        this.check = this.check.bind(this);
        this.transform = this.transform.bind(this);
        this.default = this.default.bind(this);
    }
    ZodType.prototype.is = function (u) {
        try {
            this.parse(u);
            return true;
        }
        catch (err) {
            return false;
        }
    };
    ZodType.prototype.check = function (u) {
        try {
            this.parse(u);
            return true;
        }
        catch (err) {
            return false;
        }
    };
    ZodType.prototype.transform = function (input, transformer) {
        if (transformer) {
            return cjs$1.ZodTransformer.create(this, input, transformer);
        }
        return cjs$1.ZodTransformer.create(this, exports.outputSchema(this), input);
    };
    ZodType.prototype.default = function (def) {
        var _this = this;
        return cjs$1.ZodTransformer.create(this.optional(), this, function (x) {
            return x === undefined
                ? typeof def === 'function'
                    ? def(_this)
                    : def
                : x;
        });
    };
    return ZodType;
}());
exports.ZodType = ZodType;

});

var errorUtil_1$1 = createCommonjsModule$1(function (module, exports) {
Object.defineProperty(exports, "__esModule", { value: true });
var errorUtil;
(function (errorUtil) {
    errorUtil.errToObj = function (message) { return (typeof message === 'string' ? { message: message } : message || {}); };
})(errorUtil = exports.errorUtil || (exports.errorUtil = {}));

});

var __extends$1$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __assign$5 = (commonjsGlobal$1 && commonjsGlobal$1.__assign) || function () {
    __assign$5 = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign$5.apply(this, arguments);
};
var __importStar$q = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$q = __importStar$q(base$1);


var emailRegex$1 = /^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))$/i;
var uuidRegex$1 = /([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}){1}/i;
var ZodString$1 = (function (_super) {
    __extends$1$1(ZodString, _super);
    function ZodString() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.inputSchema = _this;
        _this.outputSchema = _this;
        _this.toJSON = function () { return _this._def; };
        _this.min = function (minLength, message) {
            return _this.refinement(function (data) { return data.length >= minLength; }, __assign$5({ code: ZodError_1$1.ZodIssueCode.too_small, minimum: minLength, type: 'string', inclusive: true }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        _this.max = function (maxLength, message) {
            return _this.refinement(function (data) { return data.length <= maxLength; }, __assign$5({ code: ZodError_1$1.ZodIssueCode.too_big, maximum: maxLength, type: 'string', inclusive: true }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        _this._regex = function (regex, validation, message) {
            return _this.refinement(function (data) { return regex.test(data); }, __assign$5({ validation: validation, code: ZodError_1$1.ZodIssueCode.invalid_string }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        _this.email = function (message) {
            return _this._regex(emailRegex$1, 'email', message);
        };
        _this.url = function (message) {
            return _this.refinement(function (data) {
                try {
                    new URL(data);
                    return true;
                }
                catch (_a) {
                    return false;
                }
            }, __assign$5({ code: ZodError_1$1.ZodIssueCode.invalid_string, validation: 'url' }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        _this.uuid = function (message) {
            return _this._regex(uuidRegex$1, 'uuid', message);
        };
        _this.regex = function (regexp, message) {
            return _this._regex(regexp, 'regex', message);
        };
        _this.nonempty = function (message) {
            return _this.min(1, errorUtil_1$1.errorUtil.errToObj(message));
        };
        return _this;
    }
    ZodString.prototype.length = function (len, message) {
        return this.min(len, message).max(len, message);
    };
    ZodString.create = function () {
        return new ZodString({
            t: z$q.ZodTypes.string,
            validation: {},
        });
    };
    return ZodString;
}(z$q.ZodType));
var ZodString_1$1 = ZodString$1;


var string$1 = /*#__PURE__*/Object.defineProperty({
	ZodString: ZodString_1$1
}, '__esModule', {value: true});

var __extends$2$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __assign$1$1 = (commonjsGlobal$1 && commonjsGlobal$1.__assign) || function () {
    __assign$1$1 = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign$1$1.apply(this, arguments);
};
var __importStar$1$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$1$1 = __importStar$1$1(base$1);


var ZodNumber$1 = (function (_super) {
    __extends$2$1(ZodNumber, _super);
    function ZodNumber() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        _this.min = function (minimum, message) {
            return _this.refinement(function (data) { return data >= minimum; }, __assign$1$1({ code: ZodError_1$1.ZodIssueCode.too_small, minimum: minimum, type: 'number', inclusive: true }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        _this.max = function (maximum, message) {
            return _this.refinement(function (data) { return data <= maximum; }, __assign$1$1({ code: ZodError_1$1.ZodIssueCode.too_big, maximum: maximum, type: 'number', inclusive: true }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        _this.int = function (message) {
            return _this.refinement(function (data) { return Number.isInteger(data); }, __assign$1$1({ code: ZodError_1$1.ZodIssueCode.invalid_type, expected: 'integer', received: 'number' }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        _this.positive = function (message) {
            return _this.refinement(function (data) { return data > 0; }, __assign$1$1({ code: ZodError_1$1.ZodIssueCode.too_small, minimum: 0, type: 'number', inclusive: false }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        _this.negative = function (message) {
            return _this.refinement(function (data) { return data < 0; }, __assign$1$1({ code: ZodError_1$1.ZodIssueCode.too_big, maximum: 0, type: 'number', inclusive: false }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        _this.nonpositive = function (message) {
            return _this.refinement(function (data) { return data <= 0; }, __assign$1$1({ code: ZodError_1$1.ZodIssueCode.too_big, maximum: 0, type: 'number', inclusive: true }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        _this.nonnegative = function (message) {
            return _this.refinement(function (data) { return data >= 0; }, __assign$1$1({ code: ZodError_1$1.ZodIssueCode.too_small, minimum: 0, type: 'number', inclusive: true }, errorUtil_1$1.errorUtil.errToObj(message)));
        };
        return _this;
    }
    ZodNumber.create = function () {
        return new ZodNumber({
            t: z$1$1.ZodTypes.number,
        });
    };
    return ZodNumber;
}(z$1$1.ZodType));
var ZodNumber_1$1 = ZodNumber$1;


var number$1 = /*#__PURE__*/Object.defineProperty({
	ZodNumber: ZodNumber_1$1
}, '__esModule', {value: true});

var __extends$3$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$2$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$2$1 = __importStar$2$1(base$1);
var ZodBigInt$1 = (function (_super) {
    __extends$3$1(ZodBigInt, _super);
    function ZodBigInt() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodBigInt.create = function () {
        return new ZodBigInt({
            t: z$2$1.ZodTypes.bigint,
        });
    };
    return ZodBigInt;
}(z$2$1.ZodType));
var ZodBigInt_1$1 = ZodBigInt$1;


var bigint$1 = /*#__PURE__*/Object.defineProperty({
	ZodBigInt: ZodBigInt_1$1
}, '__esModule', {value: true});

var __extends$4$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$3$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$3$1 = __importStar$3$1(base$1);
var ZodBoolean$1 = (function (_super) {
    __extends$4$1(ZodBoolean, _super);
    function ZodBoolean() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodBoolean.create = function () {
        return new ZodBoolean({
            t: z$3$1.ZodTypes.boolean,
        });
    };
    return ZodBoolean;
}(z$3$1.ZodType));
var ZodBoolean_1$1 = ZodBoolean$1;


var boolean$1 = /*#__PURE__*/Object.defineProperty({
	ZodBoolean: ZodBoolean_1$1
}, '__esModule', {value: true});

var __extends$5$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$4$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$4$1 = __importStar$4$1(base$1);
var ZodDate$1 = (function (_super) {
    __extends$5$1(ZodDate, _super);
    function ZodDate() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodDate.create = function () {
        return new ZodDate({
            t: z$4$1.ZodTypes.date,
        });
    };
    return ZodDate;
}(z$4$1.ZodType));
var ZodDate_1$1 = ZodDate$1;


var date$1 = /*#__PURE__*/Object.defineProperty({
	ZodDate: ZodDate_1$1
}, '__esModule', {value: true});

var __extends$6$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$5$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$5$1 = __importStar$5$1(base$1);
var ZodUndefined$1 = (function (_super) {
    __extends$6$1(ZodUndefined, _super);
    function ZodUndefined() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodUndefined.create = function () {
        return new ZodUndefined({
            t: z$5$1.ZodTypes.undefined,
        });
    };
    return ZodUndefined;
}(z$5$1.ZodType));
var ZodUndefined_1$1 = ZodUndefined$1;


var _undefined$1 = /*#__PURE__*/Object.defineProperty({
	ZodUndefined: ZodUndefined_1$1
}, '__esModule', {value: true});

var __extends$7$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$6$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$6$1 = __importStar$6$1(base$1);
var ZodNull$1 = (function (_super) {
    __extends$7$1(ZodNull, _super);
    function ZodNull() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodNull.create = function () {
        return new ZodNull({
            t: z$6$1.ZodTypes.null,
        });
    };
    return ZodNull;
}(z$6$1.ZodType));
var ZodNull_1$1 = ZodNull$1;


var _null$1 = /*#__PURE__*/Object.defineProperty({
	ZodNull: ZodNull_1$1
}, '__esModule', {value: true});

var __extends$8$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$7$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$7$1 = __importStar$7$1(base$1);
var ZodAny$1 = (function (_super) {
    __extends$8$1(ZodAny, _super);
    function ZodAny() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodAny.create = function () {
        return new ZodAny({
            t: z$7$1.ZodTypes.any,
        });
    };
    return ZodAny;
}(z$7$1.ZodType));
var ZodAny_1$1 = ZodAny$1;


var any$1 = /*#__PURE__*/Object.defineProperty({
	ZodAny: ZodAny_1$1
}, '__esModule', {value: true});

var __extends$9$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$8$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$8$1 = __importStar$8$1(base$1);
var ZodUnknown$1 = (function (_super) {
    __extends$9$1(ZodUnknown, _super);
    function ZodUnknown() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodUnknown.create = function () {
        return new ZodUnknown({
            t: z$8$1.ZodTypes.unknown,
        });
    };
    return ZodUnknown;
}(z$8$1.ZodType));
var ZodUnknown_1$1 = ZodUnknown$1;


var unknown$1 = /*#__PURE__*/Object.defineProperty({
	ZodUnknown: ZodUnknown_1$1
}, '__esModule', {value: true});

var __extends$a$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$9$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$9$1 = __importStar$9$1(base$1);
var ZodNever$1 = (function (_super) {
    __extends$a$1(ZodNever, _super);
    function ZodNever() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodNever.create = function () {
        return new ZodNever({
            t: z$9$1.ZodTypes.never,
        });
    };
    return ZodNever;
}(z$9$1.ZodType));
var ZodNever_1$1 = ZodNever$1;


var never$1 = /*#__PURE__*/Object.defineProperty({
	ZodNever: ZodNever_1$1
}, '__esModule', {value: true});

var __extends$b$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$a$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$a$1 = __importStar$a$1(base$1);
var ZodVoid$1 = (function (_super) {
    __extends$b$1(ZodVoid, _super);
    function ZodVoid() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodVoid.create = function () {
        return new ZodVoid({
            t: z$a$1.ZodTypes.void,
        });
    };
    return ZodVoid;
}(z$a$1.ZodType));
var ZodVoid_1$1 = ZodVoid$1;


var _void$1 = /*#__PURE__*/Object.defineProperty({
	ZodVoid: ZodVoid_1$1
}, '__esModule', {value: true});

var __extends$c$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __assign$2$1 = (commonjsGlobal$1 && commonjsGlobal$1.__assign) || function () {
    __assign$2$1 = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign$2$1.apply(this, arguments);
};
var __importStar$b$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$b$1 = __importStar$b$1(base$1);

var ZodArray$1 = (function (_super) {
    __extends$c$1(ZodArray, _super);
    function ZodArray() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () {
            return {
                t: _this._def.t,
                nonempty: _this._def.nonempty,
                type: _this._def.type.toJSON(),
            };
        };
        _this.min = function (minLength, message) {
            return _this.refinement(function (data) { return data.length >= minLength; }, __assign$2$1({ code: ZodError_1$1.ZodIssueCode.too_small, type: 'array', inclusive: true, minimum: minLength }, (typeof message === 'string' ? { message: message } : message)));
        };
        _this.max = function (maxLength, message) {
            return _this.refinement(function (data) { return data.length <= maxLength; }, __assign$2$1({ code: ZodError_1$1.ZodIssueCode.too_big, type: 'array', inclusive: true, maximum: maxLength }, (typeof message === 'string' ? { message: message } : message)));
        };
        _this.length = function (len, message) {
            return _this.min(len, { message: message }).max(len, { message: message });
        };
        _this.nonempty = function () {
            return new ZodNonEmptyArray$1(__assign$2$1(__assign$2$1({}, _this._def), { nonempty: true }));
        };
        return _this;
    }
    Object.defineProperty(ZodArray.prototype, "element", {
        get: function () {
            return this._def.type;
        },
        enumerable: true,
        configurable: true
    });
    ZodArray.create = function (schema) {
        return new ZodArray({
            t: z$b$1.ZodTypes.array,
            type: schema,
            nonempty: false,
        });
    };
    return ZodArray;
}(z$b$1.ZodType));
var ZodArray_1$1 = ZodArray$1;
var ZodNonEmptyArray$1 = (function (_super) {
    __extends$c$1(ZodNonEmptyArray, _super);
    function ZodNonEmptyArray() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () {
            return {
                t: _this._def.t,
                type: _this._def.type.toJSON(),
            };
        };
        _this.min = function (minLength, message) {
            return _this.refinement(function (data) { return data.length >= minLength; }, __assign$2$1({ code: ZodError_1$1.ZodIssueCode.too_small, minimum: minLength, type: 'array', inclusive: true }, (typeof message === 'string' ? { message: message } : message)));
        };
        _this.max = function (maxLength, message) {
            return _this.refinement(function (data) { return data.length <= maxLength; }, __assign$2$1({ code: ZodError_1$1.ZodIssueCode.too_big, maximum: maxLength, type: 'array', inclusive: true }, (typeof message === 'string' ? { message: message } : message)));
        };
        _this.length = function (len, message) {
            return _this.min(len, { message: message }).max(len, { message: message });
        };
        return _this;
    }
    return ZodNonEmptyArray;
}(z$b$1.ZodType));
var ZodNonEmptyArray_1$1 = ZodNonEmptyArray$1;


var array$1 = /*#__PURE__*/Object.defineProperty({
	ZodArray: ZodArray_1$1,
	ZodNonEmptyArray: ZodNonEmptyArray_1$1
}, '__esModule', {value: true});

var __extends$d$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$c$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$c$1 = __importStar$c$1(base$1);
var ZodIntersection$1 = (function (_super) {
    __extends$d$1(ZodIntersection, _super);
    function ZodIntersection() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            left: _this._def.left.toJSON(),
            right: _this._def.right.toJSON(),
        }); };
        return _this;
    }
    ZodIntersection.create = function (left, right) {
        return new ZodIntersection({
            t: z$c$1.ZodTypes.intersection,
            left: left,
            right: right,
        });
    };
    return ZodIntersection;
}(z$c$1.ZodType));
var ZodIntersection_1$1 = ZodIntersection$1;


var intersection$1 = /*#__PURE__*/Object.defineProperty({
	ZodIntersection: ZodIntersection_1$1
}, '__esModule', {value: true});

var objectUtil_1$1 = createCommonjsModule$1(function (module, exports) {
var __assign = (commonjsGlobal$1 && commonjsGlobal$1.__assign) || function () {
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
var __values = (commonjsGlobal$1 && commonjsGlobal$1.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
var __read = (commonjsGlobal$1 && commonjsGlobal$1.__read) || function (o, n) {
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
};
var __spread = (commonjsGlobal$1 && commonjsGlobal$1.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read(arguments[i]));
    return ar;
};
Object.defineProperty(exports, "__esModule", { value: true });



var objectUtil;
(function (objectUtil) {
    objectUtil.mergeShapes = function (first, second) {
        var e_1, _a;
        var firstKeys = Object.keys(first);
        var secondKeys = Object.keys(second);
        var sharedKeys = firstKeys.filter(function (k) { return secondKeys.indexOf(k) !== -1; });
        var sharedShape = {};
        try {
            for (var sharedKeys_1 = __values(sharedKeys), sharedKeys_1_1 = sharedKeys_1.next(); !sharedKeys_1_1.done; sharedKeys_1_1 = sharedKeys_1.next()) {
                var k = sharedKeys_1_1.value;
                sharedShape[k] = intersection$1.ZodIntersection.create(first[k], second[k]);
            }
        }
        catch (e_1_1) { e_1 = { error: e_1_1 }; }
        finally {
            try {
                if (sharedKeys_1_1 && !sharedKeys_1_1.done && (_a = sharedKeys_1.return)) _a.call(sharedKeys_1);
            }
            finally { if (e_1) throw e_1.error; }
        }
        return __assign(__assign(__assign({}, first), second), sharedShape);
    };
    objectUtil.mergeObjects = function (first) { return function (second) {
        var mergedShape = objectUtil.mergeShapes(first._def.shape(), second._def.shape());
        var merged = new object$1.ZodObject({
            t: base$1.ZodTypes.object,
            checks: __spread((first._def.checks || []), (second._def.checks || [])),
            unknownKeys: first._def.unknownKeys,
            catchall: first._def.catchall,
            shape: function () { return mergedShape; },
        });
        return merged;
    }; };
})(objectUtil = exports.objectUtil || (exports.objectUtil = {}));

});

var isScalar$1 = createCommonjsModule$1(function (module, exports) {
Object.defineProperty(exports, "__esModule", { value: true });


exports.isScalar = function (schema, params) {
    if (params === void 0) { params = { root: true }; }
    var def = schema._def;
    var returnValue = false;
    switch (def.t) {
        case base$1.ZodTypes.string:
            returnValue = true;
            break;
        case base$1.ZodTypes.number:
            returnValue = true;
            break;
        case base$1.ZodTypes.bigint:
            returnValue = true;
            break;
        case base$1.ZodTypes.boolean:
            returnValue = true;
            break;
        case base$1.ZodTypes.undefined:
            returnValue = true;
            break;
        case base$1.ZodTypes.null:
            returnValue = true;
            break;
        case base$1.ZodTypes.any:
            returnValue = false;
            break;
        case base$1.ZodTypes.unknown:
            returnValue = false;
            break;
        case base$1.ZodTypes.never:
            returnValue = false;
            break;
        case base$1.ZodTypes.void:
            returnValue = false;
            break;
        case base$1.ZodTypes.array:
            if (params.root === false)
                return false;
            returnValue = exports.isScalar(def.type, { root: false });
            break;
        case base$1.ZodTypes.object:
            returnValue = false;
            break;
        case base$1.ZodTypes.union:
            returnValue = def.options.every(function (x) { return exports.isScalar(x); });
            break;
        case base$1.ZodTypes.intersection:
            returnValue = exports.isScalar(def.left) && exports.isScalar(def.right);
            break;
        case base$1.ZodTypes.tuple:
            returnValue = def.items.every(function (x) { return exports.isScalar(x, { root: false }); });
            break;
        case base$1.ZodTypes.lazy:
            returnValue = exports.isScalar(def.getter());
            break;
        case base$1.ZodTypes.literal:
            returnValue = true;
            break;
        case base$1.ZodTypes.enum:
            returnValue = true;
            break;
        case base$1.ZodTypes.nativeEnum:
            returnValue = true;
            break;
        case base$1.ZodTypes.function:
            returnValue = false;
            break;
        case base$1.ZodTypes.record:
            returnValue = false;
            break;
        case base$1.ZodTypes.map:
            returnValue = false;
            break;
        case base$1.ZodTypes.date:
            returnValue = true;
            break;
        case base$1.ZodTypes.promise:
            returnValue = false;
            break;
        case base$1.ZodTypes.transformer:
            returnValue = exports.isScalar(def.output);
            break;
        case base$1.ZodTypes.optional:
            returnValue = exports.isScalar(def.innerType);
            break;
        case base$1.ZodTypes.nullable:
            returnValue = exports.isScalar(def.innerType);
            break;
        default:
            util_1$1.util.assertNever(def);
    }
    return returnValue;
};

});

var __extends$e$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __assign$3$1 = (commonjsGlobal$1 && commonjsGlobal$1.__assign) || function () {
    __assign$3$1 = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign$3$1.apply(this, arguments);
};
var __read$1$1 = (commonjsGlobal$1 && commonjsGlobal$1.__read) || function (o, n) {
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
};
var __spread$1$1 = (commonjsGlobal$1 && commonjsGlobal$1.__spread) || function () {
    for (var ar = [], i = 0; i < arguments.length; i++) ar = ar.concat(__read$1$1(arguments[i]));
    return ar;
};
var __importStar$d$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$d$1 = __importStar$d$1(base$1);



var AugmentFactory$1 = function (def) { return function (augmentation) {
    return new ZodObject$1(__assign$3$1(__assign$3$1({}, def), { shape: function () { return (__assign$3$1(__assign$3$1({}, def.shape()), augmentation)); } }));
}; };
var objectDefToJson$1 = function (def) { return ({
    t: def.t,
    shape: Object.assign.apply(Object, __spread$1$1([{}], Object.keys(def.shape()).map(function (k) {
        var _a;
        return (_a = {},
            _a[k] = def.shape()[k].toJSON(),
            _a);
    }))),
}); };
var ZodObject$1 = (function (_super) {
    __extends$e$1(ZodObject, _super);
    function ZodObject() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return objectDefToJson$1(_this._def); };
        _this.strict = function () {
            return new ZodObject(__assign$3$1(__assign$3$1({}, _this._def), { unknownKeys: 'strict' }));
        };
        _this.strip = function () {
            return new ZodObject(__assign$3$1(__assign$3$1({}, _this._def), { unknownKeys: 'strip' }));
        };
        _this.passthrough = function () {
            return new ZodObject(__assign$3$1(__assign$3$1({}, _this._def), { unknownKeys: 'passthrough' }));
        };
        _this.nonstrict = _this.passthrough;
        _this.augment = AugmentFactory$1(_this._def);
        _this.extend = AugmentFactory$1(_this._def);
        _this.setKey = function (key, schema) {
            var _a;
            return _this.augment((_a = {}, _a[key] = schema, _a));
        };
        _this.merge = objectUtil_1$1.objectUtil.mergeObjects(_this);
        _this.catchall = function (index) {
            return new ZodObject(__assign$3$1(__assign$3$1({}, _this._def), { catchall: index }));
        };
        _this.pick = function (mask) {
            var shape = {};
            Object.keys(mask).map(function (key) {
                shape[key] = _this.shape[key];
            });
            return new ZodObject(__assign$3$1(__assign$3$1({}, _this._def), { shape: function () { return shape; } }));
        };
        _this.omit = function (mask) {
            var shape = {};
            Object.keys(_this.shape).map(function (key) {
                if (Object.keys(mask).indexOf(key) === -1) {
                    shape[key] = _this.shape[key];
                }
            });
            return new ZodObject(__assign$3$1(__assign$3$1({}, _this._def), { shape: function () { return shape; } }));
        };
        _this.partial = function () {
            var newShape = {};
            for (var key in _this.shape) {
                var fieldSchema = _this.shape[key];
                newShape[key] = fieldSchema.isOptional()
                    ? fieldSchema
                    : fieldSchema.optional();
            }
            return new ZodObject(__assign$3$1(__assign$3$1({}, _this._def), { shape: function () { return newShape; } }));
        };
        _this.primitives = function () {
            var newShape = {};
            for (var key in _this.shape) {
                if (isScalar$1.isScalar(_this.shape[key])) {
                    newShape[key] = _this.shape[key];
                }
            }
            return new ZodObject(__assign$3$1(__assign$3$1({}, _this._def), { shape: function () { return newShape; } }));
        };
        _this.nonprimitives = function () {
            var newShape = {};
            for (var key in _this.shape) {
                if (!isScalar$1.isScalar(_this.shape[key])) {
                    newShape[key] = _this.shape[key];
                }
            }
            return new ZodObject(__assign$3$1(__assign$3$1({}, _this._def), { shape: function () { return newShape; } }));
        };
        _this.deepPartial = function () {
            var newShape = {};
            for (var key in _this.shape) {
                var fieldSchema = _this.shape[key];
                if (fieldSchema instanceof ZodObject) {
                    newShape[key] = fieldSchema.isOptional()
                        ? fieldSchema
                        : fieldSchema.deepPartial().optional();
                }
                else {
                    newShape[key] = fieldSchema.isOptional()
                        ? fieldSchema
                        : fieldSchema.optional();
                }
            }
            return new ZodObject(__assign$3$1(__assign$3$1({}, _this._def), { shape: function () { return newShape; } }));
        };
        return _this;
    }
    Object.defineProperty(ZodObject.prototype, "shape", {
        get: function () {
            return this._def.shape();
        },
        enumerable: true,
        configurable: true
    });
    ZodObject.create = function (shape) {
        return new ZodObject({
            t: z$d$1.ZodTypes.object,
            shape: function () { return shape; },
            unknownKeys: 'strip',
            catchall: cjs$1.ZodNever.create(),
        });
    };
    ZodObject.lazycreate = function (shape) {
        return new ZodObject({
            t: z$d$1.ZodTypes.object,
            shape: shape,
            unknownKeys: 'strip',
            catchall: cjs$1.ZodNever.create(),
        });
    };
    return ZodObject;
}(z$d$1.ZodType));
var ZodObject_1$1 = ZodObject$1;


var object$1 = /*#__PURE__*/Object.defineProperty({
	ZodObject: ZodObject_1$1
}, '__esModule', {value: true});

var __extends$f$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$e$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$e$1 = __importStar$e$1(base$1);
var ZodUnion$1 = (function (_super) {
    __extends$f$1(ZodUnion, _super);
    function ZodUnion() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            options: _this._def.options.map(function (x) { return x.toJSON(); }),
        }); };
        return _this;
    }
    Object.defineProperty(ZodUnion.prototype, "options", {
        get: function () {
            return this._def.options;
        },
        enumerable: true,
        configurable: true
    });
    ZodUnion.create = function (types) {
        return new ZodUnion({
            t: z$e$1.ZodTypes.union,
            options: types,
        });
    };
    return ZodUnion;
}(z$e$1.ZodType));
var ZodUnion_1$1 = ZodUnion$1;


var union$1 = /*#__PURE__*/Object.defineProperty({
	ZodUnion: ZodUnion_1$1
}, '__esModule', {value: true});

var __extends$g$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$f$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$f$1 = __importStar$f$1(base$1);
var ZodTuple$1 = (function (_super) {
    __extends$g$1(ZodTuple, _super);
    function ZodTuple() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            items: _this._def.items.map(function (item) { return item.toJSON(); }),
        }); };
        return _this;
    }
    Object.defineProperty(ZodTuple.prototype, "items", {
        get: function () {
            return this._def.items;
        },
        enumerable: true,
        configurable: true
    });
    ZodTuple.create = function (schemas) {
        return new ZodTuple({
            t: z$f$1.ZodTypes.tuple,
            items: schemas,
        });
    };
    return ZodTuple;
}(z$f$1.ZodType));
var ZodTuple_1$1 = ZodTuple$1;


var tuple$1 = /*#__PURE__*/Object.defineProperty({
	ZodTuple: ZodTuple_1$1
}, '__esModule', {value: true});

var __extends$h$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$g$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$g$1 = __importStar$g$1(base$1);
var ZodRecord$1 = (function (_super) {
    __extends$h$1(ZodRecord, _super);
    function ZodRecord() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            valueType: _this._def.valueType.toJSON(),
        }); };
        return _this;
    }
    ZodRecord.create = function (valueType) {
        return new ZodRecord({
            t: z$g$1.ZodTypes.record,
            valueType: valueType,
        });
    };
    return ZodRecord;
}(z$g$1.ZodType));
var ZodRecord_1$1 = ZodRecord$1;


var record$1 = /*#__PURE__*/Object.defineProperty({
	ZodRecord: ZodRecord_1$1
}, '__esModule', {value: true});

var __extends$i$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$h$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$h$1 = __importStar$h$1(base$1);
var ZodMap$1 = (function (_super) {
    __extends$i$1(ZodMap, _super);
    function ZodMap() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            valueType: _this._def.valueType.toJSON(),
            keyType: _this._def.keyType.toJSON(),
        }); };
        return _this;
    }
    ZodMap.create = function (keyType, valueType) {
        return new ZodMap({
            t: z$h$1.ZodTypes.map,
            valueType: valueType,
            keyType: keyType,
        });
    };
    return ZodMap;
}(z$h$1.ZodType));
var ZodMap_1$1 = ZodMap$1;


var map$1 = /*#__PURE__*/Object.defineProperty({
	ZodMap: ZodMap_1$1
}, '__esModule', {value: true});

var __extends$j$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __assign$4$1 = (commonjsGlobal$1 && commonjsGlobal$1.__assign) || function () {
    __assign$4$1 = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign$4$1.apply(this, arguments);
};
var __importStar$i$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$i$1 = __importStar$i$1(base$1);


var ZodFunction$1 = (function (_super) {
    __extends$j$1(ZodFunction, _super);
    function ZodFunction() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.args = function () {
            var items = [];
            for (var _i = 0; _i < arguments.length; _i++) {
                items[_i] = arguments[_i];
            }
            return new ZodFunction(__assign$4$1(__assign$4$1({}, _this._def), { args: tuple$1.ZodTuple.create(items) }));
        };
        _this.returns = function (returnType) {
            return new ZodFunction(__assign$4$1(__assign$4$1({}, _this._def), { returns: returnType }));
        };
        _this.implement = function (func) {
            var validatedFunc = _this.parse(func);
            return validatedFunc;
        };
        _this.validate = _this.implement;
        _this.toJSON = function () {
            return {
                t: _this._def.t,
                args: _this._def.args.toJSON(),
                returns: _this._def.returns.toJSON(),
            };
        };
        return _this;
    }
    ZodFunction.create = function (args, returns) {
        return new ZodFunction({
            t: z$i$1.ZodTypes.function,
            args: args || tuple$1.ZodTuple.create([]),
            returns: returns || unknown$1.ZodUnknown.create(),
        });
    };
    return ZodFunction;
}(z$i$1.ZodType));
var ZodFunction_1$1 = ZodFunction$1;


var _function$1 = /*#__PURE__*/Object.defineProperty({
	ZodFunction: ZodFunction_1$1
}, '__esModule', {value: true});

var __extends$k$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$j$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$j$1 = __importStar$j$1(base$1);
var ZodLazy$1 = (function (_super) {
    __extends$k$1(ZodLazy, _super);
    function ZodLazy() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () {
            throw new Error("Can't JSONify recursive structure");
        };
        return _this;
    }
    Object.defineProperty(ZodLazy.prototype, "schema", {
        get: function () {
            return this._def.getter();
        },
        enumerable: true,
        configurable: true
    });
    ZodLazy.create = function (getter) {
        return new ZodLazy({
            t: z$j$1.ZodTypes.lazy,
            getter: getter,
        });
    };
    return ZodLazy;
}(z$j$1.ZodType));
var ZodLazy_1$1 = ZodLazy$1;


var lazy$1 = /*#__PURE__*/Object.defineProperty({
	ZodLazy: ZodLazy_1$1
}, '__esModule', {value: true});

var __extends$l$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$k$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$k$1 = __importStar$k$1(base$1);
var ZodLiteral$1 = (function (_super) {
    __extends$l$1(ZodLiteral, _super);
    function ZodLiteral() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodLiteral.create = function (value) {
        return new ZodLiteral({
            t: z$k$1.ZodTypes.literal,
            value: value,
        });
    };
    return ZodLiteral;
}(z$k$1.ZodType));
var ZodLiteral_1$1 = ZodLiteral$1;


var literal$1 = /*#__PURE__*/Object.defineProperty({
	ZodLiteral: ZodLiteral_1$1
}, '__esModule', {value: true});

var __extends$m$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __values$1$1 = (commonjsGlobal$1 && commonjsGlobal$1.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
var __importStar$l$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$l$1 = __importStar$l$1(base$1);
var ZodEnum$1 = (function (_super) {
    __extends$m$1(ZodEnum, _super);
    function ZodEnum() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    Object.defineProperty(ZodEnum.prototype, "options", {
        get: function () {
            return this._def.values;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodEnum.prototype, "enum", {
        get: function () {
            var e_1, _a;
            var enumValues = {};
            try {
                for (var _b = __values$1$1(this._def.values), _c = _b.next(); !_c.done; _c = _b.next()) {
                    var val = _c.value;
                    enumValues[val] = val;
                }
            }
            catch (e_1_1) { e_1 = { error: e_1_1 }; }
            finally {
                try {
                    if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
                }
                finally { if (e_1) throw e_1.error; }
            }
            return enumValues;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodEnum.prototype, "Values", {
        get: function () {
            var e_2, _a;
            var enumValues = {};
            try {
                for (var _b = __values$1$1(this._def.values), _c = _b.next(); !_c.done; _c = _b.next()) {
                    var val = _c.value;
                    enumValues[val] = val;
                }
            }
            catch (e_2_1) { e_2 = { error: e_2_1 }; }
            finally {
                try {
                    if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
                }
                finally { if (e_2) throw e_2.error; }
            }
            return enumValues;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(ZodEnum.prototype, "Enum", {
        get: function () {
            var e_3, _a;
            var enumValues = {};
            try {
                for (var _b = __values$1$1(this._def.values), _c = _b.next(); !_c.done; _c = _b.next()) {
                    var val = _c.value;
                    enumValues[val] = val;
                }
            }
            catch (e_3_1) { e_3 = { error: e_3_1 }; }
            finally {
                try {
                    if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
                }
                finally { if (e_3) throw e_3.error; }
            }
            return enumValues;
        },
        enumerable: true,
        configurable: true
    });
    ZodEnum.create = function (values) {
        return new ZodEnum({
            t: z$l$1.ZodTypes.enum,
            values: values,
        });
    };
    return ZodEnum;
}(z$l$1.ZodType));
var ZodEnum_1$1 = ZodEnum$1;


var _enum$1 = /*#__PURE__*/Object.defineProperty({
	ZodEnum: ZodEnum_1$1
}, '__esModule', {value: true});

var __extends$n$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$m$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$m$1 = __importStar$m$1(base$1);
var ZodNativeEnum$1 = (function (_super) {
    __extends$n$1(ZodNativeEnum, _super);
    function ZodNativeEnum() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return _this._def; };
        return _this;
    }
    ZodNativeEnum.create = function (values) {
        return new ZodNativeEnum({
            t: z$m$1.ZodTypes.nativeEnum,
            values: values,
        });
    };
    return ZodNativeEnum;
}(z$m$1.ZodType));
var ZodNativeEnum_1$1 = ZodNativeEnum$1;


var nativeEnum$1 = /*#__PURE__*/Object.defineProperty({
	ZodNativeEnum: ZodNativeEnum_1$1
}, '__esModule', {value: true});

var __extends$o$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$n$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$n$1 = __importStar$n$1(base$1);
var ZodPromise$1 = (function (_super) {
    __extends$o$1(ZodPromise, _super);
    function ZodPromise() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () {
            return {
                t: _this._def.t,
                type: _this._def.type.toJSON(),
            };
        };
        return _this;
    }
    ZodPromise.create = function (schema) {
        return new ZodPromise({
            t: z$n$1.ZodTypes.promise,
            type: schema,
        });
    };
    return ZodPromise;
}(z$n$1.ZodType));
var ZodPromise_1$1 = ZodPromise$1;


var promise$1 = /*#__PURE__*/Object.defineProperty({
	ZodPromise: ZodPromise_1$1
}, '__esModule', {value: true});

var __extends$p$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$o$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$o$1 = __importStar$o$1(base$1);
var ZodTransformer$1 = (function (_super) {
    __extends$p$1(ZodTransformer, _super);
    function ZodTransformer() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            left: _this._def.input.toJSON(),
            right: _this._def.output.toJSON(),
        }); };
        return _this;
    }
    Object.defineProperty(ZodTransformer.prototype, "output", {
        get: function () {
            return this._def.output;
        },
        enumerable: true,
        configurable: true
    });
    ZodTransformer.create = function (input, output, transformer) {
        return new ZodTransformer({
            t: z$o$1.ZodTypes.transformer,
            input: input,
            output: output,
            transformer: transformer,
        });
    };
    ZodTransformer.fromSchema = function (input) {
        return new ZodTransformer({
            t: z$o$1.ZodTypes.transformer,
            input: input,
            output: input,
            transformer: function (x) { return x; },
        });
    };
    return ZodTransformer;
}(z$o$1.ZodType));
var ZodTransformer_1$1 = ZodTransformer$1;


var transformer$1 = /*#__PURE__*/Object.defineProperty({
	ZodTransformer: ZodTransformer_1$1
}, '__esModule', {value: true});

var __extends$q$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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


var ZodOptional$1 = (function (_super) {
    __extends$q$1(ZodOptional, _super);
    function ZodOptional() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            innerType: _this._def.innerType.toJSON(),
        }); };
        return _this;
    }
    ZodOptional.create = function (type) {
        if (type instanceof ZodOptional)
            return type;
        return new ZodOptional({
            t: base$1.ZodTypes.optional,
            innerType: type,
        });
    };
    return ZodOptional;
}(base$1.ZodType));
var ZodOptional_1$1 = ZodOptional$1;


var optional$1 = /*#__PURE__*/Object.defineProperty({
	ZodOptional: ZodOptional_1$1
}, '__esModule', {value: true});

var __extends$r$1 = (commonjsGlobal$1 && commonjsGlobal$1.__extends) || (function () {
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
var __importStar$p$1 = (commonjsGlobal$1 && commonjsGlobal$1.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};

var z$p$1 = __importStar$p$1(base$1);
var ZodNullable$1 = (function (_super) {
    __extends$r$1(ZodNullable, _super);
    function ZodNullable() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.toJSON = function () { return ({
            t: _this._def.t,
            innerType: _this._def.innerType.toJSON(),
        }); };
        return _this;
    }
    ZodNullable.create = function (type) {
        if (type instanceof ZodNullable)
            return type;
        return new ZodNullable({
            t: z$p$1.ZodTypes.nullable,
            innerType: type,
        });
    };
    return ZodNullable;
}(z$p$1.ZodType));
var ZodNullable_1$1 = ZodNullable$1;


var nullable$1 = /*#__PURE__*/Object.defineProperty({
	ZodNullable: ZodNullable_1$1
}, '__esModule', {value: true});

var __values$2$1 = (commonjsGlobal$1 && commonjsGlobal$1.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};



var isOptional$1 = function (schema) {
    return schema.isOptional();
};
var ZodCodeGenerator$1 = (function () {
    function ZodCodeGenerator() {
        var _this = this;
        this.seen = [];
        this.serial = 0;
        this.randomId = function () {
            return "IZod" + _this.serial++;
        };
        this.findBySchema = function (schema) {
            return _this.seen.find(function (s) { return s.schema === schema; });
        };
        this.findById = function (id) {
            var found = _this.seen.find(function (s) { return s.id === id; });
            if (!found)
                throw new Error("Unfound ID: " + id);
            return found;
        };
        this.dump = function () {
            return "\ntype Identity<T> = T;\n\n" + _this.seen
                .map(function (item) { return "type " + item.id + " = Identity<" + item.type + ">;"; })
                .join('\n\n') + "\n";
        };
        this.setType = function (id, type) {
            var found = _this.findById(id);
            found.type = type;
            return found;
        };
        this.generate = function (schema) {
            var e_1, _a, e_2, _b;
            var found = _this.findBySchema(schema);
            if (found)
                return found;
            var def = schema._def;
            var id = _this.randomId();
            var ty = {
                schema: schema,
                id: id,
                type: "__INCOMPLETE__",
            };
            _this.seen.push(ty);
            switch (def.t) {
                case base$1.ZodTypes.string:
                    return _this.setType(id, "string");
                case base$1.ZodTypes.number:
                    return _this.setType(id, "number");
                case base$1.ZodTypes.bigint:
                    return _this.setType(id, "bigint");
                case base$1.ZodTypes.boolean:
                    return _this.setType(id, "boolean");
                case base$1.ZodTypes.date:
                    return _this.setType(id, "Date");
                case base$1.ZodTypes.undefined:
                    return _this.setType(id, "undefined");
                case base$1.ZodTypes.null:
                    return _this.setType(id, "null");
                case base$1.ZodTypes.any:
                    return _this.setType(id, "any");
                case base$1.ZodTypes.unknown:
                    return _this.setType(id, "unknown");
                case base$1.ZodTypes.never:
                    return _this.setType(id, "never");
                case base$1.ZodTypes.void:
                    return _this.setType(id, "void");
                case base$1.ZodTypes.literal:
                    var val = def.value;
                    var literalType = typeof val === 'string' ? "\"" + val + "\"" : "" + val;
                    return _this.setType(id, literalType);
                case base$1.ZodTypes.enum:
                    return _this.setType(id, def.values.map(function (v) { return "\"" + v + "\""; }).join(' | '));
                case base$1.ZodTypes.object:
                    var objectLines = [];
                    var shape = def.shape();
                    for (var key in shape) {
                        var childSchema = shape[key];
                        var childType = _this.generate(childSchema);
                        var OPTKEY = isOptional$1(childSchema) ? '?' : '';
                        objectLines.push("" + key + OPTKEY + ": " + childType.id);
                    }
                    var baseStruct = "{\n" + objectLines
                        .map(function (line) { return "  " + line + ";"; })
                        .join('\n') + "\n}";
                    _this.setType(id, "" + baseStruct);
                    break;
                case base$1.ZodTypes.tuple:
                    var tupleLines = [];
                    try {
                        for (var _c = __values$2$1(def.items), _d = _c.next(); !_d.done; _d = _c.next()) {
                            var elSchema = _d.value;
                            var elType = _this.generate(elSchema);
                            tupleLines.push(elType.id);
                        }
                    }
                    catch (e_1_1) { e_1 = { error: e_1_1 }; }
                    finally {
                        try {
                            if (_d && !_d.done && (_a = _c.return)) _a.call(_c);
                        }
                        finally { if (e_1) throw e_1.error; }
                    }
                    var baseTuple = "[\n" + tupleLines
                        .map(function (line) { return "  " + line + ","; })
                        .join('\n') + "\n]";
                    return _this.setType(id, "" + baseTuple);
                case base$1.ZodTypes.array:
                    return _this.setType(id, _this.generate(def.type).id + "[]");
                case base$1.ZodTypes.function:
                    var args = _this.generate(def.args);
                    var returns = _this.generate(def.returns);
                    return _this.setType(id, "(...args: " + args.id + ")=>" + returns.id);
                case base$1.ZodTypes.promise:
                    var promValue = _this.generate(def.type);
                    return _this.setType(id, "Promise<" + promValue.id + ">");
                case base$1.ZodTypes.union:
                    var unionLines = [];
                    try {
                        for (var _e = __values$2$1(def.options), _f = _e.next(); !_f.done; _f = _e.next()) {
                            var elSchema = _f.value;
                            var elType = _this.generate(elSchema);
                            unionLines.push(elType.id);
                        }
                    }
                    catch (e_2_1) { e_2 = { error: e_2_1 }; }
                    finally {
                        try {
                            if (_f && !_f.done && (_b = _e.return)) _b.call(_e);
                        }
                        finally { if (e_2) throw e_2.error; }
                    }
                    return _this.setType(id, unionLines.join(" | "));
                case base$1.ZodTypes.intersection:
                    return _this.setType(id, _this.generate(def.left).id + " & " + _this.generate(def.right).id);
                case base$1.ZodTypes.record:
                    return _this.setType(id, "{[k:string]: " + _this.generate(def.valueType).id + "}");
                case base$1.ZodTypes.transformer:
                    return _this.setType(id, _this.generate(def.output).id);
                case base$1.ZodTypes.map:
                    return _this.setType(id, "Map<" + _this.generate(def.keyType).id + ", " + _this.generate(def.valueType).id + ">");
                case base$1.ZodTypes.lazy:
                    var lazyType = def.getter();
                    return _this.setType(id, _this.generate(lazyType).id);
                case base$1.ZodTypes.nativeEnum:
                    return _this.setType(id, 'asdf');
                case base$1.ZodTypes.optional:
                    return _this.setType(id, _this.generate(def.innerType).id + " | undefined");
                case base$1.ZodTypes.nullable:
                    return _this.setType(id, _this.generate(def.innerType).id + " | null");
                default:
                    util_1$1.util.assertNever(def);
            }
            return _this.findById(id);
        };
    }
    ZodCodeGenerator.create = function () { return new ZodCodeGenerator(); };
    return ZodCodeGenerator;
}());
var ZodCodeGenerator_1$1 = ZodCodeGenerator$1;


var codegen$1 = /*#__PURE__*/Object.defineProperty({
	ZodCodeGenerator: ZodCodeGenerator_1$1
}, '__esModule', {value: true});

var cjs$1 = createCommonjsModule$1(function (module, exports) {
function __export(m) {
    for (var p in m) if (!exports.hasOwnProperty(p)) exports[p] = m[p];
}
Object.defineProperty(exports, "__esModule", { value: true });

exports.ZodString = string$1.ZodString;

exports.ZodNumber = number$1.ZodNumber;

exports.ZodBigInt = bigint$1.ZodBigInt;

exports.ZodBoolean = boolean$1.ZodBoolean;

exports.ZodDate = date$1.ZodDate;

exports.ZodUndefined = _undefined$1.ZodUndefined;

exports.ZodNull = _null$1.ZodNull;

exports.ZodAny = any$1.ZodAny;

exports.ZodUnknown = unknown$1.ZodUnknown;

exports.ZodNever = never$1.ZodNever;

exports.ZodVoid = _void$1.ZodVoid;

exports.ZodArray = array$1.ZodArray;

exports.ZodObject = object$1.ZodObject;

exports.ZodUnion = union$1.ZodUnion;

exports.ZodIntersection = intersection$1.ZodIntersection;

exports.ZodTuple = tuple$1.ZodTuple;

exports.ZodRecord = record$1.ZodRecord;


exports.ZodFunction = _function$1.ZodFunction;

exports.ZodLazy = lazy$1.ZodLazy;

exports.ZodLiteral = literal$1.ZodLiteral;

exports.ZodEnum = _enum$1.ZodEnum;

exports.ZodNativeEnum = nativeEnum$1.ZodNativeEnum;

exports.ZodPromise = promise$1.ZodPromise;

exports.ZodTransformer = transformer$1.ZodTransformer;

exports.ZodOptional = optional$1.ZodOptional;

exports.ZodNullable = nullable$1.ZodNullable;

exports.ZodType = base$1.ZodType;
exports.Schema = base$1.ZodType;
exports.ZodSchema = base$1.ZodType;
exports.ZodTypes = base$1.ZodTypes;

exports.ZodParsedType = parser$1.ZodParsedType;

exports.ZodCodeGenerator = codegen$1.ZodCodeGenerator;
var stringType = string$1.ZodString.create;
exports.string = stringType;
var numberType = number$1.ZodNumber.create;
exports.number = numberType;
var bigIntType = bigint$1.ZodBigInt.create;
exports.bigint = bigIntType;
var booleanType = boolean$1.ZodBoolean.create;
exports.boolean = booleanType;
var dateType = date$1.ZodDate.create;
exports.date = dateType;
var undefinedType = _undefined$1.ZodUndefined.create;
exports.undefined = undefinedType;
var nullType = _null$1.ZodNull.create;
exports.null = nullType;
var anyType = any$1.ZodAny.create;
exports.any = anyType;
var unknownType = unknown$1.ZodUnknown.create;
exports.unknown = unknownType;
var neverType = never$1.ZodNever.create;
exports.never = neverType;
var voidType = _void$1.ZodVoid.create;
exports.void = voidType;
var arrayType = array$1.ZodArray.create;
exports.array = arrayType;
var objectType = object$1.ZodObject.create;
exports.object = objectType;
var unionType = union$1.ZodUnion.create;
exports.union = unionType;
var intersectionType = intersection$1.ZodIntersection.create;
exports.intersection = intersectionType;
var tupleType = tuple$1.ZodTuple.create;
exports.tuple = tupleType;
var recordType = record$1.ZodRecord.create;
exports.record = recordType;
var mapType = map$1.ZodMap.create;
exports.map = mapType;
var functionType = _function$1.ZodFunction.create;
exports.function = functionType;
var lazyType = lazy$1.ZodLazy.create;
exports.lazy = lazyType;
var literalType = literal$1.ZodLiteral.create;
exports.literal = literalType;
var enumType = _enum$1.ZodEnum.create;
exports.enum = enumType;
var nativeEnumType = nativeEnum$1.ZodNativeEnum.create;
exports.nativeEnum = nativeEnumType;
var promiseType = promise$1.ZodPromise.create;
exports.promise = promiseType;
var transformerType = transformer$1.ZodTransformer.create;
exports.transformer = transformerType;
var optionalType = optional$1.ZodOptional.create;
exports.optional = optionalType;
var nullableType = nullable$1.ZodNullable.create;
exports.nullable = nullableType;
var ostring = function () { return stringType().optional(); };
exports.ostring = ostring;
var onumber = function () { return numberType().optional(); };
exports.onumber = onumber;
var oboolean = function () { return booleanType().optional(); };
exports.oboolean = oboolean;
var codegen$1$1 = codegen$1.ZodCodeGenerator.create;
exports.codegen = codegen$1$1;
exports.custom = function (check, params) {
    if (check)
        return anyType().refine(check, params);
    return anyType();
};
var instanceOfType = function (cls, params) {
    if (params === void 0) { params = {
        message: "Input not instance of " + cls.name,
    }; }
    return exports.custom(function (data) { return data instanceof cls; }, params);
};
exports.instanceof = instanceOfType;
exports.late = {
    object: object$1.ZodObject.lazycreate,
};
__export(ZodError_1$1);

});

const PluginConfigBaseSchema$1 = cjs$1.object({
    apiVersionRequired: cjs$1.string(),
    pluginPath: cjs$1.string(),
    id: cjs$1.string(),
})
    .catchall(cjs$1.unknown());
class PluginBase {
    constructor(apiVersionProvided) {
        this.apiVersionProvided = apiVersionProvided;
        this.id = `plugin`;
    }
}

let FORCE_COLOR$1, NODE_DISABLE_COLORS$1, NO_COLOR$1, TERM$1, isTTY$1=true;
if (typeof process !== 'undefined') {
	({ FORCE_COLOR: FORCE_COLOR$1, NODE_DISABLE_COLORS: NODE_DISABLE_COLORS$1, NO_COLOR: NO_COLOR$1, TERM: TERM$1 } = process.env);
	isTTY$1 = process.stdout && process.stdout.isTTY;
}

const $$1 = {
	enabled: !NODE_DISABLE_COLORS$1 && NO_COLOR$1 == null && TERM$1 !== 'dumb' && (
		FORCE_COLOR$1 != null && FORCE_COLOR$1 !== '0' || isTTY$1
	)
};

function init$1(x, y) {
	let rgx = new RegExp(`\\x1b\\[${y}m`, 'g');
	let open = `\x1b[${x}m`, close = `\x1b[${y}m`;

	return function (txt) {
		if (!$$1.enabled || txt == null) return txt;
		return open + ((''+txt).includes(close) ? txt.replace(rgx, close + open) : txt) + close;
	};
}
const grey$1 = init$1(90, 39);

/* eslint-disable no-console */
// const bee = `\u{1F41D}`;
const debug$2 = `\u{1F3F7}`;
const tick$1 = `\u{2705}`;
const error$1 = `\u{2757}`;
const warning$1 = `\u{26A0}`;
const info$1 = `\u{2139}`;
const fatal$1 = `\u{203C}`;
const play$1 = `\u{1F41D}`;
class Logger$1 {
    constructor(module) {
        this._prefix = `${grey$1(`Zigzag`)} ${grey$1(`[${module}]`)}`;
    }
    debug(message) {
        console.log(`${this._prefix} ${debug$2} ${message}`);
    }
    error(message) {
        console.log(`${this._prefix} ${error$1} ${message}`);
    }
    fatal(message) {
        console.log(`${this._prefix} ${fatal$1} ${message}`);
    }
    info(message) {
        console.log(`${this._prefix} ${info$1} ${message}`);
    }
    success(message) {
        console.log(`${this._prefix} ${tick$1} ${message}`);
    }
    start(message) {
        console.log(`${this._prefix} ${play$1} ${message}`);
    }
    warn(message) {
        console.log(`${this._prefix} ${warning$1} ${message}`);
    }
}
/* eslint-enable no-console */

// Note: this is the semver.org version of the spec that it implements
// Not necessarily the package version of this code.
const SEMVER_SPEC_VERSION$1 = '2.0.0';

const MAX_LENGTH$3 = 256;
const MAX_SAFE_INTEGER$2 = Number.MAX_SAFE_INTEGER ||
  /* istanbul ignore next */ 9007199254740991;

// Max safe segment length for coercion.
const MAX_SAFE_COMPONENT_LENGTH$1 = 16;

var constants$1 = {
  SEMVER_SPEC_VERSION: SEMVER_SPEC_VERSION$1,
  MAX_LENGTH: MAX_LENGTH$3,
  MAX_SAFE_INTEGER: MAX_SAFE_INTEGER$2,
  MAX_SAFE_COMPONENT_LENGTH: MAX_SAFE_COMPONENT_LENGTH$1
};

const debug$1$1 = (
  typeof process === 'object' &&
  process.env &&
  process.env.NODE_DEBUG &&
  /\bsemver\b/i.test(process.env.NODE_DEBUG)
) ? (...args) => console.error('SEMVER', ...args)
  : () => {};

var debug_1$1 = debug$1$1;

var re_1$1 = createCommonjsModule$1(function (module, exports) {
const { MAX_SAFE_COMPONENT_LENGTH } = constants$1;

exports = module.exports = {};

// The actual regexps go on exports.re
const re = exports.re = [];
const src = exports.src = [];
const t = exports.t = {};
let R = 0;

const createToken = (name, value, isGlobal) => {
  const index = R++;
  debug_1$1(index, value);
  t[name] = index;
  src[index] = value;
  re[index] = new RegExp(value, isGlobal ? 'g' : undefined);
};

// The following Regular Expressions can be used for tokenizing,
// validating, and parsing SemVer version strings.

// ## Numeric Identifier
// A single `0`, or a non-zero digit followed by zero or more digits.

createToken('NUMERICIDENTIFIER', '0|[1-9]\\d*');
createToken('NUMERICIDENTIFIERLOOSE', '[0-9]+');

// ## Non-numeric Identifier
// Zero or more digits, followed by a letter or hyphen, and then zero or
// more letters, digits, or hyphens.

createToken('NONNUMERICIDENTIFIER', '\\d*[a-zA-Z-][a-zA-Z0-9-]*');

// ## Main Version
// Three dot-separated numeric identifiers.

createToken('MAINVERSION', `(${src[t.NUMERICIDENTIFIER]})\\.` +
                   `(${src[t.NUMERICIDENTIFIER]})\\.` +
                   `(${src[t.NUMERICIDENTIFIER]})`);

createToken('MAINVERSIONLOOSE', `(${src[t.NUMERICIDENTIFIERLOOSE]})\\.` +
                        `(${src[t.NUMERICIDENTIFIERLOOSE]})\\.` +
                        `(${src[t.NUMERICIDENTIFIERLOOSE]})`);

// ## Pre-release Version Identifier
// A numeric identifier, or a non-numeric identifier.

createToken('PRERELEASEIDENTIFIER', `(?:${src[t.NUMERICIDENTIFIER]
}|${src[t.NONNUMERICIDENTIFIER]})`);

createToken('PRERELEASEIDENTIFIERLOOSE', `(?:${src[t.NUMERICIDENTIFIERLOOSE]
}|${src[t.NONNUMERICIDENTIFIER]})`);

// ## Pre-release Version
// Hyphen, followed by one or more dot-separated pre-release version
// identifiers.

createToken('PRERELEASE', `(?:-(${src[t.PRERELEASEIDENTIFIER]
}(?:\\.${src[t.PRERELEASEIDENTIFIER]})*))`);

createToken('PRERELEASELOOSE', `(?:-?(${src[t.PRERELEASEIDENTIFIERLOOSE]
}(?:\\.${src[t.PRERELEASEIDENTIFIERLOOSE]})*))`);

// ## Build Metadata Identifier
// Any combination of digits, letters, or hyphens.

createToken('BUILDIDENTIFIER', '[0-9A-Za-z-]+');

// ## Build Metadata
// Plus sign, followed by one or more period-separated build metadata
// identifiers.

createToken('BUILD', `(?:\\+(${src[t.BUILDIDENTIFIER]
}(?:\\.${src[t.BUILDIDENTIFIER]})*))`);

// ## Full Version String
// A main version, followed optionally by a pre-release version and
// build metadata.

// Note that the only major, minor, patch, and pre-release sections of
// the version string are capturing groups.  The build metadata is not a
// capturing group, because it should not ever be used in version
// comparison.

createToken('FULLPLAIN', `v?${src[t.MAINVERSION]
}${src[t.PRERELEASE]}?${
  src[t.BUILD]}?`);

createToken('FULL', `^${src[t.FULLPLAIN]}$`);

// like full, but allows v1.2.3 and =1.2.3, which people do sometimes.
// also, 1.0.0alpha1 (prerelease without the hyphen) which is pretty
// common in the npm registry.
createToken('LOOSEPLAIN', `[v=\\s]*${src[t.MAINVERSIONLOOSE]
}${src[t.PRERELEASELOOSE]}?${
  src[t.BUILD]}?`);

createToken('LOOSE', `^${src[t.LOOSEPLAIN]}$`);

createToken('GTLT', '((?:<|>)?=?)');

// Something like "2.*" or "1.2.x".
// Note that "x.x" is a valid xRange identifer, meaning "any version"
// Only the first item is strictly required.
createToken('XRANGEIDENTIFIERLOOSE', `${src[t.NUMERICIDENTIFIERLOOSE]}|x|X|\\*`);
createToken('XRANGEIDENTIFIER', `${src[t.NUMERICIDENTIFIER]}|x|X|\\*`);

createToken('XRANGEPLAIN', `[v=\\s]*(${src[t.XRANGEIDENTIFIER]})` +
                   `(?:\\.(${src[t.XRANGEIDENTIFIER]})` +
                   `(?:\\.(${src[t.XRANGEIDENTIFIER]})` +
                   `(?:${src[t.PRERELEASE]})?${
                     src[t.BUILD]}?` +
                   `)?)?`);

createToken('XRANGEPLAINLOOSE', `[v=\\s]*(${src[t.XRANGEIDENTIFIERLOOSE]})` +
                        `(?:\\.(${src[t.XRANGEIDENTIFIERLOOSE]})` +
                        `(?:\\.(${src[t.XRANGEIDENTIFIERLOOSE]})` +
                        `(?:${src[t.PRERELEASELOOSE]})?${
                          src[t.BUILD]}?` +
                        `)?)?`);

createToken('XRANGE', `^${src[t.GTLT]}\\s*${src[t.XRANGEPLAIN]}$`);
createToken('XRANGELOOSE', `^${src[t.GTLT]}\\s*${src[t.XRANGEPLAINLOOSE]}$`);

// Coercion.
// Extract anything that could conceivably be a part of a valid semver
createToken('COERCE', `${'(^|[^\\d])' +
              '(\\d{1,'}${MAX_SAFE_COMPONENT_LENGTH}})` +
              `(?:\\.(\\d{1,${MAX_SAFE_COMPONENT_LENGTH}}))?` +
              `(?:\\.(\\d{1,${MAX_SAFE_COMPONENT_LENGTH}}))?` +
              `(?:$|[^\\d])`);
createToken('COERCERTL', src[t.COERCE], true);

// Tilde ranges.
// Meaning is "reasonably at or greater than"
createToken('LONETILDE', '(?:~>?)');

createToken('TILDETRIM', `(\\s*)${src[t.LONETILDE]}\\s+`, true);
exports.tildeTrimReplace = '$1~';

createToken('TILDE', `^${src[t.LONETILDE]}${src[t.XRANGEPLAIN]}$`);
createToken('TILDELOOSE', `^${src[t.LONETILDE]}${src[t.XRANGEPLAINLOOSE]}$`);

// Caret ranges.
// Meaning is "at least and backwards compatible with"
createToken('LONECARET', '(?:\\^)');

createToken('CARETTRIM', `(\\s*)${src[t.LONECARET]}\\s+`, true);
exports.caretTrimReplace = '$1^';

createToken('CARET', `^${src[t.LONECARET]}${src[t.XRANGEPLAIN]}$`);
createToken('CARETLOOSE', `^${src[t.LONECARET]}${src[t.XRANGEPLAINLOOSE]}$`);

// A simple gt/lt/eq thing, or just "" to indicate "any version"
createToken('COMPARATORLOOSE', `^${src[t.GTLT]}\\s*(${src[t.LOOSEPLAIN]})$|^$`);
createToken('COMPARATOR', `^${src[t.GTLT]}\\s*(${src[t.FULLPLAIN]})$|^$`);

// An expression to strip any whitespace between the gtlt and the thing
// it modifies, so that `> 1.2.3` ==> `>1.2.3`
createToken('COMPARATORTRIM', `(\\s*)${src[t.GTLT]
}\\s*(${src[t.LOOSEPLAIN]}|${src[t.XRANGEPLAIN]})`, true);
exports.comparatorTrimReplace = '$1$2$3';

// Something like `1.2.3 - 1.2.4`
// Note that these all use the loose form, because they'll be
// checked against either the strict or loose comparator form
// later.
createToken('HYPHENRANGE', `^\\s*(${src[t.XRANGEPLAIN]})` +
                   `\\s+-\\s+` +
                   `(${src[t.XRANGEPLAIN]})` +
                   `\\s*$`);

createToken('HYPHENRANGELOOSE', `^\\s*(${src[t.XRANGEPLAINLOOSE]})` +
                        `\\s+-\\s+` +
                        `(${src[t.XRANGEPLAINLOOSE]})` +
                        `\\s*$`);

// Star ranges basically just allow anything at all.
createToken('STAR', '(<|>)?=?\\s*\\*');
// >=0.0.0 is like a star
createToken('GTE0', '^\\s*>=\\s*0\.0\.0\\s*$');
createToken('GTE0PRE', '^\\s*>=\\s*0\.0\.0-0\\s*$');
});

// parse out just the options we care about so we always get a consistent
// obj with keys in a consistent order.
const opts$1 = ['includePrerelease', 'loose', 'rtl'];
const parseOptions$1 = options =>
  !options ? {}
  : typeof options !== 'object' ? { loose: true }
  : opts$1.filter(k => options[k]).reduce((options, k) => {
    options[k] = true;
    return options
  }, {});
var parseOptions_1$1 = parseOptions$1;

const numeric$1 = /^[0-9]+$/;
const compareIdentifiers$2 = (a, b) => {
  const anum = numeric$1.test(a);
  const bnum = numeric$1.test(b);

  if (anum && bnum) {
    a = +a;
    b = +b;
  }

  return a === b ? 0
    : (anum && !bnum) ? -1
    : (bnum && !anum) ? 1
    : a < b ? -1
    : 1
};

const rcompareIdentifiers$1 = (a, b) => compareIdentifiers$2(b, a);

var identifiers$1 = {
  compareIdentifiers: compareIdentifiers$2,
  rcompareIdentifiers: rcompareIdentifiers$1
};

const { MAX_LENGTH: MAX_LENGTH$1$1, MAX_SAFE_INTEGER: MAX_SAFE_INTEGER$1$1 } = constants$1;
const { re: re$5, t: t$5 } = re_1$1;


const { compareIdentifiers: compareIdentifiers$1$1 } = identifiers$1;
class SemVer$1 {
  constructor (version, options) {
    options = parseOptions_1$1(options);

    if (version instanceof SemVer$1) {
      if (version.loose === !!options.loose &&
          version.includePrerelease === !!options.includePrerelease) {
        return version
      } else {
        version = version.version;
      }
    } else if (typeof version !== 'string') {
      throw new TypeError(`Invalid Version: ${version}`)
    }

    if (version.length > MAX_LENGTH$1$1) {
      throw new TypeError(
        `version is longer than ${MAX_LENGTH$1$1} characters`
      )
    }

    debug_1$1('SemVer', version, options);
    this.options = options;
    this.loose = !!options.loose;
    // this isn't actually relevant for versions, but keep it so that we
    // don't run into trouble passing this.options around.
    this.includePrerelease = !!options.includePrerelease;

    const m = version.trim().match(options.loose ? re$5[t$5.LOOSE] : re$5[t$5.FULL]);

    if (!m) {
      throw new TypeError(`Invalid Version: ${version}`)
    }

    this.raw = version;

    // these are actually numbers
    this.major = +m[1];
    this.minor = +m[2];
    this.patch = +m[3];

    if (this.major > MAX_SAFE_INTEGER$1$1 || this.major < 0) {
      throw new TypeError('Invalid major version')
    }

    if (this.minor > MAX_SAFE_INTEGER$1$1 || this.minor < 0) {
      throw new TypeError('Invalid minor version')
    }

    if (this.patch > MAX_SAFE_INTEGER$1$1 || this.patch < 0) {
      throw new TypeError('Invalid patch version')
    }

    // numberify any prerelease numeric ids
    if (!m[4]) {
      this.prerelease = [];
    } else {
      this.prerelease = m[4].split('.').map((id) => {
        if (/^[0-9]+$/.test(id)) {
          const num = +id;
          if (num >= 0 && num < MAX_SAFE_INTEGER$1$1) {
            return num
          }
        }
        return id
      });
    }

    this.build = m[5] ? m[5].split('.') : [];
    this.format();
  }

  format () {
    this.version = `${this.major}.${this.minor}.${this.patch}`;
    if (this.prerelease.length) {
      this.version += `-${this.prerelease.join('.')}`;
    }
    return this.version
  }

  toString () {
    return this.version
  }

  compare (other) {
    debug_1$1('SemVer.compare', this.version, this.options, other);
    if (!(other instanceof SemVer$1)) {
      if (typeof other === 'string' && other === this.version) {
        return 0
      }
      other = new SemVer$1(other, this.options);
    }

    if (other.version === this.version) {
      return 0
    }

    return this.compareMain(other) || this.comparePre(other)
  }

  compareMain (other) {
    if (!(other instanceof SemVer$1)) {
      other = new SemVer$1(other, this.options);
    }

    return (
      compareIdentifiers$1$1(this.major, other.major) ||
      compareIdentifiers$1$1(this.minor, other.minor) ||
      compareIdentifiers$1$1(this.patch, other.patch)
    )
  }

  comparePre (other) {
    if (!(other instanceof SemVer$1)) {
      other = new SemVer$1(other, this.options);
    }

    // NOT having a prerelease is > having one
    if (this.prerelease.length && !other.prerelease.length) {
      return -1
    } else if (!this.prerelease.length && other.prerelease.length) {
      return 1
    } else if (!this.prerelease.length && !other.prerelease.length) {
      return 0
    }

    let i = 0;
    do {
      const a = this.prerelease[i];
      const b = other.prerelease[i];
      debug_1$1('prerelease compare', i, a, b);
      if (a === undefined && b === undefined) {
        return 0
      } else if (b === undefined) {
        return 1
      } else if (a === undefined) {
        return -1
      } else if (a === b) {
        continue
      } else {
        return compareIdentifiers$1$1(a, b)
      }
    } while (++i)
  }

  compareBuild (other) {
    if (!(other instanceof SemVer$1)) {
      other = new SemVer$1(other, this.options);
    }

    let i = 0;
    do {
      const a = this.build[i];
      const b = other.build[i];
      debug_1$1('prerelease compare', i, a, b);
      if (a === undefined && b === undefined) {
        return 0
      } else if (b === undefined) {
        return 1
      } else if (a === undefined) {
        return -1
      } else if (a === b) {
        continue
      } else {
        return compareIdentifiers$1$1(a, b)
      }
    } while (++i)
  }

  // preminor will bump the version up to the next minor release, and immediately
  // down to pre-release. premajor and prepatch work the same way.
  inc (release, identifier) {
    switch (release) {
      case 'premajor':
        this.prerelease.length = 0;
        this.patch = 0;
        this.minor = 0;
        this.major++;
        this.inc('pre', identifier);
        break
      case 'preminor':
        this.prerelease.length = 0;
        this.patch = 0;
        this.minor++;
        this.inc('pre', identifier);
        break
      case 'prepatch':
        // If this is already a prerelease, it will bump to the next version
        // drop any prereleases that might already exist, since they are not
        // relevant at this point.
        this.prerelease.length = 0;
        this.inc('patch', identifier);
        this.inc('pre', identifier);
        break
      // If the input is a non-prerelease version, this acts the same as
      // prepatch.
      case 'prerelease':
        if (this.prerelease.length === 0) {
          this.inc('patch', identifier);
        }
        this.inc('pre', identifier);
        break

      case 'major':
        // If this is a pre-major version, bump up to the same major version.
        // Otherwise increment major.
        // 1.0.0-5 bumps to 1.0.0
        // 1.1.0 bumps to 2.0.0
        if (
          this.minor !== 0 ||
          this.patch !== 0 ||
          this.prerelease.length === 0
        ) {
          this.major++;
        }
        this.minor = 0;
        this.patch = 0;
        this.prerelease = [];
        break
      case 'minor':
        // If this is a pre-minor version, bump up to the same minor version.
        // Otherwise increment minor.
        // 1.2.0-5 bumps to 1.2.0
        // 1.2.1 bumps to 1.3.0
        if (this.patch !== 0 || this.prerelease.length === 0) {
          this.minor++;
        }
        this.patch = 0;
        this.prerelease = [];
        break
      case 'patch':
        // If this is not a pre-release version, it will increment the patch.
        // If it is a pre-release it will bump up to the same patch version.
        // 1.2.0-5 patches to 1.2.0
        // 1.2.0 patches to 1.2.1
        if (this.prerelease.length === 0) {
          this.patch++;
        }
        this.prerelease = [];
        break
      // This probably shouldn't be used publicly.
      // 1.0.0 'pre' would become 1.0.0-0 which is the wrong direction.
      case 'pre':
        if (this.prerelease.length === 0) {
          this.prerelease = [0];
        } else {
          let i = this.prerelease.length;
          while (--i >= 0) {
            if (typeof this.prerelease[i] === 'number') {
              this.prerelease[i]++;
              i = -2;
            }
          }
          if (i === -1) {
            // didn't increment anything
            this.prerelease.push(0);
          }
        }
        if (identifier) {
          // 1.2.0-beta.1 bumps to 1.2.0-beta.2,
          // 1.2.0-beta.fooblz or 1.2.0-beta bumps to 1.2.0-beta.0
          if (this.prerelease[0] === identifier) {
            if (isNaN(this.prerelease[1])) {
              this.prerelease = [identifier, 0];
            }
          } else {
            this.prerelease = [identifier, 0];
          }
        }
        break

      default:
        throw new Error(`invalid increment argument: ${release}`)
    }
    this.format();
    this.raw = this.version;
    return this
  }
}

var semver$2 = SemVer$1;

const {MAX_LENGTH: MAX_LENGTH$2$1} = constants$1;
const { re: re$1$1, t: t$1$1 } = re_1$1;



const parse$1 = (version, options) => {
  options = parseOptions_1$1(options);

  if (version instanceof semver$2) {
    return version
  }

  if (typeof version !== 'string') {
    return null
  }

  if (version.length > MAX_LENGTH$2$1) {
    return null
  }

  const r = options.loose ? re$1$1[t$1$1.LOOSE] : re$1$1[t$1$1.FULL];
  if (!r.test(version)) {
    return null
  }

  try {
    return new semver$2(version, options)
  } catch (er) {
    return null
  }
};

var parse_1$1 = parse$1;

const valid$2 = (version, options) => {
  const v = parse_1$1(version, options);
  return v ? v.version : null
};
var valid_1$1 = valid$2;

const clean$1 = (version, options) => {
  const s = parse_1$1(version.trim().replace(/^[=v]+/, ''), options);
  return s ? s.version : null
};
var clean_1$1 = clean$1;

const inc$1 = (version, release, options, identifier) => {
  if (typeof (options) === 'string') {
    identifier = options;
    options = undefined;
  }

  try {
    return new semver$2(version, options).inc(release, identifier).version
  } catch (er) {
    return null
  }
};
var inc_1$1 = inc$1;

const compare$1 = (a, b, loose) =>
  new semver$2(a, loose).compare(new semver$2(b, loose));

var compare_1$1 = compare$1;

const eq$1 = (a, b, loose) => compare_1$1(a, b, loose) === 0;
var eq_1$1 = eq$1;

const diff$1 = (version1, version2) => {
  if (eq_1$1(version1, version2)) {
    return null
  } else {
    const v1 = parse_1$1(version1);
    const v2 = parse_1$1(version2);
    const hasPre = v1.prerelease.length || v2.prerelease.length;
    const prefix = hasPre ? 'pre' : '';
    const defaultResult = hasPre ? 'prerelease' : '';
    for (const key in v1) {
      if (key === 'major' || key === 'minor' || key === 'patch') {
        if (v1[key] !== v2[key]) {
          return prefix + key
        }
      }
    }
    return defaultResult // may be undefined
  }
};
var diff_1$1 = diff$1;

const major$1 = (a, loose) => new semver$2(a, loose).major;
var major_1$1 = major$1;

const minor$1 = (a, loose) => new semver$2(a, loose).minor;
var minor_1$1 = minor$1;

const patch$1 = (a, loose) => new semver$2(a, loose).patch;
var patch_1$1 = patch$1;

const prerelease$1 = (version, options) => {
  const parsed = parse_1$1(version, options);
  return (parsed && parsed.prerelease.length) ? parsed.prerelease : null
};
var prerelease_1$1 = prerelease$1;

const rcompare$1 = (a, b, loose) => compare_1$1(b, a, loose);
var rcompare_1$1 = rcompare$1;

const compareLoose$1 = (a, b) => compare_1$1(a, b, true);
var compareLoose_1$1 = compareLoose$1;

const compareBuild$1 = (a, b, loose) => {
  const versionA = new semver$2(a, loose);
  const versionB = new semver$2(b, loose);
  return versionA.compare(versionB) || versionA.compareBuild(versionB)
};
var compareBuild_1$1 = compareBuild$1;

const sort$1 = (list, loose) => list.sort((a, b) => compareBuild_1$1(a, b, loose));
var sort_1$1 = sort$1;

const rsort$1 = (list, loose) => list.sort((a, b) => compareBuild_1$1(b, a, loose));
var rsort_1$1 = rsort$1;

const gt$1 = (a, b, loose) => compare_1$1(a, b, loose) > 0;
var gt_1$1 = gt$1;

const lt$1 = (a, b, loose) => compare_1$1(a, b, loose) < 0;
var lt_1$1 = lt$1;

const neq$1 = (a, b, loose) => compare_1$1(a, b, loose) !== 0;
var neq_1$1 = neq$1;

const gte$1 = (a, b, loose) => compare_1$1(a, b, loose) >= 0;
var gte_1$1 = gte$1;

const lte$1 = (a, b, loose) => compare_1$1(a, b, loose) <= 0;
var lte_1$1 = lte$1;

const cmp$1 = (a, op, b, loose) => {
  switch (op) {
    case '===':
      if (typeof a === 'object')
        a = a.version;
      if (typeof b === 'object')
        b = b.version;
      return a === b

    case '!==':
      if (typeof a === 'object')
        a = a.version;
      if (typeof b === 'object')
        b = b.version;
      return a !== b

    case '':
    case '=':
    case '==':
      return eq_1$1(a, b, loose)

    case '!=':
      return neq_1$1(a, b, loose)

    case '>':
      return gt_1$1(a, b, loose)

    case '>=':
      return gte_1$1(a, b, loose)

    case '<':
      return lt_1$1(a, b, loose)

    case '<=':
      return lte_1$1(a, b, loose)

    default:
      throw new TypeError(`Invalid operator: ${op}`)
  }
};
var cmp_1$1 = cmp$1;

const {re: re$2$1, t: t$2$1} = re_1$1;

const coerce$1 = (version, options) => {
  if (version instanceof semver$2) {
    return version
  }

  if (typeof version === 'number') {
    version = String(version);
  }

  if (typeof version !== 'string') {
    return null
  }

  options = options || {};

  let match = null;
  if (!options.rtl) {
    match = version.match(re$2$1[t$2$1.COERCE]);
  } else {
    // Find the right-most coercible string that does not share
    // a terminus with a more left-ward coercible string.
    // Eg, '1.2.3.4' wants to coerce '2.3.4', not '3.4' or '4'
    //
    // Walk through the string checking with a /g regexp
    // Manually set the index so as to pick up overlapping matches.
    // Stop when we get a match that ends at the string end, since no
    // coercible string can be more right-ward without the same terminus.
    let next;
    while ((next = re$2$1[t$2$1.COERCERTL].exec(version)) &&
        (!match || match.index + match[0].length !== version.length)
    ) {
      if (!match ||
            next.index + next[0].length !== match.index + match[0].length) {
        match = next;
      }
      re$2$1[t$2$1.COERCERTL].lastIndex = next.index + next[1].length + next[2].length;
    }
    // leave it in a clean state
    re$2$1[t$2$1.COERCERTL].lastIndex = -1;
  }

  if (match === null)
    return null

  return parse_1$1(`${match[2]}.${match[3] || '0'}.${match[4] || '0'}`, options)
};
var coerce_1$1 = coerce$1;

var iterator$1 = function (Yallist) {
  Yallist.prototype[Symbol.iterator] = function* () {
    for (let walker = this.head; walker; walker = walker.next) {
      yield walker.value;
    }
  };
};

var yallist$1 = Yallist$1;

Yallist$1.Node = Node$1;
Yallist$1.create = Yallist$1;

function Yallist$1 (list) {
  var self = this;
  if (!(self instanceof Yallist$1)) {
    self = new Yallist$1();
  }

  self.tail = null;
  self.head = null;
  self.length = 0;

  if (list && typeof list.forEach === 'function') {
    list.forEach(function (item) {
      self.push(item);
    });
  } else if (arguments.length > 0) {
    for (var i = 0, l = arguments.length; i < l; i++) {
      self.push(arguments[i]);
    }
  }

  return self
}

Yallist$1.prototype.removeNode = function (node) {
  if (node.list !== this) {
    throw new Error('removing node which does not belong to this list')
  }

  var next = node.next;
  var prev = node.prev;

  if (next) {
    next.prev = prev;
  }

  if (prev) {
    prev.next = next;
  }

  if (node === this.head) {
    this.head = next;
  }
  if (node === this.tail) {
    this.tail = prev;
  }

  node.list.length--;
  node.next = null;
  node.prev = null;
  node.list = null;

  return next
};

Yallist$1.prototype.unshiftNode = function (node) {
  if (node === this.head) {
    return
  }

  if (node.list) {
    node.list.removeNode(node);
  }

  var head = this.head;
  node.list = this;
  node.next = head;
  if (head) {
    head.prev = node;
  }

  this.head = node;
  if (!this.tail) {
    this.tail = node;
  }
  this.length++;
};

Yallist$1.prototype.pushNode = function (node) {
  if (node === this.tail) {
    return
  }

  if (node.list) {
    node.list.removeNode(node);
  }

  var tail = this.tail;
  node.list = this;
  node.prev = tail;
  if (tail) {
    tail.next = node;
  }

  this.tail = node;
  if (!this.head) {
    this.head = node;
  }
  this.length++;
};

Yallist$1.prototype.push = function () {
  for (var i = 0, l = arguments.length; i < l; i++) {
    push$1(this, arguments[i]);
  }
  return this.length
};

Yallist$1.prototype.unshift = function () {
  for (var i = 0, l = arguments.length; i < l; i++) {
    unshift$1(this, arguments[i]);
  }
  return this.length
};

Yallist$1.prototype.pop = function () {
  if (!this.tail) {
    return undefined
  }

  var res = this.tail.value;
  this.tail = this.tail.prev;
  if (this.tail) {
    this.tail.next = null;
  } else {
    this.head = null;
  }
  this.length--;
  return res
};

Yallist$1.prototype.shift = function () {
  if (!this.head) {
    return undefined
  }

  var res = this.head.value;
  this.head = this.head.next;
  if (this.head) {
    this.head.prev = null;
  } else {
    this.tail = null;
  }
  this.length--;
  return res
};

Yallist$1.prototype.forEach = function (fn, thisp) {
  thisp = thisp || this;
  for (var walker = this.head, i = 0; walker !== null; i++) {
    fn.call(thisp, walker.value, i, this);
    walker = walker.next;
  }
};

Yallist$1.prototype.forEachReverse = function (fn, thisp) {
  thisp = thisp || this;
  for (var walker = this.tail, i = this.length - 1; walker !== null; i--) {
    fn.call(thisp, walker.value, i, this);
    walker = walker.prev;
  }
};

Yallist$1.prototype.get = function (n) {
  for (var i = 0, walker = this.head; walker !== null && i < n; i++) {
    // abort out of the list early if we hit a cycle
    walker = walker.next;
  }
  if (i === n && walker !== null) {
    return walker.value
  }
};

Yallist$1.prototype.getReverse = function (n) {
  for (var i = 0, walker = this.tail; walker !== null && i < n; i++) {
    // abort out of the list early if we hit a cycle
    walker = walker.prev;
  }
  if (i === n && walker !== null) {
    return walker.value
  }
};

Yallist$1.prototype.map = function (fn, thisp) {
  thisp = thisp || this;
  var res = new Yallist$1();
  for (var walker = this.head; walker !== null;) {
    res.push(fn.call(thisp, walker.value, this));
    walker = walker.next;
  }
  return res
};

Yallist$1.prototype.mapReverse = function (fn, thisp) {
  thisp = thisp || this;
  var res = new Yallist$1();
  for (var walker = this.tail; walker !== null;) {
    res.push(fn.call(thisp, walker.value, this));
    walker = walker.prev;
  }
  return res
};

Yallist$1.prototype.reduce = function (fn, initial) {
  var acc;
  var walker = this.head;
  if (arguments.length > 1) {
    acc = initial;
  } else if (this.head) {
    walker = this.head.next;
    acc = this.head.value;
  } else {
    throw new TypeError('Reduce of empty list with no initial value')
  }

  for (var i = 0; walker !== null; i++) {
    acc = fn(acc, walker.value, i);
    walker = walker.next;
  }

  return acc
};

Yallist$1.prototype.reduceReverse = function (fn, initial) {
  var acc;
  var walker = this.tail;
  if (arguments.length > 1) {
    acc = initial;
  } else if (this.tail) {
    walker = this.tail.prev;
    acc = this.tail.value;
  } else {
    throw new TypeError('Reduce of empty list with no initial value')
  }

  for (var i = this.length - 1; walker !== null; i--) {
    acc = fn(acc, walker.value, i);
    walker = walker.prev;
  }

  return acc
};

Yallist$1.prototype.toArray = function () {
  var arr = new Array(this.length);
  for (var i = 0, walker = this.head; walker !== null; i++) {
    arr[i] = walker.value;
    walker = walker.next;
  }
  return arr
};

Yallist$1.prototype.toArrayReverse = function () {
  var arr = new Array(this.length);
  for (var i = 0, walker = this.tail; walker !== null; i++) {
    arr[i] = walker.value;
    walker = walker.prev;
  }
  return arr
};

Yallist$1.prototype.slice = function (from, to) {
  to = to || this.length;
  if (to < 0) {
    to += this.length;
  }
  from = from || 0;
  if (from < 0) {
    from += this.length;
  }
  var ret = new Yallist$1();
  if (to < from || to < 0) {
    return ret
  }
  if (from < 0) {
    from = 0;
  }
  if (to > this.length) {
    to = this.length;
  }
  for (var i = 0, walker = this.head; walker !== null && i < from; i++) {
    walker = walker.next;
  }
  for (; walker !== null && i < to; i++, walker = walker.next) {
    ret.push(walker.value);
  }
  return ret
};

Yallist$1.prototype.sliceReverse = function (from, to) {
  to = to || this.length;
  if (to < 0) {
    to += this.length;
  }
  from = from || 0;
  if (from < 0) {
    from += this.length;
  }
  var ret = new Yallist$1();
  if (to < from || to < 0) {
    return ret
  }
  if (from < 0) {
    from = 0;
  }
  if (to > this.length) {
    to = this.length;
  }
  for (var i = this.length, walker = this.tail; walker !== null && i > to; i--) {
    walker = walker.prev;
  }
  for (; walker !== null && i > from; i--, walker = walker.prev) {
    ret.push(walker.value);
  }
  return ret
};

Yallist$1.prototype.splice = function (start, deleteCount, ...nodes) {
  if (start > this.length) {
    start = this.length - 1;
  }
  if (start < 0) {
    start = this.length + start;
  }

  for (var i = 0, walker = this.head; walker !== null && i < start; i++) {
    walker = walker.next;
  }

  var ret = [];
  for (var i = 0; walker && i < deleteCount; i++) {
    ret.push(walker.value);
    walker = this.removeNode(walker);
  }
  if (walker === null) {
    walker = this.tail;
  }

  if (walker !== this.head && walker !== this.tail) {
    walker = walker.prev;
  }

  for (var i = 0; i < nodes.length; i++) {
    walker = insert$1(this, walker, nodes[i]);
  }
  return ret;
};

Yallist$1.prototype.reverse = function () {
  var head = this.head;
  var tail = this.tail;
  for (var walker = head; walker !== null; walker = walker.prev) {
    var p = walker.prev;
    walker.prev = walker.next;
    walker.next = p;
  }
  this.head = tail;
  this.tail = head;
  return this
};

function insert$1 (self, node, value) {
  var inserted = node === self.head ?
    new Node$1(value, null, node, self) :
    new Node$1(value, node, node.next, self);

  if (inserted.next === null) {
    self.tail = inserted;
  }
  if (inserted.prev === null) {
    self.head = inserted;
  }

  self.length++;

  return inserted
}

function push$1 (self, item) {
  self.tail = new Node$1(item, self.tail, null, self);
  if (!self.head) {
    self.head = self.tail;
  }
  self.length++;
}

function unshift$1 (self, item) {
  self.head = new Node$1(item, null, self.head, self);
  if (!self.tail) {
    self.tail = self.head;
  }
  self.length++;
}

function Node$1 (value, prev, next, list) {
  if (!(this instanceof Node$1)) {
    return new Node$1(value, prev, next, list)
  }

  this.list = list;
  this.value = value;

  if (prev) {
    prev.next = this;
    this.prev = prev;
  } else {
    this.prev = null;
  }

  if (next) {
    next.prev = this;
    this.next = next;
  } else {
    this.next = null;
  }
}

try {
  // add if support for Symbol.iterator is present
  iterator$1(Yallist$1);
} catch (er) {}

// A linked list to keep track of recently-used-ness


const MAX$1 = Symbol('max');
const LENGTH$1 = Symbol('length');
const LENGTH_CALCULATOR$1 = Symbol('lengthCalculator');
const ALLOW_STALE$1 = Symbol('allowStale');
const MAX_AGE$1 = Symbol('maxAge');
const DISPOSE$1 = Symbol('dispose');
const NO_DISPOSE_ON_SET$1 = Symbol('noDisposeOnSet');
const LRU_LIST$1 = Symbol('lruList');
const CACHE$1 = Symbol('cache');
const UPDATE_AGE_ON_GET$1 = Symbol('updateAgeOnGet');

const naiveLength$1 = () => 1;

// lruList is a yallist where the head is the youngest
// item, and the tail is the oldest.  the list contains the Hit
// objects as the entries.
// Each Hit object has a reference to its Yallist.Node.  This
// never changes.
//
// cache is a Map (or PseudoMap) that matches the keys to
// the Yallist.Node object.
class LRUCache$1 {
  constructor (options) {
    if (typeof options === 'number')
      options = { max: options };

    if (!options)
      options = {};

    if (options.max && (typeof options.max !== 'number' || options.max < 0))
      throw new TypeError('max must be a non-negative number')
    // Kind of weird to have a default max of Infinity, but oh well.
    const max = this[MAX$1] = options.max || Infinity;

    const lc = options.length || naiveLength$1;
    this[LENGTH_CALCULATOR$1] = (typeof lc !== 'function') ? naiveLength$1 : lc;
    this[ALLOW_STALE$1] = options.stale || false;
    if (options.maxAge && typeof options.maxAge !== 'number')
      throw new TypeError('maxAge must be a number')
    this[MAX_AGE$1] = options.maxAge || 0;
    this[DISPOSE$1] = options.dispose;
    this[NO_DISPOSE_ON_SET$1] = options.noDisposeOnSet || false;
    this[UPDATE_AGE_ON_GET$1] = options.updateAgeOnGet || false;
    this.reset();
  }

  // resize the cache when the max changes.
  set max (mL) {
    if (typeof mL !== 'number' || mL < 0)
      throw new TypeError('max must be a non-negative number')

    this[MAX$1] = mL || Infinity;
    trim$1(this);
  }
  get max () {
    return this[MAX$1]
  }

  set allowStale (allowStale) {
    this[ALLOW_STALE$1] = !!allowStale;
  }
  get allowStale () {
    return this[ALLOW_STALE$1]
  }

  set maxAge (mA) {
    if (typeof mA !== 'number')
      throw new TypeError('maxAge must be a non-negative number')

    this[MAX_AGE$1] = mA;
    trim$1(this);
  }
  get maxAge () {
    return this[MAX_AGE$1]
  }

  // resize the cache when the lengthCalculator changes.
  set lengthCalculator (lC) {
    if (typeof lC !== 'function')
      lC = naiveLength$1;

    if (lC !== this[LENGTH_CALCULATOR$1]) {
      this[LENGTH_CALCULATOR$1] = lC;
      this[LENGTH$1] = 0;
      this[LRU_LIST$1].forEach(hit => {
        hit.length = this[LENGTH_CALCULATOR$1](hit.value, hit.key);
        this[LENGTH$1] += hit.length;
      });
    }
    trim$1(this);
  }
  get lengthCalculator () { return this[LENGTH_CALCULATOR$1] }

  get length () { return this[LENGTH$1] }
  get itemCount () { return this[LRU_LIST$1].length }

  rforEach (fn, thisp) {
    thisp = thisp || this;
    for (let walker = this[LRU_LIST$1].tail; walker !== null;) {
      const prev = walker.prev;
      forEachStep$1(this, fn, walker, thisp);
      walker = prev;
    }
  }

  forEach (fn, thisp) {
    thisp = thisp || this;
    for (let walker = this[LRU_LIST$1].head; walker !== null;) {
      const next = walker.next;
      forEachStep$1(this, fn, walker, thisp);
      walker = next;
    }
  }

  keys () {
    return this[LRU_LIST$1].toArray().map(k => k.key)
  }

  values () {
    return this[LRU_LIST$1].toArray().map(k => k.value)
  }

  reset () {
    if (this[DISPOSE$1] &&
        this[LRU_LIST$1] &&
        this[LRU_LIST$1].length) {
      this[LRU_LIST$1].forEach(hit => this[DISPOSE$1](hit.key, hit.value));
    }

    this[CACHE$1] = new Map(); // hash of items by key
    this[LRU_LIST$1] = new yallist$1(); // list of items in order of use recency
    this[LENGTH$1] = 0; // length of items in the list
  }

  dump () {
    return this[LRU_LIST$1].map(hit =>
      isStale$1(this, hit) ? false : {
        k: hit.key,
        v: hit.value,
        e: hit.now + (hit.maxAge || 0)
      }).toArray().filter(h => h)
  }

  dumpLru () {
    return this[LRU_LIST$1]
  }

  set (key, value, maxAge) {
    maxAge = maxAge || this[MAX_AGE$1];

    if (maxAge && typeof maxAge !== 'number')
      throw new TypeError('maxAge must be a number')

    const now = maxAge ? Date.now() : 0;
    const len = this[LENGTH_CALCULATOR$1](value, key);

    if (this[CACHE$1].has(key)) {
      if (len > this[MAX$1]) {
        del$1(this, this[CACHE$1].get(key));
        return false
      }

      const node = this[CACHE$1].get(key);
      const item = node.value;

      // dispose of the old one before overwriting
      // split out into 2 ifs for better coverage tracking
      if (this[DISPOSE$1]) {
        if (!this[NO_DISPOSE_ON_SET$1])
          this[DISPOSE$1](key, item.value);
      }

      item.now = now;
      item.maxAge = maxAge;
      item.value = value;
      this[LENGTH$1] += len - item.length;
      item.length = len;
      this.get(key);
      trim$1(this);
      return true
    }

    const hit = new Entry$1(key, value, len, now, maxAge);

    // oversized objects fall out of cache automatically.
    if (hit.length > this[MAX$1]) {
      if (this[DISPOSE$1])
        this[DISPOSE$1](key, value);

      return false
    }

    this[LENGTH$1] += hit.length;
    this[LRU_LIST$1].unshift(hit);
    this[CACHE$1].set(key, this[LRU_LIST$1].head);
    trim$1(this);
    return true
  }

  has (key) {
    if (!this[CACHE$1].has(key)) return false
    const hit = this[CACHE$1].get(key).value;
    return !isStale$1(this, hit)
  }

  get (key) {
    return get$1(this, key, true)
  }

  peek (key) {
    return get$1(this, key, false)
  }

  pop () {
    const node = this[LRU_LIST$1].tail;
    if (!node)
      return null

    del$1(this, node);
    return node.value
  }

  del (key) {
    del$1(this, this[CACHE$1].get(key));
  }

  load (arr) {
    // reset the cache
    this.reset();

    const now = Date.now();
    // A previous serialized cache has the most recent items first
    for (let l = arr.length - 1; l >= 0; l--) {
      const hit = arr[l];
      const expiresAt = hit.e || 0;
      if (expiresAt === 0)
        // the item was created without expiration in a non aged cache
        this.set(hit.k, hit.v);
      else {
        const maxAge = expiresAt - now;
        // dont add already expired items
        if (maxAge > 0) {
          this.set(hit.k, hit.v, maxAge);
        }
      }
    }
  }

  prune () {
    this[CACHE$1].forEach((value, key) => get$1(this, key, false));
  }
}

const get$1 = (self, key, doUse) => {
  const node = self[CACHE$1].get(key);
  if (node) {
    const hit = node.value;
    if (isStale$1(self, hit)) {
      del$1(self, node);
      if (!self[ALLOW_STALE$1])
        return undefined
    } else {
      if (doUse) {
        if (self[UPDATE_AGE_ON_GET$1])
          node.value.now = Date.now();
        self[LRU_LIST$1].unshiftNode(node);
      }
    }
    return hit.value
  }
};

const isStale$1 = (self, hit) => {
  if (!hit || (!hit.maxAge && !self[MAX_AGE$1]))
    return false

  const diff = Date.now() - hit.now;
  return hit.maxAge ? diff > hit.maxAge
    : self[MAX_AGE$1] && (diff > self[MAX_AGE$1])
};

const trim$1 = self => {
  if (self[LENGTH$1] > self[MAX$1]) {
    for (let walker = self[LRU_LIST$1].tail;
      self[LENGTH$1] > self[MAX$1] && walker !== null;) {
      // We know that we're about to delete this one, and also
      // what the next least recently used key will be, so just
      // go ahead and set it now.
      const prev = walker.prev;
      del$1(self, walker);
      walker = prev;
    }
  }
};

const del$1 = (self, node) => {
  if (node) {
    const hit = node.value;
    if (self[DISPOSE$1])
      self[DISPOSE$1](hit.key, hit.value);

    self[LENGTH$1] -= hit.length;
    self[CACHE$1].delete(hit.key);
    self[LRU_LIST$1].removeNode(node);
  }
};

class Entry$1 {
  constructor (key, value, length, now, maxAge) {
    this.key = key;
    this.value = value;
    this.length = length;
    this.now = now;
    this.maxAge = maxAge || 0;
  }
}

const forEachStep$1 = (self, fn, node, thisp) => {
  let hit = node.value;
  if (isStale$1(self, hit)) {
    del$1(self, node);
    if (!self[ALLOW_STALE$1])
      hit = undefined;
  }
  if (hit)
    fn.call(thisp, hit.value, hit.key, self);
};

var lruCache$1 = LRUCache$1;

// hoisted class for cyclic dependency
class Range$1 {
  constructor (range, options) {
    options = parseOptions_1$1(options);

    if (range instanceof Range$1) {
      if (
        range.loose === !!options.loose &&
        range.includePrerelease === !!options.includePrerelease
      ) {
        return range
      } else {
        return new Range$1(range.raw, options)
      }
    }

    if (range instanceof comparator$1) {
      // just put it in the set and return
      this.raw = range.value;
      this.set = [[range]];
      this.format();
      return this
    }

    this.options = options;
    this.loose = !!options.loose;
    this.includePrerelease = !!options.includePrerelease;

    // First, split based on boolean or ||
    this.raw = range;
    this.set = range
      .split(/\s*\|\|\s*/)
      // map the range to a 2d array of comparators
      .map(range => this.parseRange(range.trim()))
      // throw out any comparator lists that are empty
      // this generally means that it was not a valid range, which is allowed
      // in loose mode, but will still throw if the WHOLE range is invalid.
      .filter(c => c.length);

    if (!this.set.length) {
      throw new TypeError(`Invalid SemVer Range: ${range}`)
    }

    // if we have any that are not the null set, throw out null sets.
    if (this.set.length > 1) {
      // keep the first one, in case they're all null sets
      const first = this.set[0];
      this.set = this.set.filter(c => !isNullSet$1(c[0]));
      if (this.set.length === 0)
        this.set = [first];
      else if (this.set.length > 1) {
        // if we have any that are *, then the range is just *
        for (const c of this.set) {
          if (c.length === 1 && isAny$1(c[0])) {
            this.set = [c];
            break
          }
        }
      }
    }

    this.format();
  }

  format () {
    this.range = this.set
      .map((comps) => {
        return comps.join(' ').trim()
      })
      .join('||')
      .trim();
    return this.range
  }

  toString () {
    return this.range
  }

  parseRange (range) {
    range = range.trim();

    // memoize range parsing for performance.
    // this is a very hot path, and fully deterministic.
    const memoOpts = Object.keys(this.options).join(',');
    const memoKey = `parseRange:${memoOpts}:${range}`;
    const cached = cache$1.get(memoKey);
    if (cached)
      return cached

    const loose = this.options.loose;
    // `1.2.3 - 1.2.4` => `>=1.2.3 <=1.2.4`
    const hr = loose ? re$3$1[t$3$1.HYPHENRANGELOOSE] : re$3$1[t$3$1.HYPHENRANGE];
    range = range.replace(hr, hyphenReplace$1(this.options.includePrerelease));
    debug_1$1('hyphen replace', range);
    // `> 1.2.3 < 1.2.5` => `>1.2.3 <1.2.5`
    range = range.replace(re$3$1[t$3$1.COMPARATORTRIM], comparatorTrimReplace$1);
    debug_1$1('comparator trim', range, re$3$1[t$3$1.COMPARATORTRIM]);

    // `~ 1.2.3` => `~1.2.3`
    range = range.replace(re$3$1[t$3$1.TILDETRIM], tildeTrimReplace$1);

    // `^ 1.2.3` => `^1.2.3`
    range = range.replace(re$3$1[t$3$1.CARETTRIM], caretTrimReplace$1);

    // normalize spaces
    range = range.split(/\s+/).join(' ');

    // At this point, the range is completely trimmed and
    // ready to be split into comparators.

    const compRe = loose ? re$3$1[t$3$1.COMPARATORLOOSE] : re$3$1[t$3$1.COMPARATOR];
    const rangeList = range
      .split(' ')
      .map(comp => parseComparator$1(comp, this.options))
      .join(' ')
      .split(/\s+/)
      // >=0.0.0 is equivalent to *
      .map(comp => replaceGTE0$1(comp, this.options))
      // in loose mode, throw out any that are not valid comparators
      .filter(this.options.loose ? comp => !!comp.match(compRe) : () => true)
      .map(comp => new comparator$1(comp, this.options));

    // if any comparators are the null set, then replace with JUST null set
    // if more than one comparator, remove any * comparators
    // also, don't include the same comparator more than once
    const l = rangeList.length;
    const rangeMap = new Map();
    for (const comp of rangeList) {
      if (isNullSet$1(comp))
        return [comp]
      rangeMap.set(comp.value, comp);
    }
    if (rangeMap.size > 1 && rangeMap.has(''))
      rangeMap.delete('');

    const result = [...rangeMap.values()];
    cache$1.set(memoKey, result);
    return result
  }

  intersects (range, options) {
    if (!(range instanceof Range$1)) {
      throw new TypeError('a Range is required')
    }

    return this.set.some((thisComparators) => {
      return (
        isSatisfiable$1(thisComparators, options) &&
        range.set.some((rangeComparators) => {
          return (
            isSatisfiable$1(rangeComparators, options) &&
            thisComparators.every((thisComparator) => {
              return rangeComparators.every((rangeComparator) => {
                return thisComparator.intersects(rangeComparator, options)
              })
            })
          )
        })
      )
    })
  }

  // if ANY of the sets match ALL of its comparators, then pass
  test (version) {
    if (!version) {
      return false
    }

    if (typeof version === 'string') {
      try {
        version = new semver$2(version, this.options);
      } catch (er) {
        return false
      }
    }

    for (let i = 0; i < this.set.length; i++) {
      if (testSet$1(this.set[i], version, this.options)) {
        return true
      }
    }
    return false
  }
}
var range$1 = Range$1;


const cache$1 = new lruCache$1({ max: 1000 });





const {
  re: re$3$1,
  t: t$3$1,
  comparatorTrimReplace: comparatorTrimReplace$1,
  tildeTrimReplace: tildeTrimReplace$1,
  caretTrimReplace: caretTrimReplace$1
} = re_1$1;

const isNullSet$1 = c => c.value === '<0.0.0-0';
const isAny$1 = c => c.value === '';

// take a set of comparators and determine whether there
// exists a version which can satisfy it
const isSatisfiable$1 = (comparators, options) => {
  let result = true;
  const remainingComparators = comparators.slice();
  let testComparator = remainingComparators.pop();

  while (result && remainingComparators.length) {
    result = remainingComparators.every((otherComparator) => {
      return testComparator.intersects(otherComparator, options)
    });

    testComparator = remainingComparators.pop();
  }

  return result
};

// comprised of xranges, tildes, stars, and gtlt's at this point.
// already replaced the hyphen ranges
// turn into a set of JUST comparators.
const parseComparator$1 = (comp, options) => {
  debug_1$1('comp', comp, options);
  comp = replaceCarets$1(comp, options);
  debug_1$1('caret', comp);
  comp = replaceTildes$1(comp, options);
  debug_1$1('tildes', comp);
  comp = replaceXRanges$1(comp, options);
  debug_1$1('xrange', comp);
  comp = replaceStars$1(comp, options);
  debug_1$1('stars', comp);
  return comp
};

const isX$1 = id => !id || id.toLowerCase() === 'x' || id === '*';

// ~, ~> --> * (any, kinda silly)
// ~2, ~2.x, ~2.x.x, ~>2, ~>2.x ~>2.x.x --> >=2.0.0 <3.0.0-0
// ~2.0, ~2.0.x, ~>2.0, ~>2.0.x --> >=2.0.0 <2.1.0-0
// ~1.2, ~1.2.x, ~>1.2, ~>1.2.x --> >=1.2.0 <1.3.0-0
// ~1.2.3, ~>1.2.3 --> >=1.2.3 <1.3.0-0
// ~1.2.0, ~>1.2.0 --> >=1.2.0 <1.3.0-0
const replaceTildes$1 = (comp, options) =>
  comp.trim().split(/\s+/).map((comp) => {
    return replaceTilde$1(comp, options)
  }).join(' ');

const replaceTilde$1 = (comp, options) => {
  const r = options.loose ? re$3$1[t$3$1.TILDELOOSE] : re$3$1[t$3$1.TILDE];
  return comp.replace(r, (_, M, m, p, pr) => {
    debug_1$1('tilde', comp, _, M, m, p, pr);
    let ret;

    if (isX$1(M)) {
      ret = '';
    } else if (isX$1(m)) {
      ret = `>=${M}.0.0 <${+M + 1}.0.0-0`;
    } else if (isX$1(p)) {
      // ~1.2 == >=1.2.0 <1.3.0-0
      ret = `>=${M}.${m}.0 <${M}.${+m + 1}.0-0`;
    } else if (pr) {
      debug_1$1('replaceTilde pr', pr);
      ret = `>=${M}.${m}.${p}-${pr
      } <${M}.${+m + 1}.0-0`;
    } else {
      // ~1.2.3 == >=1.2.3 <1.3.0-0
      ret = `>=${M}.${m}.${p
      } <${M}.${+m + 1}.0-0`;
    }

    debug_1$1('tilde return', ret);
    return ret
  })
};

// ^ --> * (any, kinda silly)
// ^2, ^2.x, ^2.x.x --> >=2.0.0 <3.0.0-0
// ^2.0, ^2.0.x --> >=2.0.0 <3.0.0-0
// ^1.2, ^1.2.x --> >=1.2.0 <2.0.0-0
// ^1.2.3 --> >=1.2.3 <2.0.0-0
// ^1.2.0 --> >=1.2.0 <2.0.0-0
const replaceCarets$1 = (comp, options) =>
  comp.trim().split(/\s+/).map((comp) => {
    return replaceCaret$1(comp, options)
  }).join(' ');

const replaceCaret$1 = (comp, options) => {
  debug_1$1('caret', comp, options);
  const r = options.loose ? re$3$1[t$3$1.CARETLOOSE] : re$3$1[t$3$1.CARET];
  const z = options.includePrerelease ? '-0' : '';
  return comp.replace(r, (_, M, m, p, pr) => {
    debug_1$1('caret', comp, _, M, m, p, pr);
    let ret;

    if (isX$1(M)) {
      ret = '';
    } else if (isX$1(m)) {
      ret = `>=${M}.0.0${z} <${+M + 1}.0.0-0`;
    } else if (isX$1(p)) {
      if (M === '0') {
        ret = `>=${M}.${m}.0${z} <${M}.${+m + 1}.0-0`;
      } else {
        ret = `>=${M}.${m}.0${z} <${+M + 1}.0.0-0`;
      }
    } else if (pr) {
      debug_1$1('replaceCaret pr', pr);
      if (M === '0') {
        if (m === '0') {
          ret = `>=${M}.${m}.${p}-${pr
          } <${M}.${m}.${+p + 1}-0`;
        } else {
          ret = `>=${M}.${m}.${p}-${pr
          } <${M}.${+m + 1}.0-0`;
        }
      } else {
        ret = `>=${M}.${m}.${p}-${pr
        } <${+M + 1}.0.0-0`;
      }
    } else {
      debug_1$1('no pr');
      if (M === '0') {
        if (m === '0') {
          ret = `>=${M}.${m}.${p
          }${z} <${M}.${m}.${+p + 1}-0`;
        } else {
          ret = `>=${M}.${m}.${p
          }${z} <${M}.${+m + 1}.0-0`;
        }
      } else {
        ret = `>=${M}.${m}.${p
        } <${+M + 1}.0.0-0`;
      }
    }

    debug_1$1('caret return', ret);
    return ret
  })
};

const replaceXRanges$1 = (comp, options) => {
  debug_1$1('replaceXRanges', comp, options);
  return comp.split(/\s+/).map((comp) => {
    return replaceXRange$1(comp, options)
  }).join(' ')
};

const replaceXRange$1 = (comp, options) => {
  comp = comp.trim();
  const r = options.loose ? re$3$1[t$3$1.XRANGELOOSE] : re$3$1[t$3$1.XRANGE];
  return comp.replace(r, (ret, gtlt, M, m, p, pr) => {
    debug_1$1('xRange', comp, ret, gtlt, M, m, p, pr);
    const xM = isX$1(M);
    const xm = xM || isX$1(m);
    const xp = xm || isX$1(p);
    const anyX = xp;

    if (gtlt === '=' && anyX) {
      gtlt = '';
    }

    // if we're including prereleases in the match, then we need
    // to fix this to -0, the lowest possible prerelease value
    pr = options.includePrerelease ? '-0' : '';

    if (xM) {
      if (gtlt === '>' || gtlt === '<') {
        // nothing is allowed
        ret = '<0.0.0-0';
      } else {
        // nothing is forbidden
        ret = '*';
      }
    } else if (gtlt && anyX) {
      // we know patch is an x, because we have any x at all.
      // replace X with 0
      if (xm) {
        m = 0;
      }
      p = 0;

      if (gtlt === '>') {
        // >1 => >=2.0.0
        // >1.2 => >=1.3.0
        gtlt = '>=';
        if (xm) {
          M = +M + 1;
          m = 0;
          p = 0;
        } else {
          m = +m + 1;
          p = 0;
        }
      } else if (gtlt === '<=') {
        // <=0.7.x is actually <0.8.0, since any 0.7.x should
        // pass.  Similarly, <=7.x is actually <8.0.0, etc.
        gtlt = '<';
        if (xm) {
          M = +M + 1;
        } else {
          m = +m + 1;
        }
      }

      if (gtlt === '<')
        pr = '-0';

      ret = `${gtlt + M}.${m}.${p}${pr}`;
    } else if (xm) {
      ret = `>=${M}.0.0${pr} <${+M + 1}.0.0-0`;
    } else if (xp) {
      ret = `>=${M}.${m}.0${pr
      } <${M}.${+m + 1}.0-0`;
    }

    debug_1$1('xRange return', ret);

    return ret
  })
};

// Because * is AND-ed with everything else in the comparator,
// and '' means "any version", just remove the *s entirely.
const replaceStars$1 = (comp, options) => {
  debug_1$1('replaceStars', comp, options);
  // Looseness is ignored here.  star is always as loose as it gets!
  return comp.trim().replace(re$3$1[t$3$1.STAR], '')
};

const replaceGTE0$1 = (comp, options) => {
  debug_1$1('replaceGTE0', comp, options);
  return comp.trim()
    .replace(re$3$1[options.includePrerelease ? t$3$1.GTE0PRE : t$3$1.GTE0], '')
};

// This function is passed to string.replace(re[t.HYPHENRANGE])
// M, m, patch, prerelease, build
// 1.2 - 3.4.5 => >=1.2.0 <=3.4.5
// 1.2.3 - 3.4 => >=1.2.0 <3.5.0-0 Any 3.4.x will do
// 1.2 - 3.4 => >=1.2.0 <3.5.0-0
const hyphenReplace$1 = incPr => ($0,
  from, fM, fm, fp, fpr, fb,
  to, tM, tm, tp, tpr, tb) => {
  if (isX$1(fM)) {
    from = '';
  } else if (isX$1(fm)) {
    from = `>=${fM}.0.0${incPr ? '-0' : ''}`;
  } else if (isX$1(fp)) {
    from = `>=${fM}.${fm}.0${incPr ? '-0' : ''}`;
  } else if (fpr) {
    from = `>=${from}`;
  } else {
    from = `>=${from}${incPr ? '-0' : ''}`;
  }

  if (isX$1(tM)) {
    to = '';
  } else if (isX$1(tm)) {
    to = `<${+tM + 1}.0.0-0`;
  } else if (isX$1(tp)) {
    to = `<${tM}.${+tm + 1}.0-0`;
  } else if (tpr) {
    to = `<=${tM}.${tm}.${tp}-${tpr}`;
  } else if (incPr) {
    to = `<${tM}.${tm}.${+tp + 1}-0`;
  } else {
    to = `<=${to}`;
  }

  return (`${from} ${to}`).trim()
};

const testSet$1 = (set, version, options) => {
  for (let i = 0; i < set.length; i++) {
    if (!set[i].test(version)) {
      return false
    }
  }

  if (version.prerelease.length && !options.includePrerelease) {
    // Find the set of versions that are allowed to have prereleases
    // For example, ^1.2.3-pr.1 desugars to >=1.2.3-pr.1 <2.0.0
    // That should allow `1.2.3-pr.2` to pass.
    // However, `1.2.4-alpha.notready` should NOT be allowed,
    // even though it's within the range set by the comparators.
    for (let i = 0; i < set.length; i++) {
      debug_1$1(set[i].semver);
      if (set[i].semver === comparator$1.ANY) {
        continue
      }

      if (set[i].semver.prerelease.length > 0) {
        const allowed = set[i].semver;
        if (allowed.major === version.major &&
            allowed.minor === version.minor &&
            allowed.patch === version.patch) {
          return true
        }
      }
    }

    // Version has a -pre, but it's not one of the ones we like.
    return false
  }

  return true
};

const ANY$3 = Symbol('SemVer ANY');
// hoisted class for cyclic dependency
class Comparator$1 {
  static get ANY () {
    return ANY$3
  }
  constructor (comp, options) {
    options = parseOptions_1$1(options);

    if (comp instanceof Comparator$1) {
      if (comp.loose === !!options.loose) {
        return comp
      } else {
        comp = comp.value;
      }
    }

    debug_1$1('comparator', comp, options);
    this.options = options;
    this.loose = !!options.loose;
    this.parse(comp);

    if (this.semver === ANY$3) {
      this.value = '';
    } else {
      this.value = this.operator + this.semver.version;
    }

    debug_1$1('comp', this);
  }

  parse (comp) {
    const r = this.options.loose ? re$4$1[t$4$1.COMPARATORLOOSE] : re$4$1[t$4$1.COMPARATOR];
    const m = comp.match(r);

    if (!m) {
      throw new TypeError(`Invalid comparator: ${comp}`)
    }

    this.operator = m[1] !== undefined ? m[1] : '';
    if (this.operator === '=') {
      this.operator = '';
    }

    // if it literally is just '>' or '' then allow anything.
    if (!m[2]) {
      this.semver = ANY$3;
    } else {
      this.semver = new semver$2(m[2], this.options.loose);
    }
  }

  toString () {
    return this.value
  }

  test (version) {
    debug_1$1('Comparator.test', version, this.options.loose);

    if (this.semver === ANY$3 || version === ANY$3) {
      return true
    }

    if (typeof version === 'string') {
      try {
        version = new semver$2(version, this.options);
      } catch (er) {
        return false
      }
    }

    return cmp_1$1(version, this.operator, this.semver, this.options)
  }

  intersects (comp, options) {
    if (!(comp instanceof Comparator$1)) {
      throw new TypeError('a Comparator is required')
    }

    if (!options || typeof options !== 'object') {
      options = {
        loose: !!options,
        includePrerelease: false
      };
    }

    if (this.operator === '') {
      if (this.value === '') {
        return true
      }
      return new range$1(comp.value, options).test(this.value)
    } else if (comp.operator === '') {
      if (comp.value === '') {
        return true
      }
      return new range$1(this.value, options).test(comp.semver)
    }

    const sameDirectionIncreasing =
      (this.operator === '>=' || this.operator === '>') &&
      (comp.operator === '>=' || comp.operator === '>');
    const sameDirectionDecreasing =
      (this.operator === '<=' || this.operator === '<') &&
      (comp.operator === '<=' || comp.operator === '<');
    const sameSemVer = this.semver.version === comp.semver.version;
    const differentDirectionsInclusive =
      (this.operator === '>=' || this.operator === '<=') &&
      (comp.operator === '>=' || comp.operator === '<=');
    const oppositeDirectionsLessThan =
      cmp_1$1(this.semver, '<', comp.semver, options) &&
      (this.operator === '>=' || this.operator === '>') &&
        (comp.operator === '<=' || comp.operator === '<');
    const oppositeDirectionsGreaterThan =
      cmp_1$1(this.semver, '>', comp.semver, options) &&
      (this.operator === '<=' || this.operator === '<') &&
        (comp.operator === '>=' || comp.operator === '>');

    return (
      sameDirectionIncreasing ||
      sameDirectionDecreasing ||
      (sameSemVer && differentDirectionsInclusive) ||
      oppositeDirectionsLessThan ||
      oppositeDirectionsGreaterThan
    )
  }
}

var comparator$1 = Comparator$1;


const {re: re$4$1, t: t$4$1} = re_1$1;

const satisfies$1 = (version, range$1$1, options) => {
  try {
    range$1$1 = new range$1(range$1$1, options);
  } catch (er) {
    return false
  }
  return range$1$1.test(version)
};
var satisfies_1$1 = satisfies$1;

// Mostly just for testing and legacy API reasons
const toComparators$1 = (range$1$1, options) =>
  new range$1(range$1$1, options).set
    .map(comp => comp.map(c => c.value).join(' ').trim().split(' '));

var toComparators_1$1 = toComparators$1;

const maxSatisfying$1 = (versions, range$1$1, options) => {
  let max = null;
  let maxSV = null;
  let rangeObj = null;
  try {
    rangeObj = new range$1(range$1$1, options);
  } catch (er) {
    return null
  }
  versions.forEach((v) => {
    if (rangeObj.test(v)) {
      // satisfies(v, range, options)
      if (!max || maxSV.compare(v) === -1) {
        // compare(max, v, true)
        max = v;
        maxSV = new semver$2(max, options);
      }
    }
  });
  return max
};
var maxSatisfying_1$1 = maxSatisfying$1;

const minSatisfying$1 = (versions, range$1$1, options) => {
  let min = null;
  let minSV = null;
  let rangeObj = null;
  try {
    rangeObj = new range$1(range$1$1, options);
  } catch (er) {
    return null
  }
  versions.forEach((v) => {
    if (rangeObj.test(v)) {
      // satisfies(v, range, options)
      if (!min || minSV.compare(v) === 1) {
        // compare(min, v, true)
        min = v;
        minSV = new semver$2(min, options);
      }
    }
  });
  return min
};
var minSatisfying_1$1 = minSatisfying$1;

const minVersion$1 = (range$1$1, loose) => {
  range$1$1 = new range$1(range$1$1, loose);

  let minver = new semver$2('0.0.0');
  if (range$1$1.test(minver)) {
    return minver
  }

  minver = new semver$2('0.0.0-0');
  if (range$1$1.test(minver)) {
    return minver
  }

  minver = null;
  for (let i = 0; i < range$1$1.set.length; ++i) {
    const comparators = range$1$1.set[i];

    let setMin = null;
    comparators.forEach((comparator) => {
      // Clone to avoid manipulating the comparator's semver object.
      const compver = new semver$2(comparator.semver.version);
      switch (comparator.operator) {
        case '>':
          if (compver.prerelease.length === 0) {
            compver.patch++;
          } else {
            compver.prerelease.push(0);
          }
          compver.raw = compver.format();
          /* fallthrough */
        case '':
        case '>=':
          if (!setMin || gt_1$1(compver, setMin)) {
            setMin = compver;
          }
          break
        case '<':
        case '<=':
          /* Ignore maximum versions */
          break
        /* istanbul ignore next */
        default:
          throw new Error(`Unexpected operation: ${comparator.operator}`)
      }
    });
    if (setMin && (!minver || gt_1$1(minver, setMin)))
      minver = setMin;
  }

  if (minver && range$1$1.test(minver)) {
    return minver
  }

  return null
};
var minVersion_1$1 = minVersion$1;

const validRange$1 = (range$1$1, options) => {
  try {
    // Return '*' instead of '' so that truthiness works.
    // This will throw if it's invalid anyway
    return new range$1(range$1$1, options).range || '*'
  } catch (er) {
    return null
  }
};
var valid$1$1 = validRange$1;

const {ANY: ANY$1$1} = comparator$1;







const outside$1 = (version, range$1$1, hilo, options) => {
  version = new semver$2(version, options);
  range$1$1 = new range$1(range$1$1, options);

  let gtfn, ltefn, ltfn, comp, ecomp;
  switch (hilo) {
    case '>':
      gtfn = gt_1$1;
      ltefn = lte_1$1;
      ltfn = lt_1$1;
      comp = '>';
      ecomp = '>=';
      break
    case '<':
      gtfn = lt_1$1;
      ltefn = gte_1$1;
      ltfn = gt_1$1;
      comp = '<';
      ecomp = '<=';
      break
    default:
      throw new TypeError('Must provide a hilo val of "<" or ">"')
  }

  // If it satisfies the range it is not outside
  if (satisfies_1$1(version, range$1$1, options)) {
    return false
  }

  // From now on, variable terms are as if we're in "gtr" mode.
  // but note that everything is flipped for the "ltr" function.

  for (let i = 0; i < range$1$1.set.length; ++i) {
    const comparators = range$1$1.set[i];

    let high = null;
    let low = null;

    comparators.forEach((comparator$1$1) => {
      if (comparator$1$1.semver === ANY$1$1) {
        comparator$1$1 = new comparator$1('>=0.0.0');
      }
      high = high || comparator$1$1;
      low = low || comparator$1$1;
      if (gtfn(comparator$1$1.semver, high.semver, options)) {
        high = comparator$1$1;
      } else if (ltfn(comparator$1$1.semver, low.semver, options)) {
        low = comparator$1$1;
      }
    });

    // If the edge version comparator has a operator then our version
    // isn't outside it
    if (high.operator === comp || high.operator === ecomp) {
      return false
    }

    // If the lowest version comparator has an operator and our version
    // is less than it then it isn't higher than the range
    if ((!low.operator || low.operator === comp) &&
        ltefn(version, low.semver)) {
      return false
    } else if (low.operator === ecomp && ltfn(version, low.semver)) {
      return false
    }
  }
  return true
};

var outside_1$1 = outside$1;

// Determine if version is greater than all the versions possible in the range.

const gtr$1 = (version, range, options) => outside_1$1(version, range, '>', options);
var gtr_1$1 = gtr$1;

// Determine if version is less than all the versions possible in the range
const ltr$1 = (version, range, options) => outside_1$1(version, range, '<', options);
var ltr_1$1 = ltr$1;

const intersects$1 = (r1, r2, options) => {
  r1 = new range$1(r1, options);
  r2 = new range$1(r2, options);
  return r1.intersects(r2)
};
var intersects_1$1 = intersects$1;

// given a set of versions and a range, create a "simplified" range
// that includes the same versions that the original range does
// If the original range is shorter than the simplified one, return that.


var simplify$1 = (versions, range, options) => {
  const set = [];
  let min = null;
  let prev = null;
  const v = versions.sort((a, b) => compare_1$1(a, b, options));
  for (const version of v) {
    const included = satisfies_1$1(version, range, options);
    if (included) {
      prev = version;
      if (!min)
        min = version;
    } else {
      if (prev) {
        set.push([min, prev]);
      }
      prev = null;
      min = null;
    }
  }
  if (min)
    set.push([min, null]);

  const ranges = [];
  for (const [min, max] of set) {
    if (min === max)
      ranges.push(min);
    else if (!max && min === v[0])
      ranges.push('*');
    else if (!max)
      ranges.push(`>=${min}`);
    else if (min === v[0])
      ranges.push(`<=${max}`);
    else
      ranges.push(`${min} - ${max}`);
  }
  const simplified = ranges.join(' || ');
  const original = typeof range.raw === 'string' ? range.raw : String(range);
  return simplified.length < original.length ? simplified : range
};

const { ANY: ANY$2$1 } = comparator$1;



// Complex range `r1 || r2 || ...` is a subset of `R1 || R2 || ...` iff:
// - Every simple range `r1, r2, ...` is a subset of some `R1, R2, ...`
//
// Simple range `c1 c2 ...` is a subset of simple range `C1 C2 ...` iff:
// - If c is only the ANY comparator
//   - If C is only the ANY comparator, return true
//   - Else return false
// - Let EQ be the set of = comparators in c
// - If EQ is more than one, return true (null set)
// - Let GT be the highest > or >= comparator in c
// - Let LT be the lowest < or <= comparator in c
// - If GT and LT, and GT.semver > LT.semver, return true (null set)
// - If EQ
//   - If GT, and EQ does not satisfy GT, return true (null set)
//   - If LT, and EQ does not satisfy LT, return true (null set)
//   - If EQ satisfies every C, return true
//   - Else return false
// - If GT
//   - If GT.semver is lower than any > or >= comp in C, return false
//   - If GT is >=, and GT.semver does not satisfy every C, return false
// - If LT
//   - If LT.semver is greater than any < or <= comp in C, return false
//   - If LT is <=, and LT.semver does not satisfy every C, return false
// - If any C is a = range, and GT or LT are set, return false
// - Else return true

const subset$1 = (sub, dom, options) => {
  if (sub === dom)
    return true

  sub = new range$1(sub, options);
  dom = new range$1(dom, options);
  let sawNonNull = false;

  OUTER: for (const simpleSub of sub.set) {
    for (const simpleDom of dom.set) {
      const isSub = simpleSubset$1(simpleSub, simpleDom, options);
      sawNonNull = sawNonNull || isSub !== null;
      if (isSub)
        continue OUTER
    }
    // the null set is a subset of everything, but null simple ranges in
    // a complex range should be ignored.  so if we saw a non-null range,
    // then we know this isn't a subset, but if EVERY simple range was null,
    // then it is a subset.
    if (sawNonNull)
      return false
  }
  return true
};

const simpleSubset$1 = (sub, dom, options) => {
  if (sub === dom)
    return true

  if (sub.length === 1 && sub[0].semver === ANY$2$1)
    return dom.length === 1 && dom[0].semver === ANY$2$1

  const eqSet = new Set();
  let gt, lt;
  for (const c of sub) {
    if (c.operator === '>' || c.operator === '>=')
      gt = higherGT$1(gt, c, options);
    else if (c.operator === '<' || c.operator === '<=')
      lt = lowerLT$1(lt, c, options);
    else
      eqSet.add(c.semver);
  }

  if (eqSet.size > 1)
    return null

  let gtltComp;
  if (gt && lt) {
    gtltComp = compare_1$1(gt.semver, lt.semver, options);
    if (gtltComp > 0)
      return null
    else if (gtltComp === 0 && (gt.operator !== '>=' || lt.operator !== '<='))
      return null
  }

  // will iterate one or zero times
  for (const eq of eqSet) {
    if (gt && !satisfies_1$1(eq, String(gt), options))
      return null

    if (lt && !satisfies_1$1(eq, String(lt), options))
      return null

    for (const c of dom) {
      if (!satisfies_1$1(eq, String(c), options))
        return false
    }

    return true
  }

  let higher, lower;
  let hasDomLT, hasDomGT;
  for (const c of dom) {
    hasDomGT = hasDomGT || c.operator === '>' || c.operator === '>=';
    hasDomLT = hasDomLT || c.operator === '<' || c.operator === '<=';
    if (gt) {
      if (c.operator === '>' || c.operator === '>=') {
        higher = higherGT$1(gt, c, options);
        if (higher === c && higher !== gt)
          return false
      } else if (gt.operator === '>=' && !satisfies_1$1(gt.semver, String(c), options))
        return false
    }
    if (lt) {
      if (c.operator === '<' || c.operator === '<=') {
        lower = lowerLT$1(lt, c, options);
        if (lower === c && lower !== lt)
          return false
      } else if (lt.operator === '<=' && !satisfies_1$1(lt.semver, String(c), options))
        return false
    }
    if (!c.operator && (lt || gt) && gtltComp !== 0)
      return false
  }

  // if there was a < or >, and nothing in the dom, then must be false
  // UNLESS it was limited by another range in the other direction.
  // Eg, >1.0.0 <1.0.1 is still a subset of <2.0.0
  if (gt && hasDomLT && !lt && gtltComp !== 0)
    return false

  if (lt && hasDomGT && !gt && gtltComp !== 0)
    return false

  return true
};

// >=1.2.3 is lower than >1.2.3
const higherGT$1 = (a, b, options) => {
  if (!a)
    return b
  const comp = compare_1$1(a.semver, b.semver, options);
  return comp > 0 ? a
    : comp < 0 ? b
    : b.operator === '>' && a.operator === '>=' ? b
    : a
};

// <=1.2.3 is higher than <1.2.3
const lowerLT$1 = (a, b, options) => {
  if (!a)
    return b
  const comp = compare_1$1(a.semver, b.semver, options);
  return comp < 0 ? a
    : comp > 0 ? b
    : b.operator === '<' && a.operator === '<=' ? b
    : a
};

var subset_1$1 = subset$1;

// just pre-load all the stuff that index.js lazily exports

var semver$1$1 = {
  re: re_1$1.re,
  src: re_1$1.src,
  tokens: re_1$1.t,
  SEMVER_SPEC_VERSION: constants$1.SEMVER_SPEC_VERSION,
  SemVer: semver$2,
  compareIdentifiers: identifiers$1.compareIdentifiers,
  rcompareIdentifiers: identifiers$1.rcompareIdentifiers,
  parse: parse_1$1,
  valid: valid_1$1,
  clean: clean_1$1,
  inc: inc_1$1,
  diff: diff_1$1,
  major: major_1$1,
  minor: minor_1$1,
  patch: patch_1$1,
  prerelease: prerelease_1$1,
  compare: compare_1$1,
  rcompare: rcompare_1$1,
  compareLoose: compareLoose_1$1,
  compareBuild: compareBuild_1$1,
  sort: sort_1$1,
  rsort: rsort_1$1,
  gt: gt_1$1,
  lt: lt_1$1,
  eq: eq_1$1,
  neq: neq_1$1,
  gte: gte_1$1,
  lte: lte_1$1,
  cmp: cmp_1$1,
  coerce: coerce_1$1,
  Comparator: comparator$1,
  Range: range$1,
  satisfies: satisfies_1$1,
  toComparators: toComparators_1$1,
  maxSatisfying: maxSatisfying_1$1,
  minSatisfying: minSatisfying_1$1,
  minVersion: minVersion_1$1,
  validRange: valid$1$1,
  outside: outside_1$1,
  gtr: gtr_1$1,
  ltr: ltr_1$1,
  intersects: intersects_1$1,
  simplifyRange: simplify$1,
  subset: subset_1$1,
};

const log$1 = new Logger$1(`plugin`);

/**
 * The set of data plugins officially supported
 */
var DataPluginID;
(function (DataPluginID) {
    // DECONZ = `deconz`,
    DataPluginID["FILE"] = "file";
    DataPluginID["GEN"] = "gen";
    // Z2M = `z2m`,
    DataPluginID["ZHA"] = "zha";
})(DataPluginID || (DataPluginID = {}));
class PluginDataBase extends PluginBase {
    constructor() {
        super();
        this.apiVersion = `1.0.0`;
        this.id = `${this.id}-data`;
    }
}

var ZigRole;
(function (ZigRole) {
    ZigRole["Coordinator"] = "Coordinator";
    ZigRole["EndDevice"] = "EndDevice";
    ZigRole["Router"] = "Router";
    ZigRole["Unknown"] = "Unknown";
})(ZigRole || (ZigRole = {}));

const ZHA_UNKNOWN = `Unknown`;

// Add any plugin specific configuration elements.
const PluginConfigSchema = PluginConfigBaseSchema.extend({
    filePath: cjs.string().nonempty(),
});
// DataPlugin to read zigs & zags from a file.
// The file format is that of the response json that a call to zha/devices produces.
// Can be created by copying the response from a web browser network trace.
class DataPlugin extends PluginDataBase {
    constructor(config) {
        super();
        this.fqpi = `${this.id}-file`;
        this.config = config;
    }
    // Fetch the device data from a file
    async fetchData() {
        const _zigs = [];
        const _zags = [];
        try {
            const zhaDevices = (await (await fetch(this.config.filePath)).json());
            DataPlugin._mapDevices(zhaDevices.result, _zigs, _zags);
        }
        catch (error) {
            // eslint-disable-next-line no-console
            console.log(`Zigzag plugin-data-file -> fetchData failed:`, error);
        }
        return { zigs: _zigs, zags: _zags };
    }
    static _fixupDevices(zigs, zags) {
        zags.forEach((zag) => {
            // Check to ensure the neighbor Zig exists
            const _zigToFind = zigs.find((zig) => zig.ieee === zag.ieee);
            // Absence means the neighbor scan reports a device that ZHA does not know about.
            // We will create a dummy Zig to reflect this.
            if (!_zigToFind) {
                zigs.push({
                    ieee: zag.ieee,
                    name: ZHA_UNKNOWN,
                    device_type: zag.device_type,
                    nwk: 0,
                    lqi: zag.lqi,
                    rssi: 0,
                    last_seen: ZHA_UNKNOWN,
                    manufacturer: ZHA_UNKNOWN,
                    model: ZHA_UNKNOWN,
                    quirk_applied: ZHA_UNKNOWN,
                    quirk_class: ZHA_UNKNOWN,
                    manufacturer_code: ZHA_UNKNOWN,
                    device_reg_id: ZHA_UNKNOWN,
                    power_source: ZHA_UNKNOWN,
                    available: true,
                });
            }
        });
    }
    // Map the data into the zig objects.
    static _mapDevices(zhaDevices, zigs, zags) {
        zigs.length = 0;
        for (const device of zhaDevices) {
            zigs.push({ ...device });
            // Map the device neighbor structure into Zags.
            DataPlugin._mapZags(device, zags);
        }
        // Ensure consistency between zigs & zags
        DataPlugin._fixupDevices(zigs, zags);
    }
    static _mapZags(device, zags) {
        for (const neighbor of device.neighbors) {
            zags.push({ from: device.ieee, ...neighbor });
        }
    }
}
function createPlugin(config) {
    return new DataPlugin(config);
}

export { DataPlugin, PluginConfigSchema, createPlugin };
//# sourceMappingURL=plugin-data-file.esm.js.map
