import { initializeApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword, signOut, GoogleAuthProvider, signInWithPopup } from 'firebase/auth';

// Firebase configuration will be loaded from environment variables
// These will be set by Cloud Run using the firebase-config secret
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Get Auth instance
export const auth = getAuth(app);

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

export const loginWithGoogle = async () => {
  try {
    const provider = new GoogleAuthProvider();
    const result = await signInWithPopup(auth, provider);
    const token = await result.user.getIdToken();
    return { user: result.user, token };
  } catch (error) {
    throw new Error(`Google authentication failed: ${error.message}`);
  }
};

export default app; 