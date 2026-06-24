import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useUserStore } from '@/store/userStore';
import { HeroChart } from '@/components/trading/HeroChart';
import { LiveMarkets } from '@/components/trading/LiveMarkets';
import { ArrowRight, BarChart3, Zap, ShieldCheck, Globe, Rocket } from 'lucide-react';

export function LandingPage() {
  const { session } = useUserStore();

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans selection:bg-primary/30 overflow-x-hidden">
      {/* Navbar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border/40 backdrop-blur-xl sticky top-0 z-50 bg-background/80">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-primary rounded-xl flex items-center justify-center font-bold text-primary-foreground shadow-lg shadow-primary/20">
            N
          </div>
          <span className="text-xl font-bold tracking-tight">NanoTrade</span>
        </div>
        <nav className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
            <a href="#markets" className="hover:text-foreground transition-colors">Markets</a>
            <a href="#pro" className="hover:text-foreground transition-colors">Pro Terminal</a>
          </div>
          {session ? (
            <Link to="/dashboard">
              <Button variant="default" className="rounded-full px-6">Terminal</Button>
            </Link>
          ) : (
            <div className="flex gap-3">
              <Link to="/auth">
                <Button variant="ghost" className="rounded-full">Log In</Button>
              </Link>
              <Link to="/auth">
                <Button variant="default" className="rounded-full px-6">Sign Up</Button>
              </Link>
            </div>
          )}
        </nav>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="relative pt-12 pb-16 px-6 overflow-hidden min-h-[85vh] flex items-center">
          {/* Background Gradients */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[500px] bg-primary/10 rounded-full blur-[100px] opacity-60 pointer-events-none" />
          
          <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center w-full">
            <div className="space-y-6 relative z-10">
              <div className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-bold text-primary backdrop-blur-sm shadow-[0_0_15px_rgba(34,197,94,0.2)]">
                <Rocket className="w-4 h-4 mr-2" />
                Beta Version Released
              </div>
              
              <h1 className="text-5xl lg:text-6xl font-black tracking-tighter leading-[1.05]">
                Trade crypto <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-blue-400">
                  without the risk.
                </span>
              </h1>
              
              <p className="text-lg text-muted-foreground font-medium max-w-[500px] leading-relaxed">
                Experience the speed and precision of a professional exchange. Master your strategies with real-time market data in INR and USD.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center gap-4 pt-4">
                {session ? (
                  <Link to="/dashboard" className="w-full sm:w-auto">
                    <Button size="lg" className="w-full sm:w-auto h-12 px-8 text-base rounded-full shadow-xl shadow-primary/20">
                      Open Terminal <ArrowRight className="ml-2 w-5 h-5" />
                    </Button>
                  </Link>
                ) : (
                  <Link to="/auth" className="w-full sm:w-auto">
                    <Button size="lg" className="w-full sm:w-auto h-12 px-8 text-base rounded-full shadow-xl shadow-primary/20">
                      Start Paper Trading <ArrowRight className="ml-2 w-5 h-5" />
                    </Button>
                  </Link>
                )}
                <a href="#markets" className="w-full sm:w-auto">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto h-12 px-8 text-base rounded-full bg-transparent border-border hover:bg-accent hover:text-accent-foreground backdrop-blur-md">
                    View Markets
                  </Button>
                </a>
              </div>
              
              <div className="flex flex-wrap items-center gap-6 pt-6 text-sm font-semibold text-muted-foreground">
                <div className="flex items-center gap-2"><Zap className="w-4 h-4 text-yellow-500" /> Zero Latency Engine</div>
                <div className="flex items-center gap-2"><Globe className="w-4 h-4 text-blue-500" /> Native INR Pricing</div>
                <div className="flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-green-500" /> 100% Risk Free</div>
              </div>
            </div>
            
            <div className="relative h-[320px] w-full lg:h-[400px] z-10 [perspective:1000px]">
              <div className="absolute inset-0 [transform:rotateY(-5deg)_rotateX(5deg)] transition-transform duration-700 hover:[transform:rotateY(0deg)_rotateX(0deg)]">
                 <HeroChart />
              </div>
            </div>
          </div>
        </section>

        {/* Live Markets Section */}
        <LiveMarkets />

        {/* Features Section */}
        <section id="features" className="py-24 bg-card/30 border-y border-border/40 px-6 relative overflow-hidden">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16 space-y-4">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Built for modern traders</h2>
              <p className="text-muted-foreground text-lg max-w-[600px] mx-auto">Everything you need to test your edge in the crypto markets, packaged in an interface that gets out of your way.</p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-6">
              {/* Feature 1 */}
              <div className="p-8 rounded-3xl bg-background border border-border/50 hover:border-primary/50 transition-colors shadow-sm group">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform">
                  <BarChart3 className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-3 tracking-tight">Professional Charts</h3>
                <p className="text-muted-foreground leading-relaxed text-sm">
                  Integrated TradingView lightweight charts with high-performance rendering. Analyze trends seamlessly with zero lag.
                </p>
              </div>
              
              {/* Feature 2 */}
              <div className="p-8 rounded-3xl bg-background border border-border/50 hover:border-primary/50 transition-colors shadow-sm group">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform">
                  <Zap className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-3 tracking-tight">Instant Execution</h3>
                <p className="text-muted-foreground leading-relaxed text-sm">
                  Custom in-memory matching engine connected via WebSockets ensures your paper trades fill instantly at live market prices.
                </p>
              </div>
              
              {/* Feature 3 */}
              <div className="p-8 rounded-3xl bg-background border border-border/50 hover:border-primary/50 transition-colors shadow-sm group">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform">
                  <Globe className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-3 tracking-tight">Dual Currency</h3>
                <p className="text-muted-foreground leading-relaxed text-sm">
                  Track your portfolio and place orders in both USD and INR. Built-in real-time conversion handles the math for you.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="py-8 bg-background border-t border-border/40 px-6 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center font-bold text-primary-foreground text-xs">
              N
            </div>
            <span className="font-semibold tracking-tight">NanoTrade</span>
          </div>
          <p className="text-sm text-muted-foreground font-medium">
            © 2026 NanoTrade. A premium paper trading experience.
          </p>
          <div className="flex gap-6 text-sm font-medium text-muted-foreground">
            <a href="#" className="hover:text-foreground transition-colors">Terms</a>
            <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
            <a href="#" className="hover:text-foreground transition-colors">Twitter</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
