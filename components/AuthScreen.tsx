import React, { useEffect, useState } from "react";
import { useColorScheme, Platform } from "react-native";
import { Pressable } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";
import { useGoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useAuth } from "@/context/AuthContext";
import useStyles from "@/constants/StylesConstants";
import { Colors } from "@/constants/Colors";
import * as WebBrowser from 'expo-web-browser';
import { GoogleSignin } from '@react-native-google-signin/google-signin';

GoogleSignin.configure();
import axios from 'axios';

WebBrowser.maybeCompleteAuthSession();

const AuthScreen = () => {
  const { user, setUser } = useAuth();
  const [isUserLoaded, setIsUserLoaded] = useState(false);
  const styles = useStyles();
  const colorScheme = useColorScheme();
  const backgroundAuthColor = colorScheme === "light" ? "#60465a" : "#bfaeba";

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const userInfo = await axios.get(
          'https://www.googleapis.com/oauth2/v3/userinfo',
          { headers: { Authorization: `Bearer ${tokenResponse.access_token}` } }
        );
        const googleUser = { id: userInfo.data.email, name: userInfo.data.email};
        await AsyncStorage.setItem("user", JSON.stringify(googleUser));
        console.log(googleUser)
        setUser(googleUser);
      } catch (error) {
        console.error("Error fetching user info", error);
      }
    },
    onError: (errorResponse) => console.error("Login error", errorResponse),
  });

  const handleGoogleLogin = async () => {
    if (Platform.OS === 'web') {
      try {
        await googleLogin(); // Call the login function
      } catch (error) {
        console.error("Error during web login", error);
      }
    } else if (Platform.OS === 'android') {
      try {
        const userInfo = await GoogleSignin.signIn();
        console.log(userInfo);
        setUser(userInfo.user);
      } catch (error) {
        console.error("Google sign-in error", error);
      }
    }
  };

  useEffect(() => {
    const loadUser = async () => {
      const storedUser = await AsyncStorage.getItem("user");
      if (storedUser) {
        const storedUserDict = JSON.parse(storedUser);
        if (storedUserDict.id !== "guest") {
          setUser(storedUserDict);
        }
      }
      setIsUserLoaded(true);
    };
    loadUser();
  }, []);

  const handleGuestLogin = async () => {
    const guestUser = { id: "guest", name: "Guest User" };
    await AsyncStorage.setItem("user", JSON.stringify(guestUser));
    setUser(guestUser);
    
  };

  if (!isUserLoaded) {
    return <ThemedView style={{flex:1, justifyContent: "center",
      alignItems: "center"}}><ThemedText type="header">Loading...</ThemedText></ThemedView>;
  }

  return (
    <ThemedView
      style={[
        {
          backgroundColor: backgroundAuthColor,
          justifyContent: "space-evenly",
          alignItems: "center",
          flex: 1,
          flexDirection: "row",
        },
      ]}
    >
      {!user ? (
        <>
            <Pressable
              onPress={() => googleLogin()}
              style={({ pressed }) => [
                {
                  backgroundColor: pressed
                    ? Colors["buttonPressed"]
                    : Colors["buttonUnpressed"],
                },
                styles.button, 
              ]}
            >
              {({ pressed }) => (
                <ThemedText
                type="header"
                style={[
                  { fontSize: 25 },
                  pressed && { textAlign: "center" },
                ]}
              >
                  {pressed ? "GOOGLING!" : "GOOgle LOgin"}
                </ThemedText>
              )}
            </Pressable>
            <Pressable
              onPress={handleGuestLogin}
              style={({ pressed }) => [
                {
                  backgroundColor: pressed
                    ? Colors["buttonPressed"]
                    : Colors["buttonUnpressed"],
                },
                styles.button, 
              ]}
            >
              {({ pressed }) => (
                <ThemedText
                type="header"
                style={[
                  { fontSize: 25 },
                  pressed && { textAlign: "center" },
                ]}
              >
                  {pressed ? "GUEST!" : "Guest User"}
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

const Tricky = () => {
  const [clientId, setClientId] = useState("");

  useEffect(() => {
    if (Platform.OS === 'web') {
      setClientId(process.env.EXPO_PUBLIC_WEB_CLIENT_ID);
    }
    if (Platform.OS === 'android') {
      setClientId(process.env.EXPO_PUBLIC_ANDROID_CLIENT_ID);
    }
  }, []);

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <AuthScreen />
    </GoogleOAuthProvider>
  );
};
export default Tricky;
