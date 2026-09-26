import { useQuery } from "@tanstack/react-query";
import { useReducer, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { formatPlanDate } from "@/entities/format";
import { isZoneType } from "@/entities/zones";
import {
  EMPTY_DRAFT,
  fromRule,
  problems,
  reduce,
  sameDraft,
  type Action,
  type RuleDraft,
} from "@/features/rules-editor/draft";
import { useSaveRule, useSelectedStage, type SaveResult } from "@/features/rules-editor/useRulesEditor";
import { equipmentClassesQuery, type StageRead } from "@/shared/api/queries";
import { ru, type StageLabel } from "@/shared/locale/ru";
import { Empty, ErrorBox, Loading } from "@/shared/ui/QueryState";

// Людей правило вехи не касается: они участвуют только в D6 (methodology.md, раздел 6).
const NOT_EQUIPMENT = "person";
const STAGE_LABELS = Object.keys(ru.stageLabel) as StageLabel[];

/**
 * Редактор правил «веха → техника» (T31): логика — данные, а не код. Меняем правило —
 * анализ пересчитывает ленту, и видно, какие отклонения исчезли или появились.
 */
export function RulesEditorScreen() {
  const { objectId = "" } = useParams();
  const { stages, items, stage, select } = useSelectedStage(objectId);

  return (
    <section className="space-y-4">
      <div>
        <Link to={`/objects/${objectId}`} className="text-sm text-muted hover:text-ink">
          ← Дашборд
        </Link>
        <h2 className="text-xl font-semibold">Правила «веха → техника»</h2>
        <p className="text-sm text-muted">
          Какая техника обязательна на вехе, какая допустима и по какому признаку веха считается
          начатой. Сохранение пересчитывает ленту предупреждений.
        </p>
      </div>

      {stages.isPending && <Loading />}
      {stages.isError && <ErrorBox error={stages.error} onRetry={() => stages.refetch()} />}
      {stages.isSuccess && items.length === 0 && (
        <Empty>У объекта нет графика: импортируйте его или сгенерируйте по МРР — правила приходят вместе с вехами.</Empty>
      )}
      {stage && (
        <div className="grid items-start gap-4 lg:grid-cols-[20rem_1fr]">
          <StageList items={items} current={stage} onSelect={select} />
          {/* Ключ — веха, а не версия правила: после сохранения итог пересчёта остаётся на экране. */}
          <RuleEditor key={stage.id} objectId={objectId} stage={stage} />
        </div>
      )}
    </section>
  );
}

function StageList({
  items,
  current,
  onSelect,
}: {
  items: StageRead[];
  current: StageRead;
  onSelect: (stage: StageRead) => void;
}) {
  return (
    <ul className="space-y-1">
      {items.map((stage) => (
        <li key={stage.id}>
          <button
            type="button"
            onClick={() => onSelect(stage)}
            className={`block w-full rounded-lg border p-2.5 text-left text-sm ${
              stage.id === current.id ? "border-accent bg-white" : "border-ink/10 bg-white/60 hover:border-ink/30"
            }`}
          >
            <span className="font-medium">{stage.code}</span> {stage.name}
            <span className="block text-xs text-muted">
              {formatPlanDate(stage.plan_start)} — {formatPlanDate(stage.plan_end)} ·{" "}
              {!stage.rule ? "правила нет" : stage.rule.is_active ? `правило, версия ${stage.rule.version}` : "правило выключено"}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function RuleEditor({ objectId, stage }: { objectId: string; stage: StageRead }) {
  const saved = stage.rule ? fromRule(stage.rule) : EMPTY_DRAFT;
  const [draft, dispatch] = useReducer(reduce, saved);
  const classes = useQuery(equipmentClassesQuery);
  const save = useSaveRule(objectId, stage);
  const names = (code: string) => classes.data?.get(code) ?? code;
  const options = [...(classes.data?.keys() ?? [])].filter((c) => c !== NOT_EQUIPMENT);
  const issues = problems(draft);
  const changed = !sameDraft(draft, saved);

  return (
    <article className="space-y-5 rounded-lg border border-ink/10 bg-white p-5">
      <header>
        <h3 className="text-lg font-semibold">
          {stage.code} {stage.name}
        </h3>
        <p className="text-sm text-muted">
          По плану {formatPlanDate(stage.plan_start)} — {formatPlanDate(stage.plan_end)} · участок «
          {isZoneType(stage.zone_type) ? ru.zoneType[stage.zone_type] : stage.zone_type}»
          {stage.rule && ` · правило версии ${stage.rule.version}`}
        </p>
      </header>

      {!stage.rule && (
        <p className="rounded bg-amber-50 p-3 text-sm text-amber-900">
          У вехи нет правила: по ней не проверяются D1, D2, D8, D9, прогресс идёт по плану.
          Заполните правило и сохраните — оно появится.
        </p>
      )}

      <Section
        title="Обязательная техника"
        hint="Группа выполнена, если классов из неё в сумме не меньше минимума. Все группы — комплект вехи: нет ни одной — D1, часть — D2."
      >
        {draft.required.length === 0 && <p className="text-sm text-muted">Групп нет.</p>}
        <div className="space-y-2">
          {draft.required.map((group, index) => (
            <div key={index} className="flex flex-wrap items-center gap-2 rounded border border-ink/10 p-2">
              <span className="text-sm text-muted">Любой из</span>
              <Chips
                codes={group.any_of}
                names={names}
                options={options}
                onAdd={(code) => dispatch({ type: "groupAdd", index, code })}
                onRemove={(code) => dispatch({ type: "groupRemove", index, code })}
              />
              <label className="flex items-center gap-1 text-sm">
                не меньше
                <input
                  type="number"
                  min={1}
                  value={group.min}
                  onChange={(e) => dispatch({ type: "groupMin", index, min: Number(e.target.value) })}
                  className="w-16 rounded border border-ink/20 px-2 py-0.5"
                />
              </label>
              <button
                type="button"
                onClick={() => dispatch({ type: "removeGroup", index })}
                className="ml-auto text-sm text-red-700 hover:underline"
              >
                удалить группу
              </button>
            </div>
          ))}
        </div>
        <button type="button" onClick={() => dispatch({ type: "addGroup" })} className="mt-2 text-sm text-accent underline">
          + группа
        </button>
      </Section>

      <Section title="Допустимая техника" hint="Её присутствие на участке вехи не вызывает D3 «техника не по этапу».">
        <Chips
          codes={draft.allowed}
          names={names}
          options={options}
          onAdd={(code) => dispatch({ type: "allowedAdd", code })}
          onRemove={(code) => dispatch({ type: "allowedRemove", code })}
        />
      </Section>

      <Section
        title="Сигнатура старта"
        hint="Веха считается начатой, когда эти классы видны одновременно, а стадия по фото — не раньше указанной."
      >
        <div className="flex flex-wrap items-center gap-3">
          <Chips
            codes={draft.signature.equipment}
            names={names}
            options={options}
            onAdd={(code) => dispatch({ type: "signatureAdd", code })}
            onRemove={(code) => dispatch({ type: "signatureRemove", code })}
          />
          <label className="flex items-center gap-1 text-sm">
            стадия по фото
            <select
              value={draft.signature.stage_label ?? ""}
              onChange={(e) =>
                dispatch({ type: "stageLabel", label: (e.target.value || null) as StageLabel | null })
              }
              className="rounded border border-ink/20 bg-white px-2 py-0.5"
            >
              <option value="">не важна</option>
              {STAGE_LABELS.map((l) => (
                <option key={l} value={l}>
                  {ru.stageLabel[l]}
                </option>
              ))}
            </select>
          </label>
        </div>
      </Section>

      <Section title="Устойчивость и включение">
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <label className="flex items-center gap-1">
            сессий подряд
            <input
              type="number"
              min={1}
              value={draft.min_sessions}
              onChange={(e) => dispatch({ type: "minSessions", value: Number(e.target.value) })}
              className="w-16 rounded border border-ink/20 px-2 py-0.5"
            />
          </label>
          <label className="flex items-center gap-1">
            <input
              type="checkbox"
              checked={draft.is_active}
              onChange={(e) => dispatch({ type: "active", value: e.target.checked })}
            />
            правило включено
          </label>
        </div>
        <p className="mt-1 text-xs text-muted">
          Условие должно держаться столько рабочих сессий подряд: одиночный кадр не повод для тревоги.
        </p>
      </Section>

      <SaveBar
        draft={draft}
        saved={saved}
        changed={changed}
        issues={issues}
        dispatch={dispatch}
        save={save}
        objectId={objectId}
        creating={!stage.rule}
      />
    </article>
  );
}

function SaveBar({
  draft,
  saved,
  changed,
  issues,
  dispatch,
  save,
  objectId,
  creating,
}: {
  draft: RuleDraft;
  saved: RuleDraft;
  changed: boolean;
  issues: string[];
  dispatch: (action: Action) => void;
  save: ReturnType<typeof useSaveRule>;
  objectId: string;
  creating: boolean;
}) {
  return (
    <div className="space-y-2 border-t border-ink/10 pt-4">
      {issues.map((issue) => (
        <p key={issue} className="text-sm text-red-700">
          {issue}
        </p>
      ))}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={!changed || issues.length > 0 || save.isPending}
          onClick={() =>
            save.mutate(draft, {
              onSuccess: (result) => dispatch({ type: "reset", draft: fromRule(result.rule) }),
            })
          }
          className="rounded bg-ink px-3 py-1.5 text-sm text-white disabled:opacity-40"
        >
          {save.isPending ? "Сохраняем и пересчитываем…" : creating ? "Создать правило и пересчитать" : "Сохранить и пересчитать"}
        </button>
        <button
          type="button"
          disabled={!changed || save.isPending}
          onClick={() => dispatch({ type: "reset", draft: saved })}
          className="rounded border border-ink/20 px-3 py-1.5 text-sm disabled:opacity-40"
        >
          Отменить правки
        </button>
      </div>
      {save.isError && <ErrorBox error={save.error} />}
      {save.data && <SaveOutcome result={save.data} objectId={objectId} />}
    </div>
  );
}

/** Итог сохранения: что пересчёт сделал с лентой. Ради этого экрана и показывают демо. */
function SaveOutcome({ result, objectId }: { result: SaveResult; objectId: string }) {
  const line = (d: SaveResult["gone"][number]) => `${d.code} — ${d.title}`;
  return (
    <div className="rounded border border-emerald-300 bg-emerald-50 p-3 text-sm text-emerald-950">
      <p className="font-medium">
        Правило сохранено, версия {result.rule.version}. Лента пересчитана.
      </p>
      {result.gone.length === 0 && result.added.length === 0 && <p>Отклонения не изменились.</p>}
      {result.gone.length > 0 && (
        <div>
          <p>Исчезли из ленты — по новому правилу их не было:</p>
          <ul className="list-disc pl-5">
            {result.gone.map((d) => (
              <li key={d.id}>{line(d)}</li>
            ))}
          </ul>
        </div>
      )}
      {result.added.length > 0 && (
        <div>
          <p>Появились:</p>
          <ul className="list-disc pl-5">
            {result.added.map((d) => (
              <li key={d.id}>{line(d)}</li>
            ))}
          </ul>
        </div>
      )}
      <Link to={`/objects/${objectId}/deviations`} className="mt-1 inline-block text-accent underline">
        Открыть ленту предупреждений
      </Link>
    </div>
  );
}

/** Классы техники списком с крестиками и выпадающим списком для добавления. */
function Chips({
  codes,
  names,
  options,
  onAdd,
  onRemove,
}: {
  codes: string[];
  names: (code: string) => string;
  options: string[];
  onAdd: (code: string) => void;
  onRemove: (code: string) => void;
}) {
  const free = options.filter((c) => !codes.includes(c));
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {codes.map((code) => (
        <span key={code} className="inline-flex items-center gap-1 rounded bg-ink/10 px-2 py-0.5 text-sm">
          {names(code)}
          <button
            type="button"
            onClick={() => onRemove(code)}
            aria-label={`Убрать ${names(code)}`}
            className="text-muted hover:text-red-700"
          >
            ×
          </button>
        </span>
      ))}
      {codes.length === 0 && <span className="text-sm text-muted">нет</span>}
      {free.length > 0 && (
        <select
          value=""
          onChange={(e) => e.target.value && onAdd(e.target.value)}
          className="rounded border border-ink/20 bg-white px-1 py-0.5 text-sm"
        >
          <option value="">+ класс</option>
          {free.map((c) => (
            <option key={c} value={c}>
              {names(c)}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}

function Section({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <section>
      <h4 className="font-semibold">{title}</h4>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}
