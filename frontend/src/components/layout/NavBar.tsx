import { useNavigate } from 'react-router-dom'
import { Button } from '../ui/Button'
import { Logo } from '../ui/Logo'
import { useAuthStore } from '../../store/auth'

export function NavBar() {
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const logout = useAuthStore((s) => s.logout)

  return (
    <header className="fixed top-0 left-0 right-0 h-14 bg-surface-base/90 backdrop-blur border-b border-surface-border flex items-center px-6 z-30">
      {/* Brand */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 font-bold text-lg text-text-heading hover:opacity-80 transition-opacity"
        aria-label="Orcha home"
      >
        <Logo size={24} />
        Orcha
        <span className="size-1.5 rounded-full bg-brand-secondary inline-block" aria-hidden="true" />
      </button>

      <div className="ml-auto flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/workflows')}
        >
          ⚡ My Workflows
        </Button>

        {isAuthenticated ? (
          <Button variant="secondary" size="sm" onClick={() => logout()}>
            Sign Out
          </Button>
        ) : (
          <Button variant="primary" size="sm" onClick={() => navigate('/login')}>
            Sign In
          </Button>
        )}
      </div>
    </header>
  )
}
