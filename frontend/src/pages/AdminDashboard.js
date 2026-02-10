import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Users, FileText, TrendingUp, DollarSign, AlertCircle, Activity } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get('/admin/dashboard');
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-gray-500">Loading dashboard...</div>;
  }

  const metrics = [
    { label: 'Total Users', value: stats?.total_users || 0, icon: Users, color: 'blue' },
    { label: 'Total Posts', value: stats?.total_posts || 0, icon: FileText, color: 'green' },
    { label: 'Total Trades', value: stats?.total_trades || 0, icon: Activity, color: 'purple' },
    { label: 'Total Volume', value: `${(stats?.total_volume || 0).toFixed(0)} credits`, icon: TrendingUp, color: 'orange' },
    { label: 'Platform Fees', value: `${(stats?.total_fees || 0).toFixed(0)} credits`, icon: DollarSign, color: 'emerald' },
    { label: 'Pending Reports', value: stats?.pending_reports || 0, icon: AlertCircle, color: 'red' },
  ];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
        <p className="text-gray-600">Platform metrics and health monitoring</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric, idx) => {
          const IconComponent = metric.icon;
          return (
            <Card key={idx} data-testid={`metric-${metric.label.toLowerCase().replace(' ', '-')}`}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {metric.label}
                </CardTitle>
                <div className={`p-2 bg-${metric.color}-100 rounded-full`}>
                  <IconComponent className={`h-4 w-4 text-${metric.color}-600`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metric.value}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
