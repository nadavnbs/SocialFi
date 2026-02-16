import React, { useState, useEffect, useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { toast, Toaster } from 'sonner';
import { 
  TrendingUp, Clock, DollarSign, BarChart3, RefreshCw, 
  ExternalLink, MessageCircle, Heart, Share2, X, Plus, 
  Briefcase, Trophy, LogOut, Filter, Link as LinkIcon 
} from 'lucide-react';

const NETWORKS = [
  { id: 'reddit', name: 'Reddit', icon: '🔴', color: 'bg-orange-500' },
  { id: 'farcaster', name: 'Farcaster', icon: '🟣', color: 'bg-purple-500' },
  { id: 'x', name: 'X', icon: '⚫', color: 'bg-zinc-600' },
  { id: 'instagram', name: 'Instagram', icon: '📷', color: 'bg-pink-500' },
  { id: 'twitch', name: 'Twitch', icon: '💜', color: 'bg-violet-500' },
];

const SORT_OPTIONS = [
  { id: 'trending', label: 'Trending', icon: TrendingUp },
  { id: 'new', label: 'New', icon: Clock },
  { id: 'price', label: 'Price', icon: DollarSign },
  { id: 'volume', label: 'Volume', icon: BarChart3 },
];

export default function Feed() {
  const { user, isAuthenticated, logout, refreshUser, connectedAddress } = useAuth();
  const history = useHistory();
  
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedNetworks, setSelectedNetworks] = useState([]);
  const [sortBy, setSortBy] = useState('trending');
  const [showTradeModal, setShowTradeModal] = useState(null);
  const [tradeAmount, setTradeAmount] = useState(1);
  const [tradeLoading, setTradeLoading] = useState(false);
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pasteUrl, setPasteUrl] = useState('');
  const [pasteLoading, setPasteLoading] = useState(false);

  const fetchPosts = useCallback(async () => {
    try {
      setLoading(true);
      const networkFilter = selectedNetworks.length > 0 ? selectedNetworks.join(',') : '';
      const response = await axios.get('/feed', {
        params: { networks: networkFilter, sort: sortBy, limit: 50 }
      });
      setPosts(response.data.posts || []);
    } catch (error) {
      toast.error('Failed to load feed');
    } finally {
      setLoading(false);
    }
  }, [selectedNetworks, sortBy]);

  useEffect(() => {
    if (!isAuthenticated) {
      history.push('/');
      return;
    }
    fetchPosts();
  }, [isAuthenticated, history, fetchPosts]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await axios.post('/feed/refresh', null, {
        params: { networks: 'reddit,farcaster' }
      });
      toast.success('Feed refresh started');
      // Wait a bit then fetch new posts
      setTimeout(() => {
        fetchPosts();
        setRefreshing(false);
      }, 2000);
    } catch (error) {
      toast.error('Refresh failed');
      setRefreshing(false);
    }
  };

  const toggleNetwork = (networkId) => {
    setSelectedNetworks(prev => 
      prev.includes(networkId) 
        ? prev.filter(n => n !== networkId)
        : [...prev, networkId]
    );
  };

  const handleTrade = async (type) => {
    if (!showTradeModal || tradeAmount <= 0) return;
    
    setTradeLoading(true);
    try {
      const endpoint = type === 'buy' ? '/trades/buy' : '/trades/sell';
      const response = await axios.post(endpoint, {
        market_id: showTradeModal.market.id,
        shares: tradeAmount
      });
      
      toast.success(`${type === 'buy' ? 'Bought' : 'Sold'} ${tradeAmount} shares for ${response.data.total_cost || response.data.total_revenue} credits`);
      setShowTradeModal(null);
      setTradeAmount(1);
      await refreshUser();
      fetchPosts();
    } catch (error) {
      toast.error(error.response?.data?.detail || `${type} failed`);
    } finally {
      setTradeLoading(false);
    }
  };

  const handlePasteUrl = async () => {
    if (!pasteUrl.trim()) return;
    
    setPasteLoading(true);
    try {
      const response = await axios.post('/posts/paste-url', { url: pasteUrl });
      toast.success(response.data.message);
      setPasteUrl('');
      setShowPasteModal(false);
      fetchPosts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to list post');
    } finally {
      setPasteLoading(false);
    }
  };

  const getNetworkBadge = (network) => {
    const net = NETWORKS.find(n => n.id === network);
    if (!net) return null;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${net.color}/20 text-white`}>
        {net.icon} {net.name}
      </span>
    );
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Toaster position="top-center" theme="dark" />
      
      {/* Header */}
      <header className="sticky top-0 z-40 bg-zinc-900/95 backdrop-blur-lg border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Logo & Nav */}
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-black" />
                </div>
                <span className="text-xl font-bold text-white">SocialFi</span>
              </div>
              
              <nav className="hidden md:flex items-center gap-1">
                <button 
                  onClick={() => history.push('/feed')}
                  className="px-4 py-2 text-sm font-medium text-emerald-400 bg-emerald-500/10 rounded-lg"
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
                  className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors flex items-center gap-2"
                >
                  <Trophy className="w-4 h-4" /> Leaderboard
                </button>
              </nav>
            </div>

            {/* User info & actions */}
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-3 px-4 py-2 bg-zinc-800 rounded-lg">
                <span className="text-sm text-zinc-400">Credits:</span>
                <span className="text-sm font-bold text-emerald-400">
                  {user?.balance_credits?.toFixed(0) || 0}
                </span>
              </div>
              
              <div className="hidden sm:flex items-center gap-2 px-3 py-2 bg-zinc-800 rounded-lg">
                <span className="text-xs text-zinc-500">LVL</span>
                <span className="text-sm font-bold text-white">{user?.level || 1}</span>
                <span className="text-xs text-zinc-500">•</span>
                <span className="text-xs text-zinc-400">{user?.xp || 0} XP</span>
              </div>

              {connectedAddress && (
                <div className="hidden md:flex items-center px-3 py-2 bg-zinc-800 rounded-lg">
                  <span className="text-xs font-mono text-zinc-400">
                    {connectedAddress.slice(0, 6)}...{connectedAddress.slice(-4)}
                  </span>
                </div>
              )}

              <button
                onClick={logout}
                className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                data-testid="logout-button"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Filters bar */}
      <div className="sticky top-[61px] z-30 bg-zinc-900/95 backdrop-blur-lg border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            {/* Network filters */}
            <div className="flex items-center gap-2 flex-wrap">
              <Filter className="w-4 h-4 text-zinc-500" />
              {NETWORKS.map((network) => (
                <button
                  key={network.id}
                  onClick={() => toggleNetwork(network.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                    selectedNetworks.includes(network.id)
                      ? 'bg-emerald-500 text-black'
                      : selectedNetworks.length === 0
                      ? 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
                      : 'bg-zinc-800/50 text-zinc-500 hover:bg-zinc-800'
                  }`}
                  data-testid={`filter-${network.id}`}
                >
                  {network.icon} {network.name}
                </button>
              ))}
              {selectedNetworks.length > 0 && (
                <button
                  onClick={() => setSelectedNetworks([])}
                  className="px-2 py-1.5 text-xs text-zinc-500 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Sort & Actions */}
            <div className="flex items-center gap-2">
              <div className="flex items-center bg-zinc-800 rounded-lg p-1">
                {SORT_OPTIONS.map((option) => (
                  <button
                    key={option.id}
                    onClick={() => setSortBy(option.id)}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${
                      sortBy === option.id
                        ? 'bg-emerald-500 text-black'
                        : 'text-zinc-400 hover:text-white'
                    }`}
                    data-testid={`sort-${option.id}`}
                  >
                    <option.icon className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">{option.label}</span>
                  </button>
                ))}
              </div>
              
              <button
                onClick={() => setShowPasteModal(true)}
                className="px-3 py-2 bg-emerald-500 text-black rounded-lg text-xs font-medium hover:bg-emerald-400 transition-colors flex items-center gap-1.5"
                data-testid="paste-url-button"
              >
                <Plus className="w-4 h-4" />
                <span className="hidden sm:inline">List Post</span>
              </button>
              
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors disabled:opacity-50"
                data-testid="refresh-button"
              >
                <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main feed */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-emerald-400 font-mono animate-pulse">Loading feed...</div>
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📭</div>
            <h3 className="text-xl font-semibold text-white mb-2">No posts yet</h3>
            <p className="text-zinc-500 mb-6">Be the first to list content from your favorite networks</p>
            <button
              onClick={() => setShowPasteModal(true)}
              className="px-6 py-3 bg-emerald-500 text-black rounded-lg font-medium hover:bg-emerald-400 transition-colors"
            >
              List a Post
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {posts.map((post) => (
              <article 
                key={post.id} 
                className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden hover:border-zinc-700 transition-colors group"
                data-testid={`post-${post.id}`}
              >
                {/* Header */}
                <div className="p-4 border-b border-zinc-800">
                  <div className="flex items-center justify-between mb-2">
                    {getNetworkBadge(post.source_network)}
                    <a
                      href={post.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-zinc-500 hover:text-white transition-colors"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {post.author_avatar_url ? (
                      <img 
                        src={post.author_avatar_url} 
                        alt={post.author_username}
                        className="w-8 h-8 rounded-full bg-zinc-800"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center text-black text-xs font-bold">
                        {post.author_username?.[0]?.toUpperCase() || '?'}
                      </div>
                    )}
                    <div>
                      <div className="text-sm font-medium text-white">
                        {post.author_display_name || post.author_username || 'Unknown'}
                      </div>
                      {post.subreddit && (
                        <div className="text-xs text-zinc-500">r/{post.subreddit}</div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="p-4">
                  {post.title && (
                    <h3 className="text-sm font-medium text-white mb-2 line-clamp-2">
                      {post.title}
                    </h3>
                  )}
                  {post.content_text && (
                    <p className="text-sm text-zinc-400 line-clamp-3 mb-3">
                      {post.content_text}
                    </p>
                  )}
                  
                  {/* Media preview */}
                  {post.media_urls && post.media_urls.length > 0 && (
                    <div className="mb-3 rounded-lg overflow-hidden bg-zinc-800">
                      <img 
                        src={post.media_urls[0]} 
                        alt=""
                        className="w-full h-40 object-cover"
                        onError={(e) => e.target.style.display = 'none'}
                      />
                    </div>
                  )}

                  {/* Engagement stats */}
                  <div className="flex items-center gap-4 text-xs text-zinc-500 mb-4">
                    <span className="flex items-center gap-1">
                      <Heart className="w-3.5 h-3.5" />
                      {post.source_likes?.toLocaleString() || 0}
                    </span>
                    <span className="flex items-center gap-1">
                      <MessageCircle className="w-3.5 h-3.5" />
                      {post.source_comments?.toLocaleString() || 0}
                    </span>
                    {post.source_shares > 0 && (
                      <span className="flex items-center gap-1">
                        <Share2 className="w-3.5 h-3.5" />
                        {post.source_shares?.toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>

                {/* Market info & Trade */}
                {post.market && (
                  <div className="p-4 bg-zinc-800/50 border-t border-zinc-800">
                    <div className="grid grid-cols-3 gap-2 mb-3 text-center">
                      <div>
                        <div className="text-xs text-zinc-500">Price</div>
                        <div className="text-sm font-bold text-emerald-400">
                          {post.market.price_current?.toFixed(2)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-500">Supply</div>
                        <div className="text-sm font-bold text-white">
                          {Math.floor(post.market.total_supply)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-500">Volume</div>
                        <div className="text-sm font-bold text-cyan-400">
                          {Math.floor(post.market.total_volume)}
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => setShowTradeModal(post)}
                        className="py-2 bg-emerald-500 text-black text-xs font-semibold rounded-lg hover:bg-emerald-400 transition-colors"
                        data-testid={`buy-${post.id}`}
                      >
                        BUY
                      </button>
                      <button
                        onClick={() => setShowTradeModal(post)}
                        className="py-2 bg-rose-500/20 text-rose-400 text-xs font-semibold rounded-lg hover:bg-rose-500/30 transition-colors border border-rose-500/30"
                        data-testid={`sell-${post.id}`}
                      >
                        SELL
                      </button>
                    </div>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </main>

      {/* Trade Modal */}
      {showTradeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={() => setShowTradeModal(null)}>
          <div 
            className="bg-zinc-900 border border-zinc-700 rounded-2xl w-full max-w-md p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white">Trade Shares</h3>
              <button onClick={() => setShowTradeModal(null)} className="text-zinc-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-6 p-4 bg-zinc-800 rounded-lg">
              <div className="text-sm text-zinc-400 mb-1">
                {showTradeModal.title || showTradeModal.content_text?.slice(0, 50) || 'Post'}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-500">Current Price</span>
                <span className="text-lg font-bold text-emerald-400">
                  {showTradeModal.market?.price_current?.toFixed(4)} credits
                </span>
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm text-zinc-400 mb-2">Number of Shares</label>
              <input
                type="number"
                min="1"
                step="1"
                value={tradeAmount}
                onChange={(e) => setTradeAmount(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-lg font-mono focus:outline-none focus:border-emerald-500"
                data-testid="trade-amount-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => handleTrade('buy')}
                disabled={tradeLoading}
                className="py-3 bg-emerald-500 text-black font-semibold rounded-lg hover:bg-emerald-400 transition-colors disabled:opacity-50"
                data-testid="confirm-buy"
              >
                {tradeLoading ? 'Processing...' : 'Buy'}
              </button>
              <button
                onClick={() => handleTrade('sell')}
                disabled={tradeLoading}
                className="py-3 bg-rose-500 text-white font-semibold rounded-lg hover:bg-rose-400 transition-colors disabled:opacity-50"
                data-testid="confirm-sell"
              >
                {tradeLoading ? 'Processing...' : 'Sell'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Paste URL Modal */}
      {showPasteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={() => setShowPasteModal(false)}>
          <div 
            className="bg-zinc-900 border border-zinc-700 rounded-2xl w-full max-w-lg p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white">List a Post</h3>
              <button onClick={() => setShowPasteModal(false)} className="text-zinc-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-sm text-zinc-400 mb-4">
              Paste a URL from Reddit, Farcaster, X, Instagram, or Twitch to create a tradable market.
            </p>

            <div className="mb-4">
              <div className="relative">
                <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <input
                  type="url"
                  value={pasteUrl}
                  onChange={(e) => setPasteUrl(e.target.value)}
                  placeholder="https://reddit.com/r/..."
                  className="w-full pl-12 pr-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500"
                  data-testid="paste-url-input"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-2 mb-6 text-xs text-zinc-500">
              <span className="px-2 py-1 bg-zinc-800 rounded">🔴 reddit.com</span>
              <span className="px-2 py-1 bg-zinc-800 rounded">🟣 warpcast.com</span>
              <span className="px-2 py-1 bg-zinc-800 rounded">⚫ x.com / twitter.com</span>
              <span className="px-2 py-1 bg-zinc-800 rounded">📷 instagram.com</span>
              <span className="px-2 py-1 bg-zinc-800 rounded">💜 twitch.tv</span>
            </div>

            <button
              onClick={handlePasteUrl}
              disabled={pasteLoading || !pasteUrl.trim()}
              className="w-full py-3 bg-emerald-500 text-black font-semibold rounded-lg hover:bg-emerald-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="submit-paste-url"
            >
              {pasteLoading ? 'Creating Market...' : 'Create Market'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
