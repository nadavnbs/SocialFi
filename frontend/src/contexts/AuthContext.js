import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import Web3 from 'web3';
import axios from 'axios';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [connectedAddress, setConnectedAddress] = useState(null);
  const [web3, setWeb3] = useState(null);
  const [chainName, setChainName] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedAddress = localStorage.getItem('wallet_address');
    if (token && savedAddress) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setConnectedAddress(savedAddress);
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get('/auth/me');
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      localStorage.removeItem('token');
      localStorage.removeItem('wallet_address');
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const connectWallet = async () => {
    if (!window.ethereum) {
      throw new Error('Please install MetaMask!');
    }

    const web3Instance = new Web3(window.ethereum);
    await window.ethereum.request({ method: 'eth_requestAccounts' });
    
    const accounts = await web3Instance.eth.getAccounts();
    const chainId = await web3Instance.eth.getChainId();
    
    const chainNames = {
      1: 'ethereum', 1n: 'ethereum',
      8453: 'base', 8453n: 'base',
      137: 'polygon', 137n: 'polygon',
      56: 'bnb', 56n: 'bnb'
    };
    
    setWeb3(web3Instance);
    setConnectedAddress(accounts[0]);
    setChainName(chainNames[chainId] || 'ethereum');
    
    return { address: accounts[0], chain: chainNames[chainId] || 'ethereum' };
  };

  const authenticate = async (signature, challenge) => {
    const response = await axios.post('/auth/verify', {
      wallet_address: connectedAddress,
      challenge,
      signature,
      chain_type: chainName
    });
    
    localStorage.setItem('token', response.data.access_token);
    localStorage.setItem('wallet_address', connectedAddress);
    axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
    setUser(response.data.user);
    setIsAuthenticated(true);
    return response.data;
  };

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('wallet_address');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    setIsAuthenticated(false);
    setConnectedAddress(null);
    setWeb3(null);
  }, []);

  const refreshUser = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      await fetchUser();
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    connectedAddress,
    web3,
    chainName,
    connectWallet,
    authenticate,
    logout,
    refreshUser
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
