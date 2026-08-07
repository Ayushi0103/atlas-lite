import backgroundUrl from "../assets/img.png";

export function BackgroundLayer() {
  return (
    <div className="background-layer" aria-hidden="true">
      <img src={backgroundUrl} alt="" loading="eager" />
      <div className="background-wash" />
    </div>
  );
}
