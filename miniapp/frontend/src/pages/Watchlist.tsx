import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Button, ErrorBlock, Input, Selector, Switch, type InputRef } from 'antd-mobile'
import LoadingState from '@/components/LoadingState'
import {
  batchUpdateWatchlist,
  createWatchlist,
  deleteWatchlist,
  getWatchlist,
  updateWatchlist,
  type WatchlistItem,
} from '@/services/watchlist'
import styles from './Page.module.css'

const conditionOptions = [
  { label: 'TVL 下跌', value: 'tvl_drop' },
  { label: 'APY 上升', value: 'apy_rise' },
  { label: '交易量变化', value: 'volume_change' },
]

const Watchlist = () => {
  const [protocolName, setProtocolName] = useState('')
  const [conditionType, setConditionType] = useState(conditionOptions[0].value)
  const [threshold, setThreshold] = useState<number>(10)
  const [alertMessage, setAlertMessage] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)

  const protocolNameRef = useRef<InputRef>(null)
  const thresholdRef = useRef<InputRef>(null)
  const alertRef = useRef<InputRef>(null)

  const getProtocolName = () =>
    (protocolName || protocolNameRef.current?.nativeElement?.value || '').trim()
  const getThreshold = () => {
    const refValue = thresholdRef.current?.nativeElement?.value
    const parsed = Number(refValue ?? threshold)
    return Number.isFinite(parsed) ? parsed : 0
  }
  const getAlertMessage = () =>
    (alertMessage || alertRef.current?.nativeElement?.value || '').trim()

  const {
    data: entries = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['watchlist', 'page'],
    queryFn: () => getWatchlist(),
  })

  const createMutation = useMutation({
    mutationFn: (payload: {
      protocolName: string
      conditionType: string
      threshold: number
      isActive: boolean
      alertMessage?: string
    }) => createWatchlist(payload),
    onSuccess: () => {
      resetForm()
      refetch()
    },
  })

  const updateMutation = useMutation({
    mutationFn: (payload: {
      id: number
      data: { conditionType: string; threshold: number; isActive: boolean; alertMessage: string }
    }) => updateWatchlist(payload.id, payload.data),
    onSuccess: () => {
      resetForm()
      refetch()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteWatchlist(id),
    onSuccess: () => refetch(),
  })

  const toggleMutation = useMutation({
    mutationFn: (payload: { id: number; isActive: boolean }) =>
      updateWatchlist(payload.id, { isActive: payload.isActive }),
    onSuccess: () => refetch(),
  })

  const batchMutation = useMutation({
    mutationFn: (active: boolean) => batchUpdateWatchlist(entries.map((item) => item.id), active),
    onSuccess: () => refetch(),
  })

  const resetForm = () => {
    setProtocolName('')
    setConditionType(conditionOptions[0].value)
    setThreshold(10)
    setAlertMessage('')
    setIsActive(true)
    setEditingId(null)
    const nameInput = protocolNameRef.current?.nativeElement
    const thresholdInput = thresholdRef.current?.nativeElement
    const alertInput = alertRef.current?.nativeElement
    if (nameInput) nameInput.value = ''
    if (thresholdInput) thresholdInput.value = ''
    if (alertInput) alertInput.value = ''
  }

  useEffect(() => {
    if (!editingId) return
    const target = entries.find((item) => item.id === editingId)
    if (!target) return
    setProtocolName(target.protocolName)
    setConditionType(target.conditionType)
    setThreshold(target.threshold)
    setAlertMessage(target.alertMessage ?? '')
    setIsActive(target.isActive)
  }, [editingId, entries])

  const submit = () => {
    const name = getProtocolName()
    if (!name && !editingId) return
    const payload = {
      conditionType,
      threshold: getThreshold(),
      isActive,
      alertMessage: getAlertMessage(),
    }
    if (editingId) {
      updateMutation.mutate({ id: editingId, data: payload })
    } else {
      createMutation.mutate({
        protocolName: name,
        conditionType,
        threshold: payload.threshold,
        isActive,
        alertMessage: payload.alertMessage,
      })
    }
  }

  if (isLoading) return <LoadingState message="加载监控列表..." />
  if (isError)
    return (
      <div className="space-y-2">
        <ErrorBlock status="default" title="加载失败" description="无法获取监控数据" />
        <Button size="small" onClick={() => refetch()}>
          重试
        </Button>
      </div>
    )

  return (
    <div className={`${styles.page} space-y-3`}>
      <div className={`${styles.section} flex flex-col gap-3`}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitle}>{editingId ? '编辑监控' : '添加监控'}</div>
        </div>
        <Input
          placeholder="协议名称"
          value={protocolName}
          onChange={setProtocolName}
          disabled={Boolean(editingId)}
          ref={protocolNameRef}
        />
        <Selector
          options={conditionOptions}
          value={[conditionType]}
          onChange={(val) => setConditionType(val[0])}
        />
        <Input
          type="number"
          placeholder="阈值"
          value={String(threshold)}
          onChange={(val) => setThreshold(Number(val || 0))}
          ref={thresholdRef}
        />
        <Input
          placeholder="提醒消息（可选）"
          value={alertMessage}
          onChange={setAlertMessage}
          ref={alertRef}
        />
        <div className="flex items-center gap-2 text-sm">
          <span>启用</span>
          <Switch checked={isActive} onChange={setIsActive} />
        </div>
        <div className="flex gap-2">
          <Button
            color="primary"
            block
            loading={createMutation.isPending || updateMutation.isPending}
            onClick={submit}
          >
            {editingId ? '保存修改' : '添加监控'}
          </Button>
          {editingId ? (
            <Button block onClick={resetForm}>
              取消
            </Button>
          ) : null}
        </div>
      </div>

      <div className={`${styles.section} flex flex-col gap-3`}>
        <div className="flex items-center justify-between">
          <div className={styles.sectionTitle}>监控列表</div>
          <div className="flex gap-2">
            <Button
              size="mini"
              loading={batchMutation.isPending}
              onClick={() => batchMutation.mutate(true)}
            >
              全部开启
            </Button>
            <Button
              size="mini"
              loading={batchMutation.isPending}
              onClick={() => batchMutation.mutate(false)}
            >
              全部关闭
            </Button>
          </div>
        </div>
        {entries.length === 0 ? (
          <ErrorBlock status="empty" title="暂无监控" description="添加监控后显示在这里" />
        ) : (
          <div className="space-y-2">
            {entries.map((item) => (
              <div
                key={item.id}
                className="flex flex-col gap-2 rounded-lg border border-[var(--tg-border-color)] bg-[var(--tg-bg-color)] p-3"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold text-[var(--tg-text-color)]">
                      {item.protocolName}
                    </div>
                    <div className="text-xs text-[var(--tg-muted-text)]">
                      条件：{item.conditionType} · 阈值 {item.threshold}
                    </div>
                  </div>
                  <Switch
                    checked={item.isActive}
                    loading={toggleMutation.isPending}
                    onChange={(value) => toggleMutation.mutate({ id: item.id, isActive: value })}
                  />
                </div>
                {item.alertMessage ? (
                  <div className="text-xs text-[var(--tg-muted-text)]">
                    提醒：{item.alertMessage}
                  </div>
                ) : null}
                <div className="flex gap-2">
                  <Button size="mini" onClick={() => setEditingId(item.id)}>
                    编辑
                  </Button>
                  <Button
                    size="mini"
                    color="warning"
                    loading={deleteMutation.isPending}
                    onClick={() => deleteMutation.mutate(item.id)}
                  >
                    删除
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Watchlist
