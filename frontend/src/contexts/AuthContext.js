import React, { createContext, useState, useContext, useEffect } from 'react';
import { BrowserProvider } from 'ethers';
import axios from 'axios';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [connectedAddress, setConnectedAddress] = useState(null);
  const [provider, setProvider] = useState(null);
  const [chainName, setChainName] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token && connectedAddress) {
      fetchUser(token);
    }
  }, [connectedAddress]);

  const fetchUser = async (token) => {
    try {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      const response = await axios.get('/auth/me');
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      logout();
    }
  };

  const connectWallet = async () => {
    if (!window.ethereum) {
      alert('Please install MetaMask or another Web3 wallet');
      return;
    }

    try {
      const provider = new BrowserProvider(window.ethereum);
      const accounts = await provider.send('eth_requestAccounts', []);
      const network = await provider.getNetwork();
      
      const chainId = Number(network.chainId);
      const chainNames = {
        1: 'ethereum',
        8453: 'base',
        137: 'polygon',
        56: 'bnb'
      };
      
      setProvider(provider);
      setConnectedAddress(accounts[0]);
      setChainName(chainNames[chainId] || 'ethereum');
      
      return { address: accounts[0], chain: chainNames[chainId] || 'ethereum' };
    } catch (error) {
      console.error('Wallet connection failed:', error);
      throw error;
    }
  };

  const authenticate = async (signature, challenge) => {
    setLoading(true);
    try {
      const response = await axios.post('/auth/verify', {
        wallet_address: connectedAddress,
        challenge,
        signature,
        chain_type: chainName
      });
      
      localStorage.setItem('token', response.data.access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      setUser(response.data.user);
      setIsAuthenticated(true);
      return response.data;
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    setIsAuthenticated(false);
    setConnectedAddress(null);
    setProvider(null);
  };

  const refreshUser = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      await fetchUser(token);
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    connectedAddress,
    provider,
    chainName,
    connectWallet,
    authenticate,
    logout,
    refreshUser
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
