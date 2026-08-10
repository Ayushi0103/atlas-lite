import { useEffect, useRef, useState } from "react";
import type { ReactElement } from "react";
import { BellIcon, ChatIcon, GridIcon, HomeIcon, MoonIcon, SearchIcon, SettingsIcon, SunIcon } from "./Icons";
import { useAuth } from "../context/AuthContext";
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

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0][0]?.toUpperCase() ?? "?";
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export function Sidebar({ currentView, onNavigate }: SidebarProps) {
  const { user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickAway(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickAway);
    return () => document.removeEventListener("mousedown", handleClickAway);
  }, []);

  const items: NavItem[] = [
    { label: "Home", icon: <HomeIcon />, view: "home" },
    { label: "Search", icon: <SearchIcon />, view: "search" },
    { label: "Collections", icon: <GridIcon />, view: "collections" },
    { label: "Chat", icon: <ChatIcon />, view: "chat" },
  ];

  return (
    <nav className="side-rail" aria-label="Primary">
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

      <div className="profile-menu" ref={menuRef}>
        <button
          aria-expanded={isMenuOpen}
          aria-label="Profile"
          className="avatar-button"
          onClick={() => setIsMenuOpen((open) => !open)}
          type="button"
        >
          <span>{user ? getInitials(user.name) : "?"}</span>
        </button>
        {isMenuOpen && (
          <div className="profile-popover" role="menu">
            <p className="profile-name">{user?.name}</p>
            <p className="profile-email">{user?.email}</p>
            <button
              className="profile-logout"
              onClick={() => {
                setIsMenuOpen(false);
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
        <button className="rail-button" aria-label="Notifications" title="Notifications" type="button"><BellIcon /></button>
        <button className="rail-button" aria-label="Settings" title="Settings" type="button"><SettingsIcon /></button>
        <button className="rail-button" aria-label="Theme" title="Theme" type="button"><MoonIcon /></button>
        <button className="rail-button" aria-label="Light mode" title="Light mode" type="button"><SunIcon /></button>
      </div>
    </nav>
  );
}