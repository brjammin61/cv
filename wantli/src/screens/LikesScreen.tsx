import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Card } from '../types';
import { cardsApi } from '../services/api';

interface LikesScreenProps {
  navigation: any;
}

export default function LikesScreen({ navigation }: LikesScreenProps) {
  const [likedCards, setLikedCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLikedCards();
  }, []);

  const loadLikedCards = async () => {
    try {
      const response = await cardsApi.getLikedCards();
      if (response.success && response.data) {
        setLikedCards(response.data);
      }
    } catch (error) {
      console.error('Error loading liked cards:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderCard = ({ item }: { item: Card }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('CardDetail', { cardId: item.id })}
    >
      <Image source={{ uri: item.images[0] }} style={styles.cardImage} />
      <View style={styles.cardInfo}>
        <Text style={styles.cardPlayer}>{item.player}</Text>
        <Text style={styles.cardDetails}>
          {item.year} {item.manufacturer}
        </Text>
        <Text style={styles.cardPrice}>${item.price.toLocaleString()}</Text>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366F1" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Liked Cards</Text>
      {likedCards.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>No liked cards yet</Text>
          <Text style={styles.emptySubtext}>
            Start swiping to find cards you love!
          </Text>
        </View>
      ) : (
        <FlatList
          data={likedCards}
          renderItem={renderCard}
          keyExtractor={(item) => item.id}
          numColumns={2}
          contentContainerStyle={styles.grid}
        />
      )}
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
  title: {
    fontSize: 32,
    fontWeight: '900',
    color: '#111827',
    padding: 20,
    paddingBottom: 12,
  },
  grid: {
    padding: 12,
  },
  card: {
    flex: 1,
    margin: 8,
    backgroundColor: '#FFF',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardImage: {
    width: '100%',
    height: 200,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
  },
  cardInfo: {
    padding: 12,
  },
  cardPlayer: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  cardDetails: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
  },
  cardPrice: {
    fontSize: 18,
    fontWeight: '900',
    color: '#6366F1',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#6B7280',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 16,
    color: '#9CA3AF',
    textAlign: 'center',
  },
});
