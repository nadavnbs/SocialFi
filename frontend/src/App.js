import React from 'react';
import { BrowserRouter, Switch, Route, Redirect } from 'react-router-dom';
import axios from 'axios';
import './index.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LandingPage from './pages/LandingPage';
import Feed from './pages/Feed';
import Portfolio from './pages/Portfolio';
import Leaderboard from './pages/Leaderboard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
axios.defaults.baseURL = `${BACKEND_URL}/api`;

// Protected Route component
function ProtectedRoute({ component: Component, ...rest }) {
  const { isAuthenticated, loading } = useAuth();
  
  return (
    <Route
      {...rest}
      render={(props) => {
        if (loading) {
          return (
            <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
              <div className="text-primary font-mono text-xl animate-pulse">Loading...</div>
            </div>
          );
        }
        return isAuthenticated ? <Component {...props} /> : <Redirect to="/" />;
      }}
    />
  );
}

function AppRoutes() {
  return (
    <Switch>
      <Route exact path="/" component={LandingPage} />
      <ProtectedRoute path="/feed" component={Feed} />
      <ProtectedRoute path="/portfolio" component={Portfolio} />
      <ProtectedRoute path="/leaderboard" component={Leaderboard} />
    </Switch>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
