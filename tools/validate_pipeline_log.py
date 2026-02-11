#!/usr/bin/env python3
"""Validate stock backtesting pipeline logs against project scope.

Focus areas:
- Stage status consistency (success/failure/fallback)
- Data dependency fallback detection (e.g. yfinance missing)
- Modeling risk flags (suspiciously high R², missing direction accuracy)
- Scope alignment keywords (주지표/보조지표/거시변수, 분기/연간)
- Backtest/reporting completeness hints
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    level: str  # INFO, WARN
    category: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate stock pipeline logs")
    parser.add_argument("log_path", type=Path, help="Path to pipeline log text file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when WARN exists (default behavior)",
    )
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="Always exit 0 after printing report (for CI dry-run/report-only mode)",
    )
    parser.add_argument(
        "--print-exit-code",
        action="store_true",
        help="Print numeric exit code at the end for shell portability checks",
    )
    return parser.parse_args()


def _collect_stage_status(text: str) -> dict[str, str]:
    stage_lines = re.findall(r"\[(\d+)단계\].*?(완료|실패)", text)
    stage_map: dict[str, str] = {}
    for stage, status in stage_lines:
        stage_map[stage] = status
    return stage_map


def _extract_model_direction_accuracy(text: str) -> dict[str, float]:
    acc: dict[str, float] = {}
    pattern = re.compile(r"^\s*([A-Za-z_]+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+([0-9.]+)\s*$")
    for line in text.splitlines():
        m = pattern.match(line)
        if m:
            model = m.group(1)
            acc[model] = float(m.group(2))
    return acc


def collect_findings(text: str) -> list[Finding]:
    findings: list[Finding] = []

    stage_map = _collect_stage_status(text)
    if not stage_map:
        findings.append(Finding("WARN", "stage", "단계 로그를 찾지 못했습니다. 로그 포맷을 확인하세요."))
    else:
        completed = sum(1 for v in stage_map.values() if v == "완료")
        failed = sum(1 for v in stage_map.values() if v == "실패")
        findings.append(Finding("INFO", "stage", f"단계 파싱 결과: 완료 {completed}개, 실패 {failed}개"))

    fallback = "No module named 'yfinance'" in text or "샘플 데이터 사용하여 계속 진행" in text
    if fallback:
        findings.append(
            Finding(
                "WARN",
                "data",
                "3단계에서 외부 데이터 의존성 문제로 fallback 실행 정황이 있습니다. 실데이터 기반 검증 신뢰도 저하 가능.",
            )
        )

    if "샘플 데이터 사용하여 계속 진행" in text and "단계 3 (데이터 수집): [성공]" in text:
        findings.append(
            Finding(
                "WARN",
                "stage",
                "요약에서 3단계를 [성공]으로 집계했지만 실제로는 fallback 실행. SUCCESS_WITH_FALLBACK 구분 권장.",
            )
        )

    r2_matches = re.findall(r"R² Score:\s*([0-9.]+)", text)
    high_r2 = [float(v) for v in r2_matches if float(v) >= 0.999]
    if high_r2:
        findings.append(
            Finding(
                "WARN",
                "ml",
                f"R² 과대 구간 감지(>=0.999, {len(high_r2)}회). look-ahead/target leakage 점검 필요.",
            )
        )

    model_acc = _extract_model_direction_accuracy(text)
    zero_acc_models = [m for m, v in model_acc.items() if v == 0.0]
    if zero_acc_models:
        findings.append(
            Finding(
                "WARN",
                "ml",
                "방향성 정확도 0으로 기록된 모델 존재: " + ", ".join(sorted(zero_acc_models)),
            )
        )

    high_corr_count_match = re.search(r"높은 상관관계 찾기 \(\|r\| > 0\.7\).*?발견:\s*(\d+)개", text, re.S)
    if high_corr_count_match:
        cnt = int(high_corr_count_match.group(1))
        if cnt >= 50:
            findings.append(
                Finding(
                    "WARN",
                    "feature",
                    f"고상관 쌍 {cnt}개 감지. 중복지표/다중공선성 제거 규칙을 명시적으로 적용하세요.",
                )
            )
        else:
            findings.append(Finding("INFO", "feature", f"고상관 쌍 개수: {cnt}개"))

    required_keywords = ["주지표", "보조지표", "거시", "분기", "연간"]
    missing = [k for k in required_keywords if k not in text]
    if missing:
        findings.append(
            Finding(
                "WARN",
                "scope",
                "로그에서 프로젝트 핵심 범위 키워드 미확인: " + ", ".join(missing),
            )
        )
    else:
        findings.append(Finding("INFO", "scope", "프로젝트 범위 키워드 확인 완료"))

    if "Annual_Return" in text:
        findings.append(Finding("INFO", "backtest", "연간 수익률 컬럼(Annual_Return) 확인"))
    else:
        findings.append(Finding("WARN", "backtest", "연간 성과 지표 확인 실패"))

    if "분기" not in text and "Q1" not in text and "Q2" not in text and "Q3" not in text and "Q4" not in text:
        findings.append(Finding("WARN", "backtest", "분기별 성과 산출 흔적이 로그에 없습니다."))

    return findings


def print_report(findings: list[Finding]) -> None:
    print("=== 파이프라인 로그 검증 결과 ===")
    for f in findings:
        print(f"[{f.level}][{f.category}] {f.message}")

    warn_count = sum(1 for f in findings if f.level == "WARN")
    print(f"\n총 경고 수: {warn_count}")
    if warn_count == 0:
        print("판정: PASS")
    elif warn_count <= 2:
        print("판정: PASS_WITH_CAUTION")
    else:
        print("판정: REVIEW_NEEDED")


def compute_exit_code(warn_count: int, lenient: bool) -> int:
    if lenient:
        return 0
    return 0 if warn_count == 0 else 2


def main() -> int:
    args = parse_args()
    log_text = args.log_path.read_text(encoding="utf-8")
    findings = collect_findings(log_text)
    print_report(findings)

    warn_count = sum(1 for f in findings if f.level == "WARN")
    exit_code = compute_exit_code(warn_count=warn_count, lenient=args.lenient)
    if args.print_exit_code:
        print(f"EXIT_CODE: {exit_code}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
