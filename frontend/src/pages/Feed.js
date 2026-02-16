import React from 'react';
import { useHistory } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Feed() {
  const { user, isAuthenticated } = useAuth();
  const history = useHistory();

  if (!isAuthenticated) {
    history.push('/');
    return null;
  }

  return (
    <div className="min-h-screen bg-[#050505] p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="font-['Press_Start_2P'] text-2xl text-primary neon-text mb-8">
          🎮 ARCADE FEED
        </h1>
        <div className="terminal-card p-6">
          <div className="terminal-header">
            <div className="terminal-dot dot-red"></div>
            <div className="terminal-dot dot-yellow"></div>
            <div className="terminal-dot dot-green"></div>
          </div>
          <div className="p-6">
            <p className="font-['Space_Mono'] text-foreground">
              Level {user?.level || 1} • {user?.xp || 0} XP • {user?.balance_credits?.toFixed(0) || 0} COINS
            </p>
            <p className="font-['VT323'] text-xl text-muted-foreground mt-4">
              FEED COMING SOON...
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
