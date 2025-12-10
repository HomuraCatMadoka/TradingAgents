import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button, ErrorBlock, Grid, List, SearchBar, Tag } from 'antd-mobile'
import { useNavigate } from 'react-router-dom'
import HistoryTable from '@/components/HistoryTable'
import ProtocolCard from '@/components/ProtocolCard'
import LoadingState from '@/components/LoadingState'
import { listAnalysisHistory } from '@/services/analysis-history'
import { getFavorites } from '@/services/favorites'
import { getList } from '@/services/protocols'
import { getWatchlist } from '@/services/watchlist'
import type { Protocol } from '@/types/protocol'
import styles from './Page.module.css'

const Dashboard = () => {
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')

  const {
    data: protocols = [],
    isLoading: loadingProtocols,
    isError: protocolError,
    refetch: refetchProtocols,
  } = useQuery<Protocol[]>({
    queryKey: ['protocols', 'dashboard', keyword],
    queryFn: () => getList({ search: keyword || undefined, limit: 8 }),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })

  const {
    data: historyData,
    isLoading: loadingHistory,
    isError: historyError,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['analysis-history', 'recent'],
    queryFn: () => listAnalysisHistory({ page: 1, limit: 5 }),
  })

  const {
    data: favorites,
    isError: favoritesError,
    isLoading: loadingFavorites,
    refetch: refetchFavorites,
  } = useQuery({
    queryKey: ['favorites', 'dashboard'],
    queryFn: getFavorites,
  })

  const {
    data: watchlist,
    isError: watchlistError,
    isLoading: loadingWatchlist,
    refetch: refetchWatchlist,
  } = useQuery({
    queryKey: ['watchlist', 'dashboard'],
    queryFn: () => getWatchlist(),
  })

  const stats = useMemo(
    () => ({
      analyses: historyData?.pagination.total ?? 0,
      favorites: favorites?.length ?? 0,
      watchlist: watchlist?.length ?? 0,
    }),
    [favorites?.length, historyData?.pagination.total, watchlist?.length],
  )

  const trending = protocols.slice(0, 4)
  const favoriteProtocols: Protocol[] =
    favorites?.slice(0, 3).map((item) => ({
      id: String(item.id),
      name: item.protocolName,
      slug: item.protocolName,
      chain: item.protocolType ?? undefined,
      isFavorite: true,
    })) ?? []

  const recentHistory = historyData?.data ?? []

  const loadingAll = loadingProtocols && loadingHistory && loadingFavorites && loadingWatchlist

  if (loadingAll) return <LoadingState message="加载仪表盘..." />

  const renderError = () => (
    <div className="space-y-2">
      <ErrorBlock status="default" title="加载失败" description="获取数据时出错，请重试" />
      <Button
        size="small"
        onClick={() => {
          refetchProtocols()
          refetchHistory()
          refetchFavorites()
          refetchWatchlist()
        }}
      >
        重试
      </Button>
    </div>
  )

  if (protocolError && historyError && favoritesError && watchlistError) {
    return renderError()
  }

  return (
    <div className={styles.page}>
      <div className={`${styles.section} flex flex-col gap-3`}>
        <div className={styles.sectionHeader}>
          <div>
            <div className={styles.sectionTitle}>概览</div>
            <div className={styles.sectionSubtitle}>分析次数 / 收藏 / 监控</div>
          </div>
        </div>
        <Grid columns={3} gap={8}>
          <Grid.Item>
            <div className="rounded-xl bg-[var(--tg-bg-color)] p-3 text-sm">
              <div className="text-[var(--tg-muted-text)]">分析次数</div>
              <div className="text-xl font-bold text-[var(--tg-text-color)]">{stats.analyses}</div>
            </div>
          </Grid.Item>
          <Grid.Item>
            <div className="rounded-xl bg-[var(--tg-bg-color)] p-3 text-sm">
              <div className="text-[var(--tg-muted-text)]">收藏数</div>
              <div className="text-xl font-bold text-[var(--tg-text-color)]">
                {stats.favorites}
              </div>
            </div>
          </Grid.Item>
          <Grid.Item>
            <div className="rounded-xl bg-[var(--tg-bg-color)] p-3 text-sm">
              <div className="text-[var(--tg-muted-text)]">监控数</div>
              <div className="text-xl font-bold text-[var(--tg-text-color)]">
                {stats.watchlist}
              </div>
            </div>
          </Grid.Item>
        </Grid>
      </div>

      <div className={`${styles.section} flex flex-col gap-3`}>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className={styles.sectionTitle}>快速搜索</div>
            <div className={styles.sectionSubtitle}>查找协议并跳转详情</div>
          </div>
          <div className="w-full sm:w-1/2">
            <SearchBar
              placeholder="输入协议名称"
              value={keyword}
              onChange={setKeyword}
              showCancelButton
            />
          </div>
        </div>
        {loadingProtocols ? (
          <LoadingState message="加载协议列表..." />
        ) : protocolError ? (
          <ErrorBlock status="default" title="协议列表加载失败" />
        ) : trending.length === 0 ? (
          <ErrorBlock status="empty" title="暂无协议" description="稍后再试或调整搜索" />
        ) : (
          trending.map((protocol) => (
            <ProtocolCard
              key={protocol.id}
              protocol={protocol}
              onClick={(slug) => navigate(`/protocols/${slug}`)}
              subtitle="点击查看详情或开始分析"
            />
          ))
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <div className={styles.sectionTitle}>我的收藏</div>
            <div className={styles.sectionSubtitle}>常看协议</div>
          </div>
          <Button size="mini" onClick={() => navigate('/favorites')}>
            管理收藏
          </Button>
        </div>
        {loadingFavorites ? (
          <LoadingState message="加载收藏..." />
        ) : favoritesError ? (
          renderError()
        ) : favoriteProtocols.length === 0 ? (
          <ErrorBlock status="empty" title="暂无收藏" description="收藏的协议会显示在这里" />
        ) : (
          favoriteProtocols.map((protocol) => (
            <ProtocolCard
              key={protocol.id}
              protocol={protocol}
              onClick={() => navigate(`/protocols/${protocol.slug}`)}
            />
          ))
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitle}>最近分析</div>
          <Button size="mini" onClick={() => navigate('/history')}>
            查看全部
          </Button>
        </div>
        <HistoryTable
          records={recentHistory}
          loading={loadingHistory}
          error={historyError ? '无法获取分析历史' : null}
          onView={(id) => navigate(`/history?id=${id}`)}
        />
      </div>
    </div>
  )
}

export default Dashboard
