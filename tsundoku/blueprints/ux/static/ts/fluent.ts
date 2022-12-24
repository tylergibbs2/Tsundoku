import "intl-pluralrules";
import { FluentBundle, FluentResource } from "@fluent/bundle";

export const getInjector = () => {
  let locale: string = window["LOCALE"];

  let bundle = new FluentBundle(locale);
  let fallbackBundle = new FluentBundle("en");

  let key = `${locale}.ftl`;
  let ftl_resource = new FluentResource(window["TRANSLATIONS"][key]);
  bundle.addResource(ftl_resource);

  // Fallback to English if the locale is invalid
  key = "en.ftl";
  ftl_resource = new FluentResource(window["TRANSLATIONS"][key]);
  fallbackBundle.addResource(ftl_resource);

  let injector = (key: string, ctx: any = {}) => {
    let msg = bundle.getMessage(key);
    if (typeof msg !== "undefined" && msg.value)
      return bundle.formatPattern(msg.value, ctx);
    else msg = fallbackBundle.getMessage(key);
    if (typeof msg !== "undefined" && msg.value)
      return fallbackBundle.formatPattern(msg.value, ctx);

    if (typeof msg === "undefined")
      console.error(
        `Key ${key} missing completely from desired and fallback locales.`
      );
    return key;
  };

  return injector;
};
