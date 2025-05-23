// app.config.js


export default ({ config }) => ({
  expo: {
    name: "Float",
    slug: "audio-emotion-detection",
    version: "1.0.23",
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
      versionCode: 23,
      adaptiveIcon: {
        foregroundImage: "./assets/images/self_improvement_icon.png",
        backgroundColor: "#A1BE95",
        monochromeImage: "./assets/images/self_improvement_icon.png"
      },
      package: "com.hatmanstack.audioemotiondetection"
    },
    extra: {
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
      "expo-router",
      [
        "@react-native-google-signin/google-signin",
        {
          "iosUrlScheme": "com.googleusercontent.apps._some_id_here_",
        }
      ]
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