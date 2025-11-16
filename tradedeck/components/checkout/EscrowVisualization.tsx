'use client';

import { motion } from 'framer-motion';
import { FiCheck, FiPackage, FiShield, FiTruck } from 'react-icons/fi';

interface EscrowStep {
  id: number;
  icon: typeof FiCheck;
  title: string;
  description: string;
  status: 'completed' | 'active' | 'pending';
}

export default function EscrowVisualization() {
  const steps: EscrowStep[] = [
    {
      id: 1,
      icon: FiShield,
      title: 'Payment Secured',
      description: 'Your payment is held safely in escrow',
      status: 'completed',
    },
    {
      id: 2,
      icon: FiPackage,
      title: 'Seller Ships',
      description: 'Seller packages and ships the card',
      status: 'active',
    },
    {
      id: 3,
      icon: FiTruck,
      title: 'In Transit',
      description: 'Card is on its way to you',
      status: 'pending',
    },
    {
      id: 4,
      icon: FiCheck,
      title: 'Delivered',
      description: 'Funds released to seller after 24 hours',
      status: 'pending',
    },
  ];

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold mb-4">Escrow Protection</h3>

      <div className="relative">
        {/* Progress Line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200">
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: '25%' }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className="w-full bg-gradient-to-b from-primary-500 to-accent-500"
          />
        </div>

        {/* Steps */}
        <div className="space-y-8">
          {steps.map((step, index) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.2 }}
              className="relative flex items-start gap-4"
            >
              {/* Icon */}
              <div
                className={`w-16 h-16 rounded-full flex items-center justify-center flex-shrink-0 z-10 ${
                  step.status === 'completed'
                    ? 'bg-gradient-to-br from-green-400 to-green-600 text-white'
                    : step.status === 'active'
                    ? 'bg-gradient-to-br from-primary-500 to-accent-500 text-white animate-pulse'
                    : 'bg-gray-100 text-gray-400'
                }`}
              >
                <step.icon className="w-7 h-7" />
              </div>

              {/* Content */}
              <div className="flex-1 pt-3">
                <h4
                  className={`font-bold text-lg mb-1 ${
                    step.status === 'pending' ? 'text-gray-400' : 'text-gray-900'
                  }`}
                >
                  {step.title}
                </h4>
                <p
                  className={`text-sm ${
                    step.status === 'pending' ? 'text-gray-400' : 'text-gray-600'
                  }`}
                >
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Info Box */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="bg-blue-50 border border-blue-200 rounded-xl p-4 mt-6"
      >
        <div className="flex items-start gap-3">
          <FiShield className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-semibold text-blue-900 mb-1">You're Protected</h4>
            <p className="text-sm text-blue-700">
              Your payment is held securely until you confirm receipt. If there's an issue,
              you can open a dispute within 24 hours of delivery.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
