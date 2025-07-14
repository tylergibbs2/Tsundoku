import * as React from "react";

import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "react-query";
import { toast } from "bulma-toast";

import { IndexApp } from "./PageIndex/App";
import { WebhooksApp } from "./PageWebhooks/App";
import { ConfigApp } from "./PageConfig/App";
import { LogsApp } from "./PageLogs/App";

import "bulma/css/bulma.min.css";
import "bulma-dashboard/dist/bulma-dashboard.min.css";
import "bulma-extensions/dist/css/bulma-extensions.min.css";

import "../css/styles.scss";
import { APIError } from "./errors";

const router = createBrowserRouter([
  {
    path: "/",
    element: <IndexApp />,
  },
  {
    path: "/webhooks",
    element: <WebhooksApp />,
  },
  {
    path: "/config",
    element: <ConfigApp />,
  },
  {
    path: "/logs",
    element: <LogsApp />,
  },
]);

const displayErrorToast = (text: string, subtext: string | null = null) => {
  toast({
    message: text + (subtext ? `\n${subtext}` : ""),
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
      else if (error instanceof Error) displayErrorToast(error.message);
      else displayErrorToast("An error occurred.");
    },
  }),
  queryCache: new QueryCache({
    onError: (error: unknown) => {
      if (error instanceof APIError)
        displayErrorToast(error.message, error.subtext);
      else if (error instanceof Error) displayErrorToast(error.message);
      else displayErrorToast("An error occurred.");
    },
  }),
});

const RootApp = () => {
  return (
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </React.StrictMode>
  );
};

const root = createRoot(document.getElementById("root"));
root.render(<RootApp />);
