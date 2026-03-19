import React, { useEffect, useRef } from 'react';
import { View, Platform } from 'react-native';
import * as Notifications from 'expo-notifications';

export default function FloatNotifications() {
  const notificationListener = useRef<Notifications.EventSubscription | null>(null);
  const responseListener = useRef<Notifications.EventSubscription | null>(null);

  useEffect(() => {
    if (Platform.OS === 'web') return;

    registerForPushNotificationsAsync()
      .then(() => {
        // Token registered
      })
      .catch((err) => {
        console.warn('Push notification registration failed', err);
      });

    notificationListener.current = Notifications.addNotificationReceivedListener(() => {
      // Notification received
    });

    responseListener.current = Notifications.addNotificationResponseReceivedListener(() => {
      // Response received
    });

    return () => {
      if (notificationListener.current) {
        notificationListener.current.remove();
      }
      if (responseListener.current) {
        responseListener.current.remove();
      }
    };
  }, []);

  return <View />;
}

async function registerForPushNotificationsAsync() {
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;
  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') {
    console.warn('Failed to get push token for push notification!');
    return;
  }
  const token = (await Notifications.getExpoPushTokenAsync()).data;
  return token;
}
