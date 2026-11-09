import { createBrowserRouter, Navigate, useLocation } from "react-router"
import { lazyPage } from "./lazy-page"
import { RootError } from "./root-error/root-error"
import { RootLayout } from "./root-layout/root-layout"
import { RouteFallback } from "./route-fallback/route-fallback"

function LegacyMapRedirect() {
  const { search } = useLocation()
  return <Navigate to={{ pathname: "/", search }} replace />
}

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    errorElement: <RootError />,
    hydrateFallbackElement: <RouteFallback />,
    children: [
      { index: true, lazy: lazyPage(() => import("@/pages/map/map-page"), "MapPage") },
      { path: "map", element: <LegacyMapRedirect /> },
      {
        path: "compare",
        lazy: lazyPage(() => import("@/pages/compare/compare-page"), "ComparePage"),
      },
      {
        path: "regions/:regionId",
        lazy: lazyPage(() => import("@/pages/region/region-page"), "RegionPage"),
      },
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
