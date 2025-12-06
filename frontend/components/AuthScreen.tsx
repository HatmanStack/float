import React, { useEffect, useState, useCallback } from 'react';
import { useColorScheme, Platform } from 'react-native';
import { Pressable } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { useGoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuth } from '@/context/AuthContext';
import useStyles from '@/constants/StylesConstants';
import { Colors } from '@/constants/Colors';
import * as WebBrowser from 'expo-web-browser';
import axios from 'axios';

// Only import and configure GoogleSignin on native platforms
let GoogleSignin: typeof import('@react-native-google-signin/google-signin').GoogleSignin | null = null;
if (Platform.OS !== 'web') {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  GoogleSignin = require('@react-native-google-signin/google-signin').GoogleSignin;
  GoogleSignin?.configure({
    webClientId: process.env.EXPO_PUBLIC_WEB_CLIENT_ID,
  });
}
WebBrowser.maybeCompleteAuthSession();

/**
 * User interface
 */
interface User {
  id: string;
  name: string;
}

/**
 * Custom hook for auth user loading
 */
function useUserLoader() {
  const [isUserLoaded, setIsUserLoaded] = useState(false);
  const { setUser } = useAuth();

  useEffect(() => {
    const loadUser = async () => {
      const storedUser = await AsyncStorage.getItem('user');
      if (storedUser) {
        const storedUserDict: User = JSON.parse(storedUser);
        if (storedUserDict.id !== 'guest') {
          setUser(storedUserDict);
        }
      }
      setIsUserLoaded(true);
    };
    loadUser();
  }, [setUser]);

  return isUserLoaded;
}

/**
 * Custom hook for authentication logic
 */
function useAuthentication() {
  const { user, setUser } = useAuth();

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const userInfo = await axios.get('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        });        const googleUser: User = { id: userInfo.data.email, name: userInfo.data.email };
        await AsyncStorage.setItem('user', JSON.stringify(googleUser));
        setUser(googleUser);
      } catch (error) {
        console.error('Error fetching user info', error);
      }
    },
    onError: (errorResponse) => console.error('Login error', errorResponse),
  });

  const handleGoogleLogin = useCallback(async () => {
    if (Platform.OS === 'web') {
      try {
        await googleLogin();
      } catch (error) {
        console.error('Error during web login', error);
      }
    } else if (Platform.OS === 'ios' || Platform.OS === 'android') {
      try {
        const userInfo = await GoogleSignin?.signIn();
        if (userInfo?.data?.user) {
          const googleUser: User = {
            id: userInfo.data.user.email ?? userInfo.data.user.id,
            name: userInfo.data.user.name ?? 'User',
          };
          await AsyncStorage.setItem('user', JSON.stringify(googleUser));
          setUser(googleUser);
        }
      } catch (error) {
        console.error('Google sign-in error', error);
      }
    }
  }, [googleLogin, setUser]);

  const handleGuestLogin = useCallback(async () => {
    const guestUser: User = { id: 'guest', name: 'Guest User' };
    await AsyncStorage.setItem('user', JSON.stringify(guestUser));
    setUser(guestUser);
  }, [setUser]);

  return {
    user,
    handleGoogleLogin,
    handleGuestLogin,
  };
}

/**
 * Authentication screen component
 */
const AuthScreen: React.FC = (): React.ReactNode => {
  const isUserLoaded = useUserLoader();
  const { user, handleGoogleLogin, handleGuestLogin } = useAuthentication();
  const styles = useStyles();
  const colorScheme = useColorScheme();
  const backgroundAuthColor = colorScheme === 'light' ? '#60465a' : '#bfaeba';

  if (!isUserLoaded) {
    return (
      <ThemedView style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ThemedText type="header">Loading...</ThemedText>
      </ThemedView>
    );
  }

  return (
    <ThemedView
      style={[
        {
          backgroundColor: backgroundAuthColor,
          justifyContent: 'space-evenly',
          alignItems: 'center',
          flex: 1,
          flexDirection: 'row',
        },
      ]}
    >
      {!user ? (
        <>
          <Pressable
            onPress={() => handleGoogleLogin()}
            style={({ pressed }) => [
              {
                backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
              },
              styles.button,
            ]}
          >
            {({ pressed }) => (
              <ThemedText type="header" style={[{ fontSize: 25, textAlign: 'center' }]}>
                {pressed ? 'Signing In...' : 'Google Login'}
              </ThemedText>
            )}
          </Pressable>
          <Pressable
            onPress={handleGuestLogin}
            style={({ pressed }) => [
              {
                backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
              },
              styles.button,
            ]}
          >
            {({ pressed }) => (
              <ThemedText type="header" style={[{ fontSize: 25, textAlign: 'center' }]}>
                {pressed ? 'GUEST!' : 'Guest User'}
              </ThemedText>
            )}
          </Pressable>
        </>
      ) : (
        <ThemedText type="header" style={styles.headerImage}>
          Welcome back!
        </ThemedText>
      )}
    </ThemedView>
  );
};

/**
 * Custom hook to get OAuth client ID based on platform
 */
function useClientId(): string {
  if (Platform.OS === 'web') {
    return process.env.EXPO_PUBLIC_WEB_CLIENT_ID || '';
  }
  if (Platform.OS === 'android') {
    return process.env.EXPO_PUBLIC_ANDROID_CLIENT_ID || '';
  }
  // iOS uses native GoogleSignin, not GoogleOAuthProvider
  return '';
}

/**
 * Custom authentication wrapper with Google OAuth provider
 */
const CustomAuth: React.FC = (): React.ReactNode => {
  const clientId = useClientId();

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <AuthScreen />
    </GoogleOAuthProvider>
  );
};

export default CustomAuth;
