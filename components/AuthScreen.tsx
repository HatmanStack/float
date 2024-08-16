import React, { useEffect, useState } from "react";
import { useColorScheme } from "react-native";
import { Pressable } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";
import * as AuthSession from "expo-auth-session";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useAuth } from "@/context/AuthContext";
import useStyles from "@/constants/StylesConstants";
import { Colors } from "@/constants/Colors";
import * as WebBrowser from 'expo-web-browser';

WebBrowser.maybeCompleteAuthSession();

const AuthScreen = () => {
  const { user, setUser } = useAuth();
  const [isUserLoaded, setIsUserLoaded] = useState(false);
  const styles = useStyles();
  const [codeChallenge, setCodeChallenge] = useState(null);
  const [codeVerifier, setCodeVerifier] = useState(null);
  const colorScheme = useColorScheme();
  const backgroundAuthColor = colorScheme === "light" ? "#60465a" : "#bfaeba";

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

  const generateRandomString = (length) => {
    const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
    let result = '';
    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * charset.length);
      result += charset[randomIndex];
    }
    return result;
  };
  
  const base64URLEncode = (str) => {
    return str.toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');
  };
  
  const sha256 = async (plain) => {
    const encoder = new TextEncoder();
    const data = encoder.encode(plain);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return base64URLEncode(hash);
  };
  useEffect(() => {
    const setupPKCE = async () => {
      const verifier = generateRandomString(128);
      const challenge = await sha256(codeVerifier);
      setCodeVerifier(verifier);
      setCodeChallenge(challenge);
    };
    setupPKCE();
  }, []);
  
 
  const issuerUrl = 'https://accounts.google.com'; 
  const discovery = AuthSession.useAutoDiscovery(issuerUrl);
  
  const [request, response, promptAsync] = AuthSession.useAuthRequest(
    {
      clientId: '161595316472-kk9j373os9r9u71edgltf7k65afquhce.apps.googleusercontent.com',
      redirectUri: AuthSession.makeRedirectUri({ useProxy: true }),
      scopes: ['profile', 'email'],
      responseType: AuthSession.ResponseType.Code,
      codeChallengeMethod: AuthSession.CodeChallengeMethod.S256,
      codeChallenge
    },
    discovery
  );

  useEffect(() => {
    if (response) {
      console.log('Auth Response:', JSON.stringify(response, null, 2));
    }
    if (response?.type === 'success') {
      const { code } = response.params;
      console.log('Authorization Code:', code);
    const tokenRequestBody = {
      grant_type: 'authorization_code',
      code,
      client_id: '161595316472-kk9j373os9r9u71edgltf7k65afquhce.apps.googleusercontent.com',
      client_secret: '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',
      redirect_uri: AuthSession.makeRedirectUri({ useProxy: true }),
      code_verifier: codeVerifier,
    };
  
    console.log('Token Request Body:', JSON.stringify(tokenRequestBody, null, 2));
  
    fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams(tokenRequestBody).toString(),
    })
       .then((response) => {
    console.log('Raw Response:', response);
    return response.json();
  })
      .then((tokenResponse) => {
        const { access_token } = tokenResponse;
        console.log('Access Token:', access_token);
        // Fetch user info with the access token
        fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${access_token}` },
        })
          .then((res) => res.json())
          .then((userInfo) => {
            console.log('User Info:', userInfo);
            const { email } = userInfo;
            console.log('User Email:', email);
            AsyncStorage.setItem('user', JSON.stringify(userInfo));
            setUser(userInfo);
          })
          .catch((err) => console.error('Error fetching user info:', err));
      })
      .catch((err) => console.error('Error exchanging code for token:', err));
  }
  }, [response]);


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
              onPress={() => promptAsync()}
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

export default AuthScreen;
