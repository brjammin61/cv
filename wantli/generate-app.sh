#!/bin/bash

# This script generates all remaining Wantli app files
# Run with: bash generate-app.sh

echo "Generating Wantli React Native App Files..."

# Create CardDetailScreen
cat > src/screens/CardDetailScreen.tsx << 'EOF'
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
EOF

echo "✓ CardDetailScreen created"

# Create UploadCardScreen with camera
cat > src/screens/UploadCardScreen.tsx << 'EOF'
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Image,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Camera } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';
import { cardsApi, uploadImage } from '../services/api';

const SPORTS = ['BASKETBALL', 'BASEBALL', 'FOOTBALL', 'SOCCER', 'HOCKEY', 'OTHER'];
const CONDITIONS = ['MINT', 'NEAR_MINT', 'EXCELLENT', 'GOOD', 'FAIR', 'POOR'];
const GRADING_COMPANIES = ['PSA', 'BGS', 'SGC', 'CGC', 'OTHER'];

export default function UploadCardScreen({ navigation }: any) {
  const [images, setImages] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);

  // Form state
  const [player, setPlayer] = useState('');
  const [year, setYear] = useState('');
  const [sport, setSport] = useState('BASKETBALL');
  const [manufacturer, setManufacturer] = useState('');
  const [setName, setSetName] = useState('');
  const [cardType, setCardType] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [price, setPrice] = useState('');
  const [condition, setCondition] = useState('NEAR_MINT');
  const [isGraded, setIsGraded] = useState(false);
  const [gradingCompany, setGradingCompany] = useState('PSA');
  const [grade, setGrade] = useState('');
  const [description, setDescription] = useState('');

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();

    if (status !== 'granted') {
      Alert.alert('Permission denied', 'We need camera roll permission');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setImages([...images, result.assets[0].uri]);
    }
  };

  const takePhoto = async () => {
    const { status } = await Camera.requestCameraPermissionsAsync();

    if (status !== 'granted') {
      Alert.alert('Permission denied', 'We need camera permission');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setImages([...images, result.assets[0].uri]);
    }
  };

  const handleSubmit = async () => {
    if (!player || !year || !manufacturer || !price || images.length === 0) {
      Alert.alert('Missing fields', 'Please fill in all required fields and add at least one image');
      return;
    }

    setUploading(true);

    try {
      // Upload images to Cloudinary
      const uploadedImages = await Promise.all(
        images.map((uri) => uploadImage(uri))
      );

      // Create card listing
      const cardData = {
        player,
        year: parseInt(year),
        sport,
        manufacturer,
        setName,
        cardType,
        cardNumber,
        price: parseFloat(price),
        condition,
        isGraded,
        gradingCompany: isGraded ? gradingCompany : undefined,
        grade: isGraded ? grade : undefined,
        description,
        images: uploadedImages,
      };

      const response = await cardsApi.createCard(cardData);

      if (response.success) {
        Alert.alert('Success!', 'Your card has been listed', [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]);
      }
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.error || 'Failed to create listing');
    } finally {
      setUploading(false);
    }
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Text style={styles.title}>List Your Card</Text>

      {/* Images */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Photos *</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.imagesContainer}>
            {images.map((uri, index) => (
              <View key={index} style={styles.imagePreview}>
                <Image source={{ uri }} style={styles.image} />
                <TouchableOpacity
                  style={styles.removeButton}
                  onPress={() => setImages(images.filter((_, i) => i !== index))}
                >
                  <Text style={styles.removeText}>✕</Text>
                </TouchableOpacity>
              </View>
            ))}
            <TouchableOpacity style={styles.addImageButton} onPress={pickImage}>
              <Text style={styles.addImageText}>📷</Text>
              <Text style={styles.addImageLabel}>Add Photo</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.addImageButton} onPress={takePhoto}>
              <Text style={styles.addImageText}>📸</Text>
              <Text style={styles.addImageLabel}>Take Photo</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>

      {/* Player Name */}
      <View style={styles.section}>
        <Text style={styles.label}>Player Name *</Text>
        <TextInput
          style={styles.input}
          value={player}
          onChangeText={setPlayer}
          placeholder="e.g. LeBron James"
        />
      </View>

      {/* Year */}
      <View style={styles.section}>
        <Text style={styles.label}>Year *</Text>
        <TextInput
          style={styles.input}
          value={year}
          onChangeText={setYear}
          placeholder="e.g. 2003"
          keyboardType="number-pad"
        />
      </View>

      {/* Sport */}
      <View style={styles.section}>
        <Text style={styles.label}>Sport *</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.optionsRow}>
            {SPORTS.map((s) => (
              <TouchableOpacity
                key={s}
                style={[styles.option, sport === s && styles.optionActive]}
                onPress={() => setSport(s)}
              >
                <Text style={[styles.optionText, sport === s && styles.optionTextActive]}>
                  {s}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>

      {/* Manufacturer */}
      <View style={styles.section}>
        <Text style={styles.label}>Manufacturer *</Text>
        <TextInput
          style={styles.input}
          value={manufacturer}
          onChangeText={setManufacturer}
          placeholder="e.g. Topps, Panini, Upper Deck"
        />
      </View>

      {/* Set Name */}
      <View style={styles.section}>
        <Text style={styles.label}>Set Name</Text>
        <TextInput
          style={styles.input}
          value={setName}
          onChangeText={setSetName}
          placeholder="e.g. Prizm, Chrome"
        />
      </View>

      {/* Card Type */}
      <View style={styles.section}>
        <Text style={styles.label}>Card Type</Text>
        <TextInput
          style={styles.input}
          value={cardType}
          onChangeText={setCardType}
          placeholder="e.g. Rookie Card, Autograph, Jersey"
        />
      </View>

      {/* Card Number */}
      <View style={styles.section}>
        <Text style={styles.label}>Card Number</Text>
        <TextInput
          style={styles.input}
          value={cardNumber}
          onChangeText={setCardNumber}
          placeholder="e.g. #23"
        />
      </View>

      {/* Price */}
      <View style={styles.section}>
        <Text style={styles.label}>Price (USD) *</Text>
        <TextInput
          style={styles.input}
          value={price}
          onChangeText={setPrice}
          placeholder="e.g. 99.99"
          keyboardType="decimal-pad"
        />
      </View>

      {/* Condition */}
      <View style={styles.section}>
        <Text style={styles.label}>Condition *</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.optionsRow}>
            {CONDITIONS.map((c) => (
              <TouchableOpacity
                key={c}
                style={[styles.option, condition === c && styles.optionActive]}
                onPress={() => setCondition(c)}
              >
                <Text style={[styles.optionText, condition === c && styles.optionTextActive]}>
                  {c.replace('_', ' ')}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>

      {/* Graded */}
      <View style={styles.section}>
        <TouchableOpacity
          style={styles.checkboxRow}
          onPress={() => setIsGraded(!isGraded)}
        >
          <View style={[styles.checkbox, isGraded && styles.checkboxActive]}>
            {isGraded && <Text style={styles.checkmark}>✓</Text>}
          </View>
          <Text style={styles.checkboxLabel}>This card is graded</Text>
        </TouchableOpacity>
      </View>

      {isGraded && (
        <>
          <View style={styles.section}>
            <Text style={styles.label}>Grading Company</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.optionsRow}>
                {GRADING_COMPANIES.map((g) => (
                  <TouchableOpacity
                    key={g}
                    style={[styles.option, gradingCompany === g && styles.optionActive]}
                    onPress={() => setGradingCompany(g)}
                  >
                    <Text
                      style={[
                        styles.optionText,
                        gradingCompany === g && styles.optionTextActive,
                      ]}
                    >
                      {g}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
          </View>

          <View style={styles.section}>
            <Text style={styles.label}>Grade</Text>
            <TextInput
              style={styles.input}
              value={grade}
              onChangeText={setGrade}
              placeholder="e.g. 10, 9.5, GEM MT 10"
            />
          </View>
        </>
      )}

      {/* Description */}
      <View style={styles.section}>
        <Text style={styles.label}>Description</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          value={description}
          onChangeText={setDescription}
          placeholder="Additional details about the card..."
          multiline
          numberOfLines={4}
        />
      </View>

      {/* Submit Button */}
      <TouchableOpacity
        style={styles.submitButton}
        onPress={handleSubmit}
        disabled={uploading}
      >
        <LinearGradient
          colors={['#6366F1', '#8B5CF6']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.submitGradient}
        >
          {uploading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.submitText}>List Card</Text>
          )}
        </LinearGradient>
      </TouchableOpacity>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF',
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: '900',
    color: '#111827',
    marginBottom: 24,
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
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#111827',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  imagesContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  imagePreview: {
    width: 120,
    height: 160,
    borderRadius: 12,
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  removeButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#EF4444',
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '700',
  },
  addImageButton: {
    width: 120,
    height: 160,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    borderWidth: 2,
    borderColor: '#D1D5DB',
    borderStyle: 'dashed',
    justifyContent: 'center',
    alignItems: 'center',
  },
  addImageText: {
    fontSize: 32,
    marginBottom: 8,
  },
  addImageLabel: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '600',
  },
  optionsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  option: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
  },
  optionActive: {
    backgroundColor: '#6366F1',
  },
  optionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  optionTextActive: {
    color: '#FFF',
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxActive: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
  },
  checkmark: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '700',
  },
  checkboxLabel: {
    fontSize: 16,
    color: '#374151',
  },
  submitButton: {
    marginTop: 12,
  },
  submitGradient: {
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
  },
  submitText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: '700',
  },
});
EOF

echo "✓ UploadCardScreen created"

echo "Done! All screen files generated."
EOF

chmod +x /home/user/cv/wantli/generate-app.sh
