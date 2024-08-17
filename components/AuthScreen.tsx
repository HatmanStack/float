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

  const googleLogin = () => {
    if (Platform.OS === 'web') {  
    useGoogleLogin({
      onSuccess: async (tokenResponse) => {
        const userInfo = await axios.get(
          'https://www.googleapis.com/oauth2/v3/userinfo',
          { headers: { Authorization: `Bearer ${tokenResponse.access_token}` } },
        );
        await AsyncStorage.setItem("user", JSON.stringify(userInfo.data.email));
        setUser(userInfo.data.email);
      },
      onError: errorResponse => console.log(errorResponse),
    });
  } 
    if (Platform.OS === 'android') {
      GoogleSignin.signIn()
      .then((userInfo) => {
        console.log(userInfo);
        setUser(userInfo.user);
      })
      .catch((error) => {
        console.log(error);
    });
    }
  };
/** 
const googleLogin = useGoogleLogin({
  flow: 'auth-code',
  onSuccess: async (codeResponse) => {
      console.log(codeResponse);
      const tokens = await axios.post(
          'http://localhost:3001/auth/google', {
              code: codeResponse.code,
          });

      console.log(tokens);
  },
  onError: errorResponse => console.log(errorResponse),
});*/

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
