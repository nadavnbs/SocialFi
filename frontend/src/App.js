import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import './index.css';
import WalletProviders from './WalletProviders';
import { AuthProvider } from './contexts/AuthContext';
import LandingPage from './pages/LandingPage';
import Feed from './pages/Feed';
import Portfolio from './pages/Portfolio';
import Profile from './pages/Profile';
import Leaderboard from './pages/Leaderboard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
axios.defaults.baseURL = `${BACKEND_URL}/api`;

function App() {
  return (
    <WalletProviders>
      <AuthProvider>
        <div className="scanlines"></div>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/feed" element={<Feed />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </WalletProviders>
  );
}

export default App;
