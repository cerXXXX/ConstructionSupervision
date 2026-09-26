import { useQuery } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { factLines, groupRows, sessionRows } from "@/entities/deviation";
import { formatMoment } from "@/entities/format";
import { deviationStatusTone, severityTone } from "@/entities/status";
import { zoneColor } from "@/entities/zones";
import { zonePolygon } from "@/features/cameras/useCameras";
import { useExplain, useVerdict } from "@/features/deviations/useDeviations";
import {
  camerasQuery,
  equipmentClassesQuery,
  imageQuery,
  zonesQuery,
  type DeviationRead,
  type ExplainRead,
} from "@/shared/api/queries";
import { label, ru } from "@/shared/locale/ru";
import { Badge } from "@/shared/ui/Badge";
import { Frame } from "@/shared/ui/Frame";
import { DetectionBox, ZoneOutline } from "@/shared/ui/overlays";
import { ErrorBox, Loading } from "@/shared/ui/QueryState";

const EVIDENCE_COLOR = "#c2451a";

/**
 * Карточка отклонения: что система решила, на каких числах, по какому правилу и на каком
 * снимке. Оператор должен за десять секунд понять, согласен ли он (methodology.md, раздел 12).
 */
export function DeviationCard({ objectId, deviation }: { objectId: string; deviation: DeviationRead }) {
  const explain = useExplain(deviation.id);
  const classes = useQuery(equipmentClassesQuery);
  const names = (code: string) => classes.data?.get(code) ?? code;
  const facts = deviation.facts as Record<string, unknown>;
  const groups = groupRows(facts, names);
  const lines = factLines(facts);

  return (
    <article className="space-y-5 rounded-lg border border-ink/10 bg-white p-5">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={severityTone(deviation.severity)}>
            {deviation.code} · {label(ru.severity, deviation.severity)}
          </Badge>
          <Badge tone={deviationStatusTone(deviation.status)}>
            {label(ru.deviationStatus, deviation.status)}
          </Badge>
          <span className="text-sm text-muted">{label(ru.deviationCode, deviation.code)}</span>
        </div>
        <h3 className="text-lg font-semibold">{deviation.title}</h3>
        <p>{deviation.message}</p>
        <p className="text-sm text-muted">
          Эпизод: {formatMoment(deviation.first_seen_at)} — {formatMoment(deviation.last_seen_at)},
          рабочих сессий: {deviation.occurrences}
        </p>
      </header>

      <Verdict deviation={deviation} />

      {(groups.length > 0 || lines.length > 0) && (
        <Section title="Числа">
          {groups.length > 0 && (
            <table className="mb-3 w-full border-collapse text-left text-sm">
              <thead className="text-muted">
                <tr className="border-b border-ink/10">
                  <th className="py-1.5 pr-4 font-normal">Обязательная техника</th>
                  <th className="py-1.5 pr-4 font-normal">Норма</th>
                  <th className="py-1.5 font-normal">Было</th>
                </tr>
              </thead>
              <tbody>
                {groups.map((g) => (
                  <tr key={g.classes} className="border-b border-ink/10">
                    <td className="py-1.5 pr-4">{g.classes}</td>
                    <td className="py-1.5 pr-4">не меньше {g.min}</td>
                    <td className={`py-1.5 font-medium ${g.ok ? "text-emerald-700" : "text-red-700"}`}>
                      {g.observed} {g.ok ? "✓" : "✗"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
            {lines.map((line) => (
              <div key={line.label} className="contents">
                <dt className="text-muted">{line.label}</dt>
                <dd>{line.value}</dd>
              </div>
            ))}
          </dl>
        </Section>
      )}

      {explain.isPending && <Loading />}
      {explain.isError && <ErrorBox error={explain.error} onRetry={() => explain.refetch()} />}
      {explain.data && (
        <>
          <RuleSection explain={explain.data} facts={facts} />
          <EvidenceSection objectId={objectId} deviation={deviation} explain={explain.data} />
          <SessionsSection deviation={deviation} explain={explain.data} names={names} />
        </>
      )}
    </article>
  );
}

function Verdict({ deviation }: { deviation: DeviationRead }) {
  const verdict = useVerdict(deviation);
  const [comment, setComment] = useState(deviation.verdict_comment ?? "");
  const recorded =
    deviation.verdict_at != null
      ? `${label(ru.verdict, deviation.verdict)}: ${deviation.verdict_by ?? "оператор"}, ${formatMoment(deviation.verdict_at)}${
          deviation.verdict_comment ? ` — «${deviation.verdict_comment}»` : ""
        }`
      : null;

  return (
    <div className="space-y-2 rounded bg-ink/5 p-3 text-sm">
      {recorded && <p className="font-medium">{recorded}</p>}
      {deviation.status === "RESOLVED" && (
        <p className="text-muted">
          Отклонение закрыто: условие уже не выполняется. Вердикт останется в истории — «да, это
          было» или «ложное срабатывание».
        </p>
      )}
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Комментарий к вердикту (необязательно)"
        maxLength={2000}
        rows={2}
        className="w-full rounded border border-ink/20 bg-white p-2"
      />
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={verdict.isPending}
          onClick={() => verdict.mutate({ status: "CONFIRMED", comment })}
          className="rounded bg-red-700 px-3 py-1.5 text-white disabled:opacity-50"
        >
          Подтвердить
        </button>
        <button
          type="button"
          disabled={verdict.isPending}
          onClick={() => verdict.mutate({ status: "REJECTED", comment })}
          className="rounded border border-ink/20 bg-white px-3 py-1.5 disabled:opacity-50"
        >
          Ложное срабатывание
        </button>
      </div>
      {verdict.isError && <ErrorBox error={verdict.error} />}
    </div>
  );
}

function RuleSection({ explain, facts }: { explain: ExplainRead; facts: Record<string, unknown> }) {
  const rule = explain.rule;
  const stageVersion = typeof facts.stage_rule_version === "number" ? facts.stage_rule_version : null;
  // Пороги — числа и флаги; вложенные словари (шаблоны текстов, названия причин) оператору
  // здесь не нужны: их видно в самом тексте отклонения.
  const params = Object.entries(rule?.params ?? {}).filter(
    ([, value]) => value === null || typeof value !== "object",
  );
  return (
    <Section title="Правило">
      {rule == null ? (
        <p className="text-sm text-muted">Настройки правила не найдены.</p>
      ) : (
        <div className="space-y-1 text-sm">
          <p>
            {rule.code} «{label(ru.deviationCode, rule.code)}» · базовая серьёзность{" "}
            {label(ru.severity, rule.severity).toLowerCase()}
            {!rule.enabled && " · правило выключено"}
          </p>
          {params.length > 0 && (
            <p className="text-muted">
              Параметры: {params.map(([key, value]) => `${key} = ${JSON.stringify(value)}`).join(", ")}
            </p>
          )}
          {stageVersion != null && (
            <p className="text-muted">
              Правило вехи «веха → техника», версия {stageVersion}: на нём построены нормы выше.
            </p>
          )}
        </div>
      )}
    </Section>
  );
}

/** Снимок-доказательство: рамки техники из вывода и зона участка отклонения. */
function EvidenceSection({
  objectId,
  deviation,
  explain,
}: {
  objectId: string;
  deviation: DeviationRead;
  explain: ExplainRead;
}) {
  const [index, setIndex] = useState(0);
  const evidence = explain.evidence;
  const current = evidence[Math.min(index, evidence.length - 1)];
  if (!current) {
    const reason = (deviation.facts as Record<string, unknown>).evidence_absent_reason;
    return (
      <Section title="Снимок">
        <p className="text-sm text-muted">
          Снимков нет{typeof reason === "string" ? `: ${reason}` : ""}. Участок не был виден — вывод
          «проверить вручную», а не «пусто».
        </p>
      </Section>
    );
  }
  return (
    <Section title={`Снимок${evidence.length > 1 ? ` ${index + 1} из ${evidence.length}` : ""}`}>
      {evidence.length > 1 && (
        <div className="mb-2 flex gap-1 text-sm">
          {evidence.map((e, i) => (
            <button
              key={e.image_id}
              type="button"
              onClick={() => setIndex(i)}
              className={`rounded px-2 py-0.5 ${i === index ? "bg-ink text-white" : "hover:bg-ink/10"}`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}
      <EvidenceFrame
        key={current.image_id}
        objectId={objectId}
        imageId={current.image_id}
        detectionIds={current.detection_ids}
        area={deviation.area ?? null}
      />
    </Section>
  );
}

function EvidenceFrame({
  objectId,
  imageId,
  detectionIds,
  area,
}: {
  objectId: string;
  imageId: string;
  detectionIds: string[];
  area: string | null;
}) {
  const image = useQuery(imageQuery(imageId));
  const cameraId = image.data?.camera_id ?? "";
  const zones = useQuery({ ...zonesQuery(cameraId), enabled: cameraId !== "" });
  const cameras = useQuery(camerasQuery(objectId));
  const classes = useQuery(equipmentClassesQuery);

  if (image.isPending) return <Loading />;
  if (image.isError) return <ErrorBox error={image.error} onRetry={() => image.refetch()} />;
  const detail = image.data;
  const size = { width: detail.width ?? 1920, height: detail.height ?? 1080 };
  const wanted = new Set(detectionIds);
  const boxes = detail.detections.filter((d) => wanted.has(d.id));
  const areaZones = (zones.data?.items ?? []).filter((z) => z.area === area);
  const camera = cameras.data?.items.find((c) => c.id === detail.camera_id);
  const name = (code: string) => classes.data?.get(code) ?? code;

  return (
    <div className="space-y-2">
      <Frame url={detail.url} alt={`Снимок ${formatMoment(detail.captured_at)}`} {...size}>
        {areaZones.map((zone) => (
          <ZoneOutline
            key={zone.id}
            polygon={zonePolygon(zone)}
            color={zoneColor(zone.zone_type)}
            label={zone.name}
            size={size}
            muted={boxes.length > 0}
          />
        ))}
        {boxes.map((d) => (
          <DetectionBox
            key={d.id}
            bbox={d.bbox}
            anchor={d.anchor}
            label={`${name(d.equipment_class)} ${d.conf.toFixed(2)}`}
            color={EVIDENCE_COLOR}
            size={size}
          />
        ))}
      </Frame>
      <p className="text-sm text-muted">
        {camera?.name ?? "Камера"} · {formatMoment(detail.captured_at)} ·{" "}
        {boxes.length > 0
          ? `рамок в выводе: ${boxes.length}`
          : "рамок нет: снимок показывает, что техники на участке не было"}
        {" · "}
        <Link
          to={`/objects/${objectId}/cameras?camera=${camera?.code ?? ""}&image=${imageId}`}
          className="text-accent underline"
        >
          открыть на экране камер
        </Link>
      </p>
      {zones.isError && <ErrorBox error={zones.error} />}
    </div>
  );
}

function SessionsSection({
  deviation,
  explain,
  names,
}: {
  deviation: DeviationRead;
  explain: ExplainRead;
  names: (code: string) => string;
}) {
  if (explain.sessions == null) {
    return (
      <Section title="Проверенные сессии">
        <p className="text-sm text-muted">
          Факты сессий сейчас недоступны
          {explain.sessions_unavailable_reason ? `: ${explain.sessions_unavailable_reason}` : ""}.
        </p>
      </Section>
    );
  }
  const rows = sessionRows(explain.sessions, deviation.area ?? null, names);
  return (
    <Section title={`Проверенные сессии: ${rows.length}`}>
      <table className="w-full border-collapse text-left text-sm">
        <thead className="text-muted">
          <tr className="border-b border-ink/10">
            <th className="py-1.5 pr-4 font-normal">Окно</th>
            <th className="py-1.5 pr-4 font-normal">Участок</th>
            <th className="py-1.5 font-normal">Техника на участке</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-ink/10 align-top">
              <td className="py-1.5 pr-4 tabular-nums">{row.at}</td>
              <td className="py-1.5 pr-4">{row.visibility}</td>
              <td className="py-1.5">{row.equipment}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {explain.sessions_truncated && (
        <p className="mt-1 text-xs text-muted">Показаны не все сессии эпизода.</p>
      )}
    </Section>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h4 className="mb-2 font-semibold">{title}</h4>
      {children}
    </section>
  );
}
