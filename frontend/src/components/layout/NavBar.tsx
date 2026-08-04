import { useNavigate } from 'react-router-dom'
import { Button } from '../ui/Button'
import { Logo } from '../ui/Logo'
import { ModeSwitch } from './ModeSwitch'
import { useAuthStore } from '../../store/auth'
import { ORCHA_VERSION, SANDBOX_BETA } from '../../version'

const SANDBOX_MODE = import.meta.env.VITE_SANDBOX_MODE === 'true'

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
        {SANDBOX_BETA && (
          <span className="text-[10px] px-1.5 py-0.5 rounded border border-surface-border text-text-disabled">
            Beta
          </span>
        )}
        <span className="text-[10px] font-normal text-text-disabled">v{ORCHA_VERSION}</span>
        <span className="size-1.5 rounded-full bg-brand-secondary inline-block" aria-hidden="true" />
      </button>

      <div className="ml-auto flex items-center gap-3">
        <ModeSwitch />
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/workflows')}
        >
          ⚡ My Workflows
        </Button>

        {/* Sandbox is a no-signup demo surface: guest bootstrap handles auth.
            A quiet sign-in link stays for BYOK/vault users and owners —
            registered accounts skip the guest message cap. */}
        {SANDBOX_MODE && !isAuthenticated && (
          <button
            onClick={() => navigate('/login')}
            className="font-mono text-xs text-text-disabled hover:text-text-body transition-colors"
          >
            sign in
          </button>
        )}
        {!SANDBOX_MODE &&
          (isAuthenticated ? (
            <Button variant="secondary" size="sm" onClick={() => logout()}>
              Sign Out
            </Button>
          ) : (
            <Button variant="primary" size="sm" onClick={() => navigate('/login')}>
              Sign In
            </Button>
          ))}
      </div>
    </header>
  )
}
