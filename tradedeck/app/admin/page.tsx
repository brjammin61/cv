'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  FiUsers,
  FiShoppingBag,
  FiDollarSign,
  FiTrendingUp,
  FiAlertCircle,
  FiActivity,
  FiEye,
  FiShield,
} from 'react-icons/fi';
import Navbar from '@/components/Navbar';

interface DashboardStats {
  totalUsers: number;
  totalListings: number;
  totalRevenue: number;
  pendingDisputes: number;
  activeTransactions: number;
  newUsersToday: number;
  salesThisMonth: number;
  averageTransactionValue: number;
}

export default function AdminDashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
      return;
    }

    if (session && session.user.role !== 'ADMIN') {
      router.push('/');
      return;
    }

    if (session && session.user.role === 'ADMIN') {
      fetchDashboardStats();
    }
  }, [session, status, router]);

  const fetchDashboardStats = async () => {
    try {
      const response = await fetch('/api/admin/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (status === 'loading' || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  if (!session || session.user.role !== 'ADMIN') {
    return null;
  }

  const statCards = [
    {
      title: 'Total Users',
      value: stats?.totalUsers || 0,
      icon: FiUsers,
      color: 'from-blue-500 to-blue-600',
      change: `+${stats?.newUsersToday || 0} today`,
    },
    {
      title: 'Active Listings',
      value: stats?.totalListings || 0,
      icon: FiShoppingBag,
      color: 'from-purple-500 to-purple-600',
      change: 'All categories',
    },
    {
      title: 'Total Revenue',
      value: `$${((stats?.totalRevenue || 0) / 100).toLocaleString()}`,
      icon: FiDollarSign,
      color: 'from-green-500 to-green-600',
      change: `${stats?.salesThisMonth || 0} sales this month`,
    },
    {
      title: 'Active Transactions',
      value: stats?.activeTransactions || 0,
      icon: FiActivity,
      color: 'from-orange-500 to-orange-600',
      change: 'In progress',
    },
    {
      title: 'Pending Disputes',
      value: stats?.pendingDisputes || 0,
      icon: FiAlertCircle,
      color: 'from-red-500 to-red-600',
      change: 'Needs attention',
    },
    {
      title: 'Avg Transaction',
      value: `$${((stats?.averageTransactionValue || 0) / 100).toLocaleString()}`,
      icon: FiTrendingUp,
      color: 'from-teal-500 to-teal-600',
      change: 'Per sale',
    },
  ];

  const adminActions = [
    {
      title: 'User Management',
      description: 'View and manage all users',
      icon: FiUsers,
      href: '/admin/users',
      color: 'bg-blue-500',
    },
    {
      title: 'Listing Moderation',
      description: 'Review and moderate card listings',
      icon: FiEye,
      href: '/admin/listings',
      color: 'bg-purple-500',
    },
    {
      title: 'Transaction Monitor',
      description: 'Track all transactions and escrow',
      icon: FiActivity,
      href: '/admin/transactions',
      color: 'bg-green-500',
    },
    {
      title: 'Dispute Resolution',
      description: 'Handle buyer/seller disputes',
      icon: FiShield,
      href: '/admin/disputes',
      color: 'bg-red-500',
    },
    {
      title: 'Analytics',
      description: 'View detailed analytics and reports',
      icon: FiTrendingUp,
      href: '/admin/analytics',
      color: 'bg-orange-500',
    },
    {
      title: 'Content Reports',
      description: 'Review reported content',
      icon: FiAlertCircle,
      href: '/admin/reports',
      color: 'bg-yellow-500',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">Admin Dashboard</h1>
            <p className="text-gray-600">
              Welcome back, {session.user.name}. Here's what's happening on TradeDeck.
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {statCards.map((stat, index) => (
              <motion.div
                key={stat.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="glass-effect rounded-2xl p-6 hover:shadow-xl transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-600 text-sm font-medium mb-1">
                      {stat.title}
                    </p>
                    <p className="text-3xl font-bold mb-2">{stat.value}</p>
                    <p className="text-sm text-gray-500">{stat.change}</p>
                  </div>
                  <div
                    className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center`}
                  >
                    <stat.icon className="w-6 h-6 text-white" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Admin Actions */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Admin Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {adminActions.map((action, index) => (
                <motion.a
                  key={action.title}
                  href={action.href}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 + index * 0.1 }}
                  className="glass-effect rounded-2xl p-6 hover:shadow-xl transition-all group cursor-pointer"
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`w-12 h-12 rounded-xl ${action.color} flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform`}
                    >
                      <action.icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg mb-1 group-hover:text-primary-600 transition-colors">
                        {action.title}
                      </h3>
                      <p className="text-gray-600 text-sm">{action.description}</p>
                    </div>
                  </div>
                </motion.a>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="glass-effect rounded-2xl p-6">
            <h2 className="text-2xl font-bold mb-4">Recent Activity</h2>
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 bg-blue-50 rounded-lg">
                <FiUsers className="w-5 h-5 text-blue-600" />
                <div className="flex-1">
                  <p className="font-medium">New user registered</p>
                  <p className="text-sm text-gray-600">2 minutes ago</p>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 bg-green-50 rounded-lg">
                <FiDollarSign className="w-5 h-5 text-green-600" />
                <div className="flex-1">
                  <p className="font-medium">Transaction completed - $450.00</p>
                  <p className="text-sm text-gray-600">15 minutes ago</p>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 bg-purple-50 rounded-lg">
                <FiShoppingBag className="w-5 h-5 text-purple-600" />
                <div className="flex-1">
                  <p className="font-medium">New listing created</p>
                  <p className="text-sm text-gray-600">1 hour ago</p>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 bg-red-50 rounded-lg">
                <FiAlertCircle className="w-5 h-5 text-red-600" />
                <div className="flex-1">
                  <p className="font-medium">Dispute opened - Transaction #1234</p>
                  <p className="text-sm text-gray-600">3 hours ago</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
