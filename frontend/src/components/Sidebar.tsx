import { BellIcon, ChatIcon, GridIcon, HomeIcon, MoonIcon, SearchIcon, SettingsIcon, SunIcon } from "./Icons";

type SidebarProps = {
  onHome: () => void;
  isSheetOpen: boolean;
};

export function Sidebar({ onHome, isSheetOpen }: SidebarProps) {
  const items = [
    { label: "Home", icon: <HomeIcon />, action: onHome, active: !isSheetOpen },
    { label: "Search", icon: <SearchIcon />, active: isSheetOpen },
    { label: "Collections", icon: <GridIcon /> },
    { label: "Chat", icon: <ChatIcon /> },
  ];

  return (
    <nav className="side-rail" aria-label="Primary">
      <div className="side-group">
        {items.map((item) => (
          <button
            aria-current={item.active ? "page" : undefined}
            aria-label={item.label}
            className={`rail-button ${item.active ? "is-active" : ""}`}
            key={item.label}
            onClick={item.action}
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
