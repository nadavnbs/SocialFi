import React from 'react';
import { WagmiProvider, createConfig, http } from 'wagmi';
import { mainnet, base, polygon, bsc } from 'wagmi/chains';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RainbowKitProvider, getDefaultConfig, darkTheme } from '@rainbow-me/rainbowkit';
import { ConnectionProvider, WalletProvider as SolanaWalletProvider } from '@solana/wallet-adapter-react';
import { WalletModalProvider } from '@solana/wallet-adapter-react-ui';
import { PhantomWalletAdapter, SolflareWalletAdapter } from '@solana/wallet-adapter-wallets';
import { clusterApiUrl } from '@solana/web3.js';
import '@rainbow-me/rainbowkit/styles.css';
import '@solana/wallet-adapter-react-ui/styles.css';

const queryClient = new QueryClient();

const wagmiConfig = createConfig(
  getDefaultConfig({
    appName: 'SocialFi Arcade',
    projectId: 'YOUR_WALLETCONNECT_PROJECT_ID',
    chains: [mainnet, base, polygon, bsc],
    transports: {
      [mainnet.id]: http(),
      [base.id]: http(),
      [polygon.id]: http(),
      [bsc.id]: http(),
    },
  })
);

const solanaEndpoint = clusterApiUrl('mainnet-beta');
const solanaWallets = [new PhantomWalletAdapter(), new SolflareWalletAdapter()];

export default function WalletProviders({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      <WagmiProvider config={wagmiConfig}>
        <RainbowKitProvider theme={darkTheme({ accentColor: '#22c55e', borderRadius: 'none' })}>
          <ConnectionProvider endpoint={solanaEndpoint}>
            <SolanaWalletProvider wallets={solanaWallets} autoConnect>
              <WalletModalProvider>
                {children}
              </WalletModalProvider>
            </SolanaWalletProvider>
          </ConnectionProvider>
        </RainbowKitProvider>
      </WagmiProvider>
    </QueryClientProvider>
  );
}
