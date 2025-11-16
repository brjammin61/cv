'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiFilter, FiX } from 'react-icons/fi';
import { Filter } from '@/types';

interface FilterPanelProps {
  filters: Filter;
  onFiltersChange: (filters: Filter) => void;
}

export default function FilterPanel({ filters, onFiltersChange }: FilterPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  const sports = ['Basketball', 'Baseball', 'Football', 'Soccer', 'Hockey'];
  const eras = ['2020s', '2010s', '2000s', '1990s', '1980s', 'Vintage'];
  const conditions = ['Mint', 'Near-Mint', 'Excellent', 'Good'];

  return (
    <>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(true)}
        className="glass-effect px-6 py-3 rounded-full shadow-lg flex items-center gap-2 font-semibold text-gray-700 hover:shadow-xl transition-all"
      >
        <FiFilter className="w-5 h-5" />
        Filters
        {Object.keys(filters).length > 0 && (
          <span className="bg-primary-500 text-white text-xs px-2 py-1 rounded-full">
            {Object.keys(filters).length}
          </span>
        )}
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            />

            {/* Filter Panel */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25 }}
              className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white shadow-2xl z-50 overflow-y-auto"
            >
              <div className="p-6 space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold">Filters</h2>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                  >
                    <FiX className="w-6 h-6" />
                  </button>
                </div>

                {/* Sport */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    Sport
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {sports.map((sport) => (
                      <button
                        key={sport}
                        onClick={() =>
                          onFiltersChange({
                            ...filters,
                            sport: filters.sport === sport ? undefined : sport,
                          })
                        }
                        className={`px-4 py-2 rounded-full font-medium transition-all ${
                          filters.sport === sport
                            ? 'bg-primary-500 text-white shadow-lg'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {sport}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Player Search */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    Player Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., Michael Jordan"
                    value={filters.player || ''}
                    onChange={(e) =>
                      onFiltersChange({ ...filters, player: e.target.value || undefined })
                    }
                    className="input-modern"
                  />
                </div>

                {/* Era */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    Era
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {eras.map((era) => (
                      <button
                        key={era}
                        onClick={() =>
                          onFiltersChange({
                            ...filters,
                            era: filters.era === era ? undefined : era,
                          })
                        }
                        className={`px-4 py-2 rounded-full font-medium transition-all ${
                          filters.era === era
                            ? 'bg-accent-500 text-white shadow-lg'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {era}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Graded Only */}
                <div className="flex items-center justify-between">
                  <label className="text-sm font-semibold text-gray-700">
                    Graded Cards Only
                  </label>
                  <button
                    onClick={() =>
                      onFiltersChange({
                        ...filters,
                        graded: !filters.graded,
                      })
                    }
                    className={`w-12 h-6 rounded-full transition-colors ${
                      filters.graded ? 'bg-primary-500' : 'bg-gray-300'
                    }`}
                  >
                    <motion.div
                      animate={{ x: filters.graded ? 24 : 0 }}
                      className="w-6 h-6 bg-white rounded-full shadow-md"
                    />
                  </button>
                </div>

                {/* Price Range */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    Price Range
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="number"
                      placeholder="Min"
                      value={filters.minPrice || ''}
                      onChange={(e) =>
                        onFiltersChange({
                          ...filters,
                          minPrice: e.target.value ? Number(e.target.value) : undefined,
                        })
                      }
                      className="input-modern"
                    />
                    <input
                      type="number"
                      placeholder="Max"
                      value={filters.maxPrice || ''}
                      onChange={(e) =>
                        onFiltersChange({
                          ...filters,
                          maxPrice: e.target.value ? Number(e.target.value) : undefined,
                        })
                      }
                      className="input-modern"
                    />
                  </div>
                </div>

                {/* Condition */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    Condition
                  </label>
                  <div className="space-y-2">
                    {conditions.map((condition) => (
                      <label key={condition} className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={filters.condition?.includes(condition) || false}
                          onChange={(e) => {
                            const current = filters.condition || [];
                            onFiltersChange({
                              ...filters,
                              condition: e.target.checked
                                ? [...current, condition]
                                : current.filter((c) => c !== condition),
                            });
                          }}
                          className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="text-gray-700">{condition}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-6">
                  <button
                    onClick={() => {
                      onFiltersChange({});
                      setIsOpen(false);
                    }}
                    className="flex-1 btn-secondary"
                  >
                    Reset
                  </button>
                  <button onClick={() => setIsOpen(false)} className="flex-1 btn-primary">
                    Apply Filters
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
