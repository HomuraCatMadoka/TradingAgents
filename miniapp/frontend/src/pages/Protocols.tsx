import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button, ErrorBlock, SearchBar, Selector } from 'antd-mobile'
import { useNavigate } from 'react-router-dom'
import ProtocolCard from '@/components/ProtocolCard'
import LoadingState from '@/components/LoadingState'
import { getList } from '@/services/protocols'
import type { Protocol } from '@/types/protocol'
import styles from './Page.module.css'

const sortOptions = [
  { label: 'TVL', value: 'tvl' },
  { label: 'APY', value: 'apy' },
  { label: '名称', value: 'name' },
]

const Protocols = () => {
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')
  const [chain, setChain] = useState<string | undefined>(undefined)
  const [sortBy, setSortBy] = useState<'tvl' | 'apy' | 'name'>('tvl')

  const {
    data: protocols = [],
    isLoading,
    isError,
    refetch,
  } = useQuery<Protocol[]>({
    queryKey: ['protocols', 'list', keyword, chain],
    queryFn: () => getList({ search: keyword || undefined, chain, limit: 50 }),
    staleTime: 2 * 60 * 1000,
  })

  const chains = useMemo(
    () =>
      Array.from(new Set(protocols.map((item) => item.chain).filter(Boolean))) as string[],
    [protocols],
  )

  const sortedProtocols = useMemo(() => {
    const data = [...protocols]
    return data.sort((a, b) => {
      if (sortBy === 'name') {
        return (a.name ?? '').localeCompare(b.name ?? '')
      }
      if (sortBy === 'tvl') {
        return (b.tvl ?? 0) - (a.tvl ?? 0)
      }
      return (b.apy ?? 0) - (a.apy ?? 0)
    })
  }, [protocols, sortBy])

  const filteredProtocols = useMemo(() => {
    const byChain = chain
      ? sortedProtocols.filter((item) => item.chain?.toLowerCase() === chain.toLowerCase())
      : sortedProtocols
    if (!keyword) return byChain
    return byChain.filter((item) => item.name.toLowerCase().includes(keyword.toLowerCase()))
  }, [chain, keyword, sortedProtocols])

  if (isLoading) {
    return <LoadingState message="加载协议列表..." />
  }

  if (isError) {
    return (
      <div className="space-y-2">
        <ErrorBlock status="default" title="加载失败" description="无法获取协议列表" />
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
            <div className={styles.sectionTitle}>协议列表</div>
            <div className={styles.sectionSubtitle}>搜索、筛选并排序</div>
          </div>
        </div>
        <SearchBar
          placeholder="搜索协议名称"
          value={keyword}
          onChange={setKeyword}
          showCancelButton
        />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Selector
            options={[
              { label: '全部链', value: 'all' },
              ...chains.map((value) => ({ label: value, value })),
            ]}
            value={chain ? [chain] : ['all']}
            onChange={(val) => setChain(val[0] === 'all' ? undefined : val[0])}
          />
          <Selector
            options={sortOptions}
            value={[sortBy]}
            onChange={(val) => setSortBy(val[0] as typeof sortBy)}
          />
        </div>
      </div>

      <div className={styles.section}>
        {filteredProtocols.length === 0 ? (
          <ErrorBlock status="empty" title="暂无协议" description="调整搜索或筛选条件后重试" />
        ) : (
          filteredProtocols.map((protocol) => (
            <ProtocolCard
              key={protocol.id}
              protocol={protocol}
              onClick={(slug) => navigate(`/protocols/${slug}`)}
            />
          ))
        )}
      </div>
    </div>
  )
}

export default Protocols
