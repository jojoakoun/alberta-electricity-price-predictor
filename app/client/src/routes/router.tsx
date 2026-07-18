import {
  createBrowserRouter,
} from "react-router";

import { AppLayout } from "../layout/AppLayout";
import { LearnPage } from "../pages/LearnPage";
import { NowPage } from "../pages/NowPage";
import { TodayPage } from "../pages/TodayPage";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      {
        path: "/",
        element: <NowPage />,
      },
      {
        path: "/today",
        element: <TodayPage />,
      },
      {
        path: "/learn",
        element: <LearnPage />,
      },
    ],
  },
]);
