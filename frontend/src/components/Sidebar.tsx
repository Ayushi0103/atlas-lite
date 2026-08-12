import { useEffect, useRef, useState } from "react";
import type { ReactElement } from "react";
import { BellIcon, ChatIcon, GridIcon, HomeIcon, MoonIcon, SearchIcon, SettingsIcon, SunIcon } from "./Icons";
import { NotificationsPanel } from "./NotificationsPanel";
import { SettingsPanel } from "./SettingsPanel";
import { useAuth } from "../context/AuthContext";
import { useNotifications } from "../context/NotificationsContext";
import { useTheme } from "../context/ThemeContext";
import type { AppView } from "../types/atlas";

type SidebarProps = {
  currentView: AppView;
  onNavigate: (view: AppView) => void;
};

type NavItem = {
  label: string;
  icon: ReactElement;
  view: AppView;
};

type PopoverKey = "profile" | "notifications" | "settings";

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0][0]?.toUpperCase() ?? "?";
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export function Sidebar({ currentView, onNavigate }: SidebarProps) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { unreadCount } = useNotifications();
  const [openPopover, setOpenPopover] = useState<PopoverKey | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickAway(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpenPopover(null);
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpenPopover(null);
    }
    document.addEventListener("mousedown", handleClickAway);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickAway);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  function togglePopover(key: PopoverKey) {
    setOpenPopover((current) => (current === key ? null : key));
  }

  const items: NavItem[] = [
    { label: "Home", icon: <HomeIcon />, view: "home" },
    { label: "Search", icon: <SearchIcon />, view: "search" },
    { label: "Collections", icon: <GridIcon />, view: "collections" },
    { label: "Chat", icon: <ChatIcon />, view: "chat" },
  ];

  return (
    <nav className="side-rail" aria-label="Primary" ref={rootRef}>
      <div className="side-group">
        {items.map((item) => (
          <button
            aria-current={currentView === item.view ? "page" : undefined}
            aria-label={item.label}
            className={`rail-button ${currentView === item.view ? "is-active" : ""}`}
            key={item.label}
            onClick={() => onNavigate(item.view)}
            title={item.label}
            type="button"
          >
            {item.icon}
          </button>
        ))}
      </div>

      <div className="profile-menu">
        <button
          aria-expanded={openPopover === "profile"}
          aria-label="Profile"
          className="avatar-button"
          onClick={() => togglePopover("profile")}
          type="button"
        >
          <span>{user ? getInitials(user.name) : "?"}</span>
        </button>
        {openPopover === "profile" && (
          <div className="profile-popover" role="menu">
            <p className="profile-name">{user?.name}</p>
            <p className="profile-email">{user?.email}</p>
            <button
              className="profile-logout"
              onClick={() => {
                setOpenPopover(null);
                logout();
              }}
              role="menuitem"
              type="button"
            >
              Log out
            </button>
          </div>
        )}
      </div>

      <div className="side-group">
        <div className="rail-popover-anchor">
          <button
            aria-expanded={openPopover === "notifications"}
            aria-label="Notifications"
            className={`rail-button ${openPopover === "notifications" ? "is-active" : ""}`}
            onClick={() => togglePopover("notifications")}
            title="Notifications"
            type="button"
          >
            <BellIcon />
            {unreadCount > 0 && (
              <span className="rail-badge" aria-hidden="true">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>
          {openPopover === "notifications" && <NotificationsPanel />}
        </div>

        <div className="rail-popover-anchor">
          <button
            aria-expanded={openPopover === "settings"}
            aria-label="Settings"
            className={`rail-button ${openPopover === "settings" ? "is-active" : ""}`}
            onClick={() => togglePopover("settings")}
            title="Settings"
            type="button"
          >
            <SettingsIcon />
          </button>
          {openPopover === "settings" && <SettingsPanel />}
        </div>

        <button
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          className="rail-button"
          onClick={toggleTheme}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          type="button"
        >
          {theme === "dark" ? <SunIcon /> : <MoonIcon />}
        </button>
      </div>
    </nav>
  );
}