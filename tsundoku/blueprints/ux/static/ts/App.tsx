import * as React from 'react';

import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "react-query";

import { IndexApp } from "./PageIndex/App";
import { DiscoverApp } from "./PageDiscover/App";
import { NyaaSearchApp } from "./PageNyaaSearch/App";
import { WebhooksApp } from "./PageWebhooks/App";
import { ConfigApp } from "./PageConfig/App";
import { LogsApp } from "./PageLogs/App";

import "bulma/css/bulma.min.css";
import "bulma-dashboard/dist/bulma-dashboard.min.css";
import "bulma-extensions/dist/css/bulma-extensions.min.css";

import "../css/styles.scss";


const router = createBrowserRouter([
    {
        path: "/",
        element: <IndexApp />
    },
    {
        path: "/discover",
        element: <DiscoverApp />
    },
    {
        path: "/nyaa",
        element: <NyaaSearchApp />
    },
    {
        path: "/webhooks",
        element: <WebhooksApp />
    },
    {
        path: "/config",
        element: <ConfigApp />
    },
    {
        path: "/logs",
        element: <LogsApp />
    }
]);

const queryClient = new QueryClient();

const RootApp = () => {
    return (
        <React.StrictMode>
            <QueryClientProvider client={queryClient}>
                <RouterProvider router={router} />
            </QueryClientProvider>
        </React.StrictMode>
    )
}

const root = createRoot(document.getElementById("root"));
root.render(<RootApp />);
