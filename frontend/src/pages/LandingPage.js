import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { toast, Toaster } from 'sonner';
import { Eye, EyeOff, TrendingUp, Users, Zap, ArrowRight, Globe } from 'lucide-react';

export default function LandingPage() {
  const history = useHistory();
  const { isAuthenticated, login, register, loading } = useAuth();
  
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated && !loading) {
      history.push('/feed');
    }
  }, [isAuthenticated, loading, history]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      if (isLoginMode) {
        await login(email, password);
        toast.success('Welcome back!');
      } else {
        if (username.length < 3) {
          toast.error('Username must be at least 3 characters');
          return;
        }
        await register(email, password, username);
        toast.success('Account created! Welcome to SocialFi');
      }
      history.push('/feed');
    } catch (error) {
      const message = error.response?.data?.detail || 'Something went wrong';
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-emerald-400 font-mono text-xl animate-pulse">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      <Toaster position="top-center" theme="dark" />
      
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/20 via-transparent to-purple-900/20" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-500/5 via-transparent to-transparent" />
      
      {/* Grid pattern */}
      <div className="absolute inset-0 opacity-10" style={{
        backgroundImage: 'linear-gradient(rgba(16,185,129,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(16,185,129,0.3) 1px, transparent 1px)',
        backgroundSize: '60px 60px'
      }} />

      <div className="relative z-10 min-h-screen flex flex-col lg:flex-row">
        {/* Left side - Hero content */}
        <div className="flex-1 flex flex-col justify-center px-8 lg:px-16 py-12 lg:py-0">
          <div className="max-w-xl">
            {/* Logo */}
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-7 h-7 text-black" />
              </div>
              <span className="text-2xl font-bold text-white tracking-tight">SocialFi</span>
            </div>

            <h1 className="text-4xl lg:text-6xl font-bold text-white mb-6 leading-tight">
              Trade the
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400"> Internet</span>
            </h1>
            
            <p className="text-lg text-zinc-400 mb-8 leading-relaxed">
              Every viral post becomes a tradable market. Aggregate content from Reddit, Farcaster, X, and more. 
              Buy low, sell high, earn rewards.
            </p>

            {/* Network badges */}
            <div className="flex flex-wrap gap-3 mb-10">
              {[
                { name: 'Reddit', icon: '🔴', active: true },
                { name: 'Farcaster', icon: '🟣', active: true },
                { name: 'X', icon: '⚫', active: false },
                { name: 'Instagram', icon: '📷', active: false },
                { name: 'Twitch', icon: '💜', active: false },
              ].map((network) => (
                <div 
                  key={network.name}
                  className={`px-4 py-2 rounded-full border text-sm flex items-center gap-2 ${
                    network.active 
                      ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400' 
                      : 'border-zinc-700 bg-zinc-800/50 text-zinc-500'
                  }`}
                >
                  <span>{network.icon}</span>
                  <span>{network.name}</span>
                  {network.active && <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />}
                </div>
              ))}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-6">
              {[
                { icon: Globe, label: 'Networks', value: '5+' },
                { icon: Users, label: 'Active Traders', value: '1K+' },
                { icon: Zap, label: 'Markets', value: 'Real-time' },
              ].map((stat, i) => (
                <div key={i} className="text-center">
                  <stat.icon className="w-6 h-6 text-emerald-400 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-white">{stat.value}</div>
                  <div className="text-xs text-zinc-500 uppercase tracking-wider">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right side - Auth form */}
        <div className="flex-1 flex items-center justify-center px-8 py-12 lg:py-0">
          <div className="w-full max-w-md">
            <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-800 rounded-2xl p-8 shadow-2xl">
              {/* Tabs */}
              <div className="flex mb-8 bg-zinc-800 rounded-lg p-1">
                <button
                  onClick={() => setIsLoginMode(true)}
                  className={`flex-1 py-2.5 text-sm font-medium rounded-md transition-all ${
                    isLoginMode 
                      ? 'bg-emerald-500 text-black' 
                      : 'text-zinc-400 hover:text-white'
                  }`}
                  data-testid="login-tab"
                >
                  Sign In
                </button>
                <button
                  onClick={() => setIsLoginMode(false)}
                  className={`flex-1 py-2.5 text-sm font-medium rounded-md transition-all ${
                    !isLoginMode 
                      ? 'bg-emerald-500 text-black' 
                      : 'text-zinc-400 hover:text-white'
                  }`}
                  data-testid="register-tab"
                >
                  Create Account
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                {!isLoginMode && (
                  <div>
                    <label className="block text-sm font-medium text-zinc-400 mb-2">Username</label>
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
                      placeholder="Choose a username"
                      className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                      required={!isLoginMode}
                      minLength={3}
                      maxLength={30}
                      data-testid="username-input"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                    required
                    data-testid="email-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors pr-12"
                      required
                      minLength={6}
                      data-testid="password-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-emerald-600 text-black font-semibold rounded-lg hover:from-emerald-400 hover:to-emerald-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
                  data-testid="submit-button"
                >
                  {isSubmitting ? (
                    <span className="animate-pulse">Processing...</span>
                  ) : (
                    <>
                      {isLoginMode ? 'Sign In' : 'Create Account'}
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </button>
              </form>

              {/* Bonus info */}
              {!isLoginMode && (
                <div className="mt-6 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                  <p className="text-sm text-emerald-400">
                    🎁 New accounts receive <span className="font-bold">1,000 credits</span> to start trading!
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
