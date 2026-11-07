import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"

export type Settlement = components["schemas"]["SettlementResponse"]
export type SettlementSort = components["schemas"]["SettlementSort"]
export type SortOrder = components["schemas"]["SortOrder"]
export type SearchResult = components["schemas"]["SearchResponse"]

export interface SettlementQuery {
  readonly regionId: string
  readonly q: string
  readonly sort: SettlementSort
  readonly order: SortOrder
  readonly limit: number
  readonly offset: number
}

export const settlementKeys = {
  page: (query: SettlementQuery) => ["settlements", query] as const,
  search: (q: string) => ["search", q] as const,
}

export function useSettlements(query: SettlementQuery) {
  return useQuery({
    queryKey: settlementKeys.page(query),
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/regions/{region_id}/settlements", {
          params: {
            path: { region_id: query.regionId },
            query: {
              q: query.q,
              sort: query.sort,
              order: query.order,
              limit: query.limit,
              offset: query.offset,
            },
          },
          signal,
        }),
      ),
    placeholderData: keepPreviousData,
  })
}

export function useSearch(q: string) {
  const term = q.trim()
  return useQuery({
    queryKey: settlementKeys.search(term),
    queryFn: ({ signal }) =>
      unwrap(api.GET("/api/v1/search", { params: { query: { q: term, limit: 6 } }, signal })),
    enabled: term.length >= 2,
    placeholderData: keepPreviousData,
  })
}
