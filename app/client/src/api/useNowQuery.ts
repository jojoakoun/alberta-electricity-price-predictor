import { useQuery } from "@tanstack/react-query";

import { fetchNow } from "./now";

export const nowQueryKey = ["now"] as const;

export function useNowQuery() {
  return useQuery({
    queryKey: nowQueryKey,
    queryFn: ({ signal }) => fetchNow(signal),
  });
}
