import { useMemo } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Button, ErrorBlock, Tag, Toast } from 'antd-mobile'
import { useNavigate, useParams } from 'react-router-dom'
import LoadingState from '@/components/LoadingState'
import { getDetail, getMarketData, getPools, triggerAnalysis } from '@/services/protocols'
import type { ProtocolDetail } from '@/types/protocol'
import styles from './Page.module.css'

const ProtocolDetail = () => {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()

  const {
    data: detail,
    isLoading,
    isError,
    refetch,
  } = useQuery<ProtocolDetail>({
    queryKey: ['protocol', slug],
    queryFn: () => getDetail(slug ?? ''),
    enabled: Boolean(slug),
  })

  const { data: marketData } = useQuery({
    queryKey: ['protocol', slug, 'market'],
    queryFn: () => getMarketData(slug ?? ''),
    enabled: Boolean(slug),
  })

  const { data: pools = [] } = useQuery({
    queryKey: ['protocol', slug, 'pools'],
    queryFn: () => getPools(slug ?? '', { limit: 5 }),
    enabled: Boolean(slug),
  })

  const { mutateAsync, isPending, data: analyzeResult } = useMutation({
    mutationFn: () => triggerAnalysis(slug ?? ''),
    onSuccess: () => {
      Toast.show({ content: '已触发分析', duration: 1000 })
    },
  })

  const metrics = useMemo(
    () =>
      [
        detail?.tvl !== undefined
          ? { label: 'TVL', value: `$${detail.tvl.toLocaleString()}` }
          : null,
        detail?.apy !== undefined ? { label: 'APY', value: `${detail.apy}%` } : null,
        marketData?.price !== undefined
          ? { label: '价格', value: `$${marketData.price.toFixed(2)}` }
          : null,
        marketData?.volume24h !== undefined
          ? { label: '24h 交易量', value: `$${marketData.volume24h.toLocaleString()}` }
          : null,
      ].filter(Boolean),
    [detail?.apy, detail?.tvl, marketData?.price, marketData?.volume24h],
  )

  if (!slug) {
    return <ErrorBlock status="empty" title="缺少协议标识" description="请从列表选择协议" />
  }

  if (isLoading) return <LoadingState message="加载协议详情..." />

  if (isError || !detail) {
    return (
      <div className="space-y-2">
        <ErrorBlock status="default" title="加载失败" description="无法获取协议详情" />
        <Button size="small" onClick={() => refetch()}>
          重试
        </Button>
      </div>
    )
  }

  return (
    <div className={`${styles.page} space-y-3`}>
      <div className={`${styles.section} flex flex-col gap-3`}>
        <div className={styles.sectionHeader}>
          <div>
            <div className={styles.sectionTitle}>{detail.name}</div>
            <div className={styles.sectionSubtitle}>{detail.description}</div>
          </div>
          <div className="flex items-center gap-2">
            {detail.chain ? (
              <Tag color="primary" fill="outline">
                {detail.chain}
              </Tag>
            ) : null}
            {detail.tags?.map((tag) => (
              <Tag key={tag} color="warning" fill="outline">
                {tag}
              </Tag>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {metrics.map((metric) => (
            <div
              key={metric!.label}
              className="rounded-xl bg-[var(--tg-bg-color)] p-3 text-sm"
            >
              <div className="text-[var(--tg-muted-text)]">{metric!.label}</div>
              <div className="text-lg font-semibold text-[var(--tg-text-color)]">
                {metric!.value as string}
              </div>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <Button
            color="primary"
            block
            loading={isPending}
            onClick={() => mutateAsync()}
          >
            触发分析
          </Button>
          <Button block onClick={() => navigate('/protocols')}>
            返回列表
          </Button>
        </div>
        {analyzeResult ? (
          <div className="rounded-lg bg-[var(--tg-bg-color)] p-3 text-sm text-[var(--tg-muted-text)]">
            最近触发：记录 {analyzeResult.record_id} · 状态 {analyzeResult.status ?? '已提交'}
          </div>
        ) : null}
      </div>

      <div className={`${styles.section} flex flex-col gap-2`}>
        <div className={styles.sectionHeader}>
          <div>
            <div className={styles.sectionTitle}>市场数据</div>
            <div className={styles.sectionSubtitle}>价格 / 市值 / 交易量</div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <div className="rounded-lg bg-[var(--tg-bg-color)] p-3">
            <div className="text-xs text-[var(--tg-muted-text)]">市值</div>
            <div className="text-base font-semibold text-[var(--tg-text-color)]">
              {marketData?.marketCap
                ? `$${marketData.marketCap.toLocaleString()}`
                : '暂无数据'}
            </div>
          </div>
          <div className="rounded-lg bg-[var(--tg-bg-color)] p-3">
            <div className="text-xs text-[var(--tg-muted-text)]">24h 变化</div>
            <div className="text-base font-semibold text-[var(--tg-text-color)]">
              {marketData?.change24h ? `${marketData.change24h}%` : '暂无数据'}
            </div>
          </div>
          <div className="rounded-lg bg-[var(--tg-bg-color)] p-3">
            <div className="text-xs text-[var(--tg-muted-text)]">描述</div>
            <div className="text-sm text-[var(--tg-text-color)]">
              {detail.description ?? '暂无描述'}
            </div>
          </div>
        </div>
      </div>

      <div className={`${styles.section} flex flex-col gap-2`}>
        <div className={styles.sectionHeader}>
          <div>
            <div className={styles.sectionTitle}>流动性池</div>
            <div className={styles.sectionSubtitle}>链 / TVL / APY</div>
          </div>
        </div>
        {pools.length === 0 ? (
          <ErrorBlock status="empty" title="暂无池数据" description="稍后重试或更换链" />
        ) : (
          <div className="grid grid-cols-1 gap-2">
            {pools.map((pool) => (
              <div
                key={pool.id}
                className="flex flex-col gap-1 rounded-lg border border-[var(--tg-border-color)] bg-[var(--tg-bg-color)] p-3"
              >
                <div className="flex items-center justify-between">
                  <div className="text-sm font-semibold text-[var(--tg-text-color)]">
                    {pool.name}
                  </div>
                  {pool.chain ? (
                    <Tag color="primary" fill="outline">
                      {pool.chain}
                    </Tag>
                  ) : null}
                </div>
                <div className="flex gap-4 text-xs text-[var(--tg-muted-text)]">
                  <span>TVL: {pool.tvl ? `$${pool.tvl.toLocaleString()}` : '未知'}</span>
                  <span>APY: {pool.apy ? `${pool.apy}%` : '未知'}</span>
                  <span>
                    24h 量: {pool.volume24h ? `$${pool.volume24h.toLocaleString()}` : '未知'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ProtocolDetail
