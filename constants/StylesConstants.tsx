import { StyleSheet, Dimensions, Platform, useColorScheme } from "react-native";

const useStyles = () => {
  const windowWidth = Dimensions.get("window").width;
  const buttonWidth = windowWidth < 500 ? 150 : 200;

  const buttonMarginTop = Platform.OS === "android" ? 60 : 30;

  const colorScheme = useColorScheme();
  const headerImageColor = colorScheme === "light" ? "#60465a" : "#bfaeba";

  return StyleSheet.create({
    button: {
      padding: 20,
      borderRadius: 20,
      width: buttonWidth,
      alignSelf: "center",
    },
    incidentContainer: {
      flexDirection: "row",
      justifyContent: "space-between",
    },
    titleContainer: {
      flexDirection: "row",
      alignItems: "center",
      gap: 8,
    },
    stepContainer: {
      gap: 8,
      marginBottom: 8,
    },
    headerImage: {
      color: headerImageColor,
      bottom: -90,
      left: -35,
      position: "absolute",
    },
    input: {
      height: 200,
      borderColor: "#60465a",
      borderWidth: 5,
      marginTop: 10,
      fontSize: 20,
      padding: 10,
      backgroundColor: "#FFFFFF",
    },
    homeButtonContainer: {
      marginBottom: 8,
      flexDirection: "row",
      justifyContent: "space-evenly",
      margin: 10,
      marginTop: buttonMarginTop,
    },
  });
};

export default useStyles;
