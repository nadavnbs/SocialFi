import React, { createContext, useState, useContext, useEffect } from 'react';
import { useAccount, useDisconnect } from 'wagmi';
import { useWallet } from '@solana/wallet-adapter-react';
import axios from 'axios';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const { address: evmAddress, isConnected: isEvmConnected, chain } = useAccount();
  const { publicKey: solanaPublicKey, connected: isSolanaConnected, wallet: solanaWallet } = useWallet();
  const { disconnect: disconnectEvm } = useDisconnect();
  const { disconnect: disconnectSolana } = useWallet();

  const connectedAddress = evmAddress || solanaPublicKey?.toString();
  const isConnected = isEvmConnected || isSolanaConnected;
  const chainType = evmAddress ? (chain?.name?.toLowerCase() || 'ethereum') : 'solana';

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

  const authenticate = async (signature, challenge) => {
    setLoading(true);
    try {
      const response = await axios.post('/auth/verify', {
        wallet_address: connectedAddress,
        challenge,
        signature,
        chain_type: chainType
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
    if (isEvmConnected) disconnectEvm();
    if (isSolanaConnected) disconnectSolana();
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
    isConnected,
    chainType,
    authenticate,
    logout,
    refreshUser
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
