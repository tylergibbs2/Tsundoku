import * as React from 'react';

import { hydrate } from "preact";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "react-query";

import { IndexApp } from "./PageIndex/App";
import { NyaaSearchApp } from "./PageNyaaSearch/App";
import { ConfigApp } from "./PageConfig/App";
import { LogsApp } from "./PageLogs/App";

import "bulma-dashboard/dist/bulma-dashboard.min.css";


const router = createBrowserRouter([
    {
        path: "/",
        element: <IndexApp />
    },
    {
        path: "/nyaa",
        element: <NyaaSearchApp />
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

hydrate(<RootApp />, document.getElementById("root")!);
