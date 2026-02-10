import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Feed from './pages/Feed';
import Portfolio from './pages/Portfolio';
import AdminDashboard from './pages/AdminDashboard';
import Layout from './components/Layout';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

axios.defaults.baseURL = `${BACKEND_URL}/api`;

axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

function PrivateRoute({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={
            <PrivateRoute>
              <Layout>
                <Feed />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/portfolio" element={
            <PrivateRoute>
              <Layout>
                <Portfolio />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/admin" element={
            <PrivateRoute>
              <Layout>
                <AdminDashboard />
              </Layout>
            </PrivateRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
