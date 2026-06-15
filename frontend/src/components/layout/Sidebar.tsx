import { NavLink, useNavigate } from 'react-router-dom'
import { cn } from '../ui/cn'
import { Logo } from '../ui/Logo'
import { useSettingsStore } from '../../store/settings'

interface NavItem {
  to: string
  icon: string
  label: string
  devOnly?: boolean
}

const navItems: NavItem[] = [
  { to: '/', icon: '💬', label: 'Chat' },
  { to: '/workflows', icon: '⚡', label: 'My Workflows' },
  { to: '/agents', icon: '🤖', label: 'Agent Library', devOnly: true },
  { to: '/settings', icon: '⚙️', label: 'Settings' },
]

export function Sidebar() {
  const isDevMode = useSettingsStore((s) => s.isDevMode)
  const navigate = useNavigate()

  const visible = navItems.filter((item) => !item.devOnly || isDevMode)

  return (
    <aside
      className="fixed left-0 top-0 bottom-0 w-16 bg-surface-base border-r border-surface-border flex flex-col z-20"
      aria-label="Main navigation"
    >
      {/* Logo mark */}
      <button
        onClick={() => navigate('/')}
        aria-label="Home"
        className="flex items-center justify-center h-14 shrink-0 hover:opacity-80 transition-opacity"
      >
        <Logo size={28} />
      </button>

      {/* Nav icons */}
      <nav className="flex flex-col items-center gap-4 pt-2 flex-1">
        {visible.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            aria-label={item.label}
            title={item.label}
            className={({ isActive }) =>
              cn(
                'size-10 flex items-center justify-center rounded-md text-lg transition-colors duration-150',
                isActive
                  ? 'bg-brand-primary-dim border border-[rgba(59,110,248,0.3)] text-brand-primary'
                  : 'text-text-secondary hover:bg-surface-overlay hover:text-text-body',
              )
            }
          >
            {item.icon}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
