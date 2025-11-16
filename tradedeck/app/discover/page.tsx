'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiHeart, FiX, FiDollarSign, FiRotateCw } from 'react-icons/fi';
import Navbar from '@/components/Navbar';
import SwipeCard from '@/components/discover/SwipeCard';
import FilterPanel from '@/components/discover/FilterPanel';
import { useStore } from '@/store/useStore';
import { sampleCards } from '@/lib/sampleData';
import { Card, Filter } from '@/types';

export default function DiscoverPage() {
  const { filters, setFilters, likedCards, toggleLike } = useStore();
  const [cards, setCards] = useState<Card[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    // Filter cards based on active filters
    let filtered = [...sampleCards];

    if (filters.sport) {
      filtered = filtered.filter((card) =>
        card.sport.toLowerCase() === filters.sport?.toLowerCase()
      );
    }

    if (filters.player) {
      filtered = filtered.filter((card) =>
        card.player.toLowerCase().includes(filters.player!.toLowerCase())
      );
    }

    if (filters.era) {
      filtered = filtered.filter((card) => card.era === filters.era);
    }

    if (filters.graded !== undefined) {
      filtered = filtered.filter((card) => card.graded === filters.graded);
    }

    if (filters.minPrice !== undefined) {
      filtered = filtered.filter((card) => card.price >= filters.minPrice!);
    }

    if (filters.maxPrice !== undefined) {
      filtered = filtered.filter((card) => card.price <= filters.maxPrice!);
    }

    if (filters.condition && filters.condition.length > 0) {
      filtered = filtered.filter((card) =>
        filters.condition?.includes(card.condition)
      );
    }

    setCards(filtered);
    setCurrentIndex(0);
  }, [filters]);

  const handleSwipe = (direction: 'left' | 'right' | 'up') => {
    const currentCard = cards[currentIndex];

    if (direction === 'right') {
      toggleLike(currentCard.id);
      console.log('Liked card:', currentCard.title);
    } else if (direction === 'left') {
      console.log('Passed on card:', currentCard.title);
    } else if (direction === 'up') {
      console.log('Making offer on card:', currentCard.title);
      // Here you would navigate to make offer page
    }

    setCurrentIndex((prev) => prev + 1);
  };

  const handleButtonSwipe = (direction: 'left' | 'right' | 'up') => {
    handleSwipe(direction);
  };

  const resetDeck = () => {
    setCurrentIndex(0);
  };

  const currentCard = cards[currentIndex];
  const remainingCards = cards.length - currentIndex;

  return (
    <div className="min-h-screen pb-20">
      <Navbar />

      <div className="pt-24 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
            <div>
              <h1 className="text-4xl font-bold mb-2">
                Discover <span className="bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">Cards</span>
              </h1>
              <p className="text-gray-600">
                {remainingCards} cards remaining • {likedCards.length} liked
              </p>
            </div>

            <FilterPanel filters={filters} onFiltersChange={setFilters} />
          </div>

          {/* Swipe Area */}
          <div className="flex flex-col items-center justify-center">
            {/* Cards Stack */}
            <div className="relative w-full max-w-sm h-[600px] mb-8">
              {cards.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="absolute inset-0 flex items-center justify-center"
                >
                  <div className="text-center p-8 glass-effect rounded-3xl">
                    <div className="text-6xl mb-4">😔</div>
                    <h3 className="text-2xl font-bold mb-2">No Cards Found</h3>
                    <p className="text-gray-600 mb-4">
                      Try adjusting your filters
                    </p>
                    <button
                      onClick={() => setFilters({})}
                      className="btn-primary"
                    >
                      Reset Filters
                    </button>
                  </div>
                </motion.div>
              ) : currentIndex >= cards.length ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="absolute inset-0 flex items-center justify-center"
                >
                  <div className="text-center p-8 glass-effect rounded-3xl">
                    <div className="text-6xl mb-4">🎉</div>
                    <h3 className="text-2xl font-bold mb-2">All Done!</h3>
                    <p className="text-gray-600 mb-4">
                      You've seen all the cards. Check your liked cards or start over.
                    </p>
                    <button onClick={resetDeck} className="btn-primary">
                      Start Over
                    </button>
                  </div>
                </motion.div>
              ) : (
                <AnimatePresence>
                  {cards.slice(currentIndex, currentIndex + 3).map((card, index) => (
                    <div
                      key={card.id}
                      style={{
                        position: 'absolute',
                        width: '100%',
                        zIndex: 10 - index,
                        scale: 1 - index * 0.05,
                        y: index * 10,
                      }}
                    >
                      <SwipeCard
                        card={card}
                        onSwipe={handleSwipe}
                        isTop={index === 0}
                      />
                    </div>
                  ))}
                </AnimatePresence>
              )}
            </div>

            {/* Action Buttons */}
            {currentCard && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-6"
              >
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => handleButtonSwipe('left')}
                  className="w-16 h-16 bg-red-500 rounded-full shadow-lg flex items-center justify-center text-white hover:shadow-2xl transition-shadow"
                >
                  <FiX className="w-8 h-8" />
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => handleButtonSwipe('up')}
                  className="w-16 h-16 bg-blue-500 rounded-full shadow-lg flex items-center justify-center text-white hover:shadow-2xl transition-shadow"
                >
                  <FiDollarSign className="w-8 h-8" />
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => handleButtonSwipe('right')}
                  className="w-16 h-16 bg-green-500 rounded-full shadow-lg flex items-center justify-center text-white hover:shadow-2xl transition-shadow"
                >
                  <FiHeart className="w-8 h-8" />
                </motion.button>
              </motion.div>
            )}

            {/* Instructions */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-8 text-center space-y-2"
            >
              <p className="text-gray-600">
                <span className="inline-block w-6 h-6 bg-red-500 rounded-full align-middle mr-2"></span>
                Swipe left or tap <FiX className="inline" /> to pass
              </p>
              <p className="text-gray-600">
                <span className="inline-block w-6 h-6 bg-green-500 rounded-full align-middle mr-2"></span>
                Swipe right or tap <FiHeart className="inline" /> to like
              </p>
              <p className="text-gray-600">
                <span className="inline-block w-6 h-6 bg-blue-500 rounded-full align-middle mr-2"></span>
                Swipe up or tap <FiDollarSign className="inline" /> to make an offer
              </p>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
