import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Briefcase, TrendingUp, TrendingDown } from 'lucide-react';
import { toast } from 'sonner';

export default function Portfolio() {
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const response = await axios.get('/users/me/portfolio');
      setHoldings(response.data);
    } catch (error) {
      toast.error('Failed to load portfolio');
    } finally {
      setLoading(false);
    }
  };

  const totalValue = holdings.reduce((sum, h) => sum + h.current_value, 0);
  const totalInvested = holdings.reduce((sum, h) => sum + (h.shares_owned * h.avg_buy_price), 0);
  const totalPnL = totalValue - totalInvested;

  if (loading) {
    return <div className="text-center py-12 text-gray-500">Loading portfolio...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Portfolio</h1>
        <p className="text-gray-600">Track your holdings and performance</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalValue.toFixed(2)} credits</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Invested</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalInvested.toFixed(2)} credits</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold flex items-center ${
              totalPnL >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {totalPnL >= 0 ? <TrendingUp className="h-5 w-5 mr-1" /> : <TrendingDown className="h-5 w-5 mr-1" />}
              {totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)}
            </div>
          </CardContent>
        </Card>
      </div>

      {holdings.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Briefcase className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No holdings yet. Start trading to build your portfolio!</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {holdings.map((holding) => {
            const pnl = holding.current_value - (holding.shares_owned * holding.avg_buy_price);
            const pnlPercent = ((pnl / (holding.shares_owned * holding.avg_buy_price)) * 100);
            
            return (
              <Card key={holding.id} data-testid={`portfolio-item-${holding.id}`}>
                <CardContent className="pt-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 mb-1">
                        @{holding.post.user.username}'s post
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                        {holding.post.content}
                      </p>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Shares Owned:</span>
                          <span className="ml-2 font-medium">{holding.shares_owned.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Avg Buy Price:</span>
                          <span className="ml-2 font-medium">{holding.avg_buy_price.toFixed(4)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Current Price:</span>
                          <span className="ml-2 font-medium">{holding.post.market.price_current.toFixed(4)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Current Value:</span>
                          <span className="ml-2 font-medium">{holding.current_value.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right ml-6">
                      <div className={`text-lg font-bold ${
                        pnl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
                      </div>
                      <div className={`text-sm ${
                        pnl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {pnl >= 0 ? '+' : ''}{pnlPercent.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
