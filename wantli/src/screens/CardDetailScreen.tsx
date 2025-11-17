import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Card } from '../types';
import { cardsApi } from '../services/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface CardDetailScreenProps {
  route: any;
  navigation: any;
}

export default function CardDetailScreen({ route, navigation }: CardDetailScreenProps) {
  const { cardId } = route.params;
  const [card, setCard] = useState<Card | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    loadCard();
  }, [cardId]);

  const loadCard = async () => {
    try {
      const response = await cardsApi.getCardById(cardId);
      if (response.success && response.data) {
        setCard(response.data);
      }
    } catch (error) {
      console.error('Error loading card:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !card) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366F1" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Image Carousel */}
        <ScrollView
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          onMomentumScrollEnd={(e) => {
            const index = Math.round(e.nativeEvent.contentOffset.x / SCREEN_WIDTH);
            setCurrentImageIndex(index);
          }}
        >
          {card.images.map((image, index) => (
            <Image
              key={index}
              source={{ uri: image }}
              style={styles.cardImage}
              resizeMode="cover"
            />
          ))}
        </ScrollView>

        {/* Image Indicators */}
        <View style={styles.indicators}>
          {card.images.map((_, index) => (
            <View
              key={index}
              style={[
                styles.indicator,
                currentImageIndex === index && styles.indicatorActive,
              ]}
            />
          ))}
        </View>

        {/* Card Details */}
        <View style={styles.content}>
          <View style={styles.header}>
            <View style={styles.priceContainer}>
              <Text style={styles.price}>${card.price.toLocaleString()}</Text>
            </View>
            <Text style={styles.title}>{card.player}</Text>
            <Text style={styles.subtitle}>
              {card.year} {card.manufacturer} {card.setName}
            </Text>
          </View>

          {/* Grading Info */}
          {card.isGraded && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Grading</Text>
              <View style={styles.gradingCard}>
                <Text style={styles.gradingCompany}>{card.gradingCompany}</Text>
                <Text style={styles.grade}>{card.grade}</Text>
              </View>
            </View>
          )}

          {/* Card Info */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Card Information</Text>
            <View style={styles.infoGrid}>
              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>Sport</Text>
                <Text style={styles.infoValue}>{card.sport}</Text>
              </View>
              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>Condition</Text>
                <Text style={styles.infoValue}>{card.condition}</Text>
              </View>
              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>Card Type</Text>
                <Text style={styles.infoValue}>{card.cardType}</Text>
              </View>
              {card.cardNumber && (
                <View style={styles.infoItem}>
                  <Text style={styles.infoLabel}>Card #</Text>
                  <Text style={styles.infoValue}>{card.cardNumber}</Text>
                </View>
              )}
            </View>
          </View>

          {/* Description */}
          {card.description && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Description</Text>
              <Text style={styles.description}>{card.description}</Text>
            </View>
          )}

          {/* Seller Info */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Seller</Text>
            <View style={styles.sellerCard}>
              <View>
                <Text style={styles.sellerName}>{card.seller.name}</Text>
                <Text style={styles.sellerRating}>
                  ⭐ {card.seller.rating.toFixed(1)} ({card.seller.totalSales} sales)
                </Text>
              </View>
              <TouchableOpacity style={styles.messageButton}>
                <Text style={styles.messageButtonText}>Message</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </ScrollView>

      {/* Bottom Actions */}
      <View style={styles.bottomActions}>
        <TouchableOpacity style={styles.likeButton}>
          <Text style={styles.likeButtonText}>♥</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.buyButton}>
          <LinearGradient
            colors={['#6366F1', '#8B5CF6']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.buyButtonGradient}
          >
            <Text style={styles.buyButtonText}>Buy Now - ${card.price}</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardImage: {
    width: SCREEN_WIDTH,
    height: SCREEN_WIDTH,
  },
  indicators: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 12,
  },
  indicator: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#D1D5DB',
    marginHorizontal: 3,
  },
  indicatorActive: {
    backgroundColor: '#6366F1',
    width: 20,
  },
  content: {
    padding: 20,
  },
  header: {
    marginBottom: 24,
  },
  priceContainer: {
    marginBottom: 12,
  },
  price: {
    fontSize: 36,
    fontWeight: '900',
    color: '#6366F1',
  },
  title: {
    fontSize: 28,
    fontWeight: '900',
    color: '#111827',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  gradingCard: {
    backgroundColor: '#F3F4F6',
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  gradingCompany: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  grade: {
    fontSize: 24,
    fontWeight: '900',
    color: '#6366F1',
  },
  infoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  infoItem: {
    backgroundColor: '#F3F4F6',
    padding: 12,
    borderRadius: 12,
    width: '48%',
  },
  infoLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  infoValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  description: {
    fontSize: 15,
    lineHeight: 24,
    color: '#374151',
  },
  sellerCard: {
    backgroundColor: '#F3F4F6',
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sellerName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  sellerRating: {
    fontSize: 14,
    color: '#6B7280',
  },
  messageButton: {
    backgroundColor: '#6366F1',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  messageButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  bottomActions: {
    flexDirection: 'row',
    padding: 20,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  likeButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#FEE2E2',
    justifyContent: 'center',
    alignItems: 'center',
  },
  likeButtonText: {
    fontSize: 24,
  },
  buyButton: {
    flex: 1,
  },
  buyButtonGradient: {
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buyButtonText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: '700',
  },
});
