import "intl-pluralrules";
import translations from "virtual:fluent";
import { FluentBundle, FluentResource } from "@fluent/bundle";

export const getInjector = () => {
  const locale: string = window.LOCALE;

  const bundle = new FluentBundle(locale);
  const fallbackBundle = new FluentBundle("en");

  let key = `${locale}.ftl`;
  let ftl_resource = new FluentResource(translations[key]);
  bundle.addResource(ftl_resource);

  // Fallback to English if the locale is invalid
  key = "en.ftl";
  ftl_resource = new FluentResource(translations[key]);
  fallbackBundle.addResource(ftl_resource);

  const injector = (key: string, ctx: any = {}) => {
    let msg = bundle.getMessage(key);
    if (msg?.value) return bundle.formatPattern(msg.value, ctx);
    else msg = fallbackBundle.getMessage(key);
    if (msg?.value) return fallbackBundle.formatPattern(msg.value, ctx);

    if (typeof msg === "undefined")
      console.error(
        `Key ${key} missing completely from desired and fallback locales.`,
      );
    return key;
  };

  return injector;
};
