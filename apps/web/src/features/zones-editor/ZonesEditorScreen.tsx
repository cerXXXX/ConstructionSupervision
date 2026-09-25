import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { selfIntersects, type Point } from "@/entities/polygon";
import { ZONE_TYPES, areaKey, isZoneType, zoneColor } from "@/entities/zones";
import {
  countByClass,
  useCameraAnchors,
  useImage,
  useSelectedCamera,
} from "@/features/cameras/useCameras";
import type { Action, DraftZone } from "@/features/zones-editor/draft";
import { EditorCanvas } from "@/features/zones-editor/EditorCanvas";
import { saveErrorText, useZonesEditor } from "@/features/zones-editor/useZonesEditor";
import { areasQuery, equipmentClassesQuery, type CameraRead } from "@/shared/api/queries";
import { ru, type ZoneType } from "@/shared/locale/ru";
import { CameraTabs } from "@/shared/ui/CameraTabs";
import { Empty, ErrorBox, Loading } from "@/shared/ui/QueryState";

/**
 * Редактор зон (T40, F11): полигоны участков на эталонном кадре камеры. Одинаковые тип и
 * название на разных камерах — один участок (ADR-0013): так участок, видимый двумя камерами,
 * остаётся видимым, когда одну из них закрыли.
 */
export function ZonesEditorScreen() {
  const { objectId = "" } = useParams();
  const { cameras, items, camera, select } = useSelectedCamera(objectId);
  const [dirty, setDirty] = useState(false);

  const switchCamera = (next: CameraRead) => {
    if (dirty && !window.confirm("Есть несохранённые правки зон. Перейти к другой камере без них?")) {
      return;
    }
    select(next);
  };

  return (
    <section className="space-y-4">
      <div>
        <Link to={`/objects/${objectId}/cameras`} className="text-sm text-muted hover:text-ink">
          ← Камеры
        </Link>
        <h2 className="text-xl font-semibold">Редактор зон</h2>
        <p className="text-sm text-muted">
          Участок — это тип и название. Одинаковые тип и название на разных камерах — один
          участок: техника на нём считается по всем камерам, а видимым он остаётся, пока его
          видит хоть одна.
        </p>
      </div>
      {cameras.isPending && <Loading />}
      {cameras.isError && <ErrorBox error={cameras.error} onRetry={() => cameras.refetch()} />}
      {cameras.isSuccess && items.length === 0 && (
        <Empty>У объекта нет камер: они появляются при загрузке снимков. Размечать пока не на чем.</Empty>
      )}
      {camera && (
        <>
          <CameraTabs cameras={items} current={camera} onSelect={switchCamera} />
          <CameraEditor key={camera.id} camera={camera} objectId={objectId} onDirty={setDirty} />
        </>
      )}
    </section>
  );
}

function CameraEditor({
  camera,
  objectId,
  onDirty,
}: {
  camera: CameraRead;
  objectId: string;
  onDirty: (dirty: boolean) => void;
}) {
  const reference = useImage(camera.reference_image_id);
  const editor = useZonesEditor(camera);
  const [drawing, setDrawing] = useState<Point[] | null>(null);
  const [newType, setNewType] = useState<ZoneType>("PIT");
  const [showAnchors, setShowAnchors] = useState(false);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const anchors = useCameraAnchors(camera.id, showAnchors);
  const classes = useQuery(equipmentClassesQuery);
  const dirty = editor.pending.length > 0;

  useEffect(() => onDirty(dirty), [dirty, onDirty]);
  useEffect(() => {
    // Закрытие вкладки с несохранёнными правками: браузер спросит сам.
    if (!dirty) return;
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  useEffect(() => {
    if (!drawing) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setDrawing(null);
      if (e.key === "Backspace") setDrawing((p) => (p ? p.slice(0, -1) : p));
      if (e.key === "Enter" && drawing.length >= 3) finishDrawing(drawing);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const finishDrawing = (points: Point[]) => {
    editor.dispatch({ type: "add", polygon: points, zoneType: newType });
    setDrawing(null);
  };

  if (camera.reference_image_id == null) {
    return (
      <Empty>
        У камеры нет эталонного кадра: он появляется с первым загруженным снимком. Выбрать другой
        кадр можно на экране <Link to={`/objects/${objectId}/cameras?camera=${camera.code}`} className="underline">камер</Link>.
      </Empty>
    );
  }
  if (reference.isPending || editor.zones.isPending) return <Loading />;
  if (reference.isError) return <ErrorBox error={reference.error} onRetry={() => reference.refetch()} />;
  if (editor.zones.isError) {
    return <ErrorBox error={editor.zones.error} onRetry={() => editor.zones.refetch()} />;
  }
  const size = { width: reference.data.width ?? 1920, height: reference.data.height ?? 1080 };
  const selected = editor.draft.zones.find((z) => z.key === editor.draft.selected && !z.deleted);
  const counts = countByClass(anchors.anchors.map((a) => ({ equipment_class: a.equipmentClass })));
  const color = anchorColors([...counts.keys()]);
  const points = anchors.anchors
    .filter((a) => !hidden.has(a.equipmentClass))
    .map((a) => ({ id: a.id, point: a.point, color: color.get(a.equipmentClass) ?? "#c2451a" }));
  const toggle = (code: string) =>
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_22rem]">
      <div className="space-y-2">
        <Toolbar
          drawing={drawing}
          newType={newType}
          onNewType={setNewType}
          onStart={() => {
            editor.dispatch({ type: "select", key: null });
            setDrawing([]);
          }}
          onFinish={() => drawing && drawing.length >= 3 && finishDrawing(drawing)}
          onCancel={() => setDrawing(null)}
        />
        <EditorCanvas
          url={reference.data.url}
          size={size}
          zones={editor.draft.zones}
          selected={editor.draft.selected}
          drawing={drawing}
          anchors={showAnchors ? points : []}
          onDraw={(next, finished) => (finished && next ? finishDrawing(next) : setDrawing(next))}
          dispatch={editor.dispatch}
        />
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          <label className="flex items-center gap-1">
            <input type="checkbox" checked={showAnchors} onChange={(e) => setShowAnchors(e.target.checked)} />
            где стояла техника на всех снимках камеры
          </label>
          {showAnchors && anchors.isPending && <span className="text-muted">загружаем снимки…</span>}
          {showAnchors &&
            [...counts].map(([code, count]) => (
              <label key={code} className="flex items-center gap-1">
                <input type="checkbox" checked={!hidden.has(code)} onChange={() => toggle(code)} />
                <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color.get(code) }} />
                {classes.data?.get(code) ?? code}: {count}
              </label>
            ))}
        </div>
        {showAnchors && anchors.error != null && <ErrorBox error={anchors.error} />}
        <p className="text-xs text-muted">
          Вершину тяните мышью, «+» на ребре добавляет вершину, двойной щелчок по вершине удаляет
          её. Зону целиком двигают за её внутреннюю часть. Машина относится к зоне по нижней
          середине своей рамки — к точке, где она стоит на земле; размечайте с запасом.
        </p>
      </div>
      <aside className="space-y-4 text-sm">
        <SavePanel editor={editor} />
        {selected ? (
          <ZoneProperties
            zone={selected}
            objectId={objectId}
            camera={camera}
            error={editor.errors.get(selected.key)}
            dispatch={editor.dispatch}
          />
        ) : (
          <p className="text-muted">Выберите зону на кадре или в списке, чтобы изменить её.</p>
        )}
        <ZoneList zones={editor.draft.zones} selected={editor.draft.selected} errors={editor.errors} dispatch={editor.dispatch} />
      </aside>
    </div>
  );
}

// Цвета точек по классам: контрастные между собой и с цветами зон, по порядку появления.
const ANCHOR_PALETTE = ["#e11d48", "#f59e0b", "#10b981", "#06b6d4", "#8b5cf6", "#ec4899", "#84cc16", "#f97316"];

function anchorColors(codes: string[]): Map<string, string> {
  return new Map(codes.map((code, i) => [code, ANCHOR_PALETTE[i % ANCHOR_PALETTE.length] ?? "#c2451a"]));
}

function Toolbar({
  drawing,
  newType,
  onNewType,
  onStart,
  onFinish,
  onCancel,
}: {
  drawing: Point[] | null;
  newType: ZoneType;
  onNewType: (t: ZoneType) => void;
  onStart: () => void;
  onFinish: () => void;
  onCancel: () => void;
}) {
  if (!drawing) {
    return (
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <select
          value={newType}
          onChange={(e) => isZoneType(e.target.value) && onNewType(e.target.value)}
          className="rounded border border-ink/20 bg-white px-2 py-1"
        >
          {ZONE_TYPES.map((t) => (
            <option key={t} value={t}>
              {ru.zoneType[t]}
            </option>
          ))}
        </select>
        <button type="button" onClick={onStart} className="rounded bg-ink px-3 py-1 text-white">
          Нарисовать зону
        </button>
      </div>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-2 rounded bg-accent/10 px-3 py-2 text-sm">
      <span>
        Новая зона «{ru.zoneType[newType]}»: щёлкайте по углам участка. Замкнуть — щелчок по первой
        точке или Enter; Backspace убирает последнюю точку, Esc — отмена.
      </span>
      <button type="button" onClick={onFinish} disabled={drawing.length < 3} className="rounded bg-ink px-3 py-1 text-white disabled:opacity-40">
        Готово
      </button>
      <button type="button" onClick={onCancel} className="underline">
        Отмена
      </button>
    </div>
  );
}

function SavePanel({ editor }: { editor: ReturnType<typeof useZonesEditor> }) {
  const count = editor.pending.length;
  const invalid = editor.draft.zones.some((z) => !z.deleted && selfIntersects(z.polygon));
  return (
    <div className="space-y-2 rounded-lg border border-ink/10 bg-white/60 p-3">
      <p>{count === 0 ? "Все правки сохранены." : `Несохранённых изменений: ${count}`}</p>
      {invalid && <p className="text-red-800">Есть зона с пересекающимися сторонами — такую сервис не примет.</p>}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => editor.save.mutate()}
          disabled={count === 0 || invalid || editor.save.isPending}
          className="rounded bg-accent px-3 py-1 text-white disabled:opacity-40"
        >
          {editor.save.isPending ? "Сохраняем…" : "Сохранить"}
        </button>
        <button type="button" onClick={editor.discard} disabled={count === 0 || editor.save.isPending} className="underline disabled:opacity-40">
          Отменить правки
        </button>
      </div>
      {editor.save.isSuccess && editor.errors.size === 0 && count === 0 && (
        <p className="text-muted">
          Сохранено. Факты окон и выводы анализа пересчитаются в фоне, повторного распознавания не
          нужно.
        </p>
      )}
      {editor.errors.size > 0 && (
        <p className="text-red-800">Не сохранено зон: {editor.errors.size}. Причина — у зоны в списке.</p>
      )}
    </div>
  );
}

function ZoneProperties({
  zone,
  objectId,
  camera,
  error,
  dispatch,
}: {
  zone: DraftZone;
  objectId: string;
  camera: CameraRead;
  error: unknown;
  dispatch: (action: Action) => void;
}) {
  const areas = useQuery(areasQuery(objectId));
  const key = areaKey(zone.zoneType, zone.name);
  const sameType = (areas.data?.areas ?? []).filter((a) => a.zone_type === zone.zoneType);
  const shared = sameType
    .find((a) => a.area === key)
    ?.cameras.filter((c) => c.camera_id !== camera.id)
    .map((c) => c.camera_code);

  return (
    <div className="space-y-3 rounded-lg border border-ink/10 bg-white/60 p-3">
      <label className="block space-y-1">
        <span className="text-muted">Тип участка</span>
        <select
          value={zone.zoneType}
          onChange={(e) => isZoneType(e.target.value) && dispatch({ type: "setType", key: zone.key, zoneType: e.target.value })}
          className="w-full rounded border border-ink/20 bg-white px-2 py-1"
        >
          {ZONE_TYPES.map((t) => (
            <option key={t} value={t}>
              {ru.zoneType[t]}
            </option>
          ))}
        </select>
        <span className="block text-xs text-muted">Роль: {ru.zoneRole[zone.zoneType]}</span>
      </label>
      <label className="block space-y-1">
        <span className="text-muted">Название участка</span>
        <input
          value={zone.name}
          onChange={(e) => dispatch({ type: "setName", key: zone.key, name: e.target.value })}
          placeholder={ru.zoneType[zone.zoneType]}
          list="area-names"
          className="w-full rounded border border-ink/20 bg-white px-2 py-1"
        />
        <datalist id="area-names">
          {sameType.map((a) => (
            <option key={a.area} value={a.name} />
          ))}
        </datalist>
        <span className="block text-xs text-muted">
          Участок: {key}
          {shared && shared.length > 0
            ? ` — тот же участок, что на ${shared.join(", ")}`
            : " — на других камерах такого участка нет"}
        </span>
      </label>
      <p className="text-xs text-muted">Вершин: {zone.polygon.length}</p>
      {error != null && <p className="text-red-800">Не сохранено: {saveErrorText(error)}</p>}
      <button
        type="button"
        onClick={() => dispatch({ type: "delete", key: zone.key })}
        className="text-red-800 underline"
      >
        Удалить зону
      </button>
    </div>
  );
}

function ZoneList({
  zones,
  selected,
  errors,
  dispatch,
}: {
  zones: DraftZone[];
  selected: string | null;
  errors: Map<string, unknown>;
  dispatch: (action: Action) => void;
}) {
  if (zones.length === 0) {
    return <Empty>Зон на этой камере нет. Выберите тип и нажмите «Нарисовать зону».</Empty>;
  }
  return (
    <ul className="space-y-1">
      {zones.map((zone) => (
        <li key={zone.key} className="flex items-center gap-2">
          <span className="h-3 w-3 shrink-0 rounded-sm" style={{ background: zoneColor(zone.zoneType) }} />
          {zone.deleted ? (
            <>
              <span className="text-muted line-through">{zone.name || ru.zoneType[zone.zoneType]}</span>
              <button type="button" onClick={() => dispatch({ type: "restore", key: zone.key })} className="text-xs underline">
                вернуть
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => dispatch({ type: "select", key: zone.key })}
              className={`text-left ${zone.key === selected ? "font-semibold" : ""}`}
            >
              {zone.name || ru.zoneType[zone.zoneType]}
              <span className="text-muted"> · {ru.zoneType[zone.zoneType]}</span>
              {zone.saved == null && <span className="text-accent"> · новая</span>}
              {errors.has(zone.key) && <span className="text-red-800"> · не сохранена</span>}
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}
