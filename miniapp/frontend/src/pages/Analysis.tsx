import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, ErrorBlock, List, SearchBar, Selector, Tabs, Tag } from 'antd-mobile'
import LoadingState from '@/components/LoadingState'
import { getList } from '@/services/protocols'
import type { Protocol } from '@/types/protocol'
import styles from './Page.module.css'

const Analysis = () => {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<string | undefined>()
  const [chain, setChain] = useState<string | undefined>()

  const {
    data: protocols = [],
    isLoading,
    isError,
  } = useQuery<Protocol[]>({
    queryKey: ['protocols'],
    queryFn: getList,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })

  const filtered = protocols.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(search.toLowerCase())
    const matchesCategory = category ? item.category === category : true
    const matchesChain = chain ? item.chain === chain : true
    return matchesSearch && matchesCategory && matchesChain
  })

  if (isLoading) return <LoadingState message="加载协议列表..." />
  if (isError)
    return (
      <ErrorBlock status="default" title="加载失败" description="无法获取协议数据" />
    )

  return (
    <div className={styles.page}>
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitle}>协议选择器</div>
        </div>
        <SearchBar
          value={search}
          placeholder="搜索协议"
          onChange={setSearch}
          showCancelButton
        />
        <div className={styles.controls}>
          <Selector
            className={styles.selector}
            options={[
              { label: 'Lending', value: 'lending' },
              { label: 'DEX', value: 'dex' },
              { label: 'Derivatives', value: 'derivatives' },
            ]}
            value={category ? [category] : []}
            onChange={(val) => setCategory(val[0])}
          />
          <Selector
            className={styles.selector}
            options={[
              { label: 'Ethereum', value: 'ethereum' },
              { label: 'Arbitrum', value: 'arbitrum' },
              { label: 'Optimism', value: 'optimism' },
            ]}
            value={chain ? [chain] : []}
            onChange={(val) => setChain(val[0])}
          />
        </div>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitle}>Agent 对话区</div>
          <div className={styles.sectionSubtitle}>最新分析消息</div>
        </div>
        <List className={styles.list}>
          <List.Item description="等待输入">欢迎使用 DeFi Agent</List.Item>
          <List.Item description="进度 0%">请选择协议开始分析</List.Item>
        </List>
      </div>

      <div className={styles.section}>
        <Tabs>
          <Tabs.Tab title="概览" key="overview">
            <List className={styles.list}>
              <List.Item description="关键指标卡片">TVL、APY、风险评分</List.Item>
              <List.Item extra={<Tag color="primary">收藏</Tag>}>收藏协议</List.Item>
            </List>
          </Tabs.Tab>
          <Tabs.Tab title="图表" key="charts">
            <Card>TVL 趋势、收益分解、风险雷达图（待对接数据）</Card>
          </Tabs.Tab>
          <Tabs.Tab title="报告" key="report">
            <Card>Analyst 报告和最终决策将在此显示。</Card>
          </Tabs.Tab>
        </Tabs>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitle}>协议列表</div>
          <div className={styles.sectionSubtitle}>筛选后的协议</div>
        </div>
        <List className={styles.list}>
          {filtered.map((item) => (
            <List.Item
              key={item.id}
              description={item.chain ?? '链待补充'}
              extra={<Tag color="primary">分析</Tag>}
            >
              {item.name}
            </List.Item>
          ))}
          {filtered.length === 0 ? (
            <ErrorBlock status="empty" title="暂无匹配协议" description="调整筛选条件再试一次" />
          ) : null}
        </List>
      </div>
    </div>
  )
}

export default Analysis
