import { ErrorBlock, Tag } from 'antd-mobile'
import type { Analysis } from '@/types/analysis'

type Props = {
  records: Analysis[]
  loading?: boolean
  error?: string | null
  onDelete?: (id: number) => void
  onView?: (id: number) => void
}

const HistoryTable = ({ records, loading, error, onDelete, onView }: Props) => {
  const showActions = Boolean(onDelete) || Boolean(onView)

  if (loading) {
    return (
      <div className="space-y-2 rounded-xl border border-[var(--tg-border-color)] bg-[var(--tg-surface-color)] p-4">
        <div className="h-4 w-1/2 animate-pulse rounded bg-[var(--tg-border-color)]" />
        <div className="h-4 w-2/3 animate-pulse rounded bg-[var(--tg-border-color)]" />
        <div className="h-4 w-1/3 animate-pulse rounded bg-[var(--tg-border-color)]" />
      </div>
    )
  }

  if (error) {
    return <ErrorBlock status="default" title="加载失败" description={error} />
  }

  if (!records.length) {
    return (
      <ErrorBlock status="empty" title="暂无历史记录" description="完成一次分析后会出现在这里" />
    )
  }

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--tg-border-color)] bg-[var(--tg-surface-color)]">
      <div className="grid grid-cols-12 bg-[var(--tg-bg-color)] px-4 py-2 text-sm text-[var(--tg-muted-text)]">
        <span className="col-span-4">协议</span>
        <span className="col-span-3">类型</span>
        <span className="col-span-3">时间</span>
        {showActions ? <span className="col-span-2 text-right">操作</span> : null}
      </div>
      <div>
        {records.map((item) => (
          <div
            key={item.id}
            className="grid grid-cols-12 items-center px-4 py-3 text-sm border-t border-[var(--tg-border-color)] first:border-t-0"
          >
            <div className="col-span-4 flex flex-col gap-1">
              <span className="font-medium text-[var(--tg-text-color)]">
                {item.protocolName}
              </span>
              {item.cached ? <Tag color="success">缓存</Tag> : null}
            </div>
            <div className="col-span-3">
              <Tag color="primary" fill="outline">
                {item.queryType ?? 'analysis'}
              </Tag>
            </div>
            <div className="col-span-3 text-[var(--tg-muted-text)]">{item.createdAt}</div>
            {showActions ? (
              <div className="col-span-2 flex justify-end gap-2">
                {onView ? (
                  <button
                    type="button"
                    className="text-[var(--tg-accent)] underline"
                    onClick={() => onView(item.id)}
                  >
                    查看
                  </button>
                ) : null}
                {onDelete ? (
                  <button
                    type="button"
                    className="text-red-500 underline"
                    onClick={() => onDelete(item.id)}
                  >
                    删除
                  </button>
                ) : null}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  )
}

export default HistoryTable
