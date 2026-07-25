import { useQuery } from "@tanstack/react-query";

import { fetchToday } from "./today";

export const todayQueryKey = Object.freeze(["today"]);

export function useTodayQuery() {
  return useQuery({
    queryKey: todayQueryKey,
    queryFn: ({ signal }) => fetchToday(signal),
  });
}
