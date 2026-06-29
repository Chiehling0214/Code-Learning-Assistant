import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { AdminPage } from "@/pages/Admin";
import { CodingExercisePage } from "@/pages/CodingExercise";
import { CoursePage } from "@/pages/Course";
import { DashboardPage } from "@/pages/Dashboard";
import { LandingPage } from "@/pages/Landing";
import { LessonPage } from "@/pages/Lesson";
import { LoginPage } from "@/pages/Login";
import { NotFoundPage } from "@/pages/NotFound";
import { ProgressPage } from "@/pages/Progress";
import { QuizPage } from "@/pages/Quiz";
import { SubscriptionPage } from "@/pages/Subscription";
import { TodayPage } from "@/pages/Today";

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  {
    // Routes that share the authenticated app shell (header + nav).
    element: <AppLayout />,
    children: [
      { path: "/dashboard", element: <DashboardPage /> },
      { path: "/today", element: <TodayPage /> },
      { path: "/courses/:slug", element: <CoursePage /> },
      { path: "/lessons/:id", element: <LessonPage /> },
      { path: "/exercises/:id", element: <CodingExercisePage /> },
      { path: "/quizzes/:id", element: <QuizPage /> },
      { path: "/progress", element: <ProgressPage /> },
      { path: "/subscription", element: <SubscriptionPage /> },
      { path: "/admin", element: <AdminPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
