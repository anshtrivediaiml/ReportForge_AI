import { Home } from 'lucide-react'
import Button from '@/components/common/Button'

export default function NotFoundPage() {
  return (
    <div className="container mx-auto px-6 py-12 text-center">
      <h1 className="text-6xl font-bold mb-4 gradient-text">404</h1>
      <p className="text-xl text-text-secondary mb-8">Page not found</p>
      <Button onClick={() => window.location.href = '/'}>
        <Home className="mr-2" />
        Go Home
      </Button>
    </div>
  )
}

