import { FormEvent, useState } from "react";
import { MoonIcon, SunIcon } from "./Icons";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { useNotifications } from "../context/NotificationsContext";

export function SettingsPanel() {
  const { user, updateProfile, changePassword } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { notify } = useNotifications();

  const [name, setName] = useState(user?.name ?? "");
  const [isSavingName, setIsSavingName] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isSavingPassword, setIsSavingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  async function handleNameSubmit(event: FormEvent) {
    event.preventDefault();
    const cleaned = name.trim();
    if (!cleaned || cleaned === user?.name) return;

    setIsSavingName(true);
    setNameError(null);
    try {
      await updateProfile(cleaned);
      notify("Profile updated", "Your display name has been changed.", "success");
    } catch (err) {
      setNameError(err instanceof Error ? err.message : "Could not update your name.");
    } finally {
      setIsSavingName(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault();
    if (!currentPassword || newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters.");
      return;
    }

    setIsSavingPassword(true);
    setPasswordError(null);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      notify("Password changed", "Use your new password next time you log in.", "success");
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : "Could not change your password.");
    } finally {
      setIsSavingPassword(false);
    }
  }

  return (
    <div className="popover settings-popover" role="menu">
      <div className="popover-header">
        <p className="popover-title">Settings</p>
      </div>

      <section className="settings-section">
        <h3>Appearance</h3>
        <button className="settings-theme-toggle" onClick={toggleTheme} type="button">
          {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          <span>{theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}</span>
        </button>
      </section>

      <div className="settings-divider" />

      <section className="settings-section">
        <h3>Display name</h3>
        <form className="settings-field" onSubmit={handleNameSubmit}>
          <input
            aria-label="Display name"
            onChange={(event) => setName(event.target.value)}
            type="text"
            value={name}
          />
          {nameError && <p className="auth-error error-copy">{nameError}</p>}
          <button disabled={isSavingName || !name.trim() || name.trim() === user?.name} type="submit">
            {isSavingName ? "Saving…" : "Save name"}
          </button>
        </form>
      </section>

      <div className="settings-divider" />

      <section className="settings-section">
        <h3>Change password</h3>
        <form className="settings-field" onSubmit={handlePasswordSubmit}>
          <input
            aria-label="Current password"
            onChange={(event) => setCurrentPassword(event.target.value)}
            placeholder="Current password"
            type="password"
            value={currentPassword}
          />
          <input
            aria-label="New password"
            onChange={(event) => setNewPassword(event.target.value)}
            placeholder="New password"
            type="password"
            value={newPassword}
          />
          {passwordError && <p className="auth-error error-copy">{passwordError}</p>}
          <button disabled={isSavingPassword} type="submit">
            {isSavingPassword ? "Updating…" : "Update password"}
          </button>
        </form>
      </section>
    </div>
  );
}