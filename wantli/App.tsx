import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ActivityIndicator, View, StyleSheet, Text } from 'react-native';
import { authStorage } from './src/utils/auth';

// Screens
import AuthScreen from './src/screens/AuthScreen';
import DiscoverScreen from './src/screens/DiscoverScreen';
import LikesScreen from './src/screens/LikesScreen';
import UploadCardScreen from './src/screens/UploadCardScreen';
import MessagesScreen from './src/screens/MessagesScreen';
import AccountScreen from './src/screens/AccountScreen';
import CardDetailScreen from './src/screens/CardDetailScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Global setter for authentication state
let globalSetIsAuthenticated: ((value: boolean) => void) | null = null;

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#6366F1',
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarStyle: {
          backgroundColor: '#FFF',
          borderTopWidth: 1,
          borderTopColor: '#E5E7EB',
          paddingBottom: 8,
          paddingTop: 8,
          height: 68,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
        },
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="Discover"
        options={{
          tabBarLabel: 'Discover',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>🎴</Text>
          ),
        }}
      >
        {(props) => (
          <DiscoverScreen
            {...props}
            onCardPress={(cardId) => props.navigation.navigate('CardDetail', { cardId })}
          />
        )}
      </Tab.Screen>

      <Tab.Screen
        name="Likes"
        component={LikesScreen}
        options={{
          tabBarLabel: 'Likes',
          tabBarIcon: () => <Text style={{ fontSize: 24 }}>♥️</Text>,
        }}
      />

      <Tab.Screen
        name="Upload"
        component={UploadCardScreen}
        options={{
          tabBarLabel: '',
          tabBarIcon: () => (
            <View
              style={{
                width: 56,
                height: 56,
                borderRadius: 28,
                backgroundColor: '#6366F1',
                justifyContent: 'center',
                alignItems: 'center',
                marginTop: -20,
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 4 },
                shadowOpacity: 0.3,
                shadowRadius: 8,
                elevation: 8,
              }}
            >
              <Text style={{ fontSize: 28, color: '#FFF', fontWeight: '700' }}>+</Text>
            </View>
          ),
        }}
      />

      <Tab.Screen
        name="Messages"
        component={MessagesScreen}
        options={{
          tabBarLabel: 'Messages',
          tabBarIcon: () => <Text style={{ fontSize: 24 }}>💬</Text>,
        }}
      />

      <Tab.Screen
        name="Account"
        options={{
          tabBarLabel: 'Account',
          tabBarIcon: () => <Text style={{ fontSize: 24 }}>👤</Text>,
        }}
      >
        {(props) => (
          <AccountScreen
            {...props}
            onSignOut={() => globalSetIsAuthenticated && globalSetIsAuthenticated(false)}
          />
        )}
      </Tab.Screen>
    </Tab.Navigator>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Make setter globally accessible
  globalSetIsAuthenticated = setIsAuthenticated;

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await authStorage.getToken();
      setIsAuthenticated(!!token);
    } catch (error) {
      console.error('Error checking auth:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366F1" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!isAuthenticated ? (
          <Stack.Screen name="Auth">
            {(props) => <AuthScreen {...props} onAuth={() => setIsAuthenticated(true)} />}
          </Stack.Screen>
        ) : (
          <>
            <Stack.Screen name="Main" component={MainTabs} />
            <Stack.Screen
              name="CardDetail"
              component={CardDetailScreen}
              options={{
                headerShown: true,
                headerTitle: '',
                headerTransparent: true,
                headerTintColor: '#111827',
              }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFF',
  },
});
