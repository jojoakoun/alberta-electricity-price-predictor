import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      refetchInterval: 5 * 60 * 1000,
      refetchIntervalInBackground: false,
      refetchOnWindowFocus: true,
    },
  },
});
