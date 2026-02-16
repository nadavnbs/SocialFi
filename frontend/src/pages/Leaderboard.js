import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { toast, Toaster } from 'sonner';
import { 
  TrendingUp, Briefcase, Trophy, LogOut, Crown, Medal, Award
} from 'lucide-react';

export default function Leaderboard() {
  const { user, isAuthenticated, logout } = useAuth();
  const history = useHistory();
  
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('xp');

  useEffect(() => {
    if (!isAuthenticated) {
      history.push('/');
      return;
    }
    fetchLeaderboard();
  }, [isAuthenticated, history, sortBy]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/leaderboard', {
        params: { sort_by: sortBy, limit: 50 }
      });
      setLeaderboard(response.data.leaderboard || []);
    } catch (error) {
      toast.error('Failed to load leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank) => {
    switch (rank) {
      case 1:
        return <Crown className="w-5 h-5 text-yellow-400" />;
      case 2:
        return <Medal className="w-5 h-5 text-zinc-400" />;
      case 3:
        return <Award className="w-5 h-5 text-amber-600" />;
      default:
        return <span className="text-zinc-500 font-mono">#{rank}</span>;
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
                  className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors flex items-center gap-2"
                >
                  <Briefcase className="w-4 h-4" /> Portfolio
                </button>
                <button 
                  onClick={() => history.push('/leaderboard')}
                  className="px-4 py-2 text-sm font-medium text-emerald-400 bg-emerald-500/10 rounded-lg flex items-center gap-2"
                >
                  <Trophy className="w-4 h-4" /> Leaderboard
                </button>
              </nav>
            </div>

            <button
              onClick={logout}
              className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-white mb-2">Leaderboard</h1>
          <p className="text-zinc-500">Top traders ranked by performance</p>
        </div>

        {/* Sort tabs */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex bg-zinc-800 rounded-lg p-1">
            {[
              { id: 'xp', label: 'XP' },
              { id: 'reputation', label: 'Reputation' },
              { id: 'balance', label: 'Balance' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSortBy(tab.id)}
                className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                  sortBy === tab.id
                    ? 'bg-emerald-500 text-black'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Leaderboard table */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          {loading ? (
            <div className="p-12 text-center">
              <div className="text-emerald-400 animate-pulse">Loading...</div>
            </div>
          ) : leaderboard.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-4xl mb-4">🏆</div>
              <h3 className="text-lg font-medium text-white mb-2">No traders yet</h3>
              <p className="text-zinc-500">Be the first to claim the top spot!</p>
            </div>
          ) : (
            <div className="divide-y divide-zinc-800">
              {leaderboard.map((entry, index) => (
                <div 
                  key={index} 
                  className={`p-4 flex items-center gap-4 hover:bg-zinc-800/50 transition-colors ${
                    entry.wallet_address?.includes(user?.wallet_address?.slice(0, 10)) ? 'bg-emerald-500/5 border-l-2 border-emerald-500' : ''
                  }`}
                >
                  <div className="w-12 flex justify-center">
                    {getRankIcon(entry.rank)}
                  </div>
                  
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center text-black font-bold">
                    {entry.wallet_address?.[2]?.toUpperCase() || '?'}
                  </div>
                  
                  <div className="flex-1">
                    <div className="font-medium text-white font-mono">
                      {entry.wallet_address}
                      {user?.wallet_address && entry.wallet_address?.includes(user.wallet_address.slice(0, 10)) && (
                        <span className="ml-2 text-xs text-emerald-400">(You)</span>
                      )}
                    </div>
                    <div className="text-xs text-zinc-500">
                      Level {entry.level}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-lg font-bold text-white">
                      {sortBy === 'xp' && `${entry.xp?.toLocaleString()} XP`}
                      {sortBy === 'reputation' && `${entry.reputation?.toFixed(1)} rep`}
                      {sortBy === 'balance' && `${entry.balance_credits?.toFixed(0)} credits`}
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
