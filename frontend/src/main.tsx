import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'
import AccessKeyGate from './components/AccessKeyGate'
import { createQueryClient } from './lib/queries'

const queryClient = createQueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <AccessKeyGate />
    </QueryClientProvider>
  </StrictMode>,
)
