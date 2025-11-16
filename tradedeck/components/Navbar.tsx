'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { FiMenu, FiX, FiHeart, FiUser, FiShoppingBag } from 'react-icons/fi';
import { useState } from 'react';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 glass-effect shadow-lg"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <motion.div
              whileHover={{ scale: 1.1, rotate: 5 }}
              className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent"
            >
              TradeDeck
            </motion.div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              href="/discover"
              className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
            >
              Discover
            </Link>
            <Link
              href="/marketplace"
              className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
            >
              Marketplace
            </Link>
            <Link
              href="/how-it-works"
              className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
            >
              How It Works
            </Link>

            <div className="flex items-center space-x-4">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                className="p-2 rounded-full hover:bg-primary-50 transition-colors"
              >
                <FiHeart className="w-5 h-5 text-gray-700" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                className="p-2 rounded-full hover:bg-primary-50 transition-colors"
              >
                <FiShoppingBag className="w-5 h-5 text-gray-700" />
              </motion.button>
              <Link href="/login">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="btn-secondary"
                >
                  Sign In
                </motion.button>
              </Link>
              <Link href="/signup">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="btn-primary"
                >
                  Get Started
                </motion.button>
              </Link>
            </div>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-primary-50 transition-colors"
          >
            {isOpen ? (
              <FiX className="w-6 h-6 text-gray-700" />
            ) : (
              <FiMenu className="w-6 h-6 text-gray-700" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="md:hidden glass-effect border-t border-gray-200"
        >
          <div className="px-4 py-6 space-y-4">
            <Link
              href="/discover"
              className="block text-gray-700 hover:text-primary-600 font-medium transition-colors"
            >
              Discover
            </Link>
            <Link
              href="/marketplace"
              className="block text-gray-700 hover:text-primary-600 font-medium transition-colors"
            >
              Marketplace
            </Link>
            <Link
              href="/how-it-works"
              className="block text-gray-700 hover:text-primary-600 font-medium transition-colors"
            >
              How It Works
            </Link>
            <div className="pt-4 space-y-3">
              <Link href="/login">
                <button className="w-full btn-secondary">Sign In</button>
              </Link>
              <Link href="/signup">
                <button className="w-full btn-primary">Get Started</button>
              </Link>
            </div>
          </div>
        </motion.div>
      )}
    </motion.nav>
  );
}
