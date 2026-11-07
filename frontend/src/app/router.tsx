import { createBrowserRouter } from "react-router"
import { lazyPage } from "./lazy-page"
import { RootError } from "./root-error/root-error"
import { RootLayout } from "./root-layout/root-layout"
import { RouteFallback } from "./route-fallback/route-fallback"

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    errorElement: <RootError />,
    hydrateFallbackElement: <RouteFallback />,
    children: [
      { index: true, lazy: lazyPage(() => import("@/pages/home/home-page"), "HomePage") },
      {
        path: "regions",
        lazy: lazyPage(() => import("@/pages/regions/regions-page"), "RegionsPage"),
      },
      {
        path: "regions/:regionId",
        lazy: lazyPage(() => import("@/pages/region/region-page"), "RegionPage"),
      },
      {
        path: "seasons",
        lazy: lazyPage(() => import("@/pages/seasons/seasons-page"), "SeasonsPage"),
      },
      { path: "method", lazy: lazyPage(() => import("@/pages/method/method-page"), "MethodPage") },
      {
        path: "sources",
        lazy: lazyPage(() => import("@/pages/sources/sources-page"), "SourcesPage"),
      },
      {
        path: "*",
        lazy: lazyPage(() => import("@/pages/not-found/not-found-page"), "NotFoundPage"),
      },
    ],
  },
])
