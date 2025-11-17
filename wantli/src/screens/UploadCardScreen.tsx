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
