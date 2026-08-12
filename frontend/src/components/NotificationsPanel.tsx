import { useNotifications } from "../context/NotificationsContext";

function formatTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function NotificationsPanel() {
  const { notifications, markAllRead, markRead, clearAll } = useNotifications();

  return (
    <div className="popover notifications-popover" role="menu">
      <div className="popover-header">
        <p className="popover-title">Notifications</p>
        <div className="popover-header-actions">
          {notifications.length > 0 && (
            <>
              <button className="popover-link" onClick={markAllRead} type="button">
                Mark all read
              </button>
              <button className="popover-link" onClick={clearAll} type="button">
                Clear
              </button>
            </>
          )}
        </div>
      </div>
      <div className="notifications-list">
        {notifications.length === 0 && (
          <p className="empty-copy">You're all caught up. Activity like uploads and chats will show up here.</p>
        )}
        {notifications.map((item) => (
          <button
            className={`notification-row notification-${item.kind} ${item.read ? "" : "is-unread"}`}
            key={item.id}
            onClick={() => markRead(item.id)}
            type="button"
          >
            <span className="notification-dot" aria-hidden="true" />
            <span className="notification-body">
              <strong>{item.title}</strong>
              {item.message && <p>{item.message}</p>}
              <time>{formatTime(item.createdAt)}</time>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}