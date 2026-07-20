import { useQuery } from "@tanstack/react-query";

import { fetchToday } from "./today";

export const todayQueryKey = ["today"] as const;

export function useTodayQuery() {
  return useQuery({
    queryKey: todayQueryKey,
    queryFn: ({ signal }) => fetchToday(signal),
  });
}
