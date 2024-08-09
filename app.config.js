// app.config.js
import 'dotenv/config';

export default ({ config }) => ({
  expo: {
    name: "audio-emotion-detection",
    slug: "audio-emotion-detection",
    version: "1.0.6",
    orientation: "portrait",
    icon: "./assets/images/self_improvement_48dp.png",
    scheme: "myapp",
    userInterfaceStyle: "automatic",
    splash: {
      image: "./assets/images/self_improvement_splash.png",
      resizeMode: "contain",
      backgroundColor: "#ffffff"
    },
    
    ios: {
      supportsTablet: true
    },
    android: {
      versionCode: 6,
      adaptiveIcon: {
        foregroundImage: "./assets/images/self_improvement_48dp.png",
        backgroundColor: "#A1BE95",
        monochromeImage: "./assets/images/self_improvement_48dp.png"
      },
      package: "com.hatmanstack.audioemotiondetection"
    },
    extra: {
      AWS_ID: process.env.AWS_ID,
          AWS_SECRET: process.env.AWS_SECRET,
          AWS_REGION: process.env.AWS_REGION,
      router: {
        origin: false
      },
      eas: {
        projectId: "6153244b-98d4-4cca-b254-a0b6c8cefe83"
      }
    },
    web: {
      bundler: "metro",
      output: "static",
      favicon: "./assets/images/self_improvement_48dp.png"
    },
    plugins: [
      "expo-router"
    ],
    experiments: {
      typedRoutes: true
    },
    build: {
      development: {
        distribution: "internal",
        android: {
          buildType: "apk"
        },
        ios: {
          simulator: true
        }
      },
      production: {
        distribution: "store",
        android: {
          buildType: "app-bundle"
        },
        ios: {
          simulator: false
        }
      }
    },
    runtimeVersion: {
      policy: "appVersion"
    },
    updates: {
      url: "https://u.expo.dev/6153244b-98d4-4cca-b254-a0b6c8cefe83"
    },
    assetBundlePatterns: [
      "**/*",
      "./assets/fonts/*.otf"  
    ]
  }
});