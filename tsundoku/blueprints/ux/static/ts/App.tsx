import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { toast } from "bulma-toast";
import * as React from "react";
import { createRoot, type Root } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { ZodError } from "zod";
import { ErrorBoundary, RouteErrorBoundary } from "./Components/ErrorBoundary";
import { ConfigApp } from "./PageConfig/App";
import { IndexApp } from "./PageIndex/App";
import { LogsApp } from "./PageLogs/App";
import { WebhooksApp } from "./PageWebhooks/App";

import "bulma/css/bulma.min.css";
import "bulma-dashboard/dist/bulma-dashboard.min.css";
// `switch` is the only class we use that bulma core does not already provide;
// the `has-tooltip-*` classes come from the @creativebulma/bulma-tooltip CDN
// link in base.html, not from here. It is compiled from Sass in styles.scss --
// see the note there. Importing the combined extensions bundle instead would
// pull in bulma-steps, whose `.step-item::before .step-marker` selector is
// invalid CSS and hard-fails the Lightning CSS minifier.

import "../css/styles.scss";
import { APIError } from "./errors";

const router = createBrowserRouter([
  {
    path: "/",
    element: <IndexApp />,
    errorElement: <RouteErrorBoundary />,
  },
  {
    path: "/webhooks",
    element: <WebhooksApp />,
    errorElement: <RouteErrorBoundary />,
  },
  {
    path: "/config",
    element: <ConfigApp />,
    errorElement: <RouteErrorBoundary />,
  },
  {
    path: "/logs",
    element: <LogsApp />,
    errorElement: <RouteErrorBoundary />,
  },
]);

// Long enough to be useful, short enough that no error can take over the page.
const MAX_TOAST_CHARS = 180;

const truncate = (text: string) =>
  text.length > MAX_TOAST_CHARS
    ? `${text.slice(0, MAX_TOAST_CHARS - 1)}\u2026`
    : text;

/**
 * Reduces an error to something a toast can show.
 *
 * ZodError.message is a JSON dump of every issue, so a response that fails
 * validation on hundreds of rows produces tens of thousands of characters --
 * bulma-toast renders that verbatim and it covers the whole page. The full
 * error still goes to the console.
 */
const summarizeError = (error: Error): [string, string | null] => {
  if (error instanceof ZodError) {
    const count = error.issues.length;
    const first = error.issues[0];
    const where = first?.path?.length ? first.path.join(".") : "response";

    return [
      `Server response did not match the expected shape (${count} ${
        count === 1 ? "problem" : "problems"
      }).`,
      first ? truncate(`${where}: ${first.message}`) : null,
    ];
  }

  return [truncate(error.message), null];
};

const displayErrorToast = (text: string, subtext: string | null = null) => {
  toast({
    message: truncate(text) + (subtext ? `\n${truncate(subtext)}` : ""),
    duration: 5000,
    position: "bottom-right",
    type: "is-danger",
    dismissible: true,
    animate: { in: "fadeIn", out: "fadeOut" },
  });
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
  mutationCache: new MutationCache({
    onError: (error: unknown) => {
      if (error instanceof APIError)
        displayErrorToast(error.message, error.subtext);
      else if (error instanceof Error) {
        console.error(error);
        displayErrorToast(...summarizeError(error));
      } else displayErrorToast("An error occurred.");
    },
  }),
  queryCache: new QueryCache({
    onError: (error: unknown) => {
      if (error instanceof APIError)
        displayErrorToast(error.message, error.subtext);
      else if (error instanceof Error) {
        console.error(error);
        displayErrorToast(...summarizeError(error));
      } else displayErrorToast("An error occurred.");
    },
  }),
});

const RootApp = () => {
  return (
    <React.StrictMode>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      </ErrorBoundary>
    </React.StrictMode>
  );
};

// This module has no exports, so react-refresh cannot hot-update it and Vite
// re-executes it instead. Creating a second root over the same container would
// leave two React trees reconciling the same DOM, which surfaces as
// "removeChild: The node to be removed is not a child of this node" the next
// time any subtree unmounts. Reuse the existing root instead.
type RootContainer = HTMLElement & { _reactRoot?: Root };

const rootElement = document.getElementById("root") as RootContainer | null;
if (rootElement) {
  rootElement._reactRoot ??= createRoot(rootElement);
  rootElement._reactRoot.render(<RootApp />);
}
