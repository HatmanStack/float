// app.config.js
import 'dotenv/config';

export default ({ config }) => ({
  expo: {
    name: "Float",
    slug: "audio-emotion-detection",
    version: "1.0.16",
    orientation: "portrait",
    icon: "./assets/images/self_improvement_icon.png",
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
      versionCode: 16,
      adaptiveIcon: {
        foregroundImage: "./assets/images/self_improvement_icon.png",
        backgroundColor: "#A1BE95",
        monochromeImage: "./assets/images/self_improvement_icon.png"
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
      favicon: "./assets/images/self_improvement_web.png"
    },
    plugins: [
      "expo-router"
    ],
    experiments: {
      typedRoutes: true
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