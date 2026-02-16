import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { toast, Toaster } from 'sonner';
import { TrendingUp, Users, Zap, Wallet, ArrowRight, Globe, CheckCircle } from 'lucide-react';

export default function LandingPage() {
  const history = useHistory();
  const { isAuthenticated, connectedAddress, chainName, connectWallet, authenticate, loading } = useAuth();
  
  const [challenge, setChallenge] = useState(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  useEffect(() => {
    if (isAuthenticated && !loading) {
      history.push('/feed');
    }
  }, [isAuthenticated, loading, history]);

  useEffect(() => {
    if (connectedAddress && !isAuthenticated) {
      requestChallenge();
    }
  }, [connectedAddress, isAuthenticated]);

  const requestChallenge = async () => {
    try {
      const response = await axios.post('/auth/challenge', {
        wallet_address: connectedAddress,
        chain_type: chainName || 'ethereum'
      });
      setChallenge(response.data.challenge);
      toast.info('Sign the message to authenticate');
    } catch (error) {
      toast.error('Failed to get challenge');
    }
  };

  const handleConnect = async () => {
    try {
      await connectWallet();
      toast.success('Wallet connected!');
    } catch (error) {
      toast.error(error.message || 'Failed to connect wallet');
    }
  };

  const handleSignAndAuthenticate = async () => {
    if (!challenge || isAuthenticating || !connectedAddress) return;
    
    setIsAuthenticating(true);
    try {
      const signature = await window.ethereum.request({
        method: 'personal_sign',
        params: [challenge, connectedAddress],
      });

      if (signature) {
        await authenticate(signature, challenge);
        toast.success('Welcome to SocialFi!');
        history.push('/feed');
      }
    } catch (error) {
      console.error('Sign error:', error);
      toast.error('Authentication failed: ' + (error.message || 'Please try again'));
      setChallenge(null);
    } finally {
      setIsAuthenticating(false);
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
                { icon: Users, label: 'Traders', value: '1K+' },
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

        {/* Right side - Wallet connect */}
        <div className="flex-1 flex items-center justify-center px-8 py-12 lg:py-0">
          <div className="w-full max-w-md">
            <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-800 rounded-2xl p-8 shadow-2xl">
              <h2 className="text-2xl font-bold text-white mb-2 text-center">Connect Wallet</h2>
              <p className="text-zinc-400 text-sm text-center mb-8">
                Sign in with your Web3 wallet to start trading
              </p>

              {!connectedAddress ? (
                <div className="space-y-6">
                  <button
                    onClick={handleConnect}
                    className="w-full py-4 bg-gradient-to-r from-emerald-500 to-emerald-600 text-black font-semibold rounded-xl hover:from-emerald-400 hover:to-emerald-500 transition-all flex items-center justify-center gap-3 group"
                    data-testid="connect-wallet-button"
                  >
                    <Wallet className="w-5 h-5" />
                    Connect Wallet
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </button>

                  <div className="text-center space-y-2">
                    <p className="text-xs text-zinc-500">Supported Networks</p>
                    <div className="flex justify-center gap-2 flex-wrap">
                      {['Ethereum', 'Base', 'Polygon', 'BNB'].map((chain) => (
                        <span key={chain} className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-400">
                          {chain}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                    <p className="text-xs text-amber-400 text-center">
                      🦊 Install MetaMask or Coinbase Wallet to continue
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Connected wallet info */}
                  <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
                    <div className="flex items-center gap-3 mb-3">
                      <CheckCircle className="w-5 h-5 text-emerald-400" />
                      <span className="text-sm font-medium text-emerald-400">Wallet Connected</span>
                    </div>
                    <div className="font-mono text-sm text-white bg-zinc-800 px-3 py-2 rounded-lg break-all">
                      {connectedAddress}
                    </div>
                    <div className="mt-2 text-xs text-zinc-400">
                      Network: <span className="text-emerald-400 uppercase">{chainName || 'Unknown'}</span>
                    </div>
                  </div>

                  {challenge && !isAuthenticating && (
                    <button
                      onClick={handleSignAndAuthenticate}
                      className="w-full py-4 bg-gradient-to-r from-emerald-500 to-emerald-600 text-black font-semibold rounded-xl hover:from-emerald-400 hover:to-emerald-500 transition-all flex items-center justify-center gap-3"
                      data-testid="sign-button"
                    >
                      Sign Message & Enter
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  )}

                  {isAuthenticating && (
                    <div className="text-center py-4">
                      <div className="text-emerald-400 animate-pulse">Authenticating...</div>
                      <p className="text-xs text-zinc-500 mt-2">Please confirm in your wallet</p>
                    </div>
                  )}
                </div>
              )}

              {/* Bonus info */}
              <div className="mt-6 p-4 bg-zinc-800/50 rounded-lg">
                <p className="text-sm text-zinc-400 text-center">
                  🎁 New wallets receive <span className="font-bold text-emerald-400">1,000 credits</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
