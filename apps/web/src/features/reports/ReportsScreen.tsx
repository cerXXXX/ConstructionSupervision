import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { formatMoment, formatPlanDate, formatSize } from "@/entities/format";
import {
  type Period,
  type ReportCreated,
  defaultPeriod,
  periodProblem,
  useCreateReport,
  useReports,
} from "@/features/reports/useReports";
import { label, ru } from "@/shared/locale/ru";
import { Empty, ErrorBox, Loading } from "@/shared/ui/QueryState";

/**
 * Отчёты объекта: сформировать PDF за период и открыть готовые (apps/web/README.md, §3).
 * Отчёт оформляет выводы последнего анализа, поэтому без анализа формировать нечего.
 */
export function ReportsScreen() {
  const { objectId = "" } = useParams();
  const { object, status, reports } = useReports(objectId);

  if (object.isPending) return <Loading />;
  if (object.isError) return <ErrorBox error={object.error} onRetry={() => object.refetch()} />;

  return (
    <section className="space-y-6">
      <div>
        <Link to={`/objects/${objectId}`} className="text-sm text-muted hover:text-ink">
          ← {object.data.name}
        </Link>
        <h2 className="text-xl font-semibold">Отчёты</h2>
        <p className="text-sm text-muted">
          PDF план-факт: статус и SPI, Гант, загрузка техники, отклонения со снимками-доказательствами,
          резюме и раздел «Ограничения» — чего система за период не видела.
        </p>
      </div>

      {status.isPending && <Loading />}
      {status.isError && <ErrorBox error={status.error} onRetry={() => status.refetch()} />}
      {status.data === null && (
        <Empty>
          По объекту ещё не было анализа: отчёт оформляет его выводы, формировать пока нечего.
          Анализ запускается кнопкой «Пересчитать» на дашборде.
        </Empty>
      )}
      {status.data && (
        <CreateForm
          objectId={objectId}
          asOf={status.data.as_of}
          // Новый анализ — новый период по умолчанию.
          key={status.data.as_of}
        />
      )}

      <div>
        <h3 className="mb-2 font-semibold">Сформированные отчёты</h3>
        {reports.isPending && <Loading />}
        {reports.isError && <ErrorBox error={reports.error} onRetry={() => reports.refetch()} />}
        {reports.data?.total === 0 && (
          <Empty>Отчётов по объекту ещё нет. Сформируйте первый формой выше.</Empty>
        )}
        {reports.data && reports.data.total > 0 && (
          <table className="w-full border-collapse text-left text-sm">
            <thead className="text-muted">
              <tr className="border-b border-ink/10">
                <th className="py-2 pr-4 font-normal">Период</th>
                <th className="py-2 pr-4 font-normal">Сформирован</th>
                <th className="py-2 pr-4 font-normal">Размер</th>
                <th className="py-2 font-normal" />
              </tr>
            </thead>
            <tbody>
              {reports.data.items.map((report) => (
                <tr key={report.key} className="border-b border-ink/10">
                  <td className="py-2 pr-4">
                    {formatPlanDate(report.period_from)} — {formatPlanDate(report.period_to)}
                  </td>
                  <td className="py-2 pr-4">{formatMoment(report.created_at)}</td>
                  <td className="py-2 pr-4">{formatSize(report.size_bytes)}</td>
                  <td className="py-2">
                    <a
                      href={report.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent underline"
                    >
                      Открыть PDF
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

function CreateForm({ objectId, asOf }: { objectId: string; asOf: string }) {
  const [period, setPeriod] = useState<Period>(() => defaultPeriod(asOf));
  const create = useCreateReport(objectId);
  const problem = periodProblem(period);

  return (
    <div className="space-y-3 rounded-lg border border-ink/10 bg-white/60 p-4">
      <form
        className="flex flex-wrap items-end gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          if (!problem) create.mutate(period);
        }}
      >
        <label className="text-sm">
          <span className="block text-muted">С</span>
          <input
            type="date"
            value={period.from}
            onChange={(e) => setPeriod({ ...period, from: e.target.value })}
            className="rounded border border-ink/20 px-2 py-1"
          />
        </label>
        <label className="text-sm">
          <span className="block text-muted">По (включительно)</span>
          <input
            type="date"
            value={period.to}
            onChange={(e) => setPeriod({ ...period, to: e.target.value })}
            className="rounded border border-ink/20 px-2 py-1"
          />
        </label>
        <button
          type="submit"
          disabled={problem != null || create.isPending}
          className="rounded bg-ink px-3 py-1.5 text-sm text-white hover:bg-ink/80 disabled:opacity-50"
        >
          {create.isPending ? "Формируем PDF…" : "Сформировать PDF"}
        </button>
        <button
          type="button"
          onClick={() => setPeriod(defaultPeriod(asOf))}
          className="text-sm text-muted underline"
        >
          Неделя по день анализа
        </button>
      </form>
      <p className="text-xs text-muted">
        Даты — сутки по Москве. Выводы в отчёте — на момент анализа {formatMoment(asOf)}; дни
        периода позже него отчёт назовёт в «Ограничениях». Отчёт того же периода, сформированный
        сегодня повторно, заменяет прежний.
      </p>
      {problem && <p className="text-sm text-red-800">{problem}</p>}
      {create.isError && <ErrorBox error={create.error} />}
      {create.data && <Created report={create.data} />}
    </div>
  );
}

function Created({ report }: { report: ReportCreated }) {
  return (
    <div className="rounded border border-emerald-300 bg-emerald-50 p-3 text-sm text-emerald-950">
      <p className="font-medium">
        Отчёт за {formatPlanDate(report.period_from)} — {formatPlanDate(report.period_to)} готов
        ({formatSize(report.size_bytes)}).{" "}
        <a href={report.url} target="_blank" rel="noreferrer" className="underline">
          Открыть PDF
        </a>
      </p>
      <p>
        Снимков-доказательств: {report.evidence_images}
        {report.evidence_missing > 0 &&
          `, не вставлено: ${report.evidence_missing} — причины в разделе «Ограничения»`}
        . Резюме: {label(ru.summarySource, report.summary_generated_by)}.
      </p>
    </div>
  );
}
