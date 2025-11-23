import React, { useEffect, useState, useCallback } from "react";
import { useColorScheme, Platform } from "react-native";
import { Pressable } from "react-native";
import { ThemedText } from "@/frontend/components/ThemedText";
import { ThemedView } from "@/frontend/components/ThemedView";
import { useGoogleLogin, GoogleOAuthProvider } from "@react-oauth/google";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useAuth } from "@/frontend/context/AuthContext";
import useStyles from "@/frontend/constants/StylesConstants";
import { Colors } from "@/frontend/constants/Colors";
import * as WebBrowser from "expo-web-browser";
import { GoogleSignin } from "@react-native-google-signin/google-signin";
import axios from "axios";
GoogleSignin.configure({
  webClientId: process.env.EXPO_PUBLIC_WEB_CLIENT_ID,
});
WebBrowser.maybeCompleteAuthSession();
interface User {
  id: string;
  name: string;
}
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
function useAuthentication() {
  const { user, setUser } = useAuth();
  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const userInfo = await axios.get('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        });
        console.log('[Auth] User authenticated via Google');
        const googleUser: User = { id: userInfo.data.email, name: userInfo.data.email };
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
        const userInfo = await GoogleSignin.signIn();
        console.log('[Auth] Native Google Sign-In successful');
        const user = (userInfo as any).user as User;
        await AsyncStorage.setItem('user', JSON.stringify(user));
        setUser(user);
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
function useClientId(): string {
  if (Platform.OS === 'web') {
    return process.env.EXPO_PUBLIC_WEB_CLIENT_ID || '";
  }
  if (Platform.OS === 'android') {
    return process.env.EXPO_PUBLIC_ANDROID_CLIENT_ID || '";
  }
  return '";
}
const CustomAuth: React.FC = (): React.ReactNode => {
  const clientId = useClientId();
  return (
    <GoogleOAuthProvider clientId={clientId}>
      <AuthScreen />
    </GoogleOAuthProvider>
  );
};
export default CustomAuth;
