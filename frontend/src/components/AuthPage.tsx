import { FormEvent, useEffect, useRef, useState } from "react";
import { GlassCard } from "./Glass";
import { SparkleIcon } from "./Icons";
import { useAuth } from "../context/AuthContext";

type Mode = "login" | "register";

type GoogleCredentialResponse = {
  credential?: string;
};

type GoogleButtonText = "signin_with" | "signup_with";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: GoogleCredentialResponse) => void;
          }) => void;
          renderButton: (
            parent: HTMLElement,
            options: {
              shape: "pill";
              size: "large";
              text: GoogleButtonText;
              theme: "outline";
              width: string;
            },
          ) => void;
        };
      };
    };
  }
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;
const GOOGLE_SCRIPT_ID = "google-identity-services";

export function AuthPage() {
  const { login, googleSignIn, register, isSubmitting, error, clearError } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [googleError, setGoogleError] = useState<string | null>(null);
  const googleButtonRef = useRef<HTMLDivElement>(null);
  const isGoogleOriginSupported =
    window.location.protocol === "https:" ||
    (window.location.protocol === "http:" && window.location.hostname === "localhost");

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !isGoogleOriginSupported) return;

    function renderGoogleButton() {
      if (!GOOGLE_CLIENT_ID || !window.google || !googleButtonRef.current) return;

      googleButtonRef.current.innerHTML = "";
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response) => {
          if (!response.credential) {
            setGoogleError("Google did not return a sign-in credential.");
            return;
          }

          setGoogleError(null);
          void googleSignIn(response.credential).catch(() => {
            // error is already surfaced via context state
          });
        },
      });
      window.google.accounts.id.renderButton(googleButtonRef.current, {
        shape: "pill",
        size: "large",
        text: mode === "login" ? "signin_with" : "signup_with",
        theme: "outline",
        width: "100%",
      });
    }

    const existingScript = document.getElementById(GOOGLE_SCRIPT_ID) as HTMLScriptElement | null;
    if (window.google) {
      renderGoogleButton();
      return;
    }

    const script = existingScript ?? document.createElement("script");
    script.id = GOOGLE_SCRIPT_ID;
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = renderGoogleButton;
    script.onerror = () => setGoogleError("Could not load Google sign-in.");

    if (!existingScript) {
      document.head.appendChild(script);
    }
  }, [googleSignIn, isGoogleOriginSupported, mode]);

  function switchMode(nextMode: Mode) {
    setMode(nextMode);
    clearError();
    setGoogleError(null);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      if (mode === "login") {
        await login(email.trim(), password);
      } else {
        await register(name.trim(), email.trim(), password);
      }
    } catch {
      // error is already surfaced via context state
    }
  }

  return (
    <div className="app-shell auth-shell">
      <div className="auth-frame">
        <GlassCard className="auth-card">
          <div className="auth-brand">
            <SparkleIcon aria-hidden="true" />
            <span>KORA</span>
          </div>
          <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
          <p className="auth-subtitle">
            {mode === "login"
              ? "Log in to reach your private knowledge base."
              : "Your notes, documents, and chats stay private to your account."}
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            {mode === "register" && (
              <label className="auth-field">
                <span>Name</span>
                <input
                  autoComplete="name"
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Ada Lovelace"
                  required
                  type="text"
                  value={name}
                />
              </label>
            )}
            <label className="auth-field">
              <span>Email</span>
              <input
                autoComplete="email"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                required
                type="email"
                value={email}
              />
            </label>
            <label className="auth-field">
              <span>Password</span>
              <input
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                minLength={mode === "register" ? 8 : undefined}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={mode === "register" ? "At least 8 characters" : "••••••••"}
                required
                type="password"
                value={password}
              />
            </label>

            {error && <p className="error-copy auth-error">{error}</p>}

            <button className="auth-submit" disabled={isSubmitting} type="submit">
              {isSubmitting
                ? mode === "login"
                  ? "Logging in…"
                  : "Creating account…"
                : mode === "login"
                  ? "Log in"
                  : "Create account"}
            </button>
          </form>

          <div className="auth-divider">
            <span>or</span>
          </div>

          {GOOGLE_CLIENT_ID && isGoogleOriginSupported ? (
            <div className="google-signin-slot" ref={googleButtonRef} />
          ) : (
            <button className="google-config-button" disabled type="button">
              Sign in with Google
            </button>
          )}
          {!GOOGLE_CLIENT_ID && (
            <p className="auth-helper">Add VITE_GOOGLE_CLIENT_ID to enable Google sign-in.</p>
          )}
          {GOOGLE_CLIENT_ID && !isGoogleOriginSupported && (
            <p className="auth-helper">Open KORA at http://localhost:5173 to use Google sign-in.</p>
          )}
          {googleError && <p className="error-copy auth-error">{googleError}</p>}

          <p className="auth-switch">
            {mode === "login" ? (
              <>
                Don't have an account?{" "}
                <button onClick={() => switchMode("register")} type="button">
                  Sign up
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button onClick={() => switchMode("login")} type="button">
                  Log in
                </button>
              </>
            )}
          </p>
        </GlassCard>
      </div>
    </div>
  );
}
