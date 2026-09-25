"""Метрики детектора на размеченной выборке: precision / recall / mAP50 по классам.

    python ml/eval/evaluate.py --weights data/models/yolov8s-worldv2.pt \
        --data ml/datasets/external/ulima/data-world.yaml --split test

Одинаково для zero-shot и дообученных весов, чтобы в docs/metrics.md шли обе колонки
(ml/README.md, «Метрики»). У YOLO-World словарь задаётся именами классов датасета — в
data-world.yaml это первые промпты классов из equipment_classes.yaml.
Печатает таблицу Markdown; матрица ошибок — в ml/runs/eval/<имя>/.
"""

import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def markdown_table(names: dict[int, str], counts: dict[int, int], metrics) -> str:
    """Строка на класс и итог: число рамок в выборке, P, R, mAP50, mAP50-95."""
    lines = [
        "| Класс | Рамок | Precision | Recall | mAP50 | mAP50-95 |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    box = metrics.box
    for row, cls in enumerate(box.ap_class_index):
        p, r, ap50, ap = box.class_result(row)
        lines.append(f"| {names[int(cls)]} | {counts.get(int(cls), 0)} | {p:.2f} | {r:.2f} | "
                     f"{ap50:.2f} | {ap:.2f} |")  # fmt: skip
    lines.append(f"| **все** | {sum(counts.values())} | {box.mp:.2f} | {box.mr:.2f} | "
                 f"{box.map50:.2f} | {box.map:.2f} |")  # fmt: skip
    return "\n".join(lines)


def label_counts(data_yaml: Path, split: str) -> dict[int, int]:
    """Сколько рамок каждого класса в выборке — без этого числа метрика ничего не говорит."""
    counts: dict[int, int] = {}
    for txt in (data_yaml.parent / "labels" / split).glob("*.txt"):
        for line in txt.read_text().splitlines():
            if line.strip():
                cls = int(line.split()[0])
                counts[cls] = counts.get(cls, 0) + 1
    return counts


def run_name(weights: Path) -> str:
    """Имя для отчёта: у весов из ml/runs/<прогон>/weights/ файл всегда last.pt или best.pt."""
    return weights.parent.parent.name if weights.parent.name == "weights" else weights.stem


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--weights", required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--conf", type=float, default=0.001, help="порог для кривой PR, не рабочий")
    args = parser.parse_args()

    from ultralytics import YOLO, YOLOWorld

    names = yaml.safe_load(args.data.read_text(encoding="utf-8"))["names"]
    if "world" in Path(args.weights).name:
        model = YOLOWorld(args.weights)
        model.set_classes(list(names.values()))
    else:
        model = YOLO(args.weights)
    metrics = model.val(
        data=str(args.data),
        split=args.split,
        imgsz=args.imgsz,
        conf=args.conf,
        batch=4,
        project=str(ROOT / "ml" / "runs" / "eval"),
        name=f"{run_name(Path(args.weights))}-{args.split}",
        exist_ok=True,
        plots=True,
        verbose=False,
    )
    print(f"\n{args.weights} на {args.data.parent.name}/{args.split}, вход {args.imgsz}\n")
    print(markdown_table(names, label_counts(args.data, args.split), metrics))


if __name__ == "__main__":
    main()
