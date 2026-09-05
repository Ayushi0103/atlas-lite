import { FormEvent, useState } from "react";
import { BackgroundLayer } from "./BackgroundLayer";
import { GlassCard } from "./Glass";
import { SparkleIcon } from "./Icons";
import { useAuth } from "../context/AuthContext";

type Mode = "login" | "register";

export function AuthPage() {
  const { login, register, isSubmitting, error, clearError } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function switchMode(nextMode: Mode) {
    setMode(nextMode);
    clearError();
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
      <BackgroundLayer />
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
