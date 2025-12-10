import { useCallback, useState } from 'react'

type UsePaginationOptions = {
  initialPage?: number
  initialLimit?: number
}

export const usePagination = (options: UsePaginationOptions = {}) => {
  const { initialPage = 1, initialLimit = 10 } = options
  const [page, setPage] = useState(initialPage)
  const [limit, setLimitState] = useState(initialLimit)

  const offset = (page - 1) * limit

  const nextPage = useCallback(() => setPage((prev) => prev + 1), [])
  const prevPage = useCallback(
    () => setPage((prev) => Math.max(1, prev - 1)),
    [],
  )

  const setLimit = useCallback((value: number) => {
    setLimitState(value)
    setPage(1)
  }, [])

  const reset = useCallback(() => {
    setPage(initialPage)
    setLimitState(initialLimit)
  }, [initialLimit, initialPage])

  return { page, limit, offset, setPage, setLimit, nextPage, prevPage, reset }
}

export type UsePaginationReturn = ReturnType<typeof usePagination>
