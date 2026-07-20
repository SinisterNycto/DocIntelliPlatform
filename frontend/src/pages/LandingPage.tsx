import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { SignInButton, SignedIn, SignedOut } from '@clerk/clerk-react';
import { ThemeToggle } from '../components/ThemeToggle';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-void flex flex-col relative overflow-hidden font-sans text-text-data">
      
      {/* Quiet Ambient Pipeline SVG Background */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.07] flex items-center justify-center text-text-data">
        <svg width="100%" height="100%" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="grid-fade" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="currentColor" stopOpacity="0" />
              <stop offset="50%" stopColor="currentColor" stopOpacity="1" />
              <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
            </linearGradient>
            <pattern id="mesh" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="url(#grid-fade)" strokeWidth="0.5"/>
            </pattern>
          </defs>
          
          <rect width="100%" height="100%" fill="url(#mesh)" />
          
          {/* Incoming Document Nodes */}
          <rect x="10%" y="20%" width="30" height="30" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(15 115 215)"/>
          <rect x="85%" y="75%" width="40" height="40" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(-10 870 770)"/>
          <rect x="15%" y="80%" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(45 160 810)"/>
          
          {/* Converging Pipeline Lines */}
          <path d="M 130 230 Q 300 300 500 500" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.5"/>
          <path d="M 850 750 Q 700 600 500 500" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.5"/>
          <path d="M 170 800 Q 350 650 500 500" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.5"/>
          
          {/* Central Synthesis Sphere */}
          <circle cx="500" cy="500" r="100" fill="none" stroke="currentColor" strokeWidth="1" strokeDasharray="4 4" />
          <circle cx="500" cy="500" r="120" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.5" />
          <circle cx="500" cy="500" r="80" fill="currentColor" opacity="0.05" />
        </svg>
      </div>

      {/* Header */}
      <header className="relative z-10 max-w-7xl mx-auto w-full px-6 h-20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono font-semibold tracking-wide text-sm">
            DocIntelliPlatform
            <span className="text-grid mx-2">|</span>
            <span className="text-text-muted text-xs uppercase tracking-widest">RAG Engine</span>
          </span>
        </div>
        <div className="flex items-center gap-6 font-mono text-xs font-semibold tracking-widest text-text-muted">
          <ThemeToggle />
          <SignedOut>
            <SignInButton mode="modal">
              <button className="hover:text-text-data transition-colors uppercase">SIGN IN</button>
            </SignInButton>
          </SignedOut>
          <SignedIn>
            <Link to="/dashboard" className="hover:text-text-data transition-colors uppercase">DASHBOARD</Link>
          </SignedIn>
        </div>
      </header>

      {/* Ambient Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-primary/10 blur-[120px] rounded-full pointer-events-none" />

      {/* Hero Section */}
      <main className="flex-1 relative z-10 flex flex-col items-center justify-center text-center px-4 pt-32 pb-24">
        <h1 className="text-5xl md:text-7xl font-sans font-bold tracking-tight text-text-data mb-6 max-w-4xl drop-shadow-sm">
          Your docs.<br />
          Actually <em className="font-serif italic font-normal text-accent">understood.</em>
        </h1>
        
        <p className="text-lg md:text-xl text-text-muted max-w-2xl mb-12 leading-relaxed">
          Give your AI the exact context it needs. Instantly ingest PDFs, scrape live developer documentation, and build a high-performance vector knowledge base that guarantees hallucination-free answers.
        </p>

        <SignedOut>
          <SignInButton mode="modal">
            <button className="group flex items-center gap-3 bg-primary/90 hover:bg-primary text-void px-8 py-4 rounded-full font-mono text-sm font-medium transition-all hover:scale-105 active:scale-95 shadow-lg shadow-primary/20">
              INITIALIZE WORKSPACE
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </SignInButton>
        </SignedOut>

        <SignedIn>
          <Link to="/dashboard" className="group flex items-center gap-3 bg-primary/90 hover:bg-primary text-void px-8 py-4 rounded-full font-mono text-sm font-medium transition-all hover:scale-105 active:scale-95 shadow-lg shadow-primary/20">
            ENTER DASHBOARD
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </SignedIn>

        {/* Feature Grid */}
        <div className="mt-32 max-w-6xl w-full grid grid-cols-1 md:grid-cols-3 gap-6 text-left px-6">
          <div className="p-8 rounded-2xl bg-surface/40 border border-grid backdrop-blur-sm">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-6">
              <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
            </div>
            <h3 className="font-mono text-sm font-bold text-text-data uppercase tracking-widest mb-3">1. Ingest</h3>
            <p className="text-text-muted text-sm leading-relaxed">Automatically scrape entire Single Page Applications or upload local PDFs. We chunk and clean the data for you.</p>
          </div>
          
          <div className="p-8 rounded-2xl bg-surface/40 border border-grid backdrop-blur-sm">
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center mb-6">
              <svg className="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
            </div>
            <h3 className="font-mono text-sm font-bold text-text-data uppercase tracking-widest mb-3">2. Vectorize</h3>
            <p className="text-text-muted text-sm leading-relaxed">Powered by local Hugging Face embedding models. We map your documentation into high-dimensional semantic space.</p>
          </div>

          <div className="p-8 rounded-2xl bg-surface/40 border border-grid backdrop-blur-sm">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-6">
              <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
            </div>
            <h3 className="font-mono text-sm font-bold text-text-data uppercase tracking-widest mb-3">3. Synthesize</h3>
            <p className="text-text-muted text-sm leading-relaxed">Ask complex questions. The LLM is fed exactly the right paragraphs to generate deterministic, perfectly cited answers.</p>
          </div>
        </div>
      </main>

    </div>
  );
}
