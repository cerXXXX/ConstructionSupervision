import type { CameraRead } from "@/shared/api/queries";

/** Переключатель камер объекта; выключенная камера видна, но помечена. */
export function CameraTabs({
  cameras,
  current,
  onSelect,
}: {
  cameras: CameraRead[];
  current: CameraRead;
  onSelect: (camera: CameraRead) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {cameras.map((camera) => (
        <button
          key={camera.id}
          type="button"
          onClick={() => onSelect(camera)}
          title={camera.code}
          className={`rounded-lg border px-3 py-1.5 text-sm ${
            camera.id === current.id
              ? "border-ink bg-ink text-white"
              : "border-ink/20 hover:border-accent"
          } ${camera.is_active ? "" : "opacity-50"}`}
        >
          {camera.name}
          {!camera.is_active && " (выключена)"}
        </button>
      ))}
    </div>
  );
}
