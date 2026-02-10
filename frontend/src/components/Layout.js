import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { TrendingUp, BarChart3, LogOut, Wallet } from 'lucide-react';

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-8">
              <Link to="/" className="flex items-center space-x-2">
                <TrendingUp className="h-6 w-6 text-blue-600" />
                <span className="text-xl font-bold text-gray-900">InfoFi</span>
              </Link>
              <div className="hidden md:flex space-x-4">
                <Link to="/" className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === '/' ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50'
                }`}>
                  Feed
                </Link>
                <Link to="/portfolio" className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === '/portfolio' ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50'
                }`}>
                  Portfolio
                </Link>
                {user?.is_admin && (
                  <Link to="/admin" className={`px-3 py-2 rounded-md text-sm font-medium ${
                    location.pathname === '/admin' ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50'
                  }`}>
                    Admin
                  </Link>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 px-4 py-2 bg-blue-50 rounded-lg">
                <Wallet className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-semibold text-blue-900">
                  {user?.balance_credits?.toFixed(2) || '0.00'} credits
                </span>
              </div>
              <div className="text-sm text-gray-600">
                {user?.username}
              </div>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
