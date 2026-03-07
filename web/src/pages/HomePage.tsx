import { useNavigate } from 'react-router-dom'
import { ArrowRight, FileText, Zap, FileCheck, BrainCircuit, Clock, Users } from 'lucide-react'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'

export default function HomePage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-32">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-transparent to-accent-purple/20" />
        <div className="container mx-auto px-6 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-6xl font-bold mb-6 gradient-text">
              Transform Code into Documentation
            </h1>
            <p className="text-xl text-text-secondary mb-8">
              AI-powered report generation that creates professional technical documentation
              from your codebase in minutes, not hours.
            </p>
            <Button
              onClick={() => navigate('/upload')}
              className="text-lg px-8 py-4"
            >
              Generate Your First Report
              <ArrowRight className="ml-2 w-5 h-5 animate-bounce-x" />
            </Button>
            
            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 mt-16">
              <div className="glass-card p-6">
                <FileText className="w-8 h-8 text-primary-400 mx-auto mb-2" />
                <div className="text-3xl font-bold">1,250+</div>
                <div className="text-text-muted text-sm">Reports Generated</div>
              </div>
              <div className="glass-card p-6">
                <Clock className="w-8 h-8 text-accent-cyan mx-auto mb-2" />
                <div className="text-3xl font-bold">500+</div>
                <div className="text-text-muted text-sm">Hours Saved</div>
              </div>
              <div className="glass-card p-6">
                <Users className="w-8 h-8 text-accent-purple mx-auto mb-2" />
                <div className="text-3xl font-bold">350+</div>
                <div className="text-text-muted text-sm">Happy Users</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-bg-secondary/50">
        <div className="container mx-auto px-6">
          <h2 className="text-4xl font-bold text-center mb-12 gradient-text">
            Why Choose ReportForge AI?
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <Card className="p-8 hover:scale-105 transition-transform">
              <BrainCircuit className="w-12 h-12 text-primary-400 mb-4" />
              <h3 className="text-xl font-semibold mb-2">AI-Powered Analysis</h3>
              <p className="text-text-secondary">
                5 specialized agents work together to understand your code structure,
                extract guidelines, and generate comprehensive documentation.
              </p>
            </Card>
            
            <Card className="p-8 hover:scale-105 transition-transform">
              <Zap className="w-12 h-12 text-accent-amber mb-4" />
              <h3 className="text-xl font-semibold mb-2">Lightning Fast</h3>
              <p className="text-text-secondary">
                Generate comprehensive reports in under 30 minutes. No more spending
                days writing documentation manually.
              </p>
            </Card>
            
            <Card className="p-8 hover:scale-105 transition-transform">
              <FileCheck className="w-12 h-12 text-success mb-4" />
              <h3 className="text-xl font-semibold mb-2">Professional Formatting</h3>
              <p className="text-text-secondary">
                IEEE, ACM, or custom formatting guidelines. Your reports will look
                professional and publication-ready.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-6 text-center">
          <Card className="max-w-2xl mx-auto p-12">
            <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
            <p className="text-text-secondary mb-8">
              Upload your codebase and guidelines, and let AI do the rest.
            </p>
            <Button onClick={() => navigate('/upload')} size="lg">
              Start Generating Reports
              <ArrowRight className="ml-2" />
            </Button>
          </Card>
        </div>
      </section>
    </div>
  )
}

