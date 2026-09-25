import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { formatMoment } from "@/entities/format";
import { isZoneType, zoneColor } from "@/entities/zones";
import {
  countByClass,
  dayOf,
  groupByDay,
  movement,
  timeOf,
  useCameraImages,
  useImage,
  useSelectedCamera,
  useSelectedImage,
  useSetReference,
  useZones,
  zonePolygon,
} from "@/features/cameras/useCameras";
import {
  equipmentClassesQuery,
  type CameraRead,
  type ImageDetail,
  type ImageRead,
  type ZoneRead,
} from "@/shared/api/queries";
import { label, ru } from "@/shared/locale/ru";
import { CameraTabs } from "@/shared/ui/CameraTabs";
import { Frame } from "@/shared/ui/Frame";
import { DetectionBox, ZoneOutline } from "@/shared/ui/overlays";
import { Empty, ErrorBox, Loading } from "@/shared/ui/QueryState";

const DETECTION_COLOR = "#c2451a";

/**
 * Просмотр камеры (T33): снимок, зоны камеры и рамки детекций, переключение камер и снимков
 * по времени. Здесь видно, что увидело распознавание и в какую зону site отнёс каждую машину.
 */
export function CamerasScreen() {
  const { objectId = "" } = useParams();
  const { cameras, items, camera, select } = useSelectedCamera(objectId);

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link to={`/objects/${objectId}`} className="text-sm text-muted hover:text-ink">
            ← Дашборд
          </Link>
          <h2 className="text-xl font-semibold">Камеры</h2>
        </div>
        <Link
          to={`/objects/${objectId}/settings/zones${camera ? `?camera=${camera.code}` : ""}`}
          className="rounded border border-ink/20 px-3 py-1.5 text-sm hover:border-accent"
        >
          Редактор зон
        </Link>
      </div>

      {cameras.isPending && <Loading />}
      {cameras.isError && <ErrorBox error={cameras.error} onRetry={() => cameras.refetch()} />}
      {cameras.isSuccess && items.length === 0 && (
        <Empty>
          У объекта нет камер. Камера появляется сама при загрузке снимков из папки с её кодом
          (`python scripts/seed.py` для демо) или через `POST /site/cameras`.
        </Empty>
      )}
      {camera && (
        <>
          <CameraTabs cameras={items} current={camera} onSelect={select} />
          <CameraView key={camera.id} camera={camera} />
        </>
      )}
    </section>
  );
}

function CameraView({ camera }: { camera: CameraRead }) {
  const images = useCameraImages(camera.id);
  const { current, index, select } = useSelectedImage(images.images);
  const zones = useZones(camera.id);

  if (images.isPending) return <Loading />;
  if (images.error) return <ErrorBox error={images.error} />;
  if (images.total === 0 || !current) {
    return <Empty>У камеры нет снимков. Загрузите их — экран покажет кадр, зоны и рамки.</Empty>;
  }
  return (
    <div className="space-y-3">
      <ImagePicker images={images.images} current={current} index={index} onSelect={select} />
      {images.truncated && (
        <p className="text-xs text-muted">
          Показаны последние {images.images.length} снимков из {images.total}.
        </p>
      )}
      <ImagePanel
        imageId={current.id}
        camera={camera}
        zones={zones.data?.items ?? []}
        zonesError={zones.error}
      />
    </div>
  );
}

/** Снимки по дням: сначала день, потом время. «←» и «→» листают подряд через дни. */
function ImagePicker({
  images,
  current,
  index,
  onSelect,
}: {
  images: ImageRead[];
  current: ImageRead;
  index: number;
  onSelect: (image: ImageRead) => void;
}) {
  const days = groupByDay(images);
  const currentDay = dayOf(current);
  const step = (delta: number) => {
    const next = images[index + delta];
    if (next) onSelect(next);
  };
  return (
    <div className="space-y-2 rounded-lg border border-ink/10 bg-white/60 p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={() => step(-1)} disabled={index === 0} className="px-2 disabled:opacity-30">
          ←
        </button>
        {[...days.keys()].map((day) => (
          <button
            key={day}
            type="button"
            onClick={() => {
              const first = days.get(day)?.[0];
              if (first) onSelect(first);
            }}
            className={`rounded px-2 py-0.5 ${day === currentDay ? "bg-ink text-white" : "hover:bg-ink/10"}`}
          >
            {day}
          </button>
        ))}
        <button
          type="button"
          onClick={() => step(1)}
          disabled={index === images.length - 1}
          className="px-2 disabled:opacity-30"
        >
          →
        </button>
      </div>
      <div className="flex flex-wrap gap-1">
        {(days.get(currentDay) ?? []).map((image) => (
          <button
            key={image.id}
            type="button"
            onClick={() => onSelect(image)}
            title={label(ru.imageStatus, image.status)}
            className={`rounded px-2 py-0.5 tabular-nums ${
              image.id === current.id ? "bg-accent text-white" : "hover:bg-ink/10"
            } ${image.usable === false ? "line-through" : ""}`}
          >
            {timeOf(image)}
          </button>
        ))}
      </div>
    </div>
  );
}

function ImagePanel({
  imageId,
  camera,
  zones,
  zonesError,
}: {
  imageId: string;
  camera: CameraRead;
  zones: ZoneRead[];
  zonesError: unknown;
}) {
  const image = useImage(imageId);
  const classes = useQuery(equipmentClassesQuery);
  const [showZones, setShowZones] = useState(true);
  // Скрытые классы переживают переход к другому снимку: людей на обзорной камере десятки.
  const [hidden, setHidden] = useState<Set<string>>(new Set());

  if (image.isPending) return <Loading />;
  if (image.isError) return <ErrorBox error={image.error} onRetry={() => image.refetch()} />;
  const detail = image.data;
  const size = { width: detail.width ?? 1920, height: detail.height ?? 1080 };
  const zoneById = new Map(zones.map((z) => [z.id, z]));
  const className = (code: string) => classes.data?.get(code) ?? code;
  const counts = countByClass(detail.detections);
  const shown = detail.detections.filter((d) => !hidden.has(d.equipment_class));
  const toggle = (code: string) =>
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
      <div className="space-y-2">
        <Frame url={detail.url} alt={`Снимок ${formatMoment(detail.captured_at)}`} {...size}>
          {showZones &&
            zones.map((zone) => (
              <ZoneOutline
                key={zone.id}
                polygon={zonePolygon(zone)}
                color={zoneColor(zone.zone_type)}
                label={zone.name}
                size={size}
                muted={shown.length > 0}
              />
            ))}
          {shown.map((d) => (
              <DetectionBox
                key={d.id}
                bbox={d.bbox}
                anchor={d.anchor}
                label={`${className(d.equipment_class)} ${d.conf.toFixed(2)}`}
                color={DETECTION_COLOR}
                size={size}
              />
            ))}
        </Frame>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <label className="flex items-center gap-1">
            <input type="checkbox" checked={showZones} onChange={(e) => setShowZones(e.target.checked)} />
            зоны
          </label>
          {[...counts].map(([code, count]) => (
            <label key={code} className="flex items-center gap-1">
              <input type="checkbox" checked={!hidden.has(code)} onChange={() => toggle(code)} />
              {className(code)}: {count}
            </label>
          ))}
        </div>
        {zonesError != null && <ErrorBox error={zonesError} />}
      </div>
      <ImageSide detail={detail} camera={camera} zoneById={zoneById} className={className} />
    </div>
  );
}

function ImageSide({
  detail,
  camera,
  zoneById,
  className,
}: {
  detail: ImageDetail;
  camera: CameraRead;
  zoneById: Map<string, ZoneRead>;
  className: (code: string) => string;
}) {
  const quality = detail.quality as { brightness?: number; blur?: number };
  return (
    <aside className="space-y-4 text-sm">
      <div className="space-y-1">
        <p className="font-medium">{formatMoment(detail.captured_at)}</p>
        <p className="text-muted">
          {label(ru.imageStatus, detail.status)}
          {detail.usable === false && ` · непригоден: ${detail.usable_reason ?? "?"}`}
        </p>
        {typeof quality.brightness === "number" && (
          <p className="text-muted">
            яркость {quality.brightness.toFixed(2)}, размытость {quality.blur?.toFixed(2) ?? "—"}
          </p>
        )}
        {detail.stage && (
          <p className="text-muted">
            стадия по фото: {detail.stage.stage_label} ({detail.stage.conf.toFixed(2)})
          </p>
        )}
        <ReferenceControl imageId={detail.id} camera={camera} />
      </div>
      <div>
        <p className="mb-1 font-medium">Техника: {detail.detections.length}</p>
        {detail.detections.length === 0 ? (
          <p className="text-muted">
            {detail.status === "ANALYZED" ? "Распознавание техники не нашло." : "Снимок ещё не распознан."}
          </p>
        ) : (
          <ul className="space-y-1">
            {detail.detections.map((d) => {
              const zone = d.zone_id ? zoneById.get(d.zone_id) : undefined;
              return (
                <li key={d.id} className="border-b border-ink/10 pb-1">
                  <span className="font-medium">{className(d.equipment_class)}</span>{" "}
                  <span className="text-muted">{d.conf.toFixed(2)}</span>
                  <br />
                  <span className="text-muted">
                    {zone
                      ? `${zone.name} (${isZoneType(zone.zone_type) ? ru.zoneType[zone.zone_type] : zone.zone_type})`
                      : "вне зон"}
                    {" · "}
                    {movement(d.moved)}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}

function ReferenceControl({ imageId, camera }: { imageId: string; camera: CameraRead }) {
  const setReference = useSetReference(camera);
  if (camera.reference_image_id === imageId) {
    return <p className="text-accent">Эталонный кадр камеры: на нём размечают зоны</p>;
  }
  return (
    <div>
      <button
        type="button"
        onClick={() => setReference.mutate(imageId)}
        disabled={setReference.isPending}
        className="text-accent underline disabled:opacity-50"
      >
        Сделать эталонным кадром
      </button>
      {setReference.isError && <ErrorBox error={setReference.error} />}
    </div>
  );
}

