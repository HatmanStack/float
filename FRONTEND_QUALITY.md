# Frontend Code Quality Standards

This document outlines the code quality standards and best practices for the Float frontend codebase. All frontend changes must adhere to these standards before being merged.

## Table of Contents

1. [Overview](#overview)
2. [TypeScript Standards](#typescript-standards)
3. [React Component Patterns](#react-component-patterns)
4. [ESLint Rules](#eslint-rules)
5. [Prettier Formatting](#prettier-formatting)
6. [Testing](#testing)
7. [Before You Commit](#before-you-commit)
8. [Common Patterns](#common-patterns)

---

## Overview

The Float frontend uses the following tools to maintain code quality:

- **TypeScript 5.3**: Strict type checking for type safety
- **ESLint 8.x**: Linting with React and TypeScript plugins
- **Prettier 3.x**: Opinionated code formatting
- **Jest**: Unit and component testing

### Quality Goals

- 100% TypeScript strict mode compliance
- 0 ESLint errors (warnings are acceptable)
- 100% Prettier formatted code
- Consistent component patterns across the codebase
- Readable, maintainable code with proper type safety

---

## TypeScript Standards

### Strict Mode Enabled

All TypeScript files use strict mode. This includes:

- `strict: true` in tsconfig.json
- No `any` types without explicit reasoning
- Non-null checks required
- Type inference where possible, explicit types for public APIs

### Type Annotations

**Required for:**

- Function parameters and return types
- Component props (via Props interface)
- Component return types (always `React.ReactNode`)
- Class properties
- Function exports

**Optional for:**

- Internal function variables (use type inference)
- Loop variables where type is obvious
- React hook variables with clear initialization

### Example: Typed Function

```typescript
// ✓ Good
interface SummaryResponse {
  id: string;
  title: string;
  content: string;
}

async function fetchSummary(id: string): Promise<SummaryResponse> {
  const response = await fetch(`/api/summary/${id}`);
  return response.json();
}

// ✗ Bad
async function fetchSummary(id) {
  const response = await fetch(`/api/summary/${id}`);
  return response.json();
}
```

---

## React Component Patterns

### Component Structure

All React components should follow this pattern:

```typescript
import React from 'react';
import { View } from 'react-native';

/**
 * Props for MyComponent
 */
interface MyComponentProps {
  title: string;
  onPress?: () => void;
  disabled?: boolean;
}

/**
 * Description of what this component does
 */
export function MyComponent({
  title,
  onPress,
  disabled,
}: MyComponentProps): React.ReactNode {
  return (
    <View>
      {/* Component JSX here */}
    </View>
  );
}
```

### Key Points

1. **Props Interface**: All components with props must have a `Props` interface at the top of the file
2. **Return Type**: Components must explicitly return `React.ReactNode`
3. **Destructuring**: Destructure props in the function signature
4. **JSDoc**: Complex components should have JSDoc comments
5. **Function Declaration**: Use `function` (not `const` with arrow) for components

### Props Interface Pattern

```typescript
// ✓ Good
interface CardProps {
  title: string;
  description: string;
  onPress?: () => void;
}

export function Card({ title, description, onPress }: CardProps): React.ReactNode {
  return <View>...</View>;
}

// ✗ Bad - No Props interface, inline types
export const Card = (props: { title: string; description: string }) => {
  return <View>...</View>;
};

// ✗ Bad - Using 'any'
export function Card(props: any): React.ReactNode {
  return <View>...</View>;
}
```

### Unused Props

If a component receives a prop it doesn't use, prefix with underscore:

```typescript
// ✓ Good
interface ButtonProps {
  onPress?: () => void;
  _testID?: string; // Internal use only
}

export function Button({ onPress, _testID }: ButtonProps): React.ReactNode {
  return <Pressable onPress={onPress} testID={_testID} />;
}
```

### Custom Hooks

Extract complex logic into custom hooks with `use` prefix:

```typescript
// ✓ Good - Custom hook
function useAudioPlayback(url: string) {
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [duration, setDuration] = React.useState(0);

  const play = React.useCallback(async () => {
    // Play logic
    setIsPlaying(true);
  }, [url]);

  return { isPlaying, duration, play };
}

// Component using hook
export function AudioPlayer({ url }: AudioPlayerProps): React.ReactNode {
  const { isPlaying, duration, play } = useAudioPlayback(url);
  return <View>...</View>;
}
```

---

## ESLint Rules

### Configuration

ESLint is configured via `.eslintrc.json` with:

- ESLint recommended rules
- React plugin rules
- TypeScript plugin rules
- React Hooks plugin rules

### Important Rules

| Rule                                                | Severity | Reason                                                  |
| --------------------------------------------------- | -------- | ------------------------------------------------------- |
| `no-console`                                        | Warning  | Development logging is OK, but avoid in production code |
| `no-unused-vars`                                    | Error    | Dead code should be removed                             |
| `react-hooks/rules-of-hooks`                        | Error    | Hooks must follow React rules                           |
| `react-hooks/exhaustive-deps`                       | Warning  | Missing dependencies can cause stale state              |
| `@typescript-eslint/explicit-module-boundary-types` | Off      | Too verbose for internal functions                      |
| `@typescript-eslint/no-explicit-any`                | Warning  | Avoid `any`, use proper types                           |

### Common Violations and Fixes

**Problem**: Unused imports

```typescript
// ✗ Bad
import { View, Text, ScrollView } from 'react-native';
// ScrollView is unused

// ✓ Good
import { View, Text } from 'react-native';
```

**Problem**: Missing prop type

```typescript
// ✗ Bad - Parameter has implicit 'any' type
function handlePress(index) {
  console.log(index);
}

// ✓ Good
function handlePress(index: number): void {
  console.log(index);
}
```

**Problem**: console.log in production code

```typescript
// ✗ Bad - Debug logging in component
export function MyComponent(props: MyProps): React.ReactNode {
  console.log('Rendering component');
  return <View>...</View>;
}

// ✓ Good - Wrap in __DEV__ check
export function MyComponent(props: MyProps): React.ReactNode {
  if (__DEV__) {
    console.log('Rendering component');
  }
  return <View>...</View>;
}
```

---

## Prettier Formatting

### Configuration

Prettier is configured via `.prettierrc.json`:

```json
{
  "printWidth": 100,
  "tabWidth": 2,
  "singleQuote": true,
  "trailingComma": "es5",
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### Key Settings

- **Print Width**: Lines max 100 characters
- **Tab Width**: 2 spaces per indentation
- **Quotes**: Single quotes for strings (except JSX)
- **Trailing Commas**: Add to multiline structures
- **Arrow Parens**: Always include parentheses

### Common Formatting Issues

**Problem**: Line too long

```typescript
// ✗ Bad - 120 characters
const veryLongString =
  'This is a very long string that exceeds the 100 character limit and should be split';

// ✓ Good - Split into multiple lines
const veryLongString =
  'This is a very long string that exceeds the 100 character limit ' + 'and should be split';
```

**Problem**: Inconsistent spacing

```typescript
// ✗ Bad - Inconsistent object spacing
const obj = { name: 'John', age: 30, city: 'New York' };

// ✓ Good - Consistent spacing
const obj = { name: 'John', age: 30, city: 'New York' };
```

---

## Testing

### Test File Location

- Component tests: `components/__tests__/ComponentName-test.tsx`
- Page tests: `app/__tests__/PageName-test.tsx`
- Hook tests: `hooks/__tests__/useHookName-test.ts`

### Test Patterns

```typescript
// ✓ Good test structure
import React from 'react';
import { render, screen } from '@testing-library/react-native';
import { MyComponent } from '../MyComponent';

describe('MyComponent', () => {
  it('should render with title prop', () => {
    render(<MyComponent title="Test Title" />);
    expect(screen.getByText('Test Title')).toBeDefined();
  });

  it('should call onPress when button is pressed', () => {
    const onPress = jest.fn();
    render(<MyComponent title="Test" onPress={onPress} />);
    screen.getByRole('button').onPress?.();
    expect(onPress).toHaveBeenCalled();
  });
});
```

---

## Before You Commit

### Quality Checklist

Run these checks locally before committing:

```bash
# 1. Type checking
npm run type-check

# 2. Linting (should show 0 errors)
npm run lint

# 3. Formatting (should show no files needing formatting)
npm run format:check

# 4. Tests (should pass)
npm test

# 5. OR run all checks together
./check_frontend_quality.sh
```

### Git Hooks (Optional)

Consider setting up pre-commit hooks to run checks automatically:

```bash
# Install husky and lint-staged
npm install -D husky lint-staged

# Setup pre-commit hook
npx husky install
npx husky add .husky/pre-commit 'npm run format && npm run lint:fix'
```

### Commit Message Format

Use descriptive commit messages:

```
feat: add audio playback component
fix: prevent memory leak in audio player
refactor: extract common styles to theme
style: format with Prettier
test: add tests for AudioPlayer
```

---

## Common Patterns

### Conditional Rendering

```typescript
// ✓ Good - Ternary for single condition
export function Card(props: CardProps): React.ReactNode {
  return (
    <View>
      {props.badge && <Badge text={props.badge} />}
      <Text>{props.title}</Text>
    </View>
  );
}

// ✓ Good - Early return for complex logic
export function UserProfile(props: UserProfileProps): React.ReactNode {
  if (!props.user) {
    return <Text>User not found</Text>;
  }

  return (
    <View>
      <Text>{props.user.name}</Text>
      {/* User profile UI */}
    </View>
  );
}
```

### Event Handlers

```typescript
// ✓ Good - Named handler
interface ButtonProps {
  onPress?: () => void;
}

export function SubmitButton(props: ButtonProps): React.ReactNode {
  const handlePress = () => {
    console.log('Submit clicked');
    props.onPress?.();
  };

  return <Pressable onPress={handlePress}><Text>Submit</Text></Pressable>;
}

// ✗ Bad - Inline complex logic
export function SubmitButton(props: ButtonProps): React.ReactNode {
  return (
    <Pressable
      onPress={() => {
        console.log('Submit clicked');
        props.onPress?.();
      }}
    >
      <Text>Submit</Text>
    </Pressable>
  );
}
```

### State Management with useState

```typescript
// ✓ Good - Separate state concerns
export function Form(_props: FormProps): React.ReactNode {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    // Submit logic
    setIsSubmitting(false);
  };

  return <View>...</View>;
}

// ✗ Bad - Mixed concerns in single state
export function Form(_props: FormProps): React.ReactNode {
  const [formState, setFormState] = React.useState({
    email: '',
    password: '',
    isSubmitting: false,
  });
  // Makes update logic complex
}
```

### Effects with Cleanup

```typescript
// ✓ Good - Effect with cleanup
export function AudioPlayer({ url }: AudioPlayerProps): React.ReactNode {
  const [isPlaying, setIsPlaying] = React.useState(false);

  React.useEffect(() => {
    const audio = new Audio(url);

    return () => {
      audio.stop();
      audio.release();
    };
  }, [url]);

  return <View>...</View>;
}
```

---

## Resources

- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Documentation](https://react.dev/)
- [ESLint Configuration](https://eslint.org/docs/latest/use/configure/)
- [Prettier Documentation](https://prettier.io/docs/en/index.html)
- [Jest Testing Framework](https://jestjs.io/)

---

## Questions or Disagreements?

If you have questions about these standards or feel a rule should be changed:

1. Discuss in the team
2. Update this document if consensus is reached
3. Update ESLint/Prettier config if tooling changes

Remember: consistent code is better than perfect code.
