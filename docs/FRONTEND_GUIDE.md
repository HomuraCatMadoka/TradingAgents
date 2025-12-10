# Frontend Guide (Telegram Mini App)

- [Naming](#naming)
- [Directory Structure](#directory-structure)
- [State Management](#state-management)
- [Styling](#styling)
- [Performance](#performance)
- [Security](#security)
- [Import Order](#import-order)
- [FAQ](#faq)

## Naming
- Components: `PascalCase` (`ProtocolCard.tsx`, `ThemeProvider.tsx`).
- Files/modules: `camelCase` for helpers/stores (`auth.ts`, `apiClient.ts`), `kebab-case` only for asset files.
- Hooks: prefix with `use` (`useAuth`, `useTheme`).

## Directory Structure
```
src/
  components/       # shared UI pieces (ProtocolCard, ProgressBar, ErrorBoundary)
  pages/            # route-level components (Dashboard, Analysis, History, Watchlist, Settings)
  router.tsx        # React Router config + layout
  services/         # API/WS clients (api.ts, auth.ts, protocols.ts, ws.ts)
  store/            # Zustand stores (auth.ts, ui.ts)
  theme/            # Theme provider/hooks tied to Telegram events
  types/            # DTOs shared with backend contracts
  utils/            # helpers (formatters, guards)
```
- Keep feature-specific styles colocated with the component; avoid deep nesting.

## State Management
- Server data: React Query only; cache keys derive from params (`['protocols', chain]`).
- UI/local state: Zustand; keep slices small (auth, ui) and serializable.
- Avoid duplicating server state in Zustand; derive from queries instead.
- Provide loading/error fallbacks close to the component boundary.

## Styling
- Use AntD Mobile theme tokens; prefer CSS/SCSS modules over inline styles.
- Keep spacing/typography tokens centralized in `theme/`.
- Responsive: rely on flex layouts; avoid hardcoded pixel widths.
- Dark mode: listen to Telegram theme events and update provider state.

## Performance
- Enable code splitting via route-level `lazy(() => import('./pages/...'))`.
- Memoize pure components (`React.memo`) and expensive calculations (`useMemo`).
- Debounce input-driven queries; cancel in-flight requests on unmount via Axios cancel tokens or AbortController.
- Avoid anonymous functions in hot paths; extract handlers when reused.

## Security
- Validate Telegram `initData` before rendering protected routes; redirect to a guard screen if invalid or expired.
- Escape/clean any HTML string rendered from API responses with DOMPurify; default to plain text whenever possible.
- Never trust query params directly; parse and validate before use.
- Avoid `dangerouslySetInnerHTML` unless sanitized and reviewed.

## Import Order
1. Node/React/3rd-party packages
2. Aliased app modules (services, stores, hooks)
3. Relative components/hooks
4. Styles last

Example:
```ts
import { useQuery } from '@tanstack/react-query';
import { getProtocols } from '@/services/protocols';
import ProtocolCard from '@/components/ProtocolCard';
import styles from './protocol-list.module.scss';
```

## FAQ
- **How do I fetch server data?** Use React Query with the shared Axios client: `useQuery({ queryKey: ['protocols'], queryFn: getProtocols })`.
- **Where to store auth token?** In a dedicated Zustand slice; set Axios interceptors to attach `Authorization: Bearer <JWT>`.
- **How to prevent XSS?** Use DOMPurify when rendering HTML; prefer Markdown-to-React or plain text. Never render raw `initData` values.
- **Why is lint failing?** Run `npm run lint`; fix import order and unused vars. If types fail, run `npm run build` to surface TS errors.
