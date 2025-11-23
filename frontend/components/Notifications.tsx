import React, { useEffect, useRef } from "react";
import { View, Platform } from "react-native";
import * as Notifications from "expo-notifications";
import * as Permissions from "expo-permissions";
export default function FloatNotifications() {
  const notificationListener = useRef<Notifications.EventSubscription | null>(null);
  const responseListener = useRef<Notifications.EventSubscription | null>(null);
  useEffect(() => {
    if (Platform.OS === 'web') return;
    registerForPushNotificationsAsync().then((token) => {
      console.log('Push token registered:', token);
    });
    notificationListener.current = Notifications.addNotificationReceivedListener((notification) => {
      console.log('Notification received:', notification);
    });
    responseListener.current = Notifications.addNotificationResponseReceivedListener((response) => {
      console.log(response);
    });
    return () => {
      if (notificationListener.current) {
        Notifications.removeNotificationSubscription(notificationListener.current);
      }
      if (responseListener.current) {
        Notifications.removeNotificationSubscription(responseListener.current);
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
  const { status: existingStatus } = await Permissions.getAsync(Permissions.NOTIFICATIONS);
  let finalStatus = existingStatus;
  if (existingStatus !== 'granted') {
    const { status } = await Permissions.askAsync(Permissions.NOTIFICATIONS);
    finalStatus = status;
  }
  if (finalStatus !== 'granted') {
    alert('Failed to get push token for push notification!');
    return;
  }
  const token = (await Notifications.getExpoPushTokenAsync()).data;
  console.log(token);
  return token;
}
