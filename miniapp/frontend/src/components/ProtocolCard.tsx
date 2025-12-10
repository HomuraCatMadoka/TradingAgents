import { Card, Tag } from 'antd-mobile'
import { StarFill } from 'antd-mobile-icons'
import type { ReactNode } from 'react'
import type { Protocol } from '@/types/protocol'
import styles from './ProtocolCard.module.css'

type Props = {
  protocol: Protocol
  subtitle?: string
  actions?: ReactNode
  footer?: ReactNode
  onClick?: (slug: string) => void
}

const ProtocolCard = ({ protocol, subtitle, actions, footer, onClick }: Props) => {
  const slug = protocol.slug ?? protocol.id ?? protocol.name

  return (
    <Card
      className={`${styles.card} shadow-sm border border-[var(--tg-border-color)]`}
      onClick={() => onClick?.(slug)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-base font-semibold text-[var(--tg-text-color)]">
              {protocol.name}
            </span>
            {protocol.chain ? (
              <Tag color="primary" fill="outline">
                {protocol.chain}
              </Tag>
            ) : null}
            {protocol.isFavorite ? <StarFill color="var(--tg-accent)" /> : null}
          </div>
          {subtitle ? (
            <div className="text-xs text-[var(--tg-muted-text)]">{subtitle}</div>
          ) : null}
          {protocol.tags?.length ? (
            <div className="flex flex-wrap gap-2">
              {protocol.tags.map((tag) => (
                <Tag key={tag} color="warning" fill="outline" className="text-xs">
                  {tag}
                </Tag>
              ))}
            </div>
          ) : null}
        </div>
        {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
      </div>
      <div className={`${styles.metrics} mt-3`}>
        {protocol.tvl !== undefined && (
          <div>
            <div className={styles.metricLabel}>TVL</div>
            <div className={styles.metricValue}>${protocol.tvl.toLocaleString()}</div>
          </div>
        )}
        {protocol.apy !== undefined && (
          <div>
            <div className={styles.metricLabel}>APY</div>
            <div className={styles.metricValue}>{protocol.apy}%</div>
          </div>
        )}
        {(protocol.metrics ?? []).map((metric) => (
          <div key={metric.label}>
            <div className={styles.metricLabel}>{metric.label}</div>
            <div className={styles.metricValue}>{metric.value}</div>
          </div>
        ))}
      </div>
      {footer ? <div className="mt-3">{footer}</div> : null}
    </Card>
  )
}

export default ProtocolCard
