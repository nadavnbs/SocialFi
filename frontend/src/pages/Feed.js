import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { toast, Toaster } from 'sonner';

export default function Feed() {
  const { user, isAuthenticated, logout } = useAuth();
  const history = useHistory();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('volume');

  useEffect(() => {
    if (!isAuthenticated) {
      history.push('/');
      return;
    }
    fetchPosts();
  }, [isAuthenticated, sortBy, history]);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/posts?sort=${sortBy}&limit=50`);
      setPosts(response.data);
    } catch (error) {
      toast.error('Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-[#050505]">
      <Toaster position="top-center" theme="dark" />
      
      {/* Header */}
      <div className="terminal-card border-b-0">
        <div className="terminal-header">
          <div className="terminal-dot dot-red"></div>
          <div className="terminal-dot dot-yellow"></div>
          <div className="terminal-dot dot-green"></div>
          <span className="text-xs text-muted-foreground ml-2 font-['Space_Mono']">ARCADE_FEED.EXE</span>
        </div>
        
        <div className="p-6 flex justify-between items-center">
          <h1 className="font-['Press_Start_2P'] text-2xl text-primary neon-text">
            🎮 ARCADE FEED
          </h1>
          
          <div className="flex items-center space-x-6">
            <div className="pixel-border px-4 py-2 bg-black/50">
              <div className="font-['VT323'] text-lg text-foreground">
                LVL {user?.level || 1} • {user?.xp || 0} XP
              </div>
            </div>
            
            <div className="pixel-border px-4 py-2 bg-black/50">
              <div className="font-['VT323'] text-lg text-accent">
                💰 {Math.floor(user?.balance_credits || 0)} COINS
              </div>
            </div>
            
            <button 
              onClick={logout}
              className="pixel-btn"
              style={{ fontSize: '8px', padding: '8px 16px' }}
            >
              LOGOUT
            </button>
          </div>
        </div>

        {/* Sort tabs */}
        <div className="flex space-x-4 px-6 pb-4">
          {[
            { key: 'volume', label: '🔥 TRENDING', icon: '📈' },
            { key: 'price', label: '💎 TOP PRICE', icon: '💰' },
            { key: 'new', label: '⚡ NEW', icon: '🆕' }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setSortBy(tab.key)}
              className={`font-['Press_Start_2P'] text-[10px] px-4 py-2 transition-all ${
                sortBy === tab.key
                  ? 'bg-primary text-black'
                  : 'bg-muted text-muted-foreground hover:bg-muted/50'
              }`}
              style={{ border: sortBy === tab.key ? '2px solid #22c55e' : '2px solid #3f3f46' }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Feed */}
      <div className="max-w-7xl mx-auto p-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="font-['Press_Start_2P'] text-primary text-xl loading-pulse">
              LOADING...
            </div>
          </div>
        ) : posts.length === 0 ? (
          <div className="terminal-card p-12 text-center">
            <div className="font-['VT323'] text-2xl text-muted-foreground">
              NO POSTS YET. BE THE FIRST TO CREATE ONE!
            </div>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {posts.map((post) => (
              <div key={post._id} className="terminal-card" data-testid={`post-${post._id}`}>
                <div className="terminal-header">
                  <div className="terminal-dot dot-green"></div>
                  <div className="terminal-dot dot-yellow"></div>
                  <div className="terminal-dot dot-red"></div>
                  <span className="text-[10px] text-muted-foreground ml-2 font-['Space_Mono']">
                    {post.user_wallet?.slice(0, 6)}...{post.user_wallet?.slice(-4)}
                  </span>
                </div>
                
                <div className="p-4 space-y-3">
                  <p className="font-['Space_Mono'] text-sm text-foreground min-h-[60px]">
                    {post.content}
                  </p>

                  {post.market && (
                    <div className="pixel-border p-3 bg-black/50 space-y-2">
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div>
                          <div className="font-['VT323'] text-xs text-muted-foreground">PRICE</div>
                          <div className="font-['VT323'] text-lg text-primary">
                            {post.market.price_current.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="font-['VT323'] text-xs text-muted-foreground">SUPPLY</div>
                          <div className="font-['VT323'] text-lg text-accent">
                            {Math.floor(post.market.total_supply)}
                          </div>
                        </div>
                        <div>
                          <div className="font-['VT323'] text-xs text-muted-foreground">VOLUME</div>
                          <div className="font-['VT323'] text-lg text-secondary">
                            {Math.floor(post.market.total_volume)}
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 pt-2">
                        <button
                          className="pixel-btn"
                          style={{ 
                            padding: '8px 12px', 
                            fontSize: '8px',
                            borderColor: '#22c55e',
                            color: '#22c55e'
                          }}
                          onClick={() => toast.info('Trading coming soon!')}
                        >
                          BUY
                        </button>
                        <button
                          className="pixel-btn"
                          style={{ 
                            padding: '8px 12px', 
                            fontSize: '8px',
                            borderColor: '#ec4899',
                            color: '#ec4899',
                            background: 'rgba(236, 72, 153, 0.1)'
                          }}
                          onClick={() => toast.info('Trading coming soon!')}
                        >
                          SELL
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
