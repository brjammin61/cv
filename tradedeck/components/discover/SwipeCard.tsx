'use client';

import { motion, useMotionValue, useTransform, PanInfo } from 'framer-motion';
import { Card } from '@/types';
import { formatPrice } from '@/lib/utils';
import { FiHeart, FiX, FiDollarSign, FiAward } from 'react-icons/fi';
import Image from 'next/image';

interface SwipeCardProps {
  card: Card;
  onSwipe: (direction: 'left' | 'right' | 'up') => void;
  isTop: boolean;
}

export default function SwipeCard({ card, onSwipe, isTop }: SwipeCardProps) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const rotateZ = useTransform(x, [-200, 200], [-20, 20]);
  const opacity = useTransform(x, [-200, -100, 0, 100, 200], [0, 1, 1, 1, 0]);

  const handleDragEnd = (event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const threshold = 100;
    const velocity = info.velocity.x;

    if (Math.abs(info.offset.x) > threshold || Math.abs(velocity) > 500) {
      if (info.offset.x > 0) {
        onSwipe('right');
      } else {
        onSwipe('left');
      }
    } else if (info.offset.y < -threshold || info.velocity.y < -500) {
      onSwipe('up');
    }
  };

  return (
    <motion.div
      style={{
        x,
        y,
        rotateZ,
        opacity,
        position: 'absolute',
        cursor: isTop ? 'grab' : 'default',
      }}
      drag={isTop}
      dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={1}
      onDragEnd={handleDragEnd}
      whileDrag={{ cursor: 'grabbing', scale: 1.05 }}
      className="w-full max-w-sm"
    >
      <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
        {/* Card Image */}
        <div className="relative h-96 bg-gradient-to-br from-gray-100 to-gray-200">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center p-8">
              <div className="w-48 h-64 bg-gradient-to-br from-primary-100 to-accent-100 rounded-lg shadow-lg mx-auto flex items-center justify-center">
                <div className="text-6xl">🏀</div>
              </div>
            </div>
          </div>

          {/* Grade Badge */}
          {card.graded && (
            <div className="absolute top-4 right-4 bg-gradient-to-r from-yellow-400 to-yellow-500 px-4 py-2 rounded-full shadow-lg flex items-center gap-2">
              <FiAward className="text-white" />
              <span className="font-bold text-white">
                {card.gradingCompany} {card.grade}
              </span>
            </div>
          )}

          {/* Featured Badge */}
          {card.featured && (
            <div className="absolute top-4 left-4 bg-gradient-to-r from-accent-500 to-accent-600 px-4 py-2 rounded-full shadow-lg">
              <span className="font-bold text-white text-sm">⭐ Featured</span>
            </div>
          )}
        </div>

        {/* Card Details */}
        <div className="p-6 space-y-4">
          <div>
            <h3 className="text-2xl font-bold text-gray-900">{card.player}</h3>
            <p className="text-gray-600">{card.title}</p>
            <p className="text-sm text-gray-500 mt-1">
              {card.year} • {card.set} • #{card.cardNumber}
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-primary-600">
                {formatPrice(card.price)}
              </div>
              <div className="text-sm text-gray-500">
                Condition: {card.condition}
              </div>
            </div>

            <div className="text-right">
              <div className="flex items-center gap-1">
                <span className="text-yellow-500">★</span>
                <span className="font-semibold">{card.sellerRating.toFixed(1)}</span>
              </div>
              <div className="text-sm text-gray-500">{card.sellerName}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Swipe Indicators */}
      {isTop && (
        <>
          <motion.div
            style={{ opacity: useTransform(x, [0, 100], [0, 1]) }}
            className="absolute top-1/3 right-8 bg-green-500 text-white px-6 py-3 rounded-full font-bold text-xl shadow-lg rotate-12"
          >
            <FiHeart className="w-8 h-8" />
          </motion.div>
          <motion.div
            style={{ opacity: useTransform(x, [-100, 0], [1, 0]) }}
            className="absolute top-1/3 left-8 bg-red-500 text-white px-6 py-3 rounded-full font-bold text-xl shadow-lg -rotate-12"
          >
            <FiX className="w-8 h-8" />
          </motion.div>
          <motion.div
            style={{ opacity: useTransform(y, [-100, 0], [1, 0]) }}
            className="absolute top-8 left-1/2 -translate-x-1/2 bg-blue-500 text-white px-6 py-3 rounded-full font-bold text-xl shadow-lg"
          >
            <FiDollarSign className="w-8 h-8" />
          </motion.div>
        </>
      )}
    </motion.div>
  );
}
