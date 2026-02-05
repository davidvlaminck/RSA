from lib.reports.ReportLoopRunner import ReportLoopRunner

if __name__ == '__main__':
    reportlooprunner = ReportLoopRunner(settings_path=r'/home/davidllinux/Documenten/AWV/resources/settings_RSA.json')
    # reportlooprunner = ReportLoopRunner(settings_path=r'C:\resources\settings_RSA.json')
    reportlooprunner.start(run_right_away=False)

# first on linux do: pip install psycopg2-binary
