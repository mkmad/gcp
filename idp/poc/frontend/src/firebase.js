import { initializeApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword, signOut } from 'firebase/auth';

// Get Firebase config from environment variable
const firebaseConfig = JSON.parse(process.env.FIREBASE_CONFIG || '{}');

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export const loginWithEmail = async (email, password) => {
  try {
    const result = await signInWithEmailAndPassword(auth, email, password);
    const token = await result.user.getIdToken();
    return { user: result.user, token };
  } catch (error) {
    throw new Error(`Authentication failed: ${error.message}`);
  }
};

export const logout = async () => {
  try {
    await signOut(auth);
  } catch (error) {
    throw new Error(`Logout failed: ${error.message}`);
  }
};

export const getCurrentUser = () => {
  return new Promise((resolve, reject) => {
    const unsubscribe = auth.onAuthStateChanged(user => {
      unsubscribe();
      resolve(user);
    }, reject);
  });
};

export default auth; 