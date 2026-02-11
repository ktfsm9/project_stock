#!/usr/bin/env python3
"""Pipeline log validator for stock backtesting workflow.

Checks:
- Stage success/fallback/failure status
- Missing dependency fallback (e.g. yfinance)
- Data leakage risk (too-good R2)
- Alignment with project scope keywords (주지표/보조지표/거시변수, 분기/연간)
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    level: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate stock pipeline logs")
    parser.add_argument("log_path", type=Path, help="Path to pipeline log text file")
    return parser.parse_args()


def collect_findings(text: str) -> list[Finding]:
    findings: list[Finding] = []

    stage_lines = re.findall(r"\[(\d+)단계\].*?(완료|실패)", text)
    stage_map: dict[str, str] = {}
    for stage, status in stage_lines:
        stage_map[stage] = status

    if not stage_map:
        findings.append(Finding("WARN", "단계 로그를 찾지 못했습니다. 로그 포맷을 확인하세요."))
    else:
        completed = sum(1 for v in stage_map.values() if v == "완료")
        failed = sum(1 for v in stage_map.values() if v == "실패")
        findings.append(Finding("INFO", f"단계 파싱 결과: 완료 {completed}개, 실패 {failed}개"))

    if "No module named 'yfinance'" in text:
        findings.append(
            Finding(
                "WARN",
                "3단계에서 yfinance 모듈 부재로 샘플 데이터 fallback 발생. 실데이터 기반 성능검증 신뢰도 저하 가능.",
            )
        )

    if "샘플 데이터 사용하여 계속 진행" in text and "단계 3 (데이터 수집): [성공]" in text:
        findings.append(
            Finding(
                "WARN",
                "요약에서 3단계를 [성공]으로 집계했지만 실제로는 fallback 실행. 상태를 SUCCESS_WITH_FALLBACK으로 구분 권장.",
            )
        )

    r2_matches = re.findall(r"R² Score:\s*([0-9.]+)", text)
    high_r2 = [float(v) for v in r2_matches if float(v) >= 0.999]
    if high_r2:
        findings.append(
            Finding(
                "WARN",
                "R²가 매우 높습니다(>=0.999). 미래정보 누수(look-ahead) 또는 타깃 누수 여부를 점검하세요.",
            )
        )

    required_keywords = ["주지표", "보조지표", "거시", "분기", "연간"]
    missing = [k for k in required_keywords if k not in text]
    if missing:
        findings.append(
            Finding(
                "WARN",
                "로그에 프로젝트 핵심 범위 키워드 일부가 보이지 않습니다: " + ", ".join(missing),
            )
        )
    else:
        findings.append(Finding("INFO", "프로젝트 범위 키워드 확인 완료"))

    if "최고 전략: RSI_30_70" in text:
        findings.append(Finding("INFO", "현재 샘플 실행 기준 최고 전략은 RSI_30_70"))

    return findings


def main() -> int:
    args = parse_args()
    log_text = args.log_path.read_text(encoding="utf-8")
    findings = collect_findings(log_text)

    print("=== 파이프라인 로그 검증 결과 ===")
    for finding in findings:
        print(f"[{finding.level}] {finding.message}")

    risk_count = sum(1 for f in findings if f.level == "WARN")
    print(f"\n총 경고 수: {risk_count}")
    if risk_count == 0:
        print("판정: PASS")
        return 0

    print("판정: REVIEW_NEEDED")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
