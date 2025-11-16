'use client';

import { motion } from 'framer-motion';
import { FiSmartphone, FiHeart, FiDollarSign, FiPackage, FiShield, FiCheck } from 'react-icons/fi';
import Navbar from '@/components/Navbar';
import Link from 'next/link';

export default function HowItWorksPage() {
  const steps = [
    {
      icon: FiSmartphone,
      title: 'Set Your Filters',
      description: 'Choose what you're looking for - sport, player, era, price range, and more.',
      details: [
        'Pick your favorite sports',
        'Search specific players',
        'Set your budget',
        'Filter by condition and grading',
      ],
    },
    {
      icon: FiHeart,
      title: 'Swipe to Discover',
      description: 'Cards appear one at a time. Swipe right to like, left to pass, up to make an offer.',
      details: [
        'Swipe right ➡️ Add to favorites',
        'Swipe left ⬅️ Pass on the card',
        'Swipe up ⬆️ Make an instant offer',
        'No boring search results',
      ],
    },
    {
      icon: FiDollarSign,
      title: 'Buy or Make an Offer',
      description: 'Found a card you love? Buy it now or negotiate with the seller.',
      details: [
        'One-click "Buy Now" option',
        'Make offers and counter-offers',
        'Chat with sellers directly',
        'All prices include shipping',
      ],
    },
    {
      icon: FiShield,
      title: 'Protected by Escrow',
      description: 'Your payment is held safely until delivery is confirmed.',
      details: [
        'Payment held in secure escrow',
        'Seller ships the card',
        'Track your package in real-time',
        '24-hour dispute window',
      ],
    },
    {
      icon: FiPackage,
      title: 'Receive Your Card',
      description: 'Card arrives safely. Inspect it and confirm delivery.',
      details: [
        'Cards shipped with tracking',
        'Optional authentication service',
        'Inspect for 24 hours',
        'Funds released to seller',
      ],
    },
    {
      icon: FiCheck,
      title: 'Start Collecting',
      description: 'Build your collection and sell cards you no longer want.',
      details: [
        'List cards in seconds',
        'Pay only 5% transaction fee',
        'Get paid instantly',
        'Rate and review sellers',
      ],
    },
  ];

  return (
    <div className="min-h-screen">
      <Navbar />

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-16"
          >
            <h1 className="text-5xl font-bold mb-4">
              How <span className="bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">TradeDeck</span> Works
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              The easiest and most secure way to buy and sell trading cards
            </p>
          </motion.div>

          {/* Steps */}
          <div className="space-y-24">
            {steps.map((step, index) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className={`flex flex-col ${
                  index % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'
                } items-center gap-12`}
              >
                {/* Icon & Number */}
                <div className="flex-shrink-0 relative">
                  <div className="absolute -top-4 -left-4 text-8xl font-bold text-primary-100">
                    {index + 1}
                  </div>
                  <div className="relative w-32 h-32 bg-gradient-to-br from-primary-500 to-accent-500 rounded-3xl flex items-center justify-center shadow-2xl">
                    <step.icon className="w-16 h-16 text-white" />
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1">
                  <h2 className="text-3xl font-bold mb-4">{step.title}</h2>
                  <p className="text-xl text-gray-600 mb-6">{step.description}</p>
                  <ul className="space-y-3">
                    {step.details.map((detail, i) => (
                      <motion.li
                        key={i}
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.2 + i * 0.1 }}
                        className="flex items-center gap-3"
                      >
                        <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                          <FiCheck className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-gray-700">{detail}</span>
                      </motion.li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            ))}
          </div>

          {/* CTA Section */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-24 text-center"
          >
            <div className="bg-gradient-to-r from-primary-600 via-accent-600 to-primary-600 rounded-3xl p-12 shadow-2xl animate-gradient">
              <h2 className="text-4xl font-bold text-white mb-6">
                Ready to Get Started?
              </h2>
              <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
                Join thousands of collectors already using TradeDeck
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/signup">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="bg-white text-primary-600 px-8 py-4 rounded-full font-bold text-lg shadow-xl hover:shadow-2xl transition-all"
                  >
                    Create Free Account
                  </motion.button>
                </Link>
                <Link href="/discover">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="bg-white/10 backdrop-blur-sm text-white px-8 py-4 rounded-full font-bold text-lg border-2 border-white hover:bg-white/20 transition-all"
                  >
                    Start Swiping
                  </motion.button>
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
