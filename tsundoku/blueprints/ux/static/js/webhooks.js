/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./node_modules/@fluent/bundle/esm/builtins.js":
/*!*****************************************************!*\
  !*** ./node_modules/@fluent/bundle/esm/builtins.js ***!
  \*****************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "DATETIME": () => (/* binding */ DATETIME),
/* harmony export */   "NUMBER": () => (/* binding */ NUMBER)
/* harmony export */ });
/* harmony import */ var _types_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./types.js */ "./node_modules/@fluent/bundle/esm/types.js");
/**
 * @overview
 *
 * The FTL resolver ships with a number of functions built-in.
 *
 * Each function take two arguments:
 *   - args - an array of positional args
 *   - opts - an object of key-value args
 *
 * Arguments to functions are guaranteed to already be instances of
 * `FluentValue`.  Functions must return `FluentValues` as well.
 */

function values(opts, allowed) {
    const unwrapped = Object.create(null);
    for (const [name, opt] of Object.entries(opts)) {
        if (allowed.includes(name)) {
            unwrapped[name] = opt.valueOf();
        }
    }
    return unwrapped;
}
const NUMBER_ALLOWED = [
    "unitDisplay",
    "currencyDisplay",
    "useGrouping",
    "minimumIntegerDigits",
    "minimumFractionDigits",
    "maximumFractionDigits",
    "minimumSignificantDigits",
    "maximumSignificantDigits",
];
/**
 * The implementation of the `NUMBER()` builtin available to translations.
 *
 * Translations may call the `NUMBER()` builtin in order to specify formatting
 * options of a number. For example:
 *
 *     pi = The value of π is {NUMBER($pi, maximumFractionDigits: 2)}.
 *
 * The implementation expects an array of `FluentValues` representing the
 * positional arguments, and an object of named `FluentValues` representing the
 * named parameters.
 *
 * The following options are recognized:
 *
 *     unitDisplay
 *     currencyDisplay
 *     useGrouping
 *     minimumIntegerDigits
 *     minimumFractionDigits
 *     maximumFractionDigits
 *     minimumSignificantDigits
 *     maximumSignificantDigits
 *
 * Other options are ignored.
 *
 * @param args The positional arguments passed to this `NUMBER()`.
 * @param opts The named argments passed to this `NUMBER()`.
 */
function NUMBER(args, opts) {
    let arg = args[0];
    if (arg instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone) {
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(`NUMBER(${arg.valueOf()})`);
    }
    if (arg instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNumber) {
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNumber(arg.valueOf(), {
            ...arg.opts,
            ...values(opts, NUMBER_ALLOWED)
        });
    }
    if (arg instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentDateTime) {
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNumber(arg.valueOf(), {
            ...values(opts, NUMBER_ALLOWED)
        });
    }
    throw new TypeError("Invalid argument to NUMBER");
}
const DATETIME_ALLOWED = [
    "dateStyle",
    "timeStyle",
    "fractionalSecondDigits",
    "dayPeriod",
    "hour12",
    "weekday",
    "era",
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
    "timeZoneName",
];
/**
 * The implementation of the `DATETIME()` builtin available to translations.
 *
 * Translations may call the `DATETIME()` builtin in order to specify
 * formatting options of a number. For example:
 *
 *     now = It's {DATETIME($today, month: "long")}.
 *
 * The implementation expects an array of `FluentValues` representing the
 * positional arguments, and an object of named `FluentValues` representing the
 * named parameters.
 *
 * The following options are recognized:
 *
 *     dateStyle
 *     timeStyle
 *     fractionalSecondDigits
 *     dayPeriod
 *     hour12
 *     weekday
 *     era
 *     year
 *     month
 *     day
 *     hour
 *     minute
 *     second
 *     timeZoneName
 *
 * Other options are ignored.
 *
 * @param args The positional arguments passed to this `DATETIME()`.
 * @param opts The named argments passed to this `DATETIME()`.
 */
function DATETIME(args, opts) {
    let arg = args[0];
    if (arg instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone) {
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(`DATETIME(${arg.valueOf()})`);
    }
    if (arg instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentDateTime) {
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentDateTime(arg.valueOf(), {
            ...arg.opts,
            ...values(opts, DATETIME_ALLOWED)
        });
    }
    if (arg instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNumber) {
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentDateTime(arg.valueOf(), {
            ...values(opts, DATETIME_ALLOWED)
        });
    }
    throw new TypeError("Invalid argument to DATETIME");
}


/***/ }),

/***/ "./node_modules/@fluent/bundle/esm/bundle.js":
/*!***************************************************!*\
  !*** ./node_modules/@fluent/bundle/esm/bundle.js ***!
  \***************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "FluentBundle": () => (/* binding */ FluentBundle)
/* harmony export */ });
/* harmony import */ var _resolver_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./resolver.js */ "./node_modules/@fluent/bundle/esm/resolver.js");
/* harmony import */ var _scope_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./scope.js */ "./node_modules/@fluent/bundle/esm/scope.js");
/* harmony import */ var _types_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./types.js */ "./node_modules/@fluent/bundle/esm/types.js");
/* harmony import */ var _builtins_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./builtins.js */ "./node_modules/@fluent/bundle/esm/builtins.js");




/**
 * Message bundles are single-language stores of translation resources. They are
 * responsible for formatting message values and attributes to strings.
 */
class FluentBundle {
    /**
     * Create an instance of `FluentBundle`.
     *
     * The `locales` argument is used to instantiate `Intl` formatters used by
     * translations. The `options` object can be used to configure the bundle.
     *
     * Examples:
     *
     *     let bundle = new FluentBundle(["en-US", "en"]);
     *
     *     let bundle = new FluentBundle(locales, {useIsolating: false});
     *
     *     let bundle = new FluentBundle(locales, {
     *       useIsolating: true,
     *       functions: {
     *         NODE_ENV: () => process.env.NODE_ENV
     *       }
     *     });
     *
     * Available options:
     *
     *   - `functions` - an object of additional functions available to
     *     translations as builtins.
     *
     *   - `useIsolating` - boolean specifying whether to use Unicode isolation
     *     marks (FSI, PDI) for bidi interpolations. Default: `true`.
     *
     *   - `transform` - a function used to transform string parts of patterns.
     */
    constructor(locales, { functions, useIsolating = true, transform = (v) => v } = {}) {
        this._terms = new Map();
        this._messages = new Map();
        this._intls = new WeakMap();
        this.locales = Array.isArray(locales) ? locales : [locales];
        this._functions = {
            NUMBER: _builtins_js__WEBPACK_IMPORTED_MODULE_3__.NUMBER,
            DATETIME: _builtins_js__WEBPACK_IMPORTED_MODULE_3__.DATETIME,
            ...functions
        };
        this._useIsolating = useIsolating;
        this._transform = transform;
    }
    /**
     * Check if a message is present in the bundle.
     *
     * @param id - The identifier of the message to check.
     */
    hasMessage(id) {
        return this._messages.has(id);
    }
    /**
     * Return a raw unformatted message object from the bundle.
     *
     * Raw messages are `{value, attributes}` shapes containing translation units
     * called `Patterns`. `Patterns` are implementation-specific; they should be
     * treated as black boxes and formatted with `FluentBundle.formatPattern`.
     *
     * @param id - The identifier of the message to check.
     */
    getMessage(id) {
        return this._messages.get(id);
    }
    /**
     * Add a translation resource to the bundle.
     *
     * The translation resource must be an instance of `FluentResource`.
     *
     *     let res = new FluentResource("foo = Foo");
     *     bundle.addResource(res);
     *     bundle.getMessage("foo");
     *     // → {value: .., attributes: {..}}
     *
     * Available options:
     *
     *   - `allowOverrides` - boolean specifying whether it's allowed to override
     *     an existing message or term with a new value. Default: `false`.
     *
     * @param   res - FluentResource object.
     * @param   options
     */
    addResource(res, { allowOverrides = false } = {}) {
        const errors = [];
        for (let i = 0; i < res.body.length; i++) {
            let entry = res.body[i];
            if (entry.id.startsWith("-")) {
                // Identifiers starting with a dash (-) define terms. Terms are private
                // and cannot be retrieved from FluentBundle.
                if (allowOverrides === false && this._terms.has(entry.id)) {
                    errors.push(new Error(`Attempt to override an existing term: "${entry.id}"`));
                    continue;
                }
                this._terms.set(entry.id, entry);
            }
            else {
                if (allowOverrides === false && this._messages.has(entry.id)) {
                    errors.push(new Error(`Attempt to override an existing message: "${entry.id}"`));
                    continue;
                }
                this._messages.set(entry.id, entry);
            }
        }
        return errors;
    }
    /**
     * Format a `Pattern` to a string.
     *
     * Format a raw `Pattern` into a string. `args` will be used to resolve
     * references to variables passed as arguments to the translation.
     *
     * In case of errors `formatPattern` will try to salvage as much of the
     * translation as possible and will still return a string. For performance
     * reasons, the encountered errors are not returned but instead are appended
     * to the `errors` array passed as the third argument.
     *
     *     let errors = [];
     *     bundle.addResource(
     *         new FluentResource("hello = Hello, {$name}!"));
     *
     *     let hello = bundle.getMessage("hello");
     *     if (hello.value) {
     *         bundle.formatPattern(hello.value, {name: "Jane"}, errors);
     *         // Returns "Hello, Jane!" and `errors` is empty.
     *
     *         bundle.formatPattern(hello.value, undefined, errors);
     *         // Returns "Hello, {$name}!" and `errors` is now:
     *         // [<ReferenceError: Unknown variable: name>]
     *     }
     *
     * If `errors` is omitted, the first encountered error will be thrown.
     */
    formatPattern(pattern, args = null, errors = null) {
        // Resolve a simple pattern without creating a scope. No error handling is
        // required; by definition simple patterns don't have placeables.
        if (typeof pattern === "string") {
            return this._transform(pattern);
        }
        // Resolve a complex pattern.
        let scope = new _scope_js__WEBPACK_IMPORTED_MODULE_1__.Scope(this, errors, args);
        try {
            let value = (0,_resolver_js__WEBPACK_IMPORTED_MODULE_0__.resolveComplexPattern)(scope, pattern);
            return value.toString(scope);
        }
        catch (err) {
            if (scope.errors) {
                scope.errors.push(err);
                return new _types_js__WEBPACK_IMPORTED_MODULE_2__.FluentNone().toString(scope);
            }
            throw err;
        }
    }
}


/***/ }),

/***/ "./node_modules/@fluent/bundle/esm/index.js":
/*!**************************************************!*\
  !*** ./node_modules/@fluent/bundle/esm/index.js ***!
  \**************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "FluentBundle": () => (/* reexport safe */ _bundle_js__WEBPACK_IMPORTED_MODULE_0__.FluentBundle),
/* harmony export */   "FluentDateTime": () => (/* reexport safe */ _types_js__WEBPACK_IMPORTED_MODULE_2__.FluentDateTime),
/* harmony export */   "FluentNone": () => (/* reexport safe */ _types_js__WEBPACK_IMPORTED_MODULE_2__.FluentNone),
/* harmony export */   "FluentNumber": () => (/* reexport safe */ _types_js__WEBPACK_IMPORTED_MODULE_2__.FluentNumber),
/* harmony export */   "FluentResource": () => (/* reexport safe */ _resource_js__WEBPACK_IMPORTED_MODULE_1__.FluentResource),
/* harmony export */   "FluentType": () => (/* reexport safe */ _types_js__WEBPACK_IMPORTED_MODULE_2__.FluentType)
/* harmony export */ });
/* harmony import */ var _bundle_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./bundle.js */ "./node_modules/@fluent/bundle/esm/bundle.js");
/* harmony import */ var _resource_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./resource.js */ "./node_modules/@fluent/bundle/esm/resource.js");
/* harmony import */ var _types_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./types.js */ "./node_modules/@fluent/bundle/esm/types.js");
/**
 * @module fluent
 * @overview
 *
 * `fluent` is a JavaScript implementation of Project Fluent, a localization
 * framework designed to unleash the expressive power of the natural language.
 *
 */





/***/ }),

/***/ "./node_modules/@fluent/bundle/esm/resolver.js":
/*!*****************************************************!*\
  !*** ./node_modules/@fluent/bundle/esm/resolver.js ***!
  \*****************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "resolveComplexPattern": () => (/* binding */ resolveComplexPattern)
/* harmony export */ });
/* harmony import */ var _types_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./types.js */ "./node_modules/@fluent/bundle/esm/types.js");
/* global Intl */
/**
 * @overview
 *
 * The role of the Fluent resolver is to format a `Pattern` to an instance of
 * `FluentValue`. For performance reasons, primitive strings are considered
 * such instances, too.
 *
 * Translations can contain references to other messages or variables,
 * conditional logic in form of select expressions, traits which describe their
 * grammatical features, and can use Fluent builtins which make use of the
 * `Intl` formatters to format numbers and dates into the bundle's languages.
 * See the documentation of the Fluent syntax for more information.
 *
 * In case of errors the resolver will try to salvage as much of the
 * translation as possible. In rare situations where the resolver didn't know
 * how to recover from an error it will return an instance of `FluentNone`.
 *
 * All expressions resolve to an instance of `FluentValue`. The caller should
 * use the `toString` method to convert the instance to a native value.
 *
 * Functions in this file pass around an instance of the `Scope` class, which
 * stores the data required for successful resolution and error recovery.
 */

// The maximum number of placeables which can be expanded in a single call to
// `formatPattern`. The limit protects against the Billion Laughs and Quadratic
// Blowup attacks. See https://msdn.microsoft.com/en-us/magazine/ee335713.aspx.
const MAX_PLACEABLES = 100;
// Unicode bidi isolation characters.
const FSI = "\u2068";
const PDI = "\u2069";
// Helper: match a variant key to the given selector.
function match(scope, selector, key) {
    if (key === selector) {
        // Both are strings.
        return true;
    }
    // XXX Consider comparing options too, e.g. minimumFractionDigits.
    if (key instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNumber &&
        selector instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNumber &&
        key.value === selector.value) {
        return true;
    }
    if (selector instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNumber && typeof key === "string") {
        let category = scope
            .memoizeIntlObject(Intl.PluralRules, selector.opts)
            .select(selector.value);
        if (key === category) {
            return true;
        }
    }
    return false;
}
// Helper: resolve the default variant from a list of variants.
function getDefault(scope, variants, star) {
    if (variants[star]) {
        return resolvePattern(scope, variants[star].value);
    }
    scope.reportError(new RangeError("No default"));
    return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone();
}
// Helper: resolve arguments to a call expression.
function getArguments(scope, args) {
    const positional = [];
    const named = Object.create(null);
    for (const arg of args) {
        if (arg.type === "narg") {
            named[arg.name] = resolveExpression(scope, arg.value);
        }
        else {
            positional.push(resolveExpression(scope, arg));
        }
    }
    return { positional, named };
}
// Resolve an expression to a Fluent type.
function resolveExpression(scope, expr) {
    switch (expr.type) {
        case "str":
            return expr.value;
        case "num":
            return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNumber(expr.value, {
                minimumFractionDigits: expr.precision
            });
        case "var":
            return resolveVariableReference(scope, expr);
        case "mesg":
            return resolveMessageReference(scope, expr);
        case "term":
            return resolveTermReference(scope, expr);
        case "func":
            return resolveFunctionReference(scope, expr);
        case "select":
            return resolveSelectExpression(scope, expr);
        default:
            return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone();
    }
}
// Resolve a reference to a variable.
function resolveVariableReference(scope, { name }) {
    let arg;
    if (scope.params) {
        // We're inside a TermReference. It's OK to reference undefined parameters.
        if (Object.prototype.hasOwnProperty.call(scope.params, name)) {
            arg = scope.params[name];
        }
        else {
            return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(`$${name}`);
        }
    }
    else if (scope.args
        && Object.prototype.hasOwnProperty.call(scope.args, name)) {
        // We're in the top-level Pattern or inside a MessageReference. Missing
        // variables references produce ReferenceErrors.
        arg = scope.args[name];
    }
    else {
        scope.reportError(new ReferenceError(`Unknown variable: $${name}`));
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(`$${name}`);
    }
    // Return early if the argument already is an instance of FluentType.
    if (arg instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentType) {
        return arg;
    }
    // Convert the argument to a Fluent type.
    switch (typeof arg) {
        case "string":
            return arg;
        case "number":
            return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNumber(arg);
        case "object":
            if (arg instanceof Date) {
                return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentDateTime(arg.getTime());
            }
        // eslint-disable-next-line no-fallthrough
        default:
            scope.reportError(new TypeError(`Variable type not supported: $${name}, ${typeof arg}`));
            return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(`$${name}`);
    }
}
// Resolve a reference to another message.
function resolveMessageReference(scope, { name, attr }) {
    const message = scope.bundle._messages.get(name);
    if (!message) {
        scope.reportError(new ReferenceError(`Unknown message: ${name}`));
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(name);
    }
    if (attr) {
        const attribute = message.attributes[attr];
        if (attribute) {
            return resolvePattern(scope, attribute);
        }
        scope.reportError(new ReferenceError(`Unknown attribute: ${attr}`));
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(`${name}.${attr}`);
    }
    if (message.value) {
        return resolvePattern(scope, message.value);
    }
    scope.reportError(new ReferenceError(`No value: ${name}`));
    return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(name);
}
// Resolve a call to a Term with key-value arguments.
function resolveTermReference(scope, { name, attr, args }) {
    const id = `-${name}`;
    const term = scope.bundle._terms.get(id);
    if (!term) {
        scope.reportError(new ReferenceError(`Unknown term: ${id}`));
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(id);
    }
    if (attr) {
        const attribute = term.attributes[attr];
        if (attribute) {
            // Every TermReference has its own variables.
            scope.params = getArguments(scope, args).named;
            const resolved = resolvePattern(scope, attribute);
            scope.params = null;
            return resolved;
        }
        scope.reportError(new ReferenceError(`Unknown attribute: ${attr}`));
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(`${id}.${attr}`);
    }
    scope.params = getArguments(scope, args).named;
    const resolved = resolvePattern(scope, term.value);
    scope.params = null;
    return resolved;
}
// Resolve a call to a Function with positional and key-value arguments.
function resolveFunctionReference(scope, { name, args }) {
    // Some functions are built-in. Others may be provided by the runtime via
    // the `FluentBundle` constructor.
    let func = scope.bundle._functions[name];
    if (!func) {
        scope.reportError(new ReferenceError(`Unknown function: ${name}()`));
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(`${name}()`);
    }
    if (typeof func !== "function") {
        scope.reportError(new TypeError(`Function ${name}() is not callable`));
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(`${name}()`);
    }
    try {
        let resolved = getArguments(scope, args);
        return func(resolved.positional, resolved.named);
    }
    catch (err) {
        scope.reportError(err);
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone(`${name}()`);
    }
}
// Resolve a select expression to the member object.
function resolveSelectExpression(scope, { selector, variants, star }) {
    let sel = resolveExpression(scope, selector);
    if (sel instanceof _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone) {
        return getDefault(scope, variants, star);
    }
    // Match the selector against keys of each variant, in order.
    for (const variant of variants) {
        const key = resolveExpression(scope, variant.key);
        if (match(scope, sel, key)) {
            return resolvePattern(scope, variant.value);
        }
    }
    return getDefault(scope, variants, star);
}
// Resolve a pattern (a complex string with placeables).
function resolveComplexPattern(scope, ptn) {
    if (scope.dirty.has(ptn)) {
        scope.reportError(new RangeError("Cyclic reference"));
        return new _types_js__WEBPACK_IMPORTED_MODULE_0__.FluentNone();
    }
    // Tag the pattern as dirty for the purpose of the current resolution.
    scope.dirty.add(ptn);
    const result = [];
    // Wrap interpolations with Directional Isolate Formatting characters
    // only when the pattern has more than one element.
    const useIsolating = scope.bundle._useIsolating && ptn.length > 1;
    for (const elem of ptn) {
        if (typeof elem === "string") {
            result.push(scope.bundle._transform(elem));
            continue;
        }
        scope.placeables++;
        if (scope.placeables > MAX_PLACEABLES) {
            scope.dirty.delete(ptn);
            // This is a fatal error which causes the resolver to instantly bail out
            // on this pattern. The length check protects against excessive memory
            // usage, and throwing protects against eating up the CPU when long
            // placeables are deeply nested.
            throw new RangeError(`Too many placeables expanded: ${scope.placeables}, ` +
                `max allowed is ${MAX_PLACEABLES}`);
        }
        if (useIsolating) {
            result.push(FSI);
        }
        result.push(resolveExpression(scope, elem).toString(scope));
        if (useIsolating) {
            result.push(PDI);
        }
    }
    scope.dirty.delete(ptn);
    return result.join("");
}
// Resolve a simple or a complex Pattern to a FluentString (which is really the
// string primitive).
function resolvePattern(scope, value) {
    // Resolve a simple pattern.
    if (typeof value === "string") {
        return scope.bundle._transform(value);
    }
    return resolveComplexPattern(scope, value);
}


/***/ }),

/***/ "./node_modules/@fluent/bundle/esm/resource.js":
/*!*****************************************************!*\
  !*** ./node_modules/@fluent/bundle/esm/resource.js ***!
  \*****************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "FluentResource": () => (/* binding */ FluentResource)
/* harmony export */ });
// This regex is used to iterate through the beginnings of messages and terms.
// With the /m flag, the ^ matches at the beginning of every line.
const RE_MESSAGE_START = /^(-?[a-zA-Z][\w-]*) *= */gm;
// Both Attributes and Variants are parsed in while loops. These regexes are
// used to break out of them.
const RE_ATTRIBUTE_START = /\.([a-zA-Z][\w-]*) *= */y;
const RE_VARIANT_START = /\*?\[/y;
const RE_NUMBER_LITERAL = /(-?[0-9]+(?:\.([0-9]+))?)/y;
const RE_IDENTIFIER = /([a-zA-Z][\w-]*)/y;
const RE_REFERENCE = /([$-])?([a-zA-Z][\w-]*)(?:\.([a-zA-Z][\w-]*))?/y;
const RE_FUNCTION_NAME = /^[A-Z][A-Z0-9_-]*$/;
// A "run" is a sequence of text or string literal characters which don't
// require any special handling. For TextElements such special characters are: {
// (starts a placeable), and line breaks which require additional logic to check
// if the next line is indented. For StringLiterals they are: \ (starts an
// escape sequence), " (ends the literal), and line breaks which are not allowed
// in StringLiterals. Note that string runs may be empty; text runs may not.
const RE_TEXT_RUN = /([^{}\n\r]+)/y;
const RE_STRING_RUN = /([^\\"\n\r]*)/y;
// Escape sequences.
const RE_STRING_ESCAPE = /\\([\\"])/y;
const RE_UNICODE_ESCAPE = /\\u([a-fA-F0-9]{4})|\\U([a-fA-F0-9]{6})/y;
// Used for trimming TextElements and indents.
const RE_LEADING_NEWLINES = /^\n+/;
const RE_TRAILING_SPACES = / +$/;
// Used in makeIndent to strip spaces from blank lines and normalize CRLF to LF.
const RE_BLANK_LINES = / *\r?\n/g;
// Used in makeIndent to measure the indentation.
const RE_INDENT = /( *)$/;
// Common tokens.
const TOKEN_BRACE_OPEN = /{\s*/y;
const TOKEN_BRACE_CLOSE = /\s*}/y;
const TOKEN_BRACKET_OPEN = /\[\s*/y;
const TOKEN_BRACKET_CLOSE = /\s*] */y;
const TOKEN_PAREN_OPEN = /\s*\(\s*/y;
const TOKEN_ARROW = /\s*->\s*/y;
const TOKEN_COLON = /\s*:\s*/y;
// Note the optional comma. As a deviation from the Fluent EBNF, the parser
// doesn't enforce commas between call arguments.
const TOKEN_COMMA = /\s*,?\s*/y;
const TOKEN_BLANK = /\s+/y;
/**
 * Fluent Resource is a structure storing parsed localization entries.
 */
class FluentResource {
    constructor(source) {
        this.body = [];
        RE_MESSAGE_START.lastIndex = 0;
        let cursor = 0;
        // Iterate over the beginnings of messages and terms to efficiently skip
        // comments and recover from errors.
        while (true) {
            let next = RE_MESSAGE_START.exec(source);
            if (next === null) {
                break;
            }
            cursor = RE_MESSAGE_START.lastIndex;
            try {
                this.body.push(parseMessage(next[1]));
            }
            catch (err) {
                if (err instanceof SyntaxError) {
                    // Don't report any Fluent syntax errors. Skip directly to the
                    // beginning of the next message or term.
                    continue;
                }
                throw err;
            }
        }
        // The parser implementation is inlined below for performance reasons,
        // as well as for convenience of accessing `source` and `cursor`.
        // The parser focuses on minimizing the number of false negatives at the
        // expense of increasing the risk of false positives. In other words, it
        // aims at parsing valid Fluent messages with a success rate of 100%, but it
        // may also parse a few invalid messages which the reference parser would
        // reject. The parser doesn't perform any validation and may produce entries
        // which wouldn't make sense in the real world. For best results users are
        // advised to validate translations with the fluent-syntax parser
        // pre-runtime.
        // The parser makes an extensive use of sticky regexes which can be anchored
        // to any offset of the source string without slicing it. Errors are thrown
        // to bail out of parsing of ill-formed messages.
        function test(re) {
            re.lastIndex = cursor;
            return re.test(source);
        }
        // Advance the cursor by the char if it matches. May be used as a predicate
        // (was the match found?) or, if errorClass is passed, as an assertion.
        function consumeChar(char, errorClass) {
            if (source[cursor] === char) {
                cursor++;
                return true;
            }
            if (errorClass) {
                throw new errorClass(`Expected ${char}`);
            }
            return false;
        }
        // Advance the cursor by the token if it matches. May be used as a predicate
        // (was the match found?) or, if errorClass is passed, as an assertion.
        function consumeToken(re, errorClass) {
            if (test(re)) {
                cursor = re.lastIndex;
                return true;
            }
            if (errorClass) {
                throw new errorClass(`Expected ${re.toString()}`);
            }
            return false;
        }
        // Execute a regex, advance the cursor, and return all capture groups.
        function match(re) {
            re.lastIndex = cursor;
            let result = re.exec(source);
            if (result === null) {
                throw new SyntaxError(`Expected ${re.toString()}`);
            }
            cursor = re.lastIndex;
            return result;
        }
        // Execute a regex, advance the cursor, and return the capture group.
        function match1(re) {
            return match(re)[1];
        }
        function parseMessage(id) {
            let value = parsePattern();
            let attributes = parseAttributes();
            if (value === null && Object.keys(attributes).length === 0) {
                throw new SyntaxError("Expected message value or attributes");
            }
            return { id, value, attributes };
        }
        function parseAttributes() {
            let attrs = Object.create(null);
            while (test(RE_ATTRIBUTE_START)) {
                let name = match1(RE_ATTRIBUTE_START);
                let value = parsePattern();
                if (value === null) {
                    throw new SyntaxError("Expected attribute value");
                }
                attrs[name] = value;
            }
            return attrs;
        }
        function parsePattern() {
            let first;
            // First try to parse any simple text on the same line as the id.
            if (test(RE_TEXT_RUN)) {
                first = match1(RE_TEXT_RUN);
            }
            // If there's a placeable on the first line, parse a complex pattern.
            if (source[cursor] === "{" || source[cursor] === "}") {
                // Re-use the text parsed above, if possible.
                return parsePatternElements(first ? [first] : [], Infinity);
            }
            // RE_TEXT_VALUE stops at newlines. Only continue parsing the pattern if
            // what comes after the newline is indented.
            let indent = parseIndent();
            if (indent) {
                if (first) {
                    // If there's text on the first line, the blank block is part of the
                    // translation content in its entirety.
                    return parsePatternElements([first, indent], indent.length);
                }
                // Otherwise, we're dealing with a block pattern, i.e. a pattern which
                // starts on a new line. Discrad the leading newlines but keep the
                // inline indent; it will be used by the dedentation logic.
                indent.value = trim(indent.value, RE_LEADING_NEWLINES);
                return parsePatternElements([indent], indent.length);
            }
            if (first) {
                // It was just a simple inline text after all.
                return trim(first, RE_TRAILING_SPACES);
            }
            return null;
        }
        // Parse a complex pattern as an array of elements.
        function parsePatternElements(elements = [], commonIndent) {
            while (true) {
                if (test(RE_TEXT_RUN)) {
                    elements.push(match1(RE_TEXT_RUN));
                    continue;
                }
                if (source[cursor] === "{") {
                    elements.push(parsePlaceable());
                    continue;
                }
                if (source[cursor] === "}") {
                    throw new SyntaxError("Unbalanced closing brace");
                }
                let indent = parseIndent();
                if (indent) {
                    elements.push(indent);
                    commonIndent = Math.min(commonIndent, indent.length);
                    continue;
                }
                break;
            }
            let lastIndex = elements.length - 1;
            let lastElement = elements[lastIndex];
            // Trim the trailing spaces in the last element if it's a TextElement.
            if (typeof lastElement === "string") {
                elements[lastIndex] = trim(lastElement, RE_TRAILING_SPACES);
            }
            let baked = [];
            for (let element of elements) {
                if (element instanceof Indent) {
                    // Dedent indented lines by the maximum common indent.
                    element = element.value.slice(0, element.value.length - commonIndent);
                }
                if (element) {
                    baked.push(element);
                }
            }
            return baked;
        }
        function parsePlaceable() {
            consumeToken(TOKEN_BRACE_OPEN, SyntaxError);
            let selector = parseInlineExpression();
            if (consumeToken(TOKEN_BRACE_CLOSE)) {
                return selector;
            }
            if (consumeToken(TOKEN_ARROW)) {
                let variants = parseVariants();
                consumeToken(TOKEN_BRACE_CLOSE, SyntaxError);
                return {
                    type: "select",
                    selector,
                    ...variants
                };
            }
            throw new SyntaxError("Unclosed placeable");
        }
        function parseInlineExpression() {
            if (source[cursor] === "{") {
                // It's a nested placeable.
                return parsePlaceable();
            }
            if (test(RE_REFERENCE)) {
                let [, sigil, name, attr = null] = match(RE_REFERENCE);
                if (sigil === "$") {
                    return { type: "var", name };
                }
                if (consumeToken(TOKEN_PAREN_OPEN)) {
                    let args = parseArguments();
                    if (sigil === "-") {
                        // A parameterized term: -term(...).
                        return { type: "term", name, attr, args };
                    }
                    if (RE_FUNCTION_NAME.test(name)) {
                        return { type: "func", name, args };
                    }
                    throw new SyntaxError("Function names must be all upper-case");
                }
                if (sigil === "-") {
                    // A non-parameterized term: -term.
                    return {
                        type: "term",
                        name,
                        attr,
                        args: []
                    };
                }
                return { type: "mesg", name, attr };
            }
            return parseLiteral();
        }
        function parseArguments() {
            let args = [];
            while (true) {
                switch (source[cursor]) {
                    case ")": // End of the argument list.
                        cursor++;
                        return args;
                    case undefined: // EOF
                        throw new SyntaxError("Unclosed argument list");
                }
                args.push(parseArgument());
                // Commas between arguments are treated as whitespace.
                consumeToken(TOKEN_COMMA);
            }
        }
        function parseArgument() {
            let expr = parseInlineExpression();
            if (expr.type !== "mesg") {
                return expr;
            }
            if (consumeToken(TOKEN_COLON)) {
                // The reference is the beginning of a named argument.
                return {
                    type: "narg",
                    name: expr.name,
                    value: parseLiteral()
                };
            }
            // It's a regular message reference.
            return expr;
        }
        function parseVariants() {
            let variants = [];
            let count = 0;
            let star;
            while (test(RE_VARIANT_START)) {
                if (consumeChar("*")) {
                    star = count;
                }
                let key = parseVariantKey();
                let value = parsePattern();
                if (value === null) {
                    throw new SyntaxError("Expected variant value");
                }
                variants[count++] = { key, value };
            }
            if (count === 0) {
                return null;
            }
            if (star === undefined) {
                throw new SyntaxError("Expected default variant");
            }
            return { variants, star };
        }
        function parseVariantKey() {
            consumeToken(TOKEN_BRACKET_OPEN, SyntaxError);
            let key;
            if (test(RE_NUMBER_LITERAL)) {
                key = parseNumberLiteral();
            }
            else {
                key = {
                    type: "str",
                    value: match1(RE_IDENTIFIER)
                };
            }
            consumeToken(TOKEN_BRACKET_CLOSE, SyntaxError);
            return key;
        }
        function parseLiteral() {
            if (test(RE_NUMBER_LITERAL)) {
                return parseNumberLiteral();
            }
            if (source[cursor] === '"') {
                return parseStringLiteral();
            }
            throw new SyntaxError("Invalid expression");
        }
        function parseNumberLiteral() {
            let [, value, fraction = ""] = match(RE_NUMBER_LITERAL);
            let precision = fraction.length;
            return {
                type: "num",
                value: parseFloat(value),
                precision
            };
        }
        function parseStringLiteral() {
            consumeChar('"', SyntaxError);
            let value = "";
            while (true) {
                value += match1(RE_STRING_RUN);
                if (source[cursor] === "\\") {
                    value += parseEscapeSequence();
                    continue;
                }
                if (consumeChar('"')) {
                    return { type: "str", value };
                }
                // We've reached an EOL of EOF.
                throw new SyntaxError("Unclosed string literal");
            }
        }
        // Unescape known escape sequences.
        function parseEscapeSequence() {
            if (test(RE_STRING_ESCAPE)) {
                return match1(RE_STRING_ESCAPE);
            }
            if (test(RE_UNICODE_ESCAPE)) {
                let [, codepoint4, codepoint6] = match(RE_UNICODE_ESCAPE);
                let codepoint = parseInt(codepoint4 || codepoint6, 16);
                return codepoint <= 0xd7ff || 0xe000 <= codepoint
                    // It's a Unicode scalar value.
                    ? String.fromCodePoint(codepoint)
                    // Lonely surrogates can cause trouble when the parsing result is
                    // saved using UTF-8. Use U+FFFD REPLACEMENT CHARACTER instead.
                    : "�";
            }
            throw new SyntaxError("Unknown escape sequence");
        }
        // Parse blank space. Return it if it looks like indent before a pattern
        // line. Skip it othwerwise.
        function parseIndent() {
            let start = cursor;
            consumeToken(TOKEN_BLANK);
            // Check the first non-blank character after the indent.
            switch (source[cursor]) {
                case ".":
                case "[":
                case "*":
                case "}":
                case undefined: // EOF
                    // A special character. End the Pattern.
                    return false;
                case "{":
                    // Placeables don't require indentation (in EBNF: block-placeable).
                    // Continue the Pattern.
                    return makeIndent(source.slice(start, cursor));
            }
            // If the first character on the line is not one of the special characters
            // listed above, it's a regular text character. Check if there's at least
            // one space of indent before it.
            if (source[cursor - 1] === " ") {
                // It's an indented text character (in EBNF: indented-char). Continue
                // the Pattern.
                return makeIndent(source.slice(start, cursor));
            }
            // A not-indented text character is likely the identifier of the next
            // message. End the Pattern.
            return false;
        }
        // Trim blanks in text according to the given regex.
        function trim(text, re) {
            return text.replace(re, "");
        }
        // Normalize a blank block and extract the indent details.
        function makeIndent(blank) {
            let value = blank.replace(RE_BLANK_LINES, "\n");
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            let length = RE_INDENT.exec(blank)[1].length;
            return new Indent(value, length);
        }
    }
}
class Indent {
    constructor(value, length) {
        this.value = value;
        this.length = length;
    }
}


/***/ }),

/***/ "./node_modules/@fluent/bundle/esm/scope.js":
/*!**************************************************!*\
  !*** ./node_modules/@fluent/bundle/esm/scope.js ***!
  \**************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "Scope": () => (/* binding */ Scope)
/* harmony export */ });
class Scope {
    constructor(bundle, errors, args) {
        /** The Set of patterns already encountered during this resolution.
         * Used to detect and prevent cyclic resolutions. */
        this.dirty = new WeakSet();
        /** A dict of parameters passed to a TermReference. */
        this.params = null;
        /** The running count of placeables resolved so far. Used to detect the
          * Billion Laughs and Quadratic Blowup attacks. */
        this.placeables = 0;
        this.bundle = bundle;
        this.errors = errors;
        this.args = args;
    }
    reportError(error) {
        if (!this.errors) {
            throw error;
        }
        this.errors.push(error);
    }
    memoizeIntlObject(ctor, opts) {
        let cache = this.bundle._intls.get(ctor);
        if (!cache) {
            cache = {};
            this.bundle._intls.set(ctor, cache);
        }
        let id = JSON.stringify(opts);
        if (!cache[id]) {
            cache[id] = new ctor(this.bundle.locales, opts);
        }
        return cache[id];
    }
}


/***/ }),

/***/ "./node_modules/@fluent/bundle/esm/types.js":
/*!**************************************************!*\
  !*** ./node_modules/@fluent/bundle/esm/types.js ***!
  \**************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "FluentDateTime": () => (/* binding */ FluentDateTime),
/* harmony export */   "FluentNone": () => (/* binding */ FluentNone),
/* harmony export */   "FluentNumber": () => (/* binding */ FluentNumber),
/* harmony export */   "FluentType": () => (/* binding */ FluentType)
/* harmony export */ });
/**
 * The `FluentType` class is the base of Fluent's type system.
 *
 * Fluent types wrap JavaScript values and store additional configuration for
 * them, which can then be used in the `toString` method together with a proper
 * `Intl` formatter.
 */
class FluentType {
    /**
     * Create a `FluentType` instance.
     *
     * @param value The JavaScript value to wrap.
     */
    constructor(value) {
        this.value = value;
    }
    /**
     * Unwrap the raw value stored by this `FluentType`.
     */
    valueOf() {
        return this.value;
    }
}
/**
 * A `FluentType` representing no correct value.
 */
class FluentNone extends FluentType {
    /**
     * Create an instance of `FluentNone` with an optional fallback value.
     * @param value The fallback value of this `FluentNone`.
     */
    constructor(value = "???") {
        super(value);
    }
    /**
     * Format this `FluentNone` to the fallback string.
     */
    toString(scope) {
        return `{${this.value}}`;
    }
}
/**
 * A `FluentType` representing a number.
 *
 * A `FluentNumber` instance stores the number value of the number it
 * represents. It may also store an option bag of options which will be passed
 * to `Intl.NumerFormat` when the `FluentNumber` is formatted to a string.
 */
class FluentNumber extends FluentType {
    /**
     * Create an instance of `FluentNumber` with options to the
     * `Intl.NumberFormat` constructor.
     *
     * @param value The number value of this `FluentNumber`.
     * @param opts Options which will be passed to `Intl.NumberFormat`.
     */
    constructor(value, opts = {}) {
        super(value);
        this.opts = opts;
    }
    /**
     * Format this `FluentNumber` to a string.
     */
    toString(scope) {
        try {
            const nf = scope.memoizeIntlObject(Intl.NumberFormat, this.opts);
            return nf.format(this.value);
        }
        catch (err) {
            scope.reportError(err);
            return this.value.toString(10);
        }
    }
}
/**
 * A `FluentType` representing a date and time.
 *
 * A `FluentDateTime` instance stores the number value of the date it
 * represents, as a numerical timestamp in milliseconds. It may also store an
 * option bag of options which will be passed to `Intl.DateTimeFormat` when the
 * `FluentDateTime` is formatted to a string.
 */
class FluentDateTime extends FluentType {
    /**
     * Create an instance of `FluentDateTime` with options to the
     * `Intl.DateTimeFormat` constructor.
     *
     * @param value The number value of this `FluentDateTime`, in milliseconds.
     * @param opts Options which will be passed to `Intl.DateTimeFormat`.
     */
    constructor(value, opts = {}) {
        super(value);
        this.opts = opts;
    }
    /**
     * Format this `FluentDateTime` to a string.
     */
    toString(scope) {
        try {
            const dtf = scope.memoizeIntlObject(Intl.DateTimeFormat, this.opts);
            return dtf.format(this.value);
        }
        catch (err) {
            scope.reportError(err);
            return new Date(this.value).toISOString();
        }
    }
}


/***/ }),

/***/ "./node_modules/css-loader/dist/cjs.js!./node_modules/bulma-dashboard/dist/bulma-dashboard.min.css":
/*!*********************************************************************************************************!*\
  !*** ./node_modules/css-loader/dist/cjs.js!./node_modules/bulma-dashboard/dist/bulma-dashboard.min.css ***!
  \*********************************************************************************************************/
/***/ ((module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _css_loader_dist_runtime_cssWithMappingToString_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../../css-loader/dist/runtime/cssWithMappingToString.js */ "./node_modules/css-loader/dist/runtime/cssWithMappingToString.js");
/* harmony import */ var _css_loader_dist_runtime_cssWithMappingToString_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_css_loader_dist_runtime_cssWithMappingToString_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../css-loader/dist/runtime/api.js */ "./node_modules/css-loader/dist/runtime/api.js");
/* harmony import */ var _css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1__);
// Imports


var ___CSS_LOADER_EXPORT___ = _css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1___default()((_css_loader_dist_runtime_cssWithMappingToString_js__WEBPACK_IMPORTED_MODULE_0___default()));
// Module
___CSS_LOADER_EXPORT___.push([module.id, ".is-scrollable{overflow-y:auto}.dashboard{display:flex;flex-direction:row}.dashboard.is-full-height{height:100vh}.dashboard-panel{display:flex;flex-direction:column;padding:2rem 1.5rem;flex:0 0 25rem;height:100%}.dashboard-panel.left{flex:0 0 25rem}.dashboard-panel.right{flex:0 0 25rem}.dashboard-panel.has-thick-padding{padding:3rem 2rem}.dashboard-panel.is-one-quarter{flex:0 0 25%}.dashboard-panel.is-half{flex:0 0 50%}.dashboard-panel.is-one-third{flex:0 0 33.3333333333%}.dashboard-panel.is-small{flex:0 0 15rem}.dashboard-panel.is-medium{flex:0 0 20rem}.dashboard-panel.is-large{flex:0 0 30rem}.dashboard-panel-header.is-centered,.dashboard-panel-content.is-centered,.dashboard-panel-footer.is-centered{display:flex;justify-content:center}.dashboard-panel-header{margin-bottom:2rem}.dashboard-panel-main{flex:1}.dashboard-panel-footer{margin-top:2rem}.dashboard-main{display:flex;flex:1;display:flex;flex-direction:column;min-height:100vh}.dashboard-main .navbar.is-fixed-top{position:-webkit-sticky;position:sticky;top:0}.dashboard-main .footer{flex:1}/*# sourceMappingURL=bulma-dashboard.min.css.map */\n", "",{"version":3,"sources":["webpack://./node_modules/bulma-dashboard/src/bulma-dashboard.sass"],"names":[],"mappings":"AA6BA,eACE,eAAA,CAEF,WAvBE,YAAA,CAIA,kBAAA,CAsBA,0BACE,YAAA,CAEF,iBA7BA,YAAA,CAQA,qBAAA,CAuBE,mBAvCsB,CAwCtB,cAAA,CACA,WAxCqB,CA0CrB,sBArBF,cAAA,CAwBE,uBAxBF,cAAA,CA2BE,mCACE,iBAAA,CAEF,gCA9BF,YAAA,CAgCE,yBAhCF,YAAA,CAkCE,8BAlCF,uBAAA,CAoCE,0BApCF,cAAA,CAsCE,2BAtCF,cAAA,CAwCE,0BAxCF,cAAA,CA4CI,6GA1DJ,YAAA,CAkBA,sBAAA,CA2CE,wBACE,kBApEiC,CAsEnC,sBArDF,MAAA,CAwDE,wBACE,eAzE8B,CA2ElC,gBAtEA,YAAA,CAWA,MAAA,CAXA,YAAA,CAQA,qBAAA,CAkEE,gBAAA,CAGE,qCACE,uBAAA,CACA,eAAA,CACA,KAAA,CAEJ,wBAvEF,MAAA,CAAA,kDAAA","sourceRoot":""}]);
// Exports
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (___CSS_LOADER_EXPORT___);


/***/ }),

/***/ "./node_modules/css-loader/dist/cjs.js!./tsundoku/blueprints/ux/static/css/webhooks.css":
/*!**********************************************************************************************!*\
  !*** ./node_modules/css-loader/dist/cjs.js!./tsundoku/blueprints/ux/static/css/webhooks.css ***!
  \**********************************************************************************************/
/***/ ((module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _node_modules_css_loader_dist_runtime_cssWithMappingToString_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../../../../../node_modules/css-loader/dist/runtime/cssWithMappingToString.js */ "./node_modules/css-loader/dist/runtime/cssWithMappingToString.js");
/* harmony import */ var _node_modules_css_loader_dist_runtime_cssWithMappingToString_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_node_modules_css_loader_dist_runtime_cssWithMappingToString_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../../../../node_modules/css-loader/dist/runtime/api.js */ "./node_modules/css-loader/dist/runtime/api.js");
/* harmony import */ var _node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1__);
// Imports


var ___CSS_LOADER_EXPORT___ = _node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1___default()((_node_modules_css_loader_dist_runtime_cssWithMappingToString_js__WEBPACK_IMPORTED_MODULE_0___default()));
// Module
___CSS_LOADER_EXPORT___.push([module.id, "#webhook-card-container {\r\n    background-color: var(--light-grey);\r\n    border-radius: 20px;\r\n    padding: 15px;\r\n}\r\n\r\n.card {\r\n    border-radius: 7.5px;\r\n}", "",{"version":3,"sources":["webpack://./tsundoku/blueprints/ux/static/css/webhooks.css"],"names":[],"mappings":"AAAA;IACI,mCAAmC;IACnC,mBAAmB;IACnB,aAAa;AACjB;;AAEA;IACI,oBAAoB;AACxB","sourcesContent":["#webhook-card-container {\r\n    background-color: var(--light-grey);\r\n    border-radius: 20px;\r\n    padding: 15px;\r\n}\r\n\r\n.card {\r\n    border-radius: 7.5px;\r\n}"],"sourceRoot":""}]);
// Exports
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (___CSS_LOADER_EXPORT___);


/***/ }),

/***/ "./node_modules/css-loader/dist/runtime/api.js":
/*!*****************************************************!*\
  !*** ./node_modules/css-loader/dist/runtime/api.js ***!
  \*****************************************************/
/***/ ((module) => {



/*
  MIT License http://www.opensource.org/licenses/mit-license.php
  Author Tobias Koppers @sokra
*/
// css base code, injected by the css-loader
// eslint-disable-next-line func-names
module.exports = function (cssWithMappingToString) {
  var list = []; // return the list of modules as css string

  list.toString = function toString() {
    return this.map(function (item) {
      var content = cssWithMappingToString(item);

      if (item[2]) {
        return "@media ".concat(item[2], " {").concat(content, "}");
      }

      return content;
    }).join("");
  }; // import a list of modules into the list
  // eslint-disable-next-line func-names


  list.i = function (modules, mediaQuery, dedupe) {
    if (typeof modules === "string") {
      // eslint-disable-next-line no-param-reassign
      modules = [[null, modules, ""]];
    }

    var alreadyImportedModules = {};

    if (dedupe) {
      for (var i = 0; i < this.length; i++) {
        // eslint-disable-next-line prefer-destructuring
        var id = this[i][0];

        if (id != null) {
          alreadyImportedModules[id] = true;
        }
      }
    }

    for (var _i = 0; _i < modules.length; _i++) {
      var item = [].concat(modules[_i]);

      if (dedupe && alreadyImportedModules[item[0]]) {
        // eslint-disable-next-line no-continue
        continue;
      }

      if (mediaQuery) {
        if (!item[2]) {
          item[2] = mediaQuery;
        } else {
          item[2] = "".concat(mediaQuery, " and ").concat(item[2]);
        }
      }

      list.push(item);
    }
  };

  return list;
};

/***/ }),

/***/ "./node_modules/css-loader/dist/runtime/cssWithMappingToString.js":
/*!************************************************************************!*\
  !*** ./node_modules/css-loader/dist/runtime/cssWithMappingToString.js ***!
  \************************************************************************/
/***/ ((module) => {



function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _unsupportedIterableToArray(arr, i) || _nonIterableRest(); }

function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }

function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }

function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }

function _iterableToArrayLimit(arr, i) { var _i = arr && (typeof Symbol !== "undefined" && arr[Symbol.iterator] || arr["@@iterator"]); if (_i == null) return; var _arr = []; var _n = true; var _d = false; var _s, _e; try { for (_i = _i.call(arr); !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"] != null) _i["return"](); } finally { if (_d) throw _e; } } return _arr; }

function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }

module.exports = function cssWithMappingToString(item) {
  var _item = _slicedToArray(item, 4),
      content = _item[1],
      cssMapping = _item[3];

  if (!cssMapping) {
    return content;
  }

  if (typeof btoa === "function") {
    // eslint-disable-next-line no-undef
    var base64 = btoa(unescape(encodeURIComponent(JSON.stringify(cssMapping))));
    var data = "sourceMappingURL=data:application/json;charset=utf-8;base64,".concat(base64);
    var sourceMapping = "/*# ".concat(data, " */");
    var sourceURLs = cssMapping.sources.map(function (source) {
      return "/*# sourceURL=".concat(cssMapping.sourceRoot || "").concat(source, " */");
    });
    return [content].concat(sourceURLs).concat([sourceMapping]).join("\n");
  }

  return [content].join("\n");
};

/***/ }),

/***/ "./node_modules/bulma-dashboard/dist/bulma-dashboard.min.css":
/*!*******************************************************************!*\
  !*** ./node_modules/bulma-dashboard/dist/bulma-dashboard.min.css ***!
  \*******************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! !../../style-loader/dist/runtime/injectStylesIntoStyleTag.js */ "./node_modules/style-loader/dist/runtime/injectStylesIntoStyleTag.js");
/* harmony import */ var _style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _css_loader_dist_cjs_js_bulma_dashboard_min_css__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! !!../../css-loader/dist/cjs.js!./bulma-dashboard.min.css */ "./node_modules/css-loader/dist/cjs.js!./node_modules/bulma-dashboard/dist/bulma-dashboard.min.css");

            

var options = {};

options.insert = "head";
options.singleton = false;

var update = _style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0___default()(_css_loader_dist_cjs_js_bulma_dashboard_min_css__WEBPACK_IMPORTED_MODULE_1__["default"], options);



/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (_css_loader_dist_cjs_js_bulma_dashboard_min_css__WEBPACK_IMPORTED_MODULE_1__["default"].locals || {});

/***/ }),

/***/ "./tsundoku/blueprints/ux/static/css/webhooks.css":
/*!********************************************************!*\
  !*** ./tsundoku/blueprints/ux/static/css/webhooks.css ***!
  \********************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _node_modules_style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! !../../../../../node_modules/style-loader/dist/runtime/injectStylesIntoStyleTag.js */ "./node_modules/style-loader/dist/runtime/injectStylesIntoStyleTag.js");
/* harmony import */ var _node_modules_style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_node_modules_style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _node_modules_css_loader_dist_cjs_js_webhooks_css__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! !!../../../../../node_modules/css-loader/dist/cjs.js!./webhooks.css */ "./node_modules/css-loader/dist/cjs.js!./tsundoku/blueprints/ux/static/css/webhooks.css");

            

var options = {};

options.insert = "head";
options.singleton = false;

var update = _node_modules_style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0___default()(_node_modules_css_loader_dist_cjs_js_webhooks_css__WEBPACK_IMPORTED_MODULE_1__["default"], options);



/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (_node_modules_css_loader_dist_cjs_js_webhooks_css__WEBPACK_IMPORTED_MODULE_1__["default"].locals || {});

/***/ }),

/***/ "./node_modules/style-loader/dist/runtime/injectStylesIntoStyleTag.js":
/*!****************************************************************************!*\
  !*** ./node_modules/style-loader/dist/runtime/injectStylesIntoStyleTag.js ***!
  \****************************************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {



var isOldIE = function isOldIE() {
  var memo;
  return function memorize() {
    if (typeof memo === 'undefined') {
      // Test for IE <= 9 as proposed by Browserhacks
      // @see http://browserhacks.com/#hack-e71d8692f65334173fee715c222cb805
      // Tests for existence of standard globals is to allow style-loader
      // to operate correctly into non-standard environments
      // @see https://github.com/webpack-contrib/style-loader/issues/177
      memo = Boolean(window && document && document.all && !window.atob);
    }

    return memo;
  };
}();

var getTarget = function getTarget() {
  var memo = {};
  return function memorize(target) {
    if (typeof memo[target] === 'undefined') {
      var styleTarget = document.querySelector(target); // Special case to return head of iframe instead of iframe itself

      if (window.HTMLIFrameElement && styleTarget instanceof window.HTMLIFrameElement) {
        try {
          // This will throw an exception if access to iframe is blocked
          // due to cross-origin restrictions
          styleTarget = styleTarget.contentDocument.head;
        } catch (e) {
          // istanbul ignore next
          styleTarget = null;
        }
      }

      memo[target] = styleTarget;
    }

    return memo[target];
  };
}();

var stylesInDom = [];

function getIndexByIdentifier(identifier) {
  var result = -1;

  for (var i = 0; i < stylesInDom.length; i++) {
    if (stylesInDom[i].identifier === identifier) {
      result = i;
      break;
    }
  }

  return result;
}

function modulesToDom(list, options) {
  var idCountMap = {};
  var identifiers = [];

  for (var i = 0; i < list.length; i++) {
    var item = list[i];
    var id = options.base ? item[0] + options.base : item[0];
    var count = idCountMap[id] || 0;
    var identifier = "".concat(id, " ").concat(count);
    idCountMap[id] = count + 1;
    var index = getIndexByIdentifier(identifier);
    var obj = {
      css: item[1],
      media: item[2],
      sourceMap: item[3]
    };

    if (index !== -1) {
      stylesInDom[index].references++;
      stylesInDom[index].updater(obj);
    } else {
      stylesInDom.push({
        identifier: identifier,
        updater: addStyle(obj, options),
        references: 1
      });
    }

    identifiers.push(identifier);
  }

  return identifiers;
}

function insertStyleElement(options) {
  var style = document.createElement('style');
  var attributes = options.attributes || {};

  if (typeof attributes.nonce === 'undefined') {
    var nonce =  true ? __webpack_require__.nc : 0;

    if (nonce) {
      attributes.nonce = nonce;
    }
  }

  Object.keys(attributes).forEach(function (key) {
    style.setAttribute(key, attributes[key]);
  });

  if (typeof options.insert === 'function') {
    options.insert(style);
  } else {
    var target = getTarget(options.insert || 'head');

    if (!target) {
      throw new Error("Couldn't find a style target. This probably means that the value for the 'insert' parameter is invalid.");
    }

    target.appendChild(style);
  }

  return style;
}

function removeStyleElement(style) {
  // istanbul ignore if
  if (style.parentNode === null) {
    return false;
  }

  style.parentNode.removeChild(style);
}
/* istanbul ignore next  */


var replaceText = function replaceText() {
  var textStore = [];
  return function replace(index, replacement) {
    textStore[index] = replacement;
    return textStore.filter(Boolean).join('\n');
  };
}();

function applyToSingletonTag(style, index, remove, obj) {
  var css = remove ? '' : obj.media ? "@media ".concat(obj.media, " {").concat(obj.css, "}") : obj.css; // For old IE

  /* istanbul ignore if  */

  if (style.styleSheet) {
    style.styleSheet.cssText = replaceText(index, css);
  } else {
    var cssNode = document.createTextNode(css);
    var childNodes = style.childNodes;

    if (childNodes[index]) {
      style.removeChild(childNodes[index]);
    }

    if (childNodes.length) {
      style.insertBefore(cssNode, childNodes[index]);
    } else {
      style.appendChild(cssNode);
    }
  }
}

function applyToTag(style, options, obj) {
  var css = obj.css;
  var media = obj.media;
  var sourceMap = obj.sourceMap;

  if (media) {
    style.setAttribute('media', media);
  } else {
    style.removeAttribute('media');
  }

  if (sourceMap && typeof btoa !== 'undefined') {
    css += "\n/*# sourceMappingURL=data:application/json;base64,".concat(btoa(unescape(encodeURIComponent(JSON.stringify(sourceMap)))), " */");
  } // For old IE

  /* istanbul ignore if  */


  if (style.styleSheet) {
    style.styleSheet.cssText = css;
  } else {
    while (style.firstChild) {
      style.removeChild(style.firstChild);
    }

    style.appendChild(document.createTextNode(css));
  }
}

var singleton = null;
var singletonCounter = 0;

function addStyle(obj, options) {
  var style;
  var update;
  var remove;

  if (options.singleton) {
    var styleIndex = singletonCounter++;
    style = singleton || (singleton = insertStyleElement(options));
    update = applyToSingletonTag.bind(null, style, styleIndex, false);
    remove = applyToSingletonTag.bind(null, style, styleIndex, true);
  } else {
    style = insertStyleElement(options);
    update = applyToTag.bind(null, style, options);

    remove = function remove() {
      removeStyleElement(style);
    };
  }

  update(obj);
  return function updateStyle(newObj) {
    if (newObj) {
      if (newObj.css === obj.css && newObj.media === obj.media && newObj.sourceMap === obj.sourceMap) {
        return;
      }

      update(obj = newObj);
    } else {
      remove();
    }
  };
}

module.exports = function (list, options) {
  options = options || {}; // Force single-tag solution on IE6-9, which has a hard limit on the # of <style>
  // tags it will allow on a page

  if (!options.singleton && typeof options.singleton !== 'boolean') {
    options.singleton = isOldIE();
  }

  list = list || [];
  var lastIdentifiers = modulesToDom(list, options);
  return function update(newList) {
    newList = newList || [];

    if (Object.prototype.toString.call(newList) !== '[object Array]') {
      return;
    }

    for (var i = 0; i < lastIdentifiers.length; i++) {
      var identifier = lastIdentifiers[i];
      var index = getIndexByIdentifier(identifier);
      stylesInDom[index].references--;
    }

    var newLastIdentifiers = modulesToDom(newList, options);

    for (var _i = 0; _i < lastIdentifiers.length; _i++) {
      var _identifier = lastIdentifiers[_i];

      var _index = getIndexByIdentifier(_identifier);

      if (stylesInDom[_index].references === 0) {
        stylesInDom[_index].updater();

        stylesInDom.splice(_index, 1);
      }
    }

    lastIdentifiers = newLastIdentifiers;
  };
};

/***/ }),

/***/ "./tsundoku/blueprints/ux/static/ts/fluent.ts":
/*!****************************************************!*\
  !*** ./tsundoku/blueprints/ux/static/ts/fluent.ts ***!
  \****************************************************/
/***/ ((__unused_webpack_module, exports, __webpack_require__) => {


Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.getInjector = void 0;
__webpack_require__(/*! intl-pluralrules */ "./node_modules/intl-pluralrules/polyfill.js");
const bundle_1 = __webpack_require__(/*! @fluent/bundle */ "./node_modules/@fluent/bundle/esm/index.js");
const getInjector = (resources) => {
    let locale = window["LOCALE"];
    let bundle = new bundle_1.FluentBundle(locale);
    let fallbackBundle = new bundle_1.FluentBundle("en");
    for (const resource of resources) {
        let key = `${locale}/${resource}.ftl`;
        let ftl_resource = new bundle_1.FluentResource({"en/base.ftl":"page-title = 積ん読 ANIME\r\n\r\ncategory-general = General\r\npage-shows = Shows\r\npage-nyaa = Nyaa Search\r\n\r\ncategory-settings = Settings\r\npage-webhooks = Webhooks\r\npage-config = Config\r\npage-logs = Logs\r\n\r\nlogout-button = Logout\r\n\r\nentry-status-downloading = Downloading\r\nentry-status-downloaded = Downloaded\r\nentry-status-renamed = Renamed\r\nentry-status-moved = Moved\r\nentry-status-completed = Completed\r\nentry-status-buffered = Buffered\r\n\r\nupdate-detected = Tsundoku Update Detected\r\n\r\nupdate-commits-behind =\r\n   You are currently <b>{$count}</b> {$count ->\r\n        [one] commit\r\n        *[other] commits\r\n    } behind!\r\n\r\nupdate-th-commit = Commit #\r\nupdate-th-message = Message\r\n\r\nupdate-prompt = Would you like to update? The most recent {$count ->\r\n        [one] commit is\r\n        *[other] commits are\r\n    } displayed below, most recent at the top.\r\n\r\nupdate-button = Update\r\nupdate-close-button = No, not now\r\n\r\nwatch-button-title = Watch\r\nunwatch-button-title = Unwatch\r\n\r\nprocess-button-title = Enable Post-Processing\r\nunprocess-button-title = Disable Post-Processing","en/cmdline.ftl":"title = Tsundoku Command Line\r\n\r\ncmd-dbshell = Launch a sqlite shell into the Tsundoku database.\r\ncmd-migrate = Migrates the Tsundoku database to match any updates.\r\ncmd-create-user = Creates a new login user.\r\ncmd-l10n-compat = Compares two languages, will point out missing translations in the second one.\r\ncmd-l10n-duplicates = Finds duplicate keys in a given language.\r\n\r\nusername = Username:\r\npassword = Password:\r\nconf-password = Confirm Password:\r\n\r\ncompare-missing-lang = Language \"{$missing}\" could not be found or does not exist.\r\ncompare-missing-file = Language \"{$lang}\" is missing the file \"{$file}\".\r\ncompare-missing-key = File \"{$file}\" in language \"{$lang}\" is missing key: \"{$key}\".\r\ncompare-conflict-count = {$count} different conflicts were found in language \"{$to}\".\r\ncompare-no-conflict = No conflicts found. Both locales have the same features.\r\n\r\ncreating-user = Creating user...\r\ncreated-user = User created.","en/config.ftl":"config-page-title = Configuration\r\nconfig-page-subtitle = Update app settings and general configuration\r\n\r\nconfig-test = Test\r\nconfig-test-success = Connected\r\nconfig-test-failure = Error connecting\r\n\r\nfeedback-request = Request a Feature\r\nfeedback-bug = Report a Bug\r\n\r\nsection-general-title = General\r\nsection-general-subtitle = General app settings and configuration\r\n\r\ngeneral-host-title = Server Host\r\ngeneral-host-tooltip = Changes require application restart\r\ngeneral-host-subtitle = Address and port to bind to\r\n\r\ngeneral-loglevel-title = Log Level\r\ngeneral-loglevel-subtitle = Severity level at which to log\r\n\r\ngeneral-locale-title = Locale\r\ngeneral-locale-tooltip = Updates on page refresh\r\ngeneral-locale-subtitle = The language that the app displays\r\n\r\ngeneral-updatecheck-title = Update Check\r\ngeneral-updatecheck-tooltip = Checks daily\r\ngeneral-updatecheck-subtitle = Whether or not to periodically check for updates\r\n\r\ngeneral-defaultformat-title = Default Desired Format\r\ngeneral-defaultformat-subtitle = Default value for new show's desired format\r\n\r\ngeneral-defaultfolder-title = Default Desired Folder\r\ngeneral-defaultfolder-subtitle = Default value for new show's desired folder\r\n\r\ngeneral-unwatchfinished-title = Unwatch When Finished\r\ngeneral-unwatchfinished-subtitle = Unwatch shows after they are marked as finished\r\n\r\nseconds-suffix = seconds\r\n\r\nsection-feeds-title = Feeds\r\nsection-feeds-subtitle = Polling intervals and cutoff for RSS feeds\r\n\r\nfeeds-fuzzy-cutoff-title = Fuzzy Cutoff\r\nfeeds-fuzzy-cutoff-subtitle = Cutoff for matching show names\r\n\r\nfeeds-pollinginterval-title = Polling Interval\r\nfeeds-pollinginterval-tooltip = Setting this to a low number may get you blocked from certain RSS feeds\r\nfeeds-pollinginterval-subtitle = Frequency for checking RSS feeds\r\n\r\nfeeds-completioncheck-title = Completion Check Interval\r\nfeeds-completioncheck-subtitle = Frequency for checking completion status\r\n\r\nfeeds-seedratio-title = Seed Ratio Limit\r\nfeeds-seedratio-subtitle = Wait for this seed ratio before processing a download\r\n\r\nsection-torrent-title = Torrent Client\r\nsection-torrent-subtitle = For connecting to a download client\r\n\r\ntorrent-client-title = Client\r\ntorrent-client-subtitle = Which torrent client to use\r\n\r\ntorrent-host-title = Client Host\r\ntorrent-host-subtitle = The location the client is hosted at\r\n\r\ntorrent-username-title = Username\r\ntorrent-username-subtitle = Authentication username\r\n\r\ntorrent-password-title = Password\r\ntorrent-password-subtitle = Authentication password\r\n\r\ntorrent-secure-title = Secure\r\ntorrent-secure-subtitle = Connect on HTTPS\r\n\r\nsection-api-title = API Key\r\nsection-api-subtitle = For third-party integration with Tsundoku\r\n\r\napi-key-refresh = Refresh\r\nconfig-api-documentation = Documentation\r\n\r\nsection-encode-title = Post-processing\r\nsection-encode-subtitle = Encoding of completed downloads for lower file sizes\r\n\r\nprocess-quality-title = Quality Preset\r\nprocess-quality-subtitle = Higher quality will result in larger file sizes\r\n\r\nencode-stats-total-encoded = {$total_encoded} Completed Encodes\r\nencode-stats-total-saved-gb = {$total_saved_gb} Total GB Saved\r\nencode-stats-avg-saved-mb = {$avg_saved_mb} Average MB Saved\r\nencode-stats-median-time-hours = {$median_time_hours} Median Hours Spent\r\nencode-stats-avg-time-hours = {$avg_time_hours} Average Hours Spent\r\n\r\nencode-quality-low = Low\r\nencode-quality-moderate = Moderate\r\nencode-quality-high = High\r\n\r\nencode-quality-low-desc = actually really bad\r\nencode-quality-moderate-desc = meh\r\nencode-quality-high-desc = visually lossless\r\n\r\nprocess-speed-title = Speed Preset\r\nprocess-speed-subtitle = Faster speeds will result in lower quality and larger file sizes\r\n\r\nencode-speed-ultrafast = Ultra Fast\r\nencode-speed-superfast = Super Fast\r\nencode-speed-veryfast = Very Fast\r\nencode-speed-faster = Faster\r\nencode-speed-fast = Fast\r\nencode-speed-medium = Medium\r\nencode-speed-slow = Slow\r\nencode-speed-slower = Slower\r\nencode-speed-veryslow = Very Slow\r\n\r\nprocess-max-encode-title = Maximum Active Encodes\r\nprocess-max-encode-subtitle = Number of possible concurrent encode operations\r\n\r\nprocess-retry-title = Retry on Failure\r\nprocess-retry-subtitle = Whether or not to retry on encoding failure\r\n\r\ncheckbox-enabled = Enabled\r\nffmpeg-missing = FFmpeg Not Installed\r\n\r\nencode-time-title = Encoding Time\r\nencode-time-subtitle = Time range in which encoding should take place\r\n\r\nhour-0 = Midnight\r\nhour-1 = 1 am\r\nhour-2 = 2 am\r\nhour-3 = 3 am\r\nhour-4 = 4 am\r\nhour-5 = 5 am\r\nhour-6 = 6 am\r\nhour-7 = 7 am\r\nhour-8 = 8 am\r\nhour-9 = 9 am\r\nhour-10 = 10 am\r\nhour-11 = 11 am\r\nhour-12 = Noon\r\nhour-13 = 1 pm\r\nhour-14 = 2 pm\r\nhour-15 = 3 pm\r\nhour-16 = 4 pm\r\nhour-17 = 5 pm\r\nhour-18 = 6 pm\r\nhour-19 = 7 pm\r\nhour-20 = 8 pm\r\nhour-21 = 9 pm\r\nhour-22 = 10 pm\r\nhour-23 = 11 pm","en/errors.ftl":"no-rss-parsers = No RSS parsers installed.\r\nno-shows-found = No shows found, is there an error with your parsers?","en/index.ftl":"shows-page-title = Shows\r\nshows-page-subtitle = Tracked shows in RSS\r\n\r\nstatus-airing = Airing\r\nstatus-finished = Finished\r\nstatus-tba = TBA\r\nstatus-unreleased = Unreleased\r\nstatus-upcoming = Upcoming\r\n\r\nshow-edit-link = Edit\r\nshow-delete-link = Delete\r\n\r\nshow-add-success = Show successfully added.\r\nshow-update-success = Show successfully updated.\r\nshow-delete-success = Show successfully removed.\r\n\r\nempty-show-container = Nothing to see here!\r\nempty-show-container-help = Begin by adding a show below.\r\n\r\nclick-for-more-shows =\r\n    Click to see {{ $not_shown }} more {$not_shown ->\r\n        [one] item\r\n        *[other] items\r\n    }...\r\nback-to-top-link = Back to Top\r\n\r\nadd-show-button = Add show\r\n\r\nadd-modal-header = Add Show\r\n\r\nadd-form-name-tt = Name of the title as it appears in the RSS feed.\r\nadd-form-name-field = Name\r\nadd-form-name-placeholder = Attack on Titan\r\n\r\nadd-form-desired-format-tt = Desired name of the file after it is renamed.\r\nadd-form-desired-format-field = Desired Format\r\n\r\nadd-form-desired-folder-tt = Folder which to place the completed file.\r\nadd-form-desired-folder-field = Desired Folder\r\n\r\nadd-form-season-tt = Value to use for the season of the series when renaming.\r\nadd-form-season-field = Season\r\n\r\nadd-form-episode-offset-tt = Positive or negative value by which to modify the episode number as it appears in the RSS feed.\r\nadd-form-episode-offset-field = Episode Offset\r\n\r\nadd-form-add-button = Add show\r\nadd-form-cancel-button = Cancel\r\n\r\ndelete-modal-header = Delete Show\r\n\r\ndelete-confirm-text = Are you sure you want to delete <b>{$name}</b>?\r\ndelete-confirm-button = Delete\r\ndelete-cancel = No, take me back\r\n\r\nedit-modal-header = Edit Show\r\nedit-clear-cache = Clear Cache\r\nedit-fix-match = Fix Match\r\nedit-kitsu-id = Kitsu.io Show ID\r\n\r\nedit-tab-info = Information\r\nedit-tab-entries = Entries\r\nedit-tab-webhooks = Webhooks\r\n\r\nedit-entries-th-episode = Episode\r\nedit-entries-th-status = Status\r\nedit-entries-th-last-update = Updated\r\n\r\nedit-entries-is-empty = No entries yet!\r\nedit-entries-last-update = {$time} ago\r\n\r\nedit-entries-form-episode = Episode\r\nedit-entries-form-magnet = Magnet URL\r\nedit-entries-form-exists = This episode is already tracked.\r\nedit-entries-form-add-button = Add entry\r\n\r\nedit-webhooks-th-webhook = Webhook\r\nedit-webhooks-th-downloading = Downloading\r\nedit-webhooks-th-downloaded = Downloaded\r\nedit-webhooks-th-renamed = Renamed\r\nedit-webhooks-th-moved = Moved\r\nedit-webhooks-th-completed = Completed\r\n\r\nedit-webhooks-is-empty = Add webhooks on the webhooks page.\r\n\r\nedit-form-name-tt = Name of the title as it appears in the RSS feed.\r\nedit-form-name-field = Name\r\nedit-form-name-placeholder = Show title\r\n\r\nedit-form-desired-format-tt = Desired name of the file after it is renamed.\r\nedit-form-desired-format-field = Desired Format\r\n\r\nedit-form-desired-folder-tt = Folder which to place the completed file.\r\nedit-form-desired-folder-field = Desired Folder\r\n\r\nedit-form-season-tt = Value to use for the season of the series when renaming.\r\nedit-form-season-field = Season\r\n\r\nedit-form-episode-offset-tt = Positive or negative value by which to modify the episode number as it appears in the RSS feed.\r\nedit-form-episode-offset-field = Episode Offset\r\n\r\nedit-form-save-button = Save changes\r\nedit-form-cancel-button = Cancel\r\n\r\nlist-view-actions-header = Actions\r\nlist-view-entry-update-header = Last Update\r\n\r\nsort-by-header = Sort By\r\nsort-dir-asc = Asc\r\nsort-dir-desc = Desc\r\nsort-key-title = Title\r\nsort-key-update = Last Update\r\nsort-key-date-added = Date Added","en/login.ftl":"form-missing-data = Login Form missing required data.\r\ninvalid-credentials = Invalid username and password combination.\r\n\r\nusername = Username\r\npassword = Password\r\n\r\nremember-me = Remember me\r\nlogin-button = Login","en/logs.ftl":"logs-page-title = Logs\r\nlogs-page-subtitle = Activity that is currently going on within the app\r\n\r\nlogs-download = Download Logs\r\n\r\nlog-level-info = Info\r\nlog-level-warning = Warning\r\nlog-level-error = Error\r\nlog-level-debug = Debug\r\n\r\ntitle-with-episode = {$title}, episode {$episode}\r\nepisode-prefix-state = Episode {$episode}, {$state}\r\n\r\ncontext-cache-failure = [Item not Cached ({$type}{$id})]\r\n\r\nwebsocket-state-connecting = Connecting\r\nwebsocket-state-connected = Connected\r\nwebsocket-state-disconnected = Disconnected","en/nyaa_search.ftl":"nyaa-page-title = Nyaa Search\r\nnyaa-page-subtitle = Search for anime releases\r\n\r\nentry-add-success = Successfully added release! Processing {$count} new {$count ->\r\n        [one] entry\r\n        *[other] entries\r\n    }.\r\n\r\nsearch-placeholder = Attack on Titan\r\nsearch-empty-results = Nothing to see here!\r\nsearch-start-searching = Start searching to see some results.\r\n\r\nsearch-th-name = Name\r\nsearch-th-size = Size\r\nsearch-th-date = Date\r\nsearch-th-seeders = Seeders\r\nsearch-th-leechers = Leechers\r\nsearch-th-link = Link to Post\r\n\r\nsearch-item-link = Link\r\n\r\nmodal-title = Add Search Result\r\nmodal-tab-new = New Show\r\nmodal-tab-existing = Add to Existing\r\n\r\nexisting-show-tt = Existing show you want to add this release to.\r\nexisting-show-field = Show\r\n\r\nname-tt = Name of the title as it appears in the RSS feed.\r\nname-field = Name\r\nname-placeholder = Show title\r\n\r\ndesired-format-tt = Desired name of the file after it is renamed.\r\ndesired-format-field = Desired Format\r\n\r\ndesired-folder-tt = Folder which to place the completed file.\r\ndesired-folder-field = Desired Folder\r\n\r\nseason-tt = Value to use for the season of the series when renaming.\r\nseason-field = Season\r\n\r\nepisode-offset-tt = Positive or negative value by which to modify the episode number as it appears in the RSS feed.\r\nepisode-offset-field = Episode Offset\r\n\r\nadd-button = Add release\r\ncancel-button = Cancel","en/webhooks.ftl":"webhooks-page-title = Webhooks\r\nwebhooks-page-subtitle = Usable by your tracked shows\r\n\r\nwebhook-status-valid = 🟢 Connected\r\nwebhook-status-invalid = 🔴 Connection Error\r\n\r\nwebhook-edit-link = Edit\r\nwebhook-delete-link = Delete\r\n\r\nwebhook-page-empty = Nothing to see here!\r\nwebhook-page-empty-subtitle = Begin by adding a webhook below.\r\n\r\nwebhook-add-button = Add webhook\r\n\r\nadd-modal-header = Add Webhook\r\n\r\nadd-form-name-tt = Name of the webhook, only for display purposes.\r\nadd-form-name-field = Name\r\nadd-form-name-placeholder = My Webhook\r\n\r\nadd-form-service-tt = The service that the webhook posts to.\r\nadd-form-service-field = Service\r\n\r\nadd-form-url-tt = URL that the webhook posts to.\r\nadd-form-url-field = URL\r\n\r\nadd-form-content-tt = The format that the content will be sent in.\r\nadd-form-content-field = Content Format\r\n\r\nadd-form-add-button = Add webhook\r\nadd-form-cancel-button = Cancel\r\n\r\ndelete-modal-header = Delete Webhook\r\ndelete-confirm-text = Are you sure you want to delete <b>{$name}</b>?\r\ndelete-confirm-button = Delete\r\ndelete-cancel = No, take me back\r\n\r\nedit-modal-header = Edit Webhook\r\n\r\nedit-form-name-tt = Name of the webhook, only for display purposes.\r\nedit-form-name-field = Name\r\n\r\nedit-form-service-tt = The service that the webhook posts to.\r\nedit-form-service-field = Service\r\n\r\nedit-form-url-tt = URL that the webhook posts to.\r\nedit-form-url-field = URL\r\n\r\nedit-form-content-tt = The format that the content will be sent in.\r\nedit-form-content-name = Content Format\r\n\r\nedit-form-save-button = Save changes\r\nedit-form-cancel-button = Cancel","ru/base.ftl":"page-title = 積ん読\r\n\r\ncategory-general = Главная\r\npage-shows = Отслеживаемые аниме\r\npage-nyaa = Поиск на Nyaa\r\n\r\ncategory-settings = Настройки\r\npage-integrations = Интеграции\r\npage-webhooks = Webhooks\r\npage-config = Конфигурация\r\n\r\nlogout-button = Выход\r\n\r\nentry-status-downloading = Скачивается\r\nentry-status-downloaded = Скачано\r\nentry-status-renamed = Переименовано\r\nentry-status-moved = Перемещено\r\nentry-status-completed = Закончено\r\nentry-status-buffered = Buffered\r\n\r\nupdate-detected = Обнаружено обновление Tsundoku\r\n\r\nupdate-commits-behind =\r\n   В данный момент найдено <b>{$count}</b> {$count ->\r\n        [one] commit\r\n        *[other] commits\r\n    } !\r\n\r\nupdate-th-commit = Commit #\r\nupdate-th-message = Описание\r\n\r\nupdate-prompt = Вы хотели бы обновить Tsundoku? {$count ->\r\n        [one] Последний commit \r\n        *[other] Последние commit'ы \r\n    } отображаются ниже, самые последние - вверху.\r\n\r\nupdate-button = Обновить\r\nupdate-close-button = Нет, не сейчас","ru/cmdline.ftl":"title = Командная строка Tsundoku\r\n\r\ncmd-migrate = Переносит базу данных Tsundoku для загрузки данных.\r\ncmd-create-user = Создает нового пользователя.\r\ncmd-no-ui = Запускает Tsundoku только с включенными API.\r\ncmd-l10n-compat = Сравнивает два языка, укажет на недостающие переводы во втором.\r\n\r\nusername = Логин:\r\npassword = Пароль:\r\nconf-password = Подтверждение пароля:\r\n\r\ncompare-missing-lang = Язык \"{$missing}\" не удалось найти или он не существует.\r\ncompare-missing-file = В языке \"{$lang}\" не найден файл \"{$file}\".\r\ncompare-missing-key = В файле \"{$file}\" языка \"{$lang}\" отсутствует ключ: \"{$key}\".\r\ncompare-conflict-count = {$count} в языке были обнаружены конфликты \"{$to}\".\r\ncompare-no-conflict = Конфликтов не обнаружено. Оба перевода имеют одинаковые функции.\r\n\r\ncreating-user = Создание пользователя...\r\ncreated-user = Пользователь создан.","ru/errors.ftl":"no-rss-parsers = RSS-парсеры не установлены.\r\nno-shows-found = Шоу не найдено, может ошибка с вашими парсерами?","ru/index.ftl":"shows-page-title = Показывает\r\nshows-page-subtitle = Отслеживаемые шоу в RSS\r\n\r\nstatus-airing = В эфире\r\nstatus-finished = Готово\r\nstatus-tba = TBA\r\nstatus-unreleased = Не выпущено\r\nstatus-upcoming = Предстоящие\r\n\r\nshow-edit-link = Редактировать\r\nshow-delete-link = Удалить\r\n\r\nempty-show-container = Здесь нечего смотреть!\r\nempty-show-container-help = Начните с добавления шоу ниже.\r\n\r\nclick-for-more-shows = Нажмите, чтобы увидеть {{ $not_shown }} другие {$not_shown ->\r\n        [one] предмет\r\n        *[other] предметы\r\n    }...\r\nback-to-top-link = Вернуться к началу\r\n\r\nadd-show-button = Добавить шоу\r\n\r\nadd-modal-header = Добавить шоу\r\n\r\nadd-form-name-tt = Название заголовка, как оно отображается в RSS-ленте.\r\nadd-form-name-field = Имя\r\n\r\nadd-form-desired-format-tt = Желаемое имя файла после его переименования.\r\nadd-form-desired-format-field = Желаемый формат\r\n\r\nadd-form-desired-folder-tt = Папка для размещения готового файла.\r\nadd-form-desired-folder-field = Желаемая папка\r\n\r\nadd-form-season-tt = Значение, используемое для сезона сериала при переименовании.\r\nadd-form-season-field = Сезон\r\n\r\nadd-form-episode-offset-tt = Положительное или отрицательное значение, на которое можно изменить номер серии, отображаемый в RSS-канале.\r\nadd-form-episode-offset-field = Смещение эпизода\r\n\r\nadd-form-add-button = Добавить шоу\r\nadd-form-cancel-button = Отменить\r\n\r\ndelete-modal-header = Удалить Показать\r\n\r\ndelete-confirm-text = Вы действительно хотите удалить <b> {$name} </b>?\r\ndelete-confirm-button = Удалить\r\ndelete-cancel = Нет, верни меня\r\n\r\nedit-modal-header = Редактировать шоу\r\nedit-clear-cache = Очистить кеш\r\nedit-fix-match = Исправить совпадение\r\nedit-kitsu-id = Показать идентификатор Kitsu.io\r\n\r\nedit-tab-info = Информация\r\nedit-tab-entries = Записи\r\nedit-tab-webhooks = Веб-перехватчики\r\n\r\nedit-entries-th-episode = Эпизод\r\nedit-entries-th-status = Статус\r\n\r\nedit-entries-form-episode = Эпизод\r\nedit-entries-form-magnet = URL-адрес магнита\r\nedit-entries-form-exists = Этот выпуск уже отслеживается.\r\nedit-entries-form-add-button = Добавить запись\r\n\r\nedit-webhooks-th-webhook = Webhook\r\nedit-webhooks-th-downloading = Скачивание\r\nedit-webhooks-th-downloaded = Загружено\r\nedit-webhooks-th-renamed = Переименовано\r\nedit-webhooks-th-moved = Перемещено\r\nedit-webhooks-th-completed = Завершено\r\n\r\nedit-form-name-tt = Название заголовка в том виде, в котором оно отображается в RSS-ленте.\r\nedit-form-name-field = Имя\r\n\r\nedit-form-desired-format-tt = Желаемое имя файла после его переименования.\r\nedit-form-desired-format-field = Желаемый формат\r\n\r\nedit-form-desired-folder-tt = Папка для размещения готового файла.\r\nedit-form-desired-folder-field = Желаемая папка\r\n\r\nedit-form-season-tt = Значение, используемое для сезона сериала при переименовании.\r\nedit-form-season-field = Сезон\r\n\r\nedit-form-episode-offset-tt = Положительное или отрицательное значение, с помощью которого можно изменить номер эпизода, отображаемый в RSS-канале.\r\nedit-form-episode-offset-field = Смещение эпизода\r\n\r\nedit-form-save-button = Сохранить изменения\r\nedit-form-cancel-button = Отменить","ru/login.ftl":"form-missing-data = Не введен логин или пароль.\r\ninvalid-credentials = Неверное имя пользователя или пароль.\r\n\r\nusername = Логин\r\npassword = Пароль\r\n\r\nremember-me = Запомнить меня\r\nlogin-button = Войти","ru/nyaa_search.ftl":"nyaa-page-title = Поиск Nyaa\r\nnyaa-page-subtitle = Искать выпуски аниме\r\n\r\nentry-add-success = Выпуск успешно добавлен! Обработка {$count} {$count ->\r\n        [one] новой записи\r\n        *[other] новых записей\r\n    }.\r\n\r\nsearch-placeholder = Attack on Titan\r\nsearch-empty-results = Здесь ничего нет!\r\nsearch-start-searching = Начните поиск, чтобы увидеть результаты.\r\n\r\nsearch-th-name = Имя\r\nsearch-th-size = Размер\r\nsearch-th-date = Дата\r\nsearch-th-seeders = Seeders\r\nsearch-th-leechers = Leechers\r\nsearch-th-link = Ссылка на пост\r\n\r\nsearch-item-link = Ссылка\r\n\r\nmodal-title = Добавить результат поиска\r\nmodal-tab-new = Новое шоу\r\nmodal-tab-existing = Добавить к существующим\r\n\r\nexisting-show-tt = Существующее шоу, в которое вы хотите добавить этот выпуск.\r\nexisting-show-field = Показать\r\n\r\nname-tt = Название заголовка в том виде, в котором оно отображается в RSS-ленте.\r\nname-field = Имя\r\nname-placeholder = Имя\r\n\r\ndesired-format-tt = Желаемое имя файла после его переименования.\r\ndesired-format-field = Желаемый формат\r\n\r\ndesired-folder-tt = Папка для размещения завершенного файла.\r\ndesired-folder-field = Желаемая папка\r\n\r\nseason-tt = Значение, используемое для сезона сериала при переименовании.\r\nseason-field = Сезон\r\n\r\nepisode-offset-tt = Положительное или отрицательное значение, на которое можно изменить номер эпизода, отображаемый в RSS-канале.\r\nepisode-offset-field = Смещение эпизода\r\n\r\nadd-button = Добавить выпуск\r\ncancel-button = Отменить","ru/webhooks.ftl":"webhooks-page-title = Webhook\r\nwebhooks-page-subtitle = Может использоваться вашими отслеживаемыми шоу\r\n\r\nwebhook-status-valid =    Подключено\r\nwebhook-status-invalid = 🔴 Ошибка подключения\r\n\r\nwebhook-edit-link = Редактировать\r\nwebhook-delete-link = Удалить\r\n\r\nwebhook-page-empty = Здесь нечего смотреть!\r\nwebhook-page-empty-subtitle = Начните с добавления Webhook'a ниже.\r\n\r\nwebhook-add-button = Добавить веб-перехватчик\r\n\r\nadd-modal-header = Добавить веб-перехватчик\r\n\r\nadd-form-name-tt = Имя Webhook, только для отображения.\r\nadd-form-name-field = Имя\r\nadd-form-name-placeholder = Мои Webhook\r\n\r\nadd-form-service-tt = Сервис, на который отправляется Webhook.\r\nadd-form-service-field = Сервис\r\n\r\nadd-form-url-tt = URL-адрес, на который отправляется Webhook.\r\nadd-form-url-field = URL-адрес\r\n\r\nadd-form-content-tt = Формат, в котором будет отправлено содержимое.\r\nadd-form-content-field = Формат содержимого\r\n\r\nadd-form-add-button = Добавить Webhook\r\nadd-form-cancel-button = Отменить\r\n\r\ndelete-modal-header = Удалить Webhook\r\ndelete-confirm-text = Вы действительно хотите удалить <b> {$name} </b>?\r\ndelete-confirm-button = Удалить\r\ndelete-cancel = Нет, верни меня\r\n\r\nedit-modal-header = Редактировать Webhook\r\n\r\nedit-form-name-tt = Имя Webhook, только для отображения.\r\nedit-form-name-field = Имя\r\n\r\nedit-form-service-tt = Служба, на которую отправляется Webhook.\r\nedit-form-service-field = Сервис\r\n\r\nedit-form-url-tt = URL-адрес, на который отправляется Webhook.\r\nedit-form-url-field = URL-адрес\r\n\r\nedit-form-content-tt = Формат, в котором будет отправлено содержимое.\r\nedit-form-content-name = Формат содержимого\r\n\r\nedit-form-save-button = Сохранить изменения\r\nedit-form-cancel-button = Отменить"}[key]);
        bundle.addResource(ftl_resource);
        key = `en/${resource}.ftl`;
        ftl_resource = new bundle_1.FluentResource({"en/base.ftl":"page-title = 積ん読 ANIME\r\n\r\ncategory-general = General\r\npage-shows = Shows\r\npage-nyaa = Nyaa Search\r\n\r\ncategory-settings = Settings\r\npage-webhooks = Webhooks\r\npage-config = Config\r\npage-logs = Logs\r\n\r\nlogout-button = Logout\r\n\r\nentry-status-downloading = Downloading\r\nentry-status-downloaded = Downloaded\r\nentry-status-renamed = Renamed\r\nentry-status-moved = Moved\r\nentry-status-completed = Completed\r\nentry-status-buffered = Buffered\r\n\r\nupdate-detected = Tsundoku Update Detected\r\n\r\nupdate-commits-behind =\r\n   You are currently <b>{$count}</b> {$count ->\r\n        [one] commit\r\n        *[other] commits\r\n    } behind!\r\n\r\nupdate-th-commit = Commit #\r\nupdate-th-message = Message\r\n\r\nupdate-prompt = Would you like to update? The most recent {$count ->\r\n        [one] commit is\r\n        *[other] commits are\r\n    } displayed below, most recent at the top.\r\n\r\nupdate-button = Update\r\nupdate-close-button = No, not now\r\n\r\nwatch-button-title = Watch\r\nunwatch-button-title = Unwatch\r\n\r\nprocess-button-title = Enable Post-Processing\r\nunprocess-button-title = Disable Post-Processing","en/cmdline.ftl":"title = Tsundoku Command Line\r\n\r\ncmd-dbshell = Launch a sqlite shell into the Tsundoku database.\r\ncmd-migrate = Migrates the Tsundoku database to match any updates.\r\ncmd-create-user = Creates a new login user.\r\ncmd-l10n-compat = Compares two languages, will point out missing translations in the second one.\r\ncmd-l10n-duplicates = Finds duplicate keys in a given language.\r\n\r\nusername = Username:\r\npassword = Password:\r\nconf-password = Confirm Password:\r\n\r\ncompare-missing-lang = Language \"{$missing}\" could not be found or does not exist.\r\ncompare-missing-file = Language \"{$lang}\" is missing the file \"{$file}\".\r\ncompare-missing-key = File \"{$file}\" in language \"{$lang}\" is missing key: \"{$key}\".\r\ncompare-conflict-count = {$count} different conflicts were found in language \"{$to}\".\r\ncompare-no-conflict = No conflicts found. Both locales have the same features.\r\n\r\ncreating-user = Creating user...\r\ncreated-user = User created.","en/config.ftl":"config-page-title = Configuration\r\nconfig-page-subtitle = Update app settings and general configuration\r\n\r\nconfig-test = Test\r\nconfig-test-success = Connected\r\nconfig-test-failure = Error connecting\r\n\r\nfeedback-request = Request a Feature\r\nfeedback-bug = Report a Bug\r\n\r\nsection-general-title = General\r\nsection-general-subtitle = General app settings and configuration\r\n\r\ngeneral-host-title = Server Host\r\ngeneral-host-tooltip = Changes require application restart\r\ngeneral-host-subtitle = Address and port to bind to\r\n\r\ngeneral-loglevel-title = Log Level\r\ngeneral-loglevel-subtitle = Severity level at which to log\r\n\r\ngeneral-locale-title = Locale\r\ngeneral-locale-tooltip = Updates on page refresh\r\ngeneral-locale-subtitle = The language that the app displays\r\n\r\ngeneral-updatecheck-title = Update Check\r\ngeneral-updatecheck-tooltip = Checks daily\r\ngeneral-updatecheck-subtitle = Whether or not to periodically check for updates\r\n\r\ngeneral-defaultformat-title = Default Desired Format\r\ngeneral-defaultformat-subtitle = Default value for new show's desired format\r\n\r\ngeneral-defaultfolder-title = Default Desired Folder\r\ngeneral-defaultfolder-subtitle = Default value for new show's desired folder\r\n\r\ngeneral-unwatchfinished-title = Unwatch When Finished\r\ngeneral-unwatchfinished-subtitle = Unwatch shows after they are marked as finished\r\n\r\nseconds-suffix = seconds\r\n\r\nsection-feeds-title = Feeds\r\nsection-feeds-subtitle = Polling intervals and cutoff for RSS feeds\r\n\r\nfeeds-fuzzy-cutoff-title = Fuzzy Cutoff\r\nfeeds-fuzzy-cutoff-subtitle = Cutoff for matching show names\r\n\r\nfeeds-pollinginterval-title = Polling Interval\r\nfeeds-pollinginterval-tooltip = Setting this to a low number may get you blocked from certain RSS feeds\r\nfeeds-pollinginterval-subtitle = Frequency for checking RSS feeds\r\n\r\nfeeds-completioncheck-title = Completion Check Interval\r\nfeeds-completioncheck-subtitle = Frequency for checking completion status\r\n\r\nfeeds-seedratio-title = Seed Ratio Limit\r\nfeeds-seedratio-subtitle = Wait for this seed ratio before processing a download\r\n\r\nsection-torrent-title = Torrent Client\r\nsection-torrent-subtitle = For connecting to a download client\r\n\r\ntorrent-client-title = Client\r\ntorrent-client-subtitle = Which torrent client to use\r\n\r\ntorrent-host-title = Client Host\r\ntorrent-host-subtitle = The location the client is hosted at\r\n\r\ntorrent-username-title = Username\r\ntorrent-username-subtitle = Authentication username\r\n\r\ntorrent-password-title = Password\r\ntorrent-password-subtitle = Authentication password\r\n\r\ntorrent-secure-title = Secure\r\ntorrent-secure-subtitle = Connect on HTTPS\r\n\r\nsection-api-title = API Key\r\nsection-api-subtitle = For third-party integration with Tsundoku\r\n\r\napi-key-refresh = Refresh\r\nconfig-api-documentation = Documentation\r\n\r\nsection-encode-title = Post-processing\r\nsection-encode-subtitle = Encoding of completed downloads for lower file sizes\r\n\r\nprocess-quality-title = Quality Preset\r\nprocess-quality-subtitle = Higher quality will result in larger file sizes\r\n\r\nencode-stats-total-encoded = {$total_encoded} Completed Encodes\r\nencode-stats-total-saved-gb = {$total_saved_gb} Total GB Saved\r\nencode-stats-avg-saved-mb = {$avg_saved_mb} Average MB Saved\r\nencode-stats-median-time-hours = {$median_time_hours} Median Hours Spent\r\nencode-stats-avg-time-hours = {$avg_time_hours} Average Hours Spent\r\n\r\nencode-quality-low = Low\r\nencode-quality-moderate = Moderate\r\nencode-quality-high = High\r\n\r\nencode-quality-low-desc = actually really bad\r\nencode-quality-moderate-desc = meh\r\nencode-quality-high-desc = visually lossless\r\n\r\nprocess-speed-title = Speed Preset\r\nprocess-speed-subtitle = Faster speeds will result in lower quality and larger file sizes\r\n\r\nencode-speed-ultrafast = Ultra Fast\r\nencode-speed-superfast = Super Fast\r\nencode-speed-veryfast = Very Fast\r\nencode-speed-faster = Faster\r\nencode-speed-fast = Fast\r\nencode-speed-medium = Medium\r\nencode-speed-slow = Slow\r\nencode-speed-slower = Slower\r\nencode-speed-veryslow = Very Slow\r\n\r\nprocess-max-encode-title = Maximum Active Encodes\r\nprocess-max-encode-subtitle = Number of possible concurrent encode operations\r\n\r\nprocess-retry-title = Retry on Failure\r\nprocess-retry-subtitle = Whether or not to retry on encoding failure\r\n\r\ncheckbox-enabled = Enabled\r\nffmpeg-missing = FFmpeg Not Installed\r\n\r\nencode-time-title = Encoding Time\r\nencode-time-subtitle = Time range in which encoding should take place\r\n\r\nhour-0 = Midnight\r\nhour-1 = 1 am\r\nhour-2 = 2 am\r\nhour-3 = 3 am\r\nhour-4 = 4 am\r\nhour-5 = 5 am\r\nhour-6 = 6 am\r\nhour-7 = 7 am\r\nhour-8 = 8 am\r\nhour-9 = 9 am\r\nhour-10 = 10 am\r\nhour-11 = 11 am\r\nhour-12 = Noon\r\nhour-13 = 1 pm\r\nhour-14 = 2 pm\r\nhour-15 = 3 pm\r\nhour-16 = 4 pm\r\nhour-17 = 5 pm\r\nhour-18 = 6 pm\r\nhour-19 = 7 pm\r\nhour-20 = 8 pm\r\nhour-21 = 9 pm\r\nhour-22 = 10 pm\r\nhour-23 = 11 pm","en/errors.ftl":"no-rss-parsers = No RSS parsers installed.\r\nno-shows-found = No shows found, is there an error with your parsers?","en/index.ftl":"shows-page-title = Shows\r\nshows-page-subtitle = Tracked shows in RSS\r\n\r\nstatus-airing = Airing\r\nstatus-finished = Finished\r\nstatus-tba = TBA\r\nstatus-unreleased = Unreleased\r\nstatus-upcoming = Upcoming\r\n\r\nshow-edit-link = Edit\r\nshow-delete-link = Delete\r\n\r\nshow-add-success = Show successfully added.\r\nshow-update-success = Show successfully updated.\r\nshow-delete-success = Show successfully removed.\r\n\r\nempty-show-container = Nothing to see here!\r\nempty-show-container-help = Begin by adding a show below.\r\n\r\nclick-for-more-shows =\r\n    Click to see {{ $not_shown }} more {$not_shown ->\r\n        [one] item\r\n        *[other] items\r\n    }...\r\nback-to-top-link = Back to Top\r\n\r\nadd-show-button = Add show\r\n\r\nadd-modal-header = Add Show\r\n\r\nadd-form-name-tt = Name of the title as it appears in the RSS feed.\r\nadd-form-name-field = Name\r\nadd-form-name-placeholder = Attack on Titan\r\n\r\nadd-form-desired-format-tt = Desired name of the file after it is renamed.\r\nadd-form-desired-format-field = Desired Format\r\n\r\nadd-form-desired-folder-tt = Folder which to place the completed file.\r\nadd-form-desired-folder-field = Desired Folder\r\n\r\nadd-form-season-tt = Value to use for the season of the series when renaming.\r\nadd-form-season-field = Season\r\n\r\nadd-form-episode-offset-tt = Positive or negative value by which to modify the episode number as it appears in the RSS feed.\r\nadd-form-episode-offset-field = Episode Offset\r\n\r\nadd-form-add-button = Add show\r\nadd-form-cancel-button = Cancel\r\n\r\ndelete-modal-header = Delete Show\r\n\r\ndelete-confirm-text = Are you sure you want to delete <b>{$name}</b>?\r\ndelete-confirm-button = Delete\r\ndelete-cancel = No, take me back\r\n\r\nedit-modal-header = Edit Show\r\nedit-clear-cache = Clear Cache\r\nedit-fix-match = Fix Match\r\nedit-kitsu-id = Kitsu.io Show ID\r\n\r\nedit-tab-info = Information\r\nedit-tab-entries = Entries\r\nedit-tab-webhooks = Webhooks\r\n\r\nedit-entries-th-episode = Episode\r\nedit-entries-th-status = Status\r\nedit-entries-th-last-update = Updated\r\n\r\nedit-entries-is-empty = No entries yet!\r\nedit-entries-last-update = {$time} ago\r\n\r\nedit-entries-form-episode = Episode\r\nedit-entries-form-magnet = Magnet URL\r\nedit-entries-form-exists = This episode is already tracked.\r\nedit-entries-form-add-button = Add entry\r\n\r\nedit-webhooks-th-webhook = Webhook\r\nedit-webhooks-th-downloading = Downloading\r\nedit-webhooks-th-downloaded = Downloaded\r\nedit-webhooks-th-renamed = Renamed\r\nedit-webhooks-th-moved = Moved\r\nedit-webhooks-th-completed = Completed\r\n\r\nedit-webhooks-is-empty = Add webhooks on the webhooks page.\r\n\r\nedit-form-name-tt = Name of the title as it appears in the RSS feed.\r\nedit-form-name-field = Name\r\nedit-form-name-placeholder = Show title\r\n\r\nedit-form-desired-format-tt = Desired name of the file after it is renamed.\r\nedit-form-desired-format-field = Desired Format\r\n\r\nedit-form-desired-folder-tt = Folder which to place the completed file.\r\nedit-form-desired-folder-field = Desired Folder\r\n\r\nedit-form-season-tt = Value to use for the season of the series when renaming.\r\nedit-form-season-field = Season\r\n\r\nedit-form-episode-offset-tt = Positive or negative value by which to modify the episode number as it appears in the RSS feed.\r\nedit-form-episode-offset-field = Episode Offset\r\n\r\nedit-form-save-button = Save changes\r\nedit-form-cancel-button = Cancel\r\n\r\nlist-view-actions-header = Actions\r\nlist-view-entry-update-header = Last Update\r\n\r\nsort-by-header = Sort By\r\nsort-dir-asc = Asc\r\nsort-dir-desc = Desc\r\nsort-key-title = Title\r\nsort-key-update = Last Update\r\nsort-key-date-added = Date Added","en/login.ftl":"form-missing-data = Login Form missing required data.\r\ninvalid-credentials = Invalid username and password combination.\r\n\r\nusername = Username\r\npassword = Password\r\n\r\nremember-me = Remember me\r\nlogin-button = Login","en/logs.ftl":"logs-page-title = Logs\r\nlogs-page-subtitle = Activity that is currently going on within the app\r\n\r\nlogs-download = Download Logs\r\n\r\nlog-level-info = Info\r\nlog-level-warning = Warning\r\nlog-level-error = Error\r\nlog-level-debug = Debug\r\n\r\ntitle-with-episode = {$title}, episode {$episode}\r\nepisode-prefix-state = Episode {$episode}, {$state}\r\n\r\ncontext-cache-failure = [Item not Cached ({$type}{$id})]\r\n\r\nwebsocket-state-connecting = Connecting\r\nwebsocket-state-connected = Connected\r\nwebsocket-state-disconnected = Disconnected","en/nyaa_search.ftl":"nyaa-page-title = Nyaa Search\r\nnyaa-page-subtitle = Search for anime releases\r\n\r\nentry-add-success = Successfully added release! Processing {$count} new {$count ->\r\n        [one] entry\r\n        *[other] entries\r\n    }.\r\n\r\nsearch-placeholder = Attack on Titan\r\nsearch-empty-results = Nothing to see here!\r\nsearch-start-searching = Start searching to see some results.\r\n\r\nsearch-th-name = Name\r\nsearch-th-size = Size\r\nsearch-th-date = Date\r\nsearch-th-seeders = Seeders\r\nsearch-th-leechers = Leechers\r\nsearch-th-link = Link to Post\r\n\r\nsearch-item-link = Link\r\n\r\nmodal-title = Add Search Result\r\nmodal-tab-new = New Show\r\nmodal-tab-existing = Add to Existing\r\n\r\nexisting-show-tt = Existing show you want to add this release to.\r\nexisting-show-field = Show\r\n\r\nname-tt = Name of the title as it appears in the RSS feed.\r\nname-field = Name\r\nname-placeholder = Show title\r\n\r\ndesired-format-tt = Desired name of the file after it is renamed.\r\ndesired-format-field = Desired Format\r\n\r\ndesired-folder-tt = Folder which to place the completed file.\r\ndesired-folder-field = Desired Folder\r\n\r\nseason-tt = Value to use for the season of the series when renaming.\r\nseason-field = Season\r\n\r\nepisode-offset-tt = Positive or negative value by which to modify the episode number as it appears in the RSS feed.\r\nepisode-offset-field = Episode Offset\r\n\r\nadd-button = Add release\r\ncancel-button = Cancel","en/webhooks.ftl":"webhooks-page-title = Webhooks\r\nwebhooks-page-subtitle = Usable by your tracked shows\r\n\r\nwebhook-status-valid = 🟢 Connected\r\nwebhook-status-invalid = 🔴 Connection Error\r\n\r\nwebhook-edit-link = Edit\r\nwebhook-delete-link = Delete\r\n\r\nwebhook-page-empty = Nothing to see here!\r\nwebhook-page-empty-subtitle = Begin by adding a webhook below.\r\n\r\nwebhook-add-button = Add webhook\r\n\r\nadd-modal-header = Add Webhook\r\n\r\nadd-form-name-tt = Name of the webhook, only for display purposes.\r\nadd-form-name-field = Name\r\nadd-form-name-placeholder = My Webhook\r\n\r\nadd-form-service-tt = The service that the webhook posts to.\r\nadd-form-service-field = Service\r\n\r\nadd-form-url-tt = URL that the webhook posts to.\r\nadd-form-url-field = URL\r\n\r\nadd-form-content-tt = The format that the content will be sent in.\r\nadd-form-content-field = Content Format\r\n\r\nadd-form-add-button = Add webhook\r\nadd-form-cancel-button = Cancel\r\n\r\ndelete-modal-header = Delete Webhook\r\ndelete-confirm-text = Are you sure you want to delete <b>{$name}</b>?\r\ndelete-confirm-button = Delete\r\ndelete-cancel = No, take me back\r\n\r\nedit-modal-header = Edit Webhook\r\n\r\nedit-form-name-tt = Name of the webhook, only for display purposes.\r\nedit-form-name-field = Name\r\n\r\nedit-form-service-tt = The service that the webhook posts to.\r\nedit-form-service-field = Service\r\n\r\nedit-form-url-tt = URL that the webhook posts to.\r\nedit-form-url-field = URL\r\n\r\nedit-form-content-tt = The format that the content will be sent in.\r\nedit-form-content-name = Content Format\r\n\r\nedit-form-save-button = Save changes\r\nedit-form-cancel-button = Cancel","ru/base.ftl":"page-title = 積ん読\r\n\r\ncategory-general = Главная\r\npage-shows = Отслеживаемые аниме\r\npage-nyaa = Поиск на Nyaa\r\n\r\ncategory-settings = Настройки\r\npage-integrations = Интеграции\r\npage-webhooks = Webhooks\r\npage-config = Конфигурация\r\n\r\nlogout-button = Выход\r\n\r\nentry-status-downloading = Скачивается\r\nentry-status-downloaded = Скачано\r\nentry-status-renamed = Переименовано\r\nentry-status-moved = Перемещено\r\nentry-status-completed = Закончено\r\nentry-status-buffered = Buffered\r\n\r\nupdate-detected = Обнаружено обновление Tsundoku\r\n\r\nupdate-commits-behind =\r\n   В данный момент найдено <b>{$count}</b> {$count ->\r\n        [one] commit\r\n        *[other] commits\r\n    } !\r\n\r\nupdate-th-commit = Commit #\r\nupdate-th-message = Описание\r\n\r\nupdate-prompt = Вы хотели бы обновить Tsundoku? {$count ->\r\n        [one] Последний commit \r\n        *[other] Последние commit'ы \r\n    } отображаются ниже, самые последние - вверху.\r\n\r\nupdate-button = Обновить\r\nupdate-close-button = Нет, не сейчас","ru/cmdline.ftl":"title = Командная строка Tsundoku\r\n\r\ncmd-migrate = Переносит базу данных Tsundoku для загрузки данных.\r\ncmd-create-user = Создает нового пользователя.\r\ncmd-no-ui = Запускает Tsundoku только с включенными API.\r\ncmd-l10n-compat = Сравнивает два языка, укажет на недостающие переводы во втором.\r\n\r\nusername = Логин:\r\npassword = Пароль:\r\nconf-password = Подтверждение пароля:\r\n\r\ncompare-missing-lang = Язык \"{$missing}\" не удалось найти или он не существует.\r\ncompare-missing-file = В языке \"{$lang}\" не найден файл \"{$file}\".\r\ncompare-missing-key = В файле \"{$file}\" языка \"{$lang}\" отсутствует ключ: \"{$key}\".\r\ncompare-conflict-count = {$count} в языке были обнаружены конфликты \"{$to}\".\r\ncompare-no-conflict = Конфликтов не обнаружено. Оба перевода имеют одинаковые функции.\r\n\r\ncreating-user = Создание пользователя...\r\ncreated-user = Пользователь создан.","ru/errors.ftl":"no-rss-parsers = RSS-парсеры не установлены.\r\nno-shows-found = Шоу не найдено, может ошибка с вашими парсерами?","ru/index.ftl":"shows-page-title = Показывает\r\nshows-page-subtitle = Отслеживаемые шоу в RSS\r\n\r\nstatus-airing = В эфире\r\nstatus-finished = Готово\r\nstatus-tba = TBA\r\nstatus-unreleased = Не выпущено\r\nstatus-upcoming = Предстоящие\r\n\r\nshow-edit-link = Редактировать\r\nshow-delete-link = Удалить\r\n\r\nempty-show-container = Здесь нечего смотреть!\r\nempty-show-container-help = Начните с добавления шоу ниже.\r\n\r\nclick-for-more-shows = Нажмите, чтобы увидеть {{ $not_shown }} другие {$not_shown ->\r\n        [one] предмет\r\n        *[other] предметы\r\n    }...\r\nback-to-top-link = Вернуться к началу\r\n\r\nadd-show-button = Добавить шоу\r\n\r\nadd-modal-header = Добавить шоу\r\n\r\nadd-form-name-tt = Название заголовка, как оно отображается в RSS-ленте.\r\nadd-form-name-field = Имя\r\n\r\nadd-form-desired-format-tt = Желаемое имя файла после его переименования.\r\nadd-form-desired-format-field = Желаемый формат\r\n\r\nadd-form-desired-folder-tt = Папка для размещения готового файла.\r\nadd-form-desired-folder-field = Желаемая папка\r\n\r\nadd-form-season-tt = Значение, используемое для сезона сериала при переименовании.\r\nadd-form-season-field = Сезон\r\n\r\nadd-form-episode-offset-tt = Положительное или отрицательное значение, на которое можно изменить номер серии, отображаемый в RSS-канале.\r\nadd-form-episode-offset-field = Смещение эпизода\r\n\r\nadd-form-add-button = Добавить шоу\r\nadd-form-cancel-button = Отменить\r\n\r\ndelete-modal-header = Удалить Показать\r\n\r\ndelete-confirm-text = Вы действительно хотите удалить <b> {$name} </b>?\r\ndelete-confirm-button = Удалить\r\ndelete-cancel = Нет, верни меня\r\n\r\nedit-modal-header = Редактировать шоу\r\nedit-clear-cache = Очистить кеш\r\nedit-fix-match = Исправить совпадение\r\nedit-kitsu-id = Показать идентификатор Kitsu.io\r\n\r\nedit-tab-info = Информация\r\nedit-tab-entries = Записи\r\nedit-tab-webhooks = Веб-перехватчики\r\n\r\nedit-entries-th-episode = Эпизод\r\nedit-entries-th-status = Статус\r\n\r\nedit-entries-form-episode = Эпизод\r\nedit-entries-form-magnet = URL-адрес магнита\r\nedit-entries-form-exists = Этот выпуск уже отслеживается.\r\nedit-entries-form-add-button = Добавить запись\r\n\r\nedit-webhooks-th-webhook = Webhook\r\nedit-webhooks-th-downloading = Скачивание\r\nedit-webhooks-th-downloaded = Загружено\r\nedit-webhooks-th-renamed = Переименовано\r\nedit-webhooks-th-moved = Перемещено\r\nedit-webhooks-th-completed = Завершено\r\n\r\nedit-form-name-tt = Название заголовка в том виде, в котором оно отображается в RSS-ленте.\r\nedit-form-name-field = Имя\r\n\r\nedit-form-desired-format-tt = Желаемое имя файла после его переименования.\r\nedit-form-desired-format-field = Желаемый формат\r\n\r\nedit-form-desired-folder-tt = Папка для размещения готового файла.\r\nedit-form-desired-folder-field = Желаемая папка\r\n\r\nedit-form-season-tt = Значение, используемое для сезона сериала при переименовании.\r\nedit-form-season-field = Сезон\r\n\r\nedit-form-episode-offset-tt = Положительное или отрицательное значение, с помощью которого можно изменить номер эпизода, отображаемый в RSS-канале.\r\nedit-form-episode-offset-field = Смещение эпизода\r\n\r\nedit-form-save-button = Сохранить изменения\r\nedit-form-cancel-button = Отменить","ru/login.ftl":"form-missing-data = Не введен логин или пароль.\r\ninvalid-credentials = Неверное имя пользователя или пароль.\r\n\r\nusername = Логин\r\npassword = Пароль\r\n\r\nremember-me = Запомнить меня\r\nlogin-button = Войти","ru/nyaa_search.ftl":"nyaa-page-title = Поиск Nyaa\r\nnyaa-page-subtitle = Искать выпуски аниме\r\n\r\nentry-add-success = Выпуск успешно добавлен! Обработка {$count} {$count ->\r\n        [one] новой записи\r\n        *[other] новых записей\r\n    }.\r\n\r\nsearch-placeholder = Attack on Titan\r\nsearch-empty-results = Здесь ничего нет!\r\nsearch-start-searching = Начните поиск, чтобы увидеть результаты.\r\n\r\nsearch-th-name = Имя\r\nsearch-th-size = Размер\r\nsearch-th-date = Дата\r\nsearch-th-seeders = Seeders\r\nsearch-th-leechers = Leechers\r\nsearch-th-link = Ссылка на пост\r\n\r\nsearch-item-link = Ссылка\r\n\r\nmodal-title = Добавить результат поиска\r\nmodal-tab-new = Новое шоу\r\nmodal-tab-existing = Добавить к существующим\r\n\r\nexisting-show-tt = Существующее шоу, в которое вы хотите добавить этот выпуск.\r\nexisting-show-field = Показать\r\n\r\nname-tt = Название заголовка в том виде, в котором оно отображается в RSS-ленте.\r\nname-field = Имя\r\nname-placeholder = Имя\r\n\r\ndesired-format-tt = Желаемое имя файла после его переименования.\r\ndesired-format-field = Желаемый формат\r\n\r\ndesired-folder-tt = Папка для размещения завершенного файла.\r\ndesired-folder-field = Желаемая папка\r\n\r\nseason-tt = Значение, используемое для сезона сериала при переименовании.\r\nseason-field = Сезон\r\n\r\nepisode-offset-tt = Положительное или отрицательное значение, на которое можно изменить номер эпизода, отображаемый в RSS-канале.\r\nepisode-offset-field = Смещение эпизода\r\n\r\nadd-button = Добавить выпуск\r\ncancel-button = Отменить","ru/webhooks.ftl":"webhooks-page-title = Webhook\r\nwebhooks-page-subtitle = Может использоваться вашими отслеживаемыми шоу\r\n\r\nwebhook-status-valid =    Подключено\r\nwebhook-status-invalid = 🔴 Ошибка подключения\r\n\r\nwebhook-edit-link = Редактировать\r\nwebhook-delete-link = Удалить\r\n\r\nwebhook-page-empty = Здесь нечего смотреть!\r\nwebhook-page-empty-subtitle = Начните с добавления Webhook'a ниже.\r\n\r\nwebhook-add-button = Добавить веб-перехватчик\r\n\r\nadd-modal-header = Добавить веб-перехватчик\r\n\r\nadd-form-name-tt = Имя Webhook, только для отображения.\r\nadd-form-name-field = Имя\r\nadd-form-name-placeholder = Мои Webhook\r\n\r\nadd-form-service-tt = Сервис, на который отправляется Webhook.\r\nadd-form-service-field = Сервис\r\n\r\nadd-form-url-tt = URL-адрес, на который отправляется Webhook.\r\nadd-form-url-field = URL-адрес\r\n\r\nadd-form-content-tt = Формат, в котором будет отправлено содержимое.\r\nadd-form-content-field = Формат содержимого\r\n\r\nadd-form-add-button = Добавить Webhook\r\nadd-form-cancel-button = Отменить\r\n\r\ndelete-modal-header = Удалить Webhook\r\ndelete-confirm-text = Вы действительно хотите удалить <b> {$name} </b>?\r\ndelete-confirm-button = Удалить\r\ndelete-cancel = Нет, верни меня\r\n\r\nedit-modal-header = Редактировать Webhook\r\n\r\nedit-form-name-tt = Имя Webhook, только для отображения.\r\nedit-form-name-field = Имя\r\n\r\nedit-form-service-tt = Служба, на которую отправляется Webhook.\r\nedit-form-service-field = Сервис\r\n\r\nedit-form-url-tt = URL-адрес, на который отправляется Webhook.\r\nedit-form-url-field = URL-адрес\r\n\r\nedit-form-content-tt = Формат, в котором будет отправлено содержимое.\r\nedit-form-content-name = Формат содержимого\r\n\r\nedit-form-save-button = Сохранить изменения\r\nedit-form-cancel-button = Отменить"}[key]);
        fallbackBundle.addResource(ftl_resource);
    }
    let injector = (key, ctx = {}) => {
        let msg = bundle.getMessage(key);
        if (typeof msg !== "undefined" && msg.value)
            return bundle.formatPattern(msg.value, ctx);
        else
            msg = fallbackBundle.getMessage(key);
        if (typeof msg !== "undefined" && msg.value)
            return fallbackBundle.formatPattern(msg.value, ctx);
        if (typeof msg === "undefined")
            console.error(`Key ${key} missing completely from desired and fallback locales.`);
        return key;
    };
    return injector;
};
exports.getInjector = getInjector;


/***/ }),

/***/ "./node_modules/intl-pluralrules/plural-rules.js":
/*!*******************************************************!*\
  !*** ./node_modules/intl-pluralrules/plural-rules.js ***!
  \*******************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {



var getPluralRules = __webpack_require__(/*! ./factory */ "./node_modules/intl-pluralrules/factory.mjs");
var PseudoNumberFormat = __webpack_require__(/*! ./pseudo-number-format */ "./node_modules/intl-pluralrules/pseudo-number-format.js");

function _interopDefaultLegacy (e) { return e && typeof e === 'object' && 'default' in e ? e : { 'default': e }; }

var getPluralRules__default = /*#__PURE__*/_interopDefaultLegacy(getPluralRules);
var PseudoNumberFormat__default = /*#__PURE__*/_interopDefaultLegacy(PseudoNumberFormat);

function _typeof(obj) {
  "@babel/helpers - typeof";

  if (typeof Symbol === "function" && typeof Symbol.iterator === "symbol") {
    _typeof = function (obj) {
      return typeof obj;
    };
  } else {
    _typeof = function (obj) {
      return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj;
    };
  }

  return _typeof(obj);
}

var commonjsGlobal = typeof globalThis !== 'undefined' ? globalThis : typeof window !== 'undefined' ? window : typeof __webpack_require__.g !== 'undefined' ? __webpack_require__.g : typeof self !== 'undefined' ? self : {};

function getDefaultExportFromCjs (x) {
	return x && x.__esModule && Object.prototype.hasOwnProperty.call(x, 'default') ? x['default'] : x;
}

var plurals$1 = {exports: {}};

(function (module, exports) {
  var a = function a(n, ord) {
    if (ord) return 'other';
    return n == 1 ? 'one' : 'other';
  };

  var b = function b(n, ord) {
    if (ord) return 'other';
    return n == 0 || n == 1 ? 'one' : 'other';
  };

  var c = function c(n, ord) {
    if (ord) return 'other';
    return n >= 0 && n <= 1 ? 'one' : 'other';
  };

  var d = function d(n, ord) {
    var s = String(n).split('.'),
        v0 = !s[1];
    if (ord) return 'other';
    return n == 1 && v0 ? 'one' : 'other';
  };

  var e = function e(n, ord) {
    return 'other';
  };

  var f = function f(n, ord) {
    if (ord) return 'other';
    return n == 1 ? 'one' : n == 2 ? 'two' : 'other';
  };

  (function (root, plurals) {
    Object.defineProperty(plurals, '__esModule', {
      value: true
    });
    module.exports = plurals;
  })(commonjsGlobal, {
    _in: e,
    af: a,
    ak: b,
    am: c,
    an: a,
    ar: function ar(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n,
          n100 = t0 && s[0].slice(-2);
      if (ord) return 'other';
      return n == 0 ? 'zero' : n == 1 ? 'one' : n == 2 ? 'two' : n100 >= 3 && n100 <= 10 ? 'few' : n100 >= 11 && n100 <= 99 ? 'many' : 'other';
    },
    ars: function ars(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n,
          n100 = t0 && s[0].slice(-2);
      if (ord) return 'other';
      return n == 0 ? 'zero' : n == 1 ? 'one' : n == 2 ? 'two' : n100 >= 3 && n100 <= 10 ? 'few' : n100 >= 11 && n100 <= 99 ? 'many' : 'other';
    },
    as: function as(n, ord) {
      if (ord) return n == 1 || n == 5 || n == 7 || n == 8 || n == 9 || n == 10 ? 'one' : n == 2 || n == 3 ? 'two' : n == 4 ? 'few' : n == 6 ? 'many' : 'other';
      return n >= 0 && n <= 1 ? 'one' : 'other';
    },
    asa: a,
    ast: d,
    az: function az(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          i10 = i.slice(-1),
          i100 = i.slice(-2),
          i1000 = i.slice(-3);
      if (ord) return i10 == 1 || i10 == 2 || i10 == 5 || i10 == 7 || i10 == 8 || i100 == 20 || i100 == 50 || i100 == 70 || i100 == 80 ? 'one' : i10 == 3 || i10 == 4 || i1000 == 100 || i1000 == 200 || i1000 == 300 || i1000 == 400 || i1000 == 500 || i1000 == 600 || i1000 == 700 || i1000 == 800 || i1000 == 900 ? 'few' : i == 0 || i10 == 6 || i100 == 40 || i100 == 60 || i100 == 90 ? 'many' : 'other';
      return n == 1 ? 'one' : 'other';
    },
    be: function be(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1),
          n100 = t0 && s[0].slice(-2);
      if (ord) return (n10 == 2 || n10 == 3) && n100 != 12 && n100 != 13 ? 'few' : 'other';
      return n10 == 1 && n100 != 11 ? 'one' : n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14) ? 'few' : t0 && n10 == 0 || n10 >= 5 && n10 <= 9 || n100 >= 11 && n100 <= 14 ? 'many' : 'other';
    },
    bem: a,
    bez: a,
    bg: a,
    bho: b,
    bm: e,
    bn: function bn(n, ord) {
      if (ord) return n == 1 || n == 5 || n == 7 || n == 8 || n == 9 || n == 10 ? 'one' : n == 2 || n == 3 ? 'two' : n == 4 ? 'few' : n == 6 ? 'many' : 'other';
      return n >= 0 && n <= 1 ? 'one' : 'other';
    },
    bo: e,
    br: function br(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1),
          n100 = t0 && s[0].slice(-2),
          n1000000 = t0 && s[0].slice(-6);
      if (ord) return 'other';
      return n10 == 1 && n100 != 11 && n100 != 71 && n100 != 91 ? 'one' : n10 == 2 && n100 != 12 && n100 != 72 && n100 != 92 ? 'two' : (n10 == 3 || n10 == 4 || n10 == 9) && (n100 < 10 || n100 > 19) && (n100 < 70 || n100 > 79) && (n100 < 90 || n100 > 99) ? 'few' : n != 0 && t0 && n1000000 == 0 ? 'many' : 'other';
    },
    brx: a,
    bs: function bs(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '',
          v0 = !s[1],
          i10 = i.slice(-1),
          i100 = i.slice(-2),
          f10 = f.slice(-1),
          f100 = f.slice(-2);
      if (ord) return 'other';
      return v0 && i10 == 1 && i100 != 11 || f10 == 1 && f100 != 11 ? 'one' : v0 && i10 >= 2 && i10 <= 4 && (i100 < 12 || i100 > 14) || f10 >= 2 && f10 <= 4 && (f100 < 12 || f100 > 14) ? 'few' : 'other';
    },
    ca: function ca(n, ord) {
      var s = String(n).split('.'),
          v0 = !s[1];
      if (ord) return n == 1 || n == 3 ? 'one' : n == 2 ? 'two' : n == 4 ? 'few' : 'other';
      return n == 1 && v0 ? 'one' : 'other';
    },
    ce: a,
    ceb: function ceb(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '',
          v0 = !s[1],
          i10 = i.slice(-1),
          f10 = f.slice(-1);
      if (ord) return 'other';
      return v0 && (i == 1 || i == 2 || i == 3) || v0 && i10 != 4 && i10 != 6 && i10 != 9 || !v0 && f10 != 4 && f10 != 6 && f10 != 9 ? 'one' : 'other';
    },
    cgg: a,
    chr: a,
    ckb: a,
    cs: function cs(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          v0 = !s[1];
      if (ord) return 'other';
      return n == 1 && v0 ? 'one' : i >= 2 && i <= 4 && v0 ? 'few' : !v0 ? 'many' : 'other';
    },
    cy: function cy(n, ord) {
      if (ord) return n == 0 || n == 7 || n == 8 || n == 9 ? 'zero' : n == 1 ? 'one' : n == 2 ? 'two' : n == 3 || n == 4 ? 'few' : n == 5 || n == 6 ? 'many' : 'other';
      return n == 0 ? 'zero' : n == 1 ? 'one' : n == 2 ? 'two' : n == 3 ? 'few' : n == 6 ? 'many' : 'other';
    },
    da: function da(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          t0 = Number(s[0]) == n;
      if (ord) return 'other';
      return n == 1 || !t0 && (i == 0 || i == 1) ? 'one' : 'other';
    },
    de: d,
    doi: c,
    dsb: function dsb(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '',
          v0 = !s[1],
          i100 = i.slice(-2),
          f100 = f.slice(-2);
      if (ord) return 'other';
      return v0 && i100 == 1 || f100 == 1 ? 'one' : v0 && i100 == 2 || f100 == 2 ? 'two' : v0 && (i100 == 3 || i100 == 4) || f100 == 3 || f100 == 4 ? 'few' : 'other';
    },
    dv: a,
    dz: e,
    ee: a,
    el: a,
    en: function en(n, ord) {
      var s = String(n).split('.'),
          v0 = !s[1],
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1),
          n100 = t0 && s[0].slice(-2);
      if (ord) return n10 == 1 && n100 != 11 ? 'one' : n10 == 2 && n100 != 12 ? 'two' : n10 == 3 && n100 != 13 ? 'few' : 'other';
      return n == 1 && v0 ? 'one' : 'other';
    },
    eo: a,
    es: a,
    et: d,
    eu: a,
    fa: c,
    ff: function ff(n, ord) {
      if (ord) return 'other';
      return n >= 0 && n < 2 ? 'one' : 'other';
    },
    fi: d,
    fil: function fil(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '',
          v0 = !s[1],
          i10 = i.slice(-1),
          f10 = f.slice(-1);
      if (ord) return n == 1 ? 'one' : 'other';
      return v0 && (i == 1 || i == 2 || i == 3) || v0 && i10 != 4 && i10 != 6 && i10 != 9 || !v0 && f10 != 4 && f10 != 6 && f10 != 9 ? 'one' : 'other';
    },
    fo: a,
    fr: function fr(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          v0 = !s[1],
          i1000000 = i.slice(-6);
      if (ord) return n == 1 ? 'one' : 'other';
      return n >= 0 && n < 2 ? 'one' : i != 0 && i1000000 == 0 && v0 ? 'many' : 'other';
    },
    fur: a,
    fy: d,
    ga: function ga(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n;
      if (ord) return n == 1 ? 'one' : 'other';
      return n == 1 ? 'one' : n == 2 ? 'two' : t0 && n >= 3 && n <= 6 ? 'few' : t0 && n >= 7 && n <= 10 ? 'many' : 'other';
    },
    gd: function gd(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n;
      if (ord) return n == 1 || n == 11 ? 'one' : n == 2 || n == 12 ? 'two' : n == 3 || n == 13 ? 'few' : 'other';
      return n == 1 || n == 11 ? 'one' : n == 2 || n == 12 ? 'two' : t0 && n >= 3 && n <= 10 || t0 && n >= 13 && n <= 19 ? 'few' : 'other';
    },
    gl: d,
    gsw: a,
    gu: function gu(n, ord) {
      if (ord) return n == 1 ? 'one' : n == 2 || n == 3 ? 'two' : n == 4 ? 'few' : n == 6 ? 'many' : 'other';
      return n >= 0 && n <= 1 ? 'one' : 'other';
    },
    guw: b,
    gv: function gv(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          v0 = !s[1],
          i10 = i.slice(-1),
          i100 = i.slice(-2);
      if (ord) return 'other';
      return v0 && i10 == 1 ? 'one' : v0 && i10 == 2 ? 'two' : v0 && (i100 == 0 || i100 == 20 || i100 == 40 || i100 == 60 || i100 == 80) ? 'few' : !v0 ? 'many' : 'other';
    },
    ha: a,
    haw: a,
    he: function he(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          v0 = !s[1],
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1);
      if (ord) return 'other';
      return n == 1 && v0 ? 'one' : i == 2 && v0 ? 'two' : v0 && (n < 0 || n > 10) && t0 && n10 == 0 ? 'many' : 'other';
    },
    hi: function hi(n, ord) {
      if (ord) return n == 1 ? 'one' : n == 2 || n == 3 ? 'two' : n == 4 ? 'few' : n == 6 ? 'many' : 'other';
      return n >= 0 && n <= 1 ? 'one' : 'other';
    },
    hr: function hr(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '',
          v0 = !s[1],
          i10 = i.slice(-1),
          i100 = i.slice(-2),
          f10 = f.slice(-1),
          f100 = f.slice(-2);
      if (ord) return 'other';
      return v0 && i10 == 1 && i100 != 11 || f10 == 1 && f100 != 11 ? 'one' : v0 && i10 >= 2 && i10 <= 4 && (i100 < 12 || i100 > 14) || f10 >= 2 && f10 <= 4 && (f100 < 12 || f100 > 14) ? 'few' : 'other';
    },
    hsb: function hsb(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '',
          v0 = !s[1],
          i100 = i.slice(-2),
          f100 = f.slice(-2);
      if (ord) return 'other';
      return v0 && i100 == 1 || f100 == 1 ? 'one' : v0 && i100 == 2 || f100 == 2 ? 'two' : v0 && (i100 == 3 || i100 == 4) || f100 == 3 || f100 == 4 ? 'few' : 'other';
    },
    hu: function hu(n, ord) {
      if (ord) return n == 1 || n == 5 ? 'one' : 'other';
      return n == 1 ? 'one' : 'other';
    },
    hy: function hy(n, ord) {
      if (ord) return n == 1 ? 'one' : 'other';
      return n >= 0 && n < 2 ? 'one' : 'other';
    },
    ia: d,
    id: e,
    ig: e,
    ii: e,
    io: d,
    is: function is(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          t0 = Number(s[0]) == n,
          i10 = i.slice(-1),
          i100 = i.slice(-2);
      if (ord) return 'other';
      return t0 && i10 == 1 && i100 != 11 || !t0 ? 'one' : 'other';
    },
    it: function it(n, ord) {
      var s = String(n).split('.'),
          v0 = !s[1];
      if (ord) return n == 11 || n == 8 || n == 80 || n == 800 ? 'many' : 'other';
      return n == 1 && v0 ? 'one' : 'other';
    },
    iu: f,
    iw: function iw(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          v0 = !s[1],
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1);
      if (ord) return 'other';
      return n == 1 && v0 ? 'one' : i == 2 && v0 ? 'two' : v0 && (n < 0 || n > 10) && t0 && n10 == 0 ? 'many' : 'other';
    },
    ja: e,
    jbo: e,
    jgo: a,
    ji: d,
    jmc: a,
    jv: e,
    jw: e,
    ka: function ka(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          i100 = i.slice(-2);
      if (ord) return i == 1 ? 'one' : i == 0 || i100 >= 2 && i100 <= 20 || i100 == 40 || i100 == 60 || i100 == 80 ? 'many' : 'other';
      return n == 1 ? 'one' : 'other';
    },
    kab: function kab(n, ord) {
      if (ord) return 'other';
      return n >= 0 && n < 2 ? 'one' : 'other';
    },
    kaj: a,
    kcg: a,
    kde: e,
    kea: e,
    kk: function kk(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1);
      if (ord) return n10 == 6 || n10 == 9 || t0 && n10 == 0 && n != 0 ? 'many' : 'other';
      return n == 1 ? 'one' : 'other';
    },
    kkj: a,
    kl: a,
    km: e,
    kn: c,
    ko: e,
    ks: a,
    ksb: a,
    ksh: function ksh(n, ord) {
      if (ord) return 'other';
      return n == 0 ? 'zero' : n == 1 ? 'one' : 'other';
    },
    ku: a,
    kw: function kw(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n,
          n100 = t0 && s[0].slice(-2),
          n1000 = t0 && s[0].slice(-3),
          n100000 = t0 && s[0].slice(-5),
          n1000000 = t0 && s[0].slice(-6);
      if (ord) return t0 && n >= 1 && n <= 4 || n100 >= 1 && n100 <= 4 || n100 >= 21 && n100 <= 24 || n100 >= 41 && n100 <= 44 || n100 >= 61 && n100 <= 64 || n100 >= 81 && n100 <= 84 ? 'one' : n == 5 || n100 == 5 ? 'many' : 'other';
      return n == 0 ? 'zero' : n == 1 ? 'one' : n100 == 2 || n100 == 22 || n100 == 42 || n100 == 62 || n100 == 82 || t0 && n1000 == 0 && (n100000 >= 1000 && n100000 <= 20000 || n100000 == 40000 || n100000 == 60000 || n100000 == 80000) || n != 0 && n1000000 == 100000 ? 'two' : n100 == 3 || n100 == 23 || n100 == 43 || n100 == 63 || n100 == 83 ? 'few' : n != 1 && (n100 == 1 || n100 == 21 || n100 == 41 || n100 == 61 || n100 == 81) ? 'many' : 'other';
    },
    ky: a,
    lag: function lag(n, ord) {
      var s = String(n).split('.'),
          i = s[0];
      if (ord) return 'other';
      return n == 0 ? 'zero' : (i == 0 || i == 1) && n != 0 ? 'one' : 'other';
    },
    lb: a,
    lg: a,
    lij: function lij(n, ord) {
      var s = String(n).split('.'),
          v0 = !s[1],
          t0 = Number(s[0]) == n;
      if (ord) return n == 11 || n == 8 || t0 && n >= 80 && n <= 89 || t0 && n >= 800 && n <= 899 ? 'many' : 'other';
      return n == 1 && v0 ? 'one' : 'other';
    },
    lkt: e,
    ln: b,
    lo: function lo(n, ord) {
      if (ord) return n == 1 ? 'one' : 'other';
      return 'other';
    },
    lt: function lt(n, ord) {
      var s = String(n).split('.'),
          f = s[1] || '',
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1),
          n100 = t0 && s[0].slice(-2);
      if (ord) return 'other';
      return n10 == 1 && (n100 < 11 || n100 > 19) ? 'one' : n10 >= 2 && n10 <= 9 && (n100 < 11 || n100 > 19) ? 'few' : f != 0 ? 'many' : 'other';
    },
    lv: function lv(n, ord) {
      var s = String(n).split('.'),
          f = s[1] || '',
          v = f.length,
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1),
          n100 = t0 && s[0].slice(-2),
          f100 = f.slice(-2),
          f10 = f.slice(-1);
      if (ord) return 'other';
      return t0 && n10 == 0 || n100 >= 11 && n100 <= 19 || v == 2 && f100 >= 11 && f100 <= 19 ? 'zero' : n10 == 1 && n100 != 11 || v == 2 && f10 == 1 && f100 != 11 || v != 2 && f10 == 1 ? 'one' : 'other';
    },
    mas: a,
    mg: b,
    mgo: a,
    mk: function mk(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '',
          v0 = !s[1],
          i10 = i.slice(-1),
          i100 = i.slice(-2),
          f10 = f.slice(-1),
          f100 = f.slice(-2);
      if (ord) return i10 == 1 && i100 != 11 ? 'one' : i10 == 2 && i100 != 12 ? 'two' : (i10 == 7 || i10 == 8) && i100 != 17 && i100 != 18 ? 'many' : 'other';
      return v0 && i10 == 1 && i100 != 11 || f10 == 1 && f100 != 11 ? 'one' : 'other';
    },
    ml: a,
    mn: a,
    mo: function mo(n, ord) {
      var s = String(n).split('.'),
          v0 = !s[1],
          t0 = Number(s[0]) == n,
          n100 = t0 && s[0].slice(-2);
      if (ord) return n == 1 ? 'one' : 'other';
      return n == 1 && v0 ? 'one' : !v0 || n == 0 || n100 >= 2 && n100 <= 19 ? 'few' : 'other';
    },
    mr: function mr(n, ord) {
      if (ord) return n == 1 ? 'one' : n == 2 || n == 3 ? 'two' : n == 4 ? 'few' : 'other';
      return n == 1 ? 'one' : 'other';
    },
    ms: function ms(n, ord) {
      if (ord) return n == 1 ? 'one' : 'other';
      return 'other';
    },
    mt: function mt(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n,
          n100 = t0 && s[0].slice(-2);
      if (ord) return 'other';
      return n == 1 ? 'one' : n == 0 || n100 >= 2 && n100 <= 10 ? 'few' : n100 >= 11 && n100 <= 19 ? 'many' : 'other';
    },
    my: e,
    nah: a,
    naq: f,
    nb: a,
    nd: a,
    ne: function ne(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n;
      if (ord) return t0 && n >= 1 && n <= 4 ? 'one' : 'other';
      return n == 1 ? 'one' : 'other';
    },
    nl: d,
    nn: a,
    nnh: a,
    no: a,
    nqo: e,
    nr: a,
    nso: b,
    ny: a,
    nyn: a,
    om: a,
    or: function or(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n;
      if (ord) return n == 1 || n == 5 || t0 && n >= 7 && n <= 9 ? 'one' : n == 2 || n == 3 ? 'two' : n == 4 ? 'few' : n == 6 ? 'many' : 'other';
      return n == 1 ? 'one' : 'other';
    },
    os: a,
    osa: e,
    pa: b,
    pap: a,
    pcm: c,
    pl: function pl(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          v0 = !s[1],
          i10 = i.slice(-1),
          i100 = i.slice(-2);
      if (ord) return 'other';
      return n == 1 && v0 ? 'one' : v0 && i10 >= 2 && i10 <= 4 && (i100 < 12 || i100 > 14) ? 'few' : v0 && i != 1 && (i10 == 0 || i10 == 1) || v0 && i10 >= 5 && i10 <= 9 || v0 && i100 >= 12 && i100 <= 14 ? 'many' : 'other';
    },
    prg: function prg(n, ord) {
      var s = String(n).split('.'),
          f = s[1] || '',
          v = f.length,
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1),
          n100 = t0 && s[0].slice(-2),
          f100 = f.slice(-2),
          f10 = f.slice(-1);
      if (ord) return 'other';
      return t0 && n10 == 0 || n100 >= 11 && n100 <= 19 || v == 2 && f100 >= 11 && f100 <= 19 ? 'zero' : n10 == 1 && n100 != 11 || v == 2 && f10 == 1 && f100 != 11 || v != 2 && f10 == 1 ? 'one' : 'other';
    },
    ps: a,
    pt: function pt(n, ord) {
      var s = String(n).split('.'),
          i = s[0];
      if (ord) return 'other';
      return i == 0 || i == 1 ? 'one' : 'other';
    },
    pt_PT: d,
    rm: a,
    ro: function ro(n, ord) {
      var s = String(n).split('.'),
          v0 = !s[1],
          t0 = Number(s[0]) == n,
          n100 = t0 && s[0].slice(-2);
      if (ord) return n == 1 ? 'one' : 'other';
      return n == 1 && v0 ? 'one' : !v0 || n == 0 || n100 >= 2 && n100 <= 19 ? 'few' : 'other';
    },
    rof: a,
    root: e,
    ru: function ru(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          v0 = !s[1],
          i10 = i.slice(-1),
          i100 = i.slice(-2);
      if (ord) return 'other';
      return v0 && i10 == 1 && i100 != 11 ? 'one' : v0 && i10 >= 2 && i10 <= 4 && (i100 < 12 || i100 > 14) ? 'few' : v0 && i10 == 0 || v0 && i10 >= 5 && i10 <= 9 || v0 && i100 >= 11 && i100 <= 14 ? 'many' : 'other';
    },
    rwk: a,
    sah: e,
    saq: a,
    sat: f,
    sc: function sc(n, ord) {
      var s = String(n).split('.'),
          v0 = !s[1];
      if (ord) return n == 11 || n == 8 || n == 80 || n == 800 ? 'many' : 'other';
      return n == 1 && v0 ? 'one' : 'other';
    },
    scn: function scn(n, ord) {
      var s = String(n).split('.'),
          v0 = !s[1];
      if (ord) return n == 11 || n == 8 || n == 80 || n == 800 ? 'many' : 'other';
      return n == 1 && v0 ? 'one' : 'other';
    },
    sd: a,
    sdh: a,
    se: f,
    seh: a,
    ses: e,
    sg: e,
    sh: function sh(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '',
          v0 = !s[1],
          i10 = i.slice(-1),
          i100 = i.slice(-2),
          f10 = f.slice(-1),
          f100 = f.slice(-2);
      if (ord) return 'other';
      return v0 && i10 == 1 && i100 != 11 || f10 == 1 && f100 != 11 ? 'one' : v0 && i10 >= 2 && i10 <= 4 && (i100 < 12 || i100 > 14) || f10 >= 2 && f10 <= 4 && (f100 < 12 || f100 > 14) ? 'few' : 'other';
    },
    shi: function shi(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n;
      if (ord) return 'other';
      return n >= 0 && n <= 1 ? 'one' : t0 && n >= 2 && n <= 10 ? 'few' : 'other';
    },
    si: function si(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '';
      if (ord) return 'other';
      return n == 0 || n == 1 || i == 0 && f == 1 ? 'one' : 'other';
    },
    sk: function sk(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          v0 = !s[1];
      if (ord) return 'other';
      return n == 1 && v0 ? 'one' : i >= 2 && i <= 4 && v0 ? 'few' : !v0 ? 'many' : 'other';
    },
    sl: function sl(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          v0 = !s[1],
          i100 = i.slice(-2);
      if (ord) return 'other';
      return v0 && i100 == 1 ? 'one' : v0 && i100 == 2 ? 'two' : v0 && (i100 == 3 || i100 == 4) || !v0 ? 'few' : 'other';
    },
    sma: f,
    smi: f,
    smj: f,
    smn: f,
    sms: f,
    sn: a,
    so: a,
    sq: function sq(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1),
          n100 = t0 && s[0].slice(-2);
      if (ord) return n == 1 ? 'one' : n10 == 4 && n100 != 14 ? 'many' : 'other';
      return n == 1 ? 'one' : 'other';
    },
    sr: function sr(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '',
          v0 = !s[1],
          i10 = i.slice(-1),
          i100 = i.slice(-2),
          f10 = f.slice(-1),
          f100 = f.slice(-2);
      if (ord) return 'other';
      return v0 && i10 == 1 && i100 != 11 || f10 == 1 && f100 != 11 ? 'one' : v0 && i10 >= 2 && i10 <= 4 && (i100 < 12 || i100 > 14) || f10 >= 2 && f10 <= 4 && (f100 < 12 || f100 > 14) ? 'few' : 'other';
    },
    ss: a,
    ssy: a,
    st: a,
    su: e,
    sv: function sv(n, ord) {
      var s = String(n).split('.'),
          v0 = !s[1],
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1),
          n100 = t0 && s[0].slice(-2);
      if (ord) return (n10 == 1 || n10 == 2) && n100 != 11 && n100 != 12 ? 'one' : 'other';
      return n == 1 && v0 ? 'one' : 'other';
    },
    sw: d,
    syr: a,
    ta: a,
    te: a,
    teo: a,
    th: e,
    ti: b,
    tig: a,
    tk: function tk(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1);
      if (ord) return n10 == 6 || n10 == 9 || n == 10 ? 'few' : 'other';
      return n == 1 ? 'one' : 'other';
    },
    tl: function tl(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          f = s[1] || '',
          v0 = !s[1],
          i10 = i.slice(-1),
          f10 = f.slice(-1);
      if (ord) return n == 1 ? 'one' : 'other';
      return v0 && (i == 1 || i == 2 || i == 3) || v0 && i10 != 4 && i10 != 6 && i10 != 9 || !v0 && f10 != 4 && f10 != 6 && f10 != 9 ? 'one' : 'other';
    },
    tn: a,
    to: e,
    tr: a,
    ts: a,
    tzm: function tzm(n, ord) {
      var s = String(n).split('.'),
          t0 = Number(s[0]) == n;
      if (ord) return 'other';
      return n == 0 || n == 1 || t0 && n >= 11 && n <= 99 ? 'one' : 'other';
    },
    ug: a,
    uk: function uk(n, ord) {
      var s = String(n).split('.'),
          i = s[0],
          v0 = !s[1],
          t0 = Number(s[0]) == n,
          n10 = t0 && s[0].slice(-1),
          n100 = t0 && s[0].slice(-2),
          i10 = i.slice(-1),
          i100 = i.slice(-2);
      if (ord) return n10 == 3 && n100 != 13 ? 'few' : 'other';
      return v0 && i10 == 1 && i100 != 11 ? 'one' : v0 && i10 >= 2 && i10 <= 4 && (i100 < 12 || i100 > 14) ? 'few' : v0 && i10 == 0 || v0 && i10 >= 5 && i10 <= 9 || v0 && i100 >= 11 && i100 <= 14 ? 'many' : 'other';
    },
    ur: d,
    uz: a,
    ve: a,
    vi: function vi(n, ord) {
      if (ord) return n == 1 ? 'one' : 'other';
      return 'other';
    },
    vo: a,
    vun: a,
    wa: b,
    wae: a,
    wo: e,
    xh: a,
    xog: a,
    yi: d,
    yo: e,
    yue: e,
    zh: e,
    zu: c
  });
})(plurals$1);

var plurals = /*@__PURE__*/getDefaultExportFromCjs(plurals$1.exports);

var P = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.assign(/*#__PURE__*/Object.create(null), plurals$1.exports, {
  'default': plurals
}));

var pluralCategories$1 = {exports: {}};

(function (module, exports) {
  var z = "zero",
      o = "one",
      t = "two",
      f = "few",
      m = "many",
      x = "other";
  var a = {
    cardinal: [o, x],
    ordinal: [x]
  };
  var b = {
    cardinal: [x],
    ordinal: [x]
  };
  var c = {
    cardinal: [o, f, m, x],
    ordinal: [x]
  };
  var d = {
    cardinal: [o, x],
    ordinal: [o, x]
  };
  var e = {
    cardinal: [o, t, x],
    ordinal: [x]
  };

  (function (root, pluralCategories) {
    Object.defineProperty(pluralCategories, '__esModule', {
      value: true
    });
    module.exports = pluralCategories;
  })(commonjsGlobal, {
    _in: b,
    af: a,
    ak: a,
    am: a,
    an: a,
    ar: {
      cardinal: [z, o, t, f, m, x],
      ordinal: [x]
    },
    ars: {
      cardinal: [z, o, t, f, m, x],
      ordinal: [x]
    },
    as: {
      cardinal: [o, x],
      ordinal: [o, t, f, m, x]
    },
    asa: a,
    ast: a,
    az: {
      cardinal: [o, x],
      ordinal: [o, f, m, x]
    },
    be: {
      cardinal: [o, f, m, x],
      ordinal: [f, x]
    },
    bem: a,
    bez: a,
    bg: a,
    bho: a,
    bm: b,
    bn: {
      cardinal: [o, x],
      ordinal: [o, t, f, m, x]
    },
    bo: b,
    br: {
      cardinal: [o, t, f, m, x],
      ordinal: [x]
    },
    brx: a,
    bs: {
      cardinal: [o, f, x],
      ordinal: [x]
    },
    ca: {
      cardinal: [o, x],
      ordinal: [o, t, f, x]
    },
    ce: a,
    ceb: a,
    cgg: a,
    chr: a,
    ckb: a,
    cs: c,
    cy: {
      cardinal: [z, o, t, f, m, x],
      ordinal: [z, o, t, f, m, x]
    },
    da: a,
    de: a,
    doi: a,
    dsb: {
      cardinal: [o, t, f, x],
      ordinal: [x]
    },
    dv: a,
    dz: b,
    ee: a,
    el: a,
    en: {
      cardinal: [o, x],
      ordinal: [o, t, f, x]
    },
    eo: a,
    es: a,
    et: a,
    eu: a,
    fa: a,
    ff: a,
    fi: a,
    fil: d,
    fo: a,
    fr: {
      cardinal: [o, m, x],
      ordinal: [o, x]
    },
    fur: a,
    fy: a,
    ga: {
      cardinal: [o, t, f, m, x],
      ordinal: [o, x]
    },
    gd: {
      cardinal: [o, t, f, x],
      ordinal: [o, t, f, x]
    },
    gl: a,
    gsw: a,
    gu: {
      cardinal: [o, x],
      ordinal: [o, t, f, m, x]
    },
    guw: a,
    gv: {
      cardinal: [o, t, f, m, x],
      ordinal: [x]
    },
    ha: a,
    haw: a,
    he: {
      cardinal: [o, t, m, x],
      ordinal: [x]
    },
    hi: {
      cardinal: [o, x],
      ordinal: [o, t, f, m, x]
    },
    hr: {
      cardinal: [o, f, x],
      ordinal: [x]
    },
    hsb: {
      cardinal: [o, t, f, x],
      ordinal: [x]
    },
    hu: d,
    hy: d,
    ia: a,
    id: b,
    ig: b,
    ii: b,
    io: a,
    is: a,
    it: {
      cardinal: [o, x],
      ordinal: [m, x]
    },
    iu: e,
    iw: {
      cardinal: [o, t, m, x],
      ordinal: [x]
    },
    ja: b,
    jbo: b,
    jgo: a,
    ji: a,
    jmc: a,
    jv: b,
    jw: b,
    ka: {
      cardinal: [o, x],
      ordinal: [o, m, x]
    },
    kab: a,
    kaj: a,
    kcg: a,
    kde: b,
    kea: b,
    kk: {
      cardinal: [o, x],
      ordinal: [m, x]
    },
    kkj: a,
    kl: a,
    km: b,
    kn: a,
    ko: b,
    ks: a,
    ksb: a,
    ksh: {
      cardinal: [z, o, x],
      ordinal: [x]
    },
    ku: a,
    kw: {
      cardinal: [z, o, t, f, m, x],
      ordinal: [o, m, x]
    },
    ky: a,
    lag: {
      cardinal: [z, o, x],
      ordinal: [x]
    },
    lb: a,
    lg: a,
    lij: {
      cardinal: [o, x],
      ordinal: [m, x]
    },
    lkt: b,
    ln: a,
    lo: {
      cardinal: [x],
      ordinal: [o, x]
    },
    lt: c,
    lv: {
      cardinal: [z, o, x],
      ordinal: [x]
    },
    mas: a,
    mg: a,
    mgo: a,
    mk: {
      cardinal: [o, x],
      ordinal: [o, t, m, x]
    },
    ml: a,
    mn: a,
    mo: {
      cardinal: [o, f, x],
      ordinal: [o, x]
    },
    mr: {
      cardinal: [o, x],
      ordinal: [o, t, f, x]
    },
    ms: {
      cardinal: [x],
      ordinal: [o, x]
    },
    mt: c,
    my: b,
    nah: a,
    naq: e,
    nb: a,
    nd: a,
    ne: d,
    nl: a,
    nn: a,
    nnh: a,
    no: a,
    nqo: b,
    nr: a,
    nso: a,
    ny: a,
    nyn: a,
    om: a,
    or: {
      cardinal: [o, x],
      ordinal: [o, t, f, m, x]
    },
    os: a,
    osa: b,
    pa: a,
    pap: a,
    pcm: a,
    pl: c,
    prg: {
      cardinal: [z, o, x],
      ordinal: [x]
    },
    ps: a,
    pt: a,
    pt_PT: a,
    rm: a,
    ro: {
      cardinal: [o, f, x],
      ordinal: [o, x]
    },
    rof: a,
    root: b,
    ru: c,
    rwk: a,
    sah: b,
    saq: a,
    sat: e,
    sc: {
      cardinal: [o, x],
      ordinal: [m, x]
    },
    scn: {
      cardinal: [o, x],
      ordinal: [m, x]
    },
    sd: a,
    sdh: a,
    se: e,
    seh: a,
    ses: b,
    sg: b,
    sh: {
      cardinal: [o, f, x],
      ordinal: [x]
    },
    shi: {
      cardinal: [o, f, x],
      ordinal: [x]
    },
    si: a,
    sk: c,
    sl: {
      cardinal: [o, t, f, x],
      ordinal: [x]
    },
    sma: e,
    smi: e,
    smj: e,
    smn: e,
    sms: e,
    sn: a,
    so: a,
    sq: {
      cardinal: [o, x],
      ordinal: [o, m, x]
    },
    sr: {
      cardinal: [o, f, x],
      ordinal: [x]
    },
    ss: a,
    ssy: a,
    st: a,
    su: b,
    sv: d,
    sw: a,
    syr: a,
    ta: a,
    te: a,
    teo: a,
    th: b,
    ti: a,
    tig: a,
    tk: {
      cardinal: [o, x],
      ordinal: [f, x]
    },
    tl: d,
    tn: a,
    to: b,
    tr: a,
    ts: a,
    tzm: a,
    ug: a,
    uk: {
      cardinal: [o, f, m, x],
      ordinal: [f, x]
    },
    ur: a,
    uz: a,
    ve: a,
    vi: {
      cardinal: [x],
      ordinal: [o, x]
    },
    vo: a,
    vun: a,
    wa: a,
    wae: a,
    wo: b,
    xh: a,
    xog: a,
    yi: a,
    yo: b,
    yue: b,
    zh: b,
    zu: a
  });
})(pluralCategories$1);

var pluralCategories = /*@__PURE__*/getDefaultExportFromCjs(pluralCategories$1.exports);

var C = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.assign(/*#__PURE__*/Object.create(null), pluralCategories$1.exports, {
  'default': pluralCategories
}));

// using them here because with this many small functions, bundlers produce less
// cruft than for ES module exports.

var Plurals = plurals || P;
var Categories = pluralCategories || C;
/* istanbul ignore next */

var NumberFormat = (typeof Intl === "undefined" ? "undefined" : _typeof(Intl)) === 'object' && Intl.NumberFormat || PseudoNumberFormat__default['default']; // make-plural exports are cast with safe-identifier to be valid JS identifiers

var id = function id(lc) {
  return lc === 'in' ? '_in' : lc === 'pt-PT' ? 'pt_PT' : lc;
};

var getSelector = function getSelector(lc) {
  return Plurals[id(lc)];
};

var getCategories = function getCategories(lc, ord) {
  return Categories[id(lc)][ord ? 'ordinal' : 'cardinal'];
};

var PluralRules = getPluralRules__default['default'](NumberFormat, getSelector, getCategories);

module.exports = PluralRules;


/***/ }),

/***/ "./node_modules/intl-pluralrules/polyfill.js":
/*!***************************************************!*\
  !*** ./node_modules/intl-pluralrules/polyfill.js ***!
  \***************************************************/
/***/ (function(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {



var PluralRules = __webpack_require__(/*! ./plural-rules */ "./node_modules/intl-pluralrules/plural-rules.js");

function _interopDefaultLegacy (e) { return e && typeof e === 'object' && 'default' in e ? e : { 'default': e }; }

var PluralRules__default = /*#__PURE__*/_interopDefaultLegacy(PluralRules);

if (typeof Intl === 'undefined') {
  if (typeof __webpack_require__.g !== 'undefined') {
    __webpack_require__.g.Intl = {
      PluralRules: PluralRules__default['default']
    };
  } else if (typeof window !== 'undefined') {
    window.Intl = {
      PluralRules: PluralRules__default['default']
    };
  } else {
    this.Intl = {
      PluralRules: PluralRules__default['default']
    };
  }

  PluralRules__default['default'].polyfill = true;
} else if (!Intl.PluralRules) {
  Intl.PluralRules = PluralRules__default['default'];
  PluralRules__default['default'].polyfill = true;
} else {
  var test = ['en', 'es', 'ru', 'zh'];
  var supported = Intl.PluralRules.supportedLocalesOf(test);

  if (supported.length < test.length) {
    Intl.PluralRules = PluralRules__default['default'];
    PluralRules__default['default'].polyfill = true;
  }
}


/***/ }),

/***/ "./node_modules/intl-pluralrules/pseudo-number-format.js":
/*!***************************************************************!*\
  !*** ./node_modules/intl-pluralrules/pseudo-number-format.js ***!
  \***************************************************************/
/***/ ((module) => {



function _classCallCheck(instance, Constructor) {
  if (!(instance instanceof Constructor)) {
    throw new TypeError("Cannot call a class as a function");
  }
}

function _defineProperties(target, props) {
  for (var i = 0; i < props.length; i++) {
    var descriptor = props[i];
    descriptor.enumerable = descriptor.enumerable || false;
    descriptor.configurable = true;
    if ("value" in descriptor) descriptor.writable = true;
    Object.defineProperty(target, descriptor.key, descriptor);
  }
}

function _createClass(Constructor, protoProps, staticProps) {
  if (protoProps) _defineProperties(Constructor.prototype, protoProps);
  if (staticProps) _defineProperties(Constructor, staticProps);
  return Constructor;
}

var PseudoNumberFormat = /*#__PURE__*/function () {
  function PseudoNumberFormat(lc, // locale is ignored; always use 'en'
  _ref) {
    var minID = _ref.minimumIntegerDigits,
        minFD = _ref.minimumFractionDigits,
        maxFD = _ref.maximumFractionDigits,
        minSD = _ref.minimumSignificantDigits,
        maxSD = _ref.maximumSignificantDigits;

    _classCallCheck(this, PseudoNumberFormat);

    this._minID = typeof minID === 'number' ? minID : 1;
    this._minFD = typeof minFD === 'number' ? minFD : 0;
    this._maxFD = typeof maxFD === 'number' ? maxFD : Math.max(this._minFD, 3);

    if (typeof minSD === 'number' || typeof maxSD === 'number') {
      this._minSD = typeof minSD === 'number' ? minSD : 1;
      this._maxSD = typeof maxSD === 'number' ? maxSD : 21;
    }
  }

  _createClass(PseudoNumberFormat, [{
    key: "resolvedOptions",
    value: function resolvedOptions() {
      var opt = {
        minimumIntegerDigits: this._minID,
        minimumFractionDigits: this._minFD,
        maximumFractionDigits: this._maxFD
      };

      if (typeof this._minSD === 'number') {
        opt.minimumSignificantDigits = this._minSD;
        opt.maximumSignificantDigits = this._maxSD;
      }

      return opt;
    }
  }, {
    key: "format",
    value: function format(n) {
      if (this._minSD) {
        var raw = String(n);
        var prec = 0;

        for (var i = 0; i < raw.length; ++i) {
          var c = raw[i];
          if (c >= '0' && c <= '9') ++prec;
        }

        if (prec < this._minSD) return n.toPrecision(this._minSD);
        if (prec > this._maxSD) return n.toPrecision(this._maxSD);
        return raw;
      }

      if (this._minFD > 0) return n.toFixed(this._minFD);
      if (this._maxFD === 0) return n.toFixed(0);
      return String(n);
    }
  }]);

  return PseudoNumberFormat;
}();

module.exports = PseudoNumberFormat;


/***/ }),

/***/ "./node_modules/intl-pluralrules/factory.mjs":
/*!***************************************************!*\
  !*** ./node_modules/intl-pluralrules/factory.mjs ***!
  \***************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ getPluralRules)
/* harmony export */ });
function _typeof(obj) {
  "@babel/helpers - typeof";

  if (typeof Symbol === "function" && typeof Symbol.iterator === "symbol") {
    _typeof = function (obj) {
      return typeof obj;
    };
  } else {
    _typeof = function (obj) {
      return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj;
    };
  }

  return _typeof(obj);
}

function _classCallCheck(instance, Constructor) {
  if (!(instance instanceof Constructor)) {
    throw new TypeError("Cannot call a class as a function");
  }
}

function _defineProperties(target, props) {
  for (var i = 0; i < props.length; i++) {
    var descriptor = props[i];
    descriptor.enumerable = descriptor.enumerable || false;
    descriptor.configurable = true;
    if ("value" in descriptor) descriptor.writable = true;
    Object.defineProperty(target, descriptor.key, descriptor);
  }
}

function _createClass(Constructor, protoProps, staticProps) {
  if (protoProps) _defineProperties(Constructor.prototype, protoProps);
  if (staticProps) _defineProperties(Constructor, staticProps);
  return Constructor;
}

// does not check for duplicate subtags
var isStructurallyValidLanguageTag = function isStructurallyValidLanguageTag(locale) {
  return locale.split('-').every(function (subtag) {
    return /[a-z0-9]+/i.test(subtag);
  });
};

var canonicalizeLocaleList = function canonicalizeLocaleList(locales) {
  if (!locales) return [];
  if (!Array.isArray(locales)) locales = [locales];
  var res = {};

  for (var i = 0; i < locales.length; ++i) {
    var tag = locales[i];
    if (tag && _typeof(tag) === 'object') tag = String(tag);

    if (typeof tag !== 'string') {
      // Requiring tag to be a String or Object means that the Number value
      // NaN will not be interpreted as the language tag "nan", which stands
      // for Min Nan Chinese.
      var msg = "Locales should be strings, ".concat(JSON.stringify(tag), " isn't.");
      throw new TypeError(msg);
    }

    if (tag[0] === '*') continue;

    if (!isStructurallyValidLanguageTag(tag)) {
      var strTag = JSON.stringify(tag);

      var _msg = "The locale ".concat(strTag, " is not a structurally valid BCP 47 language tag.");

      throw new RangeError(_msg);
    }

    res[tag] = true;
  }

  return Object.keys(res);
};

var defaultLocale = function defaultLocale() {
  return (
    /* istanbul ignore next */
    typeof navigator !== 'undefined' && navigator && (navigator.userLanguage || navigator.language) || 'en-US'
  );
};

var getType = function getType(type) {
  if (!type) return 'cardinal';
  if (type === 'cardinal' || type === 'ordinal') return type;
  throw new RangeError('Not a valid plural type: ' + JSON.stringify(type));
};

function getPluralRules(NumberFormat, getSelector, getCategories) {
  var findLocale = function findLocale(locale) {
    do {
      if (getSelector(locale)) return locale;
      locale = locale.replace(/-?[^-]*$/, '');
    } while (locale);

    return null;
  };

  var resolveLocale = function resolveLocale(locales) {
    var canonicalLocales = canonicalizeLocaleList(locales);

    for (var i = 0; i < canonicalLocales.length; ++i) {
      var lc = findLocale(canonicalLocales[i]);
      if (lc) return lc;
    }

    return findLocale(defaultLocale());
  };

  var PluralRules = /*#__PURE__*/function () {
    function PluralRules(locales) {
      var opt = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};

      _classCallCheck(this, PluralRules);

      this._locale = resolveLocale(locales);
      this._select = getSelector(this._locale);
      this._type = getType(opt.type);
      this._nf = new NumberFormat('en', opt); // make-plural expects latin digits with . decimal separator
    }

    _createClass(PluralRules, [{
      key: "resolvedOptions",
      value: function resolvedOptions() {
        var _this$_nf$resolvedOpt = this._nf.resolvedOptions(),
            minimumIntegerDigits = _this$_nf$resolvedOpt.minimumIntegerDigits,
            minimumFractionDigits = _this$_nf$resolvedOpt.minimumFractionDigits,
            maximumFractionDigits = _this$_nf$resolvedOpt.maximumFractionDigits,
            minimumSignificantDigits = _this$_nf$resolvedOpt.minimumSignificantDigits,
            maximumSignificantDigits = _this$_nf$resolvedOpt.maximumSignificantDigits;

        var opt = {
          locale: this._locale,
          minimumIntegerDigits: minimumIntegerDigits,
          minimumFractionDigits: minimumFractionDigits,
          maximumFractionDigits: maximumFractionDigits,
          pluralCategories: getCategories(this._locale, this._type === 'ordinal'),
          type: this._type
        };

        if (typeof minimumSignificantDigits === 'number') {
          opt.minimumSignificantDigits = minimumSignificantDigits;
          opt.maximumSignificantDigits = maximumSignificantDigits;
        }

        return opt;
      }
    }, {
      key: "select",
      value: function select(number) {
        if (!(this instanceof PluralRules)) throw new TypeError("select() called on incompatible ".concat(this));
        if (typeof number !== 'number') number = Number(number);
        if (!isFinite(number)) return 'other';

        var fmt = this._nf.format(Math.abs(number));

        return this._select(fmt, this._type === 'ordinal');
      }
    }], [{
      key: "supportedLocalesOf",
      value: function supportedLocalesOf(locales) {
        return canonicalizeLocaleList(locales).filter(findLocale);
      }
    }]);

    return PluralRules;
  }();

  Object.defineProperty(PluralRules, 'prototype', {
    writable: false
  });
  return PluralRules;
}




/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			id: moduleId,
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/compat get default export */
/******/ 	(() => {
/******/ 		// getDefaultExport function for compatibility with non-harmony modules
/******/ 		__webpack_require__.n = (module) => {
/******/ 			var getter = module && module.__esModule ?
/******/ 				() => (module['default']) :
/******/ 				() => (module);
/******/ 			__webpack_require__.d(getter, { a: getter });
/******/ 			return getter;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/global */
/******/ 	(() => {
/******/ 		__webpack_require__.g = (function() {
/******/ 			if (typeof globalThis === 'object') return globalThis;
/******/ 			try {
/******/ 				return this || new Function('return this')();
/******/ 			} catch (e) {
/******/ 				if (typeof window === 'object') return window;
/******/ 			}
/******/ 		})();
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/nonce */
/******/ 	(() => {
/******/ 		__webpack_require__.nc = undefined;
/******/ 	})();
/******/ 	
/************************************************************************/
var __webpack_exports__ = {};
// This entry need to be wrapped in an IIFE because it need to be isolated against other modules in the chunk.
(() => {
var exports = __webpack_exports__;
/*!***************************************************************!*\
  !*** ./tsundoku/blueprints/ux/static/ts/PageWebhooks/App.tsx ***!
  \***************************************************************/

Object.defineProperty(exports, "__esModule", ({ value: true }));
const fluent_1 = __webpack_require__(/*! ../fluent */ "./tsundoku/blueprints/ux/static/ts/fluent.ts");
__webpack_require__(/*! bulma-dashboard/dist/bulma-dashboard.min.css */ "./node_modules/bulma-dashboard/dist/bulma-dashboard.min.css");
__webpack_require__(/*! ../../css/webhooks.css */ "./tsundoku/blueprints/ux/static/css/webhooks.css");
let resources = [
    "webhooks"
];
const _ = (0, fluent_1.getInjector)(resources);
function submitAddWebhookForm(event) {
    event.preventDefault();
    let url = $(this).closest("form").attr("action");
    let method = $(this).closest("form").attr("method");
    let data = $(this).closest("form").serialize();
    $.ajax({
        url: url,
        type: method,
        data: data,
        success: function (data) {
            location.reload();
        },
        error: function (jqXHR, status, error) {
            alert("There was an error processing the request.");
        }
    });
}
function openAddWebhookModal() {
    let form = $("#add-webhook-form");
    form.attr("action", "/api/v1/webhooks");
    form.attr("method", "POST");
    form.on("submit", submitAddWebhookForm);
    $(document.documentElement).addClass("is-clipped");
    $("#add-webhook-modal").addClass("is-active");
}
;
function openEditWebhookModal(webhook) {
    let form = $("#edit-webhook-form");
    form.trigger("reset");
    $("#edit-webhook-form :input").each(function (i, elem) {
        let name = $(elem).attr("name");
        $(elem).val(webhook[name]);
    });
    form.attr("method", "PUT");
    form.attr("action", `/api/v1/webhooks/${webhook.base_id}`);
    form.on("submit", submitAddWebhookForm);
    $(document.documentElement).addClass("is-clipped");
    $("#edit-webhook-modal").addClass("is-active");
}
function openDeleteWebhookModal(webhook) {
    $("#delete-webhook-button").on("click", function (e) {
        e.preventDefault();
        $.ajax({
            url: `/api/v1/webhooks/${webhook.base_id}`,
            type: "DELETE",
            success: function () {
                location.reload();
            }
        });
    });
    $("#delete-confirm-text").html(_("delete-confirm-text", { "name": webhook.name }));
    $(document.documentElement).addClass("is-clipped");
    $("#delete-webhook-modal").addClass("is-active");
}
function closeWebhookModals() {
    $(".modal").removeClass("is-active");
    $(document.documentElement).removeClass("is-clipped");
}
$(function () {
    $('.notification .delete').each(function () {
        $(this).on("click", function () {
            $(this).parent().remove();
        });
    });
    $("#navWebhooks").addClass("is-active");
});
// PATCHES
window.openAddWebhookModal = openAddWebhookModal;
window.openEditWebhookModal = openEditWebhookModal;
window.openDeleteWebhookModal = openDeleteWebhookModal;
window.closeWebhookModals = closeWebhookModals;

})();

/******/ })()
;
//# sourceMappingURL=webhooks.js.map