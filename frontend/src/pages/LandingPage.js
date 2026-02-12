import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAccount, useSignMessage } from 'wagmi';
import { useWallet } from '@solana/wallet-adapter-react';
import { useWalletModal } from '@solana/wallet-adapter-react-ui';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { toast, Toaster } from 'sonner';

export default function LandingPage() {
  const navigate = useNavigate();
  const { isAuthenticated, connectedAddress, chainType, authenticate } = useAuth();
  const { address: evmAddress, isConnected: isEvmConnected } = useAccount();
  const { signMessage: signEVMMessage } = useSignMessage();
  const { publicKey, signMessage: signSolanaMessage, connected: isSolanaConnected } = useWallet();
  const { setVisible: setSolanaModalVisible } = useWalletModal();
  
  const [challenge, setChallenge] = useState(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/feed');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (connectedAddress && !isAuthenticated) {
      requestChallenge();
    }
  }, [connectedAddress]);

  const requestChallenge = async () => {
    try {
      const response = await axios.post('/auth/challenge', {
        wallet_address: connectedAddress,
        chain_type: chainType
      });
      setChallenge(response.data.challenge);
      toast.info('Sign the message to authenticate');
    } catch (error) {
      toast.error('Failed to get challenge');
    }
  };

  const handleSignAndAuthenticate = async () => {
    if (!challenge || isAuthenticating) return;
    
    setIsAuthenticating(true);
    try {
      let signature;
      
      if (evmAddress) {
        const result = await signEVMMessage({ message: challenge });
        signature = result;
      } else if (publicKey) {
        const messageBytes = new TextEncoder().encode(challenge);
        const signedMessage = await signSolanaMessage(messageBytes);
        signature = Buffer.from(signedMessage).toString('hex');
      }

      if (signature) {
        await authenticate(signature, challenge);
        toast.success('🎮 Welcome to the Arcade!');
        navigate('/feed');
      }
    } catch (error) {
      toast.error('Authentication failed');
      setChallenge(null);
    } finally {
      setIsAuthenticating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4 relative overflow-hidden">
      <Toaster position="top-center" theme="dark" />
      
      {/* Animated background grid */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0" style={{
          backgroundImage: 'linear-gradient(#22c55e 1px, transparent 1px), linear-gradient(90deg, #22c55e 1px, transparent 1px)',
          backgroundSize: '50px 50px',
          animation: 'grid-move 20s linear infinite'
        }}></div>
      </div>

      <div className="relative z-10 max-w-4xl w-full">
        {/* Terminal-style main card */}
        <div className="terminal-card p-8">
          <div className="terminal-header">
            <div className="terminal-dot dot-red"></div>
            <div className="terminal-dot dot-yellow"></div>
            <div className="terminal-dot dot-green"></div>
            <span className="text-xs text-muted-foreground ml-2 font-['Space_Mono']">SOCIALFI_ARCADE.EXE</span>
          </div>

          <div className="p-8 space-y-8">
            {/* Logo / Title */}
            <div className="text-center space-y-4">
              <h1 className="font-['Press_Start_2P'] text-3xl md:text-5xl text-primary neon-text mb-4 leading-relaxed">
                SOCIALFI<br/>ARCADE
              </h1>
              <div className="font-['VT323'] text-2xl text-secondary">
                [TRADE ATTENTION • EARN COINS • DOMINATE LEADERBOARDS]
              </div>
              <p className="font-['Space_Mono'] text-muted-foreground max-w-2xl mx-auto text-sm">
                Every post is a tradable asset. Buy low, sell high. Level up. Become a legend.
              </p>
            </div>

            {/* Stats display */}
            <div className="grid grid-cols-3 gap-4 py-6">
              {[
                { label: 'POSTS', value: '1,337', color: 'text-primary' },
                { label: 'TRADERS', value: '420', color: 'text-secondary' },
                { label: 'VOLUME', value: '$69K', color: 'text-accent' }
              ].map((stat, i) => (
                <div key={i} className="text-center pixel-border p-4 bg-black/50">
                  <div className={`arcade-score ${stat.color}`}>{stat.value}</div>
                  <div className="font-['Press_Start_2P'] text-[8px] text-muted-foreground mt-2">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* Wallet Connection */}
            <div className="space-y-4">
              {!connectedAddress ? (
                <div className="space-y-4">
                  <div className="text-center">
                    <p className="font-['Press_Start_2P'] text-xs text-foreground mb-6">
                      [INSERT COIN]
                    </p>
                  </div>
                  
                  {/* EVM Chains */}
                  <div className="flex justify-center">
                    <ConnectButton.Custom>
                      {({ openConnectModal }) => (
                        <button onClick={openConnectModal} className="pixel-btn">
                          🌐 CONNECT EVM WALLET
                        </button>
                      )}
                    </ConnectButton.Custom>
                  </div>

                  {/* Solana */}
                  <div className="flex justify-center">
                    <button
                      onClick={() => setSolanaModalVisible(true)}
                      className="pixel-btn"
                      style={{ borderColor: '#ec4899', color: '#ec4899', background: 'rgba(236, 72, 153, 0.1)' }}
                    >
                      ◆ CONNECT SOLANA
                    </button>
                  </div>

                  <div className="text-center">
                    <p className="font-['Space_Mono'] text-xs text-muted-foreground">
                      Supports: Ethereum • Base • Polygon • BNB • Solana
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="pixel-border p-6 bg-black/70 text-center">
                    <div className="font-['VT323'] text-xl text-primary mb-2">WALLET DETECTED</div>
                    <div className="font-['Space_Mono'] text-sm text-muted-foreground mb-4">
                      {connectedAddress.slice(0, 6)}...{connectedAddress.slice(-4)}
                    </div>
                    
                    {challenge && !isAuthenticating && (
                      <button
                        onClick={handleSignAndAuthenticate}
                        className="pixel-btn w-full"
                      >
                        🎮 SIGN & ENTER ARCADE
                      </button>
                    )}
                    
                    {isAuthenticating && (
                      <div className="font-['Press_Start_2P'] text-xs text-accent loading-pulse">
                        AUTHENTICATING...
                      </div>
                    )}
                  </div>

                  <div className="flex justify-center">
                    <ConnectButton />
                  </div>
                </div>
              )}
            </div>

            {/* Features */}
            <div className="grid md:grid-cols-3 gap-4 pt-8">
              {[
                { icon: '📈', title: 'TRADE POSTS', desc: 'Buy & sell attention shares' },
                { icon: '⚡', title: 'EARN XP', desc: 'Level up your trader status' },
                { icon: '🏆', title: 'COMPETE', desc: 'Climb the leaderboards' }
              ].map((feature, i) => (
                <div key={i} className="pixel-border p-4 bg-muted/20">
                  <div className="text-3xl mb-2">{feature.icon}</div>
                  <div className="font-['Press_Start_2P'] text-[10px] text-foreground mb-2">{feature.title}</div>
                  <div className="font-['Space_Mono'] text-xs text-muted-foreground">{feature.desc}</div>
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="text-center pt-8 border-t-2 border-border">
              <p className="font-['Space_Mono'] text-xs text-muted-foreground">
                © 2026 SOCIALFI ARCADE • POWERED BY BONDING CURVES • NO RUGS
              </p>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes grid-move {
          0% { transform: translateY(0); }
          100% { transform: translateY(50px); }
        }
      `}</style>
    </div>
  );
}
