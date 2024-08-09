
import { StyleSheet, Dimensions } from 'react-native';

const windowWidth = Dimensions.get('window').width;
const buttonWidth = windowWidth < 500 ? 150 : 200;
console.log('Button width:', buttonWidth);
console.log('Window width:', windowWidth);
const styles = StyleSheet.create({
  button: {
    padding: 20,
    borderRadius: 20,
    width: buttonWidth,
    alignSelf: 'center',
  }
  // Add other styles here if needed
});

export default styles;