import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader } from '../components/ui/card';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { TrendingUp, Plus, ArrowUp, Clock, DollarSign, Users } from 'lucide-react';
import { toast } from 'sonner';

export default function Feed() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('volume');
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [newPost, setNewPost] = useState({ content: '', image_url: '', link_url: '' });
  const [creating, setCreating] = useState(false);
  const [selectedMarket, setSelectedMarket] = useState(null);
  const [tradeAmount, setTradeAmount] = useState('');
  const [tradeQuote, setTradeQuote] = useState(null);
  const { refreshUser } = useAuth();

  useEffect(() => {
    fetchPosts();
  }, [sortBy]);

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

  const createPost = async () => {
    if (!newPost.content.trim()) {
      toast.error('Post content is required');
      return;
    }
    
    setCreating(true);
    try {
      await axios.post('/posts', newPost);
      toast.success('Post created! Market is live with 100 shares.');
      setShowCreatePost(false);
      setNewPost({ content: '', image_url: '', link_url: '' });
      fetchPosts();
      refreshUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create post');
    } finally {
      setCreating(false);
    }
  };

  const openTradeDialog = async (market, type) => {
    setSelectedMarket({ ...market, tradeType: type });
    setTradeAmount('');
    setTradeQuote(null);
  };

  const calculateQuote = async () => {
    if (!tradeAmount || parseFloat(tradeAmount) <= 0) return;
    
    try {
      const response = await axios.get(`/markets/${selectedMarket.id}/quote`, {
        params: {
          shares: parseFloat(tradeAmount),
          trade_type: selectedMarket.tradeType
        }
      });
      setTradeQuote(response.data);
    } catch (error) {
      toast.error('Failed to calculate quote');
    }
  };

  useEffect(() => {
    if (selectedMarket && tradeAmount) {
      const timer = setTimeout(calculateQuote, 300);
      return () => clearTimeout(timer);
    }
  }, [tradeAmount, selectedMarket]);

  const executeTrade = async () => {
    if (!tradeAmount || parseFloat(tradeAmount) <= 0) {
      toast.error('Enter valid amount');
      return;
    }
    
    try {
      const endpoint = selectedMarket.tradeType === 'buy' ? '/trades/buy' : '/trades/sell';
      await axios.post(endpoint, {
        market_id: selectedMarket.id,
        shares: parseFloat(tradeAmount)
      });
      toast.success(`${selectedMarket.tradeType === 'buy' ? 'Bought' : 'Sold'} ${tradeAmount} shares!`);
      setSelectedMarket(null);
      fetchPosts();
      refreshUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Trade failed');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Loading posts...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Attention Markets</h1>
        <Button onClick={() => setShowCreatePost(true)} data-testid="create-post-button">
          <Plus className="h-4 w-4 mr-2" />
          Create Post
        </Button>
      </div>

      <div className="flex space-x-2 mb-6 border-b border-gray-200">
        {[
          { key: 'volume', label: 'Trending', icon: TrendingUp },
          { key: 'price', label: 'Top Price', icon: DollarSign },
          { key: 'new', label: 'New', icon: Clock }
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setSortBy(tab.key)}
            className={`flex items-center space-x-2 px-4 py-3 border-b-2 font-medium transition-colors ${
              sortBy === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {posts.map((post) => (
          <Card key={post.id} className="hover:shadow-lg transition-shadow" data-testid={`post-card-${post.id}`}>
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm font-medium text-gray-900">{post.user.username}</div>
                  <div className="text-xs text-gray-500">
                    {new Date(post.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded-full font-medium">
                  Rep: {post.user.reputation.toFixed(1)}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-700 line-clamp-3">{post.content}</p>
              
              {post.image_url && (
                <img src={post.image_url} alt="Post" className="w-full h-40 object-cover rounded-lg" />
              )}
              
              {post.market && (
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div>
                      <div className="text-xs text-gray-500">Price</div>
                      <div className="text-sm font-bold text-gray-900">
                        {post.market.price_current.toFixed(4)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Supply</div>
                      <div className="text-sm font-bold text-gray-900">
                        {post.market.total_supply.toFixed(0)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Volume</div>
                      <div className="text-sm font-bold text-gray-900">
                        {post.market.total_volume.toFixed(0)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    <Button
                      size="sm"
                      className="flex-1"
                      onClick={() => openTradeDialog(post.market, 'buy')}
                      data-testid={`buy-button-${post.id}`}
                    >
                      Buy
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1"
                      onClick={() => openTradeDialog(post.market, 'sell')}
                      data-testid={`sell-button-${post.id}`}
                    >
                      Sell
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {posts.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>No posts yet. Be the first to create one!</p>
        </div>
      )}

      <Dialog open={showCreatePost} onOpenChange={setShowCreatePost}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Post</DialogTitle>
            <DialogDescription>
              Share your thoughts. A market will be created automatically (costs 100 credits, you get 100 shares).
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Textarea
                placeholder="What's on your mind? (max 500 characters)"
                value={newPost.content}
                onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                maxLength={500}
                rows={4}
                data-testid="post-content-input"
              />
              <div className="text-xs text-gray-500 mt-1 text-right">
                {newPost.content.length}/500
              </div>
            </div>
            <Input
              placeholder="Image URL (optional)"
              value={newPost.image_url}
              onChange={(e) => setNewPost({ ...newPost, image_url: e.target.value })}
              data-testid="post-image-url-input"
            />
            <Input
              placeholder="Link URL (optional)"
              value={newPost.link_url}
              onChange={(e) => setNewPost({ ...newPost, link_url: e.target.value })}
              data-testid="post-link-url-input"
            />
            <Button
              className="w-full"
              onClick={createPost}
              disabled={creating}
              data-testid="submit-post-button"
            >
              {creating ? 'Creating...' : 'Create Post (100 credits)'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={!!selectedMarket} onOpenChange={() => setSelectedMarket(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {selectedMarket?.tradeType === 'buy' ? 'Buy Shares' : 'Sell Shares'}
            </DialogTitle>
            <DialogDescription>
              Current price: {selectedMarket?.price_current?.toFixed(4)} credits/share
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <label className="text-sm font-medium">Number of shares</label>
              <Input
                type="number"
                placeholder="10"
                value={tradeAmount}
                onChange={(e) => setTradeAmount(e.target.value)}
                min="0.01"
                step="0.01"
                data-testid="trade-amount-input"
              />
            </div>
            
            {tradeQuote && (
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Average Price:</span>
                  <span className="font-medium">{tradeQuote.avg_price.toFixed(4)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">
                    {selectedMarket.tradeType === 'buy' ? 'Cost Before Fee:' : 'Revenue Before Fee:'}
                  </span>
                  <span className="font-medium">
                    {(selectedMarket.tradeType === 'buy' ? tradeQuote.cost_before_fee : tradeQuote.revenue_before_fee).toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Fee (2%):</span>
                  <span className="font-medium">{tradeQuote.fee.toFixed(2)}</span>
                </div>
                <div className="border-t border-gray-200 pt-2 mt-2">
                  <div className="flex justify-between text-base">
                    <span className="font-medium">
                      {selectedMarket.tradeType === 'buy' ? 'Total Cost:' : 'You Receive:'}
                    </span>
                    <span className="font-bold text-blue-600">
                      {(selectedMarket.tradeType === 'buy' ? tradeQuote.total_cost : tradeQuote.total_revenue).toFixed(2)} credits
                    </span>
                  </div>
                </div>
              </div>
            )}
            
            <Button
              className="w-full"
              onClick={executeTrade}
              disabled={!tradeAmount || parseFloat(tradeAmount) <= 0}
              data-testid="execute-trade-button"
            >
              {selectedMarket?.tradeType === 'buy' ? 'Confirm Buy' : 'Confirm Sell'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
