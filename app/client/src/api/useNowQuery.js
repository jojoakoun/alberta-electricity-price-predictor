import { useQuery } from "@tanstack/react-query";

import { fetchNow } from "./now";

export const nowQueryKey = Object.freeze(["now"]);

export function useNowQuery() {
  return useQuery({
    queryKey: nowQueryKey,
    queryFn: ({ signal }) => fetchNow(signal),
  });
}
