import { useEffect, useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Sidebar } from '../components/layout/Sidebar'
import { Toggle } from '../components/ui/Toggle'
import { Button } from '../components/ui/Button'
import { settingsApi, walletApi } from '../api/client'
import { useSettingsStore } from '../store/settings'
import { cn } from '../components/ui/cn'

type NavSection = 'Profile' | 'Developer Mode' | 'Billing' | 'Wallet' | 'Appearance'
const NAV_ITEMS: { section: string; items: NavSection[] }[] = [
  { section: 'ACCOUNT', items: ['Profile', 'Billing', 'Wallet'] },
  { section: 'PLATFORM', items: ['Appearance'] },
  { section: 'DEVELOPER', items: ['Developer Mode'] },
]

function truncateAddress(addr: string | null | undefined): string {
  if (!addr) return '—'
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`
}

function StatusBadge({ status }: Readonly<{ status: string }>) {
  const colour =
    status === 'SETTLED'
      ? 'text-semantic-success bg-semantic-successDim'
      : status === 'FAILED'
        ? 'text-semantic-error bg-semantic-errorDim'
        : 'text-semantic-warning bg-semantic-warningDim'
  return (
    <span className={cn('px-2 py-0.5 rounded text-[11px] font-medium', colour)}>
      {status}
    </span>
  )
}

export function Settings() {
  const [active, setActive] = useState<NavSection>('Profile')
  const store = useSettingsStore()

  const { data: userSettings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.get(),
  })

  useEffect(() => {
    if (userSettings) store.setUserSettings(userSettings)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userSettings])

  const patchMut = useMutation({
    mutationFn: settingsApi.update,
    onSuccess: (d) => store.setUserSettings(d),
  })

  const [displayName, setDisplayName] = useState(userSettings?.display_name ?? '')

  // ── Wallet state ───────────────────────────────────────────────────────────
  const { data: walletBalance, isLoading: walletLoading } = useQuery({
    queryKey: ['wallet-balance'],
    queryFn: () => walletApi.getBalance(),
    enabled: active === 'Wallet',
    refetchInterval: active === 'Wallet' ? 30_000 : false,
  })

  const { data: walletTxns } = useQuery({
    queryKey: ['wallet-transactions'],
    queryFn: () => walletApi.getTransactions(1),
    enabled: active === 'Wallet',
  })

  const { data: fundInfo } = useQuery({
    queryKey: ['wallet-fund-info'],
    queryFn: () => walletApi.getFundInfo(),
    enabled: active === 'Wallet',
  })

  const [showFundModal, setShowFundModal] = useState(false)
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [withdrawAddress, setWithdrawAddress] = useState('')
  const [copiedAddr, setCopiedAddr] = useState(false)

  const withdrawMut = useMutation({
    mutationFn: (body: { amount: number; to_address?: string }) =>
      walletApi.withdraw(body),
  })

  function handleCopy(text: string | null | undefined) {
    if (!text) return
    navigator.clipboard.writeText(text).then(() => {
      setCopiedAddr(true)
      setTimeout(() => setCopiedAddr(false), 1500)
    })
  }

  useEffect(() => {
    if (userSettings) setDisplayName(userSettings.display_name ?? '')
  }, [userSettings])

  return (
    <div className="flex h-screen bg-surface-canvas overflow-hidden">
      <Sidebar />

      <div className="flex flex-1 ml-16 overflow-hidden">
        {/* Settings left nav */}
        <nav
          className="w-60 h-full bg-surface-base border-r border-surface-border pt-6 px-3 shrink-0 flex flex-col gap-4"
          aria-label="Settings navigation"
        >
          {NAV_ITEMS.map(({ section, items }) => (
            <div key={section}>
              <p className="px-2 mb-1 text-[10px] font-semibold text-text-disabled tracking-caps uppercase">
                {section}
              </p>
              {items.map((item) => (
                <button
                  key={item}
                  onClick={() => setActive(item)}
                  aria-current={active === item ? 'page' : undefined}
                  className={cn(
                    'w-full text-left h-9 px-2 rounded-sm text-label transition-colors duration-100 mb-0.5',
                    active === item
                      ? 'bg-brand-primary-dim text-brand-primary-light'
                      : 'text-text-secondary hover:bg-surface-overlay hover:text-text-body',
                  )}
                >
                  {item}
                </button>
              ))}
            </div>
          ))}

          <div className="mt-auto mb-4">
            <p className="px-2 mb-1 text-[10px] font-semibold text-semantic-error tracking-caps uppercase">
              Danger Zone
            </p>
            <button className="w-full text-left h-9 px-2 rounded-sm text-label text-semantic-error hover:bg-semantic-errorDim transition-colors">
              Delete Account
            </button>
          </div>
        </nav>

        {/* Content area */}
        <main className="flex-1 overflow-y-auto scrollbar-thin px-12 py-10">
          <h1 className="text-h2 text-text-heading mb-8">Settings</h1>

          {active === 'Profile' && (
            <section>
              <h2 className="text-[18px] font-semibold text-text-heading mb-3">Profile</h2>
              <div className="border-t border-surface-border mb-6" />

              {isLoading ? (
                <p className="text-text-secondary text-body-md">Loading…</p>
              ) : (
                <div className="max-w-[440px] flex flex-col gap-4">
                  {/* Avatar */}
                  <div className="flex items-center gap-4 mb-2">
                    <div className="size-16 rounded-full bg-brand-primary-dim border-2 border-surface-border flex items-center justify-center">
                      <span className="text-[22px] font-bold text-brand-primary">
                        {(userSettings?.display_name ?? userSettings?.email ?? 'U').slice(0, 2).toUpperCase()}
                      </span>
                    </div>
                  </div>

                  <FormField label="Display Name">
                    <input
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      className="w-full h-10 px-3 rounded-md bg-surface-elevated border border-surface-border text-label text-text-body focus:outline-none focus:border-brand-primary"
                      aria-label="Display name"
                    />
                  </FormField>

                  <FormField label="Email">
                    <input
                      value={userSettings?.email ?? ''}
                      readOnly
                      className="w-full h-10 px-3 rounded-md bg-surface-elevated border border-surface-border text-label text-text-disabled"
                      aria-label="Email address (read-only)"
                    />
                  </FormField>

                  <Button
                    onClick={() => patchMut.mutate({ display_name: displayName })}
                    loading={patchMut.isPending}
                    disabled={displayName === (userSettings?.display_name ?? '')}
                    className="w-32"
                  >
                    Save
                  </Button>
                </div>
              )}
            </section>
          )}

          {active === 'Developer Mode' && (
            <section>
              <h2 className="text-[18px] font-semibold text-text-heading mb-3">Developer Mode</h2>
              <div className="border-t border-surface-border mb-6" />

              <div className="max-w-[560px]">
                <div className="flex items-center px-5 h-20 rounded-md bg-surface-elevated border border-surface-border">
                  <Toggle
                    checked={store.isDevMode}
                    onChange={(v) => {
                      store.setDevMode(v)
                      patchMut.mutate({ is_dev_mode: v })
                    }}
                    label="Developer Mode"
                    description="Register and host agents on Orcha"
                    id="dev-mode"
                  />
                </div>

                {store.isDevMode && (
                  <div className="mt-2 flex items-center gap-2 h-[34px] px-3 rounded-sm bg-semantic-warningDim border border-[#2D2000]">
                    <span className="text-[12px] text-semantic-warning">
                      ⚠ Developer mode grants access to agent registration and hosting.
                    </span>
                  </div>
                )}
              </div>
            </section>
          )}

          {active === 'Billing' && (
            <section>
              <h2 className="text-[18px] font-semibold text-text-heading mb-3">Billing</h2>
              <div className="border-t border-surface-border mb-6" />

              <div className="w-[440px] p-5 rounded-md bg-surface-elevated border border-surface-border flex items-start">
                <div className="flex-1">
                  <p className="text-[12px] font-medium text-text-secondary">Credits Balance</p>
                  <p className="text-[32px] font-bold text-text-heading mt-1 leading-none">
                    ${userSettings ? Number.parseFloat(userSettings.credits_usd).toFixed(2) : '—'}
                  </p>
                </div>
                <Button size="sm" className="mt-1">Top Up</Button>
              </div>
            </section>
          )}

          {active === 'Wallet' && (
            <section>
              <h2 className="text-[18px] font-semibold text-text-heading mb-3">Wallet</h2>
              <div className="border-t border-surface-border mb-6" />

              {walletLoading ? (
                <p className="text-text-secondary text-body-md">Loading…</p>
              ) : (
                <div className="max-w-[520px] flex flex-col gap-4">
                  {/* Arrears warning */}
                  {walletBalance?.arrears_flag && (
                    <div className="flex items-center gap-2 h-[36px] px-3 rounded-sm bg-semantic-errorDim border border-semantic-error">
                      <span className="text-[12px] text-semantic-error font-medium">
                        Outstanding balance: ${walletBalance.arrears_usd.toFixed(2)} — deposit USDC to clear
                      </span>
                    </div>
                  )}

                  {/* Balance card */}
                  <div className="p-5 rounded-md bg-surface-elevated border border-surface-border flex items-start gap-4">
                    <div className="flex-1">
                      <p className="text-[12px] font-medium text-text-secondary">Credits Balance</p>
                      <p className="text-[32px] font-bold text-text-heading mt-1 leading-none">
                        ${walletBalance ? walletBalance.credits_usd.toFixed(2) : '—'}
                      </p>
                      {walletBalance?.on_chain_usdc?.total && (
                        <p className="text-[11px] text-text-secondary mt-1">
                          On-chain: {walletBalance.on_chain_usdc.total.value} {walletBalance.on_chain_usdc.total.currency}
                        </p>
                      )}
                    </div>
                    <div className="flex flex-col gap-2 mt-1">
                      <Button size="sm" onClick={() => setShowFundModal(true)}>Fund</Button>
                    </div>
                  </div>

                  {/* Chain + address */}
                  <div className="flex items-center gap-3 px-4 h-12 rounded-md bg-surface-elevated border border-surface-border">
                    <span className="text-[11px] font-semibold text-brand-primary-light bg-brand-primary-dim px-2 py-0.5 rounded">
                      Base Sepolia
                    </span>
                    <span className="text-label text-text-secondary flex-1">
                      {truncateAddress(walletBalance?.wallet_address)}
                    </span>
                    <button
                      onClick={() => handleCopy(walletBalance?.wallet_address)}
                      className="text-[11px] text-text-disabled hover:text-text-body transition-colors"
                      aria-label="Copy wallet address"
                    >
                      {copiedAddr ? 'Copied!' : 'Copy'}
                    </button>
                  </div>

                  {/* Fund modal (inline) */}
                  {showFundModal && (
                    <div className="p-4 rounded-md bg-surface-elevated border border-surface-border flex flex-col gap-3">
                      <div className="flex items-center justify-between">
                        <p className="text-label font-semibold text-text-heading">Fund Account</p>
                        <button
                          onClick={() => setShowFundModal(false)}
                          className="text-text-disabled hover:text-text-body text-[18px] leading-none"
                          aria-label="Close"
                        >
                          ×
                        </button>
                      </div>
                      {fundInfo?.mock_mode ? (
                        <p className="text-[12px] text-semantic-warning">{fundInfo.note}</p>
                      ) : (
                        <>
                          <p className="text-[12px] text-text-secondary">
                            Send USDC on <span className="font-medium text-brand-primary-light">Base Sepolia</span> to your smart wallet below. Deposits are credited to your balance automatically.
                          </p>
                          <div className="flex flex-col gap-1">
                            <p className="text-[11px] font-medium text-text-secondary uppercase tracking-wide">Your Smart Wallet Address</p>
                            <div className="flex items-center gap-2 p-3 rounded bg-surface-base border border-surface-border">
                              <span className="text-[12px] font-mono text-text-body flex-1 break-all">
                                {fundInfo?.wallet_address ?? '—'}
                              </span>
                              <button
                                onClick={() => handleCopy(fundInfo?.wallet_address)}
                                className="text-[11px] text-text-disabled hover:text-text-body shrink-0"
                                aria-label="Copy platform wallet address"
                              >
                                {copiedAddr ? 'Copied!' : 'Copy'}
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  )}

                  {/* Withdraw (DEV only) */}
                  {userSettings?.is_dev_mode && (
                    <div className="p-4 rounded-md bg-surface-elevated border border-surface-border flex flex-col gap-3">
                      <p className="text-label font-semibold text-text-heading">Withdraw</p>
                      <div className="flex flex-col gap-2">
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          placeholder="Amount (USDC)"
                          value={withdrawAmount}
                          onChange={(e) => setWithdrawAmount(e.target.value)}
                          className="w-full h-10 px-3 rounded-md bg-surface-base border border-surface-border text-label text-text-body focus:outline-none focus:border-brand-primary"
                          aria-label="Withdrawal amount"
                        />
                        <input
                          type="text"
                          placeholder="Destination address (0x…) — optional, uses saved address"
                          value={withdrawAddress}
                          onChange={(e) => setWithdrawAddress(e.target.value)}
                          className="w-full h-10 px-3 rounded-md bg-surface-base border border-surface-border text-label text-text-body focus:outline-none focus:border-brand-primary"
                          aria-label="Withdrawal destination address"
                        />
                      </div>
                      {withdrawMut.isSuccess && (
                        <p className="text-[12px] text-semantic-success">
                          Transfer initiated — action ID: {withdrawMut.data?.action_id}
                        </p>
                      )}
                      {withdrawMut.isError && (
                        <p className="text-[12px] text-semantic-error">
                          {(withdrawMut.error as Error).message}
                        </p>
                      )}
                      <Button
                        size="sm"
                        className="w-32"
                        loading={withdrawMut.isPending}
                        disabled={!withdrawAmount || Number(withdrawAmount) <= 0}
                        onClick={() =>
                          withdrawMut.mutate({
                            amount: Number(withdrawAmount),
                            to_address: withdrawAddress || undefined,
                          })
                        }
                      >
                        Withdraw
                      </Button>
                    </div>
                  )}

                  {/* Transaction history */}
                  <div className="flex flex-col gap-2">
                    <p className="text-[13px] font-semibold text-text-heading">Transaction History</p>
                    {!walletTxns?.transactions.length ? (
                      <p className="text-[12px] text-text-secondary">No transactions yet.</p>
                    ) : (
                      <div className="rounded-md border border-surface-border overflow-hidden">
                        <table className="w-full text-[12px]">
                          <thead>
                            <tr className="bg-surface-elevated border-b border-surface-border">
                              <th className="text-left px-3 py-2 text-text-secondary font-medium">Agent</th>
                              <th className="text-right px-3 py-2 text-text-secondary font-medium">Fee</th>
                              <th className="text-right px-3 py-2 text-text-secondary font-medium">Status</th>
                              <th className="text-right px-3 py-2 text-text-secondary font-medium">Tx</th>
                              <th className="text-right px-3 py-2 text-text-secondary font-medium">Date</th>
                            </tr>
                          </thead>
                          <tbody>
                            {walletTxns.transactions.map((tx) => (
                              <tr key={tx.id} className="border-b border-surface-border last:border-0 hover:bg-surface-overlay">
                                <td className="px-3 py-2 text-text-body font-mono">
                                  {tx.agent_id.slice(0, 8)}…
                                </td>
                                <td className="px-3 py-2 text-right text-text-body">
                                  ${tx.base_fee.toFixed(4)}
                                </td>
                                <td className="px-3 py-2 text-right">
                                  <StatusBadge status={tx.status} />
                                </td>
                                <td className="px-3 py-2 text-right">
                                  {tx.tx_hash ? (
                                    <a
                                      href={`https://sepolia.basescan.org/tx/${tx.tx_hash}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-[11px] text-brand-primary-light hover:underline font-mono"
                                      title={tx.tx_hash}
                                    >
                                      {tx.tx_hash.slice(0, 8)}…
                                    </a>
                                  ) : (
                                    <span className="text-text-disabled text-[11px]">—</span>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-right text-text-disabled">
                                  {new Date(tx.created_at).toLocaleDateString()}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </section>
          )}

          {active === 'Appearance' && (
            <section>
              <h2 className="text-[18px] font-semibold text-text-heading mb-3">Appearance</h2>
              <div className="border-t border-surface-border mb-6" />

              <div className="max-w-[440px] flex flex-col gap-4">
                <FormField label="Language">
                  <select
                    value={store.language}
                    onChange={(e) => store.setLanguage(e.target.value)}
                    aria-label="Language"
                    className="w-full h-10 px-3 rounded-md bg-surface-elevated border border-surface-border text-label text-text-body focus:outline-none focus:border-brand-primary cursor-pointer"
                  >
                    <option value="en">English</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="es">Spanish</option>
                  </select>
                </FormField>

                <FormField label="Timezone">
                  <input
                    value={store.timezone}
                    onChange={(e) => store.setTimezone(e.target.value)}
                    aria-label="Timezone"
                    className="w-full h-10 px-3 rounded-md bg-surface-elevated border border-surface-border text-label text-text-body focus:outline-none focus:border-brand-primary"
                  />
                </FormField>

                <FormField label="Default Model">
                  <select
                    value={store.defaultModel}
                    onChange={(e) => store.setDefaultModel(e.target.value)}
                    aria-label="Default model"
                    className="w-full h-10 px-3 rounded-md bg-surface-elevated border border-surface-border text-label text-text-body focus:outline-none focus:border-brand-primary cursor-pointer"
                  >
                    <option value="claude-sonnet">Claude Sonnet</option>
                    <option value="claude-haiku">Claude Haiku</option>
                    <option value="gpt-4o">GPT-4o</option>
                    <option value="gpt-4o-mini">GPT-4o Mini</option>
                  </select>
                </FormField>
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  )
}

function FormField({ label, children }: Readonly<{ label: string; children: React.ReactNode }>) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[12px] font-medium text-text-secondary">{label}</label>
      {children}
    </div>
  )
}
