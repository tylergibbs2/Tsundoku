import * as React from 'react';

import { hydrate } from "preact";
import { createBrowserRouter, RouterProvider, Route } from "react-router-dom";

import { IndexApp } from "./index/app";
import { NyaaSearchApp } from "./nyaa/app";
import { ConfigApp } from "./config/app";
import { LogsApp } from "./logs/app";

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


const RootApp = () => {
    return (
        <React.StrictMode>
            <RouterProvider router={router} />
        </React.StrictMode>
    )
}

hydrate(<RootApp />, document.getElementById("root")!);
