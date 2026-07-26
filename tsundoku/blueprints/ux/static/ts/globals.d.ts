// Ambient declarations. Deliberately no import/export at top level -- that
// would make this a module, and the `virtual:fluent` block below would then be
// read as an augmentation of a module that does not otherwise exist.

// LOCALE is injected into the page by base.html before the bundle runs.
interface Window {
  LOCALE: string;
}

// Provided by the Vite plugin in l10n/VitePluginFluent.mjs: a map of `.ftl`
// file name to contents.
declare module "virtual:fluent" {
  const translations: Record<string, string>;
  export default translations;
}
