// Values injected into the page before the bundle runs: LOCALE by base.html,
// TRANSLATIONS by the Vite fluent plugin (see l10n/VitePluginFluent.mjs).
declare global {
  interface Window {
    LOCALE: string;
    TRANSLATIONS: Record<string, string>;
  }
}

export {};
