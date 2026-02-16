import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { toast, Toaster } from 'sonner';
import { 
  TrendingUp, ArrowUpRight, ArrowDownRight, Briefcase, 
  Trophy, LogOut, RefreshCw, ExternalLink 
} from 'lucide-react';

export default function Portfolio() {
  const { user, isAuthenticated, logout, refreshUser } = useAuth();
  const history = useHistory();
  
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      history.push('/');
      return;
    }
    fetchPortfolio();
  }, [isAuthenticated, history]);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/portfolio');
      setPortfolio(response.data);
    } catch (error) {
      toast.error('Failed to load portfolio');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Toaster position="top-center" theme="dark" />
      
      {/* Header */}
      <header className="sticky top-0 z-40 bg-zinc-900/95 backdrop-blur-lg border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2 cursor-pointer" onClick={() => history.push('/feed')}>
                <div className="w-9 h-9 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-black" />
                </div>
                <span className="text-xl font-bold text-white">SocialFi</span>
              </div>
              
              <nav className="hidden md:flex items-center gap-1">
                <button 
                  onClick={() => history.push('/feed')}
                  className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                >
                  Feed
                </button>
                <button 
                  onClick={() => history.push('/portfolio')}
                  className="px-4 py-2 text-sm font-medium text-emerald-400 bg-emerald-500/10 rounded-lg flex items-center gap-2"
                >
                  <Briefcase className="w-4 h-4" /> Portfolio
                </button>
                <button 
                  onClick={() => history.push('/leaderboard')}
                  className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors flex items-center gap-2"
                >
                  <Trophy className="w-4 h-4" /> Leaderboard
                </button>
              </nav>
            </div>

            <div className="flex items-center gap-4">
              <button
                onClick={fetchPortfolio}
                className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
              <button
                onClick={logout}
                className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Portfolio Summary */}
        <div className="grid gap-4 md:grid-cols-3 mb-8">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <div className="text-sm text-zinc-500 mb-1">Total Portfolio Value</div>
            <div className="text-3xl font-bold text-white">
              {portfolio?.total_portfolio?.toFixed(2) || '0.00'}
              <span className="text-sm text-zinc-500 ml-1">credits</span>
            </div>
          </div>
          
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <div className="text-sm text-zinc-500 mb-1">Holdings Value</div>
            <div className="text-3xl font-bold text-emerald-400">
              {portfolio?.total_value?.toFixed(2) || '0.00'}
              <span className="text-sm text-zinc-500 ml-1">credits</span>
            </div>
          </div>
          
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <div className="text-sm text-zinc-500 mb-1">Cash Balance</div>
            <div className="text-3xl font-bold text-cyan-400">
              {portfolio?.cash_balance?.toFixed(2) || '0.00'}
              <span className="text-sm text-zinc-500 ml-1">credits</span>
            </div>
          </div>
        </div>

        {/* Positions */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-zinc-800">
            <h2 className="text-lg font-semibold text-white">Your Positions</h2>
          </div>
          
          {loading ? (
            <div className="p-12 text-center">
              <div className="text-emerald-400 animate-pulse">Loading...</div>
            </div>
          ) : !portfolio?.positions || portfolio.positions.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-white mb-2">No positions yet</h3>
              <p className="text-zinc-500 mb-4">Start trading to build your portfolio</p>
              <button
                onClick={() => history.push('/feed')}
                className="px-6 py-2 bg-emerald-500 text-black rounded-lg font-medium hover:bg-emerald-400 transition-colors"
              >
                Browse Feed
              </button>
            </div>
          ) : (
            <div className="divide-y divide-zinc-800">
              {portfolio.positions.map((position, index) => (
                <div key={index} className="p-4 hover:bg-zinc-800/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs px-2 py-0.5 bg-zinc-800 rounded-full text-zinc-400">
                          {position.post?.source_network || 'Unknown'}
                        </span>
                        {position.post?.source_url && (
                          <a 
                            href={position.post.source_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-zinc-500 hover:text-white"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                      <div className="text-sm text-white font-medium line-clamp-1">
                        {position.post?.title || position.post?.content_text || 'Post'}
                      </div>
                      <div className="text-xs text-zinc-500 mt-1">
                        by {position.post?.author_username || 'Unknown'}
                      </div>
                    </div>
                    
                    <div className="text-right ml-4">
                      <div className="text-sm text-zinc-400">
                        {position.shares} shares @ {position.avg_price?.toFixed(4)}
                      </div>
                      <div className="text-lg font-bold text-white">
                        {position.current_value?.toFixed(2)} credits
                      </div>
                      <div className={`text-sm font-medium flex items-center justify-end gap-1 ${
                        position.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}>
                        {position.pnl >= 0 ? (
                          <ArrowUpRight className="w-4 h-4" />
                        ) : (
                          <ArrowDownRight className="w-4 h-4" />
                        )}
                        {position.pnl >= 0 ? '+' : ''}{position.pnl?.toFixed(2)} ({position.pnl_percent?.toFixed(1)}%)
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
