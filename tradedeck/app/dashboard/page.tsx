'use client';

import { motion } from 'framer-motion';
import { FiTrendingUp, FiDollarSign, FiPackage, FiStar, FiEye, FiHeart, FiShoppingBag } from 'react-icons/fi';
import Navbar from '@/components/Navbar';
import { formatPrice } from '@/lib/utils';
import { sampleCards } from '@/lib/sampleData';

export default function DashboardPage() {
  const recentSales = [
    {
      id: '1',
      card: '2003-04 Topps Chrome LeBron James',
      buyer: 'CardCollector23',
      price: 45000,
      date: '2024-01-15',
      status: 'completed',
    },
    {
      id: '2',
      card: '2017-18 Panini National Treasures Giannis',
      buyer: 'HoopsLover',
      price: 12000,
      date: '2024-01-14',
      status: 'shipped',
    },
    {
      id: '3',
      card: '2018 Panini Prizm Luka Doncic',
      buyer: 'RookieHunter',
      price: 8500,
      date: '2024-01-12',
      status: 'completed',
    },
  ];

  const stats = {
    totalSales: 65500,
    activeListings: 12,
    totalViews: 2847,
    averageRating: 4.9,
    monthlySales: 3,
    earnings: 62225, // After 5% fee
  };

  return (
    <div className="min-h-screen pb-20">
      <Navbar />

      <div className="pt-24 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">
              Seller <span className="bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">Dashboard</span>
            </h1>
            <p className="text-gray-600">Track your sales, listings, and performance</p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ y: -4 }}
              className="glass-effect p-6 rounded-2xl card-hover"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center">
                  <FiDollarSign className="w-6 h-6 text-white" />
                </div>
                <div className="text-green-600 text-sm font-semibold flex items-center gap-1">
                  <FiTrendingUp className="w-4 h-4" />
                  +12%
                </div>
              </div>
              <div className="text-3xl font-bold text-gray-900 mb-1">
                {formatPrice(stats.earnings)}
              </div>
              <div className="text-sm text-gray-600">Total Earnings</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              whileHover={{ y: -4 }}
              className="glass-effect p-6 rounded-2xl card-hover"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center">
                  <FiPackage className="w-6 h-6 text-white" />
                </div>
                <div className="text-blue-600 text-sm font-semibold">
                  {stats.monthlySales} this month
                </div>
              </div>
              <div className="text-3xl font-bold text-gray-900 mb-1">
                {stats.activeListings}
              </div>
              <div className="text-sm text-gray-600">Active Listings</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              whileHover={{ y: -4 }}
              className="glass-effect p-6 rounded-2xl card-hover"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl flex items-center justify-center">
                  <FiEye className="w-6 h-6 text-white" />
                </div>
                <div className="text-purple-600 text-sm font-semibold flex items-center gap-1">
                  <FiTrendingUp className="w-4 h-4" />
                  +24%
                </div>
              </div>
              <div className="text-3xl font-bold text-gray-900 mb-1">
                {stats.totalViews.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Total Views</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              whileHover={{ y: -4 }}
              className="glass-effect p-6 rounded-2xl card-hover"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-xl flex items-center justify-center">
                  <FiStar className="w-6 h-6 text-white" />
                </div>
                <div className="text-yellow-600 text-sm font-semibold">
                  128 reviews
                </div>
              </div>
              <div className="text-3xl font-bold text-gray-900 mb-1">
                {stats.averageRating} ★
              </div>
              <div className="text-sm text-gray-600">Average Rating</div>
            </motion.div>
          </div>

          {/* Charts & Tables */}
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Recent Sales */}
            <div className="lg:col-span-2">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="glass-effect rounded-2xl p-6"
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold">Recent Sales</h2>
                  <button className="text-primary-600 hover:text-primary-700 font-medium text-sm">
                    View All
                  </button>
                </div>

                <div className="space-y-4">
                  {recentSales.map((sale, index) => (
                    <motion.div
                      key={sale.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + index * 0.1 }}
                      className="flex items-center gap-4 p-4 rounded-xl hover:bg-primary-50/50 transition-colors"
                    >
                      <div className="w-16 h-16 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg flex items-center justify-center flex-shrink-0">
                        <div className="text-2xl">🏀</div>
                      </div>

                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 truncate">
                          {sale.card}
                        </h3>
                        <p className="text-sm text-gray-600">
                          Sold to {sale.buyer}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(sale.date).toLocaleDateString('en-US', {
                            month: 'long',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </p>
                      </div>

                      <div className="text-right">
                        <div className="text-xl font-bold text-primary-600">
                          {formatPrice(sale.price)}
                        </div>
                        <div
                          className={`text-xs px-2 py-1 rounded-full inline-block ${
                            sale.status === 'completed'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-blue-100 text-blue-700'
                          }`}
                        >
                          {sale.status}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              {/* Top Performing Cards */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
                className="glass-effect rounded-2xl p-6 mt-6"
              >
                <h2 className="text-2xl font-bold mb-6">Top Performing Listings</h2>

                <div className="space-y-4">
                  {sampleCards.slice(0, 3).map((card, index) => (
                    <div
                      key={card.id}
                      className="flex items-center gap-4 p-4 rounded-xl hover:bg-primary-50/50 transition-colors"
                    >
                      <div className="text-2xl font-bold text-gray-400 w-8">
                        #{index + 1}
                      </div>

                      <div className="w-16 h-16 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg flex items-center justify-center flex-shrink-0">
                        <div className="text-2xl">🏀</div>
                      </div>

                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{card.player}</h3>
                        <p className="text-sm text-gray-600">{card.title}</p>
                      </div>

                      <div className="text-right">
                        <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                          <FiEye className="w-4 h-4" />
                          <span>234 views</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <FiHeart className="w-4 h-4" />
                          <span>18 likes</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>

            {/* Right Sidebar */}
            <div className="space-y-6">
              {/* Quick Actions */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="glass-effect rounded-2xl p-6"
              >
                <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
                <div className="space-y-3">
                  <button className="w-full btn-primary flex items-center justify-center gap-2">
                    <FiPackage className="w-5 h-5" />
                    Add New Listing
                  </button>
                  <button className="w-full btn-secondary flex items-center justify-center gap-2">
                    <FiShoppingBag className="w-5 h-5" />
                    Manage Orders
                  </button>
                </div>
              </motion.div>

              {/* Sales This Month */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="glass-effect rounded-2xl p-6"
              >
                <h2 className="text-xl font-bold mb-4">This Month</h2>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-600">Sales Goal</span>
                      <span className="font-semibold">60%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: '60%' }}
                        transition={{ duration: 1, delay: 0.8 }}
                        className="bg-gradient-to-r from-primary-500 to-accent-500 h-2 rounded-full"
                      />
                    </div>
                  </div>

                  <div className="pt-4 border-t space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Revenue</span>
                      <span className="font-bold">{formatPrice(stats.earnings)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Platform Fee (5%)</span>
                      <span className="font-bold text-gray-500">
                        -{formatPrice(stats.totalSales * 0.05)}
                      </span>
                    </div>
                    <div className="flex justify-between pt-3 border-t">
                      <span className="font-bold">Net Earnings</span>
                      <span className="font-bold text-green-600">
                        {formatPrice(stats.earnings)}
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Performance Tips */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
                className="bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl p-6 text-white"
              >
                <h2 className="text-xl font-bold mb-4">💡 Pro Tip</h2>
                <p className="text-white/90 text-sm leading-relaxed">
                  Cards with professional photos get 3x more views. Use our AI scanner to
                  automatically identify and list your cards faster!
                </p>
                <button className="mt-4 w-full bg-white text-primary-600 px-4 py-2 rounded-lg font-semibold hover:bg-white/90 transition-colors">
                  Try AI Scanner
                </button>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
