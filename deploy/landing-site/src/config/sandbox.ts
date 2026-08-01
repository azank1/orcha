export const SANDBOX_URL = import.meta.env.VITE_SANDBOX_URL || 'https://sandbox.orcha.ai';
export const SANDBOX_STATUS_URL = `${SANDBOX_URL}/api/v1/sandbox/status`;
export const SANDBOX_HOST = new URL(SANDBOX_URL).hostname;
