from analysis import generate_report, save_report

if __name__ == "__main__":
    for ticker in ["AAPL", "7203.T"]:
        report = generate_report(ticker)
        path = save_report(report, f"output/reports/{ticker.replace('.', '_')}.md")
        print(f"saved: {path}")
