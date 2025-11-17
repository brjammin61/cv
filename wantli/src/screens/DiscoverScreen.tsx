import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  Animated,
  PanResponder,
  Image,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Card } from '../types';
import { cardsApi } from '../services/api';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const SWIPE_THRESHOLD = SCREEN_WIDTH * 0.25;

interface DiscoverScreenProps {
  onCardPress: (cardId: string) => void;
}

export default function DiscoverScreen({ onCardPress }: DiscoverScreenProps) {
  const [cards, setCards] = useState<Card[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  const position = useRef(new Animated.ValueXY()).current;
  const swipeDirection = useRef<'left' | 'right' | null>(null);

  useEffect(() => {
    loadCards();
  }, []);

  const loadCards = async () => {
    try {
      setLoading(true);
      const response = await cardsApi.getCards({ limit: 50 });
      if (response.success && response.data) {
        setCards(response.data);
      }
    } catch (error) {
      console.error('Error loading cards:', error);
    } finally {
      setLoading(false);
    }
  };

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onPanResponderMove: (_, gesture) => {
        position.setValue({ x: gesture.dx, y: gesture.dy });

        // Set swipe direction based on drag
        if (gesture.dx > 50) {
          swipeDirection.current = 'right';
        } else if (gesture.dx < -50) {
          swipeDirection.current = 'left';
        } else {
          swipeDirection.current = null;
        }
      },
      onPanResponderRelease: (_, gesture) => {
        if (gesture.dx > SWIPE_THRESHOLD) {
          // Swipe Right - Like
          forceSwipe('right');
        } else if (gesture.dx < -SWIPE_THRESHOLD) {
          // Swipe Left - Pass
          forceSwipe('left');
        } else {
          // Reset position
          resetPosition();
        }
      },
    })
  ).current;

  const forceSwipe = (direction: 'left' | 'right') => {
    const x = direction === 'right' ? SCREEN_WIDTH + 100 : -SCREEN_WIDTH - 100;
    Animated.timing(position, {
      toValue: { x, y: 0 },
      duration: 250,
      useNativeDriver: false,
    }).start(() => onSwipeComplete(direction));
  };

  const onSwipeComplete = async (direction: 'left' | 'right') => {
    const card = cards[currentIndex];

    if (direction === 'right' && card) {
      // Like the card
      try {
        await cardsApi.likeCard(card.id);
      } catch (error) {
        console.error('Error liking card:', error);
      }
    }

    position.setValue({ x: 0, y: 0 });
    setCurrentIndex(currentIndex + 1);

    // Load more cards if running low
    if (currentIndex >= cards.length - 5) {
      loadCards();
    }
  };

  const resetPosition = () => {
    Animated.spring(position, {
      toValue: { x: 0, y: 0 },
      useNativeDriver: false,
    }).start();
  };

  const getCardStyle = () => {
    const rotate = position.x.interpolate({
      inputRange: [-SCREEN_WIDTH / 2, 0, SCREEN_WIDTH / 2],
      outputRange: ['-10deg', '0deg', '10deg'],
      extrapolate: 'clamp',
    });

    return {
      ...position.getLayout(),
      transform: [{ rotate }],
    };
  };

  const renderCard = (card: Card, index: number) => {
    if (index < currentIndex) {
      return null;
    }

    if (index === currentIndex) {
      return (
        <Animated.View
          key={card.id}
          style={[styles.card, getCardStyle()]}
          {...panResponder.panHandlers}
        >
          <TouchableOpacity
            activeOpacity={0.9}
            onPress={() => onCardPress(card.id)}
            style={styles.cardContent}
          >
            <Image
              source={{ uri: card.images[0] }}
              style={styles.cardImage}
              resizeMode="cover"
            />

            <LinearGradient
              colors={['transparent', 'rgba(0,0,0,0.8)']}
              style={styles.cardGradient}
            >
              <View style={styles.cardInfo}>
                <Text style={styles.cardTitle}>{card.player}</Text>
                <Text style={styles.cardSubtitle}>
                  {card.year} {card.manufacturer}
                </Text>
                <View style={styles.cardDetails}>
                  {card.isGraded && (
                    <View style={styles.badge}>
                      <Text style={styles.badgeText}>
                        {card.gradingCompany} {card.grade}
                      </Text>
                    </View>
                  )}
                  <View style={styles.badge}>
                    <Text style={styles.badgeText}>{card.condition}</Text>
                  </View>
                </View>
                <Text style={styles.cardPrice}>${card.price.toLocaleString()}</Text>
              </View>
            </LinearGradient>

            {/* Swipe Indicators */}
            <Animated.View
              style={[
                styles.swipeIndicator,
                styles.likeIndicator,
                {
                  opacity: position.x.interpolate({
                    inputRange: [0, SWIPE_THRESHOLD],
                    outputRange: [0, 1],
                    extrapolate: 'clamp',
                  }),
                },
              ]}
            >
              <Text style={styles.indicatorText}>LIKE</Text>
            </Animated.View>

            <Animated.View
              style={[
                styles.swipeIndicator,
                styles.nopeIndicator,
                {
                  opacity: position.x.interpolate({
                    inputRange: [-SWIPE_THRESHOLD, 0],
                    outputRange: [1, 0],
                    extrapolate: 'clamp',
                  }),
                },
              ]}
            >
              <Text style={styles.indicatorText}>PASS</Text>
            </Animated.View>
          </TouchableOpacity>
        </Animated.View>
      );
    }

    // Show next card slightly behind
    return (
      <View key={card.id} style={[styles.card, { position: 'absolute', zIndex: -1 }]}>
        <Image
          source={{ uri: card.images[0] }}
          style={styles.cardImage}
          resizeMode="cover"
        />
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366F1" />
        <Text style={styles.loadingText}>Loading cards...</Text>
      </View>
    );
  }

  if (currentIndex >= cards.length) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No more cards!</Text>
        <TouchableOpacity style={styles.reloadButton} onPress={loadCards}>
          <Text style={styles.reloadText}>Load More</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.cardContainer}>
        {cards.map((card, index) => renderCard(card, index)).reverse()}
      </View>

      {/* Action Buttons */}
      <View style={styles.actionsContainer}>
        <TouchableOpacity
          style={[styles.actionButton, styles.passButton]}
          onPress={() => forceSwipe('left')}
        >
          <Text style={styles.actionIcon}>✕</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.infoButton]}
          onPress={() => onCardPress(cards[currentIndex].id)}
        >
          <Text style={styles.actionIcon}>i</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.likeButton]}
          onPress={() => forceSwipe('right')}
        >
          <Text style={styles.actionIcon}>♥</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
  },
  emptyText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#6B7280',
    marginBottom: 16,
  },
  reloadButton: {
    backgroundColor: '#6366F1',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 24,
  },
  reloadText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '700',
  },
  cardContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    position: 'absolute',
    width: SCREEN_WIDTH - 40,
    height: SCREEN_HEIGHT - 200,
    borderRadius: 24,
    backgroundColor: '#FFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
  },
  cardContent: {
    flex: 1,
    borderRadius: 24,
    overflow: 'hidden',
  },
  cardImage: {
    width: '100%',
    height: '100%',
  },
  cardGradient: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '40%',
    justifyContent: 'flex-end',
  },
  cardInfo: {
    padding: 20,
  },
  cardTitle: {
    fontSize: 32,
    fontWeight: '900',
    color: '#FFF',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 18,
    color: '#E5E7EB',
    marginBottom: 12,
  },
  cardDetails: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  badge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  badgeText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '700',
  },
  cardPrice: {
    fontSize: 28,
    fontWeight: '900',
    color: '#FFF',
  },
  swipeIndicator: {
    position: 'absolute',
    top: 50,
    padding: 16,
    borderRadius: 12,
    borderWidth: 4,
  },
  likeIndicator: {
    right: 50,
    borderColor: '#10B981',
    transform: [{ rotate: '20deg' }],
  },
  nopeIndicator: {
    left: 50,
    borderColor: '#EF4444',
    transform: [{ rotate: '-20deg' }],
  },
  indicatorText: {
    fontSize: 32,
    fontWeight: '900',
    color: '#FFF',
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 20,
    paddingVertical: 20,
    paddingHorizontal: 20,
  },
  actionButton: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  passButton: {
    backgroundColor: '#EF4444',
  },
  infoButton: {
    backgroundColor: '#6366F1',
    width: 56,
    height: 56,
    borderRadius: 28,
  },
  likeButton: {
    backgroundColor: '#10B981',
  },
  actionIcon: {
    fontSize: 32,
    color: '#FFF',
    fontWeight: '700',
  },
});
