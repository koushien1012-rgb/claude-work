import sys

from backtest.evaluate import evaluate_pending
from backtest.record import record_snapshot
from backtest.report import build_report

USAGE = "usage: python run_backtest.py [record|evaluate|report|all]"


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "record":
        n = record_snapshot()
        print(f"{n} 件の新しい予想を記録しました")
    elif cmd == "evaluate":
        evaluate_pending()
    elif cmd == "report":
        build_report()
    elif cmd == "all":
        evaluate_pending()
        build_report()
    else:
        print(f"unknown command: {cmd}")
        print(USAGE)


if __name__ == "__main__":
    main()
