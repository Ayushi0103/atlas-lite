import type { ReactElement } from "react";
import { BellIcon, ChatIcon, GridIcon, HomeIcon, MoonIcon, SearchIcon, SettingsIcon, SunIcon } from "./Icons";
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

export function Sidebar({ currentView, onNavigate }: SidebarProps) {
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
      <button className="avatar-button" aria-label="Profile" type="button">
        <span>A</span>
      </button>
      <div className="side-group">
        <button className="rail-button" aria-label="Notifications" title="Notifications" type="button"><BellIcon /></button>
        <button className="rail-button" aria-label="Settings" title="Settings" type="button"><SettingsIcon /></button>
        <button className="rail-button" aria-label="Theme" title="Theme" type="button"><MoonIcon /></button>
        <button className="rail-button" aria-label="Light mode" title="Light mode" type="button"><SunIcon /></button>
      </div>
    </nav>
  );
}
