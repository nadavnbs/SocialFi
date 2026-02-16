import React from 'react';
import { BrowserRouter, Switch, Route } from 'react-router-dom';
import axios from 'axios';
import './index.css';
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
    <AuthProvider>
      <div className="scanlines"></div>
      <BrowserRouter>
        <Switch>
          <Route exact path="/" component={LandingPage} />
          <Route path="/feed" component={Feed} />
          <Route path="/portfolio" component={Portfolio} />
          <Route path="/profile" component={Profile} />
          <Route path="/leaderboard" component={Leaderboard} />
        </Switch>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
