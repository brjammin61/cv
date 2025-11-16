'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { FiPlus, FiGrid, FiList, FiSearch, FiEdit, FiTrash2, FiDollarSign } from 'react-icons/fi';
import Navbar from '@/components/Navbar';
import { sampleCards } from '@/lib/sampleData';
import { formatPrice } from '@/lib/utils';
import { Card } from '@/types';

export default function CollectionPage() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [myCards] = useState<Card[]>(sampleCards.slice(0, 6));

  const filteredCards = myCards.filter(
    (card) =>
      card.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      card.player.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalValue = myCards.reduce((sum, card) => sum + card.price, 0);

  return (
    <div className="min-h-screen pb-20">
      <Navbar />

      <div className="pt-24 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">
              My <span className="bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">Collection</span>
            </h1>
            <p className="text-gray-600">Manage your inventory and listings</p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-effect p-6 rounded-2xl"
            >
              <div className="text-sm text-gray-600 mb-1">Total Cards</div>
              <div className="text-3xl font-bold text-primary-600">{myCards.length}</div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="glass-effect p-6 rounded-2xl"
            >
              <div className="text-sm text-gray-600 mb-1">Total Value</div>
              <div className="text-3xl font-bold text-green-600">{formatPrice(totalValue)}</div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-effect p-6 rounded-2xl"
            >
              <div className="text-sm text-gray-600 mb-1">Listed</div>
              <div className="text-3xl font-bold text-blue-600">{myCards.length}</div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="glass-effect p-6 rounded-2xl"
            >
              <div className="text-sm text-gray-600 mb-1">Sold This Month</div>
              <div className="text-3xl font-bold text-accent-600">0</div>
            </motion.div>
          </div>

          {/* Toolbar */}
          <div className="flex flex-col md:flex-row gap-4 justify-between items-center mb-6">
            {/* Search */}
            <div className="relative w-full md:w-96">
              <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search your collection..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-3 rounded-xl glass-effect border border-white/20 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/20 outline-none transition-all"
              />
            </div>

            <div className="flex gap-3">
              {/* View Toggle */}
              <div className="glass-effect rounded-xl p-1 flex">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-lg transition-all ${
                    viewMode === 'grid'
                      ? 'bg-primary-500 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <FiGrid className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-lg transition-all ${
                    viewMode === 'list'
                      ? 'bg-primary-500 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <FiList className="w-5 h-5" />
                </button>
              </div>

              {/* Add Card Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="btn-primary flex items-center gap-2"
              >
                <FiPlus className="w-5 h-5" />
                Add Card
              </motion.button>
            </div>
          </div>

          {/* Cards Grid/List */}
          {filteredCards.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-6xl mb-4">📦</div>
              <h3 className="text-2xl font-bold mb-2">No cards found</h3>
              <p className="text-gray-600 mb-6">
                {searchQuery ? 'Try a different search term' : 'Start building your collection'}
              </p>
              <button className="btn-primary">Add Your First Card</button>
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredCards.map((card, index) => (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ y: -8 }}
                  className="card-gradient rounded-2xl shadow-lg overflow-hidden border border-white/50"
                >
                  {/* Card Image */}
                  <div className="h-48 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                    <div className="text-6xl">🏀</div>
                  </div>

                  {/* Card Info */}
                  <div className="p-4">
                    <h3 className="font-bold text-lg mb-1">{card.player}</h3>
                    <p className="text-sm text-gray-600 mb-2">{card.title}</p>
                    <p className="text-xs text-gray-500 mb-3">
                      {card.year} • {card.set}
                    </p>
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-2xl font-bold text-primary-600">
                        {formatPrice(card.price)}
                      </div>
                      {card.graded && (
                        <div className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs font-semibold">
                          {card.gradingCompany} {card.grade}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary-100 text-primary-600 rounded-lg hover:bg-primary-200 transition-colors font-medium">
                        <FiEdit className="w-4 h-4" />
                        Edit
                      </button>
                      <button className="px-4 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors">
                        <FiTrash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {filteredCards.map((card, index) => (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass-effect rounded-2xl p-6 flex items-center gap-6 hover:shadow-lg transition-shadow"
                >
                  {/* Thumbnail */}
                  <div className="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl flex items-center justify-center flex-shrink-0">
                    <div className="text-4xl">🏀</div>
                  </div>

                  {/* Info */}
                  <div className="flex-1">
                    <h3 className="font-bold text-lg mb-1">{card.player}</h3>
                    <p className="text-sm text-gray-600 mb-2">{card.title}</p>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>{card.year}</span>
                      <span>•</span>
                      <span>{card.set}</span>
                      {card.graded && (
                        <>
                          <span>•</span>
                          <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs font-semibold">
                            {card.gradingCompany} {card.grade}
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Price */}
                  <div className="text-2xl font-bold text-primary-600">
                    {formatPrice(card.price)}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button className="px-4 py-2 bg-primary-100 text-primary-600 rounded-lg hover:bg-primary-200 transition-colors font-medium flex items-center gap-2">
                      <FiEdit className="w-4 h-4" />
                      Edit
                    </button>
                    <button className="px-4 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors">
                      <FiTrash2 className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
