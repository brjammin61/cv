'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { FiCreditCard, FiLock, FiShield, FiCheck } from 'react-icons/fi';
import Navbar from '@/components/Navbar';
import EscrowVisualization from '@/components/checkout/EscrowVisualization';
import { formatPrice } from '@/lib/utils';

export default function CheckoutPage() {
  const [authenticationOption, setAuthenticationOption] = useState<'direct' | 'authenticate'>('direct');

  const cardPrice = 12000;
  const authFee = 150;
  const shippingFee = 15;
  const platformFee = cardPrice * 0.05;
  const total = authenticationOption === 'authenticate'
    ? cardPrice + authFee + shippingFee
    : cardPrice + shippingFee;

  return (
    <div className="min-h-screen pb-20">
      <Navbar />

      <div className="pt-24 px-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-4xl font-bold mb-8">
            Secure <span className="bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">Checkout</span>
          </h1>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Left Column - Form */}
            <div className="lg:col-span-2 space-y-6">
              {/* Card Details */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-effect rounded-2xl p-6"
              >
                <h2 className="text-xl font-bold mb-4">Card Details</h2>
                <div className="flex gap-4">
                  <div className="w-32 h-32 bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl flex items-center justify-center flex-shrink-0">
                    <div className="text-5xl">🏀</div>
                  </div>
                  <div>
                    <h3 className="font-bold text-lg mb-1">Giannis Antetokounmpo</h3>
                    <p className="text-gray-600 mb-2">2017-18 Panini National Treasures</p>
                    <p className="text-sm text-gray-500 mb-3">PSA 10 • #125/99</p>
                    <div className="text-2xl font-bold text-primary-600">
                      {formatPrice(cardPrice)}
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Authentication Option */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="glass-effect rounded-2xl p-6"
              >
                <h2 className="text-xl font-bold mb-4">Authentication Option</h2>
                <p className="text-gray-600 mb-4">
                  Choose how you'd like to receive your card
                </p>

                <div className="space-y-4">
                  {/* Direct Shipping */}
                  <label
                    className={`block p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      authenticationOption === 'direct'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <input
                        type="radio"
                        name="auth"
                        value="direct"
                        checked={authenticationOption === 'direct'}
                        onChange={(e) => setAuthenticationOption(e.target.value as any)}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="font-semibold mb-1">Direct Shipping (Free)</div>
                        <p className="text-sm text-gray-600">
                          Card ships directly to you. Protected by escrow.
                        </p>
                      </div>
                    </div>
                  </label>

                  {/* Authentication */}
                  <label
                    className={`block p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      authenticationOption === 'authenticate'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <input
                        type="radio"
                        name="auth"
                        value="authenticate"
                        checked={authenticationOption === 'authenticate'}
                        onChange={(e) => setAuthenticationOption(e.target.value as any)}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold">Authenticate First</span>
                          <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs font-semibold">
                            +{formatPrice(authFee)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          Card ships to PSA for verification, then to you. Maximum protection.
                        </p>
                      </div>
                    </div>
                  </label>
                </div>
              </motion.div>

              {/* Payment Method */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="glass-effect rounded-2xl p-6"
              >
                <h2 className="text-xl font-bold mb-4">Payment Method</h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Card Number
                    </label>
                    <div className="relative">
                      <FiCreditCard className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        placeholder="1234 5678 9012 3456"
                        className="input-modern pl-12"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Expiry Date
                      </label>
                      <input
                        type="text"
                        placeholder="MM/YY"
                        className="input-modern"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        CVV
                      </label>
                      <div className="relative">
                        <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                          type="text"
                          placeholder="123"
                          className="input-modern pl-12"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Name on Card
                    </label>
                    <input
                      type="text"
                      placeholder="John Doe"
                      className="input-modern"
                    />
                  </div>
                </div>
              </motion.div>

              {/* Complete Purchase */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full btn-primary py-4 text-lg flex items-center justify-center gap-2"
              >
                <FiShield className="w-5 h-5" />
                Complete Secure Purchase
              </motion.button>

              <p className="text-center text-sm text-gray-500">
                <FiLock className="inline mr-1" />
                Your payment information is encrypted and secure
              </p>
            </div>

            {/* Right Column - Summary & Escrow */}
            <div className="space-y-6">
              {/* Order Summary */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="glass-effect rounded-2xl p-6 sticky top-24"
              >
                <h2 className="text-xl font-bold mb-4">Order Summary</h2>

                <div className="space-y-3 mb-4">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Card Price</span>
                    <span className="font-semibold">{formatPrice(cardPrice)}</span>
                  </div>
                  {authenticationOption === 'authenticate' && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Authentication</span>
                      <span className="font-semibold">{formatPrice(authFee)}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600">Shipping</span>
                    <span className="font-semibold">{formatPrice(shippingFee)}</span>
                  </div>
                  <div className="border-t pt-3 flex justify-between text-lg font-bold">
                    <span>Total</span>
                    <span className="text-primary-600">{formatPrice(total)}</span>
                  </div>
                </div>

                {/* Features */}
                <div className="space-y-3 pt-4 border-t">
                  <div className="flex items-center gap-3 text-sm">
                    <FiCheck className="text-green-500 flex-shrink-0" />
                    <span className="text-gray-600">Escrow protection included</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <FiCheck className="text-green-500 flex-shrink-0" />
                    <span className="text-gray-600">24-hour dispute window</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <FiCheck className="text-green-500 flex-shrink-0" />
                    <span className="text-gray-600">Package tracking included</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <FiCheck className="text-green-500 flex-shrink-0" />
                    <span className="text-gray-600">Seller verified & rated</span>
                  </div>
                </div>
              </motion.div>

              {/* Escrow Flow */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="glass-effect rounded-2xl p-6"
              >
                <EscrowVisualization />
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
